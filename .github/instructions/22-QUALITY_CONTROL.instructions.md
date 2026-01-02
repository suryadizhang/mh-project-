---
applyTo: '**'
---

# My Hibachi – Comprehensive Quality Control Standards

**Priority: CRITICAL** – Apply to ALL code changes before commit.
**Version:** 2.0.0 **Created:** 2025-01-27 **Updated:** 2025-01-27

---

## 🎯 Purpose

This document defines comprehensive quality control standards for the
My Hibachi codebase. These checks MUST pass before ANY commit to
prevent bugs, security issues, performance problems, and maintenance
debt.

**Quality is NOT optional. Every commit should improve, not degrade,
the codebase.**

---

## ✅ PRE-COMMIT CHECKLIST (Must Complete ALL)

Before typing `git commit`, verify ALL of the following:

| #   | Check               | Command                                                                       | Pass? |
| --- | ------------------- | ----------------------------------------------------------------------------- | ----- |
| 1   | **Build passes**    | `cd apps/customer && npm run build`                                           | ☐     |
| 2   | **Build passes**    | `cd apps/admin && npm run build`                                              | ☐     |
| 3   | **Tests pass**      | `cd apps/customer && npm test -- --run`                                       | ☐     |
| 4   | **Backend imports** | `cd apps/backend/src && python -c "from main import app"`                     | ☐     |
| 5   | **No console.log**  | `grep -r "console.log" apps/ --include="*.ts" --include="*.tsx"`              | ☐     |
| 6   | **No print()**      | `grep -r "print(" apps/backend/src --include="*.py"`                          | ☐     |
| 7   | **No hardcoded $**  | `grep -r "\$[0-9]" apps/ --include="*.ts" --include="*.tsx" --include="*.py"` | ☐     |
| 8   | **No TODO in prod** | `grep -r "TODO\|FIXME" apps/ --include="*.ts" --include="*.tsx"`              | ☐     |
| 9   | **Diff reviewed**   | `git diff --staged` (read every line)                                         | ☐     |
| 10  | **Types complete**  | No `any` types, all functions typed                                           | ☐     |

**If ANY check fails: FIX → RE-CHECK → COMMIT**

---

## 📋 QUALITY CATEGORIES

### Category A: SSoT Compliance (Business Values)

**Rule:** ALL business values (prices, fees, policies) MUST come from
SSoT system.

#### Forbidden Patterns (Search and Destroy)

```bash
# Run these BEFORE every commit
grep -rn "\$55\|\$30\|\$100\|\$550\|\$2" apps/ --include="*.ts" --include="*.tsx" --include="*.py"
grep -rn "55\s*dollars\|30\s*dollars\|100\s*dollars" apps/ --include="*.ts" --include="*.tsx"
grep -rn "deposit.*=.*100\|minimum.*=.*550" apps/ --include="*.ts" --include="*.tsx" --include="*.py"
```

#### ❌ WRONG (Hardcoded)

```typescript
// Frontend
const DEPOSIT = 100;
const ADULT_PRICE = 55;
<span>$550 minimum</span>

// Backend
deposit_amount = 10000  # Hardcoded cents
if total < 55000:  # Magic number
```

#### ✅ CORRECT (SSoT)

```typescript
// Frontend - Use hook
const { depositAmount, partyMinimum } = usePricing();
<span>${partyMinimum} minimum</span>

// Backend - Use service
config = await get_business_config(db)
deposit = config.deposit_amount_cents

// Backend (no db) - Use sync
config = get_business_config_sync()
```

#### SSoT Architecture Reference

```
Database (dynamic_variables table)
    ↓
Backend API (/api/v1/config/all)
    ↓
Frontend (usePricing hook → pricingTemplates.ts fallback)
    ↓
UI Components (QuoteCalculator, Menu, Booking)
```

---

### Category B: Type Safety

**Rule:** TypeScript strict mode, Python type hints, NO `any` types.

#### TypeScript Standards

