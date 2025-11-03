# Follow-Up Scheduler Quick Reference

## 🚀 Quick Start

### Initialize Scheduler

```python
from api.ai.scheduler import FollowUpScheduler
from api.ai.memory import PostgreSQLMemory
from api.ai.services import EmotionService

scheduler = FollowUpScheduler(
    memory=PostgreSQLMemory(),
    emotion_service=EmotionService(),
    timezone="UTC"  # or "US/Pacific", etc.
)

await scheduler.start()
```

### Schedule Post-Event Follow-Up

```python
job_id = await scheduler.schedule_post_event_followup(
    conversation_id="conv_123",
    user_id="user_456",
    event_date=datetime(2025, 11, 15, 18, 0, 0),
    booking_id="BK789",  # optional
    followup_delay=timedelta(hours=24)  # default
)

print(f"Scheduled: {job_id}")
# Output: followup_user_456_1763344800
```

### Schedule Re-Engagement

```python
job_id = await scheduler.schedule_reengagement(
    user_id="user_789",
    last_activity=datetime(2025, 10, 1),
    inactive_threshold=timedelta(days=30)  # default
)

print(f"Re-engagement scheduled: {job_id}")
# Output: reengagement_user_789_1762117811
```

### List Scheduled Follow-Ups

```python
# All pending jobs
jobs = await scheduler.get_scheduled_followups()

# Filter by user
jobs = await scheduler.get_scheduled_followups(user_id="user_456")

# Filter by status
jobs = await scheduler.get_scheduled_followups(
    status=FollowUpStatus.PENDING
)

for job in jobs:
    print(f"{job.id}: {job.scheduled_at} - {job.template_id}")
```

### Cancel Follow-Up

```python
success = await scheduler.cancel_followup(job_id="followup_user_456_1763344800")

if success:
    print("Follow-up cancelled")
else:
    print("Job not found or already executed")
```

### Health Check

```python
health = await scheduler.health_check()
print(health)
# Output:
# {
#     "status": "healthy",
#     "scheduler_running": True,
#     "pending_jobs": 5,
#     "executed_today": 12,
#     "apscheduler_jobs": 5
# }
```

---

## 📋 Trigger Types

```python
from api.ai.scheduler import FollowUpTriggerType

FollowUpTriggerType.POST_EVENT       # After event completion
FollowUpTriggerType.RE_ENGAGEMENT    # Inactive user campaign
FollowUpTriggerType.EMOTION_BASED    # Based on sentiment
FollowUpTriggerType.CUSTOM           # Custom timing
```

---

## 🎨 Template IDs

| Template ID | Trigger Type | Emotion Condition | Use Case |
|-------------|--------------|-------------------|----------|
| `post_event_high_emotion` | POST_EVENT | score ≥ 0.7 | Very positive experience |
| `post_event_neutral_emotion` | POST_EVENT | 0.4 ≤ score < 0.7 | Normal experience |
| `post_event_low_emotion` | POST_EVENT | score < 0.4 | Negative/concerned |
| `reengagement_general` | RE_ENGAGEMENT | N/A | First-time visitors |
| `reengagement_past_customer` | RE_ENGAGEMENT | N/A | Previous customers |
| `emotion_check_in` | EMOTION_BASED | N/A | Check-in after concern |
| `custom` | CUSTOM | N/A | Custom message |

---

## 📊 Job Status Flow

```
PENDING → EXECUTED
   ↓
CANCELLED
   ↓
FAILED (with retry)
```

### Status Enum

```python
from api.ai.scheduler import FollowUpStatus

FollowUpStatus.PENDING     # Scheduled, not yet executed
FollowUpStatus.EXECUTED    # Successfully sent
FollowUpStatus.CANCELLED   # Manually cancelled
FollowUpStatus.FAILED      # Execution error
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE scheduled_followups (
    id VARCHAR(255) PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_data JSONB NOT NULL DEFAULT '{}',
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    template_id VARCHAR(50),
    message_content TEXT,
    created_at TIMESTAMP NOT NULL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Indexes
CREATE INDEX ix_scheduled_followups_user_id ON scheduled_followups (user_id);
CREATE INDEX ix_scheduled_followups_conversation_id ON scheduled_followups (conversation_id);
CREATE INDEX ix_scheduled_followups_scheduled_at ON scheduled_followups (scheduled_at);
CREATE INDEX idx_scheduled_followups_status_scheduled ON scheduled_followups (status, scheduled_at);
CREATE INDEX idx_scheduled_followups_user_status ON scheduled_followups (user_id, status);
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Scheduler settings
SCHEDULER_TIMEZONE="UTC"
FOLLOWUP_DELAY_HOURS=24
REENGAGEMENT_INACTIVE_DAYS=30
SCHEDULER_ENABLED=true

# Database (already configured)
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
MEMORY_BACKEND="postgresql"
```

