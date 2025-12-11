# My Hibachi - Project Context & Setup Summary

**Last Updated:** December 10, 2025 **Purpose:** Reference document
for AI assistants and new team members

---

## 🏗️ Project Overview

My Hibachi is a **full-stack booking system** for hibachi catering
services.

### Tech Stack

| Layer             | Technology              | Location                                    |
| ----------------- | ----------------------- | ------------------------------------------- |
| Customer Frontend | Next.js 15 (App Router) | `apps/customer/`                            |
| Admin Frontend    | Next.js 15 (App Router) | `apps/admin/`                               |
| Backend API       | FastAPI (Python 3.11+)  | `apps/backend/`                             |
| Database          | PostgreSQL              | External                                    |
| Cache             | Redis                   | External                                    |
| Shared Packages   | TypeScript              | `packages/*` (types, api-client, utils, ui) |

---

## 🌳 Branch Strategy

```
main (production) ← Only deploy-ready code
  │
  └── dev (staging/integration) ← Test before production
        │
        └── feature/batch-X-* ← Development work
```

| Branch      | Purpose             | Auto-deploy              |
| ----------- | ------------------- | ------------------------ |
| `main`      | Production          | Vercel → Production URLs |
| `dev`       | Integration/Testing | Vercel → Preview URLs    |
| `feature/*` | Development         | PR Preview URLs          |

---

## 🚀 Deployment Architecture

### Frontend (Vercel)

| App      | Vercel Project | Root Directory  | Production URL      |
| -------- | -------------- | --------------- | ------------------- |
| Customer | `mh-customer`  | `apps/customer` | myhibachi.com       |
| Admin    | `mh-admin`     | `apps/admin`    | admin.myhibachi.com |

**Environment Variables (Vercel):**

```
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_APP_URL=https://myhibachi.com
```

### Backend (VPS/Plesk)

| Component | Domain                | Server          |
| --------- | --------------------- | --------------- |
| API       | api.myhibachichef.com | VPS with Plesk  |
| Database  | PostgreSQL            | Supabase or VPS |
| Cache     | Redis                 | VPS             |

---

## 🎛️ Feature Flags System

Feature flags are defined in `apps/backend/src/core/config.py`.

### How It Works:

```python
# In config.py - Default is OFF (safe)
FEATURE_FLAG_BETA_STRIPE_CONNECT: bool = False

# In endpoint code - Check before executing
if settings.FEATURE_FLAG_BETA_STRIPE_CONNECT:
    # Execute new payment flow
else:
    # Use old flow or return "not available"
```

### Current Feature Flags (illustrative - check config.py for actual values):

> **Note:** Some flags check environment variables; defaults may vary
> by environment.

| Flag                                       | Purpose              | Safe Default |
| ------------------------------------------ | -------------------- | ------------ |
| `FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR`    | New travel fee logic | env-based    |
| `FEATURE_FLAG_BETA_DYNAMIC_PRICING`        | Demand-based pricing | False        |
| `FEATURE_FLAG_NEW_BOOKING_VALIDATION`      | Enhanced validation  | env-based    |
| `FEATURE_FLAG_V2_DEPOSIT_CALCULATION`      | New deposit logic    | False        |
| `FEATURE_FLAG_BETA_STRIPE_CONNECT`         | Multi-chef payments  | False        |
| `FEATURE_FLAG_NEW_RINGCENTRAL_INTEGRATION` | SMS integration      | False        |
| `FEATURE_FLAG_ENABLE_RATE_LIMITING`        | API rate limits      | env-based    |
| `FEATURE_FLAG_ENABLE_AUDIT_LOGGING`        | Compliance logging   | False        |

### Enabling a Flag:

1. In `.env` file: `FEATURE_FLAG_BETA_STRIPE_CONNECT=true`
2. Or in environment variables on server
3. Restart the application

---

## 📦 Batch Deployment Strategy

Work is organized into batches. Each batch = one PR to main.

| Batch | Focus                           | Status                             |
| ----- | ------------------------------- | ---------------------------------- |
| 0     | Repo cleanup, branch strategy   | ✅ Complete                        |
| 1     | Core booking + security + CI/CD | ✅ In dev (pending deploy to main) |
| 2     | Payment processing (Stripe)     | 🔜 Next                            |
| 3     | Core AI                         | Planned                            |
| 4     | Communications (SMS, Voice)     | Planned                            |
| 5     | Advanced AI + Marketing         | Planned                            |
| 6     | AI Training + Scaling           | Planned                            |

---

## 🔧 Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL
- Redis

### Quick Start

```bash
# Install all dependencies (from root)
npm install

# Run customer frontend
cd apps/customer && npm run dev  # http://localhost:3000

# Run admin frontend
cd apps/admin && npm run dev  # http://localhost:3001

# Run backend API
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

---

## 🧪 Testing

### Frontend Tests (Vitest)

```bash
cd apps/customer
npm run test        # Run tests
npm run test:ui     # Interactive UI
```

### Backend Tests (Pytest)

```bash
cd apps/backend
pytest tests/ -v
```

### CI/CD (GitHub Actions)

- Workflow: `.github/workflows/deployment-testing.yml`
- Runs on: Push to `main`/`dev`, PRs to `main`/`dev`
- Jobs: Frontend Tests, Backend Tests, Lint Check

---

## 📁 Key File Locations

| What                 | Where                                               |
| -------------------- | --------------------------------------------------- |
| Backend config       | `apps/backend/src/core/config.py`                   |
| Feature flags        | `apps/backend/src/core/config.py` (FEATURE*FLAG*\*) |
| API routes           | `apps/backend/src/routers/v1/`                      |
| Business logic       | `apps/backend/src/services/`                        |
| Database models      | `apps/backend/src/db/models/`                       |
| Frontend API client  | `apps/customer/src/lib/api.ts`                      |
| Shared types         | `packages/types/src/`                               |
| CI/CD workflow       | `.github/workflows/deployment-testing.yml`          |
| Copilot instructions | `.github/instructions/`                             |

---

## 🔐 Security

- **Secrets:** Never commit `.env` files
- **API Keys:** Store in environment variables
- **Feature Flags:** New features OFF by default
- **Branch Protection:** PRs required for `main` and `dev`

---

## 📝 For AI Assistants

When starting a new session:

1. **Read `.github/instructions/00-BOOTSTRAP.instructions.md`** first
2. **Check `CURRENT_BATCH_STATUS.md`** for active work
3. **Follow the batch deployment rules** in
   `04-BATCH_DEPLOYMENT.instructions.md`
4. **Feature flags are critical** - all new behavior behind flags

### Key Principles:

- Production must always stay stable
- Unfinished features behind feature flags
- Tests must pass before merge
- One PR per batch to main
- Fix existing files, don't create duplicates