```typescript
// ❌ WRONG
function process(data: any) { ... }
const user = response as any;
// @ts-ignore
doSomething(badType);

// ✅ CORRECT
function process(data: BookingData): ProcessResult { ... }
const user: User | null = await fetchUser(id);
if (!user) throw new NotFoundError('User not found');
```

#### Python Type Hints

```python
# ❌ WRONG
def calculate_total(items):
    return sum(i['price'] for i in items)

# ✅ CORRECT
from typing import List
from decimal import Decimal

def calculate_total(items: List[OrderItem]) -> Decimal:
    return sum(item.price for item in items)
```

#### Null/Undefined Handling

```typescript
// ❌ WRONG
const name = user!.name; // Non-null assertion
const value = obj.nested.deep.value; // No null checks

// ✅ CORRECT
const name = user?.name ?? 'Unknown';
const value = obj?.nested?.deep?.value;
if (user) {
  console.log(user.name);
}
```

---

### Category C: API Contracts

**Rule:** All API calls must have typed requests AND responses.

#### Frontend API Calls

```typescript
// ❌ WRONG
const response = await fetch('/api/bookings');
const data = await response.json(); // Untyped

// ✅ CORRECT
interface BookingResponse {
  id: string;
  status: BookingStatus;
  customer: CustomerInfo;
}

const response = await apiFetch<BookingResponse>('/api/v1/bookings');
if (!response.ok) {
  throw new ApiError(response.status, 'Failed to fetch bookings');
}
```

#### Backend Response Schemas

```python
# ❌ WRONG
@router.get("/bookings")
async def get_bookings():
    return {"data": bookings}  # Untyped response

# ✅ CORRECT
from pydantic import BaseModel

class BookingResponse(BaseModel):
    id: UUID
    status: BookingStatus
    customer: CustomerInfo

@router.get("/bookings", response_model=List[BookingResponse])
async def get_bookings() -> List[BookingResponse]:
    return bookings
```

---

### Category D: Error Handling

**Rule:** All async operations must have error handling. Never swallow
errors.

#### Frontend Error Handling

```typescript
// ❌ WRONG
const data = await fetchData(); // Unhandled rejection
try {
  await riskyOp();
} catch {} // Swallowed error

// ✅ CORRECT
try {
  const data = await fetchData();
  return data;
} catch (error) {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return null; // Expected case
    }
    throw error; // Re-throw unexpected
  }
  console.error('Unexpected error:', error);
  throw new UnexpectedError('Failed to fetch data');
}
```

#### Backend Error Handling

```python
# ❌ WRONG
try:
    result = await db.execute(query)
except:  # Bare except
    pass  # Swallowed

# ✅ CORRECT
from fastapi import HTTPException

try:
    result = await db.execute(query)
except IntegrityError as e:
    logger.warning(f"Duplicate entry: {e}")
    raise HTTPException(409, "Resource already exists")
except SQLAlchemyError as e:
    logger.exception(f"Database error: {e}")
    raise HTTPException(500, "Internal server error")
```

---

### Category E: Security

**Rule:** Zero tolerance for security vulnerabilities.

#### SQL Injection Prevention

```python
# ❌ NEVER DO THIS
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)

# ✅ ALWAYS USE PARAMETERIZED QUERIES
# SQLAlchemy ORM (preferred)
result = await db.execute(select(User).where(User.email == email))

# Raw SQL with parameters
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)
```

#### XSS Prevention

```tsx
// ❌ DANGEROUS
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ SAFE - React auto-escapes
<div>{userInput}</div>

// ✅ SAFE - If HTML needed, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

#### Secret Management

```python
# ❌ NEVER
api_key = "sk_live_abc123..."
password = "admin123"

