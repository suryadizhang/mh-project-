# Step-by-Step Guide: Get Missing API Keys
**Date:** October 26, 2025  
**Estimated Total Time:** 45 minutes  
**Total Cost:** $0 (all free for development)

---

## 🎯 PRIORITY 1: Stripe Webhook Secret (5 minutes) - REQUIRED

### Why You Need This:
- Verify webhook events are really from Stripe (security)
- Get notified when payments succeed/fail
- Required for production payment processing

### Step-by-Step Instructions:

#### Step 1: Open Stripe Dashboard
1. Go to: **https://dashboard.stripe.com/login**
2. Log in with your Stripe account
3. Make sure you're in **TEST MODE** (toggle in top-right corner should say "Test")

#### Step 2: Navigate to Webhooks
1. Click **Developers** in the top menu
2. Click **Webhooks** in the left sidebar
3. Click **Add endpoint** button (top-right)

#### Step 3: Configure Your Webhook
1. **Endpoint URL:** Enter one of these (depending on your setup):
   - Local development: `http://localhost:8000/api/stripe/webhook`
   - Production: `https://yourdomain.com/api/stripe/webhook`
   
2. **Description:** "MyHibachi Payment Notifications"

3. **Events to listen to:** Click "Select events" and choose:
   - ✅ `payment_intent.succeeded` (payment completed)
   - ✅ `payment_intent.payment_failed` (payment failed)
   - ✅ `payment_intent.canceled` (payment canceled)
   - ✅ `checkout.session.completed` (checkout completed)
   - ✅ `customer.created` (new customer)
   - ✅ `charge.refunded` (refund processed)

4. Click **Add endpoint**

#### Step 4: Get Your Webhook Secret
1. You'll see your new webhook endpoint listed
2. Click on the endpoint you just created
3. Find the **Signing secret** section
4. Click **Reveal** (or **Click to reveal**)
5. Copy the value that starts with `whsec_...`

#### Step 5: Add to Your .env File
1. Open: `apps/backend/.env`
2. Find this line:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_test_example
   ```
3. Replace with your real secret:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET_HERE
   ```
4. Save the file

✅ **Done! Stripe webhook is configured.**

---

## 🔔 PRIORITY 2: RingCentral SMS (15 minutes) - OPTIONAL

### Why You Might Need This:
- Send SMS notifications to customers
- Two-factor authentication via SMS
- Order status updates via text

### Cost:
- Free sandbox for testing (limited features)
- Production: $30-50/month for SMS capability
- Alternative: Use email only (free with IONOS)

### Step-by-Step Instructions:

#### Step 1: Create RingCentral Account
1. Go to: **https://developers.ringcentral.com/**
2. Click **Sign Up** (top-right)
3. Choose **Create a free account**
4. Fill in:
   - Email: Your business email
   - Password: Choose a strong password
   - Company: "My Hibachi Chef"
5. Verify your email

#### Step 2: Create an App
1. After login, go to: **https://developers.ringcentral.com/my-account.html**
2. Click **Create App** (or **Apps** → **Create App**)
3. Fill in app details:
   - **App Name:** MyHibachi CRM
   - **Application Type:** Select **Server/Web**
   - **Platform Type:** Select **REST API**
   - **Auth Type:** Select **JWT**
4. Click **Create**

#### Step 3: Get Your Credentials
1. On your app page, you'll see:
   - **Client ID** - Copy this
   - **Client Secret** - Click "Show" then copy
2. Click on **Credentials** tab (if available)
3. Look for **JWT Token** or **Generate JWT**
   - Click **Generate Token**
   - Copy the JWT token (long string)

#### Step 4: Get Webhook Secret (Optional)
1. In your app settings, find **Webhooks** section
2. Click **Add Webhook Subscription**
3. Generate a webhook secret or copy provided secret

#### Step 5: Get Your SMS Phone Number
1. Go to **Sandbox** section
2. You'll be assigned a test phone number
3. Copy this number (format: +1234567890)

#### Step 6: Add to Your .env File
Open `apps/backend/.env` and update:
```bash
RC_CLIENT_ID=your_client_id_here
RC_CLIENT_SECRET=your_client_secret_here
RC_JWT_TOKEN=your_jwt_token_here
RC_WEBHOOK_SECRET=your_webhook_secret_here
RC_SMS_FROM=+1234567890  # Your assigned number
RC_SERVER_URL=https://platform.ringcentral.com
```

✅ **Done! RingCentral SMS is configured.**

**Note:** If this seems too complex or expensive, you can skip SMS and use email only (which you already have configured).

