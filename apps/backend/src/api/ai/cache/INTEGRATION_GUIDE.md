# Semantic Cache Integration Guide

**Next Step:** Integrate semantic cache into the existing AI orchestrator to start saving costs.

---

## 🎯 Integration Checklist

### Prerequisites
- [x] Semantic cache implementation complete
- [x] All tests passing (10/10)
- [x] Documentation complete
- [ ] Redis running and accessible
- [ ] OpenAI API key configured

---

## 📍 Integration Points

### 1. Locate AI Chat Endpoint

**Files to check:**
```
apps/backend/src/api/ai/orchestrator/orchestrator.py
apps/backend/src/api/ai/routes/chat.py
apps/backend/src/api/ai/services/chat_service.py
```

**Look for:**
- Main chat/completion method
- Where OpenAI API is called
- Intent detection logic
- Conversation context handling

---

### 2. Wrap with Semantic Cache

**Pattern:**
```python
# Before (in orchestrator.py or chat_service.py)
async def chat(self, query: str, context: dict) -> dict:
    # Detect intent
    intent = await self.detect_intent(query)
    
    # Call OpenAI
    response = await self.openai_provider.chat_completion(
        messages=[...],
        model="gpt-4o-mini"
    )
    
    return {"response": response, "intent": intent}


# After (with cache)
from api.ai.cache import SemanticCache, CacheConfig

class AIOrchestrator:
    def __init__(self, ...):
        # ... existing initialization
        
        # Initialize semantic cache
        self.cache = SemanticCache(
            redis_client=self.redis_client,
            embedding_provider=self.openai_provider,  # Use existing OpenAI client
            config=CacheConfig()  # Uses safe defaults (0.97 threshold)
        )
    
    async def chat(self, query: str, context: dict) -> dict:
        # Detect intent first (required for cache)
        intent = await self.detect_intent(query)
        
        # CHECK CACHE FIRST
        cached = await self.cache.check_cache(
            query=query,
            intent=intent,
            context=context
        )
        
        if cached:
            # Cache hit! Return immediately
            return {
                "response": cached["response"],
                "intent": cached["intent"],
                "cached": True,
                "similarity": cached["similarity"],
                "cost": 0.0
            }
        
        # Cache miss - call OpenAI
        response = await self.openai_provider.chat_completion(
            messages=[...],
            model="gpt-4o-mini"
        )
        
        # STORE IN CACHE
        await self.cache.store_response(
            query=query,
            response=response,
            intent=intent,
            context=context
        )
        
        return {
            "response": response,
            "intent": intent,
            "cached": False,
            "cost": 0.001  # Approximate cost
        }
```

---

### 3. Update Response Metadata

**Add cache statistics to response:**
```python
async def chat_with_stats(self, query: str, context: dict) -> dict:
    result = await self.chat(query, context)
    
    # Add cache stats to response
    cache_stats = await self.cache.get_stats()
    result["cache_stats"] = {
        "hit_rate": cache_stats["hit_rate_percent"],
        "total_savings": cache_stats["estimated_savings_usd"]
    }
    
    return result
```

---

### 4. Configuration

**Environment Variables:**
```env
# .env or environment config
REDIS_CACHE_URL=redis://localhost:6379/2  # Use separate DB for cache
OPENAI_API_KEY=sk-...
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.97  # Optional override
SEMANTIC_CACHE_INTENT_MATCH_REQUIRED=true
SEMANTIC_CACHE_CONTEXT_AWARE=true
```

**Config Class:**
```python
from api.ai.cache import CacheConfig

# Load from environment
cache_config = CacheConfig(
    similarity_threshold=float(os.getenv("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", "0.97")),
    intent_match_required=os.getenv("SEMANTIC_CACHE_INTENT_MATCH_REQUIRED", "true").lower() == "true",
    context_aware=os.getenv("SEMANTIC_CACHE_CONTEXT_AWARE", "true").lower() == "true",
)
```

---

## 🧪 Testing Integration

### 1. Unit Test with Cache
```python
import pytest
from api.ai.orchestrator import AIOrchestrator

@pytest.mark.asyncio
async def test_chat_uses_cache(orchestrator):
    query = "What's on your menu?"
    context = {"customer_id": "test123"}
    
    # First call - cache miss
    result1 = await orchestrator.chat(query, context)
    assert result1["cached"] is False
    
    # Second call - cache hit
    result2 = await orchestrator.chat(query, context)
    assert result2["cached"] is True
    assert result2["response"] == result1["response"]
```

### 2. Integration Test with Real Redis
```python
@pytest.mark.integration
async def test_cache_with_real_redis(redis_client):
    # Test with actual Redis instance
    cache = SemanticCache(redis_client, openai_provider)
    
    # Store and retrieve
    await cache.store_response("test query", "test response", "test_intent")
    cached = await cache.check_cache("test query", "test_intent")
    
    assert cached is not None
```

