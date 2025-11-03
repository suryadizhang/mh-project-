# Follow-Up Scheduler Operations Guide

**Version:** 1.0.0  
**Last Updated:** November 2, 2025  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Deployment](#deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)
8. [Security](#security)

---

## Overview

The Follow-Up Scheduler is an automated engagement system that schedules and executes:

- **Post-Event Follow-Ups:** 24 hours after booking/event completion
- **Re-Engagement Campaigns:** For users inactive 30+ days
- **Emotion-Based Messaging:** Context-aware templates based on sentiment

### Key Components

```
┌──────────────────────────────────────────────────────────────┐
│                    AI Orchestrator                            │
│  ┌────────────────────────────────────────────────────┐      │
│  │           FollowUpScheduler                         │      │
│  │  ┌─────────────────────────────────────────────┐   │      │
│  │  │  APScheduler (Background Jobs)               │   │      │
│  │  └─────────────────────────────────────────────┘   │      │
│  │  ┌─────────────────────────────────────────────┐   │      │
│  │  │  PostgreSQL (Job Persistence)                │   │      │
│  │  └─────────────────────────────────────────────┘   │      │
│  │  ┌─────────────────────────────────────────────┐   │      │
│  │  │  Memory Backend (Emotion History)            │   │      │
│  │  └─────────────────────────────────────────────┘   │      │
│  └────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture

### System Components

**1. AI Orchestrator (`ai_orchestrator.py`)**
- Initializes and manages scheduler lifecycle
- Provides callback for message sending
- Integrates with memory backend and emotion service

**2. Follow-Up Scheduler (`follow_up_scheduler.py`)**
- Schedules and executes follow-up jobs
- Manages APScheduler instance
- Handles template selection based on emotions
- Persists jobs to PostgreSQL

**3. Inactive User Detection (`inactive_user_detection.py`)**
- Daily background task (runs at 9 AM)
- Queries for users inactive 30+ days
- Schedules re-engagement campaigns

**4. Database Schema (`scheduled_followups` table)**
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
    retry_count INTEGER DEFAULT 0,
    
    -- Indexes for performance
    INDEX ix_scheduled_followups_user_id (user_id),
    INDEX ix_scheduled_followups_conversation_id (conversation_id),
    INDEX ix_scheduled_followups_scheduled_at (scheduled_at),
    INDEX idx_scheduled_followups_status_scheduled (status, scheduled_at),
    INDEX idx_scheduled_followups_user_status (user_id, status)
);
```

### Data Flow

**Booking Confirmation → Follow-Up:**
```
1. User completes booking
2. AIOrchestrator.schedule_post_event_followup() called
3. Scheduler queries emotion history
4. Template selected based on emotion
5. Job stored in PostgreSQL
6. APScheduler schedules execution
7. At scheduled time:
   a. _execute_followup() called
   b. orchestrator_callback() sends message
   c. Job marked as EXECUTED
```

**Inactive User → Re-Engagement:**
```
1. Daily cron job runs at 9 AM
2. inactive_user_detection queries for users (last_activity > 30d)
3. For each user:
   a. schedule_reengagement() called
   b. Job stored in PostgreSQL
   c. APScheduler schedules execution
4. At scheduled time, follow-up executed
```

---

## Deployment

### Prerequisites

**Required:**
- Python 3.9+
- PostgreSQL 13+
- Redis (for rate limiting, optional)

**Python Dependencies:**
```bash
apscheduler==3.10.4
pytz==2025.2
tzlocal==5.3.1
sqlalchemy>=2.0
asyncpg>=0.29
```

### Installation Steps

**1. Install Dependencies**
```bash
cd apps/backend
pip install -r requirements.txt
```

**2. Configure Environment**
```bash
# .env file
MEMORY_BACKEND=postgresql
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/myhibachi
SCHEDULER_TIMEZONE=America/Los_Angeles
FOLLOWUP_DELAY_HOURS=24
REENGAGEMENT_INACTIVE_DAYS=30
SCHEDULER_ENABLED=true
```

**3. Create Database Tables**
```bash
cd apps/backend
export PYTHONPATH="$PWD/src"
export MEMORY_BACKEND=postgresql
python src/api/ai/memory/create_tables.py
```

Expected output:
```
INFO:api.ai.memory.create_tables:✅ AI memory tables created successfully
INFO:api.ai.memory.create_tables:Created tables: ['ai_conversations', 'ai_messages', 'scheduled_followups']
```

**4. Run Tests**
```bash
# Unit tests
python src/api/ai/tests/test_follow_up_scheduler.py

# Integration tests
python src/api/ai/tests/test_scheduler_integration.py
```

Expected: All tests passing

**5. Start Application**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Check logs for:
```
✅ Memory backend and emotion service initialized
✅ Follow-up scheduler initialized (timezone: America/Los_Angeles)
✅ AI Orchestrator with Follow-Up Scheduler started
✅ Daily inactive user re-engagement check scheduled (9 AM)
```

### Docker Deployment

**Dockerfile additions:**
```dockerfile
# Install scheduler dependencies
RUN pip install apscheduler==3.10.4 pytz tzlocal

# Create tables on startup
CMD ["sh", "-c", "python src/api/ai/memory/create_tables.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
```

**docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      - MEMORY_BACKEND=postgresql
      - SCHEDULER_TIMEZONE=America/Los_Angeles
      - SCHEDULER_ENABLED=true
    depends_on:
      - postgres
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_BACKEND` | - | **Required.** Set to `postgresql` |
| `DATABASE_URL` | - | **Required.** PostgreSQL connection string |
| `SCHEDULER_TIMEZONE` | `UTC` | Timezone for scheduler (use IANA names) |
| `FOLLOWUP_DELAY_HOURS` | `24` | Hours after event to send follow-up |
| `REENGAGEMENT_INACTIVE_DAYS` | `30` | Days of inactivity before re-engagement |
| `SCHEDULER_ENABLED` | `true` | Enable/disable scheduler |

### Timezone Configuration

**Supported timezones** (IANA format):
- `UTC`
- `America/Los_Angeles` (PST/PDT)
- `America/New_York` (EST/EDT)
- `America/Chicago` (CST/CDT)
- `Europe/London` (GMT/BST)
- `Asia/Tokyo` (JST)

**Change timezone:**
```bash
export SCHEDULER_TIMEZONE="America/Los_Angeles"
```

### Template Customization

Templates are defined in `follow_up_scheduler.py`:

```python
FOLLOW_UP_TEMPLATES = {
    "post_event_high_emotion": {
        "id": "post_event_high_emotion",
        "content": "Hi! 🎉 I hope your event on {event_date} was amazing! ..."
    },
    # ... more templates
}
```

**To customize:**
1. Edit template content in `follow_up_scheduler.py`
2. Restart application
3. New follow-ups will use updated templates

**Available variables:**
- `{event_date}` - Event date (formatted)
- `{booking_id}` - Booking ID
- `{days_inactive}` - Days since last activity
- `{custom_message}` - Custom message content

---

## Monitoring

### Health Check

**HTTP Endpoint:**
```bash
curl http://localhost:8000/api/scheduler/health
```

**Response:**
```json
{
  "status": "healthy",
  "scheduler_running": true,
  "pending_jobs": 5,
  "executed_today": 12,
  "apscheduler_jobs": 5
}
```

**Programmatic:**
```python
orchestrator = app.state.orchestrator
health = await orchestrator.scheduler.health_check()
```

### Key Metrics

**1. Scheduled Jobs**
```sql
SELECT COUNT(*) FROM scheduled_followups WHERE status = 'pending';
```

**2. Executed Today**
```sql
SELECT COUNT(*) 
FROM scheduled_followups 
WHERE DATE(executed_at) = CURRENT_DATE;
```

**3. Failed Jobs**
```sql
SELECT id, user_id, error_message, retry_count
FROM scheduled_followups 
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

**4. Execution Rate**
```sql
SELECT 
    DATE(executed_at) as date,
    COUNT(*) as executed,
    AVG(EXTRACT(EPOCH FROM (executed_at - scheduled_at))) as avg_delay_seconds
FROM scheduled_followups 
WHERE executed_at IS NOT NULL
GROUP BY DATE(executed_at)
ORDER BY date DESC
LIMIT 7;
```

**5. Template Distribution**
```sql
SELECT template_id, COUNT(*) as count
FROM scheduled_followups
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY template_id
ORDER BY count DESC;
```

### Logging

**Enable debug logging:**
```python
import logging
logging.getLogger('api.ai.scheduler').setLevel(logging.DEBUG)
logging.getLogger('apscheduler').setLevel(logging.INFO)
```

**Key log messages:**
- `✅ Follow-up scheduler started`
- `Scheduled post-event follow-up: <job_id>`
- `Successfully executed follow-up: <job_id>`
- `❌ Failed to execute follow-up: <error>`

### Alerting

**Recommended alerts:**

1. **High Failure Rate**
   ```sql
   SELECT COUNT(*) FROM scheduled_followups 
   WHERE status = 'failed' 
   AND created_at > NOW() - INTERVAL '1 hour'
   ```
   Alert if > 10 in 1 hour

2. **Scheduler Down**
   Check health endpoint every 5 minutes
   Alert if `scheduler_running = false`

3. **Execution Delays**
   ```sql
   SELECT AVG(EXTRACT(EPOCH FROM (executed_at - scheduled_at))) / 60 as avg_delay_minutes
   FROM scheduled_followups 
   WHERE executed_at > NOW() - INTERVAL '1 hour'
   ```
   Alert if > 30 minutes

4. **Pending Job Backlog**
   ```sql
   SELECT COUNT(*) FROM scheduled_followups 
   WHERE status = 'pending' 
   AND scheduled_at < NOW() - INTERVAL '1 hour'
   ```
   Alert if > 50 overdue jobs

---

## Troubleshooting

### Issue: Scheduler Not Starting

**Symptoms:**
- Log message: `⚠️ Scheduler not initialized (missing dependencies)`
- No follow-ups being scheduled

**Diagnosis:**
```python
# Check if memory backend is available
from api.ai.memory import get_memory_backend
memory = get_memory_backend()
print(f"Memory backend: {memory}")

# Check if emotion service is available
from api.ai.services import get_emotion_service
emotion_service = get_emotion_service()
print(f"Emotion service: {emotion_service}")
```

**Solution:**
1. Verify `MEMORY_BACKEND=postgresql` is set
2. Check PostgreSQL connection
3. Run `create_tables.py` to ensure tables exist
4. Restart application

### Issue: Jobs Not Executing

**Symptoms:**
- Jobs stuck in PENDING status
- `scheduled_at` in the past but not executed

**Diagnosis:**
```python
# Check APScheduler jobs
jobs = orchestrator.scheduler.scheduler.get_jobs()
print(f"APScheduler has {len(jobs)} jobs")

# Check database pending jobs
SELECT id, scheduled_at, created_at 
FROM scheduled_followups 
WHERE status = 'pending' 
AND scheduled_at < NOW()
ORDER BY scheduled_at DESC 
LIMIT 10;
```

**Solution:**
1. Check if scheduler is running: `await scheduler.health_check()`
2. Check logs for execution errors
3. Restart scheduler: `await scheduler.stop(); await scheduler.start()`
4. If jobs are old, consider cancelling and rescheduling

### Issue: Duplicate Follow-Ups

**Symptoms:**
- Multiple follow-ups scheduled for same user/event
- `schedule_post_event_followup()` returns None but job exists

**Diagnosis:**
```sql
SELECT user_id, event_date, COUNT(*) 
FROM (
    SELECT user_id, trigger_data->>'event_date' as event_date
    FROM scheduled_followups 
    WHERE trigger_type = 'post_event'
    AND status = 'pending'
) t
GROUP BY user_id, event_date
HAVING COUNT(*) > 1;
```

**Solution:**
Duplicate prevention uses ±1 day tolerance. If events are close together:
1. Adjust spacing between event dates
2. Or modify tolerance in `_has_pending_followup()`

### Issue: Wrong Template Selected

**Symptoms:**
- High emotion conversation gets neutral template
- Low emotion conversation gets high emotion template

**Diagnosis:**
```python
# Check emotion history
history = await memory.get_emotion_history(conversation_id, limit=5)
print(f"Emotion history: {history}")

# Calculate average
scores = [e["score"] for e in history if e.get("score")]
if scores:
    avg = sum(scores) / len(scores)
    print(f"Average emotion: {avg}")
```

**Template Selection Rules:**
- High: score ≥ 0.7 → `post_event_high_emotion`
- Neutral: 0.4 ≤ score < 0.7 → `post_event_neutral_emotion`
- Low: score < 0.4 → `post_event_low_emotion`

**Solution:**
1. Verify emotion scores are being stored correctly
2. Check that messages have emotion_score set
3. Ensure conversation_id matches between message storage and scheduling

### Issue: Database Connection Errors

**Symptoms:**
- `asyncpg.exceptions.ConnectionDoesNotExistError`
- Jobs not persisting

**Diagnosis:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM scheduled_followups;"
```

**Solution:**
1. Verify DATABASE_URL is correct
2. Check PostgreSQL is running
3. Verify database user has permissions
4. Check connection pool settings

---

## Maintenance

### Daily Tasks

1. **Check Health**
   ```bash
   curl http://localhost:8000/api/scheduler/health
   ```

2. **Monitor Failed Jobs**
   ```sql
   SELECT COUNT(*) FROM scheduled_followups WHERE status = 'failed';
   ```

3. **Review Execution Rate**
   ```sql
   SELECT COUNT(*) FROM scheduled_followups 
   WHERE DATE(executed_at) = CURRENT_DATE;
   ```

### Weekly Tasks

1. **Clean Up Old Jobs** (keep 90 days)
   ```sql
   DELETE FROM scheduled_followups 
   WHERE status = 'executed' 
   AND executed_at < NOW() - INTERVAL '90 days';
   ```

2. **Analyze Template Performance**
   ```sql
   SELECT 
       template_id,
       COUNT(*) as used,
       COUNT(CASE WHEN status = 'executed' THEN 1 END) as executed,
       COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
   FROM scheduled_followups 
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY template_id;
   ```

3. **Check Inactive User Detection**
   ```bash
   # Check last run of daily job
   docker logs backend 2>&1 | grep "Daily re-engagement check"
   ```

### Monthly Tasks

1. **Database Vacuum**
   ```sql
   VACUUM ANALYZE scheduled_followups;
   ```

2. **Index Maintenance**
   ```sql
   REINDEX TABLE scheduled_followups;
   ```

3. **Performance Review**
   - Average execution delay
   - Failed job rate
   - Template effectiveness

### Backup

**Database Backup:**
```bash
pg_dump -t scheduled_followups -t ai_conversations -t ai_messages \
    $DATABASE_URL > scheduler_backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql $DATABASE_URL < scheduler_backup_20251102.sql
```

---

## Security

### Access Control

**Database:**
- Use least-privilege principle
- Scheduler needs: SELECT, INSERT, UPDATE on `scheduled_followups`
- Read-only for monitoring queries

**API:**
- Protect scheduler endpoints with authentication
- Limit who can schedule/cancel follow-ups

### Data Privacy

**PII in Messages:**
- Message content may contain PII
- Ensure `message_content` column is encrypted at rest
- Implement data retention policies

**User IDs:**
- Hash or anonymize user_ids where possible
- Implement right-to-be-forgotten
  ```sql
  DELETE FROM scheduled_followups WHERE user_id = '<user_id>';
  DELETE FROM ai_messages WHERE user_id = '<user_id>';
  DELETE FROM ai_conversations WHERE user_id = '<user_id>';
  ```

### Rate Limiting

**Prevent abuse:**
```python
# Limit follow-ups per user
MAX_PENDING_FOLLOWUPS_PER_USER = 10

async def schedule_with_limit(user_id, ...):
    pending = await scheduler.get_scheduled_followups(
        user_id=user_id,
        status=FollowUpStatus.PENDING
    )
    if len(pending) >= MAX_PENDING_FOLLOWUPS_PER_USER:
        raise ValueError("Too many pending follow-ups")
    
    return await scheduler.schedule_post_event_followup(...)
```

---

## Best Practices

### Development

1. **Always use timezone-aware datetimes**
   ```python
   from datetime import datetime, timezone
   event_date = datetime(2025, 11, 15, 18, 0, tzinfo=timezone.utc)
   ```

2. **Check return values**
   ```python
   job_id = await scheduler.schedule_post_event_followup(...)
   if not job_id:
       logger.warning("Follow-up not scheduled (duplicate or error)")
   ```

3. **Handle errors gracefully**
   ```python
   try:
       await orchestrator.schedule_post_event_followup(...)
   except Exception as e:
       logger.error(f"Failed to schedule follow-up: {e}")
       # Continue processing - don't fail the booking
   ```

### Production

1. **Monitor health continuously**
2. **Set up alerts for failures**
3. **Clean up old jobs regularly**
4. **Use connection pooling for database**
5. **Test template changes in staging first**

---

## Support

**Documentation:**
- Quick Reference: `SCHEDULER_QUICK_REFERENCE.md`
- Complete Guide: `PHASE_1B_TASK3_SMART_FOLLOWUP_SCHEDULER_COMPLETE.md`

**Logs Location:**
- Application: `/var/log/myhibachi/app.log`
- Scheduler: Filter by `api.ai.scheduler`
- APScheduler: Filter by `apscheduler`

**Contact:**
- Development Team: dev@myhibachi.com
- On-Call: Follow incident response playbook

---

**Version History:**
- 1.0.0 (Nov 2, 2025): Initial production release