# ✅ ALWAYS
api_key = os.getenv("STRIPE_API_KEY")
# Or from Google Secret Manager
api_key = await get_secret("stripe-api-key")
```

#### Security Scan Commands

```bash
# Check for hardcoded secrets
grep -rn "password.*=.*['\"]" apps/ --include="*.py" --include="*.ts"
grep -rn "api_key.*=.*['\"]" apps/ --include="*.py" --include="*.ts"
grep -rn "secret.*=.*['\"]" apps/ --include="*.py" --include="*.ts"
grep -rn "sk_live\|pk_live" apps/ --include="*.py" --include="*.ts"
```

---

### Category F: Performance

**Rule:** No N+1 queries, memory leaks, or unnecessary re-renders.

#### N+1 Query Prevention

```python
# ❌ N+1 PROBLEM
bookings = await db.execute(select(Booking))
for booking in bookings:
    customer = await db.execute(  # Query per booking!
        select(Customer).where(Customer.id == booking.customer_id)
    )

# ✅ EAGER LOADING
from sqlalchemy.orm import selectinload

bookings = await db.execute(
    select(Booking).options(selectinload(Booking.customer))
)
```

#### React Re-render Prevention

```tsx
// ❌ WRONG - Creates new object every render
<Component style={{ color: 'red' }} />
<Component onClick={() => handleClick(id)} />

// ✅ CORRECT - Memoized
const style = useMemo(() => ({ color: 'red' }), []);
const handleClickMemo = useCallback(() => handleClick(id), [id]);
<Component style={style} onClick={handleClickMemo} />
```

#### Memory Leak Prevention

```typescript
// ❌ WRONG - No cleanup
useEffect(() => {
  const interval = setInterval(fetchData, 5000);
}, []);

// ✅ CORRECT - Cleanup on unmount
useEffect(() => {
  const interval = setInterval(fetchData, 5000);
  return () => clearInterval(interval);
}, []);
```

---

### Category G: Testing

**Rule:** New features require tests. Changes to logic require test
updates.

#### Test Coverage Requirements

| Code Type                 | Required Coverage |
| ------------------------- | ----------------- |
| Business logic (services) | 90%+              |
| API endpoints             | 80%+              |
| Utilities                 | 70%+              |
| UI components             | 60%+              |

#### Test Quality Checklist

- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases (null, empty, boundary values)
- [ ] Tests are independent (no shared state)
- [ ] Tests have descriptive names
- [ ] Mocks are realistic

#### Running Tests

```bash
# Frontend
cd apps/customer && npm test -- --run
cd apps/customer && npm test -- --coverage

# Backend
cd apps/backend && pytest tests/ -v
cd apps/backend && pytest tests/ --cov=src
```

---

### Category H: Database Safety

**Rule:** NEVER run untested migrations on production. Staging first
for 48 hours.

#### Migration Checklist

| Step | Required | Action                                   |
| ---- | -------- | ---------------------------------------- |
| 1    | ✅       | Create migration file with IF NOT EXISTS |
| 2    | ✅       | Include rollback script as comment       |
| 3    | ✅       | Test locally                             |
| 4    | ✅       | Run on staging database                  |
| 5    | ✅       | Wait 48 hours, verify staging works      |
| 6    | ✅       | Take production backup                   |
| 7    | ✅       | Run on production                        |
| 8    | ✅       | Verify and restart backend               |

#### Migration File Template

```sql
-- =====================================================
-- Migration: Description
-- Created: YYYY-MM-DD
-- =====================================================

BEGIN;

-- Idempotent column addition
ALTER TABLE schema.table ADD COLUMN IF NOT EXISTS new_column TYPE;

-- Add comment
COMMENT ON COLUMN schema.table.new_column IS 'Description';

COMMIT;

-- ROLLBACK (keep as comment for emergency):
-- ALTER TABLE schema.table DROP COLUMN IF EXISTS new_column;
```

#### Verify Column Exists Before Deploy

```bash
# Check if column exists in production
ssh root@VPS "sudo -u postgres psql -d myhibachi_production -c \"
SELECT column_name FROM information_schema.columns
WHERE table_schema='schema' AND table_name='table'
AND column_name='new_column';\""
```

---

### Category I: Documentation

**Rule:** Public APIs must be documented. Complex logic must be
commented.

#### Docstring Requirements

```python
# ❌ WRONG - No documentation
def calculate_travel_fee(distance, config):
    if distance <= config.free_miles:
        return 0
    return (distance - config.free_miles) * config.per_mile_rate

