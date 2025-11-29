# Phase 2.4: Transcript Database Sync - Implementation Strategy

**Goal**: Automatically link call recording transcripts to Customer and Booking records  
**Estimated Time**: 2 hours  
**Priority**: High (enables AI context-aware conversations)

---

## Overview

Phase 2.4 connects call recordings with business entities, creating a complete conversation history that AI agents can reference for personalized customer service.

### Key Features
1. **Customer Linking** - Match recordings to customers via phone number
2. **Booking Linking** - Associate recordings with bookings via timing correlation
3. **Conversation History** - Unified view of all customer interactions
4. **AI Context Access** - Enable AI to reference past conversations

---

## Current State

✅ **Already Implemented**:
- `CallRecording.customer_id` - Foreign key to customers table
- `CallRecording.booking_id` - Foreign key to bookings table
- `CallRecording.from_phone` and `to_phone` - Phone numbers indexed
- `CallRecording.call_started_at` - Timestamp indexed
- `CallRecording.rc_transcript` - Full transcript text
- `CallRecording.rc_ai_insights` - JSONB with sentiment, topics, etc.

🔧 **Needs Implementation**:
- Service to match phone numbers → customers
- Service to match timestamps + customers → bookings
- Celery task to auto-link after transcript fetches
- API endpoints for conversation history
- Query optimization for AI context retrieval

---

## Architecture

```
┌─────────────────────────────────────┐
│  Recording Transcript Fetched       │
│  (Celery: fetch_recording_transcript)│
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  NEW: Link Recording to Entities    │
│  (Celery: link_recording_entities)  │
└─────────────┬───────────────────────┘
              │
              ├──────────────────────────┐
              ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│  Match Phone Number  │   │  Match Booking       │
│  → Customer ID       │   │  (Date + Customer)   │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └──────────┬───────────────┘
                      ▼
        ┌──────────────────────────┐
        │  Update CallRecording    │
        │  - customer_id           │
        │  - booking_id            │
        └──────────────────────────┘
```

---

## Implementation Tasks

### Task 1: Create RecordingLinkingService (30 min)

**File**: `services/recording_linking_service.py`

```python
class RecordingLinkingService:
    def link_customer_by_phone(recording: CallRecording) -> Optional[UUID]:
        """Match recording to customer by phone number"""
        # Try from_phone (for inbound calls)
        # Try to_phone (for outbound calls)
        # Normalize phone format (+1XXXXXXXXXX)
        
    def link_booking_by_context(recording: CallRecording) -> Optional[UUID]:
        """Match recording to booking by timing + customer"""
        # Find bookings for customer within ±24 hours
        # Prefer bookings with matching date
        # Return most likely booking_id
        
    def link_recording(recording_id: UUID) -> dict:
        """Complete linking process for a recording"""
        # Get recording
        # Link customer
        # Link booking (if customer found)
        # Update database
        # Return results
```

**Matching Logic**:

**Customer Matching**:
1. Normalize phone to E.164 format: `+1XXXXXXXXXX`
2. Try `from_phone` first (inbound = customer calling in)
3. Try `to_phone` next (outbound = we called customer)
4. Query: `SELECT id FROM customers WHERE phone = ?`
5. Update `recording.customer_id`

**Booking Matching** (only if customer found):
1. Get customer's bookings within ±24 hours of call
2. Prefer bookings with status: `pending`, `confirmed`, `in_progress`
3. Calculate relevance score:
   - Exact date match: +10 points
   - Within 3 hours: +5 points
   - Same day: +3 points
   - Customer mentioned in transcript: +5 points
4. Select highest scoring booking
5. Update `recording.booking_id`

---

### Task 2: Create Celery Linking Task (20 min)

**File**: `workers/recording_tasks.py`

Add new task after `fetch_recording_transcript`:

```python
@celery_app.task(bind=True, max_retries=2)
def link_recording_entities(self, recording_id: str):
    """
    Link call recording to customer and booking entities.
    
    Runs automatically after transcript fetch completes.
    Matches by phone number (customer) and timing (booking).
    """
    # Get recording
    # Call RecordingLinkingService.link_recording()
    # Log results
    # Return summary
```

**Trigger**: Chain with `fetch_recording_transcript`:
```python
# In ringcentral_voice_service.py handle_recording_ready():
from celery import chain
chain(
    fetch_recording_transcript.si(recording_id, call_session_id),
    link_recording_entities.si(recording_id)
).apply_async(countdown=30)
```

---

### Task 3: Add Conversation History API (30 min)

**File**: `routers/v1/conversations.py` (NEW)

Endpoints:

**`GET /api/v1/conversations/customer/{customer_id}`**
- Get all call recordings for a customer
- Include transcript excerpts
- Sort by date (newest first)
- Pagination support

