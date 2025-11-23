# 🚀 QUICK CHANNEL ACTIVATION GUIDE

**Goal**: Get 4 channels live in 2 hours

---

## ✅ STEP 1: Configure Email (15 minutes)

### A. IONOS SMTP (Customer Emails)

Add to `.env` or environment:

```bash
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USERNAME=cs@myhibachichef.com
SMTP_PASSWORD=<YOUR_IONOS_PASSWORD>
EMAIL_FROM_ADDRESS=cs@myhibachichef.com
EMAIL_FROM_NAME=MyHibachi Chef
FRONTEND_URL=https://yourdomain.com
```

### B. Gmail SMTP (Internal Admin Emails)

```bash
GMAIL_USERNAME=myhibachichef@gmail.com
GMAIL_APP_PASSWORD=<YOUR_GMAIL_APP_PASSWORD>
```

**How to get Gmail App Password**:
1. Go to Google Account Settings
2. Security → 2-Step Verification (enable if not already)
3. App Passwords → Generate new password
4. Copy 16-character password

### C. Test Email

```bash
# From backend directory
cd apps/backend/src
python -c "
from services.email_service import email_service
success = email_service.send_welcome_email(
    'test@example.com',
    'Test User'
)
print(f'Email test: {'✅ PASS' if success else '❌ FAIL'}')
"
```

✅ Email LIVE!

---

## ✅ STEP 2: Verify SMS (Already Working)

SMS should already be working with RingCentral. Verify:

```bash
# Check RingCentral credentials
echo $RINGCENTRAL_CLIENT_ID
echo $RINGCENTRAL_CLIENT_SECRET
echo $RINGCENTRAL_JWT_TOKEN
```

If missing, add:

```bash
RINGCENTRAL_CLIENT_ID=<your-client-id>
RINGCENTRAL_CLIENT_SECRET=<your-client-secret>
RINGCENTRAL_SERVER=https://platform.ringcentral.com
RINGCENTRAL_JWT_TOKEN=<your-jwt-token>
```

✅ SMS already LIVE!

---

## ✅ STEP 3: Setup Meta (Instagram + Facebook) (30 minutes)

### A. Create Meta App

1. Go to https://developers.facebook.com/
2. **My Apps** → **Create App**
3. Choose **Business** type
4. Fill in app details:
   - App Name: "MyHibachi AI Assistant"
   - Contact Email: myhibachichef@gmail.com
   - Business Account: (create if needed)
5. Click **Create App**

### B. Configure Instagram

1. In your app, go to **Add Products**
2. Add **Instagram** (click **Set Up**)
3. **Basic Settings** → Get:
   - App ID
   - App Secret
4. **Instagram Settings**:
   - Add Instagram Business Account
   - Link your Instagram account
   - Get Instagram Business Account ID

### C. Configure Facebook Messenger

1. In your app, go to **Add Products**
2. Add **Messenger** (click **Set Up**)
3. **Settings** → **Access Tokens**:
   - Connect your Facebook Page
   - Generate Page Access Token
   - Copy token (save securely)

### D. Setup Webhooks

1. Go to **Webhooks** in app settings
2. Click **Setup Webhooks** for Instagram:
   - **Callback URL**: `https://yourdomain.com/api/v1/webhooks/instagram`
   - **Verify Token**: (generate random string, save it)
   - Subscribe to: `messages`, `messaging_postbacks`, `message_echoes`
3. Click **Setup Webhooks** for Messenger:
   - **Callback URL**: `https://yourdomain.com/api/v1/webhooks/facebook`
   - **Verify Token**: (same or different)
   - Subscribe to: `messages`, `messaging_postbacks`, `message_echoes`

### E. Add to Environment