---

## 📊 Monitoring After Integration

### 1. Log Cache Performance
```python
import logging

logger = logging.getLogger(__name__)

async def chat_with_logging(self, query: str, context: dict) -> dict:
    result = await self.chat(query, context)
    
    if result.get("cached"):
        logger.info(
            f"Cache HIT: similarity={result['similarity']:.3f}, "
            f"intent={result['intent']}, saved=$0.001"
        )
    else:
        logger.info(f"Cache MISS: intent={result['intent']}, cost=$0.001")
    
    return result
```

### 2. Periodic Stats Logging
```python
# In a background task or scheduled job
async def log_cache_stats():
    stats = await cache.get_stats()
    logger.info(
        f"Cache Stats: "
        f"hit_rate={stats['hit_rate_percent']}%, "
        f"savings=${stats['estimated_savings_usd']}, "
        f"hits={stats['hits']}, misses={stats['misses']}"
    )
```

### 3. Alert on Low Hit Rate
```python
async def check_cache_health():
    stats = await cache.get_stats()
    
    if stats["hit_rate_percent"] < 30:
        logger.warning(
            f"Low cache hit rate: {stats['hit_rate_percent']}%. "
            f"Consider adjusting similarity threshold."
        )
```

---

## 🚀 Deployment Steps

### 1. Stage Environment
```bash
# Ensure Redis is running
docker-compose up -d redis

# Run tests
pytest src/api/ai/cache/ -v

# Start backend
cd apps/backend
uvicorn api.app.main:app --reload
```

### 2. Smoke Test
```bash
# Test chat endpoint with cache
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is your menu?",
    "context": {"customer_id": "test123"}
  }'

# Call again to test cache hit
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is your menu?",
    "context": {"customer_id": "test123"}
  }'
```

### 3. Monitor Logs
```bash
# Watch for cache hits/misses
tail -f logs/backend.log | grep "Cache"
```

---

## ⚠️ Rollback Plan

If issues arise:

### 1. Disable Cache via Config
```python
# Quick disable without code changes
cache_config = CacheConfig(
    similarity_threshold=1.0,  # Only exact matches (effectively disabled)
)
```

### 2. Remove Cache Layer
```python
# Revert to direct API calls
async def chat(self, query: str, context: dict) -> dict:
    intent = await self.detect_intent(query)
    response = await self.openai_provider.chat_completion(...)
    return {"response": response, "intent": intent}
```

### 3. Clear Cache
```python
# Clear all cached responses
await cache.clear_cache("ai:cache:*")
```

---

## 📈 Success Metrics

**Track after 1 week:**
- Cache hit rate: Target 40-60%
- Cost savings: $100-200/week
- Response time p50: <50ms (cached) vs 500ms+ (API)
- Wrong answers: 0 (should remain 0)

**Alert if:**
- Hit rate < 30% (threshold too high?)
- Wrong answers > 0 (safety feature broken!)
- Cache size > 1GB (need TTL adjustment?)

---

## 🔍 Common Issues

### Issue 1: Low Hit Rate
**Symptoms:** Hit rate < 30%
**Causes:**
- Similarity threshold too high
- Intent classification too granular
- Customer context too varied

**Solutions:**
- Review logs for near-misses (similarity 0.95-0.97)
- Consider lowering threshold to 0.95 (with careful testing)
- Simplify intent categories

### Issue 2: Cache Miss on Identical Queries
**Symptoms:** Same query doesn't hit cache
**Causes:**
- Context includes timestamps or UUIDs
- Intent detection is non-deterministic

**Solutions:**
- Strip timestamps from cache key
- Use stable intent detection

### Issue 3: High Memory Usage
**Symptoms:** Redis memory > 1GB
**Causes:**
- Too many cached queries
- TTL too long

**Solutions:**
- Reduce TTL for dynamic content
- Set Redis maxmemory policy: `allkeys-lru`
- Clear old cache entries

---

## 📝 Next Steps After Integration

1. **Week 1:** Monitor cache performance, ensure zero wrong answers
2. **Week 2:** Optimize thresholds based on metrics
3. **Week 3:** Implement cache warming for common queries
4. **Week 4:** Add cache analytics dashboard

---

## 🎯 Goal

**Primary:** Start saving $500-1000/month while maintaining zero wrong answers
**Secondary:** Improve response times by 98% for cached queries
**Tertiary:** Reduce OpenAI API load by 40-60%

---

**Ready for Integration:** ✅  
**Estimated Time:** 2-3 hours  
**Risk Level:** Low (fail-open design, comprehensive testing)
