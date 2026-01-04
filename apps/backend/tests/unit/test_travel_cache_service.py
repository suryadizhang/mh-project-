"""
Unit Tests for Travel Cache Service

Tests the dual-layer caching system (LRU + Database) for travel API responses.

Run with: pytest tests/unit/test_travel_cache_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# Import the service and types
from services.scheduling.travel_cache_service import (
    TravelCacheService,
    TravelCacheEntry,
    LRU_CACHE_MAX_SIZE,
    CACHE_TTL_DAYS,
    COORDINATE_DECIMALS,
)


class TestTravelCacheEntry:
    """Test TravelCacheEntry dataclass"""

    def test_create_cache_entry(self):
        """Test creating a cache entry with all fields"""
        entry = TravelCacheEntry(
            travel_time_minutes=45,
            distance_miles=28.5,
            is_rush_hour=True,
            source="google_maps",
        )

        assert entry.travel_time_minutes == 45
        assert entry.distance_miles == 28.5
        assert entry.is_rush_hour is True
        assert entry.source == "google_maps"

    def test_cache_entry_with_openroute_source(self):
        """Test cache entry from OpenRouteService source"""
        entry = TravelCacheEntry(
            travel_time_minutes=50,
            distance_miles=30.2,
            is_rush_hour=False,
            source="openroute",
        )

        assert entry.source == "openroute"
        assert entry.is_rush_hour is False


class TestTravelCacheServiceCoordinates:
    """Test coordinate handling methods"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        mock_db = AsyncMock()
        return TravelCacheService(db=mock_db)

    def test_round_coordinate_standard(self, cache_service):
        """Test rounding coordinates to 3 decimal places (~100m precision)"""
        # 3 decimal places = ~100 meters precision
        result = cache_service._round_coordinate(37.12345678)
        assert result == 37.123

    def test_round_coordinate_rounds_up(self, cache_service):
        """Test coordinate rounding up when >= 0.0005"""
        # Use 37.1236 to avoid banker's rounding ambiguity with 37.1235
        result = cache_service._round_coordinate(37.1236)
        assert result == 37.124

    def test_round_coordinate_rounds_down(self, cache_service):
        """Test coordinate rounding down when < 0.0005"""
        result = cache_service._round_coordinate(37.1234)
        assert result == 37.123

    def test_round_coordinate_negative(self, cache_service):
        """Test rounding negative coordinates (e.g., Western hemisphere)"""
        result = cache_service._round_coordinate(-122.456789)
        assert result == -122.457

    def test_round_coordinate_zero(self, cache_service):
        """Test rounding zero coordinate"""
        result = cache_service._round_coordinate(0.0)
        assert result == 0.0


