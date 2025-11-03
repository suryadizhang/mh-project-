"""
Deep Performance Profiling: Schedule Follow-Up
Measures each operation in schedule_follow_up to identify bottlenecks
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.scheduler.follow_up_scheduler import FollowUpScheduler, FollowUpTriggerType
from api.ai.memory import get_memory_backend
from api.ai.services import get_emotion_service


async def profile_schedule_followup():
    """Profile each step of schedule_follow_up"""
    
    print("=" * 80)
    print("SCHEDULE FOLLOW-UP DEEP PERFORMANCE PROFILE")
    print("=" * 80)
    print()
    
    # Initialize components
    print("[*] Initializing components...")
    t_start = time.time()
    
    memory = await get_memory_backend()
    emotion_service = get_emotion_service()
    scheduler = FollowUpScheduler(memory, emotion_service, "UTC", None)
    await scheduler.start()
    
    t_init = time.time()
    print(f"   Initialization: {(t_init - t_start) * 1000:.0f}ms")
    print()
    
    # Create test data
    user_id = f"profile_user_{time.time()}"
    conversation_id = f"profile_conv_{time.time()}"
    event_date = datetime.utcnow() + timedelta(days=7)
    
    print("[*] OPERATION BREAKDOWN")
    print("-" * 80)
    
    # Step 1: Store message with emotion
    t0 = time.time()
    from api.ai.memory.memory_backend import MessageRole, ConversationChannel
    
    await memory.store_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test booking message",
        channel=ConversationChannel.WEB,
        emotion_score=0.8,
        emotion_label="positive"
    )
    t1 = time.time()
    store_time = (t1 - t0) * 1000
    print(f"1. Store message (with emotion):        {store_time:.0f}ms")
    
    # Step 2: Check for duplicates
    t2 = time.time()
    has_duplicate = await scheduler._has_pending_followup(
        user_id, 
        FollowUpTriggerType.POST_EVENT,
        event_date
    )
    t3 = time.time()
    duplicate_check_time = (t3 - t2) * 1000
    print(f"2. Check for duplicate follow-ups:      {duplicate_check_time:.0f}ms")
    
    # Step 3: Get emotion history
    t4 = time.time()
    emotion_history = await memory.get_emotion_history(conversation_id, limit=5)
    t5 = time.time()
    emotion_history_time = (t5 - t4) * 1000
    print(f"3. Get emotion history (5 messages):    {emotion_history_time:.0f}ms")
    
    # Step 4: Select template by emotion
    t6 = time.time()
    template = await scheduler._select_template_by_emotion(
        FollowUpTriggerType.POST_EVENT,
        emotion_history
    )
    t7 = time.time()
    template_select_time = (t7 - t6) * 1000
    print(f"4. Select template by emotion:          {template_select_time:.0f}ms")
    
    # Step 5: Render template
    t8 = time.time()
    message_content = scheduler._render_template(template, {
        "event_date": event_date.strftime("%B %d, %Y")
    })
    t9 = time.time()
    render_time = (t9 - t8) * 1000
    print(f"5. Render template:                      {render_time:.0f}ms")
    
    # Step 6: Insert into database
    t10 = time.time()
    from api.ai.scheduler.models import ScheduledFollowUp, FollowUpStatus
    from api.ai.memory.database import get_db_context
    
    scheduled_at = event_date + timedelta(hours=24)
    job_id = f"profile_{user_id}_{int(scheduled_at.timestamp())}"
    
    async with get_db_context() as db:
        followup = ScheduledFollowUp(
            id=job_id,
            conversation_id=conversation_id,
            user_id=user_id,
            trigger_type=FollowUpTriggerType.POST_EVENT.value,
            trigger_data={
                "event_date": event_date.isoformat(),
                "booking_id": None,
                "followup_delay_hours": 24.0
            },
            scheduled_at=scheduled_at,
            status=FollowUpStatus.PENDING.value,
            template_id=template.id,
            message_content=message_content
        )
        db.add(followup)
        await db.commit()
    
    t11 = time.time()
    db_insert_time = (t11 - t10) * 1000
    print(f"6. Insert follow-up into database:      {db_insert_time:.0f}ms")
    
    # Step 7: Schedule APScheduler job
    from apscheduler.triggers.date import DateTrigger
    import pytz
    
    t12 = time.time()
    scheduler.scheduler.add_job(
        scheduler._execute_followup,
        trigger=DateTrigger(run_date=scheduled_at, timezone=pytz.UTC),
        args=[job_id],
        id=job_id,
        replace_existing=True
    )
    t13 = time.time()
    scheduler_add_time = (t13 - t12) * 1000
    print(f"7. Add job to APScheduler:               {scheduler_add_time:.0f}ms")
    
    # Total time
    total_time = (t13 - t0) * 1000
    print("-" * 80)
    print(f"TOTAL TIME:                              {total_time:.0f}ms")
    print()
    
    # Analysis
    print("=" * 80)
    print("BOTTLENECK ANALYSIS")
    print("=" * 80)
    print()
    
    operations = [
        ("Store message", store_time),
        ("Duplicate check", duplicate_check_time),
        ("Get emotion history", emotion_history_time),
        ("Select template", template_select_time),
        ("Render template", render_time),
        ("Database insert", db_insert_time),
        ("Add to scheduler", scheduler_add_time),
    ]
    
    # Sort by time descending
    sorted_ops = sorted(operations, key=lambda x: x[1], reverse=True)
    
    print("Operations ranked by time (slowest first):")
    print()
    for i, (name, op_time) in enumerate(sorted_ops, 1):
        percent = (op_time / total_time) * 100
        bar_length = int(percent / 2)  # Scale to 50 chars max
        bar = "█" * bar_length
        print(f"{i}. {name:.<35} {op_time:>6.0f}ms ({percent:>5.1f}%) {bar}")
    
    print()
    print("=" * 80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    # Identify optimization opportunities
    if store_time > 500:
        print("[!] Store message is slow (>500ms)")
        print("   Potential causes:")
        print("   - Multiple database writes (message + conversation update)")
        print("   - Emotion statistics calculation (_update_emotion_stats)")
        print("   - Missing indexes on ai_messages")
        print("   Solutions:")
        print("   * Batch database operations")
        print("   * Cache emotion statistics")
        print("   * Use database triggers for stats updates")
        print()
    
    if duplicate_check_time > 100:
        print("[!] Duplicate check is slow (>100ms)")
        print("   Potential causes:")
        print("   - Missing composite index on (user_id, trigger_type, status)")
        print("   - Date range query inefficiency")
        print("   Solutions:")
        print("   * Add composite index: (user_id, trigger_type, status, scheduled_at)")
        print()
    
    if emotion_history_time > 100:
        print("[!] Emotion history query is slow (>100ms)")
        print("   Potential causes:")
        print("   - Composite index not being used")
        print("   - Query planner choosing wrong execution plan")
        print("   Solutions:")
        print("   * Run EXPLAIN ANALYZE on the query")
        print("   * Force index hint if PostgreSQL not using composite index")
        print()
    
    if db_insert_time > 200:
        print("[!] Database insert is slow (>200ms)")
        print("   Potential causes:")
        print("   - Trigger overhead")
        print("   - Lock contention")
        print("   - fsync latency")
        print("   Solutions:")
        print("   * Check for unnecessary triggers")
        print("   * Consider connection pooling settings")
        print()
    
    # Cleanup
    await scheduler.cancel_followup(job_id)
    await scheduler.stop()
    
    print()
    print("[+] Profile complete!")
    

if __name__ == "__main__":
    asyncio.run(profile_schedule_followup())
