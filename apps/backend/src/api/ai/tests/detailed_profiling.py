"""
Detailed profiling of Phase 2A to identify remaining bottlenecks
"""
import asyncio
import time
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.memory.postgresql_memory import PostgreSQLMemory
from api.ai.memory.memory_backend import MessageRole, ConversationChannel

async def profile_with_breakdown():
    """Profile store_message with detailed timing breakdown"""
    
    memory = PostgreSQLMemory()
    await memory.initialize()
    
    conversation_id = f"profile_test_{int(time.time())}"
    
    print("=" * 70)
    print("DETAILED PHASE 2A PROFILING")
    print("=" * 70)
    print()
    
    # Profile 5 runs with detailed breakdown
    timings = []
    
    for i in range(5):
        print(f"Run {i+1}:")
        print("-" * 50)
        
        t_start = time.time()
        
        # Call store_message (should only have UPSERT + INSERT)
        message = await memory.store_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=f"Test message {i+1}",
            user_id="test_user",
            channel=ConversationChannel.WEB,
            emotion_score=0.75
        )
        
        t_end = time.time()
        duration = (t_end - t_start) * 1000
        
        print(f"  Total time: {duration:.0f}ms")
        timings.append(duration)
        
        # Give background tasks time to complete
        await asyncio.sleep(0.5)
        print()
    
    print("=" * 70)
    print("TIMING ANALYSIS")
    print("=" * 70)
    avg = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)
    
    print(f"Average: {avg:.0f}ms")
    print(f"Min:     {min_time:.0f}ms")
    print(f"Max:     {max_time:.0f}ms")
    print(f"Range:   {max_time - min_time:.0f}ms")
    print()
    
    # Theoretical breakdown
    print("THEORETICAL BREAKDOWN (assuming 270ms network latency):")
    print("-" * 70)
    print("  UPSERT conversation:     270ms  (1 query)")
    print("  INSERT message:          270ms  (1 query)")
    print("  SQLAlchemy overhead:      50ms  (object creation, validation)")
    print("  Background task setup:    10ms  (asyncio.create_task)")
    print("  " + "=" * 60)
    print("  EXPECTED TOTAL:         ~600ms")
    print()
    print(f"  ACTUAL AVERAGE:         {avg:.0f}ms")
    print(f"  DIFFERENCE:             {avg - 600:.0f}ms")
    print()
    
    if avg > 600:
        print("⚠️  WARNING: Actual time significantly exceeds theoretical minimum")
        print("   Possible causes:")
        print("   1. Network latency > 270ms (check current conditions)")
        print("   2. Connection pool contention (check pool stats)")
        print("   3. Hidden synchronous operations (check logs)")
        print("   4. Database load (check pg_stat_activity)")
        print()
    
    # Wait for all background tasks to complete
    print("Waiting 3 seconds for all background tasks to complete...")
    await asyncio.sleep(3)
    
    # Verify emotion stats were updated
    print()
    print("=" * 70)
    print("BACKGROUND TASK VERIFICATION")
    print("=" * 70)
    
    metadata = await memory.get_conversation_metadata(conversation_id)
    if metadata:
        print(f"✅ Conversation found")
        print(f"   Message count: {metadata.message_count}")
        print(f"   Average emotion: {metadata.context.get('avg_emotion_score', 'N/A')}")
        print(f"   Emotion trend: {metadata.context.get('emotion_trend', 'N/A')}")
    else:
        print("❌ Conversation not found")
    
    print()
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if avg < 700:
        print("✅ EXCELLENT: Performance within theoretical limits")
        print("   Continue with Phase 2B (connection pooling)")
    elif avg < 1000:
        print("⚠️  GOOD: Performance acceptable but can improve")
        print("   1. Proceed with Phase 2B (connection pooling)")
        print("   2. Monitor network latency")
    elif avg < 1500:
        print("⚠️  MODERATE: Performance needs improvement")
        print("   1. Check database connection pool settings")
        print("   2. Verify no synchronous emotion stats calls")
        print("   3. Monitor network latency")
    else:
        print("❌ POOR: Performance significantly below target")
        print("   1. Check for hidden synchronous operations")
        print("   2. Verify background tasks not blocking")
        print("   3. Check database server load")
        print("   4. Consider connection pooling first")
    
    print()

if __name__ == "__main__":
    asyncio.run(profile_with_breakdown())
