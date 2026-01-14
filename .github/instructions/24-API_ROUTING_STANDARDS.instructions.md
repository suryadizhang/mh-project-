---
applyTo: 'apps/backend/src/api/**,apps/backend/src/routers/**,apps/backend/src/main.py'
---

# My Hibachi – API Routing Standards

**Priority: HIGH** – Prevents duplicate route handlers and stub
routing issues. **Applies To:** Backend API routing files only (loaded
conditionally) **Created:** 2026-01-12 **Root Cause Reference:**
Commit 4b79201 - Token refresh 501 bug

---

## 🔴 CRITICAL: The Routing Bug Pattern

**What Happened (January 2026):**

- Two `auth.py` files existed with the same endpoint paths
- `/routers/v1/auth.py` had FULL implementation
- `/api/v1/endpoints/auth.py` had STUB returning 501
- Frontend called `/api/v1/auth/refresh` → got routed to STUB → 501
  error
- Result: Token refresh failed, WebSocket authentication broke

**The Fix:** STUB now delegates to real implementation via import.

---

## 🏛️ Canonical Route Structure

```
/api/v1/           ← CANONICAL prefix for all new endpoints
├── /auth          ← Authentication (login, refresh, logout)
├── /bookings      ← Booking CRUD
├── /customers     ← Customer management
├── /payments      ← Payment processing
├── /admin         ← Admin-only endpoints
└── /public        ← Public endpoints (no auth)

/api/auth/         ← LEGACY (delegates to /api/v1/auth)
/api/station/      ← Station-specific auth
/ws/               ← WebSocket endpoints
```

---

## 📋 Router File Organization

### Primary Implementation Files:

```
apps/backend/src/routers/v1/
├── auth.py           ← FULL auth implementation
├── bookings/         ← Booking endpoints (modularized)
├── customers.py      ← Customer endpoints
├── payments.py       ← Payment endpoints
└── ...
```

### API Layer (Thin Wrappers/Delegates):

```
apps/backend/src/api/v1/endpoints/
├── auth.py           ← DELEGATES to routers/v1/auth.py
├── bookings.py       ← DELEGATES to routers/v1/bookings/
└── ...
```

---

## 🚦 The Delegation Pattern (MANDATORY)

When `api/v1/endpoints/*.py` exists alongside `routers/v1/*.py`:

```python
# ❌ WRONG - Stub that returns 501
@router.post("/refresh")
async def refresh_token_endpoint(...):
    raise HTTPException(
        status_code=501,
        detail="Not Implemented"  # THIS BROKE PRODUCTION!
    )

# ✅ CORRECT - Delegate to real implementation
@router.post("/refresh")
async def refresh_token_endpoint(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Delegates to the full implementation."""
    from routers.v1.auth import refresh_token as refresh_token_impl
    return await refresh_token_impl(
        refresh_token=refresh_data.refresh_token,
        db=db,
    )
```

---

## 🔍 Before Creating Any Endpoint

### Checklist:

- [ ] **Search first:** Does this endpoint already exist elsewhere?
- [ ] **Check both locations:** `routers/v1/` AND `api/v1/endpoints/`
- [ ] **Verify routing:** Which file does the path actually route to?
- [ ] **No 501 stubs:** Never leave unimplemented endpoints
- [ ] **Test the endpoint:** Verify it returns expected response

### Search Commands:

```bash
# Find all handlers for a path
grep -rn "refresh" apps/backend/src/routers/v1/auth.py
grep -rn "refresh" apps/backend/src/api/v1/endpoints/auth.py

# Find all router includes
grep -rn "include_router.*auth" apps/backend/src/

# Run route audit
cd apps/backend/src && python ../../../scripts/audit_api_routes.py
```

---

## 🚫 NEVER Do These

| Anti-Pattern                                | Why It's Bad              | Do Instead                    |
| ------------------------------------------- | ------------------------- | ----------------------------- |
| Create duplicate endpoints                  | One will shadow the other | Search first, extend existing |
| Leave 501 stubs                             | Production will break     | Implement or delegate         |
| Mix implementations across files            | Hard to find code         | Single source of truth        |
| Forget to test endpoints                    | Bugs reach production     | Add integration tests         |
| Create `/api/foo` when `/api/v1/foo` exists | Version confusion         | Use canonical prefix          |

---

## ✅ Route Addition Workflow

### Adding a NEW endpoint:

1. **Determine if it's v1 or new version**
2. **Check if related router exists in `routers/v1/`**
3. **Add to existing router if it fits**
4. **If new router needed:**
   - Create in `routers/v1/new_feature.py`
   - Mount in `main.py` under `/api/v1/`
   - Add integration test

### Adding endpoint to existing v1 router:

```python
# In routers/v1/existing.py
@router.post("/new-endpoint")
async def new_endpoint(...):
    """Full implementation here."""
    pass
```

