# Phase 2.5: End-to-End Testing Guide

**Test Date**: November 12, 2025  
**Test Phone**: +1 (210) 388-4155  
**Tester**: Surya

---

## Prerequisites Checklist

### 1. Environment Configuration
```bash
# Verify all environment variables are set
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Check .env file
cat .env | grep -E "(RINGCENTRAL|DATABASE|DEEPGRAM|CELERY)"
```

**Required Variables**:
- [x] `RINGCENTRAL_CLIENT_ID` - RC OAuth credentials
- [x] `RINGCENTRAL_CLIENT_SECRET` - RC OAuth secret
- [x] `RINGCENTRAL_JWT_TOKEN` - RC JWT for API access
- [x] `RINGCENTRAL_SERVER_URL` - RC API endpoint
- [x] `RINGCENTRAL_WEBHOOK_SECRET` - Webhook validation
- [x] `DATABASE_URL` - PostgreSQL connection
- [x] `DEEPGRAM_API_KEY` - For fallback transcription
- [ ] `CELERY_BROKER_URL` - Redis/RabbitMQ for background jobs

### 2. Services Running
```bash
# Terminal 1: Backend API
cd apps\backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker
cd apps\backend
celery -A src.workers.celery_config worker --loglevel=info

# Terminal 3: ngrok (for RingCentral webhooks)
ngrok http 8000
```

### 3. Database Ready
```bash
# Run migrations
cd apps\backend
alembic upgrade head

# Verify tables exist
psql $DATABASE_URL -c "\dt communications.*"
psql $DATABASE_URL -c "\dt bookings.*"
```

### 4. Test Customer Setup
```sql
-- Create test customer with your phone number
INSERT INTO bookings.customers (
    phone, 
    email, 
    first_name, 
    last_name,
    created_at,
    updated_at
) VALUES (
    '+12103884155',
    'surya@myhibachi.com',
    'Surya',
    'Test',
    NOW(),
    NOW()
) ON CONFLICT (phone) DO UPDATE 
SET email = EXCLUDED.email,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name
RETURNING id;
```

### 5. Test Booking Setup
```sql
-- Create test booking for tomorrow at 7 PM
INSERT INTO bookings.bookings (
    customer_id,
    booking_datetime,
    party_size,
    status,
    contact_phone,
    contact_email,
    created_at,
    updated_at
) VALUES (
    (SELECT id FROM bookings.customers WHERE phone = '+12103884155'),
    NOW() + INTERVAL '1 day' + INTERVAL '19 hours',  -- Tomorrow 7 PM
    4,
    'confirmed',
    '+12103884155',
    'surya@myhibachi.com',
    NOW(),
    NOW()
) RETURNING id;
```

---

## Test Scenarios

### Scenario 1: Basic Call Recording ✅

**Objective**: Verify call is recorded and webhook received

**Steps**:
1. Call your RingCentral business number from +1 (210) 388-4155
2. Let it ring for 10 seconds
3. Hang up
4. Check webhook logs

**Expected Results**:
- Webhook `telephony.session` received
- CallRecording created with:
  - `from_phone`: "+12103884155"
  - `to_phone`: "{business_number}"
  - `state`: "ringing" → "disconnected"
  - `rc_session_id`: Set

**Verification**:
```sql
SELECT 
    id,
    from_phone,
    to_phone,
    state,
    call_started_at,
    call_ended_at
FROM communications.call_recordings
WHERE from_phone = '+12103884155'
ORDER BY created_at DESC
LIMIT 1;
```

**Log Check**:
```bash
# Backend logs
tail -f logs/app.log | grep "telephony.session"

# Celery logs
tail -f logs/celery.log | grep "recording"
```

---

### Scenario 2: AI Transcript Fetch ✅

**Objective**: Verify RingCentral AI transcript is fetched

**Steps**:
1. Make a recorded call (inbound to RC number)
2. During call, say clearly:
   ```
   "Hi, this is Surya. I'm calling about my hibachi reservation 
   for tomorrow at 7 PM for 4 people. I wanted to add vegetarian 
   options and confirm parking availability. Thank you!"
   ```
3. Wait ~30 seconds after call ends
4. Check if transcript is fetched

