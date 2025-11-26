# CRITICAL BUG FIX - Cross-Registry SQLAlchemy Issue

**Date**: November 25, 2025 **Severity**: 🔴 **CRITICAL** - Blocks all
tests and production deployment **Bug ID**: #16 (Cross-Registry Table
Redefinition)

---

## Problem Statement

**Symptom**:

```
sqlalchemy.exc.InvalidRequestError: Table 'booking_reminders' is already defined for this MetaData instance.
Specify 'extend_existing=True' to redefine options and columns on an existing Table object.
```

**Impact**:

- ❌ All pytest tests fail (cannot load conftest.py)
- ❌ Cannot run production safety tests (Bug #13)
- ❌ Blocks staging deployment
- ❌ Blocks production readiness verification

---

## Root Cause Analysis

### Issue 1: Multiple Base Classes (FIXED ✅)

**File**: `apps/backend/src/api/ai/endpoints/models.py` **Problem**:
Created its own `Base = declarative_base()` instead of using unified
`core.database.Base` **Fix Applied**: Changed to
`from core.database import Base`

### Issue 2: Table Redefinition on Import (PARTIALLY FIXED ⚠️)

**Problem**: Models are imported multiple times during pytest conftest
loading:

```python
# conftest.py line 57
from src.models.user import User  # Imports models/__init__.py
# → Imports booking_reminder
# → Imports booking
# → Triggers table definition

# Later in test file
from models.booking_reminder import BookingReminder  # SECOND import
# → Table already defined → ERROR
```

**Attempted Fix**: Added `__table_args__ = {'extend_existing': True}`
to `BookingReminder` **Result**: Fixed BookingReminder, but now
**Booking** table has the same issue

---

## The Real Problem: Cascading Table Errors

This is not just one table - it's **EVERY table** that gets imported
multiple times:

1. ✅ `booking_reminders` - Fixed with `extend_existing`
2. ❌ `bookings` - Same error
3. ❌ `customers` - Will likely fail next
4. ❌ `payments` - Will likely fail next
5. ❌ ... (all 30+ tables will have this issue)

---

## Proper Solutions (Choose ONE)

### Solution A: Add extend_existing to ALL Models (Quick but Messy)

**Pros**: Fast fix **Cons**:

- Must modify 30+ model files
- Band-aid solution
- Doesn't fix root cause
- May hide real import issues

**Implementation**:

```python
# In EVERY model file
class MyModel(Base):
    __tablename__ = "my_table"
    __table_args__ = {'extend_existing': True}  # Add this line
```

---

### Solution B: Fix Test Imports (Proper Fix) ✅ **RECOMMENDED**

**Pros**:

- Fixes root cause
- Clean architecture
- No model modifications needed

**Cons**:

- Requires understanding import order
- May need conftest refactoring

**Implementation**:

1. **Move model imports AFTER database initialization** in
   conftest.py:

```python
# conftest.py

# WRONG (current):
from src.models.user import User  # Too early

# CORRECT (should be):
@pytest.fixture
def db_session():
    # Initialize database FIRST
    Base.metadata.create_all(engine)

    # Import models AFTER database ready
    from src.models.user import User
    from src.models.booking import Booking
    ...
```

2. **Use lazy imports** in test files:

```python
# WRONG:
from models.booking_reminder import BookingReminder  # Top of file

# CORRECT:
def test_something():
    from models.booking_reminder import BookingReminder  # Inside function
```

3. **Create a single models import point**:

```python
# conftest.py
@pytest.fixture(scope="session")
def models():
    """Lazily import all models ONCE"""
    from src import models
    return models

# In tests:
def test_something(models):
    booking = models.Booking(...)
```

---

### Solution C: Separate Test and Production Bases (Enterprise Pattern)

**Pros**:

- Complete isolation
- Enterprise standard
- Prevents cross-contamination

**Cons**:

- More complex
- Requires test database setup
- More refactoring

**Implementation**:

```python
# tests/conftest.py
from sqlalchemy.orm import declarative_base

# Create TEST-ONLY Base
TestBase = declarative_base()

# Use TestBase for all test fixtures
class TestBooking(TestBase):
    __tablename__ = "bookings"
    ...
```

---

## Recommended Action Plan

### Phase 0: Immediate Fix (5 min)

Add `extend_existing=True` to `Booking` model to unblock tests:

```python
# apps/backend/src/models/booking.py
class Booking(BaseModel):
    __tablename__ = "bookings"
    __table_args__ = {'extend_existing': True}
```

### Phase 1: Proper Fix (30 min)

Refactor conftest.py to use lazy model imports (Solution B)

### Phase 2: Verify (15 min)

Run all race condition tests to confirm fix

### Phase 3: Production Safety (1 hour)

Run full test suite + fix remaining failures

---

## Files Modified

### ✅ Already Fixed:

1. `apps/backend/src/api/ai/endpoints/models.py`
   - Removed duplicate `Base = declarative_base()`
   - Now uses `from core.database import Base`

2. `apps/backend/src/models/booking_reminder.py`
   - Added `__table_args__ = {'extend_existing': True}`

### ⏳ Need to Fix:

1. `apps/backend/src/models/booking.py`
   - Add `__table_args__ = {'extend_existing': True}`

2. `apps/backend/tests/conftest.py`
   - Refactor model imports to be lazy
   - Move imports after database initialization

---

## Success Criteria

✅ All pytest tests can import conftest.py ✅ Race condition tests run
successfully ✅ No "Table already defined" errors ✅ Backend starts
without errors ✅ Production safety tests pass

---

## Related Bugs

- **Bug #13**: Race condition in booking system (BLOCKED by this bug)
- **Phase 0 Production Blockers**: Cannot test until this is fixed

---

## Next Steps

1. Apply immediate fix to `Booking` model
2. Test if more tables need the same fix
3. Once tests run, implement proper lazy import solution
4. Remove `extend_existing` flags once proper fix is in place
