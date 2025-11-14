# Real-Time Voice AI System - Complete Guide

## 🎯 Overview

Production-grade real-time voice AI system using **WebRTC** for bidirectional audio streaming between RingCentral and our AI pipeline.

**Architecture**: RingCentral → WebSocket → Audio Processing → Deepgram STT → AI Pipeline → Deepgram TTS → WebSocket → RingCentral

**Latency Target**: <100ms end-to-end
**Availability**: 99.9%+
**Success Rate**: 99%+

---

## 🏗️ Architecture

### Component Overview

```
┌─────────────────┐
│  RingCentral    │
│  (Media Gateway)│
└────────┬────────┘
         │ WebSocket (RTP/audio packets)
         ↓
┌─────────────────────────────────────────────────────────┐
│               WebRTC Call Handler                       │
│  • WebSocket connection management                      │
│  • Control/signaling message handling                   │
│  • Call lifecycle orchestration                         │
└─────────┬───────────────────────────────┬──────────────┘
          │ Audio frames                   │ Audio frames
          ↓                                ↑
┌─────────────────────┐          ┌────────────────────┐
│  Audio Processor    │          │  Deepgram TTS      │
│  • Format conversion│          │  • Text → Audio    │
│  • Resampling       │          │  • Voice synthesis │
│  • Silence detection│          └────────────────────┘
└─────────┬───────────┘                   ↑
          │ Processed frames               │ Response text
          ↓                                │
┌─────────────────────┐          ┌────────────────────┐
│  STT Bridge         │          │   AI Pipeline      │
│  • Async→thread     │          │  • Intent detection│
│  • WebSocket conn   │──────────→  • NLP analysis    │
│  • Transcript queue │          │  • Response gen    │
└─────────────────────┘          └────────────────────┘
          │ Transcripts
          ↓
┌─────────────────────┐
│  Call Session       │
│  • State management │
│  • Conversation log │
│  • Metrics tracking │
└─────────────────────┘
```

### File Structure

```
apps/backend/src/
├── services/
│   ├── realtime_voice/
│   │   ├── __init__.py                    # Module exports
│   │   ├── websocket_handler.py           # WebRTCCallHandler (320 lines)
│   │   ├── deepgram_stt_bridge.py         # DeepgramSTTBridge (330 lines)
│   │   ├── audio_processor.py             # AudioProcessor (240 lines)
│   │   └── call_session.py                # CallSession/Manager (290 lines)
│   ├── speech_service.py                  # Deepgram TTS/STT client
│   ├── enhanced_nlp_service.py            # NLP analysis
│   └── ringcentral_voice_service.py       # RingCentral integration
├── routers/v1/
│   ├── realtime_voice.py                  # WebSocket endpoints
│   └── ringcentral_voice_webhooks.py      # RingCentral webhooks
└── api/ai/endpoints/services/
    └── ai_pipeline.py                     # AI response generation
```

---

## 🔄 Call Flow

### 1. Inbound Call Received
```
RingCentral → POST /api/voice/inbound
  ├─ Create CallRecording in DB
  ├─ Build WebSocket URL
  └─ Return: {action: "answer", media: {type: "websocket", url: "..."}}
```

### 2. WebSocket Connection Established
```
RingCentral → WS /api/voice/realtime/ws/call?call_id=X&from_number=Y&to_number=Z
  ├─ Accept WebSocket connection
  ├─ Create CallSession
  ├─ Initialize AudioProcessor
  ├─ Start DeepgramSTTBridge
  ├─ Mark session IN_PROGRESS
  └─ Send greeting audio
```

### 3. Real-Time Audio Loop
```
While call active:
  ┌─ RingCentral sends audio packets (8kHz mulaw)
  ├─ AudioProcessor: mulaw→PCM, 8kHz→16kHz, mono
  ├─ STT Bridge: send audio → Deepgram WebSocket
  ├─ Deepgram: returns transcript (interim/final)
  ├─ On final transcript:
  │   ├─ NLP: extract intent, detect tone
  │   ├─ AI Pipeline: generate response
  │   ├─ Deepgram TTS: text → audio
  │   └─ WebSocket: send audio → RingCentral
  └─ Loop continues until call ends
```

