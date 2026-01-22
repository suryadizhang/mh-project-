---
applyTo: '**'
---

# My Hibachi – Testing & QA Standards

**Priority: HIGH** – Tests are mandatory, not optional.

---

## 🎯 Testing Philosophy

1. **Tests are NOT optional** – Code without tests is incomplete
2. **Test before merge** – All tests must pass before PR approval
3. **Test the right things** – Business logic > UI pixel tests
4. **Fast feedback** – Unit tests run in seconds, not minutes
5. **Test LOCALLY before PR** – Always verify tests pass locally
   before creating or updating PRs

---

## 🚀 Local Testing Before PR (MANDATORY)

**Always run tests locally before creating or updating a PR:**

### Frontend Tests:

```bash
cd apps/customer
npm run test -- --run
# All tests must pass (currently 208 tests)
```

### Backend Tests:

```bash
cd apps/backend
pip install -r requirements.txt  # Ensure dependencies are current
pytest tests/ -v --tb=short
# Note: Some tests may fail due to auth/DB requirements - focus on unit tests
```

### Verify Dependencies:

```bash
# Backend - check for conflicts
pip check

# Frontend - check for issues
npm audit
```

**DO NOT push code that fails local tests to a PR branch.**

---

## 📊 Test Types & Requirements

| Type                  | Scope                 | Required?   | When to Run         |
| --------------------- | --------------------- | ----------- | ------------------- |
| **Unit**              | Single function/class | ✅ YES      | Every commit        |
| **Integration**       | API endpoints         | ✅ YES      | Every PR            |
| **E2E**               | Full user flows       | ✅ YES      | Before merge to dev |
| **Visual Regression** | UI screenshots        | 🟡 Optional | Major UI changes    |
| **Load/Performance**  | Scalability           | 🟡 Optional | Before production   |

---

## 📁 Test File Locations

### Backend (Python/FastAPI):

```
apps/backend/
├── tests/
│   ├── unit/
│   │   ├── test_booking_service.py
│   │   ├── test_pricing_service.py
│   │   └── test_travel_fee.py
│   ├── integration/
│   │   ├── test_booking_api.py
│   │   ├── test_payment_api.py
│   │   └── test_auth_api.py
│   └── conftest.py  # Fixtures
```

### Frontend (TypeScript/Next.js):

```
apps/customer/
├── __tests__/
│   ├── components/
│   ├── hooks/
│   └── utils/
├── e2e/
│   └── booking.spec.ts
```

### E2E (Playwright):

```
e2e/
├── tests/
│   ├── booking-flow.spec.ts
│   ├── payment-flow.spec.ts
│   └── admin-flow.spec.ts
├── fixtures/
└── playwright.config.ts
```

---

## ✅ Test Requirements by Batch

### Batch 1: Core Booking + Security

- [ ] Booking CRUD unit tests
- [ ] Authentication integration tests
- [ ] RBAC permission tests
- [ ] Audit trail tests
- [ ] E2E: Complete booking flow

### Batch 2: Payment Processing

- [ ] Stripe webhook unit tests
- [ ] Payment flow integration tests
- [ ] Refund logic tests
- [ ] E2E: Checkout with payment

### Batch 3: Core AI

- [ ] AI response unit tests
- [ ] Escalation logic tests
- [ ] Knowledge retrieval tests
- [ ] E2E: Chat conversation flow

### Batch 4: Communications

- [ ] Webhook handler tests
- [ ] Message routing tests
- [ ] Channel integration tests
- [ ] E2E: Multi-channel flow

### Batch 5-6: Advanced Features

- [ ] Marketing API tests
- [ ] Loyalty system tests
- [ ] Multi-LLM tests
- [ ] Full regression suite

---

## 📝 Test Writing Standards

### Unit Test Template (Python):

```python
import pytest
from services.booking_service import BookingService

class TestBookingService:
    """Unit tests for BookingService."""

    @pytest.fixture
    def service(self):
        return BookingService()

    def test_create_booking_success(self, service):
        """Should create booking with valid data."""
        # Arrange
        data = {...}

        # Act
        result = service.create_booking(data)

        # Assert
        assert result.id is not None
        assert result.status == "confirmed"

    def test_create_booking_invalid_date(self, service):
        """Should reject booking with past date."""
        # Arrange
        data = {"date": "2020-01-01", ...}

        # Act & Assert
        with pytest.raises(ValidationError):
            service.create_booking(data)
```

