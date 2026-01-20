# Webhook Configuration for Production Deployment

## 📋 Overview

This document provides step-by-step instructions for configuring webhooks in production after deploying your My Hibachi CRM application.

**Status:** ✅ All API integrations tested and verified (8/8 passing)  
**Date:** October 27, 2025  
**Prerequisites:** Production domain and backend deployed

---

## 🔗 Webhooks to Configure

| Service | Purpose | Priority |
|---------|---------|----------|
| **Stripe** | Payment events, subscription updates | 🔴 CRITICAL |
| **Meta (Facebook/Instagram)** | Customer messages, comments | 🟡 HIGH |
| **RingCentral** | SMS notifications, voicemail | 🟢 MEDIUM |

---

## 1️⃣ Stripe Webhook Configuration

### Purpose
- Receive real-time payment notifications
- Handle subscription lifecycle events
- Process refunds and disputes
- Update order status automatically

### Production Setup

#### Step 1: Get Your Production URL
```
Your production webhook URL will be:
https://yourdomain.com/api/v1/webhooks/stripe

Example: https://mhapi.mysticdatanode.net/api/v1/webhooks/stripe
```

#### Step 2: Configure in Stripe Dashboard
1. Go to: https://dashboard.stripe.com/webhooks
2. Click **"Add endpoint"**
3. **Endpoint URL:** `https://yourdomain.com/api/v1/webhooks/stripe`
4. **Description:** `My Hibachi Production Webhooks`
5. **Events to send:** Select these 14 events:

**Payment Events:**
- ✅ `payment_intent.succeeded` - Payment completed
- ✅ `payment_intent.payment_failed` - Payment failed
- ✅ `payment_intent.canceled` - Payment canceled
- ✅ `payment_intent.created` - Payment initiated

**Checkout Events:**
- ✅ `checkout.session.completed` - Checkout completed
- ✅ `checkout.session.expired` - Checkout session expired

**Charge Events:**
- ✅ `charge.succeeded` - Charge successful
- ✅ `charge.failed` - Charge failed
- ✅ `charge.refunded` - Refund processed

**Customer Events:**
- ✅ `customer.created` - New customer
- ✅ `customer.updated` - Customer info changed
- ✅ `customer.deleted` - Customer deleted

**Refund Events:**
- ✅ `charge.refund.created` - Refund initiated
- ✅ `charge.refund.updated` - Refund status changed

6. Click **"Add endpoint"**
7. Click **"Reveal signing secret"**
8. Copy the signing secret (starts with `whsec_...`)

#### Step 3: Update Production Environment Variables
```bash
# In your production .env file:
STRIPE_WEBHOOK_SECRET=whsec_YOUR_PRODUCTION_SECRET_HERE
```

#### Step 4: Test the Webhook
1. In Stripe dashboard, go to your webhook endpoint
2. Click **"Send test webhook"**
3. Select `payment_intent.succeeded`
4. Check your backend logs for successful processing

### Webhook Handler Code Location
```
apps/backend/src/api/v1/endpoints/routers/webhooks.py
Function: stripe_webhook()
```

---

## 2️⃣ Meta (Facebook/Instagram) Webhook Configuration

### Purpose
- Receive customer messages in real-time
- Auto-reply with AI-powered responses
- Handle comments on posts
- Get Instagram mentions and DMs

### Production Setup

#### Step 1: Get Your Production URL
```
Your production webhook URL will be:
https://yourdomain.com/api/v1/webhooks/meta

Example: https://mhapi.mysticdatanode.net/api/v1/webhooks/meta
```

#### Step 2: Configure in Meta Developer Console
1. Go to: https://developers.facebook.com/apps/YOUR_APP_ID/webhooks/
2. Click **"Edit Subscription"** for your Page
3. **Callback URL:** `https://yourdomain.com/api/v1/webhooks/meta`
4. **Verify Token:** `YOUR_VERIFY_TOKEN` (from your .env)
5. Click **"Verify and Save"**

#### Step 3: Subscribe to Webhook Fields

**For Facebook Page:**
- ✅ `messages` - Customer messages
- ✅ `messaging_postbacks` - Button clicks
- ✅ `message_echoes` - Sent messages
- ✅ `feed` - Page posts and comments

**For Instagram:**
- ✅ `messages` - Instagram DMs
- ✅ `comments` - Post comments
- ✅ `mentions` - Story mentions

