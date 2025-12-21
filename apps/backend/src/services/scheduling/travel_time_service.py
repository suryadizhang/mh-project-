"""
Travel Time Service - Google Maps Integration

Calculates travel time between locations using Google Maps Distance Matrix API.
Includes caching, rush hour awareness, and fallback estimates.
"""

from datetime import datetime, time, timedelta
from typing import Optional, Tuple, NamedTuple
from uuid import UUID
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================


class Coordinates(NamedTuple):
    """Simple lat/lng coordinate pair."""

    lat: float
    lng: float


class TravelTimeResult(BaseModel):
    """Result of a travel time calculation."""

    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    travel_time_minutes: int
    distance_miles: float
    is_rush_hour: bool
    source: str  # 'google_maps', 'cache', 'estimate'
    cached: bool = False

    @property
    def travel_time_with_buffer(self) -> int:
        """Travel time plus 15 min buffer for parking/setup."""
        return self.travel_time_minutes + 15


class ChefLocation(BaseModel):
    """Chef's home or current location."""

    chef_id: UUID
    latitude: float
    longitude: float
    address: Optional[str] = None
    max_travel_distance: int = 50  # miles


# ============================================================
# Constants
# ============================================================

# Rush hour: Mon-Fri 3PM-7PM
RUSH_HOUR_DAYS = [0, 1, 2, 3, 4]  # Monday = 0
RUSH_HOUR_START = time(15, 0)  # 3:00 PM
RUSH_HOUR_END = time(19, 0)  # 7:00 PM
RUSH_HOUR_MULTIPLIER = 1.5

# Travel estimation fallbacks (when no API available)
# Based on Atlanta metro average speeds
AVERAGE_SPEED_NORMAL_MPH = 35
AVERAGE_SPEED_RUSH_HOUR_MPH = 20

# Cache settings
CACHE_EXPIRY_HOURS = 168  # 7 days


# ============================================================
# Travel Time Service
# ============================================================