# ✅ CORRECT - Clear documentation
def calculate_travel_fee(
    distance_miles: float,
    config: BusinessConfig
) -> Decimal:
    """
    Calculate travel fee based on distance from station.

    First `config.travel_free_miles` are free.
    After that, charge `config.travel_per_mile_cents` per mile.

    Args:
        distance_miles: Distance from station to venue in miles
        config: Business configuration with travel fee settings

    Returns:
        Travel fee in cents (0 if within free radius)

    Example:
        >>> config.travel_free_miles = 30
        >>> config.travel_per_mile_cents = 200
        >>> calculate_travel_fee(45, config)
        3000  # (45 - 30) * 200 = $30.00
    """
    if distance_miles <= config.travel_free_miles:
        return Decimal(0)
    billable_miles = distance_miles - config.travel_free_miles
    return Decimal(billable_miles * config.travel_per_mile_cents)
```

#### Comment Standards

```typescript
// ❌ WRONG - Comments explain WHAT (obvious)
// Increment counter
counter++;

// ✅ CORRECT - Comments explain WHY (not obvious)
// Reset to 0 after 3 failed attempts to prevent brute force
if (failedAttempts >= 3) {
  cooldownUntil = Date.now() + 30000;
}
```

---

### Category J: Accessibility

**Rule:** All UI must be accessible. Follow WCAG 2.1 AA standards.

#### Required Accessibility Checks

```tsx
// ❌ WRONG
<img src="/hero.jpg" />
<div onClick={handleClick}>Click me</div>
<input type="text" />

// ✅ CORRECT
<img src="/hero.jpg" alt="Hibachi chef cooking at outdoor party" />
<button onClick={handleClick}>Click me</button>
<label htmlFor="email">Email</label>
<input id="email" type="email" aria-describedby="email-hint" />
<span id="email-hint">We'll never share your email</span>
```

#### Accessibility Checklist

- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] All buttons have accessible names
- [ ] Color contrast meets 4.5:1 ratio
- [ ] Keyboard navigation works
- [ ] Focus states are visible
- [ ] ARIA labels where needed

---

## 🔍 AUTOMATED QUALITY GATE SCRIPT

Create and run before every commit:

**File:** `scripts/pre-commit-check.ps1`

```powershell
#!/usr/bin/env pwsh
# Pre-commit quality gate for My Hibachi

$ErrorActionPreference = "Stop"
$failed = $false

Write-Host "🔍 Running Quality Gate..." -ForegroundColor Cyan

# 1. Customer app build
Write-Host "`n[1/6] Building customer app..." -ForegroundColor Yellow
Push-Location "apps/customer"
try {
    npm run build 2>&1 | Out-Null
    Write-Host "  ✅ Customer build passed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Customer build FAILED" -ForegroundColor Red
    $failed = $true
}
Pop-Location

# 2. Admin app build
Write-Host "`n[2/6] Building admin app..." -ForegroundColor Yellow
Push-Location "apps/admin"
try {
    npm run build 2>&1 | Out-Null
    Write-Host "  ✅ Admin build passed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Admin build FAILED" -ForegroundColor Red
    $failed = $true
}
Pop-Location

# 3. Frontend tests
Write-Host "`n[3/6] Running frontend tests..." -ForegroundColor Yellow
Push-Location "apps/customer"
try {
    npm test -- --run 2>&1 | Out-Null
    Write-Host "  ✅ Frontend tests passed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Frontend tests FAILED" -ForegroundColor Red
    $failed = $true
}
Pop-Location

# 4. Backend imports
Write-Host "`n[4/6] Checking backend imports..." -ForegroundColor Yellow
Push-Location "apps/backend/src"
try {
    python -c "from main import app; print('OK')" 2>&1 | Out-Null
    Write-Host "  ✅ Backend imports OK" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Backend imports FAILED" -ForegroundColor Red
    $failed = $true
}
Pop-Location

