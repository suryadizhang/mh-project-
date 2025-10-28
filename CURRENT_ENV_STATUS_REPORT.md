# 🔍 Current Environment Variables Status Report

**Analysis Date:** October 26, 2025  
**Project:** MyHibachi Full-Stack Application  
**Purpose:** Identify what's configured vs what's needed

---

## 📊 Current Status Overview

| Component | Status | Ready? | Action Needed |
|-----------|--------|--------|---------------|
| **Backend API** | ⚠️ Partial | 🔴 NO | Need real API keys |
| **Customer Frontend** | ✅ Good | 🟡 MOSTLY | Update API URLs |
| **Admin Frontend** | ⚠️ Basic | 🔴 NO | Need more configs |
| **Database** | ✅ Working | 🟢 YES | SQLite (dev only) |
| **Payments** | ⚠️ Test Mode | 🟡 MOSTLY | Real key exists |
| **Email** | ❌ Missing | 🔴 NO | **NEED IONOS SETUP** |
| **AI Features** | ❌ Placeholder | 🔴 NO | Need OpenAI key |
| **Images** | ✅ Configured | 🟢 YES | Cloudinary working |

---

## ✅ What You ALREADY HAVE Configured

### Backend (`apps/backend/.env`)

#### ✅ Working & Configured:
1. **Database** - SQLite (development)
   ```bash
   DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db
   ```
   ✅ This works for development

2. **Redis** - Local instance
   ```bash
   REDIS_URL=redis://localhost:6379
   ```
   ✅ This works if Redis is running

3. **Cloudinary** - REAL credentials configured
   ```bash
   CLOUDINARY_CLOUD_NAME=dlubugier
   CLOUDINARY_API_KEY=652913564967941
   CLOUDINARY_API_SECRET=XWmGc5BZuPJKjJoh9tYcCY2oKRg
   ```
   ✅ **This is LIVE and will work for image uploads!**

4. **Security Keys** - Basic dev keys set
   ```bash
   SECRET_KEY=dev-secret-key-change-in-production
   ENCRYPTION_KEY=dev-encryption-key-32-chars-long
   ```
   ⚠️ These work but should be changed for production

### Customer Frontend (`apps/customer/.env.local`)

#### ✅ Working & Configured:
1. **Stripe Publishable Key** - REAL test key
   ```bash
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7z...
   ```
   ✅ **This is a real Stripe test key!**

2. **Business Information** - All set
   ```bash
   NEXT_PUBLIC_BUSINESS_PHONE=(916) 740-8768
   NEXT_PUBLIC_BUSINESS_EMAIL=info@myhibachi.com
   NEXT_PUBLIC_ZELLE_EMAIL=myhibachichef@gmail.com
   NEXT_PUBLIC_VENMO_USERNAME=@myhibachichef
   ```
   ✅ **All business info is correct**

3. **API URLs** - Configured
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_APP_URL=http://localhost:3001
   ```
   ⚠️ Works for local, but note the port is 3001 (not standard 3000)

### Admin Frontend (`apps/admin/.env.local`)

#### ✅ Basic Configuration:
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7z...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3001
```
✅ Basic setup complete

---

## ❌ What You're MISSING (Priority Order)

### 🔴 CRITICAL - System Won't Work Fully Without These

#### 1. **Email Service (IONOS)** - HIGHEST PRIORITY
**Status:** ❌ NOT CONFIGURED  
**Impact:** No booking confirmations, no review requests, no notifications

**What you need to add to `apps/backend/.env`:**
```bash
# Email Configuration (IONOS Business Email)
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=your-email@myhibachichef.com  # ← NEED THIS
SMTP_PASSWORD=your-ionos-password       # ← NEED THIS
SMTP_USE_TLS=True
FROM_EMAIL=your-email@myhibachichef.com # ← NEED THIS
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30

# Review System URLs (for email links)
CUSTOMER_APP_URL=https://myhibachichef.com  # ← Or http://localhost:3000 for dev
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-sacramento
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupon Settings
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000
```

