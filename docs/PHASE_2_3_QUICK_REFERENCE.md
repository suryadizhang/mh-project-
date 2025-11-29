# Phase 2.3 Quick Reference - Call Recording Storage

## 🎯 Quick Start

### Apply Database Migration
```bash
cd apps/backend
alembic upgrade head
```

### Test Implementation
```bash
python scripts/test_recording_storage.py
```

### Access Recordings API
```bash
# Get specific recording with transcript
GET /api/v1/recordings/{recording_id}

# Stream recording audio
GET /api/v1/recordings/{recording_id}/stream

# Search recordings
GET /api/v1/recordings/?phone_number=+1234567890&search_text=reservation
```

---

## 📋 Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Database Model** | `models/call_recording.py` | Stores transcripts & AI insights |
| **RC Service** | `services/ringcentral_service.py` | Fetches transcripts from RC AI |
| **Background Task** | `workers/recording_tasks.py` | Automated transcript fetching |
| **Webhook Handler** | `services/ringcentral_voice_service.py` | Triggers transcript fetch |
| **API Router** | `routers/v1/recordings.py` | REST API endpoints |
| **Migration** | `db/migrations/alembic/versions/6e22*.py` | Database schema changes |

---

## 🔄 Processing Flow

```
Call Ends → recording.complete webhook → Save recording URI
   ↓
Queue fetch_recording_transcript task (30s delay)
   ↓
Celery worker calls RingCentral AI API
   ↓
Save transcript + insights to database
   ↓
Available via /api/v1/recordings API
```

---

## 💾 Database Fields

```python
# CallRecording model new fields
rc_transcript: Text              # Full transcript text
rc_transcript_confidence: int    # Confidence 0-100
rc_transcript_fetched_at: datetime  # When fetched
rc_ai_insights: JSONB            # AI analysis results
```

### AI Insights Structure
```json
{
  "sentiment": {"overall": "positive", "score": 0.8},
  "topics": ["reservation", "hibachi"],
  "action_items": ["Follow up with customer"],
  "intent": "booking_inquiry",
  "speakers": [...]
}
```

---

## 🔧 Service Methods

### Fetch Transcript
```python
from services.ringcentral_service import get_ringcentral_service

rc_service = get_ringcentral_service()
transcript_data = rc_service.get_call_transcript(call_session_id)

# Returns:
# {
#   "full_text": "...",
#   "confidence": 95,
#   "segments": [...],
#   "insights": {...}
# }
```

### Get Streaming URL
```python
stream_url = rc_service.get_recording_stream_url(recording_id)
# Returns time-limited URL with auth token
```

---

## ⚙️ Celery Task

### Manual Task Trigger
```python
from workers.recording_tasks import fetch_recording_transcript

# Queue task
fetch_recording_transcript.delay(recording_id, call_session_id)

# Or with delay
fetch_recording_transcript.apply_async(
    args=[recording_id, call_session_id],
    countdown=30  # Wait 30 seconds
)
```

### Task Monitoring
```bash
# Check Celery worker logs
celery -A workers.celery_config worker --loglevel=info

# Or check in Flower dashboard
flower -A workers.celery_config --port=5555
```

---

## 🌐 API Endpoints

### Get Recording Details
```http
GET /api/v1/recordings/{recording_id}
Authorization: Bearer {admin_token}

Response:
{
  "id": "uuid",
  "rc_call_id": "...",
  "status": "available",
  "duration_seconds": 120,
  "transcript": {
    "text": "...",
    "confidence": 95,
    "fetched_at": "2025-11-12T10:00:00Z"
  },
  "ai_insights": {
    "sentiment": {...},
    "topics": [...],
    "action_items": [...]
  }
}
```

### Stream Audio
```http
GET /api/v1/recordings/{recording_id}/stream
Authorization: Bearer {admin_token}

Response: 307 Redirect to RingCentral CDN
```

### Search Recordings
```http
GET /api/v1/recordings/?phone_number=+1234567890
GET /api/v1/recordings/?start_date=2025-11-01&end_date=2025-11-30
GET /api/v1/recordings/?search_text=reservation
GET /api/v1/recordings/?has_transcript=true
GET /api/v1/recordings/?status=available&limit=50&offset=0

Response:
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "recordings": [
    {
      "id": "...",
      "rc_call_id": "...",
      "has_transcript": true,
      "transcript_preview": "...",
      "confidence": 95,
      "ai_insights_summary": {...}
    }
  ]
}
```

---