### Integration Test Template (Python):

```python
import pytest
from fastapi.testclient import TestClient
from main import app

class TestBookingAPI:
    """Integration tests for booking endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_create_booking_endpoint(self, client):
        """POST /api/v1/bookings should create booking."""
        response = client.post(
            "/api/v1/bookings",
            json={...},
            headers={"Authorization": "Bearer ..."}
        )

        assert response.status_code == 201
        assert "id" in response.json()
```

### E2E Test Template (Playwright):

```typescript
import { test, expect } from '@playwright/test';

test.describe('Booking Flow', () => {
  test('customer can complete booking', async ({ page }) => {
    // Navigate to booking page
    await page.goto('/book');

    // Fill form
    await page.fill('[data-testid="guest-count"]', '10');
    await page.click('[data-testid="date-picker"]');
    await page.click('[data-testid="submit"]');

    // Verify success
    await expect(
      page.locator('[data-testid="confirmation"]')
    ).toBeVisible();
  });
});
```

---

## 🚦 Test Quality Gates

### PR Must Pass:

| Gate              | Threshold            |
| ----------------- | -------------------- |
| Unit tests        | 100% pass            |
| Integration tests | 95%+ pass            |
| E2E tests         | 100% pass on staging |
| Coverage          | 80%+ for new code    |

### Blocking Failures:

- Any unit test failure → Block merge
- Critical path E2E failure → Block merge
- Security test failure → Block merge
- Performance regression > 20% → Block merge

---

## 🔧 Fixing Pre-Existing Test Failures

**When you discover pre-existing test failures, you MUST fix them
properly.**

### Why This Matters

Pre-existing broken tests indicate:

- Tests don't match actual component behavior
- Component API changed but tests weren't updated
- Mocks are incorrect or outdated
- Tests were written for planned features, not implemented ones

### Mandatory Process

1. **Never skip or disable tests** – Fix them to match reality
2. **Understand the component first** – Read the actual implementation
3. **Update tests to match behavior** – Tests should reflect what code
   DOES, not what we wish it did
4. **Verify the fix is correct** – Run tests multiple times to ensure
   stability

### Common Fix Patterns

| Problem                          | Solution                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------ |
| Wrong text/label in test         | Check actual component output, update test to match                            |
| Mock not matching real API       | Check what function the component actually calls (e.g., `apiFetch` vs `fetch`) |
| Multiple elements found          | Use more specific selectors (`getByRole`, `getByLabelText`, or `getAllBy*`)    |
| HTML5 validation blocking submit | Use `fireEvent.submit(form)` instead of button click                           |
| Missing import in component      | Add the import (e.g., `import React from 'react'`)                             |
| Timeout waiting for element      | Component may not render expected text – verify actual output                  |

### Test-to-Component Alignment Checklist

Before marking tests as "fixed":

- [ ] Test assertions match ACTUAL component output
- [ ] Mocks target the ACTUAL functions called
- [ ] Selectors are specific enough (no "multiple elements found")
- [ ] Async operations properly awaited
- [ ] Form submission bypasses HTML5 validation if needed
- [ ] All imports present in component file

### Example: Fixing a Misaligned Test

**Before (broken):**

```tsx
// Test expects "Payment Summary" but component shows "Final Payment Summary"
expect(screen.getByText('Payment Summary')).toBeInTheDocument();
```

**After (fixed):**

```tsx
// Match what the component ACTUALLY renders
expect(screen.getByText('Final Payment Summary')).toBeInTheDocument();
```

### When Tests Reveal Actual Bugs

If tests fail because the COMPONENT is wrong (not the test):

1. Document the bug
2. Fix the component
3. Verify test passes with correct component behavior
4. Never "fix" a test to accept wrong behavior

---

## 🔄 Test Commands

### Backend:

```bash
# Run all tests
cd apps/backend
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_booking_service.py

# Run specific test
pytest tests/unit/test_booking_service.py::test_create_booking
```