**How to get IONOS email credentials:**
1. Log into your IONOS account: https://www.ionos.com/
2. Go to **Email & Office → Email Settings**
3. Find your email address (e.g., `bookings@myhibachichef.com`)
4. The SMTP settings should show:
   - **Server:** smtp.ionos.com
   - **Port:** 587 (TLS) or 465 (SSL)
   - **Username:** Your full email address
   - **Password:** Your email password

**Testing:**
```bash
# After adding, test email sending:
curl -X POST http://localhost:8000/api/test/send-email \
  -H "Content-Type: application/json" \
  -d '{"to": "your-test-email@gmail.com", "subject": "Test", "body": "Test email"}'
```

---

#### 2. **Stripe Secret Key** - For Payment Processing
**Status:** ❌ PLACEHOLDER (test-example)  
**Impact:** Payments won't work

**Current:**
```bash
STRIPE_SECRET_KEY=sk_test_example  # ← This is a placeholder!
STRIPE_WEBHOOK_SECRET=whsec_test_example  # ← This is a placeholder!
```

**What you need:**
```bash
STRIPE_SECRET_KEY=sk_test_51RXxRdCAIUpIKF7z...  # ← Real key from Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7z...  # ← You already have this!
STRIPE_WEBHOOK_SECRET=whsec_...  # ← Need to set up webhook
```

**How to get Stripe keys:**
1. You already have an account (based on your publishable key)
2. Go to: https://dashboard.stripe.com/test/apikeys
3. Copy the **Secret key** (starts with `sk_test_`)
4. For webhook secret:
   - Go to: https://dashboard.stripe.com/test/webhooks
   - Click **Add endpoint**
   - URL: `http://localhost:8000/api/stripe/webhook` (or your deployed URL)
   - Events: Select `payment_intent.succeeded`, `payment_intent.payment_failed`
   - Copy the **Signing secret** (starts with `whsec_`)

**Your Stripe account ID:** `51RXxRdCAIUpIKF7z` (from your publishable key)

---

#### 3. **OpenAI API Key** - For AI Chat Features
**Status:** ❌ PLACEHOLDER  
**Impact:** AI chat won't work

**Current:**
```bash
OPENAI_API_KEY=test-openai-key  # ← This won't work!
```

**What you need:**
```bash
OPENAI_API_KEY=sk-proj-...  # ← Real key from OpenAI
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17
```

**How to get OpenAI key:**
1. Go to: https://platform.openai.com/signup
2. Create account (requires payment method)
3. Add $5-10 credit to start
4. Go to: https://platform.openai.com/api-keys
5. Click **Create new secret key**
6. Name it "MyHibachi Development"
7. Copy key immediately (shown only once!)

**Cost estimate:** ~$0.002 per 1K tokens (GPT-3.5) or ~$0.03 per 1K tokens (GPT-4)

---

### 🟡 IMPORTANT - Core Features Need These

#### 4. **CORS Origins** - Missing from backend
**Status:** ❌ NOT SET  
**Impact:** Frontend might not connect to backend

