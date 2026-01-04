"""
Unit Tests for TravelTimeService

Tests the main travel time service with failsafe chain:
Cache → Google Maps → OpenRouteService → Error

Run with: pytest tests/unit/test_travel_time_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, time, timedelta

# Import the service and types
from services.scheduling.travel_time_service import (
    TravelTimeService,
    TravelTimeResult,
    Coordinates,
    ChefLocation,
    RUSH_HOUR_MULTIPLIER,
    RUSH_HOUR_START,
    RUSH_HOUR_END,
)
from services.scheduling.openroute_service import OpenRouteResult, OpenRouteServiceError


class TestCoordinates:
    """Test Coordinates dataclass"""

    def test_create_coordinates(self):
        """Test creating Coordinates with valid data"""
        coords = Coordinates(lat=37.548271, lng=-122.056174)

        assert coords.lat == 37.548271
        assert coords.lng == -122.056174

    def test_coordinates_with_extreme_values(self):
        """Test coordinates at extreme valid values"""
        # North pole
        north = Coordinates(lat=90.0, lng=0.0)
        assert north.lat == 90.0

        # South pole
        south = Coordinates(lat=-90.0, lng=0.0)
        assert south.lat == -90.0

        # Date line
        dateline = Coordinates(lat=0.0, lng=180.0)
        assert dateline.lng == 180.0


class TestChefLocation:
    """Test ChefLocation Pydantic model"""

    def test_create_chef_location(self):
        """Test creating ChefLocation with valid data"""
        from uuid import UUID

        chef_uuid = UUID("11111111-1111-1111-1111-111111111111")
        loc = ChefLocation(
            chef_id=chef_uuid,
            latitude=37.548271,
            longitude=-122.056174,
            address="47481 Towhee St, Fremont, CA 94539",
        )

        assert loc.chef_id == chef_uuid
        assert loc.latitude == 37.548271
        assert loc.longitude == -122.056174
        assert "Fremont" in loc.address


class TestTravelTimeResult:
    """Test TravelTimeResult Pydantic model"""

    def test_create_travel_time_result(self):
        """Test creating TravelTimeResult with all fields"""
        result = TravelTimeResult(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            distance_miles=25.5,
            travel_time_minutes=35,
            is_rush_hour=True,
            source="google_maps",
        )

        assert result.origin_lat == 37.548
        assert result.dest_lat == 37.785
        assert result.distance_miles == 25.5
        assert result.travel_time_minutes == 35
        assert result.is_rush_hour is True
        assert result.source == "google_maps"

    def test_travel_time_result_sources(self):
        """Test different source values"""
        sources = ["cache", "google_maps", "openroute", "error"]

        for source in sources:
            result = TravelTimeResult(
                origin_lat=37.548,
                origin_lng=-122.056,
                dest_lat=37.785,
                dest_lng=-122.409,
                distance_miles=10.0,
                travel_time_minutes=15,
                is_rush_hour=False,
                source=source,
            )
            assert result.source == source


class TestRushHourConstants:
    """Test rush hour configuration constants"""

    def test_rush_hour_multiplier(self):
        """Test rush hour multiplier is 1.5x"""
        assert RUSH_HOUR_MULTIPLIER == 1.5

    def test_rush_hour_start_time(self):
        """Test rush hour starts at 3 PM (15:00)"""
        assert RUSH_HOUR_START == time(15, 0)

    def test_rush_hour_end_time(self):
        """Test rush hour ends at 7 PM (19:00)"""
        assert RUSH_HOUR_END == time(19, 0)


class TestIsRushHour:
    """Test is_rush_hour method"""

    @pytest.fixture
    def service(self):
        """Create TravelTimeService instance"""
        return TravelTimeService()

    def test_rush_hour_at_3pm_weekday(self, service):
        """Test 3:00 PM on Monday is rush hour"""
        # Monday at 3:00 PM
        dt = datetime(2025, 1, 27, 15, 0)  # Monday
        assert service.is_rush_hour(dt) is True

    def test_rush_hour_at_5pm_weekday(self, service):
        """Test 5:00 PM on Wednesday is rush hour"""
        # Wednesday at 5:00 PM
        dt = datetime(2025, 1, 29, 17, 0)  # Wednesday
        assert service.is_rush_hour(dt) is True

    def test_rush_hour_at_6_59pm_weekday(self, service):
        """Test 6:59 PM on Friday is still rush hour"""
        # Friday at 6:59 PM
        dt = datetime(2025, 1, 31, 18, 59)  # Friday
        assert service.is_rush_hour(dt) is True

    def test_not_rush_hour_at_7pm_weekday(self, service):
        """Test 7:01 PM is not rush hour (just after end boundary)"""
        # Monday at 7:01 PM (rush hour ends at 7:00 PM inclusive)
        dt = datetime(2025, 1, 27, 19, 1)  # Monday
        assert service.is_rush_hour(dt) is False

    def test_not_rush_hour_at_2pm_weekday(self, service):
        """Test 2:00 PM is not rush hour (before start)"""
        # Tuesday at 2:00 PM
        dt = datetime(2025, 1, 28, 14, 0)  # Tuesday
        assert service.is_rush_hour(dt) is False

    def test_not_rush_hour_on_saturday(self, service):
        """Test Saturday at 5 PM is not rush hour"""
        # Saturday at 5:00 PM
        dt = datetime(2025, 1, 25, 17, 0)  # Saturday
        assert service.is_rush_hour(dt) is False

    def test_not_rush_hour_on_sunday(self, service):
        """Test Sunday at 5 PM is not rush hour"""
        # Sunday at 5:00 PM
        dt = datetime(2025, 1, 26, 17, 0)  # Sunday
        assert service.is_rush_hour(dt) is False

    def test_rush_hour_morning_not_included(self, service):
        """Test morning hours are not rush hour"""
        # Monday at 8:00 AM
        dt = datetime(2025, 1, 27, 8, 0)  # Monday
        assert service.is_rush_hour(dt) is False


class TestApplyRushHourMultiplier:
    """Test apply_rush_hour_multiplier method"""

    @pytest.fixture
    def service(self):
        """Create TravelTimeService instance"""
        return TravelTimeService()

    def test_apply_multiplier_during_rush_hour(self, service):
        """Test duration is multiplied by 1.5 during rush hour"""
        # Monday at 5:00 PM (rush hour)
        dt = datetime(2025, 1, 27, 17, 0)
        original_duration = 30.0  # 30 minutes

        result = service.apply_rush_hour_multiplier(original_duration, dt)

        assert result == 45.0  # 30 * 1.5

    def test_no_multiplier_outside_rush_hour(self, service):
        """Test duration is unchanged outside rush hour"""
        # Monday at 10:00 AM (not rush hour)
        dt = datetime(2025, 1, 27, 10, 0)
        original_duration = 30.0  # 30 minutes

        result = service.apply_rush_hour_multiplier(original_duration, dt)

        assert result == 30.0  # unchanged

    def test_no_multiplier_on_weekend(self, service):
        """Test duration is unchanged on weekends"""
        # Saturday at 5:00 PM (would be rush hour on weekday)
        dt = datetime(2025, 1, 25, 17, 0)
        original_duration = 30.0  # 30 minutes

        result = service.apply_rush_hour_multiplier(original_duration, dt)

        assert result == 30.0  # unchanged


class TestCalculateDistanceMiles:
    """Test calculate_distance_miles method (Haversine formula)"""

    @pytest.fixture
    def service(self):
        """Create TravelTimeService instance"""
        return TravelTimeService()

    def test_same_location_zero_distance(self, service):
        """Test distance is 0 for same coordinates"""
        # Using positional args: lat1, lng1, lat2, lng2
        distance = service.calculate_distance_miles(
            37.548271,  # lat1 (origin)
            -122.056174,  # lng1 (origin)
            37.548271,  # lat2 (dest)
            -122.056174,  # lng2 (dest)
        )

        assert distance == 0.0

    def test_known_distance_fremont_to_sf(self, service):
        """Test approximate distance from Fremont to San Francisco"""
        # Fremont, CA to San Francisco, CA (~35-40 miles)
        # Using positional args: lat1, lng1, lat2, lng2
        distance = service.calculate_distance_miles(
            37.548271,  # lat1 - Fremont
            -122.056174,  # lng1
            37.7749,  # lat2 - San Francisco
            -122.4194,  # lng2
        )

        # Should be approximately 30-40 miles (straight line)
        assert 20 < distance < 50

    def test_short_distance(self, service):
        """Test short distance calculation (a few blocks)"""
        # About 0.01 degrees apart (~0.7 miles)
        # Using positional args: lat1, lng1, lat2, lng2
        distance = service.calculate_distance_miles(
            37.548271,  # lat1
            -122.056174,  # lng1
            37.558271,  # lat2 - 0.01 degrees north
            -122.056174,  # lng2
        )

        # Should be approximately 0.7 miles
        assert 0.5 < distance < 1.0

    def test_haversine_formula_accuracy(self, service):
        """Test Haversine formula gives expected result for known distance"""
        # LA to NYC is approximately 2,451 miles
        # Using positional args: lat1, lng1, lat2, lng2
        distance = service.calculate_distance_miles(
            34.0522,  # lat1 - Los Angeles
            -118.2437,  # lng1
            40.7128,  # lat2 - New York City
            -74.0060,  # lng2
        )

        # Should be approximately 2,400-2,500 miles
        assert 2400 < distance < 2500


@pytest.mark.asyncio
class TestGetTravelTime:
    """Test get_travel_time method with failsafe chain"""

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock TravelCacheService"""
        return AsyncMock()

    @pytest.fixture
    def mock_openroute_service(self):
        """Create mock OpenRouteService"""
        mock = AsyncMock()
        mock.is_configured.return_value = True
        return mock

    @pytest.fixture
    def service(self, mock_cache_service, mock_openroute_service):
        """Create TravelTimeService with mocked dependencies"""
        service = TravelTimeService()
        # Set the actual private attributes used by the service
        service._cache_service = mock_cache_service
        service._openroute = mock_openroute_service
        service._google_maps_healthy = False  # Disable Google for tests
        service._openroute_healthy = True
        return service

    @pytest.fixture
    def departure_time(self):
        """Standard departure time for tests"""
        from datetime import datetime

        return datetime(2025, 6, 15, 14, 0, 0)  # 2 PM, not rush hour

    async def test_returns_cached_result(self, service, mock_cache_service, departure_time):
        """Test returns cached result when available"""
        # Setup cache hit - using TravelCacheEntry with correct fields
        cached_entry = MagicMock()
        cached_entry.travel_time_minutes = 35
        cached_entry.distance_miles = 28.0
        cached_entry.source = "google_maps"
        mock_cache_service.get.return_value = cached_entry

        result = await service.get_travel_time(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            departure_time=departure_time,
        )

        assert result is not None
        assert result.distance_miles == 28.0
        assert result.travel_time_minutes == 35
        assert "cache" in result.source  # Source becomes "cache_google_maps"

    async def test_calls_openroute_on_cache_miss(
        self, service, mock_cache_service, mock_openroute_service, departure_time
    ):
        """Test calls OpenRouteService when cache misses (Google disabled in fixture)"""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Setup OpenRoute success
        mock_openroute_service.get_driving_distance.return_value = OpenRouteResult(
            distance_miles=28.0,
            travel_time_minutes=35,
            source="openroute",
        )

        result = await service.get_travel_time(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            departure_time=departure_time,
        )

        assert result is not None
        assert result.source == "openroute"
        mock_openroute_service.get_driving_distance.assert_called_once()
        # Cache should be updated
        mock_cache_service.set.assert_called_once()

    async def test_handles_openroute_failure_gracefully(
        self, service, mock_cache_service, mock_openroute_service, departure_time
    ):
        """Test handles OpenRouteService failure gracefully"""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Setup OpenRoute failure
        mock_openroute_service.get_driving_distance.side_effect = Exception("OpenRoute API error")

        # With Google disabled and OpenRoute failing, should return error result
        result = await service.get_travel_time(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            departure_time=departure_time,
        )

        assert result.source == "error"
        assert result.error is not None
        # Service retries up to 3 times, so it may be called multiple times
        assert mock_openroute_service.get_driving_distance.call_count >= 1

    async def test_raises_error_when_all_services_fail(
        self, service, mock_cache_service, mock_openroute_service, departure_time
    ):
        """Test returns error result when all services fail"""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Setup OpenRoute failure (Google already disabled in fixture)
        mock_openroute_service.get_driving_distance.side_effect = OpenRouteServiceError(
            "OpenRoute API error"
        )

        result = await service.get_travel_time(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            departure_time=departure_time,
        )

        assert result.source == "error"
        assert result.error is not None

    async def test_skips_openroute_when_not_healthy(
        self, service, mock_cache_service, mock_openroute_service, departure_time
    ):
        """Test skips OpenRouteService when not healthy"""
        # Setup cache miss
        mock_cache_service.get.return_value = None

        # Mark OpenRoute as not healthy
        service._openroute_healthy = False

        result = await service.get_travel_time(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            departure_time=departure_time,
        )

        assert result.source == "error"
        assert result.error is not None

        # OpenRoute should not be called when not healthy
        mock_openroute_service.get_driving_distance.assert_not_called()


