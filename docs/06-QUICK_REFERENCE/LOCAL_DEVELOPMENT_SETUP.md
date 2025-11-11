# 🚀 MyHibachi Local Development Setup Guide

## Complete Environment Setup for Manual Testing & Development

This guide provides everything you need to run the full MyHibachi stack locally for testing and development.

---

## 📋 **Prerequisites**

### System Requirements
- **Node.js**: >= 20.0.0
- **Python**: >= 3.11.0
- **npm**: >= 10.0.0
- **Docker**: Latest (for database services)
- **Git**: Latest

### Verify Prerequisites
```bash
# Check versions
node --version    # Should be 20+
python --version  # Should be 3.11+
npm --version     # Should be 10+
docker --version  # Latest
```

---

## 🗄️ **Database Setup**

### Option 1: Docker (Recommended)
```bash
# Start PostgreSQL and Redis with Docker
docker-compose --profile development up -d postgres redis

# Verify services
docker ps  # Should show postgres and redis running
```

### Option 2: Local Installation
```bash
# Install PostgreSQL and Redis locally
# PostgreSQL: Create database 'myhibachi'
# Redis: Start on default port 6379
```

---

## 🔧 **Environment Variables Setup**

### 1. Customer Frontend (.env.local)
Create `apps/customer/.env.local`:
```bash
# === CUSTOMER FRONTEND ENVIRONMENT ===

# Stripe Configuration (SAFE - Public keys only)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51ReuiCGdTvr1jDZ2ayoN8Ta4uIUvFTvRtx9QxOw9ejyERYXKvMaY6CXY6ZcwYKs80mEZQg7WezAXnk3azm0UTRje00nUPy0Hxu

# API URLs (Local Development)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8002
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Business Information
NEXT_PUBLIC_BUSINESS_PHONE=(916) 740-8768
NEXT_PUBLIC_BUSINESS_EMAIL=info@myhibachi.com
NEXT_PUBLIC_BUSINESS_NAME=My Hibachi LLC
NEXT_PUBLIC_WEBSITE_URL=https://myhibachi.com

# Payment Settings
NEXT_PUBLIC_PAYMENT_PROCESSING_FEE=0.08
NEXT_PUBLIC_DEPOSIT_AMOUNT=100.00
NEXT_PUBLIC_ZELLE_EMAIL=myhibachichef@gmail.com
NEXT_PUBLIC_VENMO_USERNAME=@myhibachichef
```

### 2. Admin Frontend (.env.local)
Create `apps/admin/.env.local`:
```bash
# === ADMIN FRONTEND ENVIRONMENT ===

# Stripe Configuration (SAFE - Public keys only)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51ReuiCGdTvr1jDZ2ayoN8Ta4uIUvFTvRtx9QxOw9ejyERYXKvMaY6CXY6ZcwYKs80mEZQg7WezAXnk3azm0UTRje00nUPy0Hxu

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application URLs
NEXT_PUBLIC_APP_URL=http://localhost:3001
```

### 3. Main API Backend (.env)
Create `apps/api/.env`:
```bash
# === MAIN API BACKEND ENVIRONMENT ===

# Core Configuration
APP_NAME=MyHibachi Backend API
ENVIRONMENT=development
LOG_LEVEL=info
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/myhibachi
DATABASE_URL_SYNC=postgresql://<username>:<password>@localhost:5432/myhibachi
# Alternative: SQLite for simple testing
# SQLITE_URL=sqlite:///./mh-bookings.db

# Security & Authentication
SECRET_KEY=your-super-secret-jwt-key-for-local-development-only
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:3001"]
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:3001"]

# === EXTERNAL API KEYS (Required for Full Functionality) ===

# Stripe Payment Configuration (TEST KEYS ONLY)
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_TEST_SECRET_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_STRIPE_TEST_PUBLISHABLE_KEY_HERE

# Email Configuration (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=no-reply@myhibachi.com
FROM_EMAIL=your-gmail@gmail.com
DISABLE_EMAIL=false

# RingCentral SMS (Optional)
RINGCENTRAL_CLIENT_ID=your_ringcentral_client_id
RINGCENTRAL_CLIENT_SECRET=your_ringcentral_client_secret
RINGCENTRAL_JWT_TOKEN=your_jwt_token
RINGCENTRAL_SERVER_URL=https://platform.devtest.ringcentral.com

# Application URLs
APP_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
WEBHOOK_PATH=/api/stripe/webhook

# Admin Configuration
ADMIN_EMAIL=admin@myhibachi.com
ADMIN_PHONE=+19167408768

# Alternative Payment Options
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
CASHAPP_USERNAME=$myhibachichef

# Feature Flags
ENABLE_STRIPE_CONNECT=false
ENABLE_AUTOMATIC_TAX=false
ENABLE_SUBSCRIPTIONS=false
ENABLE_WEBSOCKETS=true
ENABLE_RATE_LIMITING=true

# Testing Configuration
TESTING=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BOOKING=5/minute
RATE_LIMIT_WAITLIST=10/minute
RATE_LIMIT_GENERAL=100/minute
```

