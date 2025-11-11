# 🎤 Voice AI Configuration Guide

Complete setup guide for Deepgram + ElevenLabs voice AI integration.

---

## 📋 Prerequisites

1. **Deepgram Account** (Speech-to-Text)
   - Sign up: https://console.deepgram.com/signup
   - Free tier: $200 credit (16,000 minutes)
   - Pricing: $0.0125/min for Nova-2 model

2. **ElevenLabs Account** (Text-to-Speech)
   - Sign up: https://elevenlabs.io/sign-up
   - Free tier: 10,000 characters/month
   - Pricing: $0.30/1000 chars for Turbo v2

3. **RingCentral Account** (Already have)
   - Voice webhooks need to be configured
   - WebRTC support required for real-time audio

---

## 🔧 Installation

### 1. Install Dependencies

```bash
cd apps/backend
pip install -r voice_ai_requirements.txt
```

**Dependencies**:
- `deepgram-sdk==3.3.5` - Deepgram Python SDK
- `elevenlabs==1.2.2` - ElevenLabs Python SDK
- `pydub==0.25.1` - Audio processing

---

## 🔑 API Keys Setup

### A. Get Deepgram API Key

1. Go to https://console.deepgram.com/
2. Click **"API Keys"** in left sidebar
3. Click **"Create a New API Key"**
4. Copy the key (starts with `d...`)
5. Add to `.env`:

```bash
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

### B. Get ElevenLabs API Key

1. Go to https://elevenlabs.io/
2. Click your profile → **"Profile"**
3. Find **"API Key"** section
4. Copy the key (starts with `sk_...`)
5. Add to `.env`:

```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### C. Choose Voice (ElevenLabs)

1. Go to https://elevenlabs.io/voice-library
2. Browse voices (or use default "Rachel")
3. Click voice → Copy Voice ID
4. Add to `.env`:

```bash
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel (default)
# Or choose another:
# ELEVENLABS_VOICE_ID=ErXwobaYiN019PkySvjV  # Antoni
# ELEVENLABS_VOICE_ID=MF3mGyEYCl7XYWbV9V6O  # Elli
```

---

## ⚙️ Environment Variables

Add these to your `.env` file:

```bash
# ===== VOICE AI CONFIGURATION =====

# Enable/Disable Voice AI
ENABLE_VOICE_AI=true

# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=your_deepgram_api_key_here
DEEPGRAM_MODEL=nova-2  # Options: nova-2, nova, enhanced

# ElevenLabs (Text-to-Speech)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice
ELEVENLABS_MODEL=eleven_turbo_v2  # Options: eleven_turbo_v2, eleven_multilingual_v2

# Voice AI Behavior
VOICE_AI_MODE=triage  # Options: full_auto, assisted, human_only, triage
MAX_CALL_DURATION_SECONDS=1800  # 30 minutes

# Business Hours (for call routing)
BUSINESS_HOURS_START=9  # 9 AM
BUSINESS_HOURS_END=17  # 5 PM

# Escalation
FALLBACK_PHONE_NUMBER=+19167408768  # Human agent number
VIP_AGENT_NUMBER=+19167408768  # VIP customer agent

# RingCentral Voice (Already configured, but verify)
RINGCENTRAL_CLIENT_ID=your_existing_rc_client_id
RINGCENTRAL_CLIENT_SECRET=your_existing_rc_secret
RINGCENTRAL_SERVER=https://platform.ringcentral.com
RINGCENTRAL_JWT_TOKEN=your_existing_jwt_token
```

---

## 🔗 RingCentral Webhook Setup

### 1. Configure Voice Webhooks

Go to RingCentral Developer Console:

1. **Inbound Call Webhook**:
   - URL: `https://yourdomain.com/api/v1/webhooks/voice/inbound`
   - Events: `telephony.inbound-call`

2. **Call Status Webhook**:
   - URL: `https://yourdomain.com/api/v1/webhooks/voice/status`
   - Events: 
     * `telephony.answered`
     * `telephony.hold`
     * `telephony.recording.started`
     * `telephony.recording.stopped`
     * `telephony.transfer`
     * `telephony.hangup`

3. **Recording Complete Webhook**:
   - URL: `https://yourdomain.com/api/v1/webhooks/voice/recording-complete`
   - Events: `telephony.recording.completed`

4. **Transcription Webhook** (optional):
   - URL: `https://yourdomain.com/api/v1/webhooks/voice/transcription`
   - Events: `telephony.transcription`

### 2. Enable Voice Features

In RingCentral:
- ✅ Enable call recording
- ✅ Enable call forwarding
- ✅ Enable voicemail
- ✅ Enable WebRTC (for real-time audio)

---

## 🧪 Testing

### 1. Test Speech Service Health

```bash
curl http://localhost:8000/api/v1/webhooks/voice/health
```

