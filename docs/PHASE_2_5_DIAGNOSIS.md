# Phase 2.5 Testing - Issue Diagnosis

## What Happened

You called your RingCentral business number from `+1 (210) 388-4155` and got:
> "We are currently closed"

## Root Cause Analysis

### ✅ What's Working
1. Backend API running on http://0.0.0.0:8000
2. Database now has `communications.call_recordings` table
3. Test customer and booking data ready
4. Conversation API endpoints registered

### ❌ What's Missing
1. **No call recording in database** - 0 recordings found
2. **Communications schema didn't exist** - Just created manually
3. **Webhook not received** - Backend didn't log any incoming webhook

## Why "We Are Currently Closed"

This message could be from:

### Option 1: RingCentral Auto-Attendant
- RingCentral has built-in business hours settings
- Outside business hours → plays closed message
- **Call might not be recorded** if auto-attendant rejects before voicemail

### Option 2: Your AI Voice Agent
- If you have an AI agent configured on RingCentral
- It detected "closed" hours and responded
- **Call should be recorded** if AI answered

## Next Steps to Fix

### Step 1: Check RingCentral Webhook Configuration

**Question**: Do you have webhooks configured in RingCentral pointing to your backend?

To check/configure:
1. Go to: https://developers.ringcentral.com/my-account.html#/applications
2. Find your app
3. Check "Webhook URI" - should be something like:
   - `https://your-vps-domain.com/api/v1/webhooks/ringcentral/`
   - Or if using ngrok: `https://abc123.ngrok.io/api/v1/webhooks/ringcentral/`

**Current backend**: Running on http://0.0.0.0:8000 (local)  
**Issue**: RingCentral can't reach localhost!

### Step 2: Expose Backend with ngrok

If backend is on your local machine:

```powershell
# Install ngrok if not installed
scoop install ngrok

# Expose port 8000
ngrok http 8000
```

This will give you a public URL like: `https://abc123-def-456.ngrok-free.app`

Then update RingCentral webhook to:
```
https://abc123-def-456.ngrok-free.app/api/v1/webhooks/ringcentral/
```

### Step 3: Verify RingCentral Recording Settings

Check if call recording is enabled:
1. Log into RingCentral Admin Portal
2. Go to Phone System → Auto-Receptionist
3. Check if "Call Recording" is enabled
4. Make sure recording happens **for all calls** or **after business hours**

### Step 4: Check Business Hours

The "we are currently closed" suggests:
1. RingCentral business hours might be set
2. Current time: ~10 PM PST (November 12, 2025, late evening)
3. Default business hours: Usually 8 AM - 5 PM

**Options**:
- **Test during business hours** (tomorrow morning)
- **Or disable business hours** in RingCentral for testing
- **Or configure after-hours to still record calls**

## Testing Options

### Option A: Test Tomorrow During Business Hours
- Call between 8 AM - 5 PM PST
- Webhook should trigger
- Recording should be saved

### Option B: Configure RingCentral for Testing NOW
1. Set up ngrok to expose backend
2. Update RingCentral webhook URL
3. Disable business hours OR enable after-hours recording
4. Call again

### Option C: Manual Test (Skip Phone Call)
Create a fake call recording in database to test the rest of the system:

```sql
-- Insert test recording
INSERT INTO communications.call_recordings (
    rc_recording_id,
    rc_session_id,
    from_phone,
    to_phone,
    direction,
    type,
    call_started_at,
    call_ended_at,
    duration_seconds,
    status,
    rc_transcript,
    rc_transcript_confidence,
    rc_ai_insights,
    rc_transcript_fetched_at,
    state
) VALUES (
    'test-recording-001',
    'test-session-001',
    '+12103884155',
    '+19167408768',
    'Inbound',
    'inbound',
    NOW() - INTERVAL '5 minutes',
    NOW() - INTERVAL '3 minutes',
    120,
    'available',
    'Hi, this is Surya calling about my hibachi reservation for tomorrow at 7 PM for 4 people. I wanted to confirm vegetarian options are available.',
    95.5,
    '{"sentiment": "positive", "topics": ["reservation", "vegetarian", "confirmation"], "intent": "inquiry"}'::jsonb,
    NOW() - INTERVAL '2 minutes',
    'completed'
);
```

Then run the test script to verify linking works.

## What to Check Next

### 1. Is Backend Publicly Accessible?
```powershell
# Check if backend is only local
curl http://localhost:8000/health
```

If this works but RingCentral can't reach it → Need ngrok

### 2. What's in RingCentral Admin?
- Is call recording enabled?
- What are business hours?
- Is webhook configured?
- What's the webhook URL?

### 3. Do You Have AI Agent Already?
- Is there an AI answering calls?
- Is it integrated with RingCentral?
- Is it recording conversations?

## Recommended Action

**Tell me**:
1. Is your backend running on a **VPS** (public IP) or **local machine** (localhost)?
2. Do you want to set up **ngrok now** to expose localhost?
3. Or should we create a **manual test recording** to test the linking/AI context features?

Once we fix the webhook connection, your next call will be:
1. Received by RingCentral
2. Webhook sent to backend
3. Recording saved to database
4. Transcript fetched (30-60s delay)
5. Customer/booking linked automatically
6. AI context generated

---

**Current Status**: ⚠️ Webhook not configured or not reachable  
**Next**: Choose Option A, B, or C above to proceed