---

## 🏦 PRIORITY 3: Plaid Banking (10 minutes) - OPTIONAL

### Why You Might Need This:
- Verify customer bank accounts
- ACH payment processing
- Payment method validation

### Cost:
- Free for development (sandbox with test bank accounts)
- Production: Pay per API call (starts free, then usage-based)

### When to Skip:
If you only use Stripe for payments, you don't need Plaid.

### Step-by-Step Instructions:

#### Step 1: Create Plaid Account
1. Go to: **https://dashboard.plaid.com/signup**
2. Click **Get started for free**
3. Fill in:
   - Email: Your business email
   - Company name: "My Hibachi Chef"
   - Use case: Select "Payments"
4. Verify your email

#### Step 2: Complete Onboarding
1. Answer questions about your business
2. Select **Sandbox** environment (for development)
3. Complete the setup wizard

#### Step 3: Get Your API Keys
1. After setup, go to: **https://dashboard.plaid.com/team/keys**
2. You'll see:
   - **Client ID** - Copy this
   - **Sandbox Secret** - Copy this
   - **Development Secret** (optional for later)

#### Step 4: Add to Your .env File
Open `apps/backend/.env` and update:
```bash
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_sandbox_secret_here
PLAID_ENV=sandbox  # Use 'sandbox' for development
```

#### Step 5: Test Bank Accounts (Optional)
Plaid provides test bank accounts in sandbox:
- Username: `user_good`
- Password: `pass_good`
- Use these to test bank connections

✅ **Done! Plaid is configured.**

---

## 📱 PRIORITY 4: Meta (Facebook/Instagram) (10 minutes) - OPTIONAL

### Why You Might Need This:
- Post to Facebook business page
- Respond to Instagram messages
- Sync social media reviews

### Cost: FREE

### Step-by-Step Instructions:

#### Step 1: Create Facebook Developer Account
1. Go to: **https://developers.facebook.com/**
2. Click **Get Started** (top-right)
3. Log in with your Facebook account
4. Complete developer registration

#### Step 2: Create an App
1. Go to: **https://developers.facebook.com/apps/**
2. Click **Create App**
3. Choose use case: **Business**
4. Fill in:
   - **App Name:** MyHibachi CRM
   - **App Contact Email:** cs@myhibachichef.com
5. Click **Create App**

#### Step 3: Add Products
1. In your app dashboard, find **Add Products**
2. Add these products:
   - **Facebook Login** (click Set Up)
   - **Webhooks** (click Set Up)
   - **Instagram Graph API** (if you want Instagram)

#### Step 4: Get Your App Credentials
1. Go to **Settings** → **Basic** (left sidebar)
2. You'll see:
   - **App ID** - Copy this
   - **App Secret** - Click "Show" then copy

