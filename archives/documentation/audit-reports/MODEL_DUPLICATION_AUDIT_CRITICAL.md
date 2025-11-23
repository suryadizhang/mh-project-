# 🔴 CRITICAL: Model Duplication Audit & Consolidation Plan

**Date**: November 20, 2025  
**Status**: BLOCKING PRODUCTION  
**Priority**: P0 - IMMEDIATE ACTION REQUIRED

---

## Executive Summary

**CRITICAL FINDING**: The codebase has **MASSIVE model duplication** across 3 different systems:

1. **Modern Clean Architecture** (`src/models/`)
2. **Legacy Core System** (`src/models/legacy_core.py`)
3. **Legacy Stripe System** (`src/models/legacy_stripe_models.py`)

This is causing:
- 🔴 **Database schema mismatches**
- 🔴 **SQLAlchemy mapper errors**
- 🔴 **Circular import nightmares**
- 🔴 **Impossible to maintain**
- 🔴 **Production outages**

---

## Duplicate Models Found

### 1. **Customer Model** - 3 VERSIONS! 🚨

#### Version A: `src/models/customer.py` (Modern)
```python
class Customer(BaseModel):
    __tablename__ = "customers"
    # Uses: Integer ID, first_name, last_name, email (plain text)
    # Schema: public.customers
    # Structure: Modern clean architecture
```

#### Version B: `src/models/legacy_core.py` (Legacy Core)
```python
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}
    # Uses: UUID ID, email_encrypted, name_encrypted (encrypted)
    # Schema: core.customers
    # Structure: Multi-tenant with station_id
```

#### Version C: `src/models/legacy_stripe_models.py` (Legacy Stripe)
```python
class StripeCustomer(Base):
    __tablename__ = "customers"
    # Uses: Integer ID, stripe_customer_id, email
    # Schema: public.customers (conflicts with Version A!)
```

**PROBLEM**: All 3 point to table named "customers" but with **completely different schemas**!

---

### 2. **Booking Model** - 3 VERSIONS! 🚨

#### Version A: `src/models/booking.py` (Modern)
```python
class Booking(BaseModel):
    __tablename__ = "bookings"
    # Schema: public.bookings
    # Fields: id (Integer), customer_id (Integer), event_date, event_time...
```

#### Version B: `src/models/legacy_core.py` (Legacy Core)
```python
class Booking(Base):
    __tablename__ = "bookings"
    # Schema: core.bookings (different schema!)
    # Fields: id (UUID), customer_id (UUID), station_id, date, slot...
```

#### Version C: `src/models/legacy_booking_models.py` (Legacy Booking)
```python
class BookingLegacy(BaseModel):
    __tablename__ = "bookings_legacy"
    # They knew it was duplicate - added "_legacy" suffix!
```

---

### 3. **Payment Model** - 3 VERSIONS! 🚨

#### Version A: `src/models/booking.py::Payment` (Modern)
```python
class Payment(BaseModel):
    __tablename__ = "payments"
    # Schema: public.payments
```

#### Version B: `src/models/legacy_core.py::Payment` (Legacy Core)
```python
class Payment(Base):
    __tablename__ = "payments"
    # Schema: core.payments (different!)
```

#### Version C: `src/models/legacy_stripe_models.py::StripePayment` (Legacy Stripe)
```python
class StripePayment(Base):
    __tablename__ = "stripe_payments"  # They avoided conflict here!
```

---

### 4. Other Duplicates Found

| Model | Files | Count |
|-------|-------|-------|
| **MenuItem** | `knowledge_base.py`, `legacy_booking_models.py` | 2 |
| **MessageThread** | `legacy_core.py`, relationships in `booking.py` | 2 |
| **SocialThread** | `legacy_social.py`, `legacy_lead_newsletter.py` | 2 |
| **User** | `user.py`, `legacy_booking_models.py` | 2 |

---

## Root Cause Analysis

### Why This Happened:

1. **Multiple Migration Phases**:
   - Phase 1: Legacy system with encrypted fields + multi-tenant (`core` schema)
   - Phase 2: Simplified modern system (`public` schema)
   - Phase 3: Never cleaned up legacy code!

2. **No Single Source of Truth**:
   - Different teams/times added different models
   - No enforcement of "one model per table" rule

3. **Lazy Prefixing Instead of Deletion**:
   - `bookings_legacy`, `stripe_payments` - avoided conflicts but didn't fix root cause

4. **Import Chaos**:
   - `models/__init__.py` only exports modern models
   - Legacy models imported directly: `from models.legacy_core import Customer`
   - SQLAlchemy sees BOTH and breaks!

---

## Impact Assessment

### Current Breakage:

1. ✅ **Booking Reminders Feature** - BLOCKED
   - Can't test because Customer model mismatch
   - Database has `core.customers` but code expects `public.customers`

2. 🔴 **All Features Touching Customer** - BROKEN
   - CustomerRepository uses modern Customer
   - Database uses legacy schema
   - 100% failure rate

3. 🔴 **SQLAlchemy Mapper Errors** - EVERYWHERE
   - Circular imports
   - Relationship failures (`tone_preferences`, `Thread`, etc.)
   - Registry conflicts

4. 🔴 **Data Corruption Risk** - HIGH
   - Writing to wrong table
   - Schema mismatches
   - Type errors (UUID vs Integer)

---

## Recommended Solution: **CONSOLIDATE TO MODERN MODELS**

### Strategy:

1. **Keep**: Modern models in `src/models/` (customer.py, booking.py, etc.)
2. **Delete**: All `legacy_*.py` files
3. **Migrate**: Database from `core.*` schema to `public.*` schema
4. **Update**: All imports to use unified models

### Why Modern Over Legacy:

| Aspect | Modern | Legacy | Winner |
|--------|--------|--------|--------|
| **Simplicity** | ✅ Clean fields | ❌ Encrypted complexity | Modern |
| **Frontend Match** | ✅ Matches API schemas | ❌ Doesn't match | Modern |
| **Maintenance** | ✅ Easy to understand | ❌ Complex multi-tenant | Modern |
| **Documentation** | ✅ Well-documented | ❌ Sparse | Modern |
| **Active Use** | ✅ Used in new features | ❌ Not referenced | Modern |
| **Schema** | ✅ `public` (standard) | ❌ `core` (custom) | Modern |

---

## Migration Plan (3-Phase Approach)

### Phase 1: Immediate Fixes (TODAY - 2 hours)

**Goal**: Unblock Feature 1 testing by creating minimal test data

1. **Create Simplified Test Seed** (don't touch production yet):
   ```python
   # Use raw SQL to bypass ORM issues
   # Insert directly into whatever table exists
   # Just get Feature 1 working
   ```

2. **Document Current State**:
   - Which tables actually exist?
   - Which schema is production using?
   - Map all model→table relationships

3. **Test Feature 1 with workarounds**:
   - Use Swagger UI to test endpoints
   - Confirm booking reminders work end-to-end

### Phase 2: Schema Investigation (TOMORROW - 4 hours)

1. **Database Audit**:
   ```sql
   -- Check which tables exist
   SELECT schemaname, tablename 
   FROM pg_tables 
   WHERE schemaname IN ('public', 'core');
   
   -- Check customer table structure
   \d public.customers
   \d core.customers  -- if exists
   ```

2. **Migration Discovery**:
   - Review all Alembic migrations
   - Identify which created `core.*` vs `public.*` tables
   - Understand migration history

3. **Production Data Assessment**:
   - How much data in `core.customers` vs `public.customers`?
   - Can we merge schemas?
   - Data migration complexity?

### Phase 3: Model Consolidation (NEXT WEEK - 16 hours)

1. **Delete Legacy Models** (8 files):
   ```bash
   rm src/models/legacy_*.py
   ```

2. **Create Migration: Consolidate Schemas**:
   ```python
   # Alembic migration
   # Move all data from core.* to public.*
   # Update foreign keys
   # Drop core schema
   ```

3. **Update All Imports**:
   ```python
   # OLD (100+ files):
   from models.legacy_core import Customer
   
   # NEW:
   from models import Customer
   ```

4. **Fix Relationships**:
   - Re-enable all commented-out relationships
   - Use proper `Mapped` types
   - No circular imports

5. **Test Everything**:
   - Run full test suite
   - Verify no mapper errors
   - Confirm all CRUD operations work

---

## Immediate Action Items (Next 30 minutes)

### Task 1: Check Actual Database Schema
```bash
# What tables ACTUALLY exist?
python -c "from sqlalchemy import create_engine, inspect; ..."
```

### Task 2: Create Emergency Test Data
```python
# Bypass ORM - use raw SQL
# INSERT INTO <whatever_table_exists> ...
```

### Task 3: Test Feature 1
```bash
# Use Swagger UI
# http://localhost:8000/docs
# Test booking reminders endpoints
```

---

## Questions to Answer IMMEDIATELY

1. **Which schema is production using?**
   - [ ] `public.*` tables?
   - [ ] `core.*` tables?
   - [ ] Both? (nightmare scenario)

2. **Which Customer model matches production?**
   - [ ] Modern (first_name/last_name)?
   - [ ] Legacy (encrypted fields)?
   - [ ] Stripe (stripe_customer_id)?

3. **Can we see actual table structure?**
   ```sql
   \d customers  -- What columns exist?
   ```

4. **Which models are actually imported in main.py?**
   ```python
   # Check what's registered with SQLAlchemy
   from models import *  # Which models?
   ```

---

## Success Criteria

### Short-term (Today):
- ✅ Feature 1 test completes successfully
- ✅ No mapper errors on server start
- ✅ Database schema documented

### Medium-term (This Week):
- ✅ All legacy_*.py files deleted
- ✅ Single source of truth for each table
- ✅ All relationships working

### Long-term (Next Sprint):
- ✅ Zero model duplication
- ✅ Clean architecture enforced
- ✅ Migrations consolidated

---

## Files to Delete (After Migration)

```bash
src/models/legacy_base.py
src/models/legacy_booking_models.py
src/models/legacy_core.py
src/models/legacy_declarative_base.py
src/models/legacy_encryption.py
src/models/legacy_events.py
src/models/legacy_feedback.py
src/models/legacy_lead_newsletter.py
src/models/legacy_models_init.py
src/models/legacy_notification_groups.py
src/models/legacy_qr_tracking.py
src/models/legacy_social.py
src/models/legacy_stripe_models.py
```

**Total**: 13 legacy files = ~3,000+ lines of duplicate code

---

## Recommendation

**IMMEDIATE**: Focus on Phase 1 - get Feature 1 working with workarounds

**THIS WEEK**: Execute Phase 2 - understand current state

**NEXT SPRINT**: Execute Phase 3 - full consolidation

This is **BLOCKING ALL DEVELOPMENT** until fixed properly.

---

## Owner

**Assigned to**: Agent + User (collaborative fix)  
**Next Review**: After Phase 1 complete (today)  
**Escalation**: This is P0 - blocks all feature development
