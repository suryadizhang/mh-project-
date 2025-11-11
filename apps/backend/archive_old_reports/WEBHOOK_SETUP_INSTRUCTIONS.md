# 🎉 WEBHOOK TESTING READY - SERVICES RUNNING

## ✅ Status: ALL SYSTEMS GO!

### 🚀 Running Services

1. **Backend Server**: ✅ Running on `http://localhost:8000`
   - FastAPI application loaded
   - All API endpoints active
   - Rate limiting enabled (memory-based fallback)
   - Redis warnings expected (using fallback)

2. **Cloudflare Tunnel**: ✅ Running
   - **Public URL**: `https://proceedings-settlement-houston-orders.trycloudflare.com`
   - Status: Connected to Cloudflare edge (sjc08)
   - Protocol: QUIC
   - Note: Quick tunnel has no uptime guarantee (use for testing only)

3. **API Integrations**: ✅ 8/8 Passing
   - Google Maps API
   - RingCentral SMS (JWT auth)
   - OpenAI GPT-4
   - Stripe Payments
   - Plaid Banking
   - Meta (Facebook + Instagram)
   - Cloudinary Images
   - Environment Variables

---

## 📋 NEXT STEPS: Configure Webhooks

### 1. Stripe Webhooks

**Dashboard**: https://dashboard.stripe.com/test/webhooks/create

**Configuration**:
```
Webhook URL: https://proceedings-settlement-houston-orders.trycloudflare.com/api/v1/webhooks/stripe

Events to listen for:
✅ payment_intent.succeeded
✅ payment_intent.payment_failed  
✅ checkout.session.completed
✅ charge.succeeded
✅ charge.failed
```

**After creation**:
1. Copy the **Signing Secret** (starts with `whsec_`)
2. Update `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`
3. Restart backend server

**Test**:
- Go to: https://dashboard.stripe.com/test/payments/new
- Amount: $50.00
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- Click "Create payment"
- Check backend logs for webhook event

---

### 2. Meta (Facebook/Instagram) Webhooks

**Dashboard**: https://developers.facebook.com/apps/YOUR_APP_ID/webhooks/

**Configuration**:
```
Callback URL: https://proceedings-settlement-houston-orders.trycloudflare.com/api/v1/webhooks/meta

Verify Token: myhibachi-meta-webhook-verify-token-2025
(This is already in your .env file)
```

**Subscribe to Fields**:

**Facebook Page:**
- ✅ messages
- ✅ messaging_postbacks
- ✅ message_echoes
- ✅ feed (for comments)

**Instagram:**
- ✅ messages (DMs)
- ✅ messaging_postbacks
- ✅ comments
- ✅ mentions

**Test Facebook**:
1. Go to your Facebook Page
2. Click "Message" button
3. Send: "Hi! I'd like to book a hibachi chef for this weekend"
4. Check backend logs for incoming message
5. Should receive AI auto-reply within 2-5 seconds

**Test Instagram**:
1. Open Instagram app on phone
2. Go to your business profile
3. Send DM: "What's your pricing?"
4. Check for AI auto-reply

---

### 3. RingCentral Webhooks

**Dashboard**: https://developers.ringcentral.com/my-account.html#/applications/3ADYc6Nv8qxeddtHygnfIK/webhooks

**Configuration**:
```
Webhook URL: https://proceedings-settlement-houston-orders.trycloudflare.com/api/v1/webhooks/ringcentral

Verification Token: Use RC_WEBHOOK_SECRET from .env
```

**Subscribe to Events**:
- ✅ `/restapi/v1.0/account/~/extension/~/message-store` - SMS messages
- ✅ `/restapi/v1.0/account/~/extension/~/presence` - Call status
- ✅ `/restapi/v1.0/account/~/telephony/sessions` - Active calls

**Test SMS**:
1. Send SMS to: **+1 (916) 740-8768**
2. Message: "Hello, I'm interested in booking a hibachi chef"
3. Check backend logs
4. Should receive AI auto-reply SMS

**Note**: SMS feature may need verification from RingCentral support (as mentioned earlier)

---

## 🔍 Monitoring Webhooks

### Watch Backend Logs

