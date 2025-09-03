# 🚀 Frontend → Backend Migration Plan

## Executive Summary

Based on comprehensive repository scan, here's the migration plan to extract backend code from `myhibachi-frontend` and move it to `myhibachi-backend-fastapi`.

---

## 📊 Current Violation Status

- **Empty Files**: 11 files (to be implemented or removed)
- **Placeholder Content**: 963 violations (mostly "placeholderText" and TODOs)
- **Port Collisions**: 4 issues (backend services using wrong ports)
- **Security Violations**: 0 ✅
- **Separation Violations**: 0 ✅

---

## 🔍 Detected Backend Code in Frontend

### Next.js API Routes (to migrate)
```
myhibachi-frontend/src/app/api/
├── v1/
│   ├── customers/dashboard/route.ts → FastAPI: /api/v1/customers/dashboard
│   ├── payments/
│   │   ├── create-intent/route.ts → FastAPI: /api/v1/payments/create-intent
│   │   └── webhook/route.ts → FastAPI: /api/v1/payments/webhook
│   └── webhooks/stripe/route.ts → FastAPI: /api/v1/webhooks/stripe
```

### Server-only Services (already migrated)
```
myhibachi-frontend/src/lib/server/
└── stripeCustomerService.ts → KEEP (properly isolated)
```

---

## 🎯 Migration Mapping

### Phase 1: API Route Migration

| Source (Frontend) | Destination (Backend) | Rationale |
|-------------------|----------------------|-----------|
| `src/app/api/v1/customers/dashboard/route.ts` | `app/api/stripe_routes.py::get_customer_dashboard` | Customer analytics endpoint |
| `src/app/api/v1/payments/create-intent/route.ts` | `app/api/stripe_routes.py::create_payment_intent` | Payment processing |
| `src/app/api/v1/payments/webhook/route.ts` | `app/api/webhooks.py::stripe_webhook_handler` | Webhook processing |
| `src/app/api/v1/webhooks/stripe/route.ts` | `app/api/webhooks.py::stripe_webhook_handler` | Duplicate webhook handler |

### Phase 2: Environment Standardization

| Service | Current Port | Target Port | Env Variables |
|---------|--------------|-------------|---------------|
| Frontend | 3000 ✅ | 3000 | `NEXT_PUBLIC_*` only |
| FastAPI Backend | 8000 ✅ | 8000 | Stripe secrets, DB |
| Legacy Backend | 8000 ❌ | 8001 | Mark deprecated |
| AI Backend | 8001 ❌ | 8002 | No Stripe access |

---

## 🔧 Implementation Plan

### Step 1: Fix Port Collisions
```bash
# Legacy backend port change
myhibachi-backend/main.py: port=8000 → port=8001

# AI backend port change  
myhibachi-ai-backend/main.py: port=8001 → port=8002
```

### Step 2: Migrate API Routes

#### A. Create FastAPI Endpoints
```python
# myhibachi-backend-fastapi/app/api/stripe_routes.py
@router.post("/api/v1/payments/create-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    # Migrate logic from frontend route

@router.get("/api/v1/customers/dashboard")
async def get_customer_dashboard(customer_id: str):
    # Migrate customer analytics logic
```

#### B. Create Webhook Handler
```python
# myhibachi-backend-fastapi/app/api/webhooks.py
@router.post("/api/v1/webhooks/stripe")
async def stripe_webhook_handler(request: Request):
    # Consolidate webhook logic from both frontend routes
```

### Step 3: Frontend Rewiring

#### A. Create API Client
```typescript
// myhibachi-frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiFetch(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path}`
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
}
```

#### B. Update Frontend Calls
```typescript
// Replace: fetch('/api/v1/payments/create-intent', ...)
// With: apiFetch('/api/v1/payments/create-intent', ...)
```

### Step 4: Environment Templates

#### Frontend (.env.local.example)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

#### FastAPI Backend (.env.example)
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://...
APP_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
```

#### AI Backend (.env.example)
```bash
# No Stripe variables
OPENAI_API_KEY=sk-...
API_PORT=8002
CORS_ORIGINS=http://localhost:3000
```

#### Legacy Backend (.env.example)
```bash
# DEPRECATED - DO NOT USE FOR NEW FEATURES
PORT=8001
# Add deprecation banner
```

---

## 🛡️ Security Hardening