### Frontend:

```bash
# Run unit tests
cd apps/customer
npm test

# Run with coverage
npm test -- --coverage

# Run E2E (local)
npx playwright test
```

### Staging E2E Tests:

```bash
# Run all staging E2E tests
npm run test:e2e:staging

# Run specific project
npm run test:e2e:staging:customer  # Customer site desktop
npm run test:e2e:staging:admin     # Admin site desktop
npm run test:e2e:staging:api       # API tests only
npm run test:e2e:staging:mobile    # Customer site mobile viewport

# Production E2E (use with caution!)
npm run test:e2e:prod
```

**Playwright Configuration Files:**

| Config File                    | Target Environment | URLs                        |
| ------------------------------ | ------------------ | --------------------------- |
| `playwright.config.ts`         | Local              | `localhost:3000`            |
| `playwright.staging.config.ts` | Staging            | `staging.myhibachichef.com` |
| `playwright.prod.config.ts`    | Production         | `myhibachichef.com`         |

**⚠️ Vercel Protection:** For staging E2E to work, disable Vercel
Deployment Protection on the `dev` branch. See
`docs/04-DEPLOYMENT/STAGING_ENVIRONMENT_SETUP_GUIDE.md`.

---

## 🗄️ Database Migration Safety (MANDATORY)

### 🔴 DATABASE ENVIRONMENT RULES (NEVER BREAK!)

| Environment     | Database               | Use For                     |
| --------------- | ---------------------- | --------------------------- |
| **Development** | Supabase / Local       | Local dev, experiments      |
| **Staging**     | `myhibachi_staging`    | ALL testing, QA, migrations |
| **Production**  | `myhibachi_production` | Real customer data ONLY     |

**NEVER insert test data into production database!**

```bash
# ✅ CORRECT - Run tests against staging
pytest tests/integration/ --database-url="...myhibachi_staging"

# ❌ FORBIDDEN - Never test against production
pytest tests/integration/ --database-url="...myhibachi_production"
```

### ⚠️ CRITICAL: SQLAlchemy Model ↔ Production Sync

**Every column in SQLAlchemy model MUST exist in production
database.**

See `19-DATABASE_SCHEMA_MANAGEMENT.instructions.md` for full details.

**Quick Verification Command:**

```bash
# Check if a column exists before deploying code that uses it
ssh root@VPS "sudo -u postgres psql -d myhibachi_production -c \"
SELECT column_name FROM information_schema.columns
WHERE table_schema='schema_name' AND table_name='table_name';\""
```

**Real Example (December 2024):**

- Added `venue_lat`, `venue_lng` columns to booking model
- Forgot to run migration on production
- Result: All booking queries failed with 503 errors

### Pre-Migration Checklist:

| Check                      | Action                                                   | Why                            |
| -------------------------- | -------------------------------------------------------- | ------------------------------ |
| **Backup taken**           | `pg_dump myhibachi_staging > backup_$(date +%Y%m%d).sql` | Recovery if migration fails    |
| **Migration reviewed**     | Read every line of SQL                                   | Catch destructive operations   |
| **No DROP without backup** | Never drop columns/tables without data export            | Data loss prevention           |
| **Staging first**          | Run on staging for 48+ hours                             | Catch issues before production |
| **Rollback script ready**  | Have reverse migration prepared                          | Quick recovery                 |

### Migration Safety Rules:

```sql
-- ❌ DANGEROUS - Direct DROP
ALTER TABLE bookings DROP COLUMN legacy_data;

-- ✅ SAFE - Rename first, drop later (after verification)
-- Step 1: Rename (deploy, verify app works)
ALTER TABLE bookings RENAME COLUMN legacy_data TO _legacy_data_deprecated;

-- Step 2: Drop in NEXT release (after 1+ week in production)
ALTER TABLE bookings DROP COLUMN _legacy_data_deprecated;
```

```sql
-- ❌ DANGEROUS - Add NOT NULL without default
ALTER TABLE bookings ADD COLUMN status VARCHAR(20) NOT NULL;

-- ✅ SAFE - Add nullable first, then backfill, then add constraint
ALTER TABLE bookings ADD COLUMN status VARCHAR(20);
UPDATE bookings SET status = 'pending' WHERE status IS NULL;
ALTER TABLE bookings ALTER COLUMN status SET NOT NULL;
```