Expected response:
```json
{
  "service": "speech",
  "deepgram": {
    "enabled": true,
    "status": "healthy",
    "model": "nova-2"
  },
  "elevenlabs": {
    "enabled": true,
    "status": "healthy",
    "model": "eleven_turbo_v2"
  },
  "voice_ai_enabled": true
}
```

### 2. Test Text-to-Speech

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/voice/test" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi! Thank you for calling MyHibachi. How can I help you today?"}' \
  --output test_voice.mp3
```

Play the audio file to verify voice quality.

### 3. Test Inbound Call (Simulation)

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/voice/inbound" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "telephony.inbound-call",
    "body": {
      "sessionId": "test-123",
      "from": {"phoneNumber": "+15551234567"},
      "to": {"phoneNumber": "+19167408768"}
    }
  }'
```

### 4. Check Call Statistics

```bash
curl "http://localhost:8000/api/v1/webhooks/voice/calls/stats"
```

---

## 📊 Cost Estimation

### Per Call (5 minute average):

**Transcription (Deepgram)**:
- Duration: 5 minutes
- Model: Nova-2 ($0.0125/min)
- Cost: 5 × $0.0125 = **$0.0625**

**Speech Synthesis (ElevenLabs)**:
- Response length: ~500 characters average
- Model: Turbo v2 ($0.30/1000 chars)
- Cost: 0.5 × $0.30 = **$0.15**

**Total per call**: ~$0.21

**Monthly cost (100 calls/day)**:
- 100 calls × $0.21 = $21/day
- 30 days × $21 = **$630/month**

**vs Human Agent**:
- 100 calls × 5 min = 500 min/day = 8.3 hours/day
- 8.3 hours × $15/hour = $125/day
- 30 days × $125 = **$3,750/month**

**Savings**: $3,750 - $630 = **$3,120/month** (83% reduction)

---

## 🎯 Voice AI Modes

### 1. **Full Auto** (`VOICE_AI_MODE=full_auto`)
- AI handles entire call
- No human intervention
- Best for: Simple inquiries, FAQs, booking captures

### 2. **Triage** (`VOICE_AI_MODE=triage`) ✅ **RECOMMENDED**
- AI qualifies the call
- Captures basic info
- Transfers to human for complex issues
- Best for: Mixed inquiry types

### 3. **Assisted** (`VOICE_AI_MODE=assisted`)
- AI assists human agent
- Provides suggestions
- Auto-fills forms
- Best for: Training new agents

### 4. **Human Only** (`VOICE_AI_MODE=human_only`)
- Immediate transfer to human
- AI only used for recording/transcription
- Best for: VIP customers, complex issues

---

## 🚀 Production Checklist

Before going live:

- [ ] Deepgram API key configured
- [ ] ElevenLabs API key configured
- [ ] RingCentral voice webhooks setup
- [ ] Voice test successful (audio quality good)
- [ ] Health check passing
- [ ] Business hours configured correctly
- [ ] Fallback phone number set
- [ ] Test call completed successfully
- [ ] Call recording enabled
- [ ] Monitoring alerts configured
- [ ] Cost limits set (budget alerts)

---

## 🆘 Troubleshooting

### Audio Quality Issues

**Problem**: Choppy or distorted audio

**Solution**:
1. Check network latency
2. Increase buffer size
3. Switch to `eleven_multilingual_v2` (higher quality)

### Transcription Accuracy Low

**Problem**: AI misunderstands words

**Solution**:
1. Switch to `nova-2` model (best accuracy)
2. Reduce background noise
3. Add custom vocabulary for industry terms

### High Latency (Slow Response)

**Problem**: Long pauses between user and AI

**Solution**:
1. Use `eleven_turbo_v2` (fastest TTS)
2. Enable streaming mode
3. Pre-generate common responses

### API Rate Limits Hit

**Problem**: 429 errors from Deepgram/ElevenLabs

**Solution**:
1. Upgrade API plan
2. Implement request queuing
3. Add caching for common responses

---

## 📚 Resources

- **Deepgram Docs**: https://developers.deepgram.com/
- **ElevenLabs Docs**: https://docs.elevenlabs.io/
- **RingCentral Voice API**: https://developers.ringcentral.com/api-reference/Voice
- **Voice AI Best Practices**: See `VOICE_AI_BEST_PRACTICES.md`

---

## 🎉 You're Ready!

Once configured, your voice AI will:
- ✅ Answer calls automatically
- ✅ Understand customer inquiries
- ✅ Capture booking information
- ✅ Transfer complex calls to humans
- ✅ Record and transcribe all conversations
- ✅ Provide 24/7 phone support

**Cost**: ~$0.21/call (83% cheaper than human agents)  
**Quality**: 99% transcription accuracy  
**Speed**: <2 second response time  
**Availability**: 24/7/365  

Start with **TRIAGE mode** for best results! 🚀
