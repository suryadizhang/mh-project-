# 🎙️ Deepgram Voice AI Setup Guide

**Status:** ✅ API Key Already Configured  
**Current Key:** `68b6b657c5dcae4e54b7fe99df35a71c8c519aea`
(configured in `.env`)

---

## ✅ What's Already Done

### 1. **API Key Configured**

```bash
# apps/backend/.env
DEEPGRAM_API_KEY=68b6b657c5dcae4e54b7fe99df35a71c8c519aea
ENABLE_VOICE_AI=true
```

### 2. **Service Implementation Complete**

- ✅ `speech_service.py` (505 lines) - STT + TTS with Deepgram
- ✅ `ringcentral_voice_service.py` (370 lines) - Phone integration
- ✅ `voice_assistant.py` (600 lines) - AI voice orchestrator
- ✅ Voice webhooks router (180 lines)

### 3. **Models Configured**

- **STT (Speech-to-Text):** `nova-2` (Best quality - $0.0125/min)
- **TTS (Text-to-Speech):** `aura-asteria-en` (Natural female voice -
  $0.015/1000 chars)

---

## 🔍 What Needs Verification

### Step 1: Verify API Key is Valid

Run this test script:

```bash
cd apps/backend
python -c "
import os
import asyncio
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

load_dotenv()

async def test():
    api_key = os.getenv('DEEPGRAM_API_KEY')
    print(f'Testing API Key: {api_key[:20]}...')

    try:
        client = DeepgramClient(api_key)

        # Test with a sample audio URL
        response = await client.transcribe.v('1').prerecorded(
            {'url': 'https://dpgr.am/spacewalk.wav'},
            PrerecordedOptions(model='nova-2', language='en-US')
        )

        print('✅ Deepgram API Key is VALID!')
        print(f'Transcription: {response.results.channels[0].alternatives[0].transcript[:100]}...')
        return True

    except Exception as e:
        print(f'❌ API Key verification failed: {e}')
        return False

asyncio.run(test())
"
```

### Step 2: Check Account Limits

**Deepgram offers:**

- **Free Tier:** $200 credits (first time)
- **Pay-as-you-go:** After credits used

**Check your balance:**

1. Log in to https://console.deepgram.com/
2. Go to **Billing** → **Usage**
3. Verify you have credits remaining

---

## 🎯 Deepgram Configuration Options

### Speech-to-Text Models

| Model         | Quality | Cost/Min | Use Case                          |
| ------------- | ------- | -------- | --------------------------------- |
| **nova-2** ✅ | Highest | $0.0125  | Production (Currently Configured) |
| nova          | High    | $0.0100  | Good balance                      |
| enhanced      | Medium  | $0.0043  | Budget option                     |
| base          | Basic   | $0.0025  | Testing only                      |

**Recommendation:** Keep `nova-2` for production quality.

### Text-to-Speech Voices

**Current:** `aura-asteria-en` (Natural female voice)

**Available voices:**

#### Female Voices:

- `aura-asteria-en` ✅ (Currently configured) - Warm, professional
- `aura-luna-en` - Friendly, conversational
- `aura-stella-en` - Clear, articulate
- `aura-athena-en` - Confident, engaging
- `aura-hera-en` - Mature, reassuring

#### Male Voices:

- `aura-orion-en` - Deep, authoritative
- `aura-arcas-en` - Friendly, casual
- `aura-perseus-en` - Professional, clear
- `aura-angus-en` - Warm, approachable
- `aura-orpheus-en` - Smooth, calming

**To change voice:**

```bash
# In apps/backend/.env
DEEPGRAM_TTS_MODEL=aura-luna-en  # Change to any voice above
```

---

## 🔧 Advanced Configuration (Optional)

### 1. Language Detection (Auto-detect customer language)

```bash
# In apps/backend/.env
DEEPGRAM_DETECT_LANGUAGE=true
DEEPGRAM_LANGUAGES=en,es,fr,zh  # Supported languages
```

