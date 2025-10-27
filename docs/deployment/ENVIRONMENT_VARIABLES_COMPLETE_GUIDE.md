# 🔑 COMPLETE ENVIRONMENT VARIABLES GUIDE
## For Local Development & Production Deployment

---

## 📋 QUICK START - MINIMUM REQUIRED

### Backend (.env) - CRITICAL
```bash
# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./myhibachi.db

# Redis (optional for dev, required for production)
REDIS_URL=redis://localhost:6379/0

# Security Keys (MUST BE 32+ CHARACTERS)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-min-32-chars-REQUIRED-CHANGE-THIS-IN-PRODUCTION-123456789012
ENCRYPTION_KEY=your-encryption-key-min-32-chars-REQUIRED-CHANGE-THIS-IN-PRODUCTION-123456789012

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# OpenAI (for AI features)
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY_HERE
```

### Frontend (.env.local) - CRITICAL
```bash
# App URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Public Key
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY_HERE

# Auth Secret (MUST BE 32+ CHARACTERS)
# Generate with: openssl rand -base64 32
NEXTAUTH_SECRET=your-nextauth-secret-min-32-chars-REQUIRED-CHANGE-THIS-123456789012
NEXTAUTH_URL=http://localhost:3000
```

---

## 🔐 COMPLETE ENVIRONMENT VARIABLES

### 1. Backend (apps/backend/.env)

```bash
# ==========================================
# DATABASE CONFIGURATION (REQUIRED)
# ==========================================
# Development: SQLite
DATABASE_URL=sqlite:///./myhibachi.db

# Production: PostgreSQL
# DATABASE_URL=postgresql+asyncpg://username:password@hostname:5432/database_name

# Database Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=False  # Set to True for SQL query logging in dev


# ==========================================
# REDIS CONFIGURATION (REQUIRED)
# ==========================================
# Development: Local Redis
REDIS_URL=redis://localhost:6379/0

# Production: Redis with auth
# REDIS_URL=redis://:password@hostname:6379/0


# ==========================================
# SECURITY KEYS (REQUIRED - CRITICAL)
# ==========================================
# WARNING: MUST be at least 32 characters!
# Generate with: openssl rand -hex 32

# Secret key for JWT tokens and general security
SECRET_KEY=your-secret-key-min-32-chars-REQUIRED-CHANGE-THIS-IN-PRODUCTION-123456789012

# Encryption key for sensitive data in database
ENCRYPTION_KEY=your-encryption-key-min-32-chars-REQUIRED-CHANGE-THIS-IN-PRODUCTION-123456789012

# JWT token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30


# ==========================================
# STRIPE PAYMENT INTEGRATION (REQUIRED)
# ==========================================
# Get from: https://dashboard.stripe.com/apikeys

# Development: Test keys
STRIPE_SECRET_KEY=sk_test_51YOUR_TEST_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_TEST_WEBHOOK_SECRET_HERE

# Production: Live keys (uncomment when deploying)
# STRIPE_SECRET_KEY=sk_live_51YOUR_LIVE_SECRET_KEY_HERE
# STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY_HERE
# STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET_HERE


# ==========================================
# RINGCENTRAL SMS/PHONE (REQUIRED)
# ==========================================
# Get from: https://developers.ringcentral.com/my-account.html
RC_CLIENT_ID=your-ringcentral-client-id
RC_CLIENT_SECRET=your-ringcentral-client-secret
RC_JWT_TOKEN=your-ringcentral-jwt-token
RC_WEBHOOK_SECRET=your-ringcentral-webhook-secret
RC_SMS_FROM=+19167408768
RC_SERVER_URL=https://platform.ringcentral.com


# ==========================================
# OPENAI API (REQUIRED FOR AI FEATURES)
# ==========================================
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17


# ==========================================
# APPLICATION SETTINGS
# ==========================================
APP_NAME=My Hibachi Chef CRM
DEBUG=False  # Set to True for development debugging
ENVIRONMENT=production  # Options: development | staging | production
API_VERSION=1.0.0

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Origins (comma-separated)
CORS_ORIGINS=https://myhibachichef.com,https://admin.myhibachichef.com


# ==========================================
# PLAID BANKING INTEGRATION (OPTIONAL)
# ==========================================
# Get from: https://dashboard.plaid.com/team/keys
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox  # Options: sandbox | development | production


# ==========================================
# META (FACEBOOK/INSTAGRAM) INTEGRATION (OPTIONAL)
# ==========================================
# Get from: https://developers.facebook.com/apps/
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_VERIFY_TOKEN=your-meta-verify-token
META_PAGE_ACCESS_TOKEN=your-meta-page-access-token


# ==========================================
# GOOGLE BUSINESS INTEGRATION (OPTIONAL)
# ==========================================
# Get from: https://console.cloud.google.com/
GOOGLE_CLOUD_PROJECT=your-google-cloud-project
GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json
GBP_ACCOUNT_ID=your-google-business-account-id
GBP_LOCATION_ID=your-google-business-location-id


# ==========================================
# EMAIL SETTINGS (IONOS Business Email)
# ==========================================
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=your_email@yourdomain.com
SMTP_PASSWORD=your_password_here
SMTP_USE_TLS=True
FROM_EMAIL=your_email@yourdomain.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30


# ==========================================
# CUSTOMER REVIEW SYSTEM
# ==========================================
CUSTOMER_APP_URL=https://myhibachi.com
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-your-city
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupon Settings
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000


# ==========================================
# SENTRY ERROR TRACKING & MONITORING (RECOMMENDED)
# ==========================================
# Get from: https://sentry.io/organizations/your-org/projects/
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1


# ==========================================
# BUSINESS INFORMATION (PUBLIC DATA ONLY)
# ==========================================
BUSINESS_NAME=my Hibachi LLC
BUSINESS_EMAIL=cs@myhibachichef.com
BUSINESS_PHONE=+19167408768
BUSINESS_CITY=Fremont
BUSINESS_STATE=California
SERVICE_AREAS=Sacramento, Bay Area, Central Valley


# ==========================================
# AI SETTINGS
# ==========================================
ENABLE_AI_AUTO_REPLY=True
AI_CONFIDENCE_THRESHOLD=80


# ==========================================
# BUSINESS RULES
# ==========================================
QUIET_HOURS_START=21  # 9 PM
QUIET_HOURS_END=8     # 8 AM
DEFAULT_TIMEZONE=America/Los_Angeles
MAX_SMS_PER_THREAD=3


# ==========================================
# RATE LIMITING CONFIGURATION
# ==========================================
# Public API (unauthenticated)
RATE_LIMIT_PUBLIC_PER_MINUTE=20
RATE_LIMIT_PUBLIC_PER_HOUR=1000
RATE_LIMIT_PUBLIC_BURST=30

# Admin API (authenticated admin users)
RATE_LIMIT_ADMIN_PER_MINUTE=100
RATE_LIMIT_ADMIN_PER_HOUR=5000
RATE_LIMIT_ADMIN_BURST=150

# Super Admin (owner/manager)
RATE_LIMIT_ADMIN_SUPER_PER_MINUTE=200
RATE_LIMIT_ADMIN_SUPER_PER_HOUR=10000
RATE_LIMIT_ADMIN_SUPER_BURST=300

# AI Endpoints (cost-controlled)
RATE_LIMIT_AI_PER_MINUTE=10
RATE_LIMIT_AI_PER_HOUR=300
RATE_LIMIT_AI_BURST=15

# Webhooks (external services)
RATE_LIMIT_WEBHOOK_PER_MINUTE=100
RATE_LIMIT_WEBHOOK_PER_HOUR=5000
RATE_LIMIT_WEBHOOK_BURST=200
```

