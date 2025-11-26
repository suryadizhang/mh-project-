# Resend Webhook Setup Guide

## 🎯 Quick Access

**Admin Panel:** http://localhost:3001 (running now) **Email Page:**
http://localhost:3001/emails **Resend Dashboard:**
https://resend.com/webhooks **Production Webhook URL:**
`https://api.myhibachichef.com/api/admin/emails/webhooks/resend`

---

## 📋 Step-by-Step Setup

### 1. Login to Resend Dashboard

1. Go to https://resend.com/login
2. Login with My Hibachi credentials
3. Navigate to **Settings** → **Webhooks**

### 2. Create Webhook

Click **"Add Webhook"** and configure:

**Webhook URL:**

```
https://api.myhibachichef.com/api/admin/emails/webhooks/resend
```

**Events to Subscribe:** (Select ALL)

- ✅ `email.sent` - Email sent successfully
- ✅ `email.delivered` - Email delivered to recipient
- ✅ `email.delivery_delayed` - Temporary delivery failure
- ✅ `email.bounced` - Permanent delivery failure (invalid email)
- ✅ `email.complained` - Recipient marked as spam
- ✅ `email.opened` - Email opened (tracking enabled)
- ✅ `email.clicked` - Link clicked in email

**Webhook Signing Secret:**

- Copy the signing secret provided
- Add to `.env` file: `RESEND_WEBHOOK_SECRET=whsec_...`

### 3. Test Webhook (Local Development)

For local testing, use ngrok to expose localhost:

```bash
# Install ngrok if not already installed
# Download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add to Resend webhook: https://abc123.ngrok.io/api/admin/emails/webhooks/resend
```

### 4. Verify Webhook

**Send Test Email:**

1. Go to http://localhost:3001/emails
2. Select a customer email
3. Send a reply
4. Check backend logs for webhook events:

```bash
# Backend logs should show:
📧 Resend webhook received: email.sent
✅ Email sent: re_abc123xyz
📧 Resend webhook received: email.delivered
📬 Email delivered to customer@example.com: re_abc123xyz
```

**Test Webhook Manually:**

```bash
# Send test POST request
curl -X POST http://localhost:8000/api/admin/emails/webhooks/resend \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email.delivered",
    "created_at": "2025-11-24T12:00:00Z",
    "data": {
      "email_id": "test-123",
      "from": "cs@myhibachichef.com",
      "to": ["customer@example.com"],
      "subject": "Test Email"
    }
  }'
```

---

## 🔒 Security: Webhook Signature Verification (TODO)

**Current State:** Webhook accepts all requests (not secure for
production)

**Recommended:** Add signature verification

```python
# apps/backend/src/routers/v1/admin_emails.py

import hmac
import hashlib

@router.post("/webhooks/resend")
async def resend_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
):
    # Get webhook secret from environment
    webhook_secret = settings.RESEND_WEBHOOK_SECRET

    if not webhook_secret:
        logger.warning("⚠️ Webhook secret not configured")
        return {"success": False, "error": "Webhook secret missing"}

    # Get raw body
    body = await request.body()
    payload = body.decode()

    # Verify signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        f"{svix_id}.{svix_timestamp}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()

    if svix_signature != expected_signature:
        logger.error("❌ Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook...
```

**Add to `.env`:**

```bash
RESEND_WEBHOOK_SECRET=whsec_your_secret_here
```

---

## 📊 Webhook Events Reference

### email.sent

**Triggered:** Email successfully sent from Resend **Action:** Log
confirmation, update status to "sent"

### email.delivered

**Triggered:** Email delivered to recipient's inbox **Action:** Log
delivery, update status to "delivered"

### email.bounced

**Triggered:** Email bounced (permanent failure) **Reasons:**

- Invalid email address
- Mailbox doesn't exist
- Domain doesn't exist

**Action:**

- Log error
- Mark email as bounced
- Add to suppression list
- Notify admin via WhatsApp

### email.delivery_delayed

**Triggered:** Temporary delivery failure **Reasons:**

- Recipient's server temporarily down
- Mailbox full
- Greylisting

**Action:** Log warning, Resend will retry automatically

### email.complained

**Triggered:** Recipient marked email as spam **Action:**

- Log complaint
- Add to suppression list
- Review email content
- Notify admin

