# ✅ Quick Action Checklist - Get MyHibachi 100% Functional

**Target Time:** 20 minutes  
**Your Current Status:** 60% configured

---

## 🎯 What You Already Have ✅

- ✅ **Cloudinary** - FULLY WORKING (real credentials configured!)
- ✅ **Stripe Publishable Key** - REAL test key in customer frontend
- ✅ **Database** - SQLite working for development
- ✅ **Redis** - Connection configured
- ✅ **Business Info** - All correct in customer frontend
- ✅ **Security Keys** - Basic dev keys set

**You're 60% done! Just need 4 more things:**

---

## 🔥 What You Need RIGHT NOW (4 items)

### ☐ 1. IONOS Email Credentials ⏰ 5 minutes

**Why:** Email confirmations, review requests won't work without this

**What to do:**
1. Log into IONOS: https://www.ionos.com/
2. Go to **Email & Office → Email Settings**
3. Find your email (probably `bookings@myhibachichef.com` or `info@myhibachichef.com`)
4. Get the password

**Add to `apps/backend/.env`:**
```bash
# Add these lines:
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=your-actual-email@myhibachichef.com
SMTP_PASSWORD=your-ionos-password
SMTP_USE_TLS=True
FROM_EMAIL=your-actual-email@myhibachichef.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30
CUSTOMER_APP_URL=http://localhost:3000
```

**Test it:**
```bash
curl -X POST http://localhost:8000/api/test/send-email -H "Content-Type: application/json" -d '{"to":"your-test@gmail.com","subject":"Test","body":"Test"}'
```

---

### ☐ 2. Stripe Secret Key ⏰ 3 minutes

**Why:** Backend can't process payments without this (you have the frontend key already!)

**What to do:**
1. Go to: https://dashboard.stripe.com/test/apikeys
2. Look for **Secret key** (blurred out, click "Reveal test key")
3. Copy it (starts with `sk_test_51RXxRdCAIUpIKF7z...`)

**Update in `apps/backend/.env`:**
```bash
# Change from:
STRIPE_SECRET_KEY=sk_test_example

# To:
STRIPE_SECRET_KEY=sk_test_51RXxRdCAIUpIKF7zXXXXXXXXXXXXXXXXXXX

# Also update (you have the frontend one already):
STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7zqXGYwOMm35LCMZWMp6Bk2vIlMInoS6ua5ElRTi4xmIOoMCZp6Um1fOFSTFOIyfhqGbBaNMAT00rfx3zxLD
```

---

### ☐ 3. Stripe Webhook Secret ⏰ 5 minutes

**Why:** Stripe can't notify your backend about payment status changes

**What to do:**
1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click **Add endpoint**
3. **Endpoint URL:** `http://localhost:8000/api/stripe/webhook`
4. **Events to send:** Select these:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_`)

**Update in `apps/backend/.env`:**
```bash
# Change from:
STRIPE_WEBHOOK_SECRET=whsec_test_example

# To:
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXX
```

**Note:** For local development, you may need to use Stripe CLI to forward webhooks:
```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe listen --forward-to http://localhost:8000/api/stripe/webhook
```

---

### ☐ 4. OpenAI API Key (Optional but recommended) ⏰ 5 minutes

**Why:** AI chat features won't work

**What to do:**
1. Go to: https://platform.openai.com/signup
2. Create account (free signup, but needs payment method)
3. Go to **Settings → Billing** and add $5-10 credit
4. Go to: https://platform.openai.com/api-keys
5. Click **Create new secret key**
6. Name it "MyHibachi Dev"
7. Copy immediately (shown only once!)

**Update in `apps/backend/.env`:**
```bash
# Change from:
OPENAI_API_KEY=test-openai-key

# To:
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Also add:
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
```

**Cost:** ~$0.002 per conversation (GPT-3.5) or ~$0.03 per conversation (GPT-4)

---

## 🔧 Bonus: Small Fixes ⏰ 2 minutes

### ☐ 5. Add CORS Origins

**Add to `apps/backend/.env`:**
```bash
# Add this line:
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### ☐ 6. Add Alternative Payment Info

**Add to `apps/backend/.env`:**
```bash
# Add these lines:
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
```

---

## 📝 Copy-Paste Ready Template

Here's what to ADD to your `apps/backend/.env`:

