"""
Unit Tests for OpenRouteService

Tests the backup API client for travel calculations when Google Maps is unavailable.

Run with: pytest tests/unit/test_openroute_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

# Import the service and types
from services.scheduling.openroute_service import (
    OpenRouteService,
    OpenRouteResult,
    ORS_BASE_URL,
    METERS_TO_MILES,
    SECONDS_TO_MINUTES,
)


class TestOpenRouteResult:
    """Test OpenRouteResult dataclass"""

    def test_create_result(self):
        """Test creating an OpenRouteResult with valid data"""
        result = OpenRouteResult(
            distance_miles=27.96,
            travel_time_minutes=45,
            source="openroute",
        )

        assert result.distance_miles == 27.96
        assert result.travel_time_minutes == 45
        assert result.source == "openroute"
        assert result.error is None

    def test_result_with_error(self):
        """Test creating an OpenRouteResult with error"""
        result = OpenRouteResult(
            distance_miles=0,
            travel_time_minutes=0,
            error="API key not configured",
        )

        assert result.distance_miles == 0
        assert result.travel_time_minutes == 0
        assert result.error == "API key not configured"

    def test_result_default_source(self):
        """Test that default source is 'openroute'"""
        result = OpenRouteResult(
            distance_miles=10.5,
            travel_time_minutes=15,
        )
        assert result.source == "openroute"


class TestOpenRouteServiceConfiguration:
    """Test OpenRouteService configuration and initialization"""

    def test_is_configured_with_api_key(self):
        """Test is_configured returns True when API key is set"""
        service = OpenRouteService(api_key="test_api_key_123")
        assert service.is_configured() is True

    def test_is_configured_without_api_key(self):
        """Test is_configured returns False when no API key"""
        with patch.dict("os.environ", {}, clear=True):
            # Patch environ to not have OPENROUTE_API_KEY
            with patch("os.getenv", return_value=None):
                service = OpenRouteService(api_key=None)
                service.api_key = None  # Force no key
                assert service.is_configured() is False

    def test_is_configured_with_empty_api_key(self):
        """Test is_configured returns False when API key is empty string"""
        service = OpenRouteService(api_key="")
        assert service.is_configured() is False

    def test_service_uses_correct_base_url_constant(self):
        """Test that ORS_BASE_URL constant is correct"""
        assert "openrouteservice.org" in ORS_BASE_URL
        assert "v2/directions" in ORS_BASE_URL
        assert "driving-car" in ORS_BASE_URL

    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key"""
        service = OpenRouteService(api_key="my_explicit_key")
        assert service.api_key == "my_explicit_key"

    def test_init_without_key_reads_env(self):
        """Test initialization reads from environment when no key provided"""
        with patch("os.getenv", return_value="env_api_key_456"):
            service = OpenRouteService()
            assert service.api_key == "env_api_key_456"


@pytest.mark.asyncio
class TestOpenRouteServiceGetDrivingDistance:
    """Test get_driving_distance method"""

    @pytest.fixture
    def service_with_key(self):
        """Create an OpenRouteService with a mock API key"""
        return OpenRouteService(api_key="test_api_key_123")

    async def test_get_driving_distance_success(self, service_with_key):
        """Test successful API call returns correct result"""
        # Mock successful API response (GeoJSON format)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "summary": {
                            "distance": 45000.0,  # 45km in meters
                            "duration": 2700.0,  # 45 minutes in seconds
                        }
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error is None
            assert result.distance_miles > 0
            assert result.travel_time_minutes > 0
            assert result.source == "openroute"

    async def test_get_driving_distance_not_configured(self):
        """Test API call returns error when not configured"""
        service = OpenRouteService(api_key=None)
        service.api_key = None  # Force no key

        result = await service.get_driving_distance(
            origin_lat=37.5485,
            origin_lng=-121.9886,
            dest_lat=37.7749,
            dest_lng=-122.4194,
        )

        assert result.error == "API key not configured"
        assert result.distance_miles == 0
        assert result.travel_time_minutes == 0

    async def test_get_driving_distance_401_invalid_key(self, service_with_key):
        """Test 401 response for invalid API key"""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error == "Invalid API key"
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0

    async def test_get_driving_distance_429_rate_limit(self, service_with_key):
        """Test 429 response for rate limit exceeded"""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error == "Rate limit exceeded"
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0

    async def test_get_driving_distance_500_server_error(self, service_with_key):
        """Test 500 response for server error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert "API error: 500" in result.error
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0

    async def test_get_driving_distance_timeout(self, service_with_key):
        """Test timeout handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error == "Request timeout"
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0

    async def test_get_driving_distance_no_route_found(self, service_with_key):
        """Test response with no route (empty features)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"features": []}  # Empty features

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error == "No route found"
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0

    async def test_get_driving_distance_request_exception(self, service_with_key):
        """Test general request exception handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value = mock_client

            result = await service_with_key.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert "Request error" in result.error
            assert result.distance_miles == 0
            assert result.travel_time_minutes == 0