```bash
# Meta/Facebook/Instagram
META_APP_ID=<your-app-id>
META_APP_SECRET=<your-app-secret>
META_ACCESS_TOKEN=<your-page-access-token>
INSTAGRAM_BUSINESS_ACCOUNT_ID=<your-instagram-id>
FACEBOOK_PAGE_ID=<your-facebook-page-id>
INSTAGRAM_VERIFY_TOKEN=<your-verify-token>
FACEBOOK_VERIFY_TOKEN=<your-verify-token>
```

### F. Test Webhooks

1. Send a test message to your Instagram DM
2. Check backend logs for webhook received
3. Send a test message to your Facebook Page
4. Check logs again

✅ Instagram + Facebook LIVE!

---

## ✅ STEP 4: Test All Channels (30 minutes)

### A. Email Test

```bash
curl -X POST http://localhost:8000/api/v1/test/email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test"
  }'
```

### B. SMS Test

```bash
curl -X POST http://localhost:8000/api/v1/test/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+19167408768",
    "message": "Test SMS from MyHibachi"
  }'
```

### C. Instagram Test

1. Open Instagram app
2. Send DM to your business account: "Hi, I'd like to book a party"
3. Check backend logs
4. Verify AI response

### D. Facebook Test

1. Open Facebook Messenger
2. Send message to your business page: "What's your menu?"
3. Check backend logs
4. Verify AI response

---

## ✅ STEP 5: Monitor & Verify (15 minutes)

### Check Dashboard

```bash
# Open monitoring dashboard
curl http://localhost:8000/api/v1/monitoring/dashboard/
```

### Check AI Usage

```bash
# Check AI metrics
curl http://localhost:8000/api/v1/monitoring/dashboard/ | jq '.ai_metrics'
```

### Check Logs

```bash
# Real-time logs
tail -f logs/app.log | grep -E "email|sms|instagram|facebook"
```

---

## 🎉 DONE!

**You now have 4 channels LIVE:**
- ✅ Email (via IONOS + Gmail SMTP)
- ✅ SMS (via RingCentral)
- ✅ Instagram DM (via Meta Graph API)
- ✅ Facebook Messenger (via Meta Graph API)

**Total Time**: ~2 hours

**Next Steps**:
1. Monitor for 24-48 hours
2. Gather feedback
3. Start building voice AI for phone calls (7-10 days)

---

## 🆘 TROUBLESHOOTING

### Email Not Sending

**Check**:
```bash
# Test SMTP connection
python -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.ionos.com', 587)
    server.starttls()
    server.login('cs@myhibachichef.com', '<password>')
    print('✅ SMTP connection OK')
except Exception as e:
    print(f'❌ SMTP error: {e}')
"
```

### Instagram/Facebook Webhook Not Receiving

**Check**:
1. Webhook URL is HTTPS (not HTTP)
2. Verify token matches in app settings
3. Your domain is publicly accessible
4. Check webhook subscriptions in app

### SMS Not Working

**Check**:
```bash
# Test RingCentral auth
python -c "
from services.ringcentral_service import RingCentralService
rc = RingCentralService()
print(f'✅ RingCentral initialized: {rc.platform}')
"
```

---

## 📊 MONITORING

### Check Channel Health

```bash
# Email health
curl http://localhost:8000/api/v1/health/email

# SMS health
curl http://localhost:8000/api/v1/health/sms

# Social media health
curl http://localhost:8000/api/v1/health/social
```

### Check AI Performance

```bash
# Get dashboard summary
curl http://localhost:8000/api/v1/monitoring/dashboard/ | jq '{
  email: .ai_metrics.channels.email,
  sms: .ai_metrics.channels.sms,
  instagram: .ai_metrics.channels.instagram,
  facebook: .ai_metrics.channels.facebook
}'
```

---

## 🎯 SUCCESS METRICS

After 24 hours, you should see:
- ✅ Emails sending automatically
- ✅ SMS conversations flowing
- ✅ Instagram DMs being answered
- ✅ Facebook messages being handled
- ✅ AI cost < $5/day
- ✅ Response time < 30 seconds
- ✅ Customer satisfaction > 85%

**Congratulations! You're now omnichannel! 🚀**
