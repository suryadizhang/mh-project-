# 🚀 Step-by-Step Guide: Get Remaining API Keys

**Status:** ✅ IONOS Email added to backend .env  
**Email:** cs@myhibachichef.com configured  
**Remaining:** 3 critical items to complete

---

## ✅ What's Already Done

I've added to your `apps/backend/.env`:
- ✅ IONOS Email credentials (cs@myhibachichef.com)
- ✅ CORS origins
- ✅ Alternative payment info (Zelle, Venmo)
- ✅ Email system configuration
- ✅ Review coupon settings

---

## 🔥 What You Need to Get (3 Items)

### Priority Order:
1. **Stripe Secret Key** (3 minutes) - For payment processing
2. **Stripe Webhook Secret** (5 minutes) - For payment notifications
3. **OpenAI API Key** (5 minutes) - For AI chat features (optional but recommended)

---

## 📋 Step 1: Get Stripe Secret Key ⏰ 3 minutes

### What You Need:
Your Stripe account already exists (based on the publishable key: `pk_test_51RXxRdCAIUpIKF7z...`)

### Steps:

1. **Open Stripe Dashboard**
   - Go to: https://dashboard.stripe.com/login
   - Log in with your Stripe account

2. **Navigate to API Keys**
   - Once logged in, you'll see the sidebar
   - Click **Developers** (in left sidebar)
   - Click **API keys**
   - Or go directly to: https://dashboard.stripe.com/test/apikeys