### 2. Smart Formatting (Auto-punctuation)

```bash
# In apps/backend/.env
DEEPGRAM_SMART_FORMAT=true  # Auto-add punctuation
DEEPGRAM_DIARIZE=true       # Identify different speakers
DEEPGRAM_NUMERALS=true      # Convert "one hundred" → "100"
```

### 3. Custom Vocabulary (Industry terms)

Add MyHibachi-specific terms for better recognition:

```python
# In speech_service.py, add to PrerecordedOptions:
options = PrerecordedOptions(
    model="nova-2",
    language="en-US",
    keywords=["hibachi:3", "teppanyaki:3", "sake:2", "MyHibachi:4"]
)
```

**Keyword format:** `word:boost_level` (1-4, higher = more
recognition)

**Suggested keywords:**

- `hibachi:4` - Core service
- `teppanyaki:4` - Alternative name
- `MyHibachi:4` - Company name
- `sake:3` - Included drink
- `lobster:2`, `filet:2`, `scallops:2` - Premium proteins
- `deposit:2`, `refundable:2` - Financial terms

---

## 🧪 Testing Voice AI

### Test 1: Speech-to-Text (Transcription)

```bash
cd apps/backend
python -c "
import asyncio
from services.speech_service import SpeechService

async def test():
    service = SpeechService()

    # Test with sample audio
    result = await service.transcribe_audio(
        audio_url='https://dpgr.am/spacewalk.wav'
    )

    print(f'Transcript: {result.text}')
    print(f'Confidence: {result.confidence}')
    print(f'Duration: {result.duration}s')
    print(f'Cost: ${result.cost}')

asyncio.run(test())
"
```

### Test 2: Text-to-Speech (Voice Synthesis)

```bash
cd apps/backend
python -c "
import asyncio
from services.speech_service import SpeechService

async def test():
    service = SpeechService()

    # Generate voice response
    audio = await service.synthesize_speech(
        text='Hi! Thanks for calling MyHibachi. How can I help you today?',
        voice_model='aura-asteria-en'
    )

    # Save to file
    with open('test_output.mp3', 'wb') as f:
        f.write(audio)

    print('✅ Voice generated! Check test_output.mp3')

asyncio.run(test())
"
```

### Test 3: End-to-End Voice Call

```bash
# Call your RingCentral test number
# System will:
# 1. Answer call with Deepgram TTS greeting
# 2. Listen to your question (Deepgram STT)
# 3. Detect your tone (ToneAnalyzer)
# 4. Generate AI response (OpenAI + KnowledgeService)
# 5. Speak response (Deepgram TTS)
```

---

## 💰 Cost Estimation

### Per Voice Call (5-minute average):

**Inbound costs:**

- STT (5 min @ $0.0125/min): **$0.0625**
- TTS (300 chars @ $0.015/1000): **$0.0045**
- OpenAI GPT-4 (500 tokens): **$0.015**
- **Total per call: ~$0.08**

**Monthly projection (500 calls):**

- 500 calls × $0.08 = **$40/month** for voice AI
- Add RingCentral phone charges: **~$20/month**
- **Total voice AI cost: ~$60/month**

**ROI:**

- Replaces 500 calls × 5 min = **2,500 minutes** of staff time
- 2,500 min ÷ 60 = **42 hours saved**
- At $20/hour = **$840 saved/month**
- **Net savings: $780/month**

---

## 🚨 Troubleshooting

### Error: "Invalid API Key"

**Solution:**

1. Go to https://console.deepgram.com/
2. Navigate to **API Keys** → **Create New Key**
3. Copy new key
4. Update in `.env`:
   ```bash
   DEEPGRAM_API_KEY=your-new-key-here
   ```

### Error: "Credits Exhausted"

**Solution:**

1. Check balance: https://console.deepgram.com/billing
2. Add payment method
3. Purchase credits or enable pay-as-you-go

