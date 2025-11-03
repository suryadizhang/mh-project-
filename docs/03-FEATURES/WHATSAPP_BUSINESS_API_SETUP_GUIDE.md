# 📱 WhatsApp Business API Complete Setup Guide

## Overview

WhatsApp Business API provides official, reliable integration for sending notifications to customers. This guide covers complete setup for My Hibachi Chef.

---

## Part 1: WhatsApp Business API Setup (Official)

### Option A: Meta WhatsApp Business Platform (Recommended)

#### Prerequisites:
- Facebook Business Manager account
- Verified business
- Phone number (not currently using WhatsApp)
- Website with SSL certificate

#### Step-by-Step Setup:

##### 1. Create Facebook Business Manager Account
1. Go to https://business.facebook.com
2. Click "Create Account"
3. Enter business name: "My Hibachi Chef"
4. Enter your name and business email: cs@myhibachichef.com
5. Verify email

##### 2. Add WhatsApp Business Account
1. Go to Business Settings → Accounts → WhatsApp Accounts
2. Click "Add" → "Create a WhatsApp Business Account"
3. Business name: "My Hibachi Chef"
4. Business category: "Restaurant"
5. Business description: "Professional hibachi catering service"
6. Business address: 47481 Towhee Street, Fremont, CA 94539

##### 3. Add Phone Number
1. Click "Add phone number"
2. Choose phone number type:
   - **Option 1:** Get a new number from Meta ($Free with verification)
   - **Option 2:** Use existing number (must not be on WhatsApp Personal)
3. For this project, use: **+1 916 740 8768** (your business line)
4. Select country: United States
5. Verify via SMS or voice call

##### 4. Verify Your Business
1. Go to Business Settings → Business Info
2. Upload documents:
   - Business license or registration
   - Utility bill (if available)
   - Bank statement with business name
3. Wait 1-3 business days for verification

##### 5. Create WhatsApp Business App
1. Go to https://developers.facebook.com/apps
2. Click "Create App"
3. Select "Business" type
4. App name: "My Hibachi Notifications"
5. Contact email: cs@myhibachichef.com
6. Link to Business Manager account

##### 6. Configure WhatsApp Product
1. In your app, click "Add Product"
2. Select "WhatsApp" → "Set Up"
3. Link your WhatsApp Business Account
4. Select phone number
5. Copy credentials:
   - **Phone Number ID:** `{save_this}`
   - **WhatsApp Business Account ID:** `{save_this}`
   - **Access Token:** `{save_this}`

##### 7. Configure Webhooks
1. In WhatsApp settings, click "Configuration"
2. Edit webhook:
   - **Callback URL:** `https://yourdomain.com/webhooks/whatsapp`
   - **Verify Token:** `myhibachi-whatsapp-webhook-2025`
3. Subscribe to fields:
   - ✅ messages
   - ✅ message_status
   - ✅ message_echoes
4. Copy **Webhook Secret** for later

##### 8. Submit for Production Access
1. Current status: Development (10 conversations/day limit)
2. To go production (1,000 free conversations/month):
   - Complete business verification
   - Create message templates
   - Submit app for review (1-2 days)

---

### Option B: Twilio WhatsApp API (Faster Setup - 30 Minutes)

#### Why Choose Twilio:
- ✅ Faster setup (no business verification needed)
- ✅ Pay-as-you-go pricing
- ✅ Reliable infrastructure
- ✅ Good for testing/development
- ❌ Slightly higher cost than Meta direct

#### Pricing:
- **WhatsApp:** $0.005 per conversation (first 1,000 free)
- **SMS Fallback:** $0.0075 per message
- **Monthly minimum:** $0 (pay only for what you use)

#### Setup Steps:

##### 1. Create Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up with:
   - Email: cs@myhibachichef.com
   - Phone: +1 916 740 8768
3. Verify email and phone
4. Choose "Messaging" as primary product

##### 2. Get WhatsApp Sandbox (Immediate Testing)
1. Go to Console → Messaging → Try it out → Send a WhatsApp message
2. You'll see sandbox number: **+1 (415) 523-8886**
3. Join sandbox:
   - Save +1-415-523-8886 to your phone
   - Send: `join <your-sandbox-code>` (shown in console)
