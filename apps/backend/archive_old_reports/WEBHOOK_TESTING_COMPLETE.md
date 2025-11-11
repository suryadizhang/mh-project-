# 🎉 WEBHOOK TESTING - READY TO START

## ✅ Integration Status: 8/8 PASSED

All API integrations are now working and ready for webhook testing!

### Test Results Summary
- ✅ **Google Maps API**: Distance Matrix, Geocoding, Travel Fee Calculator
- ✅ **RingCentral API**: JWT Authentication, SMS/Voice capabilities
- ✅ **OpenAI API**: GPT-4 model, AI auto-reply ready
- ✅ **Stripe API**: Payment processing, Account verified
- ✅ **Plaid API**: Banking integration (sandbox)
- ✅ **Meta API**: Facebook Page + Instagram connected
- ✅ **Cloudinary API**: Image upload for reviews
- ✅ **Environment Variables**: All 32 variables configured

---

## 📋 Webhook Testing Plan

### Step 1: Start Backend Server
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start Cloudflare Tunnel (in new terminal)
```powershell
cd $env:USERPROFILE\cloudflared
.\cloudflared.exe tunnel --url http://localhost:8000
```

**Copy the public URL** that appears (e.g., `https://random-name.trycloudflare.com`)

---

## 🔗 Webhook Configuration URLs

Once you have the Cloudflare Tunnel URL, configure webhooks:

### 1. Stripe Webhooks
**Dashboard**: https://dashboard.stripe.com/test/webhooks

**Webhook URL**: `https://YOUR-TUNNEL-URL/api/v1/webhooks/stripe`

**Events to listen for**:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `checkout.session.completed`
- `charge.succeeded`
- `charge.failed`

**Signing secret**: Copy and update `STRIPE_WEBHOOK_SECRET` in .env

---

### 2. Meta (Facebook/Instagram) Webhooks
**Dashboard**: https://developers.facebook.com/apps/YOUR_APP_ID/webhooks/

**Callback URL**: `https://YOUR-TUNNEL-URL/api/v1/webhooks/meta`

**Verify Token**: `myhibachi-meta-webhook-verify-token-2025` (already in .env)

**Subscription Fields**:
- `messages` - For Facebook Messenger
- `messaging_postbacks` - For button clicks
- `message_echoes` - For sent messages
- `feed` - For page posts/comments

**Instagram Webhook Fields**:
- `messages` - For Instagram DMs
- `messaging_postbacks` - For quick replies
- `comments` - For post comments
- `mentions` - For @mentions

---

### 3. RingCentral Webhooks
**Dashboard**: https://developers.ringcentral.com/my-account.html#/applications/3ADYc6Nv8qxeddtHygnfIK/settings

**Webhook URL**: `https://YOUR-TUNNEL-URL/api/v1/webhooks/ringcentral`

**Events to subscribe**:
- `/restapi/v1.0/account/~/extension/~/message-store` - For SMS messages
- `/restapi/v1.0/account/~/extension/~/presence` - For call status
- `/restapi/v1.0/account/~/telephony/sessions` - For active calls

**Verification Token**: Use `RC_WEBHOOK_SECRET` from .env

---

## 🧪 Testing Webhooks

### Test Stripe Payment
1. Go to Stripe Dashboard → Payments → Create payment
2. Use test card: `4242 4242 4242 4242`
3. Any future expiry date, any CVC
4. Complete payment
5. Check backend logs for webhook event

### Test Meta Messages
**Facebook Page**:
1. Go to: https://www.facebook.com/profile.php?id=61571225263602
2. Click "Message"
3. Send a test message: "Hello, I'd like to book a hibachi chef"
4. AI should auto-reply within seconds

**Instagram DM**:
1. Go to: https://www.instagram.com/direct/inbox/
2. Find My Hibachi page
3. Send test message
4. Check for auto-reply

### Test RingCentral SMS
1. Send SMS to: +19167408768
2. Message: "Hi, I'm interested in booking"
3. Check backend logs for incoming SMS
4. AI should auto-reply via SMS

---

## 🔍 Monitoring Webhooks

### Backend Logs
Watch for incoming webhooks:
```
INFO:     Stripe webhook received: payment_intent.succeeded
INFO:     Meta webhook received: messages
INFO:     RingCentral webhook received: message-store
```

### Database Records
Check SQLite database for created records:
```python
import sqlite3
conn = sqlite3.connect('test_myhibachi.db')
cursor = conn.cursor()

# Check incoming messages
cursor.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 5")
print(cursor.fetchall())

# Check AI responses
cursor.execute("SELECT * FROM ai_responses ORDER BY created_at DESC LIMIT 5")
print(cursor.fetchall())
```

---

## 🎯 Success Criteria

### ✅ Webhook is working when:
1. **Request received**: Backend logs show incoming webhook
2. **Signature verified**: No authentication errors
3. **Data parsed**: Event type and payload extracted
4. **Action taken**: Database record created or API call made
5. **Response sent**: HTTP 200 returned to webhook provider

### ⚠️ Common Issues:

**Tunnel disconnects**: Cloudflare tunnel may disconnect after inactivity
- **Solution**: Keep terminal open, restart if needed

**Signature mismatch**: Webhook secret incorrect
- **Solution**: Copy fresh secret from provider dashboard, update .env, restart backend

**Timeout**: Backend takes too long to respond
- **Solution**: Check if background workers are running, optimize AI response time

---

## 📝 Testing Checklist

- [ ] Backend server running (port 8000)
- [ ] Cloudflare tunnel running and URL copied
- [ ] Stripe webhook configured and tested
- [ ] Meta webhook configured (Facebook + Instagram)
- [ ] RingCentral webhook configured
- [ ] Test payment processed successfully
- [ ] Test Facebook message sent and replied
- [ ] Test Instagram DM sent and replied
- [ ] Test SMS sent and replied
- [ ] Database records created for all events
- [ ] AI auto-replies working correctly

---

## 🚀 Ready to Start!

**Run these commands in separate terminals**:

Terminal 1 - Backend:
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Cloudflare Tunnel:
```powershell
cd $env:USERPROFILE\cloudflared
.\cloudflared.exe tunnel --url http://localhost:8000
```

Then configure webhooks with the tunnel URL!

---

## 📊 Expected Timeline

- **Setup**: 10 minutes (start servers, configure webhooks)
- **Testing**: 20 minutes (test all 3 webhook providers)
- **Validation**: 10 minutes (verify database records, check logs)
- **Total**: ~40 minutes

Let's do this! 🎉