---

### 2. Customer Frontend (apps/customer/.env.local)

```bash
# ==========================================
# APP CONFIGURATION (REQUIRED)
# ==========================================
NODE_ENV=production  # Options: development | production | test
NEXT_PUBLIC_APP_URL=https://myhibachichef.com
NEXT_PUBLIC_APP_NAME=MyHibachi


# ==========================================
# API CONFIGURATION (REQUIRED)
# ==========================================
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_AI_API_URL=https://ai.myhibachichef.com


# ==========================================
# STRIPE PAYMENT (REQUIRED)
# ==========================================
# Public key (safe to expose in client)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_PUBLISHABLE_KEY_HERE

# Secret keys (server-side only - NEVER expose to client)
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_TEST_WEBHOOK_SECRET_HERE


# ==========================================
# ZELLE CONFIGURATION (OPTIONAL)
# ==========================================
NEXT_PUBLIC_ZELLE_ENABLED=true
NEXT_PUBLIC_ZELLE_EMAIL=pay@myhibachichef.com
NEXT_PUBLIC_ZELLE_PHONE=+19167408768


# ==========================================
# VENMO CONFIGURATION (OPTIONAL)
# ==========================================
NEXT_PUBLIC_VENMO_ENABLED=true
NEXT_PUBLIC_VENMO_USERNAME=@myhibachichef


# ==========================================
# ANALYTICS & MONITORING (OPTIONAL)
# ==========================================
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HOTJAR_ID=XXXXXX
VERCEL_URL=auto-generated-by-vercel


# ==========================================
# FEATURE FLAGS
# ==========================================
NEXT_PUBLIC_MAINTENANCE_MODE=false
NEXT_PUBLIC_BOOKING_ENABLED=true
NEXT_PUBLIC_AI_CHAT_ENABLED=true


# ==========================================
# AUTHENTICATION (REQUIRED)
# ==========================================
# Generate with: openssl rand -base64 32
NEXTAUTH_SECRET=your-nextauth-secret-min-32-chars-REQUIRED-CHANGE-THIS-123456789012
NEXTAUTH_URL=https://myhibachichef.com


# ==========================================
# EMAIL SERVICE (OPTIONAL)
# ==========================================
RESEND_API_KEY=re_YOUR_RESEND_API_KEY_HERE


# ==========================================
# RATE LIMITING (OPTIONAL)
# ==========================================
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
```

