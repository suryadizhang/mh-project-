# Phase 2.2: RingCentral Webhook Pipeline Analysis

## Current State Assessment

### ✅ What Exists
1. **Webhook Routers** (3 files):
   - `routers/v1/voice_webhooks.py` - Basic voice webhook handlers
   - `routers/v1/ringcentral_ai_webhooks.py` - AI-integrated webhooks
   - `routers/v1/ringcentral_voice_webhooks.py` - Additional voice endpoints

2. **Services**:
   - `ringcentral_voice_service.py` - Call state management, database operations
   - `speech_service.py` - Deepgram STT/TTS (Phase 2.1 ✅ COMPLETE)
   - `ringcentral_voice.py` - Voice service configuration

3. **Database Models**:
   - `CallRecording` model with fields:
     - `rc_call_id`, `direction`, `from_number`, `to_number`
     - `status`, `state` (INITIATED, IN_PROGRESS, RECORDED, COMPLETED, FAILED)
     - `recording_uri`, `duration_seconds`
     - Timestamps: `started_at`, `ended_at`

4. **Environment Configuration**:
   - `RC_CLIENT_ID`, `RC_CLIENT_SECRET`, `RC_JWT_TOKEN`
   - `RC_WEBHOOK_SECRET` for signature validation
   - `ENABLE_VOICE_AI=true` flag

### ❌ What's Missing

1. **RingCentralVoiceAI Service**:
   - Import exists in `ringcentral_ai_webhooks.py` but class doesn't exist
   - Location: `services/ringcentral_voice_ai.py`
   - Purpose: Bridge between RingCentral webhooks → AI orchestrator

2. **AI Orchestrator Integration**:
   - No connection to existing AI components:
     - `customer_booking_ai.py` - Booking extraction
     - `ai_pipeline.py` - Conversation orchestration
     - `enhanced_nlp_service.py` - NLP processing

3. **Webhook Signature Validation**:
   - Validation function exists but not consistently applied
   - Security risk if not enforced on all endpoints

4. **Call Recording Download**:
   - Recording URI is saved but not downloaded
   - No connection to Deepgram transcription

5. **Real-time Call Handling**:
   - No WebSocket or real-time audio streaming
   - Missing connection to Deepgram streaming STT/TTS

## Phase 2.2 Implementation Plan

### Task 1: Create RingCentralVoiceAI Service (1 hour)
**File**: `src/services/ringcentral_voice_ai.py`

**Purpose**: Bridge RingCentral webhooks to AI system

**Key Methods**:
```python
class RingCentralVoiceAI:
    async def handle_inbound_call(self, call_event: VoiceCallEvent)
    async def generate_ai_reply(self, message: str, context: dict)
    async def transcribe_and_respond(self, call_id: str, audio_url: str)
    async def route_to_ai_orchestrator(self, transcript: str, context: dict)
```

**Integration Points**:
- Import `speech_service` for Deepgram STT/TTS
- Import `ai_pipeline` for conversation orchestration
- Import `customer_booking_ai` for booking extraction
- Import `enhanced_nlp_service` for intent detection

### Task 2: Update Webhook Handlers (30 min)
**Files**: 
- `routers/v1/voice_webhooks.py`
- `routers/v1/ringcentral_ai_webhooks.py`

**Changes**:
1. **Add Signature Validation** to all endpoints:
   ```python
   if not validate_webhook_signature(body, rc_signature, settings.ringcentral_webhook_secret):
       raise HTTPException(401, "Invalid signature")
   ```

2. **Route Call Events to AI**:
   ```python
   if status == "ringing":
       await ringcentral_voice_ai.handle_inbound_call(call_data)
   elif status == "answered":
       await ringcentral_voice_ai.start_ai_conversation(call_id)
   elif status == "disconnected":
       await ringcentral_voice_ai.finalize_call(call_id)
   ```

3. **Add Error Handling**:
   - Retry logic for transient failures
   - Graceful degradation if AI unavailable
   - Comprehensive logging