Look for these log entries:
```
INFO:     POST /api/v1/webhooks/stripe HTTP/1.1" 200 OK
INFO:     Stripe webhook received: payment_intent.succeeded
INFO:     Payment successful: $50.00

INFO:     POST /api/v1/webhooks/meta HTTP/1.1" 200 OK  
INFO:     Meta webhook received: messages
INFO:     AI auto-reply sent to Facebook user

INFO:     POST /api/v1/webhooks/ringcentral HTTP/1.1" 200 OK
INFO:     RingCentral webhook received: message-store
INFO:     New SMS from: +1234567890
```

### Check Database Records

Open SQLite database:
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
& "C:/Users/surya/projects/MH webapps/.venv/Scripts/python.exe" -c "
import sqlite3
conn = sqlite3.connect('test_myhibachi.db')
cursor = conn.cursor()

print('Recent messages:')
cursor.execute('SELECT * FROM messages ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)

print('\nRecent AI responses:')
cursor.execute('SELECT * FROM ai_responses ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)
"
```

---

## ✅ Testing Checklist

### Stripe Payment Webhook
- [ ] Webhook URL configured in Stripe dashboard
- [ ] Webhook signing secret updated in .env
- [ ] Backend server restarted
- [ ] Test payment created successfully
- [ ] Webhook event received in backend logs
- [ ] Database record created

### Meta Webhooks (Facebook)
- [ ] Callback URL configured
- [ ] Verify token matches .env
- [ ] Page subscription active
- [ ] Test message sent to Facebook Page
- [ ] Webhook received in backend
- [ ] AI auto-reply sent within 5 seconds
- [ ] Conversation visible in Unified Inbox

### Meta Webhooks (Instagram)  
- [ ] Instagram account connected
- [ ] Instagram subscription active
- [ ] Test DM sent to Instagram
- [ ] Webhook received
- [ ] AI auto-reply sent
- [ ] Conversation logged

### RingCentral SMS Webhook
- [ ] Webhook URL configured
- [ ] Event subscriptions active
- [ ] Test SMS sent to +19167408768
- [ ] Webhook received
- [ ] SMS parsed correctly
- [ ] AI auto-reply sent via SMS

---

## ⚠️ Important Notes

### Cloudflare Tunnel Limitations
- **No uptime guarantee** - This is a quick tunnel for testing
- **May disconnect** after inactivity or randomly
- **Regenerates URL** every time you restart
- For production, use a named tunnel with Cloudflare account

### If Tunnel Disconnects
1. Stop the tunnel (Ctrl+C in terminal)
2. Restart: `.\cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate`
3. **Copy new URL** from output
4. **Update all webhook configurations** with new URL

### Backend Server
- Running in reload mode - changes to code will auto-restart
- Redis warnings are expected (using memory fallback)
- Rate limiting is active
- Request IDs tracked for distributed tracing

### AI Auto-Reply Settings
Check `.env` for AI behavior:
```properties
ENABLE_AI_AUTO_REPLY=true
AI_CONFIDENCE_THRESHOLD=80
SOCIAL_AI_ENABLED=true
SOCIAL_AUTO_REPLY_ENABLED=false  # Change to true for full automation
SOCIAL_RESPONSE_DELAY_MINUTES=2
```

---

## 📊 Expected Results

### Successful Webhook Flow

1. **Webhook Received**: HTTP POST to webhook endpoint
2. **Signature Verified**: Request authenticated
3. **Event Parsed**: JSON payload extracted
4. **Action Triggered**: 
   - Database record created
   - AI analysis performed
   - Response sent back
5. **Response**: HTTP 200 OK returned

### Typical Response Times
- Stripe webhook: < 100ms (database write)
- Meta webhook: 2-5 seconds (AI processing + reply)
- RingCentral webhook: 3-7 seconds (AI + SMS send)

---

## 🎯 Success Metrics

After completing all webhook tests, you should have:

✅ **Stripe**: Payment webhook working, test payment recorded
✅ **Facebook**: Message webhook working, AI replied to test message  
✅ **Instagram**: DM webhook working, AI replied to test DM
✅ **RingCentral**: SMS webhook working, AI replied via SMS
✅ **Database**: All events logged in SQLite database
✅ **Logs**: Clean logs showing successful webhook processing
✅ **No Errors**: All webhooks returning HTTP 200

---

## 🚀 Ready to Test!

**Current Status**:
- ✅ Backend running on port 8000
- ✅ Cloudflare tunnel active  
- ✅ Public URL: `https://proceedings-settlement-houston-orders.trycloudflare.com`
- ✅ All API integrations tested and working

**Start configuring webhooks now!** 🎉

Estimated time: 30-40 minutes for complete webhook setup and testing.