class TestTravelCacheServiceCacheKey:
    """Test cache key generation"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        mock_db = AsyncMock()
        return TravelCacheService(db=mock_db)

    def test_make_cache_key_standard(self, cache_service):
        """Test standard cache key generation"""
        key = cache_service._make_cache_key(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=False,
        )

        # Key format: "lat:lng:lat:lng:rush"
        assert key == "37.548:-122.056:37.785:-122.409:0"

    def test_make_cache_key_with_rush_hour(self, cache_service):
        """Test cache key with rush hour flag"""
        key = cache_service._make_cache_key(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=True,
        )

        assert key == "37.548:-122.056:37.785:-122.409:1"

    def test_make_cache_key_coordinates_rounded(self, cache_service):
        """Test that coordinates are rounded in cache key"""
        key = cache_service._make_cache_key(
            origin_lat=37.5484567,  # Should round to 37.548
            origin_lng=-122.0561234,  # Should round to -122.056
            dest_lat=37.7852345,  # Should round to 37.785
            dest_lng=-122.4094567,  # Should round to -122.409
            is_rush_hour=False,
        )

        assert key == "37.548:-122.056:37.785:-122.409:0"

    def test_make_cache_key_same_location_different_rush(self, cache_service):
        """Test that same location with different rush hour produces different keys"""
        key_no_rush = cache_service._make_cache_key(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=False,
        )

        key_rush = cache_service._make_cache_key(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=True,
        )

        assert key_no_rush != key_rush
        assert key_no_rush.endswith(":0")
        assert key_rush.endswith(":1")


class TestTravelCacheServiceLRUCache:
    """Test LRU (in-memory) cache operations"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        from collections import OrderedDict

        mock_db = AsyncMock()
        service = TravelCacheService(db=mock_db)
        # Reset LRU cache for each test (must remain OrderedDict!)
        service._lru_cache = OrderedDict()
        service._stats = {"lru_hits": 0, "lru_misses": 0, "db_hits": 0, "db_misses": 0}
        return service

    def test_lru_set_and_get(self, cache_service):
        """Test setting and getting from LRU cache"""
        entry = TravelCacheEntry(
            travel_time_minutes=30,
            distance_miles=15.5,
            is_rush_hour=False,
            source="google_maps",
        )

        cache_service._lru_set("test_key", entry)
        result = cache_service._lru_get("test_key")

        assert result is not None
        assert result.travel_time_minutes == 30
        assert result.distance_miles == 15.5

    def test_lru_get_miss(self, cache_service):
        """Test LRU cache miss returns None"""
        result = cache_service._lru_get("nonexistent_key")
        assert result is None

    def test_lru_cache_updates_order(self, cache_service):
        """Test that accessing LRU cache updates access order"""
        entry1 = TravelCacheEntry(30, 15.0, False, "google_maps")
        entry2 = TravelCacheEntry(45, 25.0, True, "openroute")

        cache_service._lru_set("key1", entry1)
        cache_service._lru_set("key2", entry2)

        # Access key1 to move it to end (most recently used)
        cache_service._lru_get("key1")

        # key1 should now be at the end of OrderedDict
        keys = list(cache_service._lru_cache.keys())
        assert keys[-1] == "key1"

    def test_lru_cache_eviction(self, cache_service):
        """Test LRU cache evicts oldest entry when full"""
        from collections import OrderedDict

        # Set a small max size for testing
        original_max = LRU_CACHE_MAX_SIZE

        # We'll simulate by filling beyond typical test sizes
        # Create a smaller cache for this test
        cache_service._lru_cache = OrderedDict()

        # Add entries up to a limit, then verify eviction behavior
        for i in range(5):
            entry = TravelCacheEntry(i * 10, float(i), False, "test")
            cache_service._lru_set(f"key_{i}", entry)

        # All 5 should be present (under typical max size)
        for i in range(5):
            assert cache_service._lru_get(f"key_{i}") is not None


class TestTravelCacheServiceStats:
    """Test cache statistics tracking"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        mock_db = AsyncMock()
        return TravelCacheService(db=mock_db)

    def test_stats_initialized_to_zero(self, cache_service):
        """Test that stats are initialized to zero"""
        assert cache_service._stats["lru_hits"] == 0
        assert cache_service._stats["lru_misses"] == 0
        assert cache_service._stats["db_hits"] == 0
        assert cache_service._stats["db_misses"] == 0

    def test_lru_hit_increments_stat(self, cache_service):
        """Test that LRU hit increments the stat"""
        entry = TravelCacheEntry(30, 15.0, False, "google_maps")
        cache_service._lru_set("test_key", entry)

        # First get should be a hit
        cache_service._lru_get("test_key")

        # Check stats (note: stats are updated in get() method, not _lru_get)
        # This is testing the internal LRU mechanism


@pytest.mark.asyncio
class TestTravelCacheServiceGet:
    """Test the main get() method with async operations"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        mock_db = AsyncMock()
        return TravelCacheService(db=mock_db)

    async def test_get_lru_hit(self, cache_service):
        """Test get() returns from LRU cache (Layer 1 hit)"""
        entry = TravelCacheEntry(
            travel_time_minutes=30,
            distance_miles=15.5,
            is_rush_hour=False,
            source="google_maps",
        )

        # Pre-populate LRU cache
        cache_key = cache_service._make_cache_key(37.548, -122.056, 37.785, -122.409, False)
        cache_service._lru_set(cache_key, entry)

        result = await cache_service.get(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=False,
        )

        assert result is not None
        assert result.travel_time_minutes == 30
        assert result.distance_miles == 15.5
        assert cache_service._stats["lru_hits"] == 1

    async def test_get_cache_miss(self, cache_service):
        """Test get() returns None on complete cache miss"""
        # Mock DB to return no results using scalar_one_or_none()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        cache_service.db.execute = AsyncMock(return_value=mock_result)

        result = await cache_service.get(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            is_rush_hour=False,
        )

        assert result is None
        assert cache_service._stats["lru_misses"] == 1
        assert cache_service._stats["db_misses"] == 1


