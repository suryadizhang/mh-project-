"""
Deep Performance Profiling: Schedule Follow-Up
Measures each operation in schedule_follow_up to identify bottlenecks
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.ai.memory import get_memory_backend
from api.ai.scheduler.follow_up_scheduler import (
    FollowUpScheduler,
    FollowUpTriggerType,
)
from api.ai.services import get_emotion_service


async def profile_schedule_followup():
    """Profile each step of schedule_follow_up"""

    # Initialize components
    time.time()

    memory = await get_memory_backend()
    emotion_service = get_emotion_service()
    scheduler = FollowUpScheduler(memory, emotion_service, "UTC", None)
    await scheduler.start()

    time.time()

    # Create test data
    user_id = f"profile_user_{time.time()}"
    conversation_id = f"profile_conv_{time.time()}"
    event_date = datetime.utcnow() + timedelta(days=7)

    # Step 1: Store message with emotion
    t0 = time.time()
    from api.ai.memory.memory_backend import ConversationChannel, MessageRole

    await memory.store_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content="Test booking message",
        channel=ConversationChannel.WEB,
        emotion_score=0.8,
        emotion_label="positive",
    )
    t1 = time.time()
    store_time = (t1 - t0) * 1000

    # Step 2: Check for duplicates
    t2 = time.time()
    await scheduler._has_pending_followup(user_id, FollowUpTriggerType.POST_EVENT, event_date)
    t3 = time.time()
    duplicate_check_time = (t3 - t2) * 1000

    # Step 3: Get emotion history
    t4 = time.time()
    emotion_history = await memory.get_emotion_history(conversation_id, limit=5)
    t5 = time.time()
    emotion_history_time = (t5 - t4) * 1000

    # Step 4: Select template by emotion
    t6 = time.time()
    template = await scheduler._select_template_by_emotion(
        FollowUpTriggerType.POST_EVENT, emotion_history
    )
    t7 = time.time()
    template_select_time = (t7 - t6) * 1000

    # Step 5: Render template
    t8 = time.time()
    message_content = scheduler._render_template(
        template, {"event_date": event_date.strftime("%B %d, %Y")}
    )
    t9 = time.time()
    render_time = (t9 - t8) * 1000

    # Step 6: Insert into database
    t10 = time.time()
    from api.ai.memory.database import get_db_context
    from api.ai.scheduler.models import FollowUpStatus, ScheduledFollowUp

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
                "followup_delay_hours": 24.0,
            },
            scheduled_at=scheduled_at,
            status=FollowUpStatus.PENDING.value,
            template_id=template.id,
            message_content=message_content,
        )
        db.add(followup)
        await db.commit()

    t11 = time.time()
    db_insert_time = (t11 - t10) * 1000

    # Step 7: Schedule APScheduler job
    from apscheduler.triggers.date import DateTrigger
    import pytz

    t12 = time.time()
    scheduler.scheduler.add_job(
        scheduler._execute_followup,
        trigger=DateTrigger(run_date=scheduled_at, timezone=pytz.UTC),
        args=[job_id],
        id=job_id,
        replace_existing=True,
    )
    t13 = time.time()
    scheduler_add_time = (t13 - t12) * 1000

    # Total time
    total_time = (t13 - t0) * 1000

    # Analysis

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

    for _i, (_name, op_time) in enumerate(sorted_ops, 1):
        percent = (op_time / total_time) * 100
        bar_length = int(percent / 2)  # Scale to 50 chars max
        "█" * bar_length

    # Identify optimization opportunities
    if store_time > 500:
        pass

    if duplicate_check_time > 100:
        pass

    if emotion_history_time > 100:
        pass

    if db_insert_time > 200:
        pass

    # Cleanup
    await scheduler.cancel_followup(job_id)
    await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(profile_schedule_followup())
