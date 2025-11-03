"""
Quick Performance Verification
===============================
Validates Phase 1 optimizations (composite index + emotion history optimization)
"""

import asyncio
from pathlib import Path
import sys
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime, timedelta

from api.ai.memory import get_memory_backend
from api.ai.memory.memory_backend import ConversationChannel, MessageRole
from api.ai.scheduler.follow_up_scheduler import (
    FollowUpScheduler,
    FollowUpTriggerType,
)
from api.ai.services import get_emotion_service


async def quick_verify():
    """Quick performance verification"""

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
    t0 = time.time()
    await memory.store_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test booking",
        channel=ConversationChannel.WEB,
        emotion_score=0.8,
        emotion_label="positive",
    )
    (time.time() - t0) * 1000

    # Test duplicate check
    t0 = time.time()
    await scheduler._has_pending_followup(user_id, FollowUpTriggerType.POST_EVENT, event_date)
    dup_time = (time.time() - t0) * 1000

    # Test emotion history
    t0 = time.time()
    await memory.get_emotion_history(conversation_id, limit=5)
    emotion_time = (time.time() - t0) * 1000

    # Full schedule follow-up
    t0 = time.time()
    job_id = await scheduler.schedule_post_event(
        conversation_id=conversation_id, user_id=user_id, event_date=event_date
    )
    schedule_time = (time.time() - t0) * 1000
    ((1931 - schedule_time) / 1931) * 100

    # Summary

    ((637 - dup_time) / 637) * 100
    ((634 - emotion_time) / 634) * 100

    # Cleanup
    if job_id:
        await scheduler.cancel_followup(job_id)
    await scheduler.stop()

    # Final verdict
    if schedule_time < 1000 or schedule_time < 1500:
        pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(quick_verify())