# 5. Hardcoded values check
Write-Host "`n[5/6] Scanning for hardcoded values..." -ForegroundColor Yellow
$patterns = @(
    '\$55|\$30|\$100|\$550',
    'deposit.*=.*100',
    'minimum.*=.*550',
    'adult.*price.*=.*55'
)
$foundHardcoded = $false
foreach ($pattern in $patterns) {
    $matches = Select-String -Path "apps/**/*.ts","apps/**/*.tsx","apps/**/*.py" -Pattern $pattern -Recurse 2>$null
    if ($matches) {
        foreach ($match in $matches) {
            if (-not ($match.Path -like "*node_modules*" -or $match.Path -like "*__pycache__*")) {
                Write-Host "  ⚠️ Potential hardcoded value: $($match.Path):$($match.LineNumber)" -ForegroundColor Yellow
                $foundHardcoded = $true
            }
        }
    }
}
if (-not $foundHardcoded) {
    Write-Host "  ✅ No hardcoded business values found" -ForegroundColor Green
}

# 6. Debug code check
Write-Host "`n[6/6] Checking for debug code..." -ForegroundColor Yellow
$debugPatterns = @("console.log", "console.debug", "debugger")
$foundDebug = $false
foreach ($pattern in $debugPatterns) {
    $matches = Select-String -Path "apps/**/*.ts","apps/**/*.tsx" -Pattern $pattern -Recurse 2>$null
    if ($matches) {
        foreach ($match in $matches) {
            if (-not ($match.Path -like "*node_modules*")) {
                Write-Host "  ⚠️ Debug code: $($match.Path):$($match.LineNumber)" -ForegroundColor Yellow
                $foundDebug = $true
            }
        }
    }
}
if (-not $foundDebug) {
    Write-Host "  ✅ No debug code found" -ForegroundColor Green
}

# Summary
Write-Host "`n" + "="*50 -ForegroundColor Cyan
if ($failed) {
    Write-Host "❌ QUALITY GATE FAILED - Fix issues before committing" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ QUALITY GATE PASSED - Ready to commit" -ForegroundColor Green
    exit 0
}
```

**Usage:**

```powershell
# Run before every commit
.\scripts\pre-commit-check.ps1

# If it passes, proceed with commit
git add .
git commit -m "feat(scope): description"
```

---

## 📝 PR CODE REVIEW CHECKLIST

Before approving ANY Pull Request, verify:

### Code Quality

- [ ] No `any` types in TypeScript
- [ ] All functions have return types
- [ ] No hardcoded business values (prices, fees, limits)
- [ ] No console.log/print statements
- [ ] No TODO/FIXME comments
- [ ] No commented-out code
- [ ] Follows existing patterns in codebase

### Error Handling

- [ ] All async operations have try/catch
- [ ] Errors are logged with context
- [ ] User-friendly error messages (no stack traces)
- [ ] Proper HTTP status codes in API

### Security

- [ ] No hardcoded secrets
- [ ] Input validation on all user data
- [ ] SQL uses parameterized queries
- [ ] No XSS vulnerabilities

### Performance

- [ ] No N+1 queries (use eager loading)
- [ ] React components properly memoized
- [ ] Cleanup in useEffect hooks
- [ ] No unnecessary re-renders

### Testing

- [ ] Tests added for new features
- [ ] Tests updated for changed behavior
- [ ] All tests pass
- [ ] Edge cases covered

### Documentation

- [ ] Public APIs have docstrings
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] CHANGELOG updated for user-facing changes

---

## 🚀 QUICK REFERENCE COMMANDS

```bash
# Build verification
cd apps/customer && npm run build
cd apps/admin && npm run build

# Test verification
cd apps/customer && npm test -- --run
cd apps/backend && pytest tests/ -v