### 4. Call Termination
```
WebSocket disconnect OR timeout:
  ├─ Stop STT bridge
  ├─ Mark session ENDED
  ├─ Save conversation log
  ├─ Calculate metrics (duration, transcripts, errors)
  └─ Cleanup resources
```

---

## 📦 Components

### 1. WebRTCCallHandler (`websocket_handler.py`)

**Purpose**: Main orchestrator for real-time voice calls.

**Key Methods**:
- `handle_call()`: Main entry point, manages entire call lifecycle
- `_handle_control_message()`: Processes RingCentral signaling (start/stop/config)
- `_handle_audio_packet()`: Processes incoming audio frames
- `_handle_transcript()`: Processes STT transcripts
- `_generate_and_send_response()`: AI pipeline integration
- `_send_audio()`: Sends audio back to RingCentral

**Features**:
- WebSocket connection management (30s timeout, keepalive)
- Error recovery (max 10 errors before termination)
- Automatic greeting on call start
- Escalation detection (low confidence, specific intents)

---

### 2. DeepgramSTTBridge (`deepgram_stt_bridge.py`)

**Purpose**: Bridge between asyncio (FastAPI) and sync Deepgram WebSocket.

**Architecture**:
```
Asyncio World            │  Thread World
                         │
await send_audio(frame)  │  background_thread():
  → audio_queue.put()    │    ← audio_queue.get()
                         │    → ws.send(frame)
                         │
                         │  receive_thread():
                         │    ← ws.receive()
callback(transcript) ←   │    → transcript_queue.put()
  ← transcript_queue.get()
```

**Key Components**:
- `TranscriptResult` dataclass: text, is_final, confidence, timestamp, speech_final
- Thread-safe queues: `audio_queue` (asyncio→thread), `transcript_queue` (thread→asyncio)
- Background thread: runs `with client.listen.v1.connect()` context
- Receive thread: processes Deepgram messages
- Metrics: frames_processed, transcripts_received, errors_count

**Usage**:
```python
bridge = DeepgramSTTBridge(
    deepgram_client=client,
    callback=handle_transcript,
    model="nova-2",
    language="en",
    sample_rate=16000,
)
bridge.start(asyncio.get_event_loop())
await bridge.send_audio(audio_frame)
bridge.stop()
```

---

### 3. AudioProcessor (`audio_processor.py`)

**Purpose**: Audio format conversion, resampling, buffering.

**Features**:
- **Resampling**: 8kHz → 16kHz (numpy linear interpolation)
- **Format conversion**: mulaw/alaw → PCM 16-bit
- **Channel conversion**: Stereo → mono
- **Silence detection**: RMS-based (configurable threshold)
- **Frame buffering**: Handles incomplete chunks
- **Python 3.13+ compatible**: Pure numpy (no audioop)

**AudioConfig**:
```python
AudioConfig(
    sample_rate=16000,  # Target sample rate
    channels=1,         # Mono
    sample_width=2,     # 16-bit
    frame_duration_ms=20,  # 20ms frames
)
```

**Usage**:
```python
processor = AudioProcessor(
    target_config=AudioConfig(sample_rate=16000, channels=1),
    enable_silence_detection=True,
)
frames = processor.process_frame(
    audio_data=raw_audio,
    source_rate=8000,
    source_encoding="mulaw",
)
```

---

### 4. CallSession & CallSessionManager (`call_session.py`)

**Purpose**: Call state management, conversation logging, metrics.

**CallState Enum**:
- `INITIALIZING`: Session created, components initializing
- `RINGING`: Call ringing
- `CONNECTED`: WebSocket connected
- `IN_PROGRESS`: Active conversation
- `ENDING`: Graceful shutdown in progress
- `ENDED`: Call completed successfully
- `FAILED`: Call failed with error

