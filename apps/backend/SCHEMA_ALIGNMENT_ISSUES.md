# Critical Schema and Model Alignment Issues Discovered

## Date: 2025-10-23
## Status: **BLOCKED** - Tests Cannot Run Due to Model/Schema Misalignment

---

## Problem Summary

During MEDIUM #34 (Database Query Optimization) test execution, discovered **critical architectural issues** with multiple conflicting ORM model definitions and schema mismatches blocking all tests.

## Root Causes

### 1. **Multiple Conflicting Booking Models**
- **`booking_models.Booking`** (old, complex schema):
  - Location: `src/api/app/models/booking_models.py`
  - Schema: Originally public schema, now migrated to core
  - Fields: `user_id`, `customer_name`, `customer_email`, `booking_reference`, `venue_street`, etc.
  - Used by: Test fixtures (`conftest.py`)
  
- **`core.Booking`** (new, simple schema):
  - Location: `src/api/app/models/core.py`
  - Schema: Expects core schema
  - Fields: `station_id`, `customer_id` (FK to core.customers), `date`, `slot`, pricing fields
  - Used by: API routers (`routers/bookings.py`)

**Conflict**: Routers query for `core.Booking` structure, but database has `booking_models.Booking` structure.

### 2. **Multiple Declarative Bases**
- **`booking_models.Base`**: `src/api/app/models/booking_models.py`
- **`core.Base`**: `src/api/app/models/core.py`
- **`events.Base`**: `src/api/app/models/events.py`
- **`auth.Base`**: `src/api/app/auth/models.py`
- **`station_models.Base`**: `src/api/app/auth/station_models.py`

**Conflict**: ForeignKey relationships across different Base classes cause initialization errors:
```
sqlalchemy.exc.InvalidRequestError: When initializing mapper Mapper[Station(stations)], 
expression 'Booking.station_id' failed to locate a name ("name 'Booking' is not defined")
```

### 3. **Schema Organization Issues**
- **core schema**: Should contain bookings, customers, payments (simplified CRM models)
- **identity schema**: Should contain stations (multi-tenant isolation)
- **public schema**: Contains users, addon_items, booking_availability, etc. (legacy models)

**Current State**:
- ✅ core schema exists with tables migrated from public
- ✅ identity schema created
- ❌ Tables have OLD structure (booking_models.Booking) but NEW queries (core.Booking)
- ❌ ForeignKey constraints reference non-existent tables or columns

## Timeline of Fixes Attempted

### Session Start → 30 minutes in:
1. ✅ Created core schema
2. ✅ Migrated bookings, payments, customers tables (600+300+100 rows)
3. ✅ Updated conftest.py search_path: `SET search_path TO core, identity, public`
4. ✅ Updated booking_models.Booking: Added `__table_args__ = {"schema": "core"}`
5. ✅ Updated stripe_models.Payment: Added `__table_args__ = {"schema": "core"}`

**Result**: Test failed with `column bookings.customer_id does not exist`

### 30 minutes → 60 minutes in:
6. ✅ Updated conftest.py to import core models: `from api.app.models.core import Booking, Customer, Payment`
7. ✅ Rewrote `create_test_bookings` fixture to use core.Booking structure
8. ✅ Rewrote `create_test_payments` fixture to use core.Payment structure
9. ✅ Updated 4 ForeignKey references to use fully qualified names:
   - BookingMenuItem: `ForeignKey("core.bookings.id")`
   - BookingAddon: `ForeignKey("core.bookings.id")`
   - Refund: `ForeignKey("core.payments.id")`
   - Dispute: `ForeignKey("core.payments.id")`

**Result**: Test failed with `relation "identity.stations" does not exist`

### 60 minutes → 90 minutes in:
10. ✅ Created identity schema
11. ✅ Created identity.stations table (manual SQL)
12. ✅ Updated conftest.py to create test station using raw SQL
13. ✅ Updated search_path: `SET search_path TO core, identity, public`

**Result**: Test failed with SQLAlchemy relationship initialization error (Station → Booking cross-Base reference)

###  90 minutes → 120 minutes in:
14. ❌ Attempted to create proper table structure using `CoreBase.metadata.create_all()`

**Result**: Failed - ForeignKey can't resolve identity.stations because of cross-Base reference issues

## Correct Solution (Not Yet Implemented)