### Task 3: Integrate with AI Orchestrator (1 hour)
**File**: `src/services/ai_orchestrator.py`

**Purpose**: Unified entry point for all AI interactions

**Flow**:
```
RingCentral Webhook
  ↓
RingCentralVoiceAI.handle_inbound_call()
  ↓
AI Orchestrator.process_voice_interaction()
  ↓
├→ Speech Service (Deepgram STT)
├→ Enhanced NLP Service (Intent Detection)
├→ Customer Booking AI (Booking Extraction)
└→ AI Pipeline (Response Generation)
  ↓
Speech Service (Deepgram TTS)
  ↓
RingCentral Voice API (Play Audio)
```

### Task 4: Add Webhook Testing Utilities (30 min)
**File**: `scripts/test_ringcentral_webhooks.py`

**Test Scenarios**:
1. Inbound call (ringing) → Auto-answer
2. Call answered → Start AI conversation
3. Call disconnected → Save transcript
4. Recording ready → Download and transcribe
5. Signature validation → Reject invalid requests

### Task 5: Update Environment Configuration (10 min)
**File**: `.env.example`

**Add**:
```bash
# RingCentral Webhook Configuration
RC_WEBHOOK_URL=https://your-domain.com/api/v1/ringcentral/webhooks/events
RC_AUTO_ANSWER=true
RC_AI_MODE=full_auto  # full_auto | triage | human_only

# Voice AI Settings
VOICE_AI_GREETING=Hello! Thank you for calling My Hibachi Chef. How can I help you today?
VOICE_AI_VOICE_MODEL=aura-asteria-en
VOICE_AI_MAX_CONVERSATION_TURNS=20
```

## Test Cases

### 1. Webhook Validation Test
```bash
curl -X POST http://localhost:8000/api/v1/ringcentral/webhooks/events \
  -H "Validation-Token: test-token-12345" \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: {"validation-token": "test-token-12345", "status": "validated"}
```

### 2. Inbound Call Test
```json
{
  "timestamp": "2025-11-12T10:00:00Z",
  "uuid": "call-uuid-123",
  "event": "/restapi/v1.0/account/~/telephony/sessions",
  "body": {
    "telephonySessionId": "session-123",
    "partyId": "party-456",
    "direction": "Inbound",
    "from": {"phoneNumber": "+15551234567"},
    "to": {"phoneNumber": "+15559876543"},
    "telephonyStatus": "Ringing"
  }
}
```

### 3. Signature Validation Test
```python
import hmac
import hashlib

body = b'{"test": "payload"}'
secret = "your-webhook-secret"
signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

# Add header: X-RingCentral-Signature: {signature}
```

## Success Criteria

✅ **Phase 2.2 Complete When**:
1. `RingCentralVoiceAI` service created and tested
2. Webhook signature validation enforced on all endpoints
3. Inbound calls auto-answered and routed to AI
4. Call events logged to database with correct states
5. AI orchestrator integrated with voice pipeline
6. Test suite covers all webhook scenarios (100% pass rate)

## Performance Targets

- **Webhook Response Time**: < 200ms
- **Call Answer Time**: < 3 seconds from ringing
- **AI Response Latency**: < 500ms (STT + AI + TTS)
- **Signature Validation**: 100% enforcement
- **Error Rate**: < 0.1% for webhook processing

## Next Phase Dependencies

**Phase 2.3 (Call Recording Storage)** requires:
- Recording URI saved ✅ (already implemented)
- Database schema ready ✅ (CallRecording model exists)
- File download mechanism ⏳ (Phase 2.3)

**Phase 2.4 (Transcript Sync)** requires:
- Call recordings available ⏳ (Phase 2.3)
- Deepgram transcription working ✅ (Phase 2.1 complete)
- Transcript database schema ⏳ (Phase 2.4)

**Phase 2.5 (End-to-End Flow)** requires:
- All Phase 2.1-2.4 components complete
- Integration testing of full pipeline
