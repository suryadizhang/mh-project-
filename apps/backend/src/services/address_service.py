"""
Enterprise Address Service

Follows Uber/DoorDash/Lyft patterns for address management:
- Geocoding with permanent caching (pay Google once per address)
- Customer saved addresses for reuse
- Same address = instant travel fee (no API call)
- Service area validation based on nearest station (multi-station support)

Business Value:
- Reduces Google Maps API costs by 90%+ (cache hits)
- Enables "My Addresses" feature for customers
- Faster booking flow for returning customers
- Multi-station support: finds nearest station automatically
"""

import logging
import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models import Address
from db.models.identity import Station

logger = logging.getLogger(__name__)


# ============================================================================
# SERVICE AREA CONFIGURATION
# ============================================================================

# Maximum service radius in miles (configurable per station, default 150)
DEFAULT_SERVICE_RADIUS_MILES = 150

# Distance beyond which human escalation is required
ESCALATION_RADIUS_MILES = 150

# California-only service (for now)
ALLOWED_STATES = ["CA", "California"]

# California ZIP code prefixes (covers our service areas)
# Bay Area: 940-949, 950-951
# Sacramento: 942, 956-958
# Central Valley: 932-939, 952-955, 959
CALIFORNIA_ZIP_PREFIXES = [
    "940",
    "941",
    "942",
    "943",
    "944",
    "945",
    "946",
    "947",
    "948",
    "949",  # Bay Area
    "950",
    "951",  # Bay Area continued
    "956",
    "957",
    "958",  # Sacramento area
    "932",
    "933",
    "934",
    "935",
    "936",
    "937",
    "938",
    "939",  # Central Valley
    "952",
    "953",
    "954",
    "955",
    "959",  # Central Valley continued
    "930",
    "931",  # Near Central Valley
    "936",  # Fresno area
]