# Backend import check
cd apps/backend/src && python -c "from main import app; print('OK')"

# SSoT violation scan
grep -rn "\$55\|\$30\|\$100\|\$550" apps/ --include="*.ts" --include="*.tsx" --include="*.py"

# Debug code scan
grep -rn "console.log\|console.debug\|debugger" apps/ --include="*.ts" --include="*.tsx"
grep -rn "print(" apps/backend/src --include="*.py" | grep -v "__pycache__"

# Security scan
grep -rn "password\|secret\|api_key" apps/ --include="*.ts" --include="*.py" -i

# TODO scan
grep -rn "TODO\|FIXME\|HACK\|XXX" apps/ --include="*.ts" --include="*.tsx" --include="*.py"

# Type safety scan (find `any`)
grep -rn ": any\|as any" apps/ --include="*.ts" --include="*.tsx"
```

---

## � FILE SIZE LIMITS & MODULARIZATION (CRITICAL)

**Rule:** Files over 500 lines MUST be split into modular packages.

### Maximum File Size Limits

| File Type                                          | Max Lines | Action When Exceeded          |
| -------------------------------------------------- | --------- | ----------------------------- |
| **Router files** (`routers/v1/*.py`)               | 500 lines | Split into package            |
| **Service files** (`services/*.py`)                | 500 lines | Split by responsibility       |
| **Model files** (`db/models/*.py`)                 | 700 lines | Split by domain               |
| **Config files** (`config/*.py`, `core/config.py`) | 800 lines | Acceptable (mostly constants) |
| **Migration files** (`migrations/*.py`)            | No limit  | Auto-generated                |
| **Test files** (`tests/*.py`)                      | 600 lines | Split by test category        |

### Modularization Pattern (Example: Router Package)

When a router file exceeds 500 lines, convert it to a package:

**Before (single file):**

```
routers/v1/bookings.py  # 2500+ lines ❌
```

**After (modular package):**

```
routers/v1/bookings/
├── __init__.py       # Router combiner (~60 lines)
├── schemas.py        # Pydantic models (~300 lines)
├── constants.py      # Business constants (~100 lines)
├── crud.py           # GET/POST/PUT endpoints (~500 lines)
├── delete.py         # DELETE with soft-delete (~200 lines)
├── calendar.py       # Calendar views (~300 lines)
├── availability.py   # Slot checking (~250 lines)
├── cancellation.py   # 2-step workflow (~500 lines)
└── notifications.py  # Async helpers (~200 lines)
```

### Module Responsibilities

| Module             | Contains                         | Max Lines |
| ------------------ | -------------------------------- | --------- |
| `__init__.py`      | Router imports, combiner         | 100       |
| `schemas.py`       | Pydantic request/response models | 400       |
| `constants.py`     | Enums, constants, mappings       | 150       |
| `crud.py`          | Create, Read, Update endpoints   | 500       |
| `delete.py`        | Delete/archive operations        | 250       |
| `helpers.py`       | Shared utility functions         | 300       |
| `notifications.py` | Email/SMS/webhook triggers       | 250       |

### **init**.py Pattern (Router Combiner)

```python
"""
Bookings Router Package
=======================
Modular package for booking-related endpoints.

Modules:
- crud.py: GET/POST/PUT operations
- delete.py: Soft-delete with RBAC
- calendar.py: Weekly/monthly views
- availability.py: Slot checking
- cancellation.py: 2-step workflow
- notifications.py: Async helpers
"""

from fastapi import APIRouter

# Import sub-routers
from .crud import router as crud_router
from .delete import router as delete_router
from .calendar import router as calendar_router
from .availability import router as availability_router
from .cancellation import router as cancellation_router

# Combine into single router
router = APIRouter()
router.include_router(crud_router)
router.include_router(delete_router)
router.include_router(calendar_router)
router.include_router(availability_router)
router.include_router(cancellation_router)

# Re-export for backwards compatibility
__all__ = ["router"]
```

### Service Modularization Pattern

For large service files, split by domain:

```
services/email_service.py  # 900+ lines ❌

services/email/
├── __init__.py           # Re-exports
├── templates.py          # Email templates
├── transactional.py      # Booking confirmations, receipts
├── marketing.py          # Campaigns, newsletters
├── smtp_client.py        # SMTP connection handling
└── tracking.py           # Open/click tracking
```

### When to Modularize (Checklist)

Before creating or modifying files, check:

- [ ] Is this file already over 500 lines?
- [ ] Will my changes push it over 500 lines?
- [ ] Does this file have 3+ distinct responsibilities?
- [ ] Are there logical groupings that could be separate modules?

**If YES to any:** Modularize BEFORE adding new code!

### Files Pending Modularization by Batch

Track large files and their target batch:

| File                                     | Lines | Batch   | Status                                          |
| ---------------------------------------- | ----- | ------- | ----------------------------------------------- |
| `routers/v1/bookings.py`                 | 2502  | Batch 1 | ✅ DONE → `routers/v1/bookings/` (9 files)      |
| `core/security.py`                       | 1085  | Batch 1 | ✅ DONE → `core/security/` (13 files)           |
| `utils/auth.py`                          | 1003  | Batch 1 | ✅ DONE → `utils/auth/` (8 files)               |
| `routers/v1/auth.py`                     | 634   | Batch 1 | ⚠️ MONITOR (close to limit, defer until growth) |
| `routers/v1/leads.py`                    | 629   | Batch 1 | ⚠️ MONITOR (close to limit, defer until growth) |
| `routers/v1/stripe.py`                   | 1196  | Batch 2 | 📋 FUTURE                                       |
| `routers/v1/admin_analytics.py`          | 1323  | Batch 2 | 📋 FUTURE                                       |
| `api/ai/orchestrator/ai_orchestrator.py` | 1535  | Batch 3 | 📋 FUTURE                                       |
| `routers/v1/newsletter.py`               | 963   | Batch 4 | 📋 FUTURE                                       |
| `routers/v1/admin_emails.py`             | 1168  | Batch 4 | 📋 FUTURE                                       |
| `main.py`                                | 1424  | Batch 1 | ⚠️ REVIEW (entry point - special handling)      |

### Scan for Large Files Command

```bash
# Find files over 500 lines that need modularization
Get-ChildItem -Path "apps/backend/src" -Recurse -Include "*.py" | `
  ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    if ($lines -gt 500) {
      [PSCustomObject]@{Lines=$lines; Path=$_.Name}
    }
  } | Sort-Object Lines -Descending
```

### Benefits of Modularization

1. **Faster Code Navigation** - Find code quickly by module name
2. **Reduced Merge Conflicts** - Smaller files = fewer conflicts
3. **Easier Testing** - Test modules in isolation
4. **Better Code Review** - Review smaller, focused PRs
5. **Cleaner Imports** - Import only what you need
6. **Single Responsibility** - Each module has one job

---

## �🔗 Related Documentation

- [01-CORE_PRINCIPLES.instructions.md](./01-CORE_PRINCIPLES.instructions.md)
  – Non-negotiables
- [07-TESTING_QA.instructions.md](./07-TESTING_QA.instructions.md) –
  Testing standards
- [10-COPILOT_PERFORMANCE.instructions.md](./10-COPILOT_PERFORMANCE.instructions.md)
  – Pre-commit review
- [19-DATABASE_SCHEMA_MANAGEMENT.instructions.md](./19-DATABASE_SCHEMA_MANAGEMENT.instructions.md)
  – Migration safety
- [20-SINGLE_SOURCE_OF_TRUTH.instructions.md](./20-SINGLE_SOURCE_OF_TRUTH.instructions.md)
  – SSoT architecture
- [21-BUSINESS_MODEL.instructions.md](./21-BUSINESS_MODEL.instructions.md)
  – Business rules

---

**Remember:** Quality is not a destination, it's a continuous journey.
Every commit should leave the codebase better than you found it.
