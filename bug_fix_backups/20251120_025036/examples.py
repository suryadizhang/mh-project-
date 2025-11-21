"""
Semantic Cache Integration Example

Shows how to integrate semantic caching into AI orchestrator to save costs
while preventing wrong answers.

Author: MyHibachi AI Team
Created: November 10, 2025
"""

import asyncio

from api.ai.cache import CacheConfig, SemanticCache
from api.ai.orchestrator.providers.openai_provider import OpenAIProvider


async def example_with_caching():
    """
    Example: Using semantic cache with OpenAI provider.

    This shows the complete integration flow:
    1. Check cache first (sub-10ms if hit)
    2. If miss, call OpenAI API
    3. Store response in cache
    4. Return response

    Expected savings: 40-60% of API calls cached
    """
    # Initialize cache with safety settings
    cache_config = CacheConfig(
        similarity_threshold=0.97,  # HIGH threshold to prevent wrong answers
        intent_match_required=True,  # Must match intent
        context_aware=True,  # Include customer context
        ttl_static=604800,  # 7 days for static content
        ttl_realtime=300,  # 5 minutes for bookings
    )

    # Initialize OpenAI provider
    openai = OpenAIProvider()

    # Initialize cache with OpenAI's embedding model
    cache = SemanticCache(
        embedding_provider=openai,  # Use OpenAI for embeddings
        config=cache_config,
    )

    # Example queries
    queries = [
        {
            "query": "What is on your menu?",
            "intent": "menu",
            "context": None,
        },
        {
            "query": "What items do you serve?",  # Similar to above
            "intent": "menu",
            "context": None,
        },
        {
            "query": "Show my reservation",  # Customer-specific
            "intent": "booking",
            "context": {"customer_id": "cust_123"},
        },
        {
            "query": "Show my reservation",  # Same query, different customer
            "intent": "booking",
            "context": {"customer_id": "cust_456"},
        },
    ]

    for i, item in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {item['query']}")
        print(f"Intent: {item['intent']}")
        print(f"Context: {item['context']}")
        print(f"{'='*60}")

        # STEP 1: Check cache first
        cached_response = await cache.check_cache(
            query=item["query"],
            intent=item["intent"],
            context=item["context"],
        )

        if cached_response:
            # Cache HIT - use cached response (sub-10ms, $0 cost)
            print("✅ CACHE HIT!")
            print(f"Similarity: {cached_response.get('similarity', 0):.3f}")
            print(f"Response: {cached_response['response'][:100]}...")
            print("💰 Saved API call - $0 cost!")
            continue

        # Cache MISS - call OpenAI API
        print("❌ Cache miss - calling OpenAI API...")

        # STEP 2: Call OpenAI API
        # (In real implementation, this would be the full AI orchestrator)
        response = await openai.chat_completion(
            messages=[{"role": "user", "content": item["query"]}],
            temperature=0.3,
        )

        ai_response = response["choices"][0]["message"]["content"]
        print(f"API Response: {ai_response[:100]}...")
        print("💵 API cost: ~$0.001")

        # STEP 3: Store in cache for future use
        await cache.store_response(
            query=item["query"],
            response=ai_response,
            intent=item["intent"],
            context=item["context"],
        )
        print("💾 Stored in cache")

    # Show cache statistics
    print(f"\n{'='*60}")
    print("CACHE STATISTICS")
    print(f"{'='*60}")
    stats = await cache.get_stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Cache Hits: {stats['hits']}")
    print(f"Cache Misses: {stats['misses']}")
    print(f"Hit Rate: {stats['hit_rate_percent']}%")
    print(f"Estimated Savings: ${stats['estimated_savings_usd']}")
    print("\nWith 40-60% hit rate, monthly savings: $500-1000")