If `api/v1/endpoints/existing.py` exists, add delegation:

```python
# In api/v1/endpoints/existing.py
@router.post("/new-endpoint")
async def new_endpoint_delegate(...):
    from routers.v1.existing import new_endpoint as impl
    return await impl(...)
```

---

## 🧪 Required Tests for Auth Endpoints

Every auth endpoint MUST have tests that verify:

```python
# test_auth_refresh.py

async def test_refresh_endpoint_not_501(client):
    """CRITICAL: Must NOT return 501."""
    response = await client.post("/api/v1/auth/refresh", json={...})
    assert response.status_code != 501

async def test_refresh_returns_proper_error(client):
    """Must return proper error structure."""
    response = await client.post("/api/v1/auth/refresh", json={...})
    assert "Not Implemented" not in str(response.json())
```

---

## 📊 Route Audit Script

Run periodically to detect issues:

```bash
# From apps/backend/src/
python ../../../scripts/audit_api_routes.py

# Save report to docs
python ../../../scripts/audit_api_routes.py --save
```

The script detects:

- Duplicate routes (same method + path)
- Stub endpoints (501, NotImplemented)
- Route conflicts (overlapping paths)

---

## 🔗 Router Mounting in main.py

```python
# main.py - Router mounting order matters!

# LEGACY: /api/auth (keep for backwards compat)
app.include_router(auth.router, prefix="/api/auth")

# CANONICAL: /api/v1 (all new development)
app.include_router(v1_api_router, prefix="/api/v1")
```

**Note:** The v1_api_router includes routers from `api/v1/api.py`

---

## 🚨 Emergency: Endpoint Returns 501

If you discover a 501 response:

1. **Identify the stub file:**

   ```bash
   grep -rn "501" apps/backend/src/api/
   grep -rn "NotImplemented" apps/backend/src/api/
   ```

2. **Find the real implementation:**

   ```bash
   grep -rn "def endpoint_name" apps/backend/src/routers/
   ```

3. **Fix with delegation pattern** (see above)

4. **Add integration test** to prevent regression

5. **Run route audit** to find other stubs

---

## 📝 Summary

| Rule                                     | Reason                |
| ---------------------------------------- | --------------------- |
| Single source of truth for each endpoint | Prevents shadowing    |
| Canonical prefix is `/api/v1/`           | Consistent versioning |
| Stubs must delegate, not 501             | Production stability  |
| Always test endpoints exist              | Catch routing issues  |
| Run route audit regularly                | Detect issues early   |

---

**Remember:** The 501 bug took hours to debug. Follow these patterns
to prevent it from happening again.

---

## 🖥️ FRONTEND API CALLING STANDARDS (CRITICAL)

**Added:** 2025-01-30 **Root Cause Reference:** Audit Logs 404 bug -
missing `/api` prefix

---

### 🔴 THE FRONTEND BUG PATTERN

**What Happened (January 2025):**

- Frontend called `/admin/audit-logs` instead of
  `/api/admin/audit-logs`
- Missing `/api` prefix caused 404 errors
- Result: "Failed to fetch audit logs" in UI

**Why This Happens:**

- `NEXT_PUBLIC_API_URL` = `https://mhapi.mysticdatanode.net` (no
  `/api` suffix)
- Backend routes are mounted at `/api/v1/*` and `/api/admin/*`
- Developer forgets the `/api` prefix when writing frontend code

---

### 📋 Frontend API Path Rules

#### Rule 1: ALL Backend Calls Start with `/api/`

| Endpoint Type | Path Pattern                  | Example                   |
| ------------- | ----------------------------- | ------------------------- |
| **Public v1** | `/api/v1/{resource}`          | `/api/v1/bookings`        |
| **Admin**     | `/api/admin/{resource}`       | `/api/admin/audit-logs`   |
| **Webhooks**  | `/api/v1/webhooks/{provider}` | `/api/v1/webhooks/stripe` |

#### Rule 2: Use Centralized Constants

```typescript
// ❌ WRONG - Hardcoded path
const response = await apiFetch('/api/admin/audit-logs');

// ✅ CORRECT - Use constant
import { API_ENDPOINTS } from '@/lib/api/endpoints';
const response = await apiFetch(API_ENDPOINTS.ADMIN.AUDIT_LOGS);
```

#### Rule 3: Distinguish Local vs Backend Calls

| Call Type               | Function            | What It Does                                      |
| ----------------------- | ------------------- | ------------------------------------------------- |
| **Backend API**         | `apiFetch()`        | Prepends `NEXT_PUBLIC_API_URL`, calls VPS backend |
| **Local Next.js route** | `fetch('/api/...')` | Calls local Next.js API route                     |

---

### 📂 API Constants Location

Create or use these files:

```
apps/customer/src/lib/api/endpoints.ts
apps/admin/src/lib/api/endpoints.ts
```

**Template:**