```bash
# ==========================================
# ADD THESE SECTIONS TO YOUR EXISTING .env FILE
# ==========================================

# CORS (ADD THIS)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Stripe (UPDATE THESE - You have the publishable key in frontend already)
STRIPE_SECRET_KEY=sk_test_GET_FROM_STRIPE_DASHBOARD
STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7zqXGYwOMm35LCMZWMp6Bk2vIlMInoS6ua5ElRTi4xmIOoMCZp6Um1fOFSTFOIyfhqGbBaNMAT00rfx3zxLD
STRIPE_WEBHOOK_SECRET=whsec_GET_FROM_STRIPE_WEBHOOKS

# Email - IONOS (ADD YOUR ACTUAL CREDENTIALS)
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=YOUR_EMAIL@myhibachichef.com
SMTP_PASSWORD=YOUR_IONOS_PASSWORD
SMTP_USE_TLS=True
FROM_EMAIL=YOUR_EMAIL@myhibachichef.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30
CUSTOMER_APP_URL=http://localhost:3000
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-sacramento
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000

# OpenAI (ADD YOUR KEY)
OPENAI_API_KEY=sk-proj-GET_FROM_OPENAI_PLATFORM
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Alternative Payments (ADD THIS)
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
```

---

## 🧪 Testing After Setup

```bash
# 1. Validate backend config
cd apps/backend
python -c "from core.config import get_settings; settings = get_settings(); print('✅ Config valid!')"

# 2. Start backend (new terminal)
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 3. Test email (new terminal)
curl -X POST http://localhost:8000/api/test/send-email \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@gmail.com","subject":"Test","body":"Test from MyHibachi"}'

# 4. Test Stripe
curl http://localhost:8000/api/stripe/config
# Should return your publishable key

# 5. Test Cloudinary (already working!)
curl http://localhost:8000/api/cloudinary/config
# Should return: {"cloudName": "dlubugier"}

# 6. Start customer frontend (new terminal)
cd apps/customer
npm run dev

# 7. Full booking test
# Open http://localhost:3000/BookUs
# Fill out form
# Use test card: 4242 4242 4242 4242
# Any future date, any CVC
# Should create booking and send confirmation email!
```

---

## 📊 Progress Tracker

### Before:
- [ ] Email configured
- [ ] Stripe backend key
- [ ] Stripe webhooks
- [ ] OpenAI key
- [ ] CORS origins
- [ ] Alternative payments

### After (Your Goal):
- [x] Email configured ✅
- [x] Stripe backend key ✅
- [x] Stripe webhooks ✅
- [x] OpenAI key ✅
- [x] CORS origins ✅
- [x] Alternative payments ✅

**Completion: 0% → 100%** 🎉

---

## 🚨 Troubleshooting

### Backend won't start after changes
```bash
# Check config validation
cd apps/backend
python -c "from core.config import get_settings; get_settings()"
# Look for error message about specific variable
```

### Email test fails
```bash
# Common issues:
# 1. Wrong password → Check IONOS dashboard
# 2. Wrong port → Try 465 with SMTP_USE_SSL=True instead of 587
# 3. Email not enabled in IONOS → Check email settings

# Test SMTP connection directly:
python -c "
import smtplib
server = smtplib.SMTP('smtp.ionos.com', 587)
server.starttls()
server.login('your-email@myhibachichef.com', 'your-password')
print('✅ SMTP connection successful!')
server.quit()
"
```

### Stripe webhook not working locally
```bash
# Use Stripe CLI to forward webhooks:
# 1. Install: https://stripe.com/docs/stripe-cli#install
# 2. Login: stripe login
# 3. Forward: stripe listen --forward-to http://localhost:8000/api/stripe/webhook
# 4. Use the webhook secret shown in terminal
```

---

## 💰 Cost Summary

| Item | Cost | Status |
|------|------|--------|
| IONOS Email | Included? | Check your plan |
| Stripe | $0* | Pay-per-transaction only |
| OpenAI | $5-10 | One-time credit add |
| Cloudinary | $0 | Free tier (25GB) |
| **Total** | **$5-10** | One-time setup |

*Stripe charges per transaction (2.9% + $0.30 per successful charge)

---

## ✅ Final Checklist

After completing all steps:

- [ ] All 4 critical items added to backend .env
- [ ] Backend starts without errors
- [ ] Email test successful (got test email)
- [ ] Stripe test successful (can see publishable key)
- [ ] Cloudinary test successful (image upload working)
- [ ] Customer frontend loads at http://localhost:3000
- [ ] Can complete test booking with card 4242 4242 4242 4242
- [ ] Received booking confirmation email

**When all checked:** 🎉 **YOUR SYSTEM IS 100% FUNCTIONAL!**

---

**Time Investment:** 20 minutes  
**Money Investment:** $5-10 (OpenAI)  
**Result:** Fully functional booking system with payments, email, AI, and image uploads

**Questions?** Check [CURRENT_ENV_STATUS_REPORT.md](./CURRENT_ENV_STATUS_REPORT.md) for detailed explanations.