#### Step 5: Generate Access Token
1. Go to **Tools** → **Graph API Explorer**
2. Select your app from dropdown
3. Click **Generate Access Token**
4. Grant necessary permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_messaging`
5. Copy the access token

#### Step 6: Create Verify Token
1. Create a random string (for webhook verification)
2. Example: `myhibachi_webhook_verify_2025_secure`

#### Step 7: Add to Your .env File
Open `apps/backend/.env` and update:
```bash
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_VERIFY_TOKEN=myhibachi_webhook_verify_2025_secure
META_PAGE_ACCESS_TOKEN=your_access_token_here
```

✅ **Done! Meta is configured.**

---

## 🌐 PRIORITY 5: Google Business Profile (10 minutes) - OPTIONAL

### Why You Might Need This:
- Fetch Google Business reviews
- Post updates to Google Business Profile
- Respond to customer reviews

### Cost: FREE

### Step-by-Step Instructions:

#### Step 1: Create Google Cloud Project
1. Go to: **https://console.cloud.google.com/**
2. Click **Select a project** → **New Project**
3. Fill in:
   - **Project name:** MyHibachi-CRM
   - **Organization:** Leave default
4. Click **Create**

#### Step 2: Enable APIs
1. Go to: **APIs & Services** → **Library**
2. Search and enable these APIs:
   - **Google My Business API**
   - **Google Business Profile API**
3. Click **Enable** for each

#### Step 3: Create Service Account
1. Go to: **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in:
   - **Service account name:** myhibachi-crm-service
   - **Description:** "CRM system for My Hibachi Chef"
4. Click **Create and Continue**
5. Grant role: **Owner** (or **Editor**)
6. Click **Done**

#### Step 4: Generate JSON Key
1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**
6. A JSON file will download - save it securely!

#### Step 5: Get Your Account and Location IDs
1. Go to: **https://business.google.com/**
2. Select your business location
3. Look at the URL, it will look like:
   ```
   https://business.google.com/u/0/n/12345678901234567890/location/09876543210987654321
   ```
4. The first long number is your **Account ID**
5. The second long number is your **Location ID**

#### Step 6: Add to Your .env File
Open `apps/backend/.env` and update:
```bash
GOOGLE_CLOUD_PROJECT=myhibachi-crm
GOOGLE_CREDENTIALS_JSON=/path/to/your/downloaded-credentials.json
GBP_ACCOUNT_ID=12345678901234567890  # From URL
GBP_LOCATION_ID=09876543210987654321  # From URL
```

**Important:** Store the JSON credentials file securely!
- Save it to: `apps/backend/credentials/google-credentials.json`
- Add this path to `.gitignore` (should already be there)
- Update the path in .env accordingly

✅ **Done! Google Business Profile is configured.**

---

## 📋 QUICK CHECKLIST

Use this to track your progress:

### Required (for full functionality):
- [ ] Stripe Webhook Secret (`whsec_...`) - 5 minutes

### Optional (choose based on needs):
- [ ] RingCentral SMS (if you want SMS notifications) - 15 minutes
- [ ] Plaid Banking (if you need bank verification) - 10 minutes
- [ ] Meta (if you want social media integration) - 10 minutes
- [ ] Google Business (if you want Google review integration) - 10 minutes

---

## 🎯 RECOMMENDED PRIORITIES

### Do Right Now:
1. ✅ **Stripe Webhook Secret** - Required for payment processing

### Do This Week:
2. ✅ **Google Business Profile** - Get reviews flowing into your system
3. ✅ **Meta (Facebook)** - Social media presence

### Do Later (If Needed):
4. ⚠️ **RingCentral SMS** - Only if email isn't enough
5. ⚠️ **Plaid** - Only if you need bank account verification

---

## 💡 COST-BENEFIT ANALYSIS

### Free Forever:
- ✅ Stripe Webhook (included with Stripe account)
- ✅ Meta/Facebook APIs (free)
- ✅ Google Cloud/Business Profile (free tier sufficient)
- ✅ Plaid Sandbox (free for development)

### Costs Money in Production:
- 💰 RingCentral: $30-50/month (skip if email works for you)
- 💰 Plaid Production: Usage-based (only pay if you use it)

### My Recommendation:
**Start with:** Stripe webhook only (5 minutes, $0)  
**Add later:** Google Business Profile (free, helps with reviews)  
**Skip for now:** RingCentral SMS, Plaid (unless you specifically need them)

---

## 🆘 TROUBLESHOOTING

### "I can't find my Stripe webhook secret"
- Make sure you're in TEST mode (toggle top-right)
- Go to Developers → Webhooks
- Click on your webhook endpoint
- Look for "Signing secret" section
- Click "Reveal"

### "RingCentral JWT token expired"
- JWT tokens expire after a period
- Generate a new one from the developer console
- Update your .env file with the new token

### "Google credentials file not found"
- Make sure the path in GOOGLE_CREDENTIALS_JSON is absolute
- Example: `C:/Users/surya/projects/MH webapps/apps/backend/credentials/google-credentials.json`
- Check the file exists at that location
- Make sure it's valid JSON (open in text editor to verify)

### "Meta access token invalid"
- Page access tokens can expire
- Generate a long-lived token (60 days) using token exchange
- Or use a system user token (doesn't expire)

---

## ✅ AFTER GETTING ALL KEYS

### Test Your Configuration:
```bash
cd apps/backend
python -c "from src.core.config import get_settings; s = get_settings(); print('✅ All configs valid!')"
```

### Start Your Backend:
```bash
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Check All Features Work:
- [ ] Make test payment with Stripe
- [ ] Webhook receives notification
- [ ] Email sends successfully (already configured)
- [ ] AI chat responds (already configured)
- [ ] Image upload works (already configured)

---

## 📞 NEED HELP?

If you get stuck on any step:
1. Check the troubleshooting section above
2. Refer to official documentation:
   - Stripe: https://stripe.com/docs/webhooks
   - RingCentral: https://developers.ringcentral.com/guide/getting-started
   - Plaid: https://plaid.com/docs/quickstart/
   - Meta: https://developers.facebook.com/docs/
   - Google: https://developers.google.com/my-business

---

**Good luck! Start with the Stripe webhook (5 minutes) and you'll have a fully functional payment system!** 🚀
