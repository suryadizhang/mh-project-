# Visual Guide: Finding Your Stripe Webhook Secret

## 🎯 You're Almost There!

Based on what you're seeing, here's the exact path:

---

## Current Screen: Webhooks Overview

You're seeing:
- "Trigger reactions in your integration with Stripe events"
- "Add destination" button
- "Test with a local listener"

### ✅ What to Do Next:

---

## Step 1: Click "Add Endpoint" or "Add Destination"

Look for one of these buttons on the page:
- **"Add endpoint"** (most common)
- **"Add destination"** (newer interface)

**Click it!**

---

## Step 2: Fill in the Form

You'll see a form with these fields:

### Endpoint URL:
```
http://localhost:8000/api/stripe/webhook
```
*(For local development)*

Or if you have a production domain:
```
https://yourdomain.com/api/stripe/webhook
```

### Description (optional):
```
MyHibachi Payment Notifications
```

### Version:
- Leave as default (usually latest API version)

### Events to send:
Click **"Select events"** or **"+ Select events"**

Then select these:
- ✅ `payment_intent.succeeded`
- ✅ `payment_intent.payment_failed`
- ✅ `payment_intent.canceled`
- ✅ `checkout.session.completed`
- ✅ `customer.created`
- ✅ `charge.refunded`

*(Or select "Send all events" for development)*

### Click "Add endpoint"

---

## Step 3: Get Your Webhook Secret

After creating the endpoint, you'll be taken to the endpoint details page.

### Look for:
**"Signing secret"** section

You'll see:
```
Signing secret
whsec_••••••••••••••••••••••••••••
[Click to reveal]  or  [Reveal]
```

### Click "Reveal" or "Click to reveal"

You'll see something like:
```
whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890abcd
```

**Copy this entire string!**

---

## Step 4: Add to Your .env File

Open: `apps/backend/.env`

Find this line:
```bash
STRIPE_WEBHOOK_SECRET=whsec_test_example
```

Replace with your actual secret:
```bash
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890abcd
```

**Save the file!**

---

## 🔍 Alternative: If You Already Created an Endpoint

If you already have an endpoint listed:

1. Look for a list of endpoints on the webhooks page
2. Click on the endpoint URL (it will look like a link)
3. Scroll down to **"Signing secret"** section
4. Click **"Reveal"**
5. Copy the `whsec_...` value

---

## 📍 Visual Reference

### The URL Path Should Be:
```
https://dashboard.stripe.com/test/webhooks
```

### Make Sure You're In:
- ✅ **TEST MODE** (toggle top-right should say "Viewing test data")
- ✅ **Developers** → **Webhooks** section

---

## ⚠️ About the Code You Showed Me

The code snippet you showed:
```javascript
const stripe = require('stripe')('{{TEST_SECRET_KEY}}');
```

This is **NOT** the webhook secret. This is showing you:
- How to create a PaymentIntent (for Connect/platform accounts)
- The `{{TEST_SECRET_KEY}}` is your Stripe secret key (you already have this!)

**You need a different secret - the webhook signing secret!**

---

## 🆘 Still Can't Find It?

### Option 1: Direct Link (for test mode)
Try this direct link:
```
https://dashboard.stripe.com/test/webhooks/create
```

### Option 2: Step-by-Step Navigation
1. Go to: https://dashboard.stripe.com/test
2. Click **"Developers"** in top menu
3. Click **"Webhooks"** in left sidebar
4. Click **"Add endpoint"** button (top-right or center)

### Option 3: Check Existing Endpoints
If you see a list of endpoints:
- Click on any existing endpoint
- Scroll to "Signing secret"
- Click "Reveal"

---

## 🎯 Quick Test After Setup

After you add the webhook secret to `.env`, test it:

```bash
cd apps/backend
python -c "from src.core.config import get_settings; s = get_settings(); print(f'Webhook secret: {s.STRIPE_WEBHOOK_SECRET[:20]}...')"
```

Should show:
```
Webhook secret: whsec_12345678901234...
```

---

## 📞 What If I Don't Want to Set Up Webhooks Yet?

For **local development only**, you can use a placeholder temporarily:

In `apps/backend/.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_local_development_placeholder_minimum_length
```

**But for production or testing payment flows, you MUST use a real webhook secret!**

---

**Next Step:** Click "Add endpoint" on the Stripe dashboard and follow the form! 🚀