## 🧪 Testing

### Run Test Suite
```bash
cd apps/backend
python scripts/test_recording_storage.py
```

### Expected Results
- ✅ Database Model: All fields present
- ✅ Service Methods: get_call_transcript, get_recording_stream_url
- ✅ Celery Task: fetch_recording_transcript available
- ✅ API Endpoints: 3 endpoints registered
- ✅ Migration: File exists

### Test with Real Call
1. Make test call through RingCentral
2. Wait for `recording.complete` webhook
3. Check database:
   ```sql
   SELECT rc_call_id, rc_transcript, rc_transcript_confidence, rc_ai_insights
   FROM call_recordings
   WHERE rc_call_id = 'your-call-id';
   ```

---

## 🐛 Troubleshooting

### Transcript Not Fetching
**Problem**: Recording saved but no transcript

**Solutions**:
1. Check Celery worker is running:
   ```bash
   celery -A workers.celery_config inspect active
   ```
2. Check RingCentral AI is enabled in account settings
3. Check logs for task errors:
   ```bash
   grep "fetch_recording_transcript" logs/celery.log
   ```
4. Manually retry:
   ```python
   fetch_recording_transcript.delay(recording_id, call_session_id)
   ```

### Empty Transcript
**Problem**: `rc_transcript` is empty or null

**Possible Causes**:
- RC AI not available yet (retry after 1-5 min)
- Call too short (<10 seconds)
- RC AI not enabled in account
- Network error calling RC API

**Check Logs**:
```python
# Look for error in rc_ai_insights
SELECT rc_ai_insights->>'error' FROM call_recordings WHERE id = 'xxx';
```

### API Returns 404
**Problem**: Recording not found

**Solutions**:
1. Verify recording exists:
   ```sql
   SELECT * FROM call_recordings WHERE id = 'xxx';
   ```
2. Check migration applied:
   ```bash
   alembic current
   alembic history
   ```
3. Verify router registered in `main.py`

---

## 📊 Monitoring

### Key Metrics to Track
```sql
-- Transcript fetch success rate
SELECT 
  COUNT(*) FILTER (WHERE rc_transcript IS NOT NULL) * 100.0 / COUNT(*) as success_rate
FROM call_recordings
WHERE created_at > NOW() - INTERVAL '7 days';

-- Average confidence score
SELECT AVG(rc_transcript_confidence) as avg_confidence
FROM call_recordings
WHERE rc_transcript IS NOT NULL;

-- Transcripts by sentiment
SELECT 
  rc_ai_insights->>'sentiment'->>'overall' as sentiment,
  COUNT(*) 
FROM call_recordings
WHERE rc_ai_insights IS NOT NULL
GROUP BY sentiment;

-- Most common topics
SELECT 
  topic,
  COUNT(*) as frequency
FROM call_recordings,
  jsonb_array_elements_text(rc_ai_insights->'topics') as topic
GROUP BY topic
ORDER BY frequency DESC
LIMIT 10;
```

---

## 💰 Cost Savings

| Approach | Cost per Hour | Cost per Month (10 calls/day) |
|----------|---------------|-------------------------------|
| **RingCentral Native** | $0 | $0 |
| Deepgram Custom | $0.75 | $225 |

**Monthly Savings**: $225

---

## 📚 Related Phases

- **Phase 2.1**: Deepgram STT/TTS Integration
- **Phase 2.2**: RingCentral Webhook Pipeline
- **Phase 2.4**: Transcript Database Sync (Next)
- **Phase 2.5**: End-to-End Flow Testing

---

## 🚀 Production Checklist

Before deploying to production:

- [ ] Apply database migration (`alembic upgrade head`)
- [ ] Verify Celery workers running (`celery inspect ping`)
- [ ] Test with real RingCentral call
- [ ] Verify transcript appears in database
- [ ] Test API endpoints with Postman
- [ ] Set up monitoring alerts for failed tasks
- [ ] Document RC AI pricing for client
- [ ] Train support team on recordings UI
- [ ] Set up retention policy (auto-delete after X days)
- [ ] Configure backup for transcripts

---

## 🔗 External Resources

- [RingCentral AI Insights API](https://developers.ringcentral.com/api-reference/Call-Log/readUserCallLog)
- [RingCentral Call Recording Guide](https://developers.ringcentral.com/guide/voice/recording)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

---

**Last Updated**: November 12, 2025  
**Implementation Time**: 1.5 hours  
**Status**: ✅ Complete (awaiting migration + real call test)
