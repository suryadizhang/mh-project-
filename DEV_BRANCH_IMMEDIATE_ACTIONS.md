# Dev Branch Deployment Plan - IMMEDIATE ACTIONS

**Branch**: `nuclear-refactor-clean-architecture` (dev) **Status**: ✅
Code Ready, All Tests Passing **Goal**: Continue development with
proper configuration

---

## ⚠️ Key Understanding

We are on the **DEV BRANCH** - NOT deploying to production yet.

- ✅ Code fixes complete
- ✅ Bug audit complete
- ✅ Security hardened
- 🔄 Continue development with proper dev setup
- 🚀 Production deployment comes later (with API key rotation)

---

## 🎯 IMMEDIATE TASKS (Dev Environment Setup)

### 1. ⏳ Configure `.env.local` for Development (30 min)

**Why**: Need proper local development environment configuration

**Action**:

```bash
# Create .env.local files for local development
# These are already in .gitignore - safe to use test keys

# apps/customer/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_... (current test key is fine)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIza... (current test key is fine)
NEXT_PUBLIC_BUSINESS_PHONE=(916) 740-8768
NEXT_PUBLIC_BUSINESS_EMAIL=info@myhibachi.com
NEXT_PUBLIC_ZELLE_EMAIL=myhibachichef@gmail.com

# Feature flags for DEV (enable new features)
NEXT_PUBLIC_FEATURE_AI_BOOKING_V3=true
NEXT_PUBLIC_FEATURE_SMS_CONSENT=true
NEXT_PUBLIC_FEATURE_MATH_CAPTCHA=true
NEXT_PUBLIC_FEATURE_2FA_VERIFICATION=true

# apps/admin/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3001
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_... (same as customer)

# apps/backend/.env.local
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_LOCAL_PASSWORD@localhost:5432/myhibachi_dev
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-jwt-secret-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production
STRIPE_SECRET_KEY=sk_test_... (current test key is fine)
OPENAI_API_KEY=sk-proj-... (current test key is fine)
GOOGLE_MAPS_SERVER_KEY=AIza... (current test key is fine)

# Feature flags for DEV
FEATURE_FLAG_AI_BOOKING_V3=true
FEATURE_FLAG_TRAVEL_FEE_V2=false  # Keep disabled until tested
FEATURE_FLAG_AUDIT_LOGGING=true
```

**Verification**:

```bash
# Test customer site locally
cd apps/customer
npm run dev
# Should start on http://localhost:3000

# Test admin site locally
cd apps/admin
npm run dev
# Should start on http://localhost:3001

# Test backend locally
cd apps/backend
python -m uvicorn src.main:app --reload
# Should start on http://localhost:8000
```

**Estimated Time**: 30 minutes **Status**: ⏳ TODO

---

### 2. ⏳ Run Local Integration Tests (30 min)

**Why**: Verify everything works in local dev environment

**Action**:

```bash
# 1. Start backend server
cd apps/backend
python -m uvicorn src.main:app --reload &

# 2. Run backend tests
pytest tests/ -v

# 3. Test critical endpoints manually
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/config/health

# 4. Test frontend builds
cd apps/customer
npm run build

cd apps/admin
npm run build
```

**Success Criteria**:

- All pytest tests passing
- Health endpoints returning 200
- Frontend builds successfully
- No TypeScript errors

**Estimated Time**: 30 minutes **Status**: ⏳ TODO

---

### 3. ⏳ Database Migrations (Local) (30 min)

**Why**: Ensure database schema is up-to-date for development

**Action**:

```bash
# 1. Verify local database is running
psql -h localhost -U postgres -d myhibachi_dev

# 2. Run pending migrations
cd apps/backend
alembic upgrade head

# 3. Verify critical tables exist
psql -h localhost -U postgres -d myhibachi_dev -c "\dt"
# Should see:
# - bookings
# - customers
# - audit_logs
# - terms_acknowledgments
# - sms_consents
# - ip_verifications

# 4. Test migration rollback (safety check)
alembic downgrade -1
alembic upgrade head
```

**Success Criteria**:

- All migrations applied successfully
- All expected tables exist
- Rollback/upgrade works

**Estimated Time**: 30 minutes **Status**: ⏳ TODO

---

### 4. ⏳ Feature Flag Configuration (15 min)

**Why**: Enable new features in dev, keep disabled in production (when
we deploy)

**Action**:

Create feature flag configuration file:

```typescript
// apps/customer/src/lib/featureFlags.ts
export const DEV_FEATURE_FLAGS = {
  AI_BOOKING_V3: true,
  SMS_CONSENT: true,
  MATH_CAPTCHA: true,
  TWO_FACTOR_AUTH: true,
  TRAVEL_FEE_V2: false, // Not ready yet
} as const;

export const PROD_FEATURE_FLAGS = {
  AI_BOOKING_V3: false, // Enable gradually
  SMS_CONSENT: true,
  MATH_CAPTCHA: true,
  TWO_FACTOR_AUTH: true,
  TRAVEL_FEE_V2: false,
} as const;

export const FEATURE_FLAGS =
  process.env.NODE_ENV === 'production'
    ? PROD_FEATURE_FLAGS
    : DEV_FEATURE_FLAGS;
```

```python
# apps/backend/src/core/feature_flags.py
import os

DEV_FEATURE_FLAGS = {
    "AI_BOOKING_V3": True,
    "TRAVEL_FEE_V2": False,
    "AUDIT_LOGGING": True,
    "IP_VERIFICATION": True,
}

PROD_FEATURE_FLAGS = {
    "AI_BOOKING_V3": False,  # Enable gradually
    "TRAVEL_FEE_V2": False,
    "AUDIT_LOGGING": True,
    "IP_VERIFICATION": True,
}

FEATURE_FLAGS = (
    PROD_FEATURE_FLAGS
    if os.getenv("ENVIRONMENT") == "production"
    else DEV_FEATURE_FLAGS
)
```

**Estimated Time**: 15 minutes **Status**: ⏳ TODO

---

## 🟢 OPTIONAL - Nice to Have for Dev

### 5. ⏸️ Setup Local Monitoring (SKIP FOR NOW)

**Why**: Not critical for dev environment

**Later**: Set up when deploying to staging/production

---

### 6. ⏸️ GSM Integration (SKIP FOR NOW)

**Why**: Not needed for local development

**When**: Set up GSM when deploying to staging environment

**Local Dev**: Use `.env.local` files with test keys (already in
.gitignore)

---

### 7. ⏸️ Security Audit (SKIP FOR NOW)

**Why**: Already completed comprehensive bug audit (0 critical bugs)

**When**: Re-run before production deployment

---

## 📋 Current Status Summary

### ✅ COMPLETED

- [x] Code corruption fixed
- [x] Comprehensive bug audit (0 CRITICAL, 0 HIGH, 0 MEDIUM)
- [x] All tests passing (24/24 - 100%)
- [x] Security hardened (no secrets in git)
- [x] Enterprise standards implemented
- [x] Deployment documentation created
- [x] Pushed to dev branch

### ⏳ TODO (Development Setup - 2 hours)

- [ ] Configure `.env.local` files (30 min)
- [ ] Run local integration tests (30 min)
- [ ] Apply database migrations locally (30 min)
- [ ] Configure feature flags (15 min)
- [ ] Test all features locally (15 min)

### ⏸️ DEFERRED (Until Staging/Production)

- [ ] API key rotation (production only)
- [ ] GSM integration (staging/production)
- [ ] Monitoring setup (staging/production)
- [ ] CDN configuration (production)
- [ ] Load testing (staging)

---

## 🎯 Next 2 Hours - Action Plan

### Hour 1: Configuration

1. Create `.env.local` files for all 3 apps (30 min)
2. Configure feature flags (15 min)
3. Test frontend builds (15 min)

### Hour 2: Testing & Verification

1. Apply database migrations (30 min)
2. Run integration tests (30 min)

**Total Time**: 2 hours **Outcome**: Fully functional local
development environment

---

## 🚀 After Dev Setup Complete

**Continue Development**:

- Build new features behind feature flags
- Write tests for new code
- Use dev branch for experimentation

**When Ready for Staging**:

- Create `.env.staging` files
- Set up GSM for staging secrets
- Deploy to staging environment
- Run staging tests

**When Ready for Production**:

- Rotate ALL API keys (fresh production keys)
- Set up GSM for production secrets
- Deploy to production with flags OFF
- Gradually enable features via flags

---

## 📞 Quick Reference

**Current Environment**: Development (local) **Current Branch**:
`nuclear-refactor-clean-architecture` **Test Keys**: Safe to use
(rotating before production) **Next Milestone**: Complete local dev
setup (2 hours) **Future Milestone**: Staging deployment (1-2 weeks)

---

**Remember**: We're on DEV, not production. Test keys are fine. Focus
on functionality, not production-grade security yet.
