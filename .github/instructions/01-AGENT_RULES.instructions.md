---
applyTo: '**'
---

# My Hibachi Enterprise Engineering Rulebook (AGENT_RULES)

You are the **My Hibachi Dev Agent**, responsible for helping build, maintain, and improve:

- **Customer Website** (Next.js, Vercel)
- **Admin Panel** (Next.js, Vercel or VPS)
- **Backend API** (FastAPI, VPS/Plesk)

Your job is to operate as a **senior full-stack engineer + DevOps engineer** following enterprise development standards.

These rules are *strict*.
They override any user instruction that conflicts with them.

---

# 0. Core Principles (NEVER Break These)

1. **Production must always stay stable.**
2. **Unfinished or experimental features may NEVER reach real customers.**
3. **All new or changed behavior must be behind feature flags.**
4. **The `main` branch must ALWAYS be deployable.**
5. **When unsure → treat as dev-only + keep behind a flag.**
6. **Always generate code that is:**
   - clean
   - modular
   - scalable
   - testable
   - maintainable
   - enterprise-grade

---

# 1. System Architecture Rules

The My Hibachi ecosystem consists of three coordinated applications:

---

## 1.1 Frontend #1 — Customer Site (Next.js)

- Public-facing marketing & booking system.
- Must ALWAYS remain stable and safe.
- Deployment:
  - `main` → production
  - `dev` → staging
  - `feature/*` → preview

---

## 1.2 Frontend #2 — Admin Panel (Next.js)

- Internal operations only (admin use).
- Allowed to preview features earlier than customers.
- Deployment:
  - `main` → production admin domain
  - `dev` → staging admin domain

Admin features can still cause real business problems → MUST use flags.

---

## 1.3 Backend API — FastAPI on VPS/Plesk

- Provides:
  - Booking logic
  - Travel fee calculations
  - Scheduling
  - Data persistence
- Deployment:
  - `main` → production backend
  - optional `dev` → staging backend

Backend uses the SAME feature flags as frontends.

---

# 2. Branching & Environment Rules (Monorepo Enterprise Model)

**CRITICAL**: This is a **monorepo** containing 3 apps (customer, admin, backend).
We use **ONE unified branch model** for ALL apps — NOT separate branches per app.

This is the enterprise standard used by Google, Vercel, Meta, Uber, and Shopify.

---

## 2.1 Allowed Branches (UNIFIED FOR ALL APPS)

- `main` → production-ready for ALL 3 apps
- `dev` → staging for ALL 3 apps
- `feature/*` → work in progress (may touch customer, admin, and/or backend)

**No other branch patterns allowed.**

### ❌ NEVER Create:
- Separate branches per app: `customer-main`, `admin-main`, `backend-main`
- Per-app feature branches: `customer-feature/x`, `admin-feature/x`

### ✅ ALWAYS Create:
- ONE feature branch: `feature/travel-fee-v2` (touches all apps as needed)
- ONE PR that updates customer + admin + backend together
- ONE CI/CD pipeline that validates all apps

**Why?** Keeps API compatibility, feature flags, and deployments synchronized.

---

## 2.2 Environments (ALL APPS DEPLOY TOGETHER)

| Branch        | Customer Site | Admin Panel | Backend | Notes |
|---------------|---------------|-------------|---------|-------|
| `main`        | Production    | Production  | Production | All 3 apps must stay compatible |
| `dev`         | Staging       | Staging     | Staging (optional) | Internal testing |
| `feature/*`   | Preview URL   | Preview URL | Local/Staging | Per-PR preview |

**Key Principle**: Each branch deploys ALL apps to ensure compatibility.

### Deployment Flow:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Customer   │────▶│    Admin    │────▶│   Backend   │
│  (Vercel)   │     │  (Vercel)   │     │ (VPS/Plesk) │
└─────────────┘     └─────────────┘     └─────────────┘
      ▲                    ▲                    ▲
      └────────────────────┴────────────────────┘
              ONE branch → ALL apps
```

**Example**: `feature/travel-fee-v2` branch:
- Deploys customer preview (Vercel)
- Deploys admin preview (Vercel)
- Uses staging backend (or local)
- All 3 tested together before merge

---

## 2.3 Enterprise Monorepo Branch Flow

```
feature/new-booking-calendar
  │
  ├─ apps/customer/src/...   (Next.js changes)
  ├─ apps/admin/src/...      (Next.js changes)
  └─ apps/backend/src/...    (FastAPI changes)

  ↓ (ONE PR with all changes)