### Python Settings

```python
from core.config import Settings

class Settings(BaseSettings):
    SCHEDULER_TIMEZONE: str = "UTC"
    FOLLOWUP_DELAY_HOURS: int = 24
    REENGAGEMENT_INACTIVE_DAYS: int = 30
    SCHEDULER_ENABLED: bool = True
```

---

## 🧪 Testing

### Run All Tests

```bash
cd apps/backend
$env:PYTHONPATH="$PWD/src"
$env:MEMORY_BACKEND="postgresql"
python src/api/ai/tests/test_follow_up_scheduler.py
```

### Run Specific Test

```bash
python src/api/ai/tests/test_follow_up_scheduler.py TestFollowUpScheduler.test_03_emotion_based_template_selection
```

### Expected Output

```
Ran 10 tests in 48.645s
OK
Tests run: 10
Passed: 10
Failed: 0
Errors: 0
✅ ALL TESTS PASSED
```

---

## 🔧 Common Operations

### Stop Scheduler

```python
await scheduler.stop()
# Gracefully stops all jobs and shuts down APScheduler
```

### Get Pending Job Count

```python
jobs = await scheduler.get_scheduled_followups(
    status=FollowUpStatus.PENDING
)
count = len(jobs)
print(f"Pending: {count}")
```

### Get Jobs Scheduled Today

```python
from datetime import datetime, timedelta

today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
today_end = today_start + timedelta(days=1)

# Query database directly
async with get_db_context() as db:
    query = select(ScheduledFollowUp).where(
        and_(
            ScheduledFollowUp.scheduled_at >= today_start,
            ScheduledFollowUp.scheduled_at < today_end
        )
    )
    result = await db.execute(query)
    jobs = result.scalars().all()
```

### Reschedule Job

```python
# Cancel existing job
await scheduler.cancel_followup(old_job_id)

# Schedule new one
new_job_id = await scheduler.schedule_post_event_followup(
    conversation_id=conversation_id,
    user_id=user_id,
    event_date=new_event_date
)
```

---

## 🐛 Troubleshooting

### Issue: Jobs Not Executing

**Check scheduler status:**
```python
health = await scheduler.health_check()
if not health["scheduler_running"]:
    await scheduler.start()
```

**Check APScheduler:**
```python
jobs = scheduler.scheduler.get_jobs()
print(f"APScheduler has {len(jobs)} jobs")
```

### Issue: Duplicate Jobs Created

**Reason:** Event dates within ±1 day tolerance  
**Solution:** Space events at least 2 days apart or adjust tolerance

```python
# In follow_up_scheduler.py _has_pending_followup()
date_start = event_date - timedelta(days=2)  # Increase tolerance
date_end = event_date + timedelta(days=2)
```

### Issue: Wrong Template Selected

**Check emotion history:**
```python
history = await scheduler.memory.get_emotion_history(
    conversation_id=conv_id,
    limit=5
)
print(f"Emotion history: {history}")

# Calculate average
scores = [e["score"] for e in history if e.get("score")]
if scores:
    avg = sum(scores) / len(scores)
    print(f"Average emotion: {avg}")
```

**Verify template selection:**
- High emotion: score ≥ 0.7 → `post_event_high_emotion`
- Neutral: 0.4 ≤ score < 0.7 → `post_event_neutral_emotion`
- Low emotion: score < 0.4 → `post_event_low_emotion`

### Issue: Database Connection Errors