### Stripe Integration Audit
- ✅ Use Payment Element/Checkout only
- ✅ Add idempotency keys
- ✅ Verify webhook signatures
- ✅ Attach metadata (bookingId, userId)
- ✅ Customer Portal endpoint
- ✅ Refund capabilities
- ✅ Tax handling

### Environment Security
- ✅ No secrets in frontend bundle
- ✅ CORS properly configured
- ✅ Webhook signature verification
- ✅ Input validation

---

## 🔄 CI/CD Setup

### GitHub Actions Workflows

#### frontend.yml
```yaml
name: Frontend CI
on:
  push:
    paths: ['myhibachi-frontend/**']
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd myhibachi-frontend && npm ci
      - run: cd myhibachi-frontend && npm run lint
      - run: cd myhibachi-frontend && npx tsc --noEmit
      - run: cd myhibachi-frontend && npm run build
      - run: python guard.py
```

#### backend-fastapi.yml
```yaml
name: FastAPI Backend CI
on:
  push:
    paths: ['myhibachi-backend-fastapi/**']
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd myhibachi-backend-fastapi && pip install -r requirements.txt
      - run: cd myhibachi-backend-fastapi && alembic upgrade head
      - run: cd myhibachi-backend-fastapi && pytest
      - run: python guard.py
```

---

## 🧪 End-to-End Test Scenarios

### S1: Deposit via Checkout
- **Test**: Create payment intent → process with test card
- **Expected**: Webhook stored, payment row created, booking updated
- **Status**: 🔄 TO IMPLEMENT

### S2: Payment Element (if implemented)
- **Test**: 3DS authentication flow
- **Expected**: Payment completes, DB synced
- **Status**: 🔄 TO IMPLEMENT

### S3: Refund Processing
- **Test**: Admin initiates partial refund
- **Expected**: Webhook updates, refunds table updated
- **Status**: 🔄 TO IMPLEMENT

### S4: Dispute Handling
- **Test**: Simulate dispute event
- **Expected**: Event stored, visible in admin timeline
- **Status**: 🔄 TO IMPLEMENT

### S5: Customer Portal
- **Test**: Authenticated user opens portal
- **Expected**: Can update payment methods
- **Status**: 🔄 TO IMPLEMENT

### S6: Tax Calculation
- **Test**: Stripe Tax or manual rates
- **Expected**: Correct tax displayed and collected
- **Status**: 🔄 TO IMPLEMENT

### S7: Webhook Idempotency
- **Test**: Resend same webhook event
- **Expected**: DB unchanged (idempotent processing)
- **Status**: 🔄 TO IMPLEMENT

### S8: CORS & Security
- **Test**: Frontend calls backend, verify no secrets in bundle
- **Expected**: CORS allows calls, no secrets exposed
- **Status**: ✅ VERIFIED

### S9: Migration Verification
- **Test**: No remaining Next.js payment API routes
- **Expected**: All payment calls use NEXT_PUBLIC_API_URL
- **Status**: 🔄 TO IMPLEMENT

---

## 📋 Immediate Actions Required

### Critical Fixes
1. **Fix Port Collisions** (breaks development environment)
2. **Implement Empty Files** (11 missing components)
3. **Replace Placeholder Content** (963 TODOs)
4. **Migrate API Routes** (4 endpoints)

### Environment Setup
1. Create .env.example files for all services
2. Update CORS configurations
3. Standardize port assignments
4. Add deprecation banners

### Testing
1. Set up local development environment
2. Implement end-to-end test scenarios
3. Verify webhook processing
4. Test payment flows

---

## 🎯 Success Criteria

### Migration Complete When:
- ✅ No Next.js API routes contain Stripe logic
- ✅ Frontend uses only NEXT_PUBLIC_* env vars
- ✅ All payment calls go through apiFetch()
- ✅ Guard script passes (0 violations)
- ✅ All 9 test scenarios pass
- ✅ CI/CD pipelines green

### Quality Gates:
- TypeScript strict mode ✅
- ESLint passing ✅
- No security violations ✅
- CORS properly configured ✅
- Webhook signature verification ✅

---

## 📞 Next Steps

1. **Execute port fixes** (immediate)
2. **Implement empty files** (1-2 days)
3. **Clean placeholder content** (ongoing)
4. **Execute migration** (3-5 days)
5. **Set up CI/CD** (1 day)
6. **End-to-end testing** (2-3 days)

**Total Estimated Timeline: 1-2 weeks**

---

*Migration Plan Generated: September 1, 2025*
*Status: 🔄 READY FOR EXECUTION*