### email.opened

**Triggered:** Recipient opened email (tracking must be enabled)
**Note:** Not 100% accurate (image blocking, etc.) **Action:** Track
open metrics

### email.clicked

**Triggered:** Recipient clicked link in email **Action:** Track click
metrics, link engagement

---

## 🧪 Testing Checklist

- [ ] Send email via admin panel
- [ ] Check backend logs for `email.sent` webhook
- [ ] Check backend logs for `email.delivered` webhook
- [ ] Send to invalid email address
- [ ] Check backend logs for `email.bounced` webhook
- [ ] Review Resend dashboard for event history
- [ ] Verify webhook signature (once implemented)

---

## 🚀 Production Deployment

### Backend (VPS/Plesk)

1. **Update `.env` on production server:**

```bash
# SSH into server
ssh user@api.myhibachichef.com

# Edit .env
nano /var/www/myhibachi-backend/.env

# Add:
RESEND_WEBHOOK_SECRET=whsec_production_secret_here
```

2. **Restart backend service:**

```bash
sudo systemctl restart myhibachi-api
```

3. **Verify webhook endpoint is accessible:**

```bash
# Test from external network
curl https://api.myhibachichef.com/api/admin/emails/webhooks/resend \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type":"email.sent","created_at":"2025-11-24T12:00:00Z","data":{}}'

# Should return:
# {"success":true,"event_type":"email.sent","processed_at":"..."}
```

### Resend Dashboard

1. Update webhook URL to production:

   ```
   https://api.myhibachichef.com/api/admin/emails/webhooks/resend
   ```

2. Test webhook with Resend's test feature

3. Monitor webhook logs in Resend dashboard

---

## 📝 Monitoring & Debugging

### Backend Logs

```bash
# Watch logs in real-time
tail -f /var/log/myhibachi-api/app.log | grep webhook

# Search for webhook events
grep "Resend webhook" /var/log/myhibachi-api/app.log
```

### Resend Dashboard

1. Go to **Webhooks** → Your webhook
2. Click **"Recent Deliveries"**
3. View request/response for each event
4. Check for failed deliveries

### Common Issues

**Webhook not receiving events:**

- Verify URL is correct
- Check firewall allows POST requests
- Ensure backend is running
- Check Resend dashboard for delivery failures

**401 Unauthorized:**

- Signature verification failing
- Check `RESEND_WEBHOOK_SECRET` is correct
- Verify signature algorithm matches Resend's

**500 Internal Server Error:**

- Check backend logs for Python errors
- Verify JSON parsing works
- Test with curl first

---

## 🎯 Next Steps

1. ✅ **Setup webhook in Resend dashboard** (5 mins)
2. ✅ **Test with ngrok locally** (10 mins)
3. ⏳ **Implement signature verification** (30 mins)
4. ⏳ **Deploy to production** (15 mins)
5. ⏳ **Store webhook events in database** (2 hours)
6. ⏳ **Create webhook dashboard UI** (3 hours)

---

## 📊 Future Enhancements

### Email Delivery Dashboard

- Track delivery rates
- Monitor bounce rates
- View open/click analytics
- Export reports

### Database Storage

```sql
CREATE TABLE email_webhook_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    email_id VARCHAR(255) NOT NULL,
    recipient_email VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    data JSONB,
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_webhook_events_email_id ON email_webhook_events(email_id);
CREATE INDEX idx_webhook_events_type ON email_webhook_events(event_type);
```

### Alert System

- Slack/Discord notifications for bounces
- Email admin when bounce rate > 5%
- WhatsApp alert for spam complaints

---

## ✅ Admin Panel Access

**Local Development:**

- URL: http://localhost:3001
- Email Page: http://localhost:3001/emails
- Status: ✅ Running (port 3001)

**Production:**

- URL: https://admin.myhibachichef.com
- Email Page: https://admin.myhibachichef.com/emails
- Status: ⏳ Pending deployment

---

## 🔗 Resources

- Resend Webhooks Docs:
  https://resend.com/docs/dashboard/webhooks/introduction
- Resend API Reference:
  https://resend.com/docs/api-reference/webhooks/webhook-object
- Ngrok Download: https://ngrok.com/download
- Our Implementation: `apps/backend/src/routers/v1/admin_emails.py`
  (line 628)
