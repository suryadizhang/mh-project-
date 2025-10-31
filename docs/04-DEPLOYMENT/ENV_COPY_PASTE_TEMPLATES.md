# 🚀 Copy-Paste Environment Templates

**Quick Setup:** Copy these templates directly into your `.env` files

---

## 📁 File 1: Backend API

**Location:** `apps/backend/.env`

```bash
# ==========================================
# COPY THIS TEMPLATE TO apps/backend/.env
# REPLACE VALUES WITH YOUR ACTUAL CREDENTIALS
# ==========================================

# ==========================================
# 🔴 CRITICAL - Required to Start
# ==========================================

# Database (choose one)
# Option 1: SQLite (development only)
DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db

# Option 2: PostgreSQL (recommended)
# DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/myhibachi

# Redis
REDIS_URL=redis://localhost:6379/0

# Security Keys - CHANGE THESE!
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=CHANGE-ME-your-secret-key-min-32-chars-1234567890abcdef
ENCRYPTION_KEY=CHANGE-ME-your-encryption-key-min-32-chars-1234567890ab

# Application
ENVIRONMENT=development
DEBUG=true
API_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ==========================================
# 🟡 IMPORTANT - Core Features (Optional)
# ==========================================

# Stripe Payments - Get from https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# OpenAI - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Email (Gmail SMTP)
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=True
FROM_EMAIL=your-gmail@gmail.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30

# Cloudinary Images - Get from https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Customer Review URLs
CUSTOMER_APP_URL=http://localhost:3000
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-your-city
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupons
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000

# ==========================================
# 🟢 OPTIONAL - Enhanced Features
# ==========================================

# RingCentral SMS - Get from https://developers.ringcentral.com/
RC_CLIENT_ID=your-ringcentral-client-id
RC_CLIENT_SECRET=your-ringcentral-client-secret
RC_JWT_TOKEN=your-ringcentral-jwt-token
RC_WEBHOOK_SECRET=your-ringcentral-webhook-secret
RC_SMS_FROM=+19167408768
RC_SERVER_URL=https://platform.ringcentral.com

# Plaid Banking - Get from https://dashboard.plaid.com/team/keys
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox

# Meta (Facebook/Instagram) - Get from https://developers.facebook.com/apps/
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_VERIFY_TOKEN=your-meta-verify-token
META_PAGE_ACCESS_TOKEN=your-meta-page-access-token

# Google Business - Get from https://console.cloud.google.com/
GOOGLE_CLOUD_PROJECT=your-google-cloud-project
GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json
GBP_ACCOUNT_ID=your-google-business-account-id
GBP_LOCATION_ID=your-google-business-location-id

# Sentry Error Tracking - Get from https://sentry.io/
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/your-project-id
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Business Information (PUBLIC DATA)
BUSINESS_NAME=my Hibachi LLC
BUSINESS_EMAIL=cs@myhibachichef.com
BUSINESS_PHONE=+19167408768
BUSINESS_CITY=Fremont
BUSINESS_STATE=California
SERVICE_AREAS=Sacramento, Bay Area, Central Valley

# AI Settings
ENABLE_AI_AUTO_REPLY=True
AI_CONFIDENCE_THRESHOLD=80

# Business Rules
QUIET_HOURS_START=21
QUIET_HOURS_END=8
DEFAULT_TIMEZONE=America/Los_Angeles
MAX_SMS_PER_THREAD=3

# Rate Limiting
RATE_LIMIT_PUBLIC_PER_MINUTE=20
RATE_LIMIT_PUBLIC_PER_HOUR=1000
RATE_LIMIT_PUBLIC_BURST=30
RATE_LIMIT_ADMIN_PER_MINUTE=100
RATE_LIMIT_ADMIN_PER_HOUR=5000
RATE_LIMIT_ADMIN_BURST=150
RATE_LIMIT_ADMIN_SUPER_PER_MINUTE=200
RATE_LIMIT_ADMIN_SUPER_PER_HOUR=10000
RATE_LIMIT_ADMIN_SUPER_BURST=300
RATE_LIMIT_AI_PER_MINUTE=10
RATE_LIMIT_AI_PER_HOUR=300
RATE_LIMIT_AI_BURST=15
RATE_LIMIT_WEBHOOK_PER_MINUTE=100
RATE_LIMIT_WEBHOOK_PER_HOUR=5000
RATE_LIMIT_WEBHOOK_BURST=200

# Database Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=False

# Access Token Expiry
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📁 File 2: Customer Frontend

**Location:** `apps/customer/.env.local`

```bash
# ==========================================
# COPY THIS TEMPLATE TO apps/customer/.env.local
# REPLACE VALUES WITH YOUR ACTUAL CREDENTIALS
# ==========================================

# ==========================================
# 🔴 CRITICAL - Required
# ==========================================

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# ==========================================
# 🟡 IMPORTANT - Core Features
# ==========================================

# Stripe Payments - Get from https://dashboard.stripe.com/test/apikeys
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE

# ==========================================
# 🟢 OPTIONAL - Enhanced Features
# ==========================================

# Alternative Payments
NEXT_PUBLIC_ZELLE_EMAIL=myhibachichef@gmail.com
NEXT_PUBLIC_VENMO_USERNAME=@myhibachichef
NEXT_PUBLIC_CASHAPP_USERNAME=$myhibachichef

# Analytics - Get from https://analytics.google.com/
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HOTJAR_ID=1234567

# Review URLs
NEXT_PUBLIC_YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef
NEXT_PUBLIC_GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Business Information (PUBLIC)
NEXT_PUBLIC_BUSINESS_PHONE=(916) 740-8768
NEXT_PUBLIC_BUSINESS_EMAIL=info@myhibachi.com
NEXT_PUBLIC_BUSINESS_NAME=My Hibachi LLC