**Check PostgreSQL connection:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM scheduled_followups;"
```

**Verify table exists:**
```python
from api.ai.memory.create_tables import create_ai_memory_tables
await create_ai_memory_tables()
```

---

## 📈 Monitoring

### Key Metrics to Track

1. **Scheduled Jobs:** `SELECT COUNT(*) FROM scheduled_followups WHERE status = 'pending'`
2. **Executed Today:** `SELECT COUNT(*) FROM scheduled_followups WHERE DATE(executed_at) = CURRENT_DATE`
3. **Failed Jobs:** `SELECT COUNT(*) FROM scheduled_followups WHERE status = 'failed'`
4. **Average Execution Time:** `SELECT AVG(EXTRACT(EPOCH FROM (executed_at - scheduled_at))) FROM scheduled_followups WHERE executed_at IS NOT NULL`

### Health Check Endpoint

```python
# In FastAPI app
@app.get("/api/scheduler/health")
async def scheduler_health():
    scheduler = get_scheduler()
    return await scheduler.health_check()
```

### Logging

```python
import logging

# Enable scheduler logging
logging.getLogger('api.ai.scheduler').setLevel(logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.INFO)
```

---

## 🔗 Integration Examples

### With FastAPI

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global scheduler
    scheduler = FollowUpScheduler(
        memory=PostgreSQLMemory(),
        emotion_service=EmotionService()
    )
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/bookings/{booking_id}/schedule-followup")
async def schedule_followup(booking_id: str, event_date: datetime):
    job_id = await scheduler.schedule_post_event_followup(
        conversation_id=f"booking_{booking_id}",
        user_id=current_user.id,
        event_date=event_date,
        booking_id=booking_id
    )
    return {"job_id": job_id}
```

### With Background Tasks

```python
from fastapi import BackgroundTasks

async def check_inactive_users():
    """Background task to check for inactive users"""
    inactive_threshold = datetime.utcnow() - timedelta(days=30)
    users = await get_inactive_users(since=inactive_threshold)
    
    for user in users:
        await scheduler.schedule_reengagement(
            user_id=user.id,
            last_activity=user.last_activity_at
        )

@app.on_event("startup")
async def schedule_background_tasks():
    # Run daily at 9 AM
    scheduler.scheduler.add_job(
        check_inactive_users,
        trigger='cron',
        hour=9,
        minute=0
    )
```

---

## 📚 API Reference

### FollowUpScheduler

**Constructor:**
```python
FollowUpScheduler(
    memory: MemoryBackend,
    emotion_service: EmotionService,
    timezone: str = "UTC"
)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `start()` | None | None | Start scheduler |
| `stop()` | None | None | Stop scheduler |
| `schedule_post_event_followup()` | `conversation_id`, `user_id`, `event_date`, `booking_id`, `followup_delay` | `Optional[str]` | Schedule post-event follow-up |
| `schedule_reengagement()` | `user_id`, `last_activity`, `inactive_threshold` | `Optional[str]` | Schedule re-engagement |
| `cancel_followup()` | `job_id` | `bool` | Cancel scheduled job |
| `get_scheduled_followups()` | `user_id`, `status`, `limit` | `List[FollowUpJob]` | List scheduled jobs |
| `health_check()` | None | `Dict[str, Any]` | Get scheduler status |

---

## 🎯 Best Practices

1. **Always check return value:** `schedule_*` methods return `None` if duplicate detected
2. **Use timezone-aware datetimes:** Specify timezone explicitly to avoid ambiguity
3. **Monitor health regularly:** Use `health_check()` to track scheduler status
4. **Clean up old jobs:** Periodically delete executed jobs older than 90 days
5. **Test with production data:** Use realistic emotion scores and event dates in tests
6. **Log all operations:** Enable INFO logging for debugging

---

## 📝 Changelog

### v1.0.0 (November 2, 2025)
- ✅ Initial release
- ✅ 10/10 tests passing
- ✅ Production ready
- ✅ Emotion-aware template selection
- ✅ PostgreSQL persistence
- ✅ APScheduler integration
- ✅ Duplicate prevention
- ✅ Health monitoring

---

**For detailed documentation, see:** `PHASE_1B_TASK3_SMART_FOLLOWUP_SCHEDULER_COMPLETE.md`