3. **Get Your Secret Key**
   - You'll see two keys on the page:
     - **Publishable key** (starts with `pk_test_`) - You already have this!
     - **Secret key** (starts with `sk_test_`) - This is what you need
   
   - The secret key will be **hidden/blurred**
   - Click **Reveal test key** button next to it
   - Copy the entire key (it's long, starts with `sk_test_51RXxRdCAIUpIKF7z...`)

4. **Update Your .env File**
   - Open: `apps/backend/.env`
   - Find the line: `STRIPE_SECRET_KEY=sk_test_example`
   - Replace with: `STRIPE_SECRET_KEY=sk_test_51RXxRdCAIUpIKF7z...` (your actual key)

### ✅ Verification:
```bash
# The key should:
# - Start with sk_test_
# - Be about 107 characters long
# - Match the same account ID as your publishable key (51RXxRdCAIUpIKF7z)
```

---

## 📋 Step 2: Get Stripe Webhook Secret ⏰ 5 minutes

### What You Need:
A webhook endpoint so Stripe can notify your backend about payment events.

### Steps:

1. **Navigate to Webhooks**
   - In Stripe Dashboard, click **Developers** (left sidebar)
   - Click **Webhooks**
   - Or go directly to: https://dashboard.stripe.com/test/webhooks

2. **Add New Endpoint**
   - Click **Add endpoint** button (top right)
   - You'll see a form

3. **Configure the Endpoint**
   - **Endpoint URL:** Enter `http://localhost:8000/api/stripe/webhook`
   - **Description:** Enter "MyHibachi Local Development"
   - **Events to send:** Click "Select events"
   
4. **Select Events**
   - In the event selection screen, check these:
     - ✅ `payment_intent.succeeded`
     - ✅ `payment_intent.payment_failed`
     - ✅ `payment_intent.canceled`
     - ✅ `charge.succeeded`
     - ✅ `charge.failed`
   - Click **Add events** button

5. **Create the Endpoint**
   - Click **Add endpoint** button at bottom
   - You'll see your new endpoint listed

6. **Get the Signing Secret**
   - Click on your newly created endpoint
   - You'll see **Signing secret** section
   - Click **Reveal** to show the secret
   - Copy the secret (starts with `whsec_`)

7. **Update Your .env File**
   - Open: `apps/backend/.env`
   - Find: `STRIPE_WEBHOOK_SECRET=whsec_test_example`
   - Replace with: `STRIPE_WEBHOOK_SECRET=whsec_...` (your actual secret)

### ⚠️ Important Note:
The webhook endpoint `http://localhost:8000` only works when testing locally. For production, you'll need to:
- Create a new endpoint with your production URL
- Use Stripe CLI for local testing (optional): https://stripe.com/docs/stripe-cli

### ✅ Verification:
```bash
# The webhook secret should:
# - Start with whsec_
# - Be about 32-40 characters long
```

---

## 📋 Step 3: Get OpenAI API Key ⏰ 5 minutes (Optional)

### What You Need:
An OpenAI account with API access.

### Steps:

1. **Create OpenAI Account** (if you don't have one)
   - Go to: https://platform.openai.com/signup
   - Click **Sign up**
   - Use your email or Google/Microsoft account
   - Verify your email if required

2. **Set Up Billing** (Required for API access)
   - Go to: https://platform.openai.com/settings/organization/billing/overview
   - Click **Add payment method**
   - Enter credit card information
   - Add credit (start with $5-10)
   - Note: OpenAI requires prepaid credits, not monthly billing

3. **Navigate to API Keys**
   - Go to: https://platform.openai.com/api-keys
   - Or click **API keys** in the left sidebar

4. **Create New API Key**
   - Click **Create new secret key** button
   - Give it a name: "MyHibachi Development"
   - (Optional) Set permissions if available
   - Click **Create secret key**

5. **Copy the Key IMMEDIATELY**
   - ⚠️ **CRITICAL:** The key is shown only ONCE!
   - Copy the entire key (starts with `sk-proj-` or `sk-`)
   - Save it somewhere safe temporarily
   - You cannot retrieve it later - you'd need to create a new one

6. **Update Your .env File**
   - Open: `apps/backend/.env`
   - Find: `OPENAI_API_KEY=test-openai-key`
   - Replace with: `OPENAI_API_KEY=sk-proj-...` (your actual key)

### 💰 Cost Information:
- **GPT-3.5-Turbo:** ~$0.002 per 1K tokens (~500 words)
- **GPT-4:** ~$0.03 per 1K tokens (~500 words)
- **Estimated monthly cost:** $5-20 for light usage
- You can set usage limits in billing settings

### ✅ Verification:
```bash
# The key should:
# - Start with sk-proj- or sk-
# - Be about 48-56 characters long
```

### ⚠️ Skip if Not Needed:
If you don't want AI chat features right now, you can skip this. The system will work without it (just no AI assistant).

---

## 🧪 Test Your Configuration

After adding all keys, test everything:

### Test 1: Validate Config
```bash
cd apps/backend
python -c "from core.config import get_settings; settings = get_settings(); print('✅ Configuration valid!')"
```

### Test 2: Start Backend
```bash
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**If you see errors:**
- Check the specific error message
- Verify all environment variables are correct
- Make sure no typos in the .env file

### Test 3: Test Email (New Terminal)
```bash
curl -X POST http://localhost:8000/api/test/send-email -H "Content-Type: application/json" -d "{\"to\":\"your-personal-email@gmail.com\",\"subject\":\"MyHibachi Test\",\"body\":\"Email system working!\"}"
```

**Expected result:** Check your personal email inbox for test email from cs@myhibachichef.com

### Test 4: Test Stripe Connection
```bash
curl http://localhost:8000/api/stripe/config
```

**Expected output:**
```json
{
  "publishableKey": "pk_test_51RXxRdCAIUpIKF7z..."
}
```

### Test 5: Full Booking Flow
```bash
# Start frontend in new terminal
cd apps/customer
npm run dev
```

Then:
1. Open http://localhost:3000/BookUs
2. Fill out booking form
3. Use test card: `4242 4242 4242 4242`
4. Any future expiry date (e.g., 12/25)
5. Any CVC (e.g., 123)
6. Click submit
7. Check your email for booking confirmation!

---

## 📊 Progress Checklist

Track your progress:

- [x] IONOS Email added (cs@myhibachichef.com) ✅
- [ ] Stripe Secret Key added
- [ ] Stripe Webhook Secret added
- [ ] OpenAI API Key added (optional)
- [ ] Backend starts successfully
- [ ] Email test successful
- [ ] Stripe test successful
- [ ] Full booking flow works

---

## 🎯 Quick Reference: Where to Get Keys

| Service | URL | What to Get |
|---------|-----|-------------|
| **Stripe Keys** | https://dashboard.stripe.com/test/apikeys | Secret key (sk_test_...) |
| **Stripe Webhook** | https://dashboard.stripe.com/test/webhooks | Signing secret (whsec_...) |
| **OpenAI API** | https://platform.openai.com/api-keys | API key (sk-proj-...) |

---

## 🚨 Troubleshooting

### "Can't log into Stripe"
- Check if you have a Stripe account
- Try password reset
- Check email for verification link
- Your account ID from publishable key: `51RXxRdCAIUpIKF7z`

### "Stripe webhook won't create"
- Make sure backend is running first
- Use exact URL: `http://localhost:8000/api/stripe/webhook`
- Select at least one event type
- For local testing, webhook might not receive events until you use Stripe CLI

### "OpenAI requires payment method"
- OpenAI API requires prepaid credits
- Minimum credit: $5
- Set up usage limits in billing settings
- Alternative: Skip for now, add later

### "Backend won't start"
- Check for typos in .env file
- Ensure Redis is running: `redis-server` or `docker run -p 6379:6379 redis`
- Check Python version: `python --version` (need 3.11+)
- Install dependencies: `pip install -r requirements.txt`

### "Email test fails"
- Verify IONOS credentials are correct
- Try logging into https://mail.ionos.com with cs@myhibachichef.com
- Check if SMTP is enabled in IONOS
- Try port 465 instead of 587 if TLS fails

---

## 📝 Updated .env File Preview

After you complete all steps, your `apps/backend/.env` should look like:

```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db
DATABASE_URL_SYNC=sqlite:///./test_myhibachi.db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production-at-least-32-characters-long
ENCRYPTION_KEY=dev-encryption-key-32-chars-long

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Email - IONOS (✅ DONE)
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=cs@myhibachichef.com
SMTP_PASSWORD=myhibachicustomers!
SMTP_USE_TLS=True
FROM_EMAIL=cs@myhibachichef.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30

# Stripe (UPDATE THESE 2 LINES)
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_WEBHOOK_SECRET_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_51RXxRdCAIUpIKF7zqXGYwOMm35LCMZWMp6Bk2vIlMInoS6ua5ElRTi4xmIOoMCZp6Um1fOFSTFOIyfhqGbBaNMAT00rfx3zxLD

# OpenAI (UPDATE THIS LINE)
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_API_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Cloudinary (✅ ALREADY WORKING)
CLOUDINARY_CLOUD_NAME=dlubugier
CLOUDINARY_API_KEY=652913564967941
CLOUDINARY_API_SECRET=XWmGc5BZuPJKjJoh9tYcCY2oKRg

# Alternative Payments (✅ DONE)
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef

# Customer Review URLs (✅ DONE)
CUSTOMER_APP_URL=http://localhost:3000
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-sacramento
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupons (✅ DONE)
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000
```

---

## ✅ Completion Checklist

You're done when you can:
- [x] IONOS email configured
- [ ] Stripe secret key obtained and added
- [ ] Stripe webhook created and secret added
- [ ] OpenAI key obtained and added (optional)
- [ ] Backend starts without errors
- [ ] Can send test email
- [ ] Can process test payment
- [ ] Can complete full booking flow

---

## 🎉 What Happens After Completion

Once all keys are added:
1. **Payment system fully functional** - Accept real test payments
2. **Email system working** - Send booking confirmations
3. **AI chat enabled** - Intelligent customer assistance
4. **Image uploads working** - Customer review photos (already working!)
5. **Full booking system** - End-to-end tested

**Total time:** ~15 minutes  
**Cost:** $5-10 (OpenAI credit only)  
**Result:** 100% functional booking system!

---

**Questions?** If you get stuck on any step:
1. Check the specific error message
2. Verify you're logged into the correct account
3. Double-check the URL you're visiting
4. Make sure you copied the entire key (no spaces/truncation)

**Next:** After adding keys, run all tests to verify everything works!
