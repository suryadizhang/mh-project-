"""
Detailed profiling of Phase 2A to identify remaining bottlenecks
"""

import asyncio
from pathlib import Path
import sys
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.memory.memory_backend import ConversationChannel, MessageRole
from api.ai.memory.postgresql_memory import PostgreSQLMemory


async def profile_with_breakdown():
    """Profile store_message with detailed timing breakdown"""

    memory = PostgreSQLMemory()
    await memory.initialize()

    conversation_id = f"profile_test_{int(time.time())}"

    # Profile 5 runs with detailed breakdown
    timings = []

    for i in range(5):

        t_start = time.time()

        # Call store_message (should only have UPSERT + INSERT)
        await memory.store_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=f"Test message {i+1}",
            user_id="test_user",
            channel=ConversationChannel.WEB,
            emotion_score=0.75,
        )

        t_end = time.time()
        duration = (t_end - t_start) * 1000

        timings.append(duration)

        # Give background tasks time to complete
        await asyncio.sleep(0.5)

    avg = sum(timings) / len(timings)
    min(timings)
    max(timings)

    # Theoretical breakdown

    if avg > 600:
        pass

    # Wait for all background tasks to complete
    await asyncio.sleep(3)

    # Verify emotion stats were updated

    metadata = await memory.get_conversation_metadata(conversation_id)
    if metadata:
        pass
    else:
        pass

    if avg < 700 or avg < 1000 or avg < 1500:
        pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(profile_with_breakdown())
