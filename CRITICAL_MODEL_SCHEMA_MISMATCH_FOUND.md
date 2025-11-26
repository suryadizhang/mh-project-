# 🔴 CRITICAL: Database Schema vs Model Mismatch Discovered

**Discovery Date**: November 26, 2025 **Severity**: CRITICAL -
Production Blocker **Impact**: Tests failing, models can't
insert/query data, potential data corruption risk

---

## Executive Summary

While fixing Bug #13 race condition tests, we discovered that
**SQLAlchemy models are completely out of sync with the actual
PostgreSQL database schema**. This affects multiple core tables and is
blocking all test execution.

**Root Cause**: Legacy model duplication + incomplete Alembic
migrations

---

## Affected Tables & Mismatches

### 1. `core.customers` Table

**Actual Database Schema** (PostgreSQL):

```sql
-- Columns in core.customers:
id: UUID
first_name: VARCHAR(100)
last_name: VARCHAR(100)
email_encrypted: TEXT              ❌ Model has: email (plaintext)
phone_encrypted: TEXT              ❌ Model has: phone (plaintext)
consent_sms: BOOLEAN               ❌ Model has: sms_notifications
consent_email: BOOLEAN             ❌ Model has: email_notifications
consent_updated_at: TIMESTAMP      ❌ Model missing this
timezone: VARCHAR(50)              ❌ Model missing this
tags: ARRAY                        ❌ Model missing this
notes: TEXT                        ❌ Model missing this
created_at: TIMESTAMP
updated_at: TIMESTAMP
deleted_at: TIMESTAMP              ❌ Model missing this
station_id: UUID (NOT NULL)        ❌ Model has this as Optional
```

**Python Model #1** (`models/customer.py` - DEPRECATED):

```python
# ⚠️ DEPRECATED: Maps to public.customers (doesn't exist)
email = Column(String(255))
phone = Column(String(20))
email_notifications = Column(Boolean)
sms_notifications = Column(Boolean)
# Missing: email_encrypted, phone_encrypted, consent_*, timezone, tags, notes, deleted_at
```

**Python Model #2** (`db/models/core.py` - "MODERN"):

```python
# Maps to core.customers but STILL wrong schema
email: Mapped[str]  # DB has email_encrypted
phone: Mapped[str]  # DB has phone_encrypted
marketing_consent: Mapped[bool]  # DB has consent_email, consent_sms
# Missing: timezone, tags, notes, deleted_at
```

**Impact**:

- ❌ Cannot create Customer records (field mismatch)
- ❌ All booking tests fail (foreign key to customers)
- ❌ Customer endpoints may be broken in production
- 🔴 **SECURITY RISK**: Models expect plaintext email/phone, DB
  expects encrypted

---

### 2. `identity.stations` Table

**Error**: `column "zip_code" of relation "stations" does not exist`

**Issue**: Model expects `zip_code`, database has different column
name or structure

**Impact**:

- ❌ Cannot create test fixtures (customers require station_id)
- ❌ Station-related endpoints may be broken

---

### 3. `core.bookings` Table (Partially Fixed)

**Status**: ✅ BookingStatus enum fixed (aligned with database)

**Remaining Issues**:

- ⚠️ Foreign key to customers table (customers can't be created)
- ⚠️ May have other column mismatches not yet discovered

---

## Legacy Model Duplication Problem

We have **THREE Customer model definitions**:

1. **`models/customer.py`** (DEPRECATED)
   - Maps to `public.customers` (table doesn't exist?)
   - Has deprecation warning
   - Wrong schema

2. **`db/models/core.py`** (MODERN)
   - Maps to `core.customers` (table exists)
   - Still has wrong schema
   - Missing encryption fields

3. **Actual Database** (`core.customers`)
   - Has encrypted fields
   - Has different consent field names
   - Has additional metadata fields

**Documentation Found**: `CUSTOMER_MODEL_DUPLICATION_ANALYSIS.md`
mentions this issue

---

## Current Workaround (Temporary)

For Bug #13 tests, we're using **raw SQL** to bypass the model:

```python
# tests/test_race_condition_fix.py
await db_session.execute(
    text("""
        INSERT INTO core.customers (
            id, station_id, first_name, last_name,
            email_encrypted, phone_encrypted,
            consent_sms, consent_email,
            timezone, tags, notes,
            created_at, updated_at
        )
        VALUES (...)
    """)
)
```

**Why This Is Bad**:

- ❌ Bypasses model validation
- ❌ No type safety
- ❌ Can't use ORM relationships
- ❌ Duplicates business logic
- ❌ Not maintainable

---

## Root Cause Analysis

### Why This Happened:

1. **Incomplete Migration**: Database schema was updated (added
   encryption, changed field names) but models weren't updated

2. **Model Duplication**: Two Customer models exist, causing confusion
   about which to use

3. **Missing Alembic Sync**: Alembic migrations don't match actual
   database state

4. **No Schema Validation**: No automated checks that models match
   database

5. **Tests Use Mocks**: Tests used Mock objects instead of real DB,
   hiding the schema mismatch

---

## Validation Commands Used

```bash
# Check actual database schema
python check_customer_columns.py
# Output: email_encrypted, phone_encrypted, consent_sms, consent_email...

# Check stations schema
python -c "from sqlalchemy import inspect; ..."
# Output: zip_code column doesn't exist

# Check BookingStatus enum
python check_status_column.py
# Output: ['new', 'deposit_pending', 'confirmed', 'completed', 'cancelled', 'no_show']
```

---

## Impact on Test Suite

**Bug #13 Race Condition Tests**: ❌ BLOCKED

- Can't create customer fixtures
- Can't create bookings (foreign key violation)
- **Status**: Using raw SQL workaround (not sustainable)

**Other Tests**: ⚠️ UNKNOWN

- Likely also failing if they use Customer model
- Need to audit all tests that touch customers table

---

## Recommended Fix (Industry Best Practice)

### Option A: Update Models to Match Database (FASTEST)

**Estimated Time**: 2-4 hours

**Steps**:

1. Update `db/models/core.py` Customer model to match actual database
   schema
2. Add encryption helper methods for email/phone
3. Update all endpoints to use encrypted fields
4. Add Alembic migration to document the changes
5. Delete deprecated `models/customer.py`
6. Update all imports to use `db.models.core.Customer`
7. Fix all tests to use real database entities (not mocks)

**Pros**:

- ✅ Preserves existing database data
- ✅ Follows existing database design (encryption)
- ✅ Can deploy immediately after fix

**Cons**:

- ⚠️ Need to audit all Customer usages (endpoints, services, tests)
- ⚠️ May break some endpoints temporarily

---

### Option B: Migrate Database to Match Models (DANGEROUS)

**Estimated Time**: 8-16 hours

**Steps**:

1. Create Alembic migration to rename columns
2. Decrypt email_encrypted → email
3. Update database schema
4. Delete deprecated models
5. Test all endpoints

**Pros**:

- ✅ Models stay unchanged
- ✅ No code changes needed (model side)

**Cons**:

- 🔴 **SECURITY RISK**: Removes encryption from PII
- 🔴 Requires database downtime
- 🔴 Need to migrate production data
- 🔴 Can't rollback easily

**Recommendation**: ❌ **DO NOT USE** (removes security feature)

---

### Option C: Generate Correct Models from Database (IDEAL)

**Estimated Time**: 4-6 hours

**Steps**:

1. Use SQLAlchemy's `automap_base()` or `sqlacodegen` to generate
   models from actual database
2. Review generated models
3. Add business logic methods
4. Replace existing models
5. Update all imports
6. Fix all tests

**Pros**:

- ✅ Guaranteed to match database
- ✅ Discovers ALL schema mismatches
- ✅ Industry standard approach

**Cons**:

- ⚠️ May reveal many more issues
- ⚠️ Need to re-add business logic to models

---

## Immediate Next Steps

### Step 1: Document All Schema Mismatches (30 minutes)

Create diagnostic script to compare ALL tables:

```python
# check_all_schema_mismatches.py
for table in ['customers', 'bookings', 'chefs', 'stations', ...]:
    db_columns = get_db_columns(table)
    model_columns = get_model_columns(table)
    compare_and_report_mismatches()
```

### Step 2: Fix Customer Model (1-2 hours)

Update `db/models/core.py`:

```python
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}

    # Match actual database schema
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    consent_sms: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(50))
    tags: Mapped[list] = mapped_column(ARRAY(String))
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)  # NOT OPTIONAL

    # Helper methods for encryption/decryption
    def get_email(self) -> str:
        return decrypt(self.email_encrypted)

    def set_email(self, email: str):
        self.email_encrypted = encrypt(email)
```

### Step 3: Delete Deprecated Models (15 minutes)

```bash
# Remove legacy model
rm apps/backend/src/models/customer.py

# Update all imports
grep -r "from models.customer import Customer" | # Find all usages
sed 's/from models.customer/from db.models.core/' | # Replace
```

### Step 4: Fix Stations Model (30 minutes)

Inspect `identity.stations` schema and update model to match.

### Step 5: Update Bug #13 Tests (30 minutes)

Replace raw SQL with proper Customer model usage:

```python
@pytest.fixture
async def customer(self, db_session):
    from db.models.core import Customer

    customer = Customer(
        id=uuid.uuid4(),
        station_id=station_id,  # From station fixture
        first_name="Test",
        last_name="Customer",
        email_encrypted=encrypt("test@example.com"),
        phone_encrypted=encrypt("+1234567890"),
        consent_sms=True,
        consent_email=True,
        timezone="America/New_York",
        tags=[],
        notes="Test customer"
    )
    db_session.add(customer)
    await db_session.commit()
    return customer
```

---

## Long-Term Prevention

### 1. Add Schema Validation to CI/CD

```python
# tests/test_schema_validation.py
def test_models_match_database_schema():
    """Ensure all SQLAlchemy models match actual database schema"""
    for model in [Customer, Booking, Chef, ...]:
        db_columns = get_db_columns(model.__tablename__)
        model_columns = get_model_columns(model)
        assert db_columns == model_columns, f"Schema mismatch in {model.__tablename__}"
```

### 2. Use Alembic Autogenerate Properly

```bash
# Generate migration to detect drift
alembic revision --autogenerate -m "Check for schema drift"
# Should generate EMPTY migration if models match DB
# If changes found: CRITICAL - schema drift detected
```

### 3. Enforce Single Source of Truth

**Rule**: ONE model per table, no duplicates

```python
# ✅ CORRECT
from db.models.core import Customer  # Single source

# ❌ WRONG
from models.customer import Customer  # Legacy, deprecated
```

### 4. Document Model-to-Table Mapping

Create `MODEL_TABLE_REGISTRY.md`:

```markdown
| Table     | Schema   | Model Location        | Status    |
| --------- | -------- | --------------------- | --------- |
| customers | core     | db/models/core.py     | ✅ Active |
| bookings  | core     | db/models/core.py     | ✅ Active |
| stations  | identity | db/models/identity.py | ✅ Active |
```

---

## Files to Clean Up

### Deprecated Models (DELETE):

- ❌ `apps/backend/src/models/customer.py` (DEPRECATED)
- ❌ `apps/backend/src/models/booking.py` (if deprecated version
  exists)
- ⚠️ Any other files in `models/` that duplicate `db/models/`

### Models to Update (FIX):

- 🔧 `apps/backend/src/db/models/core.py` (Customer, Booking schemas)
- 🔧 `apps/backend/src/db/models/identity.py` (Station schema)

### Tests to Update (FIX):

- 🔧 `tests/test_race_condition_fix.py` (remove raw SQL, use proper
  models)
- ⚠️ All other tests that use Customer model

### Documentation to Update:

- 📝 `CUSTOMER_MODEL_DUPLICATION_ANALYSIS.md` (update status)
- 📝 `CRITICAL_DATABASE_AUDIT_PRE_MIGRATION.md` (add findings)

---

## Decision Required

**Question for User**: Which approach do you want to take?

**Option A** (RECOMMENDED): Update models to match database (2-4
hours)

- ✅ Preserves encryption
- ✅ Fastest path to working tests
- ✅ Production-safe

**Option C** (IDEAL): Auto-generate models from database (4-6 hours)

- ✅ Discovers ALL mismatches
- ✅ Industry standard
- ⚠️ More time upfront, but prevents future issues

**My Recommendation**: Start with **Option A** to unblock Bug #13
tests, then do **Option C** as part of Phase 0 validation to catch all
other schema mismatches.

---

## Status

**Current State**: 🔴 BLOCKED - Cannot run Bug #13 tests without
schema fixes

**Workaround**: Using raw SQL (temporary, not sustainable)

**Next Action**: Awaiting decision on fix approach

**Priority**: CRITICAL - Must fix before any other Phase 0 work