#### Step 4: Environment Variables (Already Set)
```bash
META_APP_ID=YOUR_META_APP_ID
META_APP_SECRET=YOUR_META_APP_SECRET
META_PAGE_ACCESS_TOKEN=YOUR_PAGE_ACCESS_TOKEN
META_VERIFY_TOKEN=YOUR_VERIFY_TOKEN
META_PAGE_ID=YOUR_PAGE_ID
META_INSTAGRAM_ID=YOUR_INSTAGRAM_ID
```

#### Step 5: Test the Webhook
1. Send a test message to your Facebook Page
2. Check backend logs for received webhook event
3. Verify AI auto-reply is sent

### Webhook Handler Code Location
```
apps/backend/src/api/ai/endpoints/routers/webhooks.py
Function: meta_webhook()
```

---

## 3️⃣ RingCentral Webhook Configuration (Optional - Programmatic)

### Purpose
- Receive SMS notifications
- Get voicemail transcriptions
- Track call events
- Monitor fax status

### Production Setup

RingCentral webhooks are created **programmatically** via API (no dashboard setup needed).

#### Step 1: Create Webhook Subscription (Code Example)

```python
# This will be done automatically by your backend on startup
# File: apps/backend/src/services/ringcentral_service.py

from ringcentral import SDK

# Initialize SDK
rcsdk = SDK(
    client_id=os.getenv('RC_CLIENT_ID'),
    client_secret=os.getenv('RC_CLIENT_SECRET'),
    server='https://platform.ringcentral.com'
)

# Login
platform = rcsdk.platform()
platform.login(
    jwt=os.getenv('RC_JWT_TOKEN')
)

# Create webhook subscription
webhook_url = 'https://yourdomain.com/api/v1/webhooks/ringcentral'

response = platform.post('/restapi/v1.0/subscription', {
    'eventFilters': [
        '/restapi/v1.0/account/~/extension/~/message-store',  # SMS/MMS
        '/restapi/v1.0/account/~/extension/~/presence',        # Status
    ],
    'deliveryMode': {
        'transportType': 'WebHook',
        'address': webhook_url
    }
})

print(f"Webhook created: {response.json()['id']}")
```

#### Step 2: Webhook Endpoint (Already Implemented)
```
URL: https://yourdomain.com/api/v1/webhooks/ringcentral
Handler: apps/backend/src/api/v1/endpoints/routers/webhooks.py
Function: ringcentral_webhook()
```

#### Step 3: Environment Variables (Already Set)
```bash
RC_CLIENT_ID=3ADYc6Nv8qxeddtHygnfIK
RC_CLIENT_SECRET=V665HVqP...54Cy
RC_JWT_TOKEN=your_jwt_token_here
RC_USERNAME=suryadizhang.chef@gmail.com
RC_EXTENSION=101
RC_SMS_FROM=+19167408768
```

---

## 🔒 Security Best Practices

### 1. Webhook Signature Verification

**All webhook handlers MUST verify signatures:**

#### Stripe
```python
# Verify Stripe webhook signature
stripe.Webhook.construct_event(
    payload=body,
    sig_header=signature,
    secret=STRIPE_WEBHOOK_SECRET
)
```

#### Meta (Facebook/Instagram)
```python
# Verify Meta webhook signature
import hmac
import hashlib

def verify_meta_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        META_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f'sha256={expected}', signature)
```

### 2. HTTPS Only
- ✅ All webhooks MUST use HTTPS in production
- ❌ Never use HTTP for webhooks (security risk)

### 3. IP Whitelisting (Optional)

**Stripe IP Ranges:**
```
3.18.12.63/32
3.130.192.231/32
13.235.14.237/32
13.235.122.149/32
18.211.135.69/32
... (full list in Stripe docs)
```

**Meta IP Ranges:**
```
31.13.24.0/21
31.13.64.0/18
66.220.144.0/20
69.63.176.0/20
... (full list in Meta docs)
```

### 4. Rate Limiting
```python
# Implement rate limiting per webhook source
# Example: Max 100 requests per minute per IP
```

### 5. Idempotency
```python
# Store processed webhook IDs to prevent duplicate processing
processed_webhooks = set()

def process_webhook(webhook_id: str):
    if webhook_id in processed_webhooks:
        return {"status": "already_processed"}
    
    # Process webhook...
    processed_webhooks.add(webhook_id)
```

---

## 📊 Monitoring & Logging

