"""
Unit Tests for Cache Service
Test caching, TTL, invalidation, and decorators
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.cache import CacheService, cached, invalidate_cache
import json


@pytest.fixture
async def cache_service():
    """Create cache service for testing"""
    service = CacheService("redis://localhost:6379/0")
    # Mock Redis for testing
    service.redis = AsyncMock()
    yield service
    await service.disconnect()


@pytest.mark.asyncio
class TestCacheService:
    """Test CacheService class"""
    
    async def test_connect_disconnect(self):
        """Test Redis connection and disconnection"""
        service = CacheService("redis://localhost:6379/0")
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            await service.connect()
            assert service.redis is not None
            
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
        cache_service.redis.get.assert_called_once_with("test_key")
    
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
            "test_key",
            300,
            json.dumps(test_data)
        )
    
    async def test_set_without_ttl(self, cache_service):
        """Test setting key without TTL"""
        test_data = {"status": "success"}
        
        await cache_service.set("test_key", test_data)
        
        cache_service.redis.set.assert_called_once_with(
            "test_key",
            json.dumps(test_data)
        )
    
    async def test_delete_key(self, cache_service):
        """Test deleting single key"""
        await cache_service.delete("test_key")
        
        cache_service.redis.delete.assert_called_once_with("test_key")
    
    async def test_delete_pattern(self, cache_service):
        """Test deleting keys by pattern"""
        # Setup mock keys
        cache_service.redis.keys.return_value = [
            b"user:1:profile",
            b"user:2:profile",
            b"user:3:profile"
        ]
        
        # Execute
        deleted = await cache_service.delete_pattern("user:*:profile")
        
        # Verify
        assert deleted == 3
        cache_service.redis.keys.assert_called_once()
        assert cache_service.redis.delete.call_count == 3


@pytest.mark.asyncio
class TestCacheDecorators:
    """Test cache decorators"""
    
    async def test_cached_decorator_cache_miss(self, cache_service):
        """Test @cached decorator on cache miss"""
        # Setup
        call_count = 0
        
        @cached(ttl=300, key_prefix="test")
        async def expensive_function(x: int):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Mock cache service
        with patch('core.cache.CacheService') as mock_cache_class:
            mock_cache_class.return_value = cache_service
            cache_service.redis.get.return_value = None
            
            # Execute - cache miss
            result = await expensive_function(5)
            
            # Verify
            assert result == 10
            assert call_count == 1
            cache_service.redis.setex.assert_called_once()
    
    async def test_cached_decorator_cache_hit(self, cache_service):
        """Test @cached decorator on cache hit"""
        call_count = 0
        
        @cached(ttl=300, key_prefix="test")
        async def expensive_function(x: int):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Mock cache hit
        with patch('core.cache.CacheService') as mock_cache_class:
            mock_cache_class.return_value = cache_service
            cache_service.redis.get.return_value = json.dumps(10)
            
            # Execute - cache hit
            result = await expensive_function(5)
            
            # Verify
            assert result == 10
            assert call_count == 0  # Function not called!
    
    async def test_invalidate_cache_decorator(self, cache_service):
        """Test @invalidate_cache decorator"""
        
        @invalidate_cache("test:*")
        async def update_function():
            return {"updated": True}
        
        # Mock cache service
        with patch('core.cache.CacheService') as mock_cache_class:
            mock_cache_class.return_value = cache_service
            cache_service.redis.keys.return_value = [b"test:1", b"test:2"]
            
            # Execute
            result = await update_function()
            
            # Verify
            assert result == {"updated": True}
            cache_service.redis.keys.assert_called_once()


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
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = ConnectionError("Redis unavailable")
            
            # Should not raise exception
            await service.connect()
            
            # Operations should return None gracefully
            result = await service.get("test_key")
            assert result is None
    
    async def test_serialization_error(self, cache_service):
        """Test handling of non-serializable data"""
        # Create non-serializable object
        class CustomObject:
            pass
        
        obj = CustomObject()
        
        # Should handle gracefully
        result = await cache_service.set("test_key", obj)
        assert result is False or result is None


# Integration test (requires Redis)
@pytest.mark.integration
@pytest.mark.asyncio
class TestCacheIntegration:
    """Integration tests with real Redis"""
    
    async def test_real_redis_operations(self):
        """Test with real Redis instance"""
        service = CacheService("redis://localhost:6379/1")  # Use DB 1 for tests
        
        try:
            await service.connect()
            
            # Set
            await service.set("test_key", {"value": 123}, ttl=10)
            
            # Get
            result = await service.get("test_key")
            assert result == {"value": 123}
            
            # Delete
            await service.delete("test_key")
            result = await service.get("test_key")
            assert result is None
            
        finally:
            await service.disconnect()
    
    async def test_ttl_expiration(self):
        """Test TTL expiration"""
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