### 4. AI API Backend (.env)
Create `apps/ai-api/.env`:
```bash
# === AI API BACKEND ENVIRONMENT ===

# OpenAI Configuration (REQUIRED for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

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

## 🔑 **Required External API Keys**

### 🟡 **Critical for Payment Testing**
1. **Stripe Test Keys** (Get from [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys))
   - `STRIPE_SECRET_KEY`: sk_test_...
   - `STRIPE_PUBLISHABLE_KEY`: pk_test_...
   - `STRIPE_WEBHOOK_SECRET`: whsec_... (from webhooks section)

### 🟡 **Critical for AI Features**
2. **OpenAI API Key** (Get from [OpenAI Platform](https://platform.openai.com/api-keys))
   - `OPENAI_API_KEY`: sk-...

### 🟠 **Important for Email Features**
3. **Gmail SMTP** (For email notifications)
   - Enable 2FA on Gmail account
   - Generate App Password in Google Account settings
   - Use App Password as `SMTP_PASSWORD`

### 🔵 **Optional for SMS Features**
4. **RingCentral** (For SMS notifications)
   - Create developer account at [RingCentral Developers](https://developers.ringcentral.com/)
   - Get sandbox credentials

---

## 🚀 **Installation & Startup**

### 1. Install Dependencies
```bash
# Clone and navigate to project
cd "path/to/MH webapps"

# Install root dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd apps/customer && npm install && cd ../..
cd apps/admin && npm install && cd ../..
```

### 2. Start Services

#### Option A: Automated Script (Recommended)
```bash
# Make script executable (Linux/Mac)
chmod +x scripts/start-local.sh

# Start all services
./scripts/start-local.sh
```

#### Option B: Manual Start
```bash
# Terminal 1: Start API Backend
cd apps/api
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start AI API Backend  
cd apps/ai-api
python main.py

# Terminal 3: Start Customer Frontend
cd apps/customer
npm run dev

# Terminal 4: Start Admin Frontend
cd apps/admin
npm run dev -- --port 3001
```

---

## 🌐 **Service URLs**

Once everything is running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Customer Frontend** | http://localhost:3000 | Main customer-facing website |
| **Admin Dashboard** | http://localhost:3001 | Admin management interface |
| **Main API** | http://localhost:8000 | Core backend API |
| **AI API** | http://localhost:8002 | AI chat and recommendations |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System health status |

---

## 🗃️ **Database Setup**

### Run Migrations
```bash
cd apps/api
alembic upgrade head
```

### Create Test Data (Optional)
```bash
# Create admin user
cd apps/api
python -c "
from app.auth import create_admin_user
create_admin_user('admin@myhibachi.com', 'admin123')
print('Admin user created')
"
```

---

## 🧪 **Testing Your Setup**

### 1. Basic Health Checks
```bash
# Test API health
curl http://localhost:8000/health

# Test AI API health
curl http://localhost:8002/health

# Test Frontend (should return HTML)
curl http://localhost:3000
curl http://localhost:3001
```

### 2. Stripe Payment Testing
1. Visit: http://localhost:3000/BookUs
2. Fill out booking form
3. Use Stripe test card: `4242 4242 4242 4242`
4. Any future expiry date, any CVC

### 3. AI Chat Testing
1. Visit: http://localhost:3000
2. Look for chat widget
3. Test AI responses (requires OPENAI_API_KEY)

---

## 🚨 **Troubleshooting**

### Common Issues

**Port Already in Use**
```bash
# Find and kill process on port
lsof -ti:3000 | xargs kill -9  # For port 3000
lsof -ti:8000 | xargs kill -9  # For port 8000
```

**Database Connection Failed**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Start database if stopped
docker-compose up -d postgres
```

**Node.js Version Issues**
```bash
# Use Node Version Manager
nvm install 20
nvm use 20
```

**Python Issues**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 📝 **Development Workflow**

### Daily Development
1. Start database: `docker-compose up -d postgres redis`
2. Start all services: `./scripts/start-local.sh`
3. Develop and test
4. Stop services: `./scripts/stop-local.sh`

### Making Changes
- **Frontend**: Changes auto-reload (hot reload enabled)
- **Backend**: Changes auto-reload (--reload flag enabled)
- **Database**: Use Alembic migrations for schema changes

### Logs & Debugging
- **API Logs**: `logs/api.log`
- **Customer Logs**: `logs/customer.log`
- **Admin Logs**: `logs/admin.log`
- **Browser DevTools**: F12 for frontend debugging

---

## 🔒 **Security Notes**

⚠️ **NEVER commit .env files with real API keys**
⚠️ **Use TEST keys only for local development**
⚠️ **Keep production keys separate and secure**

---

## ✅ **Quick Start Checklist**

- [ ] Install prerequisites (Node.js 20+, Python 3.11+, Docker)
- [ ] Start PostgreSQL & Redis (`docker-compose up -d postgres redis`)
- [ ] Create all .env files with your API keys
- [ ] Install dependencies (`npm install` + `pip install -r requirements.txt`)
- [ ] Run database migrations (`cd apps/api && alembic upgrade head`)
- [ ] Start all services (`./scripts/start-local.sh`)
- [ ] Test URLs: http://localhost:3000, http://localhost:3001, http://localhost:8000
- [ ] Test payment flow with Stripe test card
- [ ] Test AI chat (if OpenAI key configured)

---

🎉 **You're ready to develop and test MyHibachi locally!**

For production deployment, see `DEPLOYMENT_ANALYSIS.md`.