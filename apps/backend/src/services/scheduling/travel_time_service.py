"""
Travel Time Service

Calculates travel time between locations using Google Maps API.
Includes rush hour awareness and caching.

Business Rules:
- Rush hour: Mon-Fri 3:00 PM - 7:00 PM = travel time × 1.5
- Cache results for 7 days (routes don't change often)
- Buffer: 15 minutes added to travel time for parking/setup
"""

import os
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class Coordinates:
    """Geographic coordinates"""

    lat: Decimal
    lng: Decimal

    def to_string(self) -> str:
        """Format for Google Maps API"""
        return f"{self.lat},{self.lng}"


@dataclass
class TravelTimeResult:
    """Result from travel time calculation"""

    origin: Coordinates
    destination: Coordinates
    base_duration_minutes: int  # Without traffic
    traffic_duration_minutes: int  # With traffic (may include rush hour)
    distance_km: float
    is_rush_hour: bool
    route_summary: Optional[str] = None
    from_cache: bool = False


# Rush hour configuration
RUSH_HOUR_START = time(15, 0)  # 3:00 PM
RUSH_HOUR_END = time(19, 0)  # 7:00 PM
RUSH_HOUR_MULTIPLIER = 1.5
RUSH_HOUR_DAYS = {0, 1, 2, 3, 4}  # Monday=0 to Friday=4

# Cache settings
CACHE_TTL_DAYS = 7


