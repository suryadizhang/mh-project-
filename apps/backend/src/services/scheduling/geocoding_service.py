"""
Geocoding Service

Converts addresses to geographic coordinates using Google Maps Geocoding API.
Provides address normalization and validation.
"""

import os
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GeocodedAddress:
    """Result from geocoding an address"""

    original_address: str
    normalized_address: str
    lat: Decimal
    lng: Decimal
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    place_id: Optional[str] = None  # Google Place ID
    is_valid: bool = True
    confidence: float = 1.0


class GeocodingService:
    """
    Convert addresses to coordinates using Google Maps Geocoding API.

    Features:
    - Address normalization
    - Component extraction (city, state, zip)
    - Confidence scoring
    - Caching (via travel_time_cache proximity)
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        google_maps_api_key: Optional[str] = None,
    ):
        self.session = session
        self.api_key = google_maps_api_key or os.getenv("GOOGLE_MAPS_API_KEY")

    async def geocode(self, address: str) -> Optional[GeocodedAddress]:
        """
        Convert address string to coordinates.

        Args:
            address: Full address string

        Returns:
            GeocodedAddress with coordinates and normalized address,
            or None if geocoding failed
        """
        if not address or not address.strip():
            return None

        # Try Google Maps API first
        if self.api_key:
            result = await self._geocode_with_google(address)
            if result:
                return result

        # Fallback: try to parse zip code for approximate location
        return await self._fallback_geocode(address)

    async def _geocode_with_google(self, address: str) -> Optional[GeocodedAddress]:
        """Use Google Maps Geocoding API."""
        try:
            import httpx

            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": address,
                "key": self.api_key,
                "components": "country:US",  # Restrict to US
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()

            if data.get("status") != "OK" or not data.get("results"):
                return None

            result = data["results"][0]
            location = result["geometry"]["location"]

            # Extract address components
            components = {}
            for component in result.get("address_components", []):
                types = component.get("types", [])
                if "street_number" in types:
                    components["street_number"] = component["short_name"]
                elif "route" in types:
                    components["street_name"] = component["short_name"]
                elif "locality" in types:
                    components["city"] = component["long_name"]
                elif "administrative_area_level_1" in types:
                    components["state"] = component["short_name"]
                elif "postal_code" in types:
                    components["zip_code"] = component["short_name"]
                elif "country" in types:
                    components["country"] = component["short_name"]

            # Determine confidence based on result type
            location_type = result["geometry"].get("location_type", "")
            confidence = {
                "ROOFTOP": 1.0,
                "RANGE_INTERPOLATED": 0.9,
                "GEOMETRIC_CENTER": 0.7,
                "APPROXIMATE": 0.5,
            }.get(location_type, 0.5)

            return GeocodedAddress(
                original_address=address,
                normalized_address=result.get("formatted_address", address),
                lat=Decimal(str(location["lat"])),
                lng=Decimal(str(location["lng"])),
                street_number=components.get("street_number"),
                street_name=components.get("street_name"),
                city=components.get("city"),
                state=components.get("state"),
                zip_code=components.get("zip_code"),
                country=components.get("country", "US"),
                place_id=result.get("place_id"),
                is_valid=True,
                confidence=confidence,
            )

        except Exception:
            return None

    async def _fallback_geocode(self, address: str) -> Optional[GeocodedAddress]:
        """
        Fallback geocoding using zip code centroid.

        This is a rough approximation when API is unavailable.
        """
        import re

        # Try to extract zip code
        zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", address)
        if not zip_match:
            return None

        zip_code = zip_match.group(1)

        # Common US zip code centroids (small sample)
        # In production, this would query a zip code database
        ZIP_CENTROIDS = {
            # Texas (Houston area)
            "77001": (29.7604, -95.3698),
            "77002": (29.7533, -95.3599),
            "77003": (29.7439, -95.3391),
            # Add more as needed...
        }

        coords = ZIP_CENTROIDS.get(zip_code)
        if not coords:
            # Default to rough US center
            return GeocodedAddress(
                original_address=address,
                normalized_address=address,
                lat=Decimal("39.8283"),
                lng=Decimal("-98.5795"),
                zip_code=zip_code,
                is_valid=False,
                confidence=0.1,
            )

        return GeocodedAddress(
            original_address=address,
            normalized_address=address,
            lat=Decimal(str(coords[0])),
            lng=Decimal(str(coords[1])),
            zip_code=zip_code,
            is_valid=True,
            confidence=0.3,  # Low confidence for zip-only
        )

    async def validate_address(self, address: str) -> tuple[bool, str]:
        """
        Validate an address and return normalized version.

        Returns:
            Tuple of (is_valid, normalized_address or error_message)
        """
        result = await self.geocode(address)

        if result is None:
            return False, "Unable to validate address"

        if not result.is_valid:
            return False, "Address could not be verified"

        if result.confidence < 0.5:
            return False, f"Address is approximate. Did you mean: {result.normalized_address}?"

        return True, result.normalized_address

    async def get_coordinates(
        self,
        address: str,
    ) -> Optional[tuple[Decimal, Decimal]]:
        """
        Simple method to just get lat/lng coordinates.

        Returns:
            Tuple of (latitude, longitude) or None
        """
        result = await self.geocode(address)
        if result and result.is_valid:
            return result.lat, result.lng
        return None