4. You can now send/receive test messages

##### 3. Upgrade to Production WhatsApp
1. Go to Console → Messaging → WhatsApp → Senders
2. Click "New Sender"
3. Select "Facebook Business Manager"
4. Options:
   - **Option A:** Request new number from Twilio ($2/month)
   - **Option B:** Link your WhatsApp Business Account (recommended)

##### 4. For Linking Existing WhatsApp Business:
1. Create WhatsApp Business Account (see Option A steps 1-6)
2. In Twilio Console, click "Link existing account"
3. Login to Facebook Business Manager
4. Grant permissions to Twilio
5. Select your business phone number
6. Complete setup (5-10 minutes)

##### 5. Get API Credentials
1. Go to Console → Account → API Keys & Tokens
2. Copy:
   - **Account SID:** `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token:** `your_auth_token`
3. Go to Messaging → WhatsApp → Senders
4. Copy:
   - **WhatsApp Sender:** `whatsapp:+14155238886` (sandbox) or your number

##### 6. Set Up Webhooks (Optional)
1. Console → Messaging → Settings → WhatsApp sandbox settings
2. Set webhook URL: `https://yourdomain.com/webhooks/twilio-whatsapp`
3. HTTP Method: POST
4. Status callback: Same URL + `/status`

---

## Part 2: Environment Configuration

### Add to `.env` file:

```env
# ==========================================
# WhatsApp Business API Configuration
# ==========================================

# Choose one: 'meta' or 'twilio'
WHATSAPP_PROVIDER=twilio

# ==========================================
# Meta WhatsApp Business Platform (Option A)
# ==========================================
META_WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
META_WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
META_WHATSAPP_ACCESS_TOKEN=your_access_token
META_WHATSAPP_WEBHOOK_SECRET=myhibachi-whatsapp-webhook-2025

# ==========================================
# Twilio WhatsApp API (Option B - Current)
# ==========================================
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_SMS_NUMBER=+19167408768
WHATSAPP_GROUP_WEBHOOK=

# ==========================================
# Notification Settings
# ==========================================
# Admin phone for all notifications
ADMIN_NOTIFICATION_PHONE=+19167408768

# Enable/disable notification types
NOTIFY_NEW_BOOKING=true
NOTIFY_EDIT_BOOKING=true
NOTIFY_CANCEL_BOOKING=true
NOTIFY_PAYMENT_RECEIVED=true
NOTIFY_REVIEW_RECEIVED=true
NOTIFY_COMPLAINT_RECEIVED=true

# Admin group chat (if using WhatsApp Web webhook)
WHATSAPP_ADMIN_GROUP_ID=

# Notification quiet hours (24-hour format)
NOTIFICATION_QUIET_START=22
NOTIFICATION_QUIET_END=8
```

---

## Part 3: Testing Without API (Local Development)

### Mock WhatsApp Service

I'll create a mock service that logs notifications locally without requiring API credentials.

---

## Part 4: Implementation Costs

### Meta WhatsApp Business Platform:
- **Setup:** Free
- **First 1,000 conversations/month:** Free
- **After 1,000:** $0.005-$0.009 per conversation (varies by country)
- **Business verification:** Free
- **Phone number:** Free (Meta-provided)

### Twilio WhatsApp API:
- **Setup:** Free
- **Phone number:** $2/month (optional, can use Meta number)
- **WhatsApp messages:** $0.005 per conversation
- **SMS fallback:** $0.0075 per message
- **No monthly minimum**

### Estimated Monthly Cost (100 notifications):
- **Meta:** $0 (within free tier)
- **Twilio:** $0.50 for WhatsApp + $0.75 for SMS fallback = **$1.25/month**

---

## Part 5: Recommended Approach

### For My Hibachi Chef:

**Phase 1 (Now): Development & Testing**
- ✅ Use Twilio Sandbox (free, instant)
- ✅ Test all notification types
- ✅ Verify message templates
- ✅ Timeline: 1-2 days

**Phase 2 (Week 2): Production Setup**
- ✅ Create Meta WhatsApp Business Account
- ✅ Verify business (1-3 days wait)
- ✅ Link to Twilio for easy management
- ✅ Timeline: 1 week