class TravelTimeService:
    """
    Calculate travel time between locations with Google Maps integration.

    Includes:
    - Rush hour awareness (Mon-Fri 3-7 PM = ×1.5)
    - Database caching (7 day TTL)
    - Fallback estimation when API unavailable
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        google_maps_api_key: Optional[str] = None,
    ):
        self.session = session
        self.api_key = google_maps_api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        self._google_client = None

    # =========================================================================
    # RUSH HOUR LOGIC
    # =========================================================================

    @staticmethod
    def is_rush_hour(dt: datetime) -> bool:
        """
        Check if datetime falls in rush hour.

        Rush hour: Monday-Friday, 3:00 PM - 7:00 PM

        Args:
            dt: Datetime to check

        Returns:
            True if rush hour, False otherwise
        """
        # Check if weekday (Monday=0 to Friday=4)
        if dt.weekday() not in RUSH_HOUR_DAYS:
            return False

        # Check if within rush hour times
        current_time = dt.time()
        return RUSH_HOUR_START <= current_time < RUSH_HOUR_END

    @staticmethod
    def apply_rush_hour_multiplier(base_minutes: int, is_rush: bool) -> int:
        """
        Apply rush hour multiplier to travel time.

        Args:
            base_minutes: Base travel time
            is_rush: Whether it's rush hour

        Returns:
            Adjusted travel time (×1.5 during rush hour)
        """
        if is_rush:
            return int(base_minutes * RUSH_HOUR_MULTIPLIER)
        return base_minutes

    # =========================================================================
    # MAIN CALCULATION
    # =========================================================================

    async def get_travel_time(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Get travel time between two locations.

        Checks cache first, then falls back to API or estimation.

        Args:
            origin: Starting coordinates
            destination: Ending coordinates
            departure_time: When travel starts (for rush hour calculation)

        Returns:
            TravelTimeResult with duration, distance, and rush hour info
        """
        is_rush = self.is_rush_hour(departure_time)

        # Try cache first
        cached = await self._get_from_cache(
            origin, destination, departure_time.hour, departure_time.weekday()
        )
        if cached:
            cached.is_rush_hour = is_rush
            cached.from_cache = True
            return cached

        # Try Google Maps API
        if self.api_key:
            result = await self._fetch_from_google_maps(origin, destination, departure_time)
            if result:
                # Cache the result
                await self._save_to_cache(result, departure_time)
                return result

        # Fallback: estimate based on distance
        return await self._estimate_travel_time(origin, destination, departure_time, is_rush)

    # =========================================================================
    # CACHE OPERATIONS
    # =========================================================================

    async def _get_from_cache(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_hour: int,
        day_of_week: int,
    ) -> Optional[TravelTimeResult]:
        """Check cache for existing travel time."""
        if not self.session:
            return None

        try:
            query = text(
                """
                SELECT base_duration_minutes, traffic_duration_minutes, 
                       distance_km, route_summary, is_rush_hour
                FROM ops.travel_time_cache
                WHERE ROUND(origin_lat::numeric, 2) = ROUND(:origin_lat, 2)
                  AND ROUND(origin_lng::numeric, 2) = ROUND(:origin_lng, 2)
                  AND ROUND(dest_lat::numeric, 2) = ROUND(:dest_lat, 2)
                  AND ROUND(dest_lng::numeric, 2) = ROUND(:dest_lng, 2)
                  AND (departure_hour = :hour OR departure_hour IS NULL)
                  AND expires_at > NOW()
                ORDER BY departure_hour NULLS LAST
                LIMIT 1
            """
            )

            result = await self.session.execute(
                query,
                {
                    "origin_lat": float(origin.lat),
                    "origin_lng": float(origin.lng),
                    "dest_lat": float(destination.lat),
                    "dest_lng": float(destination.lng),
                    "hour": departure_hour,
                },
            )
            row = result.fetchone()

            if row:
                # Update hit count
                await self._update_cache_hit_count(origin, destination)

                return TravelTimeResult(
                    origin=origin,
                    destination=destination,
                    base_duration_minutes=row.base_duration_minutes,
                    traffic_duration_minutes=row.traffic_duration_minutes
                    or row.base_duration_minutes,
                    distance_km=float(row.distance_km) if row.distance_km else 0.0,
                    is_rush_hour=row.is_rush_hour,
                    route_summary=row.route_summary,
                    from_cache=True,
                )
        except Exception:
            pass

        return None

    async def _save_to_cache(
        self,
        result: TravelTimeResult,
        departure_time: datetime,
    ) -> None:
        """Save travel time result to cache."""
        if not self.session:
            return

        try:
            query = text(
                """
                INSERT INTO ops.travel_time_cache (
                    origin_lat, origin_lng, dest_lat, dest_lng,
                    departure_hour, day_of_week, is_rush_hour,
                    base_duration_minutes, traffic_duration_minutes,
                    distance_km, route_summary, expires_at
                ) VALUES (
                    :origin_lat, :origin_lng, :dest_lat, :dest_lng,
                    :hour, :dow, :is_rush,
                    :base_dur, :traffic_dur,
                    :distance, :route, NOW() + INTERVAL ':ttl days'
                )
                ON CONFLICT DO NOTHING
            """
            )

            await self.session.execute(
                query,
                {
                    "origin_lat": float(result.origin.lat),
                    "origin_lng": float(result.origin.lng),
                    "dest_lat": float(result.destination.lat),
                    "dest_lng": float(result.destination.lng),
                    "hour": departure_time.hour,
                    "dow": departure_time.weekday(),
                    "is_rush": result.is_rush_hour,
                    "base_dur": result.base_duration_minutes,
                    "traffic_dur": result.traffic_duration_minutes,
                    "distance": result.distance_km,
                    "route": result.route_summary,
                    "ttl": CACHE_TTL_DAYS,
                },
            )
            await self.session.commit()
        except Exception:
            pass

    async def _update_cache_hit_count(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> None:
        """Increment cache hit count for analytics."""
        if not self.session:
            return

        try:
            query = text(
                """
                UPDATE ops.travel_time_cache
                SET hit_count = hit_count + 1
                WHERE ROUND(origin_lat::numeric, 2) = ROUND(:origin_lat, 2)
                  AND ROUND(origin_lng::numeric, 2) = ROUND(:origin_lng, 2)
                  AND ROUND(dest_lat::numeric, 2) = ROUND(:dest_lat, 2)
                  AND ROUND(dest_lng::numeric, 2) = ROUND(:dest_lng, 2)
            """
            )
            await self.session.execute(
                query,
                {
                    "origin_lat": float(origin.lat),
                    "origin_lng": float(origin.lng),
                    "dest_lat": float(destination.lat),
                    "dest_lng": float(destination.lng),
                },
            )
        except Exception:
            pass

    # =========================================================================
    # GOOGLE MAPS INTEGRATION
    # =========================================================================

    async def _fetch_from_google_maps(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime,
    ) -> Optional[TravelTimeResult]:
        """
        Fetch travel time from Google Maps Directions API.

        Note: Requires GOOGLE_MAPS_API_KEY environment variable.
        """
        if not self.api_key:
            return None

        try:
            import httpx

            # Use Distance Matrix API for travel time
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": origin.to_string(),
                "destinations": destination.to_string(),
                "key": self.api_key,
                "departure_time": int(departure_time.timestamp()),
                "traffic_model": "best_guess",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()

            if data.get("status") != "OK":
                return None

            element = data["rows"][0]["elements"][0]
            if element.get("status") != "OK":
                return None

            # Extract duration and distance
            base_duration = element["duration"]["value"] // 60  # seconds to minutes
            traffic_duration = (
                element.get("duration_in_traffic", {}).get("value", element["duration"]["value"])
                // 60
            )
            distance = element["distance"]["value"] / 1000  # meters to km

            is_rush = self.is_rush_hour(departure_time)

            return TravelTimeResult(
                origin=origin,
                destination=destination,
                base_duration_minutes=base_duration,
                traffic_duration_minutes=traffic_duration,
                distance_km=distance,
                is_rush_hour=is_rush,
                route_summary=None,
                from_cache=False,
            )

        except Exception:
            return None

    # =========================================================================
    # FALLBACK ESTIMATION
    # =========================================================================

    async def _estimate_travel_time(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime,
        is_rush: bool,
    ) -> TravelTimeResult:
        """
        Estimate travel time based on straight-line distance.

        Fallback when Google Maps API is unavailable.

        Assumptions:
        - Average speed: 40 km/h in normal conditions
        - 1.3x distance multiplier for road routing
        """
        import math

        # Calculate straight-line distance using Haversine formula
        R = 6371  # Earth's radius in km

        lat1 = math.radians(float(origin.lat))
        lat2 = math.radians(float(destination.lat))
        dlat = math.radians(float(destination.lat) - float(origin.lat))
        dlng = math.radians(float(destination.lng) - float(origin.lng))

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        straight_distance = R * c

        # Apply routing multiplier (roads aren't straight)
        estimated_distance = straight_distance * 1.3

        # Calculate time at average 40 km/h
        base_minutes = int((estimated_distance / 40) * 60)
        base_minutes = max(base_minutes, 5)  # Minimum 5 minutes

        # Apply rush hour
        traffic_minutes = self.apply_rush_hour_multiplier(base_minutes, is_rush)

        return TravelTimeResult(
            origin=origin,
            destination=destination,
            base_duration_minutes=base_minutes,
            traffic_duration_minutes=traffic_minutes,
            distance_km=round(estimated_distance, 2),
            is_rush_hour=is_rush,
            route_summary="Estimated (API unavailable)",
            from_cache=False,
        )

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    async def get_travel_time_simple(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Convenience method with simple float coordinates.
        """
        origin = Coordinates(Decimal(str(origin_lat)), Decimal(str(origin_lng)))
        destination = Coordinates(Decimal(str(dest_lat)), Decimal(str(dest_lng)))
        return await self.get_travel_time(origin, destination, departure_time)
