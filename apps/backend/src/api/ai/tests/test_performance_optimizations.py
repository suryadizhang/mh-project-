"""
Performance Test for Scheduler Optimizations
=============================================

Tests the performance improvements from:
1. Composite index on (conversation_id, emotion_score, timestamp)
2. Health check caching (30-second TTL)
3. Database ANALYZE for query planner statistics
"""

import asyncio
from datetime import datetime, timezone, timedelta
import sys
import time

from api.ai.memory import get_memory_backend
from api.ai.memory.memory_backend import MessageRole
from api.ai.orchestrator import AIOrchestrator


async def test_performance():
    """Test scheduler performance with optimizations"""

    # Initialize orchestrator
    orchestrator = AIOrchestrator(use_router=False)
    await orchestrator.start()
    memory = await get_memory_backend()

    # Test 1: Schedule Follow-Up Performance

    conv_id = f"perf_test_{time.time()}"
    user_id = f"perf_user_{time.time()}"

    # Store message first
    await memory.store_message(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content="Test booking",
        user_id=user_id,
        emotion_score=0.8,
        emotion_label="positive",
    )

    # Measure scheduling time
    start = time.time()
    job_id = await orchestrator.schedule_post_event_followup(
        conversation_id=conv_id,
        user_id=user_id,
        event_date=datetime.now(timezone.utc) + timedelta(days=7),
    )
    duration_ms = (time.time() - start) * 1000

    # Cleanup
    if job_id:
        await orchestrator.scheduler.cancel_followup(job_id)

    # Test 2: Health Check Performance (First Call)

    # Clear cache to simulate first call
    orchestrator.scheduler._health_cache = None
    orchestrator.scheduler._health_cache_time = None

    start = time.time()
    await orchestrator.scheduler.health_check()
    duration1_ms = (time.time() - start) * 1000

    # Test 3: Health Check Performance (Second Call - Should be Cached)

    start = time.time()
    await orchestrator.scheduler.health_check()
    duration2_ms = (time.time() - start) * 1000

    # Test 4: Multiple Health Checks (All Cached)

    start = time.time()
    for _i in range(10):
        await orchestrator.scheduler.health_check()
    batch_duration_ms = (time.time() - start) * 1000
    avg_duration_ms = batch_duration_ms / 10

    # Summary

    results = [
        ("Schedule follow-up", duration_ms, 500),
        ("Health check (first)", duration1_ms, 100),
        ("Health check (cached)", duration2_ms, 10),
        ("Health check (batch avg)", avg_duration_ms, 10),
    ]

    passed = sum(1 for _, duration, target in results if duration < target)
    total = len(results)

    for _test, _duration, _target in results:
        pass

    if duration2_ms < 10:
        pass

    if duration_ms < 500:
        pass

    # Cleanup
    await orchestrator.stop()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_performance())
    sys.exit(0 if success else 1)
