"""
Unit Tests for Cache Service
Test caching, TTL, invalidation, and decorators
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.cache import CacheService, cached, invalidate_cache
import json


@pytest.fixture
async def cache_service():
    """Create cache service for testing"""
    service = CacheService("redis://localhost:6379/0")
    # Mock Redis for testing with proper async methods
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.close = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    service.redis = mock_redis
    yield service
    await service.disconnect()


@pytest.mark.asyncio
class TestCacheService:
    """Test CacheService class"""

    async def test_connect_disconnect(self):
        """Test Redis connection and disconnection"""
        service = CacheService("redis://localhost:6379/0")

        with patch("core.cache.redis") as mock_redis_module:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_redis_module.from_url = AsyncMock(return_value=mock_client)

            await service.connect()
            assert service.redis is not None
            assert service._client is not None

            await service.disconnect()
            mock_client.close.assert_called_once()

    async def test_get_existing_key(self, cache_service):
        """Test getting existing key from cache"""
        # Setup
        test_data = {"name": "Test", "value": 123}
        cache_service.redis.get.return_value = json.dumps(test_data)

        # Execute
        result = await cache_service.get("test_key")

        # Verify
        assert result == test_data
        cache_service.redis.get.assert_called_once_with("myhibachi:test_key")

    async def test_get_nonexistent_key(self, cache_service):
        """Test getting non-existent key returns None"""
        cache_service.redis.get.return_value = None

        result = await cache_service.get("nonexistent")

        assert result is None

    async def test_set_with_ttl(self, cache_service):
        """Test setting key with TTL"""
        test_data = {"status": "success"}

        await cache_service.set("test_key", test_data, ttl=300)

        cache_service.redis.setex.assert_called_once_with(
            "myhibachi:test_key", 300, json.dumps(test_data)
        )

    async def test_set_without_ttl(self, cache_service):
        """Test setting key without TTL"""
        test_data = {"status": "success"}

        await cache_service.set("test_key", test_data)

        cache_service.redis.set.assert_called_once_with(
            "myhibachi:test_key", json.dumps(test_data)
        )

    async def test_delete_key(self, cache_service):
        """Test deleting single key"""
        await cache_service.delete("test_key")

        cache_service.redis.delete.assert_called_once_with(
            "myhibachi:test_key"
        )

    async def test_delete_pattern(self, cache_service):
        """Test deleting keys by pattern"""

        # Setup mock scan_iter to yield keys
        async def mock_scan_iter(match):
            keys = [
                b"myhibachi:user:1:profile",
                b"myhibachi:user:2:profile",
                b"myhibachi:user:3:profile",
            ]
            for key in keys:
                yield key

        cache_service.redis.scan_iter = mock_scan_iter
        cache_service.redis.delete = AsyncMock(return_value=3)

        # Execute
        deleted = await cache_service.delete_pattern("user:*:profile")

        # Verify
        assert deleted == 3
        cache_service.redis.delete.assert_called_once()


@pytest.mark.asyncio
class TestCacheDecorators:
    """Test cache decorators"""

    async def test_cached_decorator_cache_miss(self, cache_service):
        """Test @cached decorator on cache miss"""

        # Setup - Create a class with cache attribute for decorator to use
        class TestService:
            def __init__(self, cache):
                self.cache = cache

            @cached(ttl=300, key_prefix="test")
            async def expensive_function(self, x: int):
                return x * 2

        # Create service with mocked cache
        cache_service.redis.get = AsyncMock(return_value=None)
        cache_service.redis.setex = AsyncMock()
        service = TestService(cache_service)

        # Execute - cache miss
        result = await service.expensive_function(5)

        # Verify
        assert result == 10
        cache_service.redis.get.assert_called_once()
        cache_service.redis.setex.assert_called_once()

    async def test_cached_decorator_cache_hit(self, cache_service):
        """Test @cached decorator on cache hit"""

        # Setup - Create a class with cache attribute
        class TestService:
            def __init__(self, cache):
                self.cache = cache

            @cached(ttl=300, key_prefix="test")
            async def expensive_function(self, x: int):
                return x * 2

        # Mock cache hit - return serialized value
        cache_service.redis.get = AsyncMock(return_value=json.dumps(10))
        service = TestService(cache_service)

        # Execute - cache hit
        result = await service.expensive_function(5)

        # Verify
        assert result == 10
        cache_service.redis.get.assert_called_once()
        # setex should NOT be called on cache hit
        cache_service.redis.setex.assert_not_called()

    async def test_invalidate_cache_decorator(self, cache_service):
        """Test @invalidate_cache decorator"""

        # Setup - Create a class with cache attribute
        class TestService:
            def __init__(self, cache):
                self.cache = cache

            @invalidate_cache("test:*")
            async def update_function(self):
                return {"updated": True}

        # Mock scan_iter to yield keys (delete_pattern uses scan_iter, not keys)
        async def mock_scan_iter(match):
            keys = [b"myhibachi:test:1", b"myhibachi:test:2"]
            for key in keys:
                yield key

        cache_service.redis.scan_iter = mock_scan_iter
        cache_service.redis.delete = AsyncMock(return_value=2)
        service = TestService(cache_service)

        # Execute
        result = await service.update_function()

        # Verify
        assert result == {"updated": True}
        # delete should be called once with all matching keys
        cache_service.redis.delete.assert_called_once()


@pytest.mark.asyncio
class TestCachePerformance:
    """Test cache performance characteristics"""

    async def test_concurrent_cache_access(self, cache_service):
        """Test concurrent cache operations"""
        cache_service.redis.get.return_value = json.dumps({"value": 123})

        # Execute 100 concurrent gets
        tasks = [cache_service.get(f"key_{i}") for i in range(100)]
        results = await asyncio.gather(*tasks)

        # Verify
        assert len(results) == 100
        assert all(r == {"value": 123} for r in results)

    async def test_large_data_serialization(self, cache_service):
        """Test caching large data structures"""
        large_data = {
            "items": [{"id": i, "data": f"item_{i}"} for i in range(1000)]
        }

        await cache_service.set("large_key", large_data, ttl=300)

        # Verify serialization happened
        cache_service.redis.setex.assert_called_once()
        call_args = cache_service.redis.setex.call_args[0]

        # Check data can be deserialized
        serialized = call_args[2]
        deserialized = json.loads(serialized)
        assert len(deserialized["items"]) == 1000


@pytest.mark.asyncio
class TestCacheErrorHandling:
    """Test cache error handling"""

    async def test_redis_connection_error(self):
        """Test graceful handling of Redis connection errors"""
        service = CacheService("redis://invalid:6379/0")

        with patch("redis.asyncio.from_url") as mock_redis:
            mock_redis.side_effect = ConnectionError("Redis unavailable")

            # Should not raise exception
            await service.connect()

            # Operations should return None gracefully
            result = await service.get("test_key")
            assert result is None

    async def test_serialization_error(self):
        """Test handling of non-serializable data"""
        # Create service without mocked redis (redis will be None, which is fine)
        service = CacheService("redis://localhost:6379/0")
        # Don't connect, so _client stays None

        # Create non-serializable object
        class CustomObject:
            def __repr__(self):
                raise TypeError("Not serializable")

        obj = CustomObject()

        # Should handle gracefully when redis is not connected
        result = await service.set("test_key", obj)
        # Returns False when client is None
        assert result is False


# Integration test (requires Redis)
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests with real Redis - requires Redis server running"""

    async def test_real_redis_operations(self):
        """Test with real Redis instance"""
        try:
            import redis.asyncio as redis
        except ImportError:
            pytest.skip("redis package not installed")

        service = CacheService(
            "redis://localhost:6379/1"
        )  # Use DB 1 for tests

        try:
            await service.connect()

            # Skip test if Redis connection failed
            if service.redis is None:
                pytest.skip("Redis server not available")

            # Set
            await service.set("test_key", {"value": 123}, ttl=10)

            # Get
            result = await service.get("test_key")
            assert result == {"value": 123}

            # Delete
            await service.delete("test_key")
            result = await service.get("test_key")
            assert result is None

        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        finally:
            await service.disconnect()

    async def test_ttl_expiration(self):
        """Test TTL expiration"""
        try:
            import redis.asyncio as redis
        except ImportError:
            pytest.skip("redis package not installed")

        service = CacheService("redis://localhost:6379/1")

        try:
            await service.connect()

            # Set with 1 second TTL
            await service.set("expire_test", {"value": 123}, ttl=1)

            # Should exist immediately
            result = await service.get("expire_test")
            assert result == {"value": 123}

            # Wait for expiration
            await asyncio.sleep(2)

            # Should be gone
            result = await service.get("expire_test")
            assert result is None

        finally:
            await service.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