**Expected Results**:
- Celery task `fetch_recording_transcript` runs after 30s
- `rc_transcript` field populated with transcript text
- `rc_transcript_confidence` > 80%
- `rc_ai_insights` contains:
  - `sentiment`: "positive" or "neutral"
  - `topics`: ["reservation", "dietary", "parking"]
  - `intent`: "modification" or "inquiry"

**Verification**:
```sql
SELECT 
    id,
    LEFT(rc_transcript, 200) as transcript_excerpt,
    rc_transcript_confidence,
    rc_ai_insights->>'sentiment' as sentiment,
    rc_ai_insights->'topics' as topics,
    rc_transcript_fetched_at
FROM communications.call_recordings
WHERE from_phone = '+12103884155'
AND rc_transcript IS NOT NULL
ORDER BY created_at DESC
LIMIT 1;
```

**API Check**:
```bash
# Get recording via API
curl -X GET "http://localhost:8000/api/v1/recordings/{recording_id}" \
  -H "Authorization: Bearer {admin_token}"
```

---

### Scenario 3: Customer Linking ✅

**Objective**: Verify recording is linked to customer by phone

**Steps**:
1. Call should be from +1 (210) 388-4155 (your number)
2. Wait for transcript fetch to complete
3. Wait additional 5 seconds for linking task
4. Check `customer_id` field

**Expected Results**:
- Celery task `link_recording_entities` runs after transcript
- `customer_id` is set to your customer record ID
- Phone number normalized and matched

**Verification**:
```sql
-- Check if linked
SELECT 
    cr.id as recording_id,
    cr.from_phone,
    cr.customer_id,
    c.first_name,
    c.last_name,
    c.email
FROM communications.call_recordings cr
LEFT JOIN bookings.customers c ON cr.customer_id = c.id
WHERE cr.from_phone = '+12103884155'
ORDER BY cr.created_at DESC
LIMIT 1;
```

**Expected Output**:
```
recording_id | from_phone      | customer_id | first_name | last_name | email
-------------+-----------------+-------------+------------+-----------+---------------------
abc-123-...  | +12103884155    | 123         | Surya      | Test      | surya@myhibachi.com
```

**Logs**:
```bash
tail -f logs/celery.log | grep "link_recording_entities"
# Should see: "Entity linking complete for {id}: customer=linked, booking=linked"
```

---

### Scenario 4: Booking Correlation ✅

**Objective**: Verify recording is linked to booking by timing

**Steps**:
1. Make call within 24 hours of your test booking
2. Mention booking in transcript (helps scoring)
3. Wait for linking task
4. Check `booking_id` field

**Expected Results**:
- `booking_id` is set to your test booking ID
- Relevance score calculated:
  - Within 24 hours: ✓
  - Same customer: ✓
  - Booking status confirmed: ✓
  - Mentioned in call: +points

**Verification**:
```sql
-- Check if linked to booking
SELECT 
    cr.id as recording_id,
    cr.customer_id,
    cr.booking_id,
    b.booking_datetime,
    b.party_size,
    b.status,
    cr.call_started_at,
    EXTRACT(EPOCH FROM (b.booking_datetime - cr.call_started_at))/3600 as hours_difference
FROM communications.call_recordings cr
LEFT JOIN bookings.bookings b ON cr.booking_id = b.id
WHERE cr.from_phone = '+12103884155'
ORDER BY cr.created_at DESC
LIMIT 1;
```

**Expected Output**:
```
recording_id | customer_id | booking_id | booking_datetime    | hours_difference
-------------+-------------+------------+---------------------+------------------
abc-123-...  | 123         | 456        | 2024-11-13 19:00:00 | ~31 hours
```

---

### Scenario 5: Conversation History API ✅

**Objective**: Retrieve your conversation history via API

**Steps**:
1. Get your customer_id from database
2. Call conversation history API
3. Verify all your calls are returned

