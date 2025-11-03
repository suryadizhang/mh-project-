"""
Quick Performance Verification
===============================
Validates Phase 1 optimizations (composite index + emotion history optimization)
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.scheduler.follow_up_scheduler import FollowUpScheduler, FollowUpTriggerType
from api.ai.memory import get_memory_backend
from api.ai.services import get_emotion_service
from api.ai.memory.memory_backend import MessageRole, ConversationChannel
from datetime import datetime, timedelta


async def quick_verify():
    """Quick performance verification"""
    
    print("=" * 80)
    print("PHASE 1 OPTIMIZATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Initialize
    memory = await get_memory_backend()
    emotion_service = get_emotion_service()
    scheduler = FollowUpScheduler(memory, emotion_service, "UTC", None)
    await scheduler.start()
    
    # Create test data
    user_id = f"verify_{time.time()}"
    conversation_id = f"verify_{time.time()}"
    event_date = datetime.utcnow() + timedelta(days=7)
    
    # Store message with emotion
    print("1. Storing message with emotion...")
    t0 = time.time()
    await memory.store_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test booking",
        channel=ConversationChannel.WEB,
        emotion_score=0.8,
        emotion_label="positive"
    )
    store_time = (time.time() - t0) * 1000
    print(f"   Time: {store_time:.0f}ms")
    print()
    
    # Test duplicate check
    print("2. Testing duplicate check (with composite index)...")
    t0 = time.time()
    has_dup = await scheduler._has_pending_followup(
        user_id,
        FollowUpTriggerType.POST_EVENT,
        event_date
    )
    dup_time = (time.time() - t0) * 1000
    status = "[+] FAST" if dup_time < 150 else "[!] SLOW"
    print(f"   Time: {dup_time:.0f}ms {status}")
    print(f"   Target: <150ms (improved from 637ms)")
    print()
    
    # Test emotion history
    print("3. Testing emotion history query (optimized SELECT)...")
    t0 = time.time()
    history = await memory.get_emotion_history(conversation_id, limit=5)
    emotion_time = (time.time() - t0) * 1000
    status = "[+] FAST" if emotion_time < 150 else "[!] SLOW"
    print(f"   Time: {emotion_time:.0f}ms {status}")
    print(f"   Target: <150ms (improved from 634ms)")
    print()
    
    # Full schedule follow-up
    print("4. Testing full schedule_follow_up operation...")
    t0 = time.time()
    job_id = await scheduler.schedule_post_event(
        conversation_id=conversation_id,
        user_id=user_id,
        event_date=event_date
    )
    schedule_time = (time.time() - t0) * 1000
    status = "[+] IMPROVED" if schedule_time < 1500 else "[!] STILL SLOW"
    print(f"   Time: {schedule_time:.0f}ms {status}")
    print(f"   Baseline: 1931ms")
    print(f"   Target: <1000ms (Phase 1), <500ms (Final)")
    improvement = ((1931 - schedule_time) / 1931) * 100
    print(f"   Improvement: {improvement:.1f}%")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Duplicate check:    {dup_time:.0f}ms (baseline: 637ms, target: <150ms)")
    print(f"Emotion history:    {emotion_time:.0f}ms (baseline: 634ms, target: <150ms)")
    print(f"Full schedule:      {schedule_time:.0f}ms (baseline: 1931ms, target: <1000ms)")
    print()
    
    dup_improvement = ((637 - dup_time) / 637) * 100
    emotion_improvement = ((634 - emotion_time) / 634) * 100
    
    print(f"Improvements:")
    print(f"  Duplicate check: {dup_improvement:+.1f}%")
    print(f"  Emotion history: {emotion_improvement:+.1f}%")
    print(f"  Full schedule:   {improvement:+.1f}%")
    print()
    
    # Cleanup
    if job_id:
        await scheduler.cancel_followup(job_id)
    await scheduler.stop()
    
    # Final verdict
    if schedule_time < 1000:
        print("[+] PHASE 1 TARGET ACHIEVED: <1000ms")
    elif schedule_time < 1500:
        print("[~] PARTIAL SUCCESS: Significant improvement but not at target yet")
    else:
        print("[!] PHASE 1 TARGET NOT MET: Additional optimization needed")
    print()


if __name__ == "__main__":
    asyncio.run(quick_verify())