**`GET /api/v1/conversations/booking/{booking_id}`**
- Get recordings linked to a booking
- Show pre-booking, during, post-booking calls
- Include AI insights

**`GET /api/v1/conversations/search`**
- Search across all transcripts
- Filter by customer, booking, date range, sentiment
- Full-text search on transcript content

---

### Task 4: Create ConversationHistoryService (30 min)

**File**: `services/conversation_history_service.py`

```python
class ConversationHistoryService:
    def get_customer_history(customer_id: UUID, limit: int = 20) -> list[dict]:
        """Get conversation history for a customer"""
        # Query call_recordings where customer_id matches
        # Include transcript excerpts (first 200 chars)
        # Include AI insights summary
        # Sort by call_started_at DESC
        
    def get_booking_context(booking_id: UUID) -> dict:
        """Get all conversations related to a booking"""
        # Find recordings with booking_id
        # Group by call timeline (before/during/after event)
        # Extract key information (concerns, requests, feedback)
        
    def get_ai_context_for_customer(customer_id: UUID) -> str:
        """Format recent conversation history for AI prompts"""
        # Get last 5 conversations
        # Extract key points from AI insights
        # Format as concise context string for AI
        # Example: "Previous calls: [1] 2024-11-10 - Inquiry about catering for 50..."
```

---

### Task 5: Update Webhook Handler (10 min)

**File**: `services/ringcentral_voice_service.py`

Modify `handle_recording_ready()` to chain linking task:

```python
from celery import chain
from workers.recording_tasks import fetch_recording_transcript, link_recording_entities

# Queue transcript fetch + entity linking
chain(
    fetch_recording_transcript.si(str(call_recording.id), call_id),
    link_recording_entities.si(str(call_recording.id))
).apply_async(countdown=30)
```

---

### Task 6: Create Test Suite (20 min)

**File**: `scripts/test_transcript_sync.py`

Tests:
1. Phone number normalization
2. Customer matching (inbound/outbound)
3. Booking matching by date
4. End-to-end linking workflow
5. Conversation history API
6. AI context generation

---

### Task 7: Add Database Indexes (10 min)

**File**: New migration `add_recording_linking_indexes.py`

```python
# Optimize customer phone lookups
CREATE INDEX idx_customers_phone_normalized 
ON bookings.customers (REGEXP_REPLACE(phone, '[^0-9]', '', 'g'));

# Optimize booking date range queries
CREATE INDEX idx_bookings_customer_date 
ON bookings.bookings (customer_id, event_date);
```

---

## Data Flow Example

### Scenario: Customer calls about their upcoming event

**1. Call Happens**
- Customer `+1-555-0123` calls business
- RingCentral records call
- Call ends at `2024-11-15 10:30 AM`

**2. Webhook Triggered**
- `recording.complete` webhook received
- Create `CallRecording` record:
  ```python
  from_phone = "+15550123"
  to_phone = "+19167408768"  # Business number
  call_started_at = "2024-11-15 10:27:00"
  ```

**3. Transcript Fetched** (30s delay)
- Celery task `fetch_recording_transcript` runs
- RC AI provides transcript:
  ```
  "Hi, this is John Smith. I'm calling about my hibachi party
  next Friday for 30 people. Can I add vegetarian options?"
  ```
- AI insights: `{sentiment: positive, topics: [catering, dietary], intent: modification}`

**4. Entity Linking** (runs after transcript)
- Celery task `link_recording_entities` runs
- **Customer Match**:
  ```sql
  SELECT id FROM customers 
  WHERE phone = '+15550123' 
  -- Found: customer_id = 'abc-123-...'
  ```
- **Booking Match**:
  ```sql
  SELECT id FROM bookings 
  WHERE customer_id = 'abc-123-...'
  AND event_date BETWEEN '2024-11-14' AND '2024-11-16'
  AND status IN ('confirmed', 'pending')
  -- Found: booking_id = 'xyz-789-...' (event on 2024-11-15)
  ```
- **Update Recording**:
  ```python
  recording.customer_id = 'abc-123-...'
  recording.booking_id = 'xyz-789-...'
  ```

**5. Available for AI**
- Next time John calls, AI retrieves context:
  ```python
  context = get_ai_context_for_customer('abc-123-...')
  # "Previous call 2024-11-15: Asked about vegetarian options for 
  # Nov 15 event (30 guests). Sentiment: positive."
  ```
- AI can provide informed responses:
  ```
  "Hi John! I see you called earlier about vegetarian options 
  for your November 15th party. Let me help you with that..."
  ```

---

## Phone Number Normalization