**API Calls**:
```bash
# Get customer ID first
CUSTOMER_ID=$(psql $DATABASE_URL -t -c "SELECT id FROM bookings.customers WHERE phone = '+12103884155'")

# Get conversation history
curl -X GET "http://localhost:8000/api/v1/conversations/customer/${CUSTOMER_ID}?limit=10" \
  -H "Authorization: Bearer {admin_token}" \
  | jq '.'

# Expected response:
{
  "customer_id": "123",
  "customer_name": "Surya Test",
  "customer_phone": "+12103884155",
  "total_conversations": 1,
  "conversations": [
    {
      "id": "rec-001",
      "call_started_at": "2024-11-12T15:30:00Z",
      "duration_seconds": 45,
      "transcript_excerpt": "Hi, this is Surya. I'm calling about...",
      "ai_insights": {
        "sentiment": "positive",
        "topics": ["reservation", "dietary"]
      }
    }
  ]
}
```

---

### Scenario 6: AI Context Generation ✅

**Objective**: Get AI-formatted context for your customer

**API Call**:
```bash
# Get AI context
curl -X GET "http://localhost:8000/api/v1/conversations/customer/${CUSTOMER_ID}/ai-context?max_conversations=5" \
  -H "Authorization: Bearer {admin_token}"

# Expected response:
{
  "customer_id": "123",
  "context": "Customer: Surya Test (+12103884155)\nRecent interactions (last 1 call):\n- 2024-11-12 15:30: Inquiry about reservation. Positive sentiment.\n\nKey topics discussed: reservation, dietary, parking\nActive booking: 2024-11-13 19:00, 4 guests, confirmed"
}
```

**Test in AI Agent**:
```python
# Use context in AI prompt
context = api.get_customer_ai_context(customer_id)

system_prompt = f"""
You are a helpful customer service AI for MyHibachi.

CUSTOMER CONTEXT:
{context}

Provide personalized service based on their history.
"""

# AI now knows:
# - You called about reservation
# - You want vegetarian options
# - You asked about parking
# - You have booking tomorrow at 7 PM for 4 people
```

---

### Scenario 7: Transcript Search ✅

**Objective**: Search for keywords in transcripts

**API Calls**:
```bash
# Search for "vegetarian"
curl -X GET "http://localhost:8000/api/v1/conversations/search?q=vegetarian&limit=10" \
  -H "Authorization: Bearer {admin_token}" \
  | jq '.'

# Search for "reservation" with positive sentiment
curl -X GET "http://localhost:8000/api/v1/conversations/search?q=reservation&sentiment=positive" \
  -H "Authorization: Bearer {admin_token}" \
  | jq '.'

# Search by customer
curl -X GET "http://localhost:8000/api/v1/conversations/search?q=parking&customer_id=${CUSTOMER_ID}" \
  -H "Authorization: Bearer {admin_token}" \
  | jq '.'
```

---

### Scenario 8: Booking Context Timeline ✅

**Objective**: See all calls related to a booking grouped by timeline

**API Call**:
```bash
# Get booking ID
BOOKING_ID=$(psql $DATABASE_URL -t -c "SELECT id FROM bookings.bookings WHERE contact_phone = '+12103884155' ORDER BY created_at DESC LIMIT 1")

# Get booking conversations
curl -X GET "http://localhost:8000/api/v1/conversations/booking/${BOOKING_ID}" \
  -H "Authorization: Bearer {admin_token}" \
  | jq '.'

# Expected response:
{
  "booking_id": "456",
  "booking_datetime": "2024-11-13T19:00:00Z",
  "total_conversations": 1,
  "conversations": {
    "pre_booking": [
      {
        "id": "rec-001",
        "call_started_at": "2024-11-12T15:30:00Z",
        "transcript_excerpt": "Hi, this is Surya..."
      }
    ],
    "day_of": [],
    "post_booking": []
  },
  "key_insights": {
    "common_topics": ["dietary", "parking"],
    "sentiment_summary": {
      "positive": {"count": 1, "percentage": 100.0}
    }
  }
}
```

---

## Performance Benchmarks

### Expected Timing
1. **Webhook Receipt**: < 1 second after call ends
2. **Transcript Fetch**: 30-60 seconds (RC AI processing time)
3. **Entity Linking**: < 5 seconds after transcript
4. **Total Time**: ~60 seconds from call end to fully linked