### Error: "Model not found"

**Solution:** Check model name spelling in `.env`:

```bash
DEEPGRAM_MODEL=nova-2  # Must be exact: nova-2, nova, enhanced, or base
DEEPGRAM_TTS_MODEL=aura-asteria-en  # Must match Deepgram voice names
```

### Poor Transcription Quality

**Solutions:**

1. **Upgrade model:**

   ```bash
   DEEPGRAM_MODEL=nova-2  # Best quality
   ```

2. **Add custom keywords:**

   ```python
   keywords=["hibachi:4", "teppanyaki:4", "deposit:3"]
   ```

3. **Enable smart formatting:**

   ```bash
   DEEPGRAM_SMART_FORMAT=true
   DEEPGRAM_PUNCTUATE=true
   ```

4. **Check audio quality:**
   - Minimum: 8kHz, mono
   - Recommended: 16kHz+, mono
   - Phone audio: 8kHz (automatically handled)

---

## ✅ Pre-Flight Checklist

Before starting Week 3 testing:

- [x] **Deepgram API Key configured** (in `.env`)
- [ ] **API Key verified** (run test script above)
- [ ] **Account has credits** (check console.deepgram.com)
- [x] **STT model configured** (`nova-2`)
- [x] **TTS voice selected** (`aura-asteria-en`)
- [x] **Voice AI enabled** (`ENABLE_VOICE_AI=true`)
- [ ] **RingCentral phone number active** (for testing calls)
- [ ] **Test call made** (verify end-to-end flow)

---

## 🎯 Recommended Settings for MyHibachi

```bash
# apps/backend/.env

# === Deepgram Configuration ===
DEEPGRAM_API_KEY=68b6b657c5dcae4e54b7fe99df35a71c8c519aea
ENABLE_VOICE_AI=true

# STT Settings (Speech-to-Text)
DEEPGRAM_MODEL=nova-2                    # Best quality
DEEPGRAM_DETECT_LANGUAGE=false           # Keep English only
DEEPGRAM_SMART_FORMAT=true               # Auto-punctuation
DEEPGRAM_DIARIZE=false                   # Single speaker (customer)
DEEPGRAM_NUMERALS=true                   # Convert numbers
DEEPGRAM_PROFANITY_FILTER=false          # Don't censor

# TTS Settings (Text-to-Speech)
DEEPGRAM_TTS_MODEL=aura-asteria-en       # Warm female voice
DEEPGRAM_TTS_SPEED=1.0                   # Normal speed
DEEPGRAM_TTS_SAMPLE_RATE=24000           # High quality audio

# Performance
DEEPGRAM_INTERIM_RESULTS=true            # Real-time transcription
DEEPGRAM_ENDPOINTING=300                 # 300ms silence detection
DEEPGRAM_VAD_TURNOFF=1000                # 1s silence = end of speech
```

---

## 📞 Testing Workflow

### 1. Verify API Key (2 min)

```bash
cd apps/backend
python scripts/test_deepgram.py  # Run verification script
```

### 2. Test Transcription (3 min)

```bash
# Upload a test audio file or use sample URL
python scripts/test_transcription.py
```

### 3. Test Voice Synthesis (3 min)

```bash
# Generate AI greeting
python scripts/test_tts.py
```

### 4. End-to-End Call Test (10 min)

```bash
# Start backend
python -m uvicorn main:app --reload

# In another terminal, make test call
# Call RingCentral number: [YOUR_RINGCENTRAL_NUMBER]
# Follow prompts and verify:
# - Greeting is clear
# - Transcription is accurate
# - AI response makes sense
# - Voice sounds natural
```

---

## 🚀 Ready to Test!

**Next Steps:**

1. ✅ Verify API key (run test script)
2. ✅ Confirm account has credits
3. ✅ Optional: Customize voice/settings
4. 🎯 **Start Week 3 Testing!**

Say **"Start Week 3"** when API verification complete! 🎯