---

### 3. Admin Frontend (apps/admin/.env.local)

```bash
# Same as customer app, but with admin-specific URL
NODE_ENV=production
NEXT_PUBLIC_APP_URL=https://admin.myhibachichef.com
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXTAUTH_SECRET=<same-as-customer-app>
NEXTAUTH_URL=https://admin.myhibachichef.com

# Add same Stripe, Analytics, etc. as customer app
```

---

## 🚀 SETUP INSTRUCTIONS

### 1. Create .env Files
```bash
# Backend
cd apps/backend
cp .env.example .env
# Edit .env and fill in values

# Customer Frontend
cd apps/customer
touch .env.local
# Copy variables from this guide

# Admin Frontend
cd apps/admin
touch .env.local
# Copy variables from this guide
```

### 2. Generate Secure Keys
```bash
# For SECRET_KEY and ENCRYPTION_KEY
openssl rand -hex 32

# For NEXTAUTH_SECRET
openssl rand -base64 32

# Use different keys for each!
```

### 3. Get API Keys

#### Stripe
1. Go to https://dashboard.stripe.com/apikeys
2. Copy "Publishable key" → `STRIPE_PUBLISHABLE_KEY`
3. Copy "Secret key" → `STRIPE_SECRET_KEY`
4. Go to https://dashboard.stripe.com/webhooks
5. Create webhook → Copy secret → `STRIPE_WEBHOOK_SECRET`

#### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy → `OPENAI_API_KEY`

#### RingCentral
1. Go to https://developers.ringcentral.com/my-account.html
2. Create app
3. Copy credentials

### 4. Verify Setup
```bash
# Check backend can start
cd apps/backend/src
python -m uvicorn main:app --reload

# Check frontend can build
cd apps/customer
npm run build
```

---

## ⚠️ SECURITY WARNINGS

### NEVER commit these files:
- ❌ `.env`
- ❌ `.env.local`
- ❌ `.env.production`
- ❌ Any file with actual secrets

### ALWAYS use placeholders in:
- ✅ `.env.example`
- ✅ `.env.template`
- ✅ Documentation files

### Key Length Requirements:
- `SECRET_KEY`: Minimum 32 characters
- `ENCRYPTION_KEY`: Minimum 32 characters
- `NEXTAUTH_SECRET`: Minimum 32 characters

### Stripe Key Formats:
- Test Secret: `sk_test_51...` (99+ chars)
- Live Secret: `sk_live_51...` (99+ chars)
- Test Public: `pk_test_...` (99+ chars)
- Live Public: `pk_live_...` (99+ chars)
- Webhook: `whsec_...` (32+ chars)

---

## 🔍 TROUBLESHOOTING

### "SECRET_KEY must be at least 32 characters"
```bash
# Generate new key
openssl rand -hex 32
# Copy output to SECRET_KEY in .env
```

### "Database connection failed"
```bash
# SQLite (development)
DATABASE_URL=sqlite:///./myhibachi.db

# PostgreSQL (production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
```

### "Stripe key invalid"
```bash
# Verify key format
echo $STRIPE_SECRET_KEY | grep -E "^sk_(test|live)_"

# Test key with curl
curl https://api.stripe.com/v1/customers -u $STRIPE_SECRET_KEY:
```

### "NEXTAUTH_SECRET not set"
```bash
# Generate secret
openssl rand -base64 32

# Add to .env.local
echo "NEXTAUTH_SECRET=$(openssl rand -base64 32)" >> .env.local
```

---

## 📚 REFERENCES

- **Stripe Documentation:** https://stripe.com/docs/keys
- **OpenAI API Keys:** https://platform.openai.com/api-keys
- **RingCentral Docs:** https://developers.ringcentral.com/
- **Next.js Environment Variables:** https://nextjs.org/docs/basic-features/environment-variables
- **FastAPI Settings:** https://fastapi.tiangolo.com/advanced/settings/

---

**Status:** ✅ Complete environment variables guide  
**Last Updated:** October 26, 2025  
**Maintained By:** Development Team
