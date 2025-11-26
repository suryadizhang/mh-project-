# Customer Model Duplication Analysis 🔍

**Date**: January 2025 **Issue**: Three different Customer models
exist in the codebase **Status**: ⚠️ **ARCHITECTURAL PROBLEM** - Needs
resolution

---

## Summary

We have **THREE different Customer models** mapping to **TWO different
tables**:

| Model          | Location                  | Table       | Schema   | Purpose                              | Status      |
| -------------- | ------------------------- | ----------- | -------- | ------------------------------------ | ----------- |
| **Customer**   | `db.models.core`          | `customers` | `core`   | ✅ **PRIMARY** - Core business model | Production  |
| **Customer**   | `models.customer`         | `customers` | `public` | ⚠️ **LEGACY** - Old model            | Deprecated  |
| **AICustomer** | `api.ai.endpoints.models` | `customers` | `public` | ⚠️ **DUPLICATE** - Growth tracking   | Unnecessary |

---

## Detailed Analysis

### Model #1: `db.models.core.Customer` ✅ **PRIMARY**

**File**: `apps/backend/src/db/models/core.py` (Line 210)

**Schema**: `core.customers` (PostgreSQL schema-qualified)

**Columns**:

```python
# Primary Key
id: UUID

# Contact Info
first_name: str
last_name: str
email: str (unique, indexed)
phone: str (indexed)

# Preferences
preferred_contact_method: Optional[str]
dietary_restrictions: Optional[str]

# Marketing
marketing_consent: bool

# Metadata
customer_metadata: JSONB
station_id: UUID (FK to identity.stations)

# Timestamps
created_at: DateTime(tz=True)
updated_at: DateTime(tz=True)
```

**Relationships**:

- `bookings` → List[Booking]
- `message_threads` → List[MessageThread]

**Usage**: ✅ **Core business operations**

- Booking system
- Customer service messages
- Station management

**Architecture**: ✅ **Modern (New Architecture)**

- Uses SQLAlchemy 2.0 `Mapped[]` type hints
- Schema-qualified (`core` schema)
- Proper timezone handling
- JSONB for flexible metadata

---

### Model #2: `models.customer.Customer` ⚠️ **LEGACY**

**File**: `apps/backend/src/models/customer.py` (Line 34)

**Schema**: `public.customers` (default schema)

**Columns**:

```python
# Primary Key
id: Integer (auto-increment)

# Contact Info
first_name: str
last_name: str
email: str (unique, indexed)
phone: str (indexed)

# Status
status: Enum (active/inactive/suspended/vip)
dietary_preferences: Text (JSON string)
special_notes: Text

# Communication
email_notifications: bool
sms_notifications: bool
marketing_emails: bool

# Profile
date_of_birth: DateTime
anniversary_date: DateTime

# Loyalty
loyalty_points: int
total_visits: int
total_spent: int (cents)

# Activity
last_booking_date: DateTime
last_visit_date: DateTime
```

**Relationships**:

- `bookings` → List[Booking] (qualified path:
  "models.booking.Booking")
- `escalations` → List[Escalation]

**Usage**: ⚠️ **Legacy code**

- Old booking system
- Some admin endpoints
- Growth tracker (uses this model!)

**Architecture**: ⚠️ **Old Architecture**

- Uses old SQLAlchemy style (no `Mapped[]`)
- Public schema (default)
- Inherits from `BaseModel` (deprecated base)
- Has `extend_existing=True` (band-aid fix)

---

### Model #3: `api.ai.endpoints.models.AICustomer` ⚠️ **DUPLICATE**

**File**: `apps/backend/src/api/ai/endpoints/models.py` (Line 354)

**Schema**: `public.customers` (same as legacy model!)

**Columns**:

```python
# Primary Key
id: String(36) (UUID as string)

# Contact Info
email: str (unique, indexed)
name: str (DIFFERENT from first_name/last_name!)
phone: str

# Timestamps
created_at: DateTime
updated_at: DateTime
```

**Relationships**:

- `conversations` → List[Conversation] (AI chat conversations)

**Usage**: ⚠️ **Minimal**