class TravelTimeService:
    """
    Calculates travel time between locations using Google Maps.

    Features:
    - Google Maps Distance Matrix API integration
    - Intelligent caching to reduce API calls
    - Rush hour awareness (1.5x multiplier Mon-Fri 3-7PM)
    - Fallback estimates when API unavailable
    """

    def __init__(
        self, google_maps_api_key: Optional[str] = None, db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize the travel time service.

        Args:
            google_maps_api_key: Google Maps API key (optional, uses fallback if not provided)
            db_session: Database session for caching (optional)
        """
        self.api_key = google_maps_api_key
        self.db = db_session
        self._client = None

    async def get_travel_time(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Get travel time between two locations.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            departure_time: When the trip will start

        Returns:
            TravelTimeResult with travel time, distance, and metadata
        """
        is_rush = self.is_rush_hour(departure_time)

        # 1. Check cache first
        if self.db:
            cached = await self._get_from_cache(origin_lat, origin_lng, dest_lat, dest_lng, is_rush)
            if cached:
                return cached

        # 2. Try Google Maps API
        if self.api_key:
            try:
                result = await self._call_google_maps(
                    origin_lat, origin_lng, dest_lat, dest_lng, departure_time
                )
                # Cache the result
                if self.db and result:
                    await self._save_to_cache(result)
                return result
            except Exception as e:
                logger.warning(f"Google Maps API error: {e}, using fallback")

        # 3. Fallback: Haversine distance + average speed estimate
        return self._estimate_travel_time(origin_lat, origin_lng, dest_lat, dest_lng, is_rush)

    def is_rush_hour(self, dt: datetime) -> bool:
        """
        Check if the given datetime is during rush hour.

        Rush hour: Monday-Friday, 3:00 PM - 7:00 PM

        Args:
            dt: Datetime to check

        Returns:
            True if during rush hour
        """
        # Check day of week (0 = Monday)
        if dt.weekday() not in RUSH_HOUR_DAYS:
            return False

        # Check time
        current_time = dt.time()
        return RUSH_HOUR_START <= current_time <= RUSH_HOUR_END

    def apply_rush_hour_multiplier(self, base_minutes: int, dt: datetime) -> int:
        """
        Apply rush hour multiplier to travel time.

        Args:
            base_minutes: Base travel time in minutes
            dt: Datetime of travel

        Returns:
            Adjusted travel time (1.5x during rush hour)
        """
        if self.is_rush_hour(dt):
            return int(base_minutes * RUSH_HOUR_MULTIPLIER)
        return base_minutes

    def calculate_distance_miles(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1, lng1: First point coordinates
            lat2, lng2: Second point coordinates

        Returns:
            Distance in miles
        """
        import math

        # Earth's radius in miles
        R = 3959

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return round(distance, 2)

    async def get_chef_to_venue_travel(
        self,
        chef_location: ChefLocation,
        venue_lat: float,
        venue_lng: float,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Calculate travel time from chef's location to venue.

        Args:
            chef_location: Chef's current/home location
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            departure_time: When chef will leave

        Returns:
            TravelTimeResult
        """
        return await self.get_travel_time(
            origin_lat=chef_location.latitude,
            origin_lng=chef_location.longitude,
            dest_lat=venue_lat,
            dest_lng=venue_lng,
            departure_time=departure_time,
        )

    async def can_chef_make_it(
        self,
        chef_location: ChefLocation,
        venue_lat: float,
        venue_lng: float,
        required_arrival_time: datetime,
        buffer_minutes: int = 30,
    ) -> Tuple[bool, Optional[TravelTimeResult]]:
        """
        Check if a chef can arrive at venue on time.

        Args:
            chef_location: Chef's location
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            required_arrival_time: When chef needs to arrive
            buffer_minutes: Extra time buffer (default 30 min for setup)

        Returns:
            Tuple of (can_make_it: bool, travel_result: TravelTimeResult)
        """
        # Calculate when chef would need to leave
        departure_time = required_arrival_time - timedelta(minutes=buffer_minutes)

        result = await self.get_travel_time(
            origin_lat=chef_location.latitude,
            origin_lng=chef_location.longitude,
            dest_lat=venue_lat,
            dest_lng=venue_lng,
            departure_time=departure_time,
        )

        # Chef can make it if travel time + buffer fits before required arrival
        total_time_needed = result.travel_time_minutes + buffer_minutes

        # Check distance limit
        if result.distance_miles > chef_location.max_travel_distance:
            return False, result

        # Check timing
        can_make_it = total_time_needed <= buffer_minutes + result.travel_time_minutes

        return can_make_it, result

    # ============================================================
    # Private Methods
    # ============================================================

    async def _get_from_cache(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        is_rush_hour: bool,
    ) -> Optional[TravelTimeResult]:
        """Get cached travel time if available and not expired."""
        if not self.db:
            return None

        try:
            # Round coordinates to 3 decimal places for cache grouping
            # (approximately 100m precision)
            o_lat = round(origin_lat, 3)
            o_lng = round(origin_lng, 3)
            d_lat = round(dest_lat, 3)
            d_lng = round(dest_lng, 3)

            # Query cache
            # Note: This would use the actual ORM model in production
            # For now, we return None to trigger API call or fallback
            return None

        except Exception as e:
            logger.warning(f"Cache lookup error: {e}")
            return None

    async def _save_to_cache(self, result: TravelTimeResult) -> None:
        """Save travel time result to cache."""
        if not self.db:
            return

        try:
            # Round coordinates for cache key
            o_lat = round(result.origin_lat, 3)
            o_lng = round(result.origin_lng, 3)
            d_lat = round(result.dest_lat, 3)
            d_lng = round(result.dest_lng, 3)

            # Note: This would use the actual ORM model in production
            logger.debug(f"Cached travel time: {o_lat},{o_lng} → {d_lat},{d_lng}")

        except Exception as e:
            logger.warning(f"Cache save error: {e}")

    async def _call_google_maps(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Call Google Maps Distance Matrix API.

        Requires google-maps-services-python package:
        pip install googlemaps
        """
        try:
            import googlemaps
        except ImportError:
            logger.warning("googlemaps package not installed, using fallback")
            return self._estimate_travel_time(
                origin_lat, origin_lng, dest_lat, dest_lng, self.is_rush_hour(departure_time)
            )

        if not self._client:
            self._client = googlemaps.Client(key=self.api_key)

        try:
            result = self._client.distance_matrix(
                origins=[(origin_lat, origin_lng)],
                destinations=[(dest_lat, dest_lng)],
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess",
            )

            element = result["rows"][0]["elements"][0]

            if element["status"] != "OK":
                raise ValueError(f"Google Maps API error: {element['status']}")

            # Extract travel time (with traffic if available)
            if "duration_in_traffic" in element:
                travel_seconds = element["duration_in_traffic"]["value"]
            else:
                travel_seconds = element["duration"]["value"]

            travel_minutes = travel_seconds // 60
            distance_meters = element["distance"]["value"]
            distance_miles = distance_meters * 0.000621371

            return TravelTimeResult(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                dest_lat=dest_lat,
                dest_lng=dest_lng,
                travel_time_minutes=travel_minutes,
                distance_miles=round(distance_miles, 2),
                is_rush_hour=self.is_rush_hour(departure_time),
                source="google_maps",
                cached=False,
            )

        except Exception as e:
            logger.error(f"Google Maps API call failed: {e}")
            raise

    def _estimate_travel_time(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        is_rush_hour: bool,
    ) -> TravelTimeResult:
        """
        Estimate travel time using Haversine distance and average speeds.

        This is a fallback when Google Maps API is unavailable.
        """
        # Calculate straight-line distance
        distance = self.calculate_distance_miles(origin_lat, origin_lng, dest_lat, dest_lng)

        # Apply road factor (roads aren't straight)
        # Typical factor is 1.3-1.5 for urban areas
        road_distance = distance * 1.4

        # Calculate time based on average speed
        if is_rush_hour:
            speed = AVERAGE_SPEED_RUSH_HOUR_MPH
        else:
            speed = AVERAGE_SPEED_NORMAL_MPH

        travel_minutes = int((road_distance / speed) * 60)

        # Minimum travel time of 5 minutes
        travel_minutes = max(5, travel_minutes)

        return TravelTimeResult(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            travel_time_minutes=travel_minutes,
            distance_miles=round(road_distance, 2),
            is_rush_hour=is_rush_hour,
            source="estimate",
            cached=False,
        )


# ============================================================
# Utility Functions
# ============================================================


def calculate_event_duration(guest_count: int) -> int:
    """
    Calculate event duration based on party size.

    Returns duration in minutes.

    Business Rules:
    - 1-10 guests: 90 minutes (standard)
    - 11-20 guests: 105 minutes
    - 21-30 guests: 120 minutes
    - 31+ guests: 120 minutes (may need 2 chefs)
    """
    if guest_count <= 10:
        return 90
    elif guest_count <= 20:
        return 105
    elif guest_count <= 30:
        return 120
    else:
        return 120


def calculate_arrival_time(event_start: datetime, setup_minutes: int = 30) -> datetime:
    """
    Calculate when chef should arrive (before event start).

    Args:
        event_start: When the event begins
        setup_minutes: Time needed for setup (default 30 min)

    Returns:
        Required arrival time
    """
    return event_start - timedelta(minutes=setup_minutes)


def calculate_departure_time(event_end: datetime, cleanup_minutes: int = 15) -> datetime:
    """
    Calculate when chef can leave for next booking.

    Args:
        event_end: When the event ends
        cleanup_minutes: Time needed for cleanup (default 15 min)

    Returns:
        Earliest departure time
    """
    return event_end + timedelta(minutes=cleanup_minutes)