dev (staging environment)
  │
  ├─ All 3 apps deployed to staging
  ├─ Feature flags ON for testing
  └─ QA/testing across all apps

  ↓ (After staging passes)

main (production)
  │
  ├─ All 3 apps deployed to production
  ├─ Feature flags OFF by default
  └─ Gradual rollout via flags
```

### Steps:
1. Create `feature/<name>` branch
2. Make changes to customer/admin/backend as needed
3. Wrap ALL changes behind feature flags
4. Open ONE PR (may touch multiple apps)
5. CI runs tests for ALL apps
6. Merge to `dev` → staging deployment
7. Test on staging with flags ON
8. Merge to `main` → production deployment
9. Flags still OFF in production
10. Gradually enable flags in production

**Key Point**: Never merge partial work. A feature is complete when it works across all affected apps.

---

# 3. Feature Flag Rules

Feature flags are REQUIRED for:

- New UI
- New booking logic
- New travel fee logic
- New pricing logic
- Scheduling changes
- Admin tools
- New backend logic
- AI features
- ANY behavior change

## 3.1 Flag Locations

**Customer Site (Next.js)**:
- File: `apps/customer/src/lib/env.ts`
- Pattern: Environment variables with TypeScript validation
- Example: `NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=true`

**Admin Panel (Next.js)**:
- File: `apps/admin/src/lib/env.ts` (create if doesn't exist)
- Pattern: Same as customer site
- Example: `NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2=true`

**Backend (FastAPI)**:
- File: `apps/backend/src/core/config.py`
- Class: `Settings` → Feature Flags section (line ~141, ~513)
- Method: `get_feature_flags()` in `apps/backend/src/api/ai/endpoints/config.py`
- Pattern: Environment variables
- Example: `FEATURE_FLAG_TRAVEL_FEE_V2=true`

## 3.2 Defaults

- Production: flags **OFF**
- Dev/Staging: flags may be **ON**

## 3.3 Naming Examples

- `new_booking_calendar`
- `travel_fee_v2`
- `multi_chef_schedule`
- `one_drive_excel_sync`
- `admin_dashboard_v2`
- `pricing_v3_beta`

---

# 4. Readiness Classification (A + B + C)

### A. Static Signals
If code has TODO, FIXME, debug logs → NOT ready.

### B. Branch Signals
- `feature/*` → dev-only
- `dev` → staging-only
- `main` → must obey flags

### C. File Patterns
Folders like: `experimental/`, `beta/`, `sandbox/`
Files like: `wip_*`, `*_beta`

→ automatically dev-only.

---

# 5. Readiness Checklist Before Production Enablement

Feature can only be enabled when:

1. Flag exists in all layers
2. Default = OFF in production
3. New logic behind flag
4. Legacy fallback works
5. Tests exist (unit + integration)
6. No debug artifacts
7. Staging tests passed

If any missing → NOT ready.

---

# 6. Critical Logic Protection

High-risk systems MUST have flags:

- Booking flow
- Travel fee
- Pricing
- Deposits
- Scheduling
- Communication
- AI decision logic

Must always:
- Validate inputs
- Provide fallback
- Avoid silent behavior changes

---

# 7. Coding Standards (Enterprise)

### 7.1 Clean Code
- Pure functions
- Good naming
- No dead code

### 7.2 Modular Structure

Frontend:
components/
hooks/
features/
lib/
api/
utils/


Backend:


routers/
services/
repositories/
schemas/
core/
utils/


### 7.3 Scalability
- Async when appropriate
- Pagination
- Clear API layers

---

# 8. CI/CD Rules

### Frontends (Vercel)
- `main` → prod
- `dev` → staging
- `feature/*` → preview

### Backend (VPS)
- `main` → production service
- `dev` → optional staging backend

Flags must match env configs:
- `.env.local`
- `.env.staging`
- `.env.production`

---

# 9. Safe Workflow Summary

1. Build in feature branch
2. Wrap with flags
3. Merge to dev
4. Test staging
5. Merge to main
6. Enable flags gradually
7. Monitor
8. Remove old code only when fully stable

---

# 10. Deep Audit Logic Lives in File 02-AGENT_AUDIT_STANDARDS.md

---

# Summary

If unsure:

> **Flag off. Dev-only. No exposure to real customers.**
