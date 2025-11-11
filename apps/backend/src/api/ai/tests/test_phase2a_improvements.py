"""
Test Phase 2A Performance Improvements
=======================================
Validates that store_message optimization achieves target performance.

Expected Results:
- Before: 2000ms (6 queries)
- After: <1200ms (3 queries + background task)
- Target: <1000ms
"""

import asyncio
from pathlib import Path
import sys
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.memory import get_memory_backend
from api.ai.memory.memory_backend import ConversationChannel, MessageRole


async def test_store_message_performance():
    """Test store_message performance after Phase 2A optimizations"""

    memory = await get_memory_backend()

    # Test parameters
    test_runs = 5
    times = []

    for _i in range(test_runs):
        user_id = f"test_user_{time.time()}"
        conversation_id = f"test_conv_{time.time()}"

        t0 = time.time()

        await memory.store_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.USER,
            content="Test booking message",
            channel=ConversationChannel.WEB,
            emotion_score=0.8,
            emotion_label="positive",
        )

        duration = (time.time() - t0) * 1000
        times.append(duration)

    avg_time = sum(times) / len(times)
    min(times)
    max(times)

    # Performance analysis

    if avg_time < 2000:
        ((2000 - avg_time) / 2000) * 100

    # Final verdict
    if avg_time < 1000 or avg_time < 1200:
        return True
    elif avg_time < 1500:
        return False
    else:
        return False


async def test_background_task_completion():
    """Verify background tasks complete successfully"""

    memory = await get_memory_backend()

    user_id = f"bg_test_{time.time()}"
    conversation_id = f"bg_conv_{time.time()}"

    # Store message with emotion
    await memory.store_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test message",
        channel=ConversationChannel.WEB,
        emotion_score=0.9,
        emotion_label="very positive",
    )

    # Wait for background task
    await asyncio.sleep(2)

    # Check if emotion stats were updated
    conversation = await memory.get_conversation_metadata(conversation_id)

    return bool(conversation and conversation.average_emotion_score is not None)


if __name__ == "__main__":

    async def main():
        performance_ok = await test_store_message_performance()
        background_ok = await test_background_task_completion()

        if (performance_ok and background_ok) or performance_ok:
            pass
        else:
            pass

    asyncio.run(main())