**CallSession** (dataclass):
```python
@dataclass
class CallSession:
    # Identifiers
    session_id: UUID
    call_id: str
    from_number: str
    to_number: str
    
    # State
    state: CallState
    is_active: bool
    should_escalate: bool
    current_intent: Optional[str]
    
    # Timestamps
    created_at: datetime
    connected_at: Optional[datetime]
    ended_at: Optional[datetime]
    
    # Components
    stt_bridge: Optional[DeepgramSTTBridge]
    audio_processor: Optional[AudioProcessor]
    websocket: Optional[WebSocket]
    
    # Conversation
    turn_count: int
    messages: List[Dict]
    transcripts: List[Dict]
    
    # Metrics
    audio_frames_received: int
    audio_frames_sent: int
    transcripts_count: int
    errors_count: int
```

**CallSessionManager** (singleton):
```python
manager = call_session_manager

# Create session
session = await manager.create_session(call_id, from_number, to_number)

# Get session
session = manager.get_session(session_id)

# End session (cleanup)
await manager.end_session(session_id)

# Statistics
stats = manager.get_stats()
# {active_sessions: 3, total_calls: 150, completed: 145, failed: 5, success_rate: 0.97}
```

---

## 🔌 API Endpoints

### WebSocket Endpoint
```
WS /api/voice/realtime/ws/call
Query params:
  - call_id: RingCentral call ID
  - from_number: Caller number (E.164)
  - to_number: Called number (E.164)
  - session_id: Optional session ID

Example:
ws://localhost:8000/api/voice/realtime/ws/call?call_id=abc123&from_number=+15555551234&to_number=+15555555678
```

### Health Check
```
GET /api/voice/realtime/health

Response:
{
  "status": "healthy",
  "deepgram": "healthy",
  "active_calls": 3,
  "total_calls": 150,
  "success_rate": 0.97
}
```

### Inbound Call Webhook
```
POST /api/voice/inbound

Request (from RingCentral):
{
  "event": "call.inbound",
  "body": {
    "id": "call-123",
    "from": {"phoneNumber": "+15555551234"},
    "to": {"phoneNumber": "+15555555678"}
  }
}

Response (to RingCentral):
{
  "action": "answer",
  "media": {
    "type": "websocket",
    "url": "ws://example.com/api/voice/realtime/ws/call?...",
    "format": {
      "encoding": "pcm",
      "sampleRate": 8000,
      "channels": 1
    }
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Deepgram (REQUIRED)
DEEPGRAM_API_KEY=your-key-here
DEEPGRAM_MODEL=nova-2
DEEPGRAM_TTS_MODEL=aura-asteria-en
ENABLE_VOICE_AI=true

# Real-time Voice
VOICE_WEBSOCKET_TIMEOUT=30       # WebSocket timeout (seconds)
VOICE_AUDIO_SAMPLE_RATE=16000    # Target audio sample rate (Hz)
VOICE_SILENCE_THRESHOLD=0.01     # Silence detection threshold (RMS)
VOICE_MAX_ERRORS=10              # Max errors before termination

# RingCentral (REQUIRED)
RC_CLIENT_ID=your-client-id
RC_CLIENT_SECRET=your-client-secret
RC_JWT_TOKEN=your-jwt-token
RC_WEBHOOK_SECRET=your-webhook-secret
RC_SERVER_URL=https://platform.ringcentral.com
```

### Audio Configuration Defaults

```python
# Target configuration (Deepgram requirements)
sample_rate: 16000 Hz  # 16kHz
channels: 1            # Mono
sample_width: 2        # 16-bit PCM
frame_duration: 20ms   # 320 bytes per frame at 16kHz

# Source configuration (typical RingCentral)
source_rate: 8000 Hz   # 8kHz
source_encoding: mulaw # μ-law or PCM
```

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/api/voice/realtime/health
```

### TTS Test
```bash
curl -X POST "http://localhost:8000/api/voice/test?text=Hello%20world" \
  --output test.mp3
```

### WebSocket Test (using wscat)
```bash
npm install -g wscat

wscat -c "ws://localhost:8000/api/voice/realtime/ws/call?call_id=test-123&from_number=+15555551234&to_number=+15555555678"

# Send control message
> {"type": "start"}