### Database Query Performance
```sql
-- Test query speeds with EXPLAIN ANALYZE

-- Customer lookup (should use index)
EXPLAIN ANALYZE
SELECT id FROM bookings.customers WHERE phone = '+12103884155';
-- Expected: < 5ms, uses idx_customers_phone_normalized

-- Booking correlation (should use composite index)
EXPLAIN ANALYZE
SELECT id FROM bookings.bookings
WHERE customer_id = 123
AND booking_datetime BETWEEN NOW() - INTERVAL '24 hours' AND NOW() + INTERVAL '24 hours'
ORDER BY ABS(EXTRACT(EPOCH FROM (booking_datetime - NOW())))
LIMIT 1;
-- Expected: < 10ms, uses idx_bookings_customer_datetime

-- Conversation history (should use composite index)
EXPLAIN ANALYZE
SELECT * FROM communications.call_recordings
WHERE customer_id = 123
ORDER BY call_started_at DESC
LIMIT 10;
-- Expected: < 20ms, uses idx_call_recordings_customer_datetime
```

---

## Test Script

Create `scripts/test_e2e_conversation.py`:

```python
"""
End-to-end test for conversation linking with real calls.
Run after making a test call to your phone number.
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from core.database import get_db_session
from models.call_recording import CallRecording
from models.customer import Customer
from models.booking import Booking

TEST_PHONE = "+12103884155"

async def test_full_pipeline():
    """Test complete conversation pipeline"""
    
    print("\n" + "=" * 80)
    print("End-to-End Conversation Pipeline Test")
    print("=" * 80 + "\n")
    
    async for db in get_db_session():
        try:
            # 1. Find test customer
            print("1️⃣  Finding test customer...")
            stmt = select(Customer).where(Customer.phone == TEST_PHONE)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
            
            if not customer:
                print(f"   ❌ Customer not found with phone {TEST_PHONE}")
                print("   Run setup SQL first!")
                return False
            
            print(f"   ✅ Customer found: {customer.first_name} {customer.last_name} (ID: {customer.id})")
            
            # 2. Find recent recordings
            print("\n2️⃣  Finding recent call recordings...")
            stmt = select(CallRecording).where(
                CallRecording.from_phone == TEST_PHONE
            ).order_by(CallRecording.created_at.desc()).limit(1)
            result = await db.execute(stmt)
            recording = result.scalar_one_or_none()
            
            if not recording:
                print(f"   ❌ No recordings found from {TEST_PHONE}")
                print("   Make a test call first!")
                return False
            
            print(f"   ✅ Recording found: {recording.id}")
            print(f"      Call time: {recording.call_started_at}")
            print(f"      Duration: {recording.duration_seconds}s")
            
            # 3. Check transcript
            print("\n3️⃣  Checking transcript...")
            if recording.rc_transcript:
                print(f"   ✅ Transcript fetched ({len(recording.rc_transcript)} chars)")
                print(f"      Confidence: {recording.rc_transcript_confidence}%")
                print(f"      Preview: {recording.rc_transcript[:100]}...")
                
                if recording.rc_ai_insights:
                    insights = recording.rc_ai_insights
                    print(f"      Sentiment: {insights.get('sentiment', 'N/A')}")
                    print(f"      Topics: {', '.join(insights.get('topics', []))}")
            else:
                print("   ⏳ Transcript not yet fetched (wait ~30s)")
                return False
            
            # 4. Check customer linking
            print("\n4️⃣  Checking customer linking...")
            if recording.customer_id:
                print(f"   ✅ Linked to customer: {recording.customer_id}")
                if recording.customer_id == customer.id:
                    print("   ✅ Correct customer matched!")
                else:
                    print("   ❌ Wrong customer linked!")
                    return False
            else:
                print("   ⏳ Customer not yet linked (wait a few seconds)")
                return False
            
            # 5. Check booking linking
            print("\n5️⃣  Checking booking linking...")
            if recording.booking_id:
                print(f"   ✅ Linked to booking: {recording.booking_id}")
                
                # Get booking details
                stmt = select(Booking).where(Booking.id == recording.booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                
                if booking:
                    print(f"      Booking date: {booking.booking_datetime}")
                    print(f"      Party size: {booking.party_size}")
                    print(f"      Status: {booking.status}")
                    
                    # Check timing
                    time_diff = abs((booking.booking_datetime - recording.call_started_at).total_seconds() / 3600)
                    print(f"      Time difference: {time_diff:.1f} hours")
                    
                    if time_diff > 24:
                        print("   ⚠️  Booking is more than 24 hours away from call")
            else:
                print("   ℹ️  No booking linked (might be outside 24h window or no matching booking)")
            
            # 6. Test conversation history API
            print("\n6️⃣  Testing conversation history...")
            from services.conversation_history_service import ConversationHistoryService
            
            service = ConversationHistoryService(db)
            history = await service.get_customer_history(customer.id, limit=10)
            
            print(f"   ✅ Retrieved {len(history['conversations'])} conversations")
            
            # 7. Test AI context generation
            print("\n7️⃣  Testing AI context generation...")
            context = await service.get_ai_context_for_customer(customer.id, max_conversations=5)
            
            print("   ✅ AI Context generated:")
            print("\n" + "-" * 80)
            print(context)
            print("-" * 80 + "\n")
            
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED!")
            print("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_full_pipeline())
    sys.exit(0 if result else 1)
```