### What to Monitor

1. **Webhook Success Rate**
   - Track successful vs failed webhook deliveries
   - Alert if success rate drops below 95%

2. **Response Time**
   - Webhook handlers should respond within 5 seconds
   - Stripe requires response within 30 seconds

3. **Error Rates**
   - Log all webhook processing errors
   - Alert on unusual error spikes

### Logging Example
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    try:
        # Process webhook
        logger.info(f"Stripe webhook received: {event_type}")
        
    except stripe.error.SignatureVerificationError:
        logger.error("Stripe signature verification failed")
        raise HTTPException(status_code=400)
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500)
```

---

## 🧪 Testing Webhooks in Production

### Stripe Test Events
```bash
# Using Stripe CLI
stripe listen --forward-to https://yourdomain.com/api/v1/webhooks/stripe

# Trigger test event
stripe trigger payment_intent.succeeded
```

### Meta Test Messages
1. Go to your Facebook Page
2. Send a test message from another account
3. Verify webhook receives the message
4. Check AI auto-reply is sent

### RingCentral Test SMS
```bash
# Send test SMS to your RC number
# Verify webhook receives SMS event
# Check backend processing logs
```

---

## 🚨 Troubleshooting

### Webhook Not Receiving Events

**Check 1: URL Accessibility**
```bash
# Test if webhook URL is publicly accessible
curl https://yourdomain.com/api/v1/webhooks/stripe

# Should return: 405 Method Not Allowed (GET not allowed, only POST)
```

**Check 2: SSL Certificate**
```bash
# Verify SSL certificate is valid
curl -v https://yourdomain.com/api/v1/webhooks/stripe
```

**Check 3: Firewall Rules**
```bash
# Ensure port 443 (HTTPS) is open
# Check cloud provider firewall settings
```

### Signature Verification Fails

**Check 1: Correct Secret**
```bash
# Verify webhook secret matches dashboard
echo $STRIPE_WEBHOOK_SECRET
```

**Check 2: Raw Body**
```python
# Ensure you're using raw request body, not parsed JSON
body = await request.body()  # ✅ Correct
body = await request.json()  # ❌ Wrong - signature will fail
```

### Events Not Processing

**Check 1: Backend Logs**
```bash
# Check application logs for errors
tail -f /var/log/myhibachi/backend.log
```

**Check 2: Database Connection**
```bash
# Verify database is accessible
# Check connection pool not exhausted
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] All environment variables set in production
- [ ] HTTPS certificate installed and valid
- [ ] Backend deployed and running
- [ ] Database migrations completed
- [ ] Firewall rules configured

### Webhook Configuration
- [ ] Stripe webhook URL configured
- [ ] Stripe webhook secret updated in .env
- [ ] Stripe test event sent successfully
- [ ] Meta webhook URL verified
- [ ] Meta webhook fields subscribed
- [ ] Meta test message sent successfully
- [ ] RingCentral webhook subscription created (if needed)

### Post-Deployment
- [ ] Monitor webhook success rate (24 hours)
- [ ] Check error logs for issues
- [ ] Verify customer messages receive auto-replies
- [ ] Test payment flow end-to-end
- [ ] Document any issues encountered

---

## 🔗 Quick Reference Links

### Stripe
- Dashboard: https://dashboard.stripe.com/webhooks
- Webhook Documentation: https://stripe.com/docs/webhooks
- Test Events: https://stripe.com/docs/webhooks/test

### Meta (Facebook/Instagram)
- Developer Console: https://developers.facebook.com/apps/YOUR_APP_ID/
- Webhook Documentation: https://developers.facebook.com/docs/graph-api/webhooks
- Test Webhooks: https://developers.facebook.com/tools/webhooks/

### RingCentral
- Developer Console: https://developers.ringcentral.com/
- Webhook Documentation: https://developers.ringcentral.com/guide/notifications/webhooks
- API Reference: https://developers.ringcentral.com/api-reference

---

## 📞 Support

If you encounter issues during webhook configuration:

1. **Check backend logs** for detailed error messages
2. **Review webhook dashboard** in each service (Stripe, Meta, RingCentral)
3. **Test locally first** using tunnel (ngrok/cloudflare) before production
4. **Verify signatures** are being validated correctly
5. **Monitor response times** - webhooks should respond quickly

---

**Last Updated:** October 27, 2025  
**Status:** Ready for Production Deployment ✅