# Send audio (binary)
> <binary audio data>
```

### Integration Test (simulate full call)
```python
import asyncio
import websockets

async def test_call():
    uri = "ws://localhost:8000/api/voice/realtime/ws/call?call_id=test-123&from_number=+15555551234&to_number=+15555555678"
    
    async with websockets.connect(uri) as ws:
        # Send start signal
        await ws.send('{"type": "start"}')
        
        # Send test audio (silence for now)
        audio = b'\x00' * 320  # 20ms of silence at 16kHz
        for _ in range(50):  # 1 second
            await ws.send(audio)
            await asyncio.sleep(0.02)
        
        # Receive greeting audio
        response = await ws.recv()
        print(f"Received {len(response)} bytes")

asyncio.run(test_call())
```

---

## 📊 Monitoring

### Metrics Tracked

**Per-Call Metrics**:
- Duration (connected_at → ended_at)
- Audio frames received/sent
- Transcripts count
- Errors count
- Final state (completed/failed)

**System Metrics**:
- Active calls (concurrent)
- Total calls (lifetime)
- Success rate (completed / total)
- Average call duration
- Error rate

### Call Session Lifecycle
```python
# Get session stats
stats = call_session_manager.get_stats()

# {
#   "active_sessions": 3,
#   "total_calls": 150,
#   "completed_calls": 145,
#   "failed_calls": 5,
#   "success_rate": 0.9666666666666667
# }
```

### Logging

All components log at appropriate levels:
- **INFO**: Call start/end, transcripts, AI responses
- **WARNING**: Low confidence, escalation triggers
- **ERROR**: Processing errors, WebSocket issues
- **DEBUG**: Interim transcripts, audio frame details

**Example logs**:
```
INFO: 🔌 WebSocket connected | call=abc123
INFO: 📞 Call start signal | session=uuid-123
INFO: 👋 Sending greeting | session=uuid-123
INFO: 📝 Final transcript: 'I want to book a table' (conf=0.95)
INFO: 🧠 NLP | intent=booking | conf=0.95 | tone=neutral
INFO: 🤖 AI response: 'I'd be happy to help you book a table...'
INFO: 📤 Sent audio | size=25704 bytes
INFO: 📴 Call stop signal | session=uuid-123
INFO: ✅ Call ended | duration=125.3s | transcripts=8 | errors=0
```

---

## 🚀 Deployment

### Prerequisites
1. Python 3.11+
2. Deepgram API key (https://console.deepgram.com/)
3. RingCentral account with WebRTC API access
4. PostgreSQL database
5. Redis (for session management)

### Installation
```bash
cd apps/backend
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
# Edit .env with your credentials
nano .env
```

### Run Server
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### RingCentral Webhook Setup

1. Go to RingCentral Developer Portal
2. Create/edit your app
3. Configure webhooks:
   - Event: `call.inbound`
   - URL: `https://your-domain.com/api/voice/inbound`
   - Webhook secret: (set in RC_WEBHOOK_SECRET)

4. Configure WebRTC media gateway:
   - Enable WebSocket audio streaming
   - Set format: PCM or mulaw, 8kHz, mono
   - Connection URL will be provided dynamically by webhook response

---

## 🔒 Security

### WebSocket Security
- Origin validation (check `request.headers.get('origin')`)
- Authentication via query params (call_id verification)
- Rate limiting on connection attempts
- Max connection duration (timeout)

### Audio Security
- Input validation (sample rate, channels, format)
- Buffer size limits (prevent memory exhaustion)
- Error count limits (prevent infinite loops)

### Data Security
- Conversation logs encrypted at rest
- Audio streams not persisted (real-time only)
- PII scrubbing in logs
- GDPR compliance (delete on request)

---

## 🐛 Troubleshooting

### Issue: WebSocket connection refused
**Solution**: Check firewall, ensure port 8000 accessible, verify URL format

### Issue: No audio received from RingCentral
**Solution**: 
- Verify RingCentral media config (encoding, sample rate)
- Check logs for audio packet messages
- Test with simpler audio format (PCM instead of mulaw)

