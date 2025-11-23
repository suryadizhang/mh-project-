# My Hibachi - Quick Onboarding Guide

**Welcome to the My Hibachi project!** This guide will get you up and
running in 15 minutes.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Environment Setup](#environment-setup)
5. [Running the Apps](#running-the-apps)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Useful Resources](#useful-resources)

---

## 🏗️ Project Overview

My Hibachi is a monorepo containing 3 applications:

- **Customer Site** (`apps/customer`) - Next.js 15 + React 19 (Public
  booking site)
- **Admin Panel** (`apps/admin`) - Next.js 15 + React 19 (Internal
  operations)
- **Backend API** (`apps/backend`) - FastAPI + Python 3.13 (Business
  logic)

**Tech Stack:**

- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS
- Backend: Python 3.13, FastAPI, SQLAlchemy 2.0, PostgreSQL
- AI: OpenAI GPT-4, Deepgram, RingCentral
- Infrastructure: Vercel (frontend), VPS/Plesk (backend)

---

## ✅ Prerequisites

1. **Node.js 18+** and **npm 9+**
2. **Python 3.13+** and **pip**
3. **PostgreSQL 14+**
4. **Git**
5. **VS Code** (recommended)

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/suryadizhang/mh-project-.git
cd mh-project-
```

### 2. Install dependencies

**Customer Site:**

```bash
cd apps/customer
npm install
```

**Admin Panel:**

```bash
cd apps/admin
npm install
```

**Backend:**

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

**Customer Site** (`apps/customer/.env.local`):

```bash
# Copy from .env.example
cp .env.example .env.local

# Required variables:
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

**Backend** (`apps/backend/.env`):

```bash
# Database (replace with your actual credentials)
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/myhibachi_dev

# OpenAI (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx

# RingCentral (for SMS/Voice AI - get from developer.ringcentral.com)
RINGCENTRAL_CLIENT_ID=<your_client_id>
RINGCENTRAL_CLIENT_SECRET=<your_client_secret>
RINGCENTRAL_JWT_TOKEN=<your_jwt_token>

# Deepgram (for voice AI - get from deepgram.com)
DEEPGRAM_API_KEY=<your_deepgram_key>

# Stripe (get from dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
```

**See** `ENVIRONMENT_CONFIGURATION.md` for full list of variables.

### 4. Set up the database

```bash
cd apps/backend

# Run migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

---

## 🏃 Running the Apps

### Development Mode (All apps)

**Customer Site:**

```bash
cd apps/customer
npm run dev
# Opens at http://localhost:3000
```

**Admin Panel:**

```bash
cd apps/admin
npm run dev
# Opens at http://localhost:3001
```

**Backend API:**

```bash
cd apps/backend
uvicorn src.main:app --reload --port 8000
# Opens at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Tip:** Run all three in separate terminals for full-stack
development.

---

## 🧪 Testing

### Frontend Tests

```bash
cd apps/customer
npm run test          # Unit tests
npm run test:e2e      # E2E tests (Playwright)
npm run lint          # Linting
npm run typecheck     # TypeScript check
```

### Backend Tests

```bash
cd apps/backend
pytest                          # All tests
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests
pytest --cov=src --cov-report=html  # Coverage report
```

**See** `E2E_QUICK_REFERENCE.md` for detailed testing guide.

---

## 🚢 Deployment

### Staging Deployment

```bash
# Push to dev branch
git checkout dev
git merge feature/your-feature
git push origin dev

# Auto-deploys to:
# - Customer: customer-staging.vercel.app
# - Admin: admin-staging.vercel.app
# - Backend: staging-api.myhibachi.com
```

### Production Deployment

```bash
# Push to main branch (after staging tests pass)
git checkout main
git merge dev
git push origin main

# Auto-deploys to:
# - Customer: myhibachi.com
# - Admin: admin.myhibachi.com
# - Backend: api.myhibachi.com
```

**See** `DEPLOYMENT_QUICK_REFERENCE.md` for deployment commands and
`PRODUCTION_DEPLOYMENT_GUIDE.md` for production checklist.

---

## 📚 Useful Resources

### Quick References

- `AI_V3_QUICK_REFERENCE.md` - AI system guide
- `DEPLOYMENT_QUICK_REFERENCE.md` - Deploy commands
- `E2E_QUICK_REFERENCE.md` - Testing guide
- `MONITORING_API_QUICK_REFERENCE.md` - Monitoring & alerts

### Setup Guides

- `GSM_ENHANCED_VARIABLES_SETUP_GUIDE.md` - Secrets management (Google
  Secret Manager)
- `VOICE_AI_SETUP_GUIDE.md` - Voice AI configuration
- `ENVIRONMENT_CONFIGURATION.md` - All environment variables

### Architecture

- `DATABASE_ARCHITECTURE_BUSINESS_MODEL.md` - Database schema
- `DATABASE_RELATIONSHIP_MAP.md` - DB relationships
- `DEEP_PROJECT_ANALYSIS_NOV_2025.md` - Current architecture

### Strategic Planning

- `IMPLEMENTATION_PLAN_NOV_2025.md` - Roadmap
- `OPERATIONAL_PRIORITY_LIST.md` - Priorities
- `ML_SCALABILITY_PREP_GUIDE.md` - Scale-up plan

### Compliance

- `OPENAI_POLICY_COMPLIANCE_REPORT.md` - AI compliance
- `LEGAL_PROOF_QUICK_REFERENCE.md` - Legal compliance

---

## 🆘 Common Issues

### 1. Database connection failed

**Solution:** Check `DATABASE_URL` in `.env` and ensure PostgreSQL is
running.

### 2. OpenAI API errors

**Solution:** Verify `OPENAI_API_KEY` is valid and has credits.

### 3. Next.js build errors

**Solution:** Delete `.next` folder and `node_modules`, then
reinstall:

```bash
rm -rf .next node_modules
npm install
npm run build
```

### 4. Python import errors

**Solution:** Ensure virtual environment is activated and dependencies
installed:

```bash
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run linters: `npm run lint` (frontend) and `ruff check` (backend)
4. Commit with descriptive message
5. Push and create Pull Request to `dev` branch
6. Wait for CI/CD checks to pass
7. Request review from team lead

**Never push directly to `main` or `dev` branches!**

---

## 📞 Support

- **Technical Issues:** Open GitHub issue
- **Urgent Bugs:** Slack #dev-team channel
- **Questions:** Email dev@myhibachi.com

---

**Last Updated:** November 22, 2025  
**Maintained By:** My Hibachi Development Team
