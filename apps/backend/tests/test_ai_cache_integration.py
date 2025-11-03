"""
Test AI Response Caching Integration
Validates that caching reduces OpenAI calls and improves response time
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from api.ai.endpoints.services.chat_service import ChatService
from api.ai.endpoints.services.ai_cache_service import AIResponseCache
from api.ai.endpoints.schemas import ChatIngestRequest, ChannelType


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def cache_service():
    """Create cache service without Redis (uses memory cache)"""
    return AIResponseCache(redis_client=None)


@pytest.fixture
def chat_service_with_cache(cache_service):
    """Create chat service with mocked AI pipeline"""
    service = ChatService()
    service.cache = cache_service
    
    # Mock the AI pipeline to return predictable responses
    async def mock_process_message(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.message = "For 10 guests, our pricing starts at $450. This includes our chef, setup, and all equipment."
        mock_response.confidence = 0.92
        mock_response.source = "gpt-4o-mini"
        return mock_response
    
    service.ai_service.process_message = mock_process_message
    
    return service


@pytest.mark.asyncio
async def test_cache_hit_reduces_processing_time(mock_db, chat_service_with_cache):
    """Test that cache hits are significantly faster than fresh AI calls"""
    
    request = ChatIngestRequest(
        message="What's your pricing for 10 guests?",
        channel=ChannelType.WEBSITE,
        user_id="test_user_123",
        thread_id="thread_001",
        metadata={}
    )
    
    # Mock database queries
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    
    # First call - cache MISS (should call AI)
    start_time = time.time()
    response1 = await chat_service_with_cache.ingest_chat(request, mock_db)
    first_call_time = time.time() - start_time
    
    print(f"First call (cache MISS): {first_call_time * 1000:.2f}ms")
    print(f"Source: {response1.source}")
    
    # Second call - cache HIT (should skip AI)
    start_time = time.time()
    response2 = await chat_service_with_cache.ingest_chat(request, mock_db)
    second_call_time = time.time() - start_time
    
    print(f"Second call (cache HIT): {second_call_time * 1000:.2f}ms")
    print(f"Source: {response2.source}")
    
    # Assertions
    assert response1.response == response2.response, "Cached response should match original"
    assert "cached" in response2.source.lower(), "Second call should indicate cache hit"
    assert second_call_time < first_call_time, "Cache hit should be faster"
    assert second_call_time < 0.1, "Cache hit should be under 100ms"
    
    print(f"✅ Cache improved response time by {((first_call_time - second_call_time) / first_call_time * 100):.1f}%")


@pytest.mark.asyncio
async def test_cache_categorization():
    """Test that different message types get appropriate cache TTLs"""
    
    cache = AIResponseCache(redis_client=None)
    
    test_cases = [
        ("What are your payment options?", "static"),
        ("Do you have chicken options?", "semi_static"),
        ("Are you available tomorrow?", "dynamic"),
        ("Can you tell me more about my order #12345?", "personalized"),
    ]
    
    for message, expected_category in test_cases:
        category = cache._determine_cache_category(message)
        print(f"Message: '{message}' → Category: {category}")
        assert category == expected_category, f"Expected {expected_category}, got {category}"
    
    print("✅ All cache categories correctly identified")


@pytest.mark.asyncio
async def test_cache_key_normalization():
    """Test that similar questions generate the same cache key"""
    
    cache = AIResponseCache(redis_client=None)
    
    # These should all generate the same cache key
    similar_questions = [
        "What's your pricing for 10 guests?",
        "What's your pricing for 10 guests",  # No punctuation
        "what's your pricing for 10 guests?",  # Different case
        "  What's your pricing for 10 guests?  ",  # Extra spaces
    ]
    
    keys = [cache._generate_cache_key(q) for q in similar_questions]
    
    print(f"Generated {len(set(keys))} unique keys from {len(similar_questions)} similar questions")
    
    assert len(set(keys)) == 1, "Similar questions should generate the same cache key"
    print(f"✅ Cache key normalization working: {keys[0]}")


@pytest.mark.asyncio
async def test_cache_stores_and_retrieves():
    """Test basic cache store and retrieve operations"""
    
    cache = AIResponseCache(redis_client=None)
    
    message = "What time do you open?"
    response_data = {
        "response": "We're available 7 days a week, with flexible scheduling from 10 AM to 10 PM.",
        "confidence": 0.95,
        "source": "knowledge-base"
    }
    
    # Store in cache
    stored = await cache.cache_response(message, response_data)
    assert stored is True, "Cache storage should succeed"
    
    # Retrieve from cache
    cached = await cache.get_cached_response(message)
    assert cached is not None, "Should retrieve cached response"
    assert cached["response"] == response_data["response"], "Cached response should match"
    assert cached["cached"] is True, "Should be marked as cached"
    
    print(f"✅ Cache store and retrieve working correctly")
    print(f"   Original: {response_data['response'][:50]}...")
    print(f"   Cached:   {cached['response'][:50]}...")


@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation patterns"""
    
    cache = AIResponseCache(redis_client=None)
    
    # Store multiple responses
    messages = [
        "What's your pricing?",
        "What's your payment policy?",
        "Do you accept credit cards?",
    ]
    
    for msg in messages:
        await cache.cache_response(msg, {"response": f"Answer to: {msg}"})
    
    # Check all are cached
    for msg in messages:
        cached = await cache.get_cached_response(msg)
        assert cached is not None, f"Should find cached response for: {msg}"
    
    print(f"✅ Stored {len(messages)} responses in cache")
    
    # Invalidate payment-related cache
    invalidated = await cache.invalidate_cache(pattern="*payment*")
    print(f"✅ Invalidated {invalidated} cache entries matching 'payment'")
    
    # First message should still be cached
    cached = await cache.get_cached_response(messages[0])
    assert cached is not None, "Non-payment question should still be cached"
    
    # Payment question should be invalidated
    cached = await cache.get_cached_response(messages[1])
    assert cached is None, "Payment question should be invalidated"
    
    print("✅ Selective cache invalidation working correctly")


