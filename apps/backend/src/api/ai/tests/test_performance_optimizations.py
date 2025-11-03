"""
Performance Test for Scheduler Optimizations
=============================================

Tests the performance improvements from:
1. Composite index on (conversation_id, emotion_score, timestamp)
2. Health check caching (30-second TTL)
3. Database ANALYZE for query planner statistics
"""

import asyncio
import time
from datetime import datetime, timedelta
from api.ai.orchestrator import AIOrchestrator
from api.ai.memory import get_memory_backend
from api.ai.memory.memory_backend import MessageRole


async def test_performance():
    """Test scheduler performance with optimizations"""
    
    print("=" * 80)
    print("SCHEDULER PERFORMANCE TEST")
    print("=" * 80)
    print()
    
    # Initialize orchestrator
    print("Initializing orchestrator...")
    orchestrator = AIOrchestrator(use_router=False)
    await orchestrator.start()
    memory = await get_memory_backend()
    
    # Test 1: Schedule Follow-Up Performance
    print("\n📊 TEST 1: Schedule Follow-Up Performance")
    print("-" * 80)
    
    conv_id = f"perf_test_{time.time()}"
    user_id = f"perf_user_{time.time()}"
    
    # Store message first
    await memory.store_message(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content="Test booking",
        user_id=user_id,
        emotion_score=0.8,
        emotion_label="positive"
    )
    
    # Measure scheduling time
    start = time.time()
    job_id = await orchestrator.schedule_post_event_followup(
        conversation_id=conv_id,
        user_id=user_id,
        event_date=datetime.utcnow() + timedelta(days=7)
    )
    duration_ms = (time.time() - start) * 1000
    
    status = "✅ PASS" if duration_ms < 500 else "⚠️  SLOW"
    print(f"{status}: Schedule follow-up took {duration_ms:.0f}ms (target: <500ms)")
    
    # Cleanup
    if job_id:
        await orchestrator.scheduler.cancel_followup(job_id)
    
    # Test 2: Health Check Performance (First Call)
    print("\n📊 TEST 2: Health Check Performance (First Call - No Cache)")
    print("-" * 80)
    
    # Clear cache to simulate first call
    orchestrator.scheduler._health_cache = None
    orchestrator.scheduler._health_cache_time = None
    
    start = time.time()
    health1 = await orchestrator.scheduler.health_check()
    duration1_ms = (time.time() - start) * 1000
    
    status = "✅ PASS" if duration1_ms < 100 else "⚠️  SLOW"
    print(f"{status}: Health check (first) took {duration1_ms:.0f}ms (target: <100ms)")
    print(f"   - Cached: {health1.get('cached', False)}")
    
    # Test 3: Health Check Performance (Second Call - Should be Cached)
    print("\n📊 TEST 3: Health Check Performance (Second Call - Cached)")
    print("-" * 80)
    
    start = time.time()
    health2 = await orchestrator.scheduler.health_check()
    duration2_ms = (time.time() - start) * 1000
    
    status = "✅ PASS" if duration2_ms < 10 else "⚠️  SLOW"
    print(f"{status}: Health check (cached) took {duration2_ms:.0f}ms (target: <10ms)")
    print(f"   - Cached: {health2.get('cached', 'N/A')}")
    print(f"   - Cache speedup: {duration1_ms / duration2_ms:.1f}x faster")
    
    # Test 4: Multiple Health Checks (All Cached)
    print("\n📊 TEST 4: Multiple Health Checks (Batch - All Cached)")
    print("-" * 80)
    
    start = time.time()
    for i in range(10):
        await orchestrator.scheduler.health_check()
    batch_duration_ms = (time.time() - start) * 1000
    avg_duration_ms = batch_duration_ms / 10
    
    status = "✅ PASS" if avg_duration_ms < 10 else "⚠️  SLOW"
    print(f"{status}: 10 health checks took {batch_duration_ms:.0f}ms total")
    print(f"   - Average: {avg_duration_ms:.1f}ms per call (target: <10ms)")
    
    # Summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    
    results = [
        ("Schedule follow-up", duration_ms, 500),
        ("Health check (first)", duration1_ms, 100),
        ("Health check (cached)", duration2_ms, 10),
        ("Health check (batch avg)", avg_duration_ms, 10),
    ]
    
    passed = sum(1 for _, duration, target in results if duration < target)
    total = len(results)
    
    print(f"\n{'Test':<30} {'Actual':<15} {'Target':<15} {'Status':<10}")
    print("-" * 75)
    for test, duration, target in results:
        status = "✅ PASS" if duration < target else "⚠️  SLOW"
        print(f"{test:<30} {duration:>8.0f}ms     {target:>8}ms       {status}")
    
    print()
    print(f"Overall: {passed}/{total} tests meeting performance targets ({passed/total*100:.0f}%)")
    
    if duration2_ms < 10:
        print("\n✅ CACHING IS WORKING - Health checks are fast when cached!")
    
    if duration_ms < 500:
        print("✅ SCHEDULING IS FAST - Composite index optimization effective!")
    
    # Cleanup
    await orchestrator.stop()
    
    print()
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_performance())
    exit(0 if success else 1)