# Feature Flags
NEXT_PUBLIC_MAINTENANCE_MODE=false
NEXT_PUBLIC_BOOKING_ENABLED=true
NEXT_PUBLIC_AI_CHAT_ENABLED=true

# Environment
NODE_ENV=development
```

---

## 📁 File 3: Admin Frontend

**Location:** `apps/admin/.env.local`

```bash
# ==========================================
# COPY THIS TEMPLATE TO apps/admin/.env.local
# REPLACE VALUES WITH YOUR ACTUAL CREDENTIALS
# ==========================================

# ==========================================
# 🔴 CRITICAL - Required
# ==========================================

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8002

# ==========================================
# 🟡 IMPORTANT - Core Features
# ==========================================

# Authentication (Auth0) - Get from https://manage.auth0.com/
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain.auth0.com
NEXT_PUBLIC_AUTH_CLIENT_ID=your_auth_client_id

# ==========================================
# 🟢 OPTIONAL - Enhanced Features
# ==========================================

# WebSocket
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Analytics - Get from https://analytics.google.com/
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Social Media
NEXT_PUBLIC_FB_PAGE_ID=your_facebook_page_id
NEXT_PUBLIC_FB_APP_ID=your_facebook_app_id
NEXT_PUBLIC_IG_USERNAME=@your_instagram_username

# Email Service (Resend) - Get from https://resend.com/api-keys
RESEND_API_KEY=re_your_resend_api_key_here

# Environment
NODE_ENV=development
```

---

## 📁 File 4: AI API (Optional)

**Location:** `apps/ai-api/.env`

```bash
# ==========================================
# COPY THIS TEMPLATE TO apps/ai-api/.env
# REPLACE VALUES WITH YOUR ACTUAL CREDENTIALS
# ==========================================
# NOTE: If using integrated AI in backend, this file is optional

# ==========================================
# 🟡 IMPORTANT - AI Features
# ==========================================

# OpenAI - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY_HERE

# ==========================================
# 🟢 OPTIONAL - Configuration
# ==========================================

# Application Configuration
API_PORT=8002
APP_ENV=development
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Chat Configuration
MAX_CONVERSATION_LENGTH=10
DEFAULT_MODEL=gpt-3.5-turbo
MAX_TOKENS=500

# Rate Limiting
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_PERIOD=60

# Feature Flags
ENABLE_CONVERSATION_MEMORY=true
ENABLE_MENU_RECOMMENDATIONS=true
```

---

## 🔐 Generate Secure Keys

Run these commands to generate secure keys:

```bash
# Generate SECRET_KEY (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate 64-character keys (production)
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## ✅ Quick Validation

After copying the templates:

```bash
# 1. Test Backend Configuration
cd apps/backend
python -c "from core.config import get_settings; settings = get_settings(); print('✅ Backend config valid!')"

# 2. Test Customer Frontend Build
cd apps/customer
npm run build

# 3. Test Admin Frontend Build
cd apps/admin
npm run build

# 4. Start All Services
npm run dev:all
```

---

## 🎯 Minimum Setup (No External Services)

If you just want to run the system locally without any external services:

### apps/backend/.env (minimal)
```bash
DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-at-least-32-characters-long-for-security
ENCRYPTION_KEY=dev-encryption-key-at-least-32-characters-long
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENVIRONMENT=development
DEBUG=true
```

### apps/customer/.env.local (minimal)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### apps/admin/.env.local (minimal)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8002
```

**Result:** System runs but without payments, AI, email, or images.

---

## 🚀 Production Template

For production deployment, update these values:

### Backend
```bash
# Change to production database
DATABASE_URL=postgresql+asyncpg://user:STRONG_PASSWORD@prod-host:5432/myhibachi

# Change to production Redis
REDIS_URL=redis://prod-redis-host:6379/0

# Generate NEW strong keys (64+ chars)
SECRET_KEY=<64-random-characters>
ENCRYPTION_KEY=<64-random-characters>

# Update to production URLs
CORS_ORIGINS=https://myhibachichef.com,https://admin.myhibachichef.com
CUSTOMER_APP_URL=https://myhibachichef.com

# Set production environment
ENVIRONMENT=production
DEBUG=False

# Use LIVE Stripe keys
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET
```

### Customer Frontend
```bash
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_APP_URL=https://myhibachichef.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY_HERE
NODE_ENV=production
```

### Admin Frontend
```bash
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_AI_API_URL=https://ai.myhibachichef.com
NODE_ENV=production
```

---

## 📚 Related Documentation

- [COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md](./COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md) - Full reference
- [ENV_VARS_QUICK_REFERENCE.md](./ENV_VARS_QUICK_REFERENCE.md) - Quick commands
- [ENV_SETUP_CHECKLIST.md](./ENV_SETUP_CHECKLIST.md) - Interactive checklist
- [LOCAL_DEVELOPMENT_SETUP.md](./LOCAL_DEVELOPMENT_SETUP.md) - Setup guide

---

## 🆘 Troubleshooting

### "File not found" errors
```bash
# Make sure you're in the project root
cd "c:\Users\surya\projects\MH webapps"

# Then navigate to specific app
cd apps/backend    # or apps/customer or apps/admin
```

### "Cannot parse .env file"
- Check for spaces around `=` (should be `KEY=value`, not `KEY = value`)
- Check for unquoted values with spaces (use `KEY="value with spaces"`)
- Check for missing closing quotes

### "Invalid environment configuration"
- Run validation: `python -c "from core.config import get_settings; get_settings()"`
- Check error message for specific missing/invalid variable
- Verify key formats (Stripe keys, database URLs, etc.)

---

**Last Updated:** October 26, 2025  
**Next Steps:** Copy templates → Replace values → Test → Deploy