@pytest.mark.asyncio
async def test_cache_memory_limit():
    """Test that cache doesn't grow indefinitely"""
    
    cache = AIResponseCache(redis_client=None)
    
    # Store 1500 responses (more than the 1000 limit)
    for i in range(1500):
        await cache.cache_response(
            f"Test question {i}",
            {"response": f"Answer {i}"}
        )
    
    cache_size = len(cache.memory_cache)
    print(f"Cache size after 1500 insertions: {cache_size}")
    
    # Should have cleaned up to stay under limit
    assert cache_size <= 1000, "Cache should enforce size limit"
    print(f"✅ Cache memory limit enforced (kept {cache_size} entries)")


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics reporting"""
    
    cache = AIResponseCache(redis_client=None)
    
    # Add some test data
    for i in range(10):
        await cache.cache_response(f"Question {i}", {"response": f"Answer {i}"})
    
    stats = await cache.get_cache_stats()
    
    print("Cache Statistics:")
    print(f"  Memory cache size: {stats['memory_cache_size']}")
    print(f"  Redis available: {stats['redis_available']}")
    
    assert stats["memory_cache_size"] == 10, "Should have 10 cached items"
    assert stats["redis_available"] is False, "Redis should not be available in test"
    
    print("✅ Cache statistics working correctly")


if __name__ == "__main__":
    print("🧪 Running AI Cache Integration Tests...\n")
    
    # Run all tests
    asyncio.run(test_cache_categorization())
    asyncio.run(test_cache_key_normalization())
    asyncio.run(test_cache_stores_and_retrieves())
    asyncio.run(test_cache_invalidation())
    asyncio.run(test_cache_memory_limit())
    asyncio.run(test_cache_stats())
    
    print("\n✅ All cache tests passed!")