**Challenge**: Phone numbers come in many formats
- `555-0123` (local)
- `(555) 012-3456` (formatted)
- `+1-555-012-3456` (international)
- `15550123456` (raw)

**Solution**: Normalize to E.164
```python
import phonenumbers

def normalize_phone(phone: str, default_region: str = "US") -> str:
    """Normalize phone to E.164 format: +1XXXXXXXXXX"""
    try:
        parsed = phonenumbers.parse(phone, default_region)
        return phonenumbers.format_number(
            parsed, 
            phonenumbers.PhoneNumberFormat.E164
        )
    except:
        # Fallback: strip non-digits, add +1
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) == 10:
            return f"+1{digits}"
        return f"+{digits}"
```

---

## API Response Examples

### Customer Conversation History

**Request**: `GET /api/v1/conversations/customer/abc-123`

**Response**:
```json
{
  "customer_id": "abc-123-...",
  "customer_name": "John Smith",
  "total_calls": 5,
  "conversations": [
    {
      "id": "rec-001",
      "call_started_at": "2024-11-15T10:27:00Z",
      "duration_seconds": 180,
      "call_type": "inbound",
      "booking_id": "xyz-789",
      "transcript_excerpt": "Hi, this is John Smith. I'm calling about my hibachi party...",
      "ai_insights": {
        "sentiment": "positive",
        "topics": ["catering", "dietary"],
        "intent": "modification",
        "action_items": ["Add vegetarian options"]
      },
      "confidence": 95
    }
  ]
}
```

### AI Context String

**Request**: `get_ai_context_for_customer('abc-123')`

**Output**:
```
Customer: John Smith
Recent interactions:
- 2024-11-15 10:27: Called about vegetarian options for Nov 15 event (30 guests). Positive sentiment.
- 2024-11-10 14:20: Booking confirmation for hibachi party. Asked about parking. Positive sentiment.
- 2024-11-08 09:15: Initial inquiry about catering prices. Interested in 30-person event. Neutral sentiment.

Key preferences: Vegetarian options important, concerned about parking
Booking status: Confirmed for 2024-11-15, 30 guests
```

---

## Success Criteria

- [ ] ✅ Customer linking accuracy > 95%
- [ ] ✅ Booking linking accuracy > 80%
- [ ] ✅ Linking completes within 5 seconds of transcript fetch
- [ ] ✅ Conversation history API responds < 500ms
- [ ] ✅ AI context retrieval < 200ms
- [ ] ✅ Test suite passes 100%
- [ ] ✅ Works with phone number variations
- [ ] ✅ Handles edge cases (no customer match, multiple bookings)

---

## Edge Cases

### No Customer Match
- **Scenario**: Phone number not in system
- **Action**: Leave `customer_id` NULL, log for manual review
- **Future**: Create lead from unmatched calls

### Multiple Booking Matches
- **Scenario**: Customer has 2 bookings on same day
- **Action**: Use AI insights to determine which booking
  - Analyze transcript for time mentions ("lunch party" vs "dinner")
  - Check booking details (guest count mentioned in call)
- **Fallback**: Link to nearest future booking

### Outbound Calls
- **Scenario**: Business calls customer (`from_phone` = business)
- **Action**: Match `to_phone` to customer
- **Context**: Often follow-up or confirmation calls

---

## Performance Optimization

### Database Queries
```sql
-- Customer lookup (indexed)
SELECT id FROM bookings.customers WHERE phone = '+15550123';

-- Booking lookup (composite index)
SELECT id FROM bookings.bookings 
WHERE customer_id = 'abc-123' 
AND event_date BETWEEN NOW() - INTERVAL '24 hours' AND NOW() + INTERVAL '24 hours'
AND status IN ('confirmed', 'pending')
ORDER BY ABS(EXTRACT(EPOCH FROM (event_date - '2024-11-15 10:27:00')))
LIMIT 1;
```

### Caching Strategy
- Cache customer phone → ID mappings (Redis, 24h TTL)
- Cache conversation history (5 min TTL)
- Invalidate on customer/booking updates

---

## Next Steps After Phase 2.4

**Phase 2.5: End-to-End Voice Flow**
- Full integration test with real calls
- Performance benchmarking
- Error recovery procedures
- Production monitoring dashboard
- AI agent integration with conversation context

**Estimated Time**: 2 hours

---

## Dependencies

**Python Packages**:
```bash
pip install phonenumbers
```

**Database**:
- PostgreSQL with pg_trgm extension (already required)
- Customer and Booking tables exist (already implemented)

**Services**:
- Celery worker running (already required)
- RingCentral webhooks active (already implemented)

---

**Status**: Ready to Implement  
**Complexity**: Medium  
**Impact**: High (enables AI conversation memory)