**Phase 3 (Week 3): Go Live**
- ✅ Switch from sandbox to production number
- ✅ Enable for all customers
- ✅ Monitor delivery and costs

---

## Part 6: Quick Start (Testing Today)

### 1. Sign up for Twilio (10 minutes)
```bash
# Go to: https://www.twilio.com/try-twilio
# Enter: cs@myhibachichef.com
# Phone: +19167408768
```

### 2. Get Sandbox Credentials (5 minutes)
```bash
# Console → Messaging → Try it out → WhatsApp
# Copy: Account SID, Auth Token, Sandbox number
```

### 3. Update `.env`
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 4. Join Sandbox
```bash
# 1. Save +1-415-523-8886 to your phone
# 2. Send WhatsApp: "join <your-code>"
# 3. Done! Can now receive notifications
```

### 5. Test Notification
```bash
cd apps/backend
python -c "
import asyncio
from services.whatsapp_notification_service import send_payment_notification

asyncio.run(send_payment_notification(
    phone_number='+19167408768',
    customer_name='Suryadi Zhang',
    amount=150.00,
    provider='Venmo',
    sender_name='Test Sender',
    match_score=175,
    booking_id=123
))
"
```

---

## Part 7: WhatsApp Message Templates (Required for Production)

### Template: New Booking Confirmation
```
Hello {{1}}! 🎉

Your hibachi booking is confirmed!

Date: {{2}}
Time: {{3}}
Guests: {{4}}
Location: {{5}}

Booking #{{6}}

We'll send payment instructions shortly.

Questions? Reply here or call +19167408768

- My Hibachi Chef Team
```

### Template: Payment Received
```
Payment Confirmed! ✅

Hi {{1}},

We've received your payment of ${{2}} via {{3}}.

Booking #{{4}} is now fully paid.

Looking forward to serving you on {{5}}!

- My Hibachi Chef Team
```

### Template: Event Reminder (24 hours before)
```
Reminder: Your Hibachi Event Tomorrow! 🔥

Hi {{1}},

Just a friendly reminder:

📅 Tomorrow at {{2}}
📍 {{3}}
👥 {{4}} guests

Our chef will arrive 30 minutes early to set up.

See you soon!
- My Hibachi Chef
```

### Template: Review Request (After event)
```
How was your hibachi experience? ⭐

Hi {{1}},

We hope you enjoyed your event!

Please share your feedback:
{{2}}

As a thank you, get 10% off your next booking!

- My Hibachi Chef Team
```

---

## Part 8: Next Steps

### Immediate (Today):
1. ✅ Sign up for Twilio (10 min)
2. ✅ Get sandbox credentials
3. ✅ Test with your phone
4. ✅ Verify notifications work

### This Week:
1. Create Facebook Business Manager
2. Add WhatsApp Business Account
3. Start business verification process
4. Create message templates

### Next Week:
1. Complete business verification
2. Link to Twilio (optional) or use Meta direct
3. Submit templates for approval
4. Go production!

---

## Part 9: Troubleshooting

### "Cannot send to this number"
- Number not in sandbox → Join sandbox first
- Number not opted in → Customer needs to reply "START"

### "Insufficient permissions"
- Check Access Token has messaging permissions
- Verify WhatsApp Business Account is active

### "Template not found"
- Template not approved yet → Use sandbox templates
- Template name mismatch → Check exact name

### "Webhook failed"
- Invalid URL → Check HTTPS and valid endpoint
- Wrong verify token → Match webhook settings

---

## Support

**Twilio Support:**
- Email: help@twilio.com
- Phone: +1 (888) 908-9547
- Docs: https://www.twilio.com/docs/whatsapp

**Meta Support:**
- Business Support: https://business.facebook.com/help
- Developer Docs: https://developers.facebook.com/docs/whatsapp

**My Implementation:**
- Check logs: `apps/backend/logs/app.log`
- Service file: `src/services/whatsapp_notification_service.py`

---

**Recommended Start:** Twilio Sandbox (10 minutes, free, test immediately)
**Production Goal:** Meta WhatsApp Business (1-2 weeks, free tier, official)
