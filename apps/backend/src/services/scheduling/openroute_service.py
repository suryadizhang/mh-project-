"""
OpenRouteService API Client
===========================

Backup API for travel time/distance calculations when Google Maps is unavailable.
OpenRouteService provides a free tier with 2000 requests/day.

API Documentation: https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get

Free Tier Limits:
- 2000 requests/day
- 40 requests/minute
- Driving-car profile available

Setup:
1. Sign up at https://openrouteservice.org/dev/#/signup
2. Get API key from dashboard
3. Add to environment: OPENROUTE_API_KEY=your_key

Usage:
    from services.scheduling.openroute_service import OpenRouteService

    ors = OpenRouteService(api_key="your_key")
    result = await ors.get_driving_distance(
        origin_lat=37.5485, origin_lng=-121.9886,  # Fremont
        dest_lat=37.7749, dest_lng=-122.4194       # SF
    )
    # Returns: {"distance_miles": 35.2, "travel_time_minutes": 45, "source": "openroute"}

Note: This is a FALLBACK only. Primary should be Google Maps for accuracy.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# OpenRouteService API endpoint
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# Conversion factors
METERS_TO_MILES = 0.000621371
SECONDS_TO_MINUTES = 1 / 60

# Timeouts
REQUEST_TIMEOUT_SECONDS = 10


@dataclass
class OpenRouteResult:
    """Result from OpenRouteService API call."""

    distance_miles: float
    travel_time_minutes: int
    source: str = "openroute"
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Returns True if the API call was successful (no error)."""
        return self.error is None

    @property
    def duration_minutes(self) -> int:
        """Alias for travel_time_minutes for compatibility."""
        return self.travel_time_minutes


class OpenRouteServiceError(Exception):
    """Exception for OpenRouteService API errors."""

    pass


class OpenRouteService:
    """
    OpenRouteService API client for travel distance/time calculations.

    Used as backup when Google Maps API fails or is unavailable.

    Advantages over Google:
    - Free tier (2000 req/day)
    - Open source routing data (OpenStreetMap)

    Disadvantages:
    - Less accurate traffic data
    - Fewer API features
    - May have routing gaps in some areas
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouteService client.

        Args:
            api_key: OpenRouteService API key. If not provided, will try
                    to get from environment variable OPENROUTE_API_KEY.
        """
        self.api_key = api_key
        if not self.api_key:
            import os

            self.api_key = os.getenv("OPENROUTE_API_KEY")

        if not self.api_key:
            logger.warning(
                "⚠️ OpenRouteService API key not configured. "
                "Backup travel calculations will not work. "
                "Set OPENROUTE_API_KEY environment variable."
            )

    async def get_driving_distance(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> OpenRouteResult:
        """
        Get driving distance and time between two points.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            OpenRouteResult with distance and time

        Raises:
            OpenRouteServiceError: If API call fails
        """
        if not self.api_key:
            logger.error("❌ OpenRouteService API key not configured")
            return OpenRouteResult(
                distance_miles=0, travel_time_minutes=0, error="API key not configured"
            )

        # ORS uses [lng, lat] format (GeoJSON standard)
        start = f"{origin_lng},{origin_lat}"
        end = f"{dest_lng},{dest_lat}"

        url = f"{ORS_BASE_URL}?start={start}&end={end}"

        headers = {
            "Authorization": self.api_key,
            "Accept": "application/json, application/geo+json",
        }

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                logger.debug(
                    f"🌍 OpenRouteService request: ({origin_lat}, {origin_lng}) → ({dest_lat}, {dest_lng})"
                )

                response = await client.get(url, headers=headers)

                if response.status_code == 401:
                    logger.error("❌ OpenRouteService: Invalid API key")
                    return OpenRouteResult(
                        distance_miles=0, travel_time_minutes=0, error="Invalid API key"
                    )

                if response.status_code == 429:
                    logger.warning("⚠️ OpenRouteService: Rate limit exceeded")
                    return OpenRouteResult(
                        distance_miles=0, travel_time_minutes=0, error="Rate limit exceeded"
                    )

                if response.status_code != 200:
                    logger.error(
                        f"❌ OpenRouteService error: {response.status_code} - {response.text}"
                    )
                    return OpenRouteResult(
                        distance_miles=0,
                        travel_time_minutes=0,
                        error=f"API error: {response.status_code}",
                    )

                data = response.json()

                # Parse GeoJSON response
                # Structure: features[0].properties.summary.{distance, duration}
                if "features" not in data or len(data["features"]) == 0:
                    logger.warning("⚠️ OpenRouteService: No route found")
                    return OpenRouteResult(
                        distance_miles=0, travel_time_minutes=0, error="No route found"
                    )

                summary = data["features"][0]["properties"]["summary"]

                distance_meters = summary.get("distance", 0)
                duration_seconds = summary.get("duration", 0)

                distance_miles = distance_meters * METERS_TO_MILES
                travel_time_minutes = int(duration_seconds * SECONDS_TO_MINUTES)

                logger.info(
                    f"✅ OpenRouteService: {distance_miles:.1f} miles, "
                    f"{travel_time_minutes} minutes"
                )

                return OpenRouteResult(
                    distance_miles=round(distance_miles, 1),
                    travel_time_minutes=max(1, travel_time_minutes),  # Min 1 minute
                    source="openroute",
                )

        except httpx.TimeoutException:
            logger.warning("⚠️ OpenRouteService: Request timeout")
            return OpenRouteResult(distance_miles=0, travel_time_minutes=0, error="Request timeout")
        except httpx.RequestError as e:
            logger.error(f"❌ OpenRouteService request error: {e}")
            return OpenRouteResult(
                distance_miles=0, travel_time_minutes=0, error=f"Request error: {e}"
            )
        except Exception as e:
            logger.error(f"❌ OpenRouteService unexpected error: {e}")
            return OpenRouteResult(
                distance_miles=0, travel_time_minutes=0, error=f"Unexpected error: {e}"
            )

    def is_configured(self) -> bool:
        """Check if the service is properly configured with an API key."""
        return bool(self.api_key)


async def get_openroute_service() -> OpenRouteService:
    """
    Factory function to get configured OpenRouteService.

    Returns:
        OpenRouteService instance
    """
    import os

    api_key = os.getenv("OPENROUTE_API_KEY")
    return OpenRouteService(api_key=api_key)