- Only used by `Conversation` model for foreign key
- Intended for growth tracking (customer count monitoring)
- **NOT actually used by growth_tracker.py!**

**Architecture**: ⚠️ **Problematic**

- Simplified schema (missing most customer fields)
- Uses `name` instead of `first_name`/`last_name`
- Has `extend_existing=True` (trying to map to same table as legacy)
- **Created to avoid cross-registry issues but created NEW issues**

---

## The Problem 🚨

### Issue #1: Schema Mismatch

AICustomer has **different columns** than legacy Customer:

- AICustomer: `name` (single column)
- Legacy Customer: `first_name`, `last_name` (two columns)

**Result**: They **CANNOT** map to the same table!

### Issue #2: Growth Tracker Confusion

`growth_tracker.py` imports **legacy Customer**, NOT AICustomer:

```python
# File: api/ai/monitoring/growth_tracker.py
from models.customer import Customer  # ← Uses LEGACY model!
```

But `Conversation` model references AICustomer:

```python
# File: api/ai/endpoints/models.py
customer_id = Column(String(36), ForeignKey("customers.id"))
customer = relationship("AICustomer", back_populates="conversations")
```

**Result**: Foreign key points to `public.customers`, but core
business uses `core.customers`!

### Issue #3: Three Models, Two Tables

```
db.models.core.Customer     → core.customers     (UUID id, first_name, last_name)
models.customer.Customer    → public.customers   (Integer id, first_name, last_name)
ai.endpoints.AICustomer     → public.customers   (String id, name)
                              ↑ SAME TABLE!
```

**Result**: Two models fighting for same table with incompatible
schemas!

---

## Business Logic Impact 🎯

### Which Customer is "Real"?

**Answer**: **`db.models.core.Customer`** (core schema)

**Evidence**:

1. ✅ Used by `core.Booking` model
2. ✅ Schema-qualified (isolated from public schema)
3. ✅ Modern SQLAlchemy 2.0 architecture
4. ✅ Proper timezone handling
5. ✅ Matches current database migration state

### Legacy Model (`models.customer.Customer`)

**Status**: **Deprecated but still used**

**Still Used By**:

1. ⚠️ `growth_tracker.py` - Customer count monitoring
2. ⚠️ Some admin endpoints
3. ⚠️ Old booking code (if any)

**Should Reference**: `core.Customer` instead

### AICustomer Model

**Status**: **Unnecessary - Should be removed**

**Why It Exists**:

- Created during AI features development
- Attempt to avoid cross-registry issues
- Simplified schema for "just counting customers"

**Why It's Wrong**:

1. ❌ Duplicates existing customer data
2. ❌ Different schema (name vs first_name/last_name)
3. ❌ Not actually used by growth tracker
4. ❌ Creates foreign key ambiguity
5. ❌ `extend_existing=True` is a band-aid

---

## Correct Architecture 🏗️

### What It Should Be:

```
┌─────────────────────────────────────┐
│ SINGLE SOURCE OF TRUTH              │
│ db.models.core.Customer             │
│ Table: core.customers               │
└─────────────────────────────────────┘
           ▲         ▲         ▲
           │         │         │
     ┌─────┘    ┌────┘    └─────┐
     │          │               │
Bookings   Messages      AI Conversations
(core)     (core)        (relationships)
```

**All code should import**: `from db.models.core import Customer`

---

## Migration Plan 🔧

### Step 1: Update Growth Tracker ✅ **HIGH PRIORITY**

**File**: `apps/backend/src/api/ai/monitoring/growth_tracker.py`

**Change**:

```python
# BEFORE
from models.customer import Customer

# AFTER
from db.models.core import Customer
```

**Impact**: Growth tracker will count customers from `core.customers`
(correct table)

---

### Step 2: Update AI Conversation Model ✅ **HIGH PRIORITY**

**File**: `apps/backend/src/api/ai/endpoints/models.py`

**Option A: Remove customer relationship** (Simple)

```python
class Conversation(Base):
    # Remove these:
    # customer_id = Column(...)
    # customer = relationship("AICustomer", ...)

    # Keep user identification in metadata:
    user_id = Column(String(255))  # External identifier
    channel_metadata = Column(JSON)  # Phone, email, etc.
```

