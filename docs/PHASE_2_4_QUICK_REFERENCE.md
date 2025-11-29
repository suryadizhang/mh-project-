# Phase 2.4: Quick Reference Guide

## Test Suite
```bash
# Run all tests
python scripts/test_transcript_sync.py

# Expected: 10/10 tests passing
```

## API Endpoints

### Get Customer Conversations
```bash
GET /api/v1/conversations/customer/{customer_id}?limit=20&offset=0
Authorization: Bearer <admin_token>
```

### Get Booking Conversations
```bash
GET /api/v1/conversations/booking/{booking_id}
Authorization: Bearer <admin_token>
```

### Get AI Context
```bash
GET /api/v1/conversations/customer/{customer_id}/ai-context?max_conversations=5
Authorization: Bearer <admin_token>
```

### Search Transcripts
```bash
GET /api/v1/conversations/search?q=vegetarian&sentiment=positive&limit=50
Authorization: Bearer <admin_token>
```

## Service Usage

### Link Recording Manually
```python
from services.recording_linking_service import RecordingLinkingService

service = RecordingLinkingService(db)
result = await service.link_recording(recording_id)

# Returns:
# {
#   "customer_linked": True,
#   "customer_id": "abc-123",
#   "booking_linked": True,
#   "booking_id": "xyz-789",
#   "error": None
# }
```

### Get Customer History
```python
from services.conversation_history_service import ConversationHistoryService

service = ConversationHistoryService(db)
history = await service.get_customer_history(
    customer_id=customer_id,
    limit=20,
    offset=0
)
```

### Get AI Context
```python
service = ConversationHistoryService(db)
context = await service.get_ai_context_for_customer(
    customer_id=customer_id,
    max_conversations=5
)

# Use in AI prompt:
system_prompt = f"""
You are a helpful customer service AI.

CUSTOMER CONTEXT:
{context}
"""
```

## Celery Tasks

### Trigger Linking Manually
```python
from workers.recording_tasks import link_recording_entities

# Queue task
link_recording_entities.apply_async(
    args=[str(recording_id)],
    countdown=0  # Run immediately
)
```

### Check Task Status
```bash
# View Celery worker logs
tail -f /var/log/celery/worker.log | grep link_recording_entities
```

## Database Queries

### Find Unlinked Recordings
```sql
SELECT id, from_phone, to_phone, call_started_at
FROM communications.call_recordings
WHERE customer_id IS NULL
AND rc_transcript IS NOT NULL
LIMIT 100;
```

### Check Linking Statistics
```sql
SELECT 
    COUNT(*) as total_recordings,
    COUNT(customer_id) as customer_linked,
    COUNT(booking_id) as booking_linked,
    ROUND(COUNT(customer_id)::numeric / COUNT(*)::numeric * 100, 1) as customer_pct,
    ROUND(COUNT(booking_id)::numeric / COUNT(*)::numeric * 100, 1) as booking_pct
FROM communications.call_recordings
WHERE rc_transcript IS NOT NULL;
```

### Find Conversations for Customer
```sql
SELECT 
    id,
    call_started_at,
    duration_seconds,
    LEFT(rc_transcript, 100) as excerpt,
    rc_transcript_confidence,
    rc_ai_insights->>'sentiment' as sentiment
FROM communications.call_recordings
WHERE customer_id = 'abc-123-...'
ORDER BY call_started_at DESC
LIMIT 10;
```

## Troubleshooting

### Recordings Not Linking
1. Check phone number format in database
2. Verify customer.phone exists
3. Check Celery worker is running
4. Review logs: `tail -f /var/log/backend/app.log | grep link_recording`

### Low Booking Correlation Rate
1. Check booking date range (±24 hours)
2. Verify booking.booking_datetime is set correctly
3. Review relevance scoring thresholds
4. Check if contact_phone matches recording phones

### API Errors
1. Verify admin authentication token
2. Check database connection
3. Confirm migrations have run
4. Review API logs for specific errors

## Performance Monitoring

### Key Metrics
- **Customer Link Rate**: Should be > 95%
- **Booking Link Rate**: Should be > 80%
- **API Response Time**: Should be < 500ms
- **Linking Time**: Should be < 5 seconds

### Monitor with SQL
```sql
-- Average linking time (if tracked)
SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_seconds
FROM communications.call_recordings
WHERE customer_id IS NOT NULL;

-- Recent linking activity
SELECT 
    DATE(created_at) as date,
    COUNT(*) as recordings,
    COUNT(customer_id) as linked_customers,
    COUNT(booking_id) as linked_bookings
FROM communications.call_recordings
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Common Patterns

### Backfill Existing Recordings
```python
from services.recording_linking_service import RecordingLinkingService

service = RecordingLinkingService(db)

# Get all unlinked recording IDs
stmt = select(CallRecording.id).where(
    and_(
        CallRecording.customer_id.is_(None),
        CallRecording.rc_transcript.isnot(None)
    )
)
result = await db.execute(stmt)
recording_ids = [row[0] for row in result]

# Bulk link
results = await service.bulk_link_recordings(recording_ids)
print(f"Linked {results['customers_linked']} customers, {results['bookings_linked']} bookings")
```

### Custom Relevance Scoring
```python
# Modify _calculate_booking_relevance_score() in RecordingLinkingService
# Adjust weights based on your business needs:
# - Same day: +5 points
# - Within 3 hours: +5 points
# - Future booking: +2 points
# - Active status: +3 points
# - Contact phone match: +10 points
```

## Environment Variables

Required:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_secret
```

Optional (for caching):
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Related Documentation
- Phase 2.3: Call Recording Storage
- Phase 2.4 Strategy: PHASE_2_4_TRANSCRIPT_SYNC_STRATEGY.md
- Phase 2.4 Complete: PHASE_2_4_COMPLETE.md
- API Documentation: /docs (Swagger UI)

---

**Quick Start**: Run tests → Verify all passing → Deploy → Monitor linking rates → Integrate with AI