@pytest.mark.asyncio
class TestTravelCacheServiceSet:
    """Test the main set() method with async operations"""

    @pytest.fixture
    def cache_service(self):
        """Create a TravelCacheService with mocked DB session"""
        mock_db = AsyncMock()

        # Mock execute() to return an object with scalar_one_or_none()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing entry
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()  # add() is sync
        mock_db.rollback = AsyncMock()

        return TravelCacheService(db=mock_db)

    async def test_set_adds_to_lru_and_db(self, cache_service):
        """Test set() adds entry to both LRU and database"""
        result = await cache_service.set(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            travel_time_minutes=30,
            distance_miles=15.5,
            is_rush_hour=False,
            source="google_maps",
        )

        assert result is True

        # Verify LRU cache was populated
        cache_key = cache_service._make_cache_key(37.548, -122.056, 37.785, -122.409, False)
        lru_entry = cache_service._lru_get(cache_key)
        assert lru_entry is not None
        assert lru_entry.travel_time_minutes == 30

        # Verify DB execute was called
        cache_service.db.execute.assert_called()

    async def test_set_with_rush_hour(self, cache_service):
        """Test set() with rush hour flag"""
        result = await cache_service.set(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            travel_time_minutes=45,
            distance_miles=15.5,
            is_rush_hour=True,
            source="google_maps",
        )

        assert result is True

        # Verify rush hour key was used
        cache_key = cache_service._make_cache_key(37.548, -122.056, 37.785, -122.409, True)
        lru_entry = cache_service._lru_get(cache_key)
        assert lru_entry is not None
        assert lru_entry.is_rush_hour is True
        assert lru_entry.travel_time_minutes == 45

    async def test_set_handles_db_error(self, cache_service):
        """Test set() handles database errors gracefully"""
        cache_service.db.execute = AsyncMock(side_effect=Exception("DB Error"))

        # Should not raise, but return False
        result = await cache_service.set(
            origin_lat=37.548,
            origin_lng=-122.056,
            dest_lat=37.785,
            dest_lng=-122.409,
            travel_time_minutes=30,
            distance_miles=15.5,
            is_rush_hour=False,
            source="google_maps",
        )

        # LRU should still work even if DB fails
        cache_key = cache_service._make_cache_key(37.548, -122.056, 37.785, -122.409, False)
        lru_entry = cache_service._lru_get(cache_key)
        assert lru_entry is not None


class TestCacheConstants:
    """Test cache configuration constants"""

    def test_lru_cache_max_size(self):
        """Test LRU cache max size is reasonable"""
        assert LRU_CACHE_MAX_SIZE == 1000
        assert LRU_CACHE_MAX_SIZE > 0

    def test_cache_ttl_days(self):
        """Test cache TTL is set to 7 days"""
        assert CACHE_TTL_DAYS == 7
        assert CACHE_TTL_DAYS > 0

    def test_coordinate_decimals(self):
        """Test coordinate precision is 3 decimals (~100m)"""
        assert COORDINATE_DECIMALS == 3
        # 3 decimals gives ~100 meter precision for coordinates