class AddressService:
    """
    Enterprise address management service.

    Key Features:
    - find_or_create_address(): Check cache first, then geocode
    - get_customer_addresses(): List saved addresses for a customer
    - set_default_address(): Mark an address as customer's default
    - calculate_cached_travel_fee(): Use cached coordinates for travel fee
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_address(
        self,
        raw_address: str,
        customer_id: Optional[UUID] = None,
        label: Optional[str] = None,
        is_default: bool = False,
    ) -> Address:
        """
        Find existing address by normalized form, or create and geocode new one.

        Enterprise Pattern (Uber/DoorDash style):
        1. Check if address already exists in cache (by raw_address match)
        2. If found and geocoded, return immediately (no API call)
        3. If not found, geocode with Google and cache permanently

        Args:
            raw_address: Customer-entered address (may be messy)
            customer_id: If provided, save address for customer reuse
            label: Customer label like "Home", "Work", "Mom's House"
            is_default: Whether to set as customer's default address

        Returns:
            Address: Geocoded address (from cache or freshly geocoded)
        """
        # First: Check if address already exists (cache hit)
        existing = await self._find_existing_address(raw_address)
        if existing:
            logger.info(f"Address cache HIT: {raw_address[:50]}...")

            # If customer provided, maybe link to their account
            if customer_id and not existing.customer_id:
                existing.customer_id = customer_id
                existing.address_label = label
                existing.is_default = is_default
                await self.db.commit()

            return existing

        # Cache miss: Need to geocode
        logger.info(f"Address cache MISS: {raw_address[:50]}... - calling Google API")

        # Create new address record
        address = Address(
            raw_address=raw_address,
            customer_id=customer_id,
            address_label=label,
            is_default=is_default,
            geocode_status="pending",
        )
        self.db.add(address)

        # Geocode with Google
        geocode_result = await self._geocode_address(raw_address)

        if geocode_result:
            address.formatted_address = geocode_result.get("formatted_address")
            address.lat = Decimal(str(geocode_result.get("lat", 0)))
            address.lng = Decimal(str(geocode_result.get("lng", 0)))
            address.google_place_id = geocode_result.get("place_id")
            address.street_number = geocode_result.get("street_number")
            address.street_name = geocode_result.get("street_name")
            address.city = geocode_result.get("city")
            address.state = geocode_result.get("state")
            address.zip_code = geocode_result.get("zipcode")  # DB column is zip_code
            address.country = geocode_result.get("country", "US")
            address.geocode_status = "success"
            address.geocoded_at = datetime.now(timezone.utc)

            # Check service area using nearest station (multi-station support)
            service_check = await self._check_service_area_with_station(
                lat=float(address.lat),
                lng=float(address.lng),
                state=address.state,
            )

            address.is_serviceable = service_check["is_serviceable"]
            address.service_station_id = service_check.get("station_id")
            address.distance_to_station_km = (
                Decimal(str(service_check["distance_km"]))
                if service_check.get("distance_km") is not None
                else None
            )

            if address.is_serviceable:
                logger.info(
                    f"Address SERVICEABLE: {address.city}, {address.state} - "
                    f"Station: {service_check.get('station_code', 'N/A')} "
                    f"({service_check.get('distance_miles', 0):.1f} miles)"
                )
            else:
                logger.info(
                    f"Address OUTSIDE service area: {address.city}, {address.state} - "
                    f"Reason: {service_check.get('reason', 'Unknown')}"
                )
        else:
            address.geocode_status = "failed"
            address.is_serviceable = False

        await self.db.commit()
        await self.db.refresh(address)

        return address

    async def _find_existing_address(self, raw_address: str) -> Optional[Address]:
        """
        Find existing address by raw_address or formatted_address.

        Uses case-insensitive matching for robustness.
        """
        # Normalize for comparison
        normalized = raw_address.strip().lower()

        stmt = select(Address).where(Address.raw_address.ilike(normalized)).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_service_area_with_station(
        self,
        lat: float,
        lng: float,
        state: Optional[str],
    ) -> dict:
        """
        Check if address is within service area of any active station.

        Multi-station support: Finds the NEAREST active station and checks
        if the address is within that station's service radius.

        Business Rules:
        - Must be in allowed states (currently California only)
        - Must be within nearest station's service_area_radius (default 150 miles)
        - If distance > escalation_radius_miles (150 miles), requires human escalation

        Returns:
            dict with keys:
            - is_serviceable: bool
            - station_id: UUID or None
            - station_code: str or None
            - distance_km: float or None
            - distance_miles: float or None
            - requires_escalation: bool
            - reason: str (if not serviceable)
        """
        result = {
            "is_serviceable": False,
            "station_id": None,
            "station_code": None,
            "distance_km": None,
            "distance_miles": None,
            "requires_escalation": False,
            "reason": None,
        }

        # Check 1: Must be in allowed states
        if state and state not in ALLOWED_STATES:
            result["reason"] = (
                f"State '{state}' not in service area. We currently serve California only."
            )
            logger.debug(f"Service area check FAILED: state {state} not in {ALLOWED_STATES}")
            return result

        # Find the nearest active station
        nearest = await self._find_nearest_station(lat, lng)

        if not nearest:
            result["reason"] = "No active stations found. Please contact us for availability."
            logger.warning("Service area check FAILED: No active stations in database")
            return result

        station, distance_km = nearest
        distance_miles = distance_km * 0.621371

        result["station_id"] = station.id
        result["station_code"] = station.code
        result["distance_km"] = round(distance_km, 2)
        result["distance_miles"] = round(distance_miles, 2)

        # Check if within service radius
        service_radius = station.service_area_radius or DEFAULT_SERVICE_RADIUS_MILES
        escalation_radius = station.escalation_radius_miles or ESCALATION_RADIUS_MILES

        if distance_miles > service_radius:
            result["reason"] = (
                f"Location is {distance_miles:.0f} miles from our nearest station ({station.code}). "
                f"We currently service within {service_radius} miles."
            )
            logger.debug(
                f"Service area check FAILED: {distance_miles:.1f} mi > {service_radius} mi radius"
            )
            return result

        # Check if escalation required (but still serviceable)
        if distance_miles > escalation_radius:
            result["requires_escalation"] = True
            logger.info(
                f"Address requires escalation: {distance_miles:.1f} mi > {escalation_radius} mi threshold"
            )

        result["is_serviceable"] = True
        return result

    async def _find_nearest_station(
        self,
        lat: float,
        lng: float,
    ) -> Optional[tuple["Station", float]]:
        """
        Find the nearest active station to the given coordinates.

        Returns:
            Tuple of (Station, distance_km) or None if no stations found
        """
        # Get all active, geocoded stations
        stmt = select(Station).where(
            Station.status == "active",
            Station.lat.isnot(None),
            Station.lng.isnot(None),
        )
        result = await self.db.execute(stmt)
        stations = result.scalars().all()

        if not stations:
            logger.warning("No active geocoded stations found in database")
            return None

        # Find nearest station
        nearest_station = None
        min_distance = float("inf")

        for station in stations:
            distance = station.distance_to_km(lat, lng)
            if distance is not None and distance < min_distance:
                min_distance = distance
                nearest_station = station

        if nearest_station:
            logger.debug(f"Nearest station: {nearest_station.code} at {min_distance:.2f} km")
            return (nearest_station, min_distance)

        return None

    def _haversine_distance(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float,
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Returns distance in kilometers.
        """
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def _geocode_address(self, address: str) -> Optional[dict]:
        """
        Call Google Geocoding API to get coordinates and components.

        Returns dict with:
        - formatted_address: Google's standardized format
        - lat, lng: Coordinates
        - place_id: Google's unique ID
        - street_number, street_name, city, state, zipcode, country
        """
        try:
            import httpx

            api_key = settings.GOOGLE_MAPS_API_KEY
            if not api_key:
                logger.warning("GOOGLE_MAPS_API_KEY not set - cannot geocode")
                return None

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "address": address,
                        "key": api_key,
                        "region": "us",  # Bias to US
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

            if data.get("status") != "OK" or not data.get("results"):
                logger.warning(
                    f"Geocoding failed for: {address[:50]}... - status: {data.get('status')}"
                )
                return None

            result = data["results"][0]
            location = result["geometry"]["location"]

            # Parse address components
            components = self._parse_address_components(result.get("address_components", []))

            return {
                "formatted_address": result.get("formatted_address"),
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "place_id": result.get("place_id"),
                **components,
            }

        except Exception as e:
            logger.error(f"Geocoding error for {address[:50]}...: {e}")
            return None

    def _parse_address_components(self, components: list) -> dict:
        """
        Parse Google's address_components array into flat dict.
        """
        result = {}

        for comp in components:
            types = comp.get("types", [])
            value = comp.get("long_name", "")
            short = comp.get("short_name", "")

            if "street_number" in types:
                result["street_number"] = value
            elif "route" in types:
                result["street_name"] = value
            elif "locality" in types:
                result["city"] = value
            elif "administrative_area_level_1" in types:
                result["state"] = short  # Use short for state (e.g., "CA" not "California")
            elif "postal_code" in types:
                result["zipcode"] = value
            elif "country" in types:
                result["country"] = short

        return result

    async def get_customer_addresses(self, customer_id: UUID) -> list[Address]:
        """
        Get all saved addresses for a customer.

        Useful for "My Addresses" feature in customer portal.
        """
        stmt = (
            select(Address)
            .where(Address.customer_id == customer_id)
            .order_by(Address.is_default.desc(), Address.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_default_address(self, customer_id: UUID, address_id: UUID) -> bool:
        """
        Set an address as customer's default.

        Clears is_default from all other addresses first.
        """
        # Clear existing default
        stmt = select(Address).where(Address.customer_id == customer_id, Address.is_default == True)
        result = await self.db.execute(stmt)
        for addr in result.scalars().all():
            addr.is_default = False

        # Set new default
        stmt = select(Address).where(Address.id == address_id)
        result = await self.db.execute(stmt)
        address = result.scalar_one_or_none()

        if address:
            address.is_default = True
            await self.db.commit()
            return True

        return False

    async def get_address_by_id(self, address_id: UUID) -> Optional[Address]:
        """
        Get address by ID.
        """
        stmt = select(Address).where(Address.id == address_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def calculate_distance(
        self,
        address_id: UUID,
        station_lat: Decimal,
        station_lng: Decimal,
    ) -> Optional[float]:
        """
        Calculate distance between address and station.

        Uses Haversine formula for quick estimation.
        For exact travel time, use TravelTimeService.

        Returns distance in kilometers.
        """
        import math

        address = await self.get_address_by_id(address_id)
        if not address or not address.lat or not address.lng:
            return None

        # Haversine formula
        R = 6371  # Earth radius in km

        lat1 = math.radians(float(address.lat))
        lat2 = math.radians(float(station_lat))
        dlat = lat2 - lat1
        dlng = math.radians(float(station_lng) - float(address.lng))

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