### Issue: STT not working
**Solution**:
- Verify Deepgram API key
- Check audio format (must be 16kHz mono PCM for Deepgram)
- Inspect `frames_processed` metric (should be incrementing)
- Check Deepgram console for API usage

### Issue: High latency (>500ms)
**Solution**:
- Profile each component:
  - Audio processing: <10ms
  - STT: <100ms (Deepgram)
  - AI pipeline: <200ms
  - TTS: <100ms (Deepgram)
- Check network latency to Deepgram
- Optimize AI pipeline (caching, simpler models)
- Consider regional Deepgram endpoints

### Issue: Call drops after 30 seconds
**Solution**:
- WebSocket timeout triggered (no activity)
- Increase `VOICE_WEBSOCKET_TIMEOUT`
- Ensure keepalive messages sent
- Check RingCentral connection status

---

## 📈 Performance Optimization

### Latency Optimization
1. **Async everything**: All I/O operations are async
2. **Parallel processing**: STT and AI pipeline run concurrently where possible
3. **Frame buffering**: Minimize context switches
4. **Connection pooling**: Reuse Deepgram connections

### Resource Optimization
1. **Memory**: Frame buffers limited to 1 second max
2. **CPU**: Numpy-based audio processing (vectorized)
3. **Network**: Deepgram WebSocket (single connection per call)
4. **Database**: Async SQLAlchemy, connection pooling

### Scalability
- **Horizontal**: Multiple FastAPI workers (gunicorn)
- **Vertical**: Multi-threading for STT bridge
- **Load balancing**: Nginx/HAProxy for WebSocket connections
- **Auto-scaling**: Based on active_calls metric

---

## 🎓 Advanced Topics

### Custom Voice Models
```python
# In websocket_handler.py, modify:
audio_bytes = await speech_service.synthesize_speech(
    text=response,
    voice_model="aura-zeus-en",  # Male voice
    # voice_model="aura-asteria-en",  # Female voice (default)
    # voice_model="aura-athena-en",  # Professional female
)
```

### Conversation Context
```python
# CallSession stores full conversation history
session.messages = [
    {"role": "assistant", "content": "Hello! How can I help?"},
    {"role": "user", "content": "I want to book a table"},
    {"role": "assistant", "content": "I'd be happy to help..."},
]

# Pass to AI pipeline for context-aware responses
ai_context["conversation_history"] = session.messages[-5:]  # Last 5 turns
```

### Escalation Triggers
```python
# In _generate_and_send_response():
if intent in ["complaint", "escalation", "manager"]:
    session.should_escalate = True
    logger.warning("⚠️ Escalation triggered")
    # Transfer to human agent (implement in RingCentral)

if confidence < 0.4:
    session.should_escalate = True
    logger.warning("⚠️ Low confidence, escalating")
```

### Audio Quality Modes
```python
# Low latency (lower quality)
AudioConfig(sample_rate=8000, channels=1, sample_width=2)

# High quality (higher latency)
AudioConfig(sample_rate=48000, channels=1, sample_width=2)

# Balanced (default)
AudioConfig(sample_rate=16000, channels=1, sample_width=2)
```

---

## 📚 References

- [Deepgram API Docs](https://developers.deepgram.com/)
- [RingCentral WebRTC Guide](https://developers.ringcentral.com/guide/voice/webrtc)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Numpy Audio Processing](https://numpy.org/doc/stable/user/quickstart.html)

---

## ✅ Checklist

**Production Readiness**:
- [x] WebSocket handler implementation
- [x] STT bridge with threading
- [x] Audio processor (numpy-based)
- [x] Call session management
- [x] API endpoints (WebSocket + health)
- [x] RingCentral webhook integration
- [ ] Integration tests
- [ ] Load testing (100+ concurrent calls)
- [ ] Monitoring/alerting setup
- [ ] Error rate tracking
- [ ] Graceful shutdown
- [ ] Documentation complete

**Next Steps**:
1. Write integration tests
2. Add monitoring integration
3. Implement graceful shutdown
4. Load test with simulated calls
5. Production deployment

---

**Status**: 🟡 Core implementation complete, testing pending

**Last Updated**: 2025-01-13