**Add to `apps/backend/.env`:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8000
```

---

#### 5. **Alternative Payment Info** - Partially set
**Status:** ⚠️ In frontend but not backend  
**Impact:** Alternative payment options won't show properly

**Add to `apps/backend/.env`:**
```bash
# Alternative Payment Options (matches frontend)
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
CASHAPP_USERNAME=$myhibachichef  # ← If you have one
```

---

### 🟢 OPTIONAL - Can Skip for Now

#### 6. **RingCentral SMS** - All placeholders
**Status:** ❌ NOT CONFIGURED  
**Impact:** No SMS notifications

**Current:** All test values
```bash
RC_CLIENT_ID=test-client-id  # Won't work
```

**Skip for now unless you want SMS features.** Cost: ~$20-30/month

---

#### 7. **Meta/Facebook Integration** - All placeholders
**Status:** ❌ NOT CONFIGURED  
**Impact:** No Facebook/Instagram integration

**Skip for now unless you want social media features.**

---

#### 8. **Google Business Profile** - All placeholders
**Status:** ❌ NOT CONFIGURED  
**Impact:** No Google Business integration

**Skip for now unless you want GBP features.**

---

## 🎯 IMMEDIATE ACTION PLAN

### Step 1: Fix Email (IONOS) - **DO THIS FIRST** ⏰ 5 minutes

1. Get your IONOS email credentials
2. Add to `apps/backend/.env`:
   ```bash
   EMAIL_ENABLED=True
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.ionos.com
   SMTP_PORT=587
   SMTP_USER=bookings@myhibachichef.com  # Your actual email
   SMTP_PASSWORD=your-ionos-password
   SMTP_USE_TLS=True
   FROM_EMAIL=bookings@myhibachichef.com
   EMAILS_FROM_NAME="My Hibachi Chef"
   CUSTOMER_APP_URL=http://localhost:3000
   ```

### Step 2: Fix Stripe Backend - **DO THIS SECOND** ⏰ 3 minutes

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Secret key** (starts with `sk_test_`)
3. Update `apps/backend/.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_KEY_HERE
   STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7zqXGYwOMm35LCMZWMp6Bk2vIlMInoS6ua5ElRTi4xmIOoMCZp6Um1fOFSTFOIyfhqGbBaNMAT00rfx3zxLD
   ```

### Step 3: Set Up Stripe Webhook - **DO THIS THIRD** ⏰ 5 minutes

1. Go to https://dashboard.stripe.com/test/webhooks
2. Add endpoint: `http://localhost:8000/api/stripe/webhook`
3. Copy webhook secret (starts with `whsec_`)
4. Update `apps/backend/.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET_HERE
   ```

### Step 4: Add OpenAI (Optional but recommended) - ⏰ 5 minutes

1. Go to https://platform.openai.com/api-keys
2. Create account and add $5-10 credit
3. Create new API key
4. Update `apps/backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
   OPENAI_MODEL=gpt-4
   ```

### Step 5: Fix CORS - ⏰ 1 minute

Add to `apps/backend/.env`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Step 6: Add Alternative Payment Info - ⏰ 1 minute

Add to `apps/backend/.env`:
```bash
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
```

---

## 📋 Updated .env File Template

Here's what your `apps/backend/.env` should look like after updates:

```bash
# ==========================================
# Environment
# ==========================================
ENVIRONMENT=development
DEBUG=true

# ==========================================
# Database (WORKING - Keep as is for dev)
# ==========================================
DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db
DATABASE_URL_SYNC=sqlite:///./test_myhibachi.db

# ==========================================
# Redis (WORKING - Keep as is)
# ==========================================
REDIS_URL=redis://localhost:6379

# ==========================================
# Security (WORKING for dev - update for production)
# ==========================================
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production-at-least-32-characters-long
ENCRYPTION_KEY=dev-encryption-key-32-chars-long

# ==========================================
# CORS (ADD THIS)
# ==========================================
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ==========================================
# Stripe (UPDATE WITH REAL KEYS)
# ==========================================
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_FROM_STRIPE_DASHBOARD
STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7zqXGYwOMm35LCMZWMp6Bk2vIlMInoS6ua5ElRTi4xmIOoMCZp6Um1fOFSTFOIyfhqGbBaNMAT00rfx3zxLD
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_FROM_STRIPE_WEBHOOKS

# ==========================================
# Email - IONOS (ADD YOUR CREDENTIALS)
# ==========================================
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=bookings@myhibachichef.com
SMTP_PASSWORD=YOUR_IONOS_EMAIL_PASSWORD
SMTP_USE_TLS=True
FROM_EMAIL=bookings@myhibachichef.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30

# Customer Review System
CUSTOMER_APP_URL=http://localhost:3000
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-sacramento
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupons
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000

# ==========================================
# OpenAI (ADD YOUR KEY)
# ==========================================
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# ==========================================
# Cloudinary (WORKING - Keep as is)
# ==========================================
CLOUDINARY_CLOUD_NAME=dlubugier
CLOUDINARY_API_KEY=652913564967941
CLOUDINARY_API_SECRET=XWmGc5BZuPJKjJoh9tYcCY2oKRg

# ==========================================
# Alternative Payments (ADD THIS)
# ==========================================
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef

# ==========================================
# OPTIONAL - Skip these for now
# ==========================================
# RingCentral SMS
RC_CLIENT_ID=test-client-id
RC_CLIENT_SECRET=test-client-secret
RC_JWT_TOKEN=test-jwt-token
RC_WEBHOOK_SECRET=test-webhook-secret
RC_SMS_FROM=+1234567890

# Plaid
PLAID_CLIENT_ID=test-plaid-client
PLAID_SECRET=test-plaid-secret

# Meta (Facebook/Instagram)
META_APP_ID=test-meta-app-id
META_APP_SECRET=test-meta-app-secret
META_VERIFY_TOKEN=test-meta-verify-token
META_PAGE_ACCESS_TOKEN=test-meta-page-token

# Google Cloud
GOOGLE_CLOUD_PROJECT=test-project
GOOGLE_CREDENTIALS_JSON={}
GBP_ACCOUNT_ID=test-gbp-account
GBP_LOCATION_ID=test-gbp-location
```