```typescript
/**
 * Centralized API Endpoints - Single Source of Truth
 * NEVER hardcode API paths in components/services.
 */

const V1 = '/api/v1';
const ADMIN = '/api/admin';

export const API_ENDPOINTS = {
  V1: {
    BOOKINGS: `${V1}/bookings`,
    BOOKINGS_BOOKED_DATES: `${V1}/bookings/booked-dates`,
    CUSTOMERS: `${V1}/customers`,
    CUSTOMERS_DASHBOARD: `${V1}/customers/dashboard`,

    PAYMENTS: {
      CHECKOUT_SESSION: `${V1}/payments/checkout-session`,
      ALTERNATIVE: `${V1}/payments/alternative-payment`,
    },

    PUBLIC: {
      BOOKINGS_BOOKED_DATES: `${V1}/public/bookings/booked-dates`,
      QUOTE_EMAIL: `${V1}/public/quote/email`,
      LEADS: `${V1}/public/leads`,
    },

    ESCALATIONS: `${V1}/escalations`,
    ESCALATION_DETAIL: (id: string) => `${V1}/escalations/${id}`,
    INBOX_THREADS: `${V1}/inbox/threads`,
  },

  ADMIN: {
    AUDIT_LOGS: `${ADMIN}/audit-logs`,
    AUDIT_LOGS_STATS: `${ADMIN}/audit-logs/stats`,
    AUDIT_LOG_DETAIL: (id: string) => `${ADMIN}/audit-logs/${id}`,

    ERROR_LOGS: `${ADMIN}/error-logs`,
    ERROR_LOGS_STATS: `${ADMIN}/error-logs/stats`,
    ERROR_LOG_DETAIL: (id: string) => `${ADMIN}/error-logs/${id}`,

    AI_READINESS: `${ADMIN}/ai-readiness`,
  },
} as const;
```

---

### 🔍 Frontend Pre-Commit Verification

**Add to pre-commit checks:**

```bash
# Find hardcoded API paths (should use constants)
grep -rn "apiFetch\(['\`\"]/" apps/ --include="*.ts" --include="*.tsx" | \
  grep -v "endpoints.ts" | \
  grep -v "__tests__"

# Find paths missing /api prefix (CRITICAL)
grep -rn "apiFetch(['\`\"]/[^a]" apps/ --include="*.ts" --include="*.tsx"
grep -rn "apiFetch(['\`\"]/admin" apps/ --include="*.ts" --include="*.tsx"
```

**Expected:** No results = all paths use constants or have proper
`/api` prefix.

---

### ❌ Frontend Anti-Patterns

```typescript
// ❌ WRONG - Missing /api prefix (WILL 404!)
await apiFetch('/admin/audit-logs');
await apiFetch('/v1/bookings');

// ❌ WRONG - Hardcoded path
await apiFetch('/api/admin/audit-logs');

// ✅ CORRECT - Use constant
await apiFetch(API_ENDPOINTS.ADMIN.AUDIT_LOGS);
```

---

### ✅ Correct Usage Examples

```typescript
import { API_ENDPOINTS } from '@/lib/api/endpoints';

// Simple endpoint
const response = await apiFetch(API_ENDPOINTS.ADMIN.AUDIT_LOGS);

// With query params
const response = await apiFetch(
  `${API_ENDPOINTS.ADMIN.AUDIT_LOGS}?page=${page}&limit=${limit}`
);

// Dynamic endpoint
const response = await apiFetch(
  API_ENDPOINTS.ADMIN.AUDIT_LOG_DETAIL(logId)
);

// With request body
const response = await apiFetch(API_ENDPOINTS.V1.BOOKINGS, {
  method: 'POST',
  body: JSON.stringify(bookingData),
});
```

---

### 📊 Adding New Frontend API Calls

**Workflow:**

1. **Check if endpoint constant exists** in `endpoints.ts`
2. **If not, add it** to the appropriate section
3. **Import and use** the constant in your component
4. **Never hardcode** the path string directly

**Example: Adding a new endpoint**

```typescript
// Step 1: Add to endpoints.ts
export const API_ENDPOINTS = {
  ADMIN: {
    // ... existing
    NEW_FEATURE: `${ADMIN}/new-feature`,
    NEW_FEATURE_DETAIL: (id: string) => `${ADMIN}/new-feature/${id}`,
  },
} as const;

// Step 2: Use in component
import { API_ENDPOINTS } from '@/lib/api/endpoints';
const data = await apiFetch(API_ENDPOINTS.ADMIN.NEW_FEATURE);
```

---

## 🔗 Related Documentation

- [22-QUALITY_CONTROL.instructions.md](./22-QUALITY_CONTROL.instructions.md)
  – API path verification checklist
- [02-ARCHITECTURE.instructions.md](./02-ARCHITECTURE.instructions.md)
  – System architecture
- [apps/backend/src/main.py](../../apps/backend/src/main.py) – Backend
  router registration
