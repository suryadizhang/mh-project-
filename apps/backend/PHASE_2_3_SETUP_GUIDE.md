# Phase 2.3: Call Recording Storage - Setup & Testing Guide

**Status**: ✅ Code Complete | ⚠️ Database Migration Pending  
**Test Score**: 6/7 passing (85.7%)

---

## Quick Setup

### 1. Database Migration

The Phase 2.3 migration requires the base `call_recordings` table to exist first. Run all migrations:

```bash
cd apps/backend
alembic upgrade head
```

**What happens:**
- Creates `communications` schema (if not exists)
- Creates `call_recordings` base table (migration `010_escalation_call_recording.py`)
- Adds transcript fields (migration `6e2245429ea8_add_ringcentral_ai_transcript_fields.py`)

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade 010 -> 6e2245429ea8
📝 Adding RingCentral AI transcript fields to call_recordings table...
✅ RingCentral AI transcript fields added successfully
```

**If you see this (OK):**
```
⚠️  call_recordings table not found in communications schema
    This migration will be applied after 010_escalation_call_recording.py runs
    Run 'alembic upgrade head' again to complete this migration
```
Just run `alembic upgrade head` again after the base migration completes.

---

### 2. Environment Variables

Ensure these variables are set in `.env`:

```env
# RingCentral API
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_client_secret
RINGCENTRAL_JWT_TOKEN=your_jwt_token
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
```

---

### 3. Celery Worker

Start Celery to process transcript fetch tasks:

```bash
cd apps/backend
celery -A workers.celery_config worker --loglevel=info
```

**Verify it loads the new task:**
```
[tasks]
  . workers.recording_tasks.fetch_recording_transcript
  . workers.recording_tasks.fetch_call_recording
```

---

### 4. Run Tests

Validate implementation:

```bash
cd apps/backend
python scripts/test_recording_storage.py
```

**Expected Results:**
```
✅ Service Configuration: RingCentral credentials configured
✅ Database Model: All transcript fields present
✅ Service Methods: get_call_transcript, get_recording_stream_url
✅ Celery Task: fetch_recording_transcript available
✅ API Endpoints: All 3 endpoints registered
✅ Database Migration: Migration file exists
✅ Database Table Structure: All transcript columns exist

Total Tests: 7
✅ Passed: 7
❌ Failed: 0
Success Rate: 100.0%
```

---

## Testing with Real Calls

### Manual Test Flow

1. **Make a test call** through RingCentral
2. **Wait for webhook** - `recording.complete` triggers after call ends
3. **Check database** - Transcript should appear within 30-60 seconds
4. **Verify API** - Access recording via endpoints

### Check Transcript Status

```sql
SELECT 
    rc_call_id,
    rc_transcript IS NOT NULL as has_transcript,
    rc_transcript_confidence,
    rc_transcript_fetched_at,
    rc_ai_insights->>'sentiment' as sentiment
FROM communications.call_recordings
ORDER BY recorded_at DESC
LIMIT 5;
```

### Test API Endpoints

```bash
# Get recording with transcript
curl http://localhost:8000/api/v1/recordings/{recording_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Stream audio
curl http://localhost:8000/api/v1/recordings/{recording_id}/stream \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search recordings
curl "http://localhost:8000/api/v1/recordings/?search_text=reservation&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Issue: Migration skips transcript fields

**Symptom:**
```
⚠️  call_recordings table not found in communications schema
```

**Solution:**
1. Check if base migrations ran:
   ```bash
   alembic current
   ```
2. Run all migrations:
   ```bash
   alembic upgrade head
   ```