**Option B: Use core.Customer** (Complex - requires schema change)

```python
from db.models.core import Customer

class Conversation(Base):
    customer_id = Column(PGUUID, ForeignKey("core.customers.id"))
    customer = relationship("Customer", back_populates="conversations")
```

**Recommendation**: **Option A** - AI conversations don't need
customer FK

- `user_id` already tracks identity
- `channel_metadata` has contact info
- Avoids cross-schema FK complexity

---

### Step 3: Delete AICustomer Model ✅ **MEDIUM PRIORITY**

**File**: `apps/backend/src/api/ai/endpoints/models.py`

**Action**: Delete entire `AICustomer` class (lines 354-378)

**Prerequisites**:

- ✅ Step 1 complete (growth tracker updated)
- ✅ Step 2 complete (conversation FK removed)
- ✅ Verify no other code imports AICustomer

---

### Step 4: Deprecate Legacy Customer ⚠️ **LOW PRIORITY**

**File**: `apps/backend/src/models/customer.py`

**Action**: Add deprecation warning, plan migration

**Migration Path**:

1. Find all imports of `models.customer.Customer`
2. Replace with `db.models.core.Customer`
3. Update any code expecting `public.customers` table
4. Eventually delete `models/customer.py`

**Complexity**: **HIGH** - requires full codebase search

---

## Testing Impact 🧪

### Current Test Issue

**Test**: `test_race_condition_fix.py`

**Error**:
`TypeError: 'name' is an invalid keyword argument for Customer`

**Root Cause**: Test uses legacy `models.customer.Customer` which
expects `first_name`/`last_name`, not `name`

**Fix Applied**: ✅ Changed fixture to use
`first_name="Test", last_name="Customer"`

---

## Recommendations 📋

### Immediate Actions (Before Production)

1. ✅ **Fix growth tracker** - Change import to
   `db.models.core.Customer`
2. ✅ **Remove AICustomer FK** - Option A (remove customer
   relationship)
3. ✅ **Delete AICustomer model** - No longer needed
4. ⚠️ **Document legacy model** - Mark as deprecated
5. ⚠️ **Update tests** - Use core.Customer in new tests

### Long-Term Actions (Post-Production)

1. 🔄 **Migrate all code to core.Customer**
2. 🔄 **Delete models/customer.py** (legacy model)
3. 🔄 **Drop public.customers table** (if safe)
4. 🔄 **Update documentation** - Single customer model

---

## Risk Assessment ⚠️

### Current Risk: **MEDIUM**

**Why**:

- ✅ Production uses `core.customers` (safe)
- ⚠️ Growth tracker uses wrong table (monitoring inaccurate)
- ⚠️ AI conversations have broken FK (customer_id never populated)
- ❌ Schema conflicts block test execution (Bug #16)

### If Not Fixed:

1. 📊 **Growth tracker counts wrong table** - May miss 1,000 customer
   threshold
2. 💔 **AI conversation customer_id always NULL** - Cannot link to
   customers
3. 🐛 **Future developers confused** - Which Customer to use?
4. 🧪 **Tests fail or give false results** - Using wrong model

### After Fix:

1. ✅ **Single source of truth** - `db.models.core.Customer`
2. ✅ **Growth tracker accurate** - Counts core.customers
3. ✅ **AI conversations simplified** - No customer FK needed
4. ✅ **Tests reliable** - Using production model

---

## Summary

**Problem**: Three Customer models, two tables, schema conflicts

**Root Cause**:

- Legacy model (`models.customer`) not migrated to new architecture
- AICustomer created to work around cross-registry issues
- Growth tracker never updated to use core model

**Solution**:

1. Update growth tracker → use `db.models.core.Customer`
2. Remove AICustomer.customer relationship → use user_id instead
3. Delete AICustomer model → no longer needed
4. Deprecate legacy Customer → migrate over time

**Priority**: **HIGH** - Affects production monitoring and data
integrity

**Effort**: 2-3 hours

**Impact**: Fixes monitoring, simplifies architecture, resolves Bug
#16

---

**Next Step**: Should I implement the migration plan?