### Option A: Consolidate to Single Base (RECOMMENDED)
1. **Merge all models into one declarative_base()**
   - Create `src/api/app/models/__init__.py` with single Base
   - Import all models through this single Base
   - Update all model files to use shared Base

2. **Align Database Schema**
   - Drop all existing tables
   - Recreate using `Base.metadata.create_all()`
   - Ensures perfect alignment between ORM and database

3. **Update All Imports**
   - Change `from api.app.models.booking_models import Base` → `from api.app.models import Base`
   - Ensure consistent model usage across routers and tests

**Effort**: 4-6 hours
**Risk**: Medium (requires coordination across many files)
**Benefit**: Permanent fix, proper architecture

### Option B: Disable Foreign Keys for Testing (QUICK FIX)
1. **Make station_id nullable in core models**
   ```python
   station_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
   ```

2. **Remove FK constraint temporarily**
   ```python
   # station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), ...)
   station_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)  # No FK
   ```

3. **Use raw UUIDs in tests**
   - No need to create stations table
   - Tests focus on pagination performance, not referential integrity

**Effort**: 30 minutes
**Risk**: Low (only affects tests)
**Benefit**: Unblocks testing immediately

### Option C: Use booking_models Everywhere (ROLLBACK)
1. **Update routers to use booking_models.Booking**
   - Change `from api.app.models.core import Booking` → `from api.app.models.booking_models import Booking`
   - Update field names in queries (customer_id → user_id, etc.)

2. **Keep test fixtures as-is**
   - Already using booking_models.Booking

3. **Adjust pagination logic**
   - Update response mapping to match booking_models fields

**Effort**: 2-3 hours
**Risk**: Low (less invasive)
**Benefit**: Uses existing, stable schema

## Immediate Recommendation

**Implement Option B (Quick Fix)** to unblock testing, then plan Option A (Proper Fix) for next sprint.

### Quick Fix Steps:
1. Edit `src/api/app/models/core.py`:
   ```python
   # Customer model - line 35
   # station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
   station_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)  # FK removed for testing
   
   # Booking model - line 78
   # station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
   station_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)  # FK removed for testing
   ```

2. Drop and recreate core tables:
   ```sql
   DROP TABLE IF EXISTS core.payments CASCADE;
   DROP TABLE IF EXISTS core.bookings CASCADE;
   DROP TABLE IF EXISTS core.customers CASCADE;
   
   -- Then run Python script to create from models
   python -c "
   import asyncio
   from api.app.database import engine
   from api.app.models.core import Base
   async def create():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   asyncio.run(create())
   "
   ```

3. Run tests:
   ```bash
   pytest tests/test_api_performance.py -v
   ```

**Estimated Time**: 15 minutes
**Success Criteria**: First test passes, demonstrating pagination performance

## Files Modified This Session

1. **conftest.py** - Multiple updates to fixtures and imports
2. **booking_models.py** - Added schema specification, updated ForeignKeys
3. **stripe_models.py** - Added schema specification, updated ForeignKeys
4. **create_core_schema.py** - Created (200 lines) - Migration script
5. **setup_test_schema.py** - Created (45 lines) - Schema setup script
6. **check_identity_schema.py** - Created (16 lines) - Schema verification
7. **TEST_INFRASTRUCTURE_VALIDATION.md** - Created (300 lines) - Status report
8. **SCHEMA_MIGRATION_COMPLETE.md** - Created (250 lines) - Migration docs

## Next Steps

1. **Immediate** (Today): Implement Option B quick fix to unblock testing
2. **Short-term** (This Week): Complete MEDIUM #34 performance testing with quick fix in place
3. **Medium-term** (Next Sprint): Implement Option A to properly consolidate models
4. **Long-term** (Future): Consider migrating to Alembic for proper schema versioning

## Lessons Learned

1. **Multiple declarative_base() instances create integration hell** - Always use a single shared Base
2. **Schema migrations must be tracked** - Need Alembic or similar tool
3. **Test fixtures must match production schemas** - Drift causes false positives/negatives
4. **Foreign keys across schemas require careful planning** - Especially with multi-tenant designs

---

**Status**: Documented and ready for decision on which path forward
**Blocking**: All performance tests (MEDIUM #34)
**Priority**: **CRITICAL** - Required to validate optimization work