@pytest.mark.asyncio
class TestGetChefToVenueTravel:
    """Test get_chef_to_venue_travel method"""

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock TravelCacheService"""
        return AsyncMock()

    @pytest.fixture
    def mock_openroute_service(self):
        """Create mock OpenRouteService"""
        mock = AsyncMock()
        mock.is_configured.return_value = True
        mock.get_route.return_value = {
            "distance_meters": 32000,
            "duration_seconds": 1800,
        }
        return mock

    @pytest.fixture
    def service(self, mock_cache_service, mock_openroute_service):
        """Create TravelTimeService with mocked dependencies (Google disabled)"""
        service = TravelTimeService()
        service._cache_service = mock_cache_service
        service._openroute = mock_openroute_service
        # Google Maps is disabled, OpenRoute is enabled
        service._google_maps_healthy = False
        service._openroute_healthy = True
        return service

    async def test_calculates_travel_for_chef_location(
        self, service, mock_cache_service, mock_openroute_service
    ):
        """Test calculates travel from chef location to venue"""
        from uuid import uuid4

        chef = ChefLocation(
            chef_id=uuid4(),
            latitude=37.548271,
            longitude=-122.056174,
            address="Fremont, CA",
        )

        # Setup cache miss and OpenRoute success
        mock_cache_service.get.return_value = None

        departure_time = datetime.now() + timedelta(hours=2)
        result = await service.get_chef_to_venue_travel(
            chef_location=chef,
            venue_lat=37.7749,
            venue_lng=-122.4194,
            departure_time=departure_time,
        )

        assert result is not None
        assert result.distance_miles > 0
        assert result.duration_minutes > 0


class TestTravelTimeServiceInitialization:
    """Test TravelTimeService initialization"""

    def test_service_creates_dependencies(self):
        """Test service creates cache and API service dependencies"""
        service = TravelTimeService()

        # Service uses private attributes with underscore prefix
        assert hasattr(service, "_cache_service")
        assert hasattr(service, "_openroute")

    def test_service_has_required_methods(self):
        """Test service has all required public methods"""
        service = TravelTimeService()

        assert hasattr(service, "get_travel_time")
        assert hasattr(service, "is_rush_hour")
        assert hasattr(service, "apply_rush_hour_multiplier")
        assert hasattr(service, "calculate_distance_miles")
        assert callable(service.is_rush_hour)
        assert callable(service.calculate_distance_miles)