@pytest.mark.asyncio
class TestOpenRouteServiceCoordinateFormat:
    """Test that coordinates are sent in correct format"""

    async def test_coordinates_sent_as_lng_lat(self):
        """Test that coordinates are sent in lng,lat format (GeoJSON standard)"""
        service = OpenRouteService(api_key="test_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "summary": {
                            "distance": 10000.0,
                            "duration": 600.0,
                        }
                    }
                }
            ]
        }

        captured_url = None

        async def capture_get(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            return mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = capture_get
            mock_client_class.return_value = mock_client

            await service.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            # Verify URL contains lng,lat format (not lat,lng)
            assert captured_url is not None
            # Origin should be lng,lat = -121.9886,37.5485
            assert "-121.9886,37.5485" in captured_url
            # Dest should be lng,lat = -122.4194,37.7749
            assert "-122.4194,37.7749" in captured_url


@pytest.mark.asyncio
class TestOpenRouteServiceIntegrationPatterns:
    """Test realistic integration scenarios"""

    async def test_short_distance_calculation(self):
        """Test calculation for short distance (~5 miles)"""
        service = OpenRouteService(api_key="test_key")

        # 8km ≈ 5 miles, 600s = 10 minutes
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "summary": {
                            "distance": 8000.0,  # 8km in meters
                            "duration": 600.0,  # 10 minutes
                        }
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.5600,
                dest_lng=-122.0000,
            )

            assert result.error is None
            # 8000m * 0.000621371 ≈ 4.97 miles, rounded to 5.0
            assert result.distance_miles == pytest.approx(5.0, abs=0.5)
            assert result.travel_time_minutes == 10

    async def test_long_distance_calculation(self):
        """Test calculation for long distance (~50 miles)"""
        service = OpenRouteService(api_key="test_key")

        # 80km ≈ 50 miles, 3600s = 60 minutes
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "summary": {
                            "distance": 80000.0,  # 80km in meters
                            "duration": 3600.0,  # 60 minutes
                        }
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.7749,
                dest_lng=-122.4194,
            )

            assert result.error is None
            # 80000m * 0.000621371 ≈ 49.7 miles, rounded to 49.7
            assert result.distance_miles == pytest.approx(49.7, abs=1.0)
            assert result.travel_time_minutes == 60

    async def test_minimum_travel_time(self):
        """Test that travel time is at least 1 minute"""
        service = OpenRouteService(api_key="test_key")

        # Very short trip - 30 seconds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "summary": {
                            "distance": 100.0,  # 100 meters
                            "duration": 30.0,  # 30 seconds
                        }
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await service.get_driving_distance(
                origin_lat=37.5485,
                origin_lng=-121.9886,
                dest_lat=37.5486,
                dest_lng=-121.9887,
            )

            assert result.error is None
            # Even though calculated to 0.5 min, should be minimum 1 minute
            assert result.travel_time_minutes >= 1


class TestConversionConstants:
    """Test conversion constants are correct"""

    def test_meters_to_miles_constant(self):
        """Test METERS_TO_MILES constant is accurate"""
        # 1609.344 meters = 1 mile
        # So 1 meter = 1/1609.344 miles ≈ 0.000621371
        assert METERS_TO_MILES == pytest.approx(0.000621371, abs=0.0000001)

    def test_seconds_to_minutes_constant(self):
        """Test SECONDS_TO_MINUTES constant is correct"""
        assert SECONDS_TO_MINUTES == 1 / 60

    def test_conversion_accuracy(self):
        """Test that conversions produce expected results"""
        # 10 miles in meters = 16093.44
        meters = 16093.44
        miles = meters * METERS_TO_MILES
        assert miles == pytest.approx(10.0, abs=0.01)

        # 30 minutes in seconds = 1800
        seconds = 1800
        minutes = seconds * SECONDS_TO_MINUTES
        assert minutes == 30.0