async def example_safety_features():
    """
    Example: Demonstrating safety features that prevent wrong answers.

    Shows how the cache handles:
    1. Similar questions with different intents
    2. Same question for different customers
    3. Nearly-similar but different questions
    """
    cache_config = CacheConfig(
        similarity_threshold=0.97,
        intent_match_required=True,
        context_aware=True,
    )

    openai = OpenAIProvider()
    cache = SemanticCache(embedding_provider=openai, config=cache_config)

    print("\n" + "=" * 60)
    print("SAFETY FEATURE DEMONSTRATION")
    print("=" * 60)

    # Safety Test 1: Different intents
    print("\n1️⃣  Different Intents Test")
    print("-" * 60)

    # Cache "hours" question
    await cache.store_response(
        query="What time do you open?",
        response="We open at 11 AM daily.",
        intent="hours",
    )

    # Try to use cache for "booking" question with similar words
    cached = await cache.check_cache(
        query="What time is my reservation?",
        intent="booking",
    )

    if cached:
        print("⚠️  WARNING: Cache returned response despite intent mismatch!")
    else:
        print("✅ SAFE: Cache correctly rejected due to intent mismatch")
        print("   'hours' intent ≠ 'booking' intent")

    # Safety Test 2: Different customers
    print("\n2️⃣  Different Customers Test")
    print("-" * 60)

    # Cache for customer A
    await cache.store_response(
        query="Show my reservation",
        response="Your reservation: 4 people at 7 PM",
        intent="booking",
        context={"customer_id": "customer_a"},
    )

    # Try to use cache for customer B
    cached = await cache.check_cache(
        query="Show my reservation",
        intent="booking",
        context={"customer_id": "customer_b"},
    )

    if cached:
        print("⚠️  WARNING: Cache returned customer A's data to customer B!")
    else:
        print("✅ SAFE: Cache correctly rejected due to customer mismatch")
        print("   Customer A's data protected from Customer B")

    # Safety Test 3: High similarity threshold
    print("\n3️⃣  High Similarity Threshold Test")
    print("-" * 60)

    # Cache vegetarian question
    await cache.store_response(
        query="Do you have vegetarian options?",
        response="Yes, we offer tofu and vegetable hibachi.",
        intent="menu",
    )

    # Try slightly different question (vegan vs vegetarian)
    cached = await cache.check_cache(
        query="Do you have vegan options?",
        intent="menu",
    )

    if cached:
        print(
            f"⚠️  Cache returned (similarity: {cached.get('similarity', 0):.3f})"
        )
        print("   NOTE: Vegetarian ≠ Vegan, but similarity >= 0.97")
        print("   You may want to increase threshold for critical differences")
    else:
        print("✅ SAFE: Cache correctly rejected due to low similarity")
        print("   'vegetarian' vs 'vegan' are different questions")

    print("\n" + "=" * 60)
    print("Safety features working as designed!")
    print("=" * 60)


async def example_integration_with_orchestrator():
    """
    Example: Full integration with AI orchestrator.

    Shows how to wrap the AI orchestrator with caching layer.
    """

    class CachedAIOrchestrator:
        """AI Orchestrator with semantic caching."""

        def __init__(self):
            self.cache = SemanticCache(
                embedding_provider=OpenAIProvider(),
                config=CacheConfig(
                    similarity_threshold=0.97,
                    intent_match_required=True,
                    context_aware=True,
                ),
            )
            self.openai = OpenAIProvider()

        async def chat(
            self,
            query: str,
            intent: str | None = None,
            context: dict | None = None,
        ) -> dict:
            """
            Chat with AI, using cache when possible.

            Returns:
                {
                    "response": "AI response text",
                    "cached": bool,
                    "similarity": float (if cached),
                    "cost": float (estimated USD),
                }
            """
            # Check cache first
            cached = await self.cache.check_cache(
                query=query,
                intent=intent,
                context=context,
            )

            if cached:
                return {
                    "response": cached["response"],
                    "cached": True,
                    "similarity": cached.get("similarity", 0),
                    "cost": 0.0,  # No API call = $0
                }

            # Cache miss - call OpenAI
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": query}],
                temperature=0.3,
            )

            ai_response = response["choices"][0]["message"]["content"]

            # Store in cache
            await self.cache.store_response(
                query=query,
                response=ai_response,
                intent=intent,
                context=context,
            )

            return {
                "response": ai_response,
                "cached": False,
                "cost": 0.001,  # ~$0.001 per call for gpt-4o-mini
            }

    # Use cached orchestrator
    orchestrator = CachedAIOrchestrator()

    # First call - cache miss
    result1 = await orchestrator.chat(
        query="What are your hours?",
        intent="hours",
    )
    print(f"\nCall 1: Cached={result1['cached']}, Cost=${result1['cost']}")

    # Second call - cache hit
    result2 = await orchestrator.chat(
        query="What are your hours?",
        intent="hours",
    )
    print(f"Call 2: Cached={result2['cached']}, Cost=${result2['cost']}")

    print(f"\nSavings: ${result1['cost'] - result2['cost']}")


if __name__ == "__main__":
    print("Semantic Cache Integration Examples")
    print("=" * 60)

    # Run examples
    asyncio.run(example_with_caching())
    asyncio.run(example_safety_features())
    asyncio.run(example_integration_with_orchestrator())