**Run Test**:
```bash
python scripts/test_e2e_conversation.py
```

---

## Troubleshooting

### Issue: Transcript Not Fetching
**Symptoms**: `rc_transcript` is NULL after 60 seconds

**Checks**:
1. Celery worker running: `ps aux | grep celery`
2. RingCentral AI enabled on account
3. Recording was actually recorded (not just ringing)
4. Check logs: `tail -f logs/celery.log | grep fetch_recording_transcript`

**Solutions**:
- Restart Celery worker
- Check RC_JWT_TOKEN is valid
- Verify call was longer than 30 seconds

### Issue: Customer Not Linking
**Symptoms**: `customer_id` is NULL

**Checks**:
1. Phone number in database matches exactly: `+12103884155`
2. Linking task ran: Check celery logs
3. Phone normalization working

**Solutions**:
```sql
-- Check phone format
SELECT phone FROM bookings.customers WHERE phone LIKE '%210388%';

-- Update if needed
UPDATE bookings.customers 
SET phone = '+12103884155' 
WHERE phone LIKE '%2103884155%';
```

### Issue: Booking Not Linking
**Symptoms**: `booking_id` is NULL but customer linked

**Checks**:
1. Booking exists for customer
2. Booking datetime within ±24 hours of call
3. Booking status is active (not cancelled)

**Solutions**:
```sql
-- Check bookings
SELECT 
    id,
    booking_datetime,
    status,
    NOW() as current_time,
    EXTRACT(EPOCH FROM (booking_datetime - NOW()))/3600 as hours_until_booking
FROM bookings.bookings
WHERE customer_id = (SELECT id FROM bookings.customers WHERE phone = '+12103884155')
ORDER BY booking_datetime;
```

### Issue: API Returns 401 Unauthorized
**Symptoms**: API calls fail with authentication error

**Solutions**:
```bash
# Get admin token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@myhibachi.com", "password": "your_password"}'

# Use token
TOKEN="eyJ..."
curl -H "Authorization: Bearer $TOKEN" ...
```

---

## Success Criteria

- [x] Call recorded in database within 1 second
- [ ] Transcript fetched within 60 seconds
- [ ] Customer linked within 5 seconds of transcript
- [ ] Booking linked (if applicable) within 5 seconds
- [ ] Conversation history API works
- [ ] AI context generation works
- [ ] Search API works
- [ ] Performance < 500ms for API calls

---

## Next Steps After Testing

1. **Monitor production calls** - Watch real customer calls being processed
2. **Analyze linking accuracy** - Check % of successful customer/booking links
3. **Optimize scoring** - Adjust booking relevance scoring weights
4. **Add caching** - Redis cache for frequently accessed customers
5. **AI integration** - Connect context to voice AI agents
6. **Analytics dashboard** - Build admin view for conversation insights

---

**Ready to test!** Make a call to your RingCentral number from +1 (210) 388-4155 and follow the test scenarios above.
