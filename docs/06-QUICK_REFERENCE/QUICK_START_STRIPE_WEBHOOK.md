# Quick Start: Get Stripe Webhook Secret (5 Minutes)

## 🎯 This is the ONLY key you need right now!

All other keys are optional. Start here:

---

## Step 1: Login to Stripe (1 minute)

1. Open: **https://dashboard.stripe.com/login**
2. Login with your Stripe account
3. ✅ Make sure you're in **TEST MODE** (toggle top-right)

---

## Step 2: Go to Webhooks (1 minute)

1. Click **Developers** (top menu)
2. Click **Webhooks** (left sidebar)
3. Click **Add endpoint** button

---

## Step 3: Configure Webhook (2 minutes)

**Endpoint URL:**

```
http://localhost:8000/api/stripe/webhook
```

**Description:**

```
MyHibachi Payment Notifications
```

**Events to select:** (click "Select events" button)

- ✅ `payment_intent.succeeded`
- ✅ `payment_intent.payment_failed`
- ✅ `payment_intent.canceled`
- ✅ `checkout.session.completed`

**Click:** Add endpoint

---

## Step 4: Get Your Secret (1 minute)

1. Click on the webhook you just created
2. Find **Signing secret** section
3. Click **Reveal**
4. Copy the value starting with `whsec_...`

---

## Step 5: Update .env File (30 seconds)

Open: `apps/backend/.env`

Find this line:

```bash
STRIPE_WEBHOOK_SECRET=whsec_test_example
```

Replace with your secret:

```bash
STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET_HERE
```

**Save the file!**

---

## ✅ DONE! Test Your Backend:

```bash
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Your payment system is now fully functional! 🎉

---

## What About Other APIs?

| Service         | Required?  | When to Get It                        |
| --------------- | ---------- | ------------------------------------- |
| Stripe Webhook  | ✅ **YES** | **Now** (5 min)                       |
| RingCentral SMS | ❌ No      | Only if you want SMS (you have email) |
| Plaid Banking   | ❌ No      | Only if you need bank verification    |
| Meta/Facebook   | ❌ No      | Only if you want social media         |
| Google Business | ❌ No      | Nice to have for reviews              |

**You already have these working:**

- ✅ OpenAI (AI features)
- ✅ IONOS Email (notifications)
- ✅ Cloudinary (image uploads)
- ✅ Stripe Payments (just need webhook)

---

## 📞 Having Trouble?

### Can't find the webhook secret?

- Make sure you clicked on the webhook endpoint (not just viewing the
  list)
- Look for "Signing secret" section
- Click "Reveal" to see it

### Not sure if you're in test mode?

- Look at top-right corner of Stripe dashboard
- Should say "Viewing test data"
- If it says "Viewing live data", click it to toggle

### Backend still won't start?

Run this to check your config:

```bash
cd apps/backend
python -c "from src.core.config import get_settings; s = get_settings(); print('Config OK!')"
```

---

**Start with just the Stripe webhook - you can add other APIs later if
needed!** 🚀