3. Verify table exists:
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_schema = 'communications' 
   AND table_name = 'call_recordings';
   ```

---

### Issue: Test fails - "Database Table Structure"

**Symptom:**
```
❌ Database Table Structure: call_recordings table does not exist
```

**Solution:**
Run the database migration:
```bash
cd apps/backend
alembic upgrade head
```

Then re-run tests:
```bash
python scripts/test_recording_storage.py
```

---

### Issue: Transcript not fetching

**Symptom:**
Call recorded but `rc_transcript` remains NULL after 5 minutes.

**Debug Steps:**

1. **Check Celery is running:**
   ```bash
   celery -A workers.celery_config inspect active
   ```

2. **Check Celery logs:**
   Look for:
   ```
   [INFO] Fetching transcript for call call-session-12345
   ```

3. **Manually trigger task:**
   ```python
   from workers.recording_tasks import fetch_recording_transcript
   fetch_recording_transcript.apply_async(
       args=['recording-uuid', 'call-session-id']
   )
   ```

4. **Check RingCentral API directly:**
   ```bash
   curl https://platform.ringcentral.com/restapi/v1.0/account/~/call-log/{call-id}/transcript \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

---

### Issue: GIN index creation fails

**Symptom:**
```
⚠️  Could not create GIN index (pg_trgm may not be available)
```

**Solution:**
Enable pg_trgm extension:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Then re-run migration:
```bash
alembic downgrade -1
alembic upgrade head
```

---

## Performance Optimization

### Index Status

Check if indexes were created:
```sql
SELECT 
    schemaname, 
    tablename, 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'call_recordings'
AND schemaname = 'communications';
```

### Transcript Search Performance

Test full-text search speed:
```sql
EXPLAIN ANALYZE
SELECT * FROM communications.call_recordings
WHERE rc_transcript ILIKE '%reservation%'
LIMIT 10;
```

Should use GIN index:
```
Bitmap Index Scan on idx_call_recordings_transcript_search
```

---

## Production Checklist

Before deploying Phase 2.3 to production:

- [ ] ✅ All migrations applied (`alembic current` matches latest)
- [ ] ✅ Test suite passes 100% (`python scripts/test_recording_storage.py`)
- [ ] ✅ Celery worker running with transcript task loaded
- [ ] ✅ RingCentral credentials configured (production values)
- [ ] ✅ Database has `pg_trgm` extension enabled
- [ ] ✅ Test call made and transcript fetched successfully
- [ ] ✅ API endpoints tested and accessible
- [ ] ✅ Monitoring alerts configured for transcript fetch failures
- [ ] ✅ Backup/restore procedures tested with JSONB data

---

## Next Steps - Phase 2.4

Once Phase 2.3 is fully tested and deployed:

**Phase 2.4: Transcript Database Sync**
- Link transcripts to Customer records (phone number matching)
- Link transcripts to Booking records (date/time correlation)
- Create conversation history view
- Enable AI to reference past call context
- Full-text search across all customer interactions

**Estimated Time**: 2 hours

---

## Cost Analysis

**RingCentral Native Transcription:**
- Recording storage: Included with RC account
- AI transcription: Included with RC AI add-on ($15-30/user/month)
- Per-call cost: $0.00

**Alternative (Deepgram):**
- Recording download: Bandwidth costs
- Deepgram transcription: $0.0125/min = $0.75/hour
- Storage: VPS or S3 costs

**Monthly Savings** (10 calls/day, 10 min avg):
- RingCentral: $0/month
- Deepgram: $225/month
- **Savings: $225/month** ✅

---

## Support & Documentation

- **Main Documentation**: `/PHASE_2_3_COMPLETE.md`
- **Strategy Document**: `/docs/PHASE_2_3_RINGCENTRAL_NATIVE_RECORDING.md`
- **RingCentral AI API**: https://developers.ringcentral.com/api-reference/Call-Log/readUserCallLog
- **Migration File**: `db/migrations/alembic/versions/6e2245429ea8_*.py`
- **Test Script**: `scripts/test_recording_storage.py`

---

**Last Updated**: November 12, 2025  
**Version**: 1.0  
**Status**: Ready for Production Testing
