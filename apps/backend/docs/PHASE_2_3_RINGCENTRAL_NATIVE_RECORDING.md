# Phase 2.3: Call Recording Storage - RingCentral Native Implementation

## Overview
Instead of downloading recordings and transcribing ourselves, we'll leverage RingCentral's built-in features:
- ✅ Automatic call recording (enabled in RC account)
- ✅ Recording storage (on RingCentral's servers)
- ✅ AI transcription (RingCentral AI feature)
- ✅ Webhook notifications when recordings are ready

## RingCentral Features We're Using

### 1. Automatic Call Recording
- Enabled in RingCentral account settings
- All inbound calls automatically recorded
- Recordings available via RC API

### 2. RingCentral AI Insights
- **Automatic Transcription**: Speech-to-text for all recordings
- **Conversation Intelligence**: Intent detection, sentiment analysis
- **Action Items**: Automatically extracted follow-up tasks
- **Topics & Keywords**: Key conversation themes
- **Speaker Separation**: Who said what

### 3. Recording Access Methods

#### Option A: Stream from RingCentral (Recommended)
**Benefits**:
- No storage costs
- Always up-to-date
- No sync issues
- Lower latency

**Implementation**:
```python
# Get recording URL from RC API
recording_url = rc_service.get_recording_url(recording_id)

# Stream to user
return redirect(recording_url)  # Or proxy through our API
```

#### Option B: Download and Store Locally
**When to use**:
- Need offline access
- Custom audio processing
- Integration with other systems

**Already implemented** in `workers/recording_tasks.py`:
- `fetch_call_recording()` - Downloads from RC
- Stores in `/var/www/vhosts/myhibachi/recordings/`
- Organized by date: `/YYYY/MM/filename.mp3`

### 4. RingCentral AI Transcript Access

**API Endpoint**:
```
GET /restapi/v1.0/account/~/call-log/{call-session-id}/transcript
```

**Returns**:
- Full transcript with timestamps
- Speaker labels
- Confidence scores
- Word-level timing

## Implementation Strategy

### Phase 2.3: Simplified Approach

**What We Need**:
1. ✅ Database schema (already exists - `CallRecording` model)
2. ✅ Webhook handler for `recording.complete` (already exists)
3. ✅ Link recordings to database (already implemented)
4. 🔜 Fetch RC AI transcript (new method)
5. 🔜 Store transcript metadata in database
6. 🔜 API endpoint to access recordings

### Database Schema Updates Needed

Add transcript fields to `CallRecording` model:
```python
# Transcript from RingCentral AI
rc_transcript = Column(Text, nullable=True)  # Full transcript
rc_transcript_confidence = Column(Float, nullable=True)
rc_transcript_fetched_at = Column(DateTime, nullable=True)

# RingCentral AI Insights
rc_ai_insights = Column(JSONB, default={}, nullable=False)
# Structure:
# {
#   "sentiment": {"overall": "positive", "score": 0.8},
#   "topics": ["booking", "dietary restrictions", "date change"],
#   "action_items": ["Follow up on Friday", "Send menu options"],
#   "intent": "booking_modification",
#   "speakers": [
#     {"id": "1", "label": "Customer", "talk_time_percent": 60},
#     {"id": "2", "label": "Agent", "talk_time_percent": 40}
#   ]
# }
```

### New Service Methods

#### 1. Fetch RingCentral AI Transcript
```python
async def fetch_rc_transcript(
    self,
    call_session_id: str,
    recording_id: UUID,
    db: AsyncSession
) -> dict[str, Any]:
    """
    Fetch transcript from RingCentral AI Insights API.
    
    This uses RC's built-in transcription - no Deepgram needed!
    """
    # Call RC API
    transcript_data = rc_service.get_call_transcript(call_session_id)
    
    # Update database
    call_recording = await db.get(CallRecording, recording_id)
    call_recording.rc_transcript = transcript_data["full_text"]
    call_recording.rc_transcript_confidence = transcript_data["confidence"]
    call_recording.rc_ai_insights = transcript_data["insights"]
    call_recording.rc_transcript_fetched_at = datetime.now(timezone.utc)
    
    await db.commit()
```

#### 2. Get Recording Playback URL
```python
async def get_recording_url(
    self,
    recording_id: UUID,
    db: AsyncSession,
    user_id: UUID
) -> str:
    """
    Get streaming URL for recording playback.
    
    Returns RC-hosted URL (no download needed).
    """
    call_recording = await db.get(CallRecording, recording_id)
    
    # Track access
    call_recording.record_access(user_id)
    await db.commit()
    
    # Return RC streaming URL
    return rc_service.get_recording_stream_url(
        call_recording.rc_recording_id
    )
```

### API Endpoints Needed

```python
# GET /api/v1/recordings/{recording_id}
# Get recording metadata + transcript

# GET /api/v1/recordings/{recording_id}/stream
# Stream recording audio (proxy from RC)

# GET /api/v1/recordings/{recording_id}/transcript
# Get full transcript with AI insights

# GET /api/v1/recordings/search
# Search recordings by date, phone, transcript content
```

## Cost Comparison

### Option A: RingCentral Native (Recommended)
- **Recording Storage**: Included with RC plan
- **Transcription**: Included with RC AI add-on ($15-30/user/month)
- **API Calls**: Free (within rate limits)
- **Our Costs**: $0 additional

### Option B: Download + Deepgram
- **Storage**: VPS disk space (~100MB/hour of calls)
- **Deepgram Transcription**: $0.0125/min = $0.75/hour
- **Bandwidth**: Transfer costs
- **Maintenance**: Worker jobs, storage management
- **Our Costs**: ~$1-2/hour of calls

**Recommendation**: Use RingCentral native features (Option A)

## Implementation Tasks

### Task 1: Update Database Model (10 min)
Add transcript fields to `CallRecording` model

### Task 2: RingCentral Service Methods (20 min)
- `get_call_transcript(call_session_id)` 
- `get_recording_stream_url(recording_id)`

### Task 3: Webhook Enhancement (15 min)
When `recording.complete` webhook received:
1. Save recording metadata ✅ (already done)
2. Queue transcript fetch (new Celery task)

### Task 4: Celery Task for Transcripts (20 min)
```python
@celery_app.task
def fetch_recording_transcript(recording_id: str):
    # Fetch from RC AI API
    # Save to database
```

### Task 5: API Endpoints (30 min)
- Recording list/detail endpoints
- Streaming proxy endpoint
- Transcript access endpoint

### Task 6: Testing (15 min)
Test webhook → transcript fetch → database storage

**Total Estimated Time**: 2 hours

## Success Criteria

✅ Phase 2.3 Complete When:
1. Webhook receives `recording.complete` events
2. Recording metadata saved to database
3. RC AI transcript automatically fetched
4. AI insights stored (sentiment, topics, action items)
5. API endpoints provide recording access
6. No manual download/transcription needed

## Next Phase

**Phase 2.4**: Transcript Database Sync will link transcripts to:
- Customer records
- Booking records  
- Support escalations
- AI conversation history