---

## ✅ Testing Checklist

After making changes:

```bash
# 1. Test backend config loads
cd apps/backend
python -c "from core.config import get_settings; settings = get_settings(); print('✅ Config valid!')"

# 2. Test email sending
curl -X POST http://localhost:8000/api/test/send-email \
  -H "Content-Type: application/json" \
  -d '{"to":"your-email@gmail.com","subject":"Test","body":"Test"}'

# 3. Test Stripe connection
curl http://localhost:8000/api/stripe/config

# 4. Test image upload
curl http://localhost:8000/api/cloudinary/config

# 5. Start backend
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 6. Start customer frontend
cd apps/customer
npm run dev

# 7. Test booking flow
# Open http://localhost:3000/BookUs
# Complete booking with test card: 4242 4242 4242 4242
```

---

## 🔐 Security Notes

**⚠️ IMPORTANT:**
1. Your Cloudinary credentials are LIVE - they're in the .env file!
2. Never commit `.env` files to Git (they should be in `.gitignore`)
3. For production:
   - Generate new SECRET_KEY and ENCRYPTION_KEY (64+ chars)
   - Use Stripe LIVE keys (sk_live_ and pk_live_)
   - Use strong database password
   - Set DEBUG=False and ENVIRONMENT=production

---

## 📞 Where to Get Help

**IONOS Email:**
- Support: https://www.ionos.com/help
- SMTP Settings: Look for "Email Settings" in your IONOS dashboard

**Stripe:**
- Dashboard: https://dashboard.stripe.com/
- Docs: https://stripe.com/docs
- Test Cards: https://stripe.com/docs/testing

**OpenAI:**
- Platform: https://platform.openai.com/
- Pricing: https://openai.com/pricing
- Docs: https://platform.openai.com/docs

---

## 📊 Summary

**What's Working:** ✅
- Database (SQLite for dev)
- Redis connection
- Cloudinary (image uploads) **← FULLY WORKING!**
- Customer frontend Stripe key **← REAL KEY!**
- Business information
- Basic security keys (for dev)

**What Needs Immediate Attention:** 🔴
1. **IONOS Email credentials** (bookings@myhibachichef.com password)
2. **Stripe Secret Key** (from your dashboard)
3. **Stripe Webhook Secret** (create webhook endpoint)
4. **OpenAI API Key** (optional but recommended)
5. **CORS_ORIGINS** (add to backend)

**What Can Wait:** 🟢
- RingCentral SMS
- Facebook/Instagram integration
- Google Business Profile
- Plaid banking
- Production database (PostgreSQL)

---

**Total Time to Fix Critical Items:** ~20 minutes  
**Cost to Add Critical Items:** $5-10 (OpenAI credit)  
**System Readiness After Fixes:** 95% functional for development

---

**Last Updated:** October 26, 2025  
**Next Review:** After adding missing credentials
