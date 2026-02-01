"""
Travel Time Service - Multi-API Integration with Failsafe Chain
================================================================

Calculates travel time between locations using a failsafe chain:
1. Cache (LRU in-memory + Database)
2. Google Maps Distance Matrix API (primary)
3. OpenRouteService API (backup)
4. Human escalation (last resort) - NO Haversine for travel fee accuracy

CRITICAL: For travel fee calculations, we NEVER use Haversine estimates.
Customer pays real money based on these calculations - accuracy is mandatory.

Features:
- Dual-layer caching (LRU + DB) via TravelCacheService
- Google Maps API with retry logic
- OpenRouteService backup (free tier: 2000 req/day)
- Rush hour awareness (1.5x multiplier Mon-Fri 3-7PM)
- Graceful degradation to human escalation

Architecture:
    TravelTimeService
        ├─→ TravelCacheService (LRU + DB)
        ├─→ Google Maps API (primary, with retry)
        ├─→ OpenRouteService (backup, with retry)
        └─→ Error result for human escalation

Note: Haversine is ONLY used for:
- Quick distance checks (is venue within service area)
- Smart scheduling chef optimizer (adjustable by chef count)
- NOT for travel fee calculations shown to customers
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import NamedTuple, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.scheduling.openroute_service import OpenRouteService
from services.scheduling.travel_cache_service import (
    TravelCacheEntry,
    TravelCacheService,
)

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
    source: str  # 'google_maps', 'openroute', 'cache', 'error'
    cached: bool = False
    error: Optional[str] = None  # Set when source='error'

    @property
    def travel_time_with_buffer(self) -> int:
        """Travel time plus 15 min buffer for parking/setup."""
        return self.travel_time_minutes + 15

    @property
    def duration_minutes(self) -> int:
        """Alias for travel_time_minutes for compatibility."""
        return self.travel_time_minutes

    @property
    def is_valid(self) -> bool:
        """Check if this result has valid data (not an error)."""
        return self.source != "error" and self.error is None


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

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0

# API timeout
API_TIMEOUT_SECONDS = 10

# Haversine constants (for quick distance checks only)
AVERAGE_SPEED_NORMAL_MPH = 35
AVERAGE_SPEED_RUSH_HOUR_MPH = 20

# Cache settings
CACHE_EXPIRY_HOURS = 168  # 7 days


# ============================================================
# Travel Time Service
# ============================================================


class TravelTimeService:
    """
    Calculates travel time between locations with failsafe chain.

    Failsafe Priority (for travel fee calculation):
    1. Cache (LRU in-memory → Database)
    2. Google Maps Distance Matrix API (with retry)
    3. OpenRouteService API (backup, with retry)
    4. Error result → triggers human escalation in frontend

    IMPORTANT: NO Haversine fallback for travel fee calculations.
    Haversine is inaccurate for driving distances and time.
    If all APIs fail, we return an error for human escalation.

    For scheduling/optimization use cases, Haversine can be used
    via the separate calculate_distance_miles() method.
    """

    def __init__(
        self,
        google_maps_api_key: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
        openroute_api_key: Optional[str] = None,
    ):
        """
        Initialize the travel time service.

        Args:
            google_maps_api_key: Google Maps API key
            db_session: Database session for caching
            openroute_api_key: OpenRouteService API key (backup)
        """
        self.api_key = google_maps_api_key
        self.db = db_session
        self._client = None

        # Initialize cache service
        self._cache_service = TravelCacheService(db_session) if db_session else None

        # Initialize backup API
        self._openroute = OpenRouteService(api_key=openroute_api_key)

        # Track API health for smart routing
        self._google_maps_healthy = True
        self._openroute_healthy = True

    async def get_travel_time(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Get travel time between two locations using failsafe chain.

        Priority:
        1. Cache (LRU → DB)
        2. Google Maps API (with retry)
        3. OpenRouteService (backup, with retry)
        4. Error result (triggers human escalation)

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            departure_time: When the trip will start (for rush hour check)

        Returns:
            TravelTimeResult with travel time, distance, and metadata
            If all APIs fail, returns result with source='error'
        """
        is_rush = self.is_rush_hour(departure_time)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: Check cache first (fastest)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self._cache_service:
            cached = await self._cache_service.get(
                origin_lat, origin_lng, dest_lat, dest_lng, is_rush
            )
            if cached:
                logger.debug(
                    f"📦 Cache hit: {cached.distance_miles:.1f} mi, {cached.travel_time_minutes} min"
                )
                return TravelTimeResult(
                    origin_lat=origin_lat,
                    origin_lng=origin_lng,
                    dest_lat=dest_lat,
                    dest_lng=dest_lng,
                    travel_time_minutes=cached.travel_time_minutes,
                    distance_miles=cached.distance_miles,
                    is_rush_hour=is_rush,
                    source=f"cache_{cached.source}",  # e.g., "cache_google_maps"
                    cached=True,
                )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: Try Google Maps API (primary)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self.api_key and self._google_maps_healthy:
            result = await self._call_google_maps_with_retry(
                origin_lat, origin_lng, dest_lat, dest_lng, departure_time
            )
            if result and result.source == "google_maps":
                # Success! Cache it and return
                await self._save_to_cache(result, is_rush)
                return result
            # Google Maps failed, mark unhealthy temporarily
            self._google_maps_healthy = False
            logger.warning("⚠️ Google Maps API unhealthy, trying backup")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Try OpenRouteService (backup)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self._openroute.is_configured() and self._openroute_healthy:
            result = await self._call_openroute_with_retry(
                origin_lat, origin_lng, dest_lat, dest_lng, is_rush
            )
            if result and result.source == "openroute":
                # Success! Cache it and return
                await self._save_to_cache(result, is_rush)
                return result
            # OpenRouteService failed
            self._openroute_healthy = False
            logger.warning("⚠️ OpenRouteService also failed")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 4: All APIs failed → Return error for human escalation
        # NO HAVERSINE FALLBACK - accuracy is critical for travel fees
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.error(
            f"❌ All travel APIs failed for ({origin_lat}, {origin_lng}) → "
            f"({dest_lat}, {dest_lng}). Returning error for human escalation."
        )

        return TravelTimeResult(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            travel_time_minutes=0,
            distance_miles=0,
            is_rush_hour=is_rush,
            source="error",
            cached=False,
            error="Travel calculation unavailable. Please call (916) 740-8768 for assistance.",
        )

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

    def calculate_distance_miles(
        self, lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
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
    # Private Methods - API Calls with Retry
    # ============================================================

    async def _call_google_maps_with_retry(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
    ) -> Optional[TravelTimeResult]:
        """
        Call Google Maps API with retry logic.

        Args:
            origin_lat, origin_lng: Origin coordinates
            dest_lat, dest_lng: Destination coordinates
            departure_time: When travel starts

        Returns:
            TravelTimeResult on success, None on failure
        """
        delay = RETRY_DELAY_SECONDS

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = await self._call_google_maps(
                    origin_lat, origin_lng, dest_lat, dest_lng, departure_time
                )
                # Mark API as healthy on success
                self._google_maps_healthy = True
                return result

            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(
                        f"🔄 Google Maps attempt {attempt + 1}/{MAX_RETRIES + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= RETRY_BACKOFF_MULTIPLIER
                else:
                    logger.error(
                        f"❌ Google Maps failed after {MAX_RETRIES + 1} attempts: {e}"
                    )

        return None

    async def _call_openroute_with_retry(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        is_rush_hour: bool,
    ) -> Optional[TravelTimeResult]:
        """
        Call OpenRouteService API with retry logic.

        Args:
            origin_lat, origin_lng: Origin coordinates
            dest_lat, dest_lng: Destination coordinates
            is_rush_hour: Whether it's during rush hour

        Returns:
            TravelTimeResult on success, None on failure
        """
        delay = RETRY_DELAY_SECONDS

        for attempt in range(MAX_RETRIES + 1):
            try:
                ors_result = await self._openroute.get_driving_distance(
                    origin_lat, origin_lng, dest_lat, dest_lng
                )

                if not ors_result.success:
                    raise Exception(ors_result.error or "OpenRouteService failed")

                # Apply rush hour multiplier if needed
                travel_minutes = ors_result.duration_minutes
                if is_rush_hour:
                    travel_minutes = int(travel_minutes * RUSH_HOUR_MULTIPLIER)

                # Mark API as healthy on success
                self._openroute_healthy = True

                return TravelTimeResult(
                    origin_lat=origin_lat,
                    origin_lng=origin_lng,
                    dest_lat=dest_lat,
                    dest_lng=dest_lng,
                    travel_time_minutes=travel_minutes,
                    distance_miles=ors_result.distance_miles,
                    is_rush_hour=is_rush_hour,
                    source="openroute",
                    cached=False,
                )

            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(
                        f"🔄 OpenRouteService attempt {attempt + 1}/{MAX_RETRIES + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= RETRY_BACKOFF_MULTIPLIER
                else:
                    logger.error(
                        f"❌ OpenRouteService failed after {MAX_RETRIES + 1} attempts: {e}"
                    )

        return None

    async def _save_to_cache(
        self, result: TravelTimeResult, is_rush_hour: bool
    ) -> None:
        """
        Save travel time result to cache (both LRU and DB).

        Args:
            result: The travel result to cache
            is_rush_hour: Whether this was a rush hour calculation
        """
        if not self._cache_service:
            return

        try:
            entry = TravelCacheEntry(
                travel_time_minutes=result.travel_time_minutes,
                distance_miles=result.distance_miles,
                is_rush_hour=is_rush_hour,
                source=result.source,
            )
            await self._cache_service.set(
                origin_lat=result.origin_lat,
                origin_lng=result.origin_lng,
                dest_lat=result.dest_lat,
                dest_lng=result.dest_lng,
                is_rush_hour=is_rush_hour,
                entry=entry,
            )
            logger.debug(
                f"💾 Cached: {result.origin_lat:.3f},{result.origin_lng:.3f} → "
                f"{result.dest_lat:.3f},{result.dest_lng:.3f} = {result.distance_miles:.1f} mi"
            )
        except Exception as e:
            # Cache failures should not break the flow
            logger.warning(f"⚠️ Cache save failed (non-blocking): {e}")

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

        IMPORTANT: This method does NOT fall back to Haversine estimation.
        Per user requirement, travel fees MUST use real API data or escalate to human.
        Haversine is only acceptable for smart scheduling (chef assignment).

        Requires google-maps-services-python package:
        pip install googlemaps

        Raises:
            ImportError: If googlemaps package not installed
            ValueError: If API returns error status
            Exception: On any other API failure
        """
        try:
            import googlemaps
        except ImportError:
            logger.error(
                "❌ googlemaps package not installed - cannot calculate travel fee"
            )
            raise ImportError(
                "googlemaps package not installed. "
                "Install with: pip install googlemaps"
            )

        if not self._client:
            if not self.api_key:
                raise ValueError("Google Maps API key not configured")
            self._client = googlemaps.Client(key=self.api_key)

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

    def _estimate_travel_time_scheduling_only(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        is_rush_hour: bool,
    ) -> TravelTimeResult:
        """
        Estimate travel time using Haversine distance and average speeds.

        ⚠️ WARNING: FOR SMART SCHEDULING (ChefOptimizer) ONLY!
        ⚠️ NEVER USE THIS FOR TRAVEL FEE CALCULATION!

        This method uses Haversine distance which is NOT accurate for travel fees.
        Travel fees MUST use real API data (Google Maps or backup API) or
        escalate to human for manual calculation.

        This estimation is acceptable for:
        - Chef assignment decisions (which chef is closest)
        - Feasibility checks (can a chef make it in time?)
        - Schedule optimization (reducing total drive time)

        The logic should be adjustable based on:
        - Number of chefs available that day
        - Historical accuracy data
        - Geographic region characteristics
        """
        # Calculate straight-line distance (Haversine)
        distance = self.calculate_distance_miles(
            origin_lat, origin_lng, dest_lat, dest_lng
        )

        # Apply road factor (roads aren't straight)
        # Typical factor is 1.3-1.5 for urban areas
        # This factor could be made adjustable per region
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


def calculate_arrival_time(event_start: datetime, setup_minutes: int = 60) -> datetime:
    """
    Calculate when chef should arrive (before event start).

    Args:
        event_start: When the event begins
        setup_minutes: Time needed for setup (default 60 min - accounts for traffic)

    Returns:
        Required arrival time
    """
    return event_start - timedelta(minutes=setup_minutes)


def calculate_departure_time(
    event_end: datetime, cleanup_minutes: int = 15
) -> datetime:
    """
    Calculate when chef can leave for next booking.

    Args:
        event_end: When the event ends
        cleanup_minutes: Time needed for cleanup (default 15 min)

    Returns:
        Earliest departure time
    """
    return event_end + timedelta(minutes=cleanup_minutes)