### Post-Migration Verification:

```bash
# Verify schema matches expectations
psql -d myhibachi_staging -c "\d bookings"

# Verify row counts didn't change unexpectedly
psql -d myhibachi_staging -c "SELECT COUNT(*) FROM bookings"

# Verify application health
curl https://staging-api.mysticdatanode.net/health

# Run integration tests against staging
pytest tests/integration/ --base-url=https://staging-api.mysticdatanode.net
```

---

## 📋 PR Review Checklist (Industry Standard)

### Before Approving ANY PR:

**Code Quality:**

- [ ] Code follows SOLID principles (01-CORE_PRINCIPLES)
- [ ] No `any` types in TypeScript
- [ ] Error handling is comprehensive
- [ ] No hardcoded values (use config/env)
- [ ] No console.log/print statements left
- [ ] Comments explain "why", not "what"

**Testing:**

- [ ] Unit tests for new logic
- [ ] Integration tests for new endpoints
- [ ] Tests actually test the behavior (not mocks)
- [ ] Edge cases covered (null, empty, boundary)

**Security:**

- [ ] Input validation on all user data
- [ ] No secrets in code
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (escaped output)
- [ ] Authorization checks on endpoints

**Performance:**

- [ ] No N+1 queries (eager loading used)
- [ ] Pagination for list endpoints
- [ ] Heavy operations are async/background
- [ ] No unnecessary re-renders (React)

**Documentation:**

- [ ] Public APIs documented
- [ ] Complex logic commented
- [ ] CHANGELOG updated if user-facing
- [ ] Feature flag documented if used

### PR Size Guidelines:

| PR Size   | Lines Changed | Review Time | Action            |
| --------- | ------------- | ----------- | ----------------- |
| 🟢 Small  | < 100         | 15 min      | Quick review      |
| 🟡 Medium | 100-300       | 30 min      | Standard review   |
| 🟠 Large  | 300-500       | 1 hour      | Split if possible |
| 🔴 Huge   | > 500         | 2+ hours    | MUST split        |

---

## ⚠️ Test Anti-Patterns

| Don't                       | Do Instead                     |
| --------------------------- | ------------------------------ |
| Test implementation details | Test behavior/outcomes         |
| Skip edge cases             | Test boundaries and nulls      |
| Use real APIs in unit tests | Mock external dependencies     |
| Test everything in E2E      | Unit test logic, E2E for flows |
| Write tests after bugs      | Write tests with features      |
| Ignore flaky tests          | Fix or quarantine them         |

---

## 📊 Coverage Targets

| Area                      | Target | Priority    |
| ------------------------- | ------ | ----------- |
| Business logic (services) | 90%+   | 🔴 CRITICAL |
| API endpoints             | 80%+   | 🔴 CRITICAL |
| Utilities                 | 70%+   | 🟠 HIGH     |
| UI components             | 60%+   | 🟡 MEDIUM   |
| Config/setup              | 50%+   | 🟢 LOW      |

---

## � Pre-Commit Code Review (CROSS-REFERENCE)

**For comprehensive pre-commit review standards, see:**
`10-COPILOT_PERFORMANCE.instructions.md` → "Pre-Commit Code Review"
section

**Quick Summary - Before Every Commit:**

1. ✅ Run `npm run build` (both apps)
2. ✅ Run `npm test -- --run` (all tests pass)
3. ✅ Review `git diff --staged` line-by-line
4. ✅ Verify all imports resolve
5. ✅ Check error handling is complete
6. ✅ Remove console.log/print statements
7. ✅ Verify no hardcoded secrets

**This is enterprise-standard practice that senior SWEs follow.**

---

## 🔗 Related Docs

- `docs/05-TESTING/` – Detailed test guides
- `e2e/README.md` – E2E setup guide
- `pytest.ini` – Pytest configuration
- `playwright.config.ts` – Playwright configuration
- `10-COPILOT_PERFORMANCE.instructions.md` – Pre-commit review details
