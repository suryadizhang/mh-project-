# 🔥 NUCLEAR MODEL CONSOLIDATION - EXECUTION PLAN

**Date**: November 20, 2025  
**Priority**: P0 - ARCHITECTURAL FOUNDATION  
**Duration**: 1 Day (Systematic Cleanup)  
**Status**: IN PROGRESS

---

## Phase 1: Complete Audit (30 min) ✅ COMPLETE

### Findings Summary:

**DUPLICATE MODELS FOUND:**
1. ✅ Customer - 3 versions (customer.py, legacy_core.py, legacy_stripe_models.py)
2. ✅ Booking - 3 versions (booking.py, legacy_core.py, legacy_booking_models.py)
3. ✅ Payment - 3 versions (booking.py, legacy_core.py, legacy_stripe_models.py)
4. ✅ MenuItem - 2 versions (knowledge_base.py, legacy_booking_models.py)
5. ✅ User - 2 versions (user.py, legacy_booking_models.py)
6. ✅ MessageThread - 2 versions (legacy_core.py, relationship references)
7. ✅ SocialThread - 2 versions (legacy_social.py, legacy_lead_newsletter.py)

**PRODUCTION DATABASE REALITY:**
- Schema: `public` (has data: 1 customer, 7 bookings)
- Schema: `core` (empty - 0 rows everywhere)
- Schema: `identity` (auth system - keep separate)

**DECISION:** Use `public` schema with modern clean architecture models

---

## Phase 2: Model Consolidation Strategy (NOW)

### 2.1 Keep (Modern Clean Architecture):
```
src/models/
├── base.py              ✅ KEEP - Base model class
├── customer.py          🔧 FIX - Update to match public.customers
├── booking.py           🔧 FIX - Update to match public.bookings
├── booking_reminder.py  ✅ KEEP - Feature 1 (already correct)
├── payment_notification.py ✅ KEEP
├── review.py            ✅ KEEP
├── user.py              ✅ KEEP
├── role.py              ✅ KEEP
├── business.py          ✅ KEEP
├── audit.py             ✅ KEEP
├── escalation.py        ✅ KEEP
├── knowledge_base.py    ✅ KEEP
├── call_recording.py    ✅ KEEP
├── system_event.py      ✅ KEEP
├── terms_acknowledgment.py ✅ KEEP
└── station.py           ✅ KEEP
```

### 2.2 Delete (Legacy Duplicates):
```
src/models/
├── legacy_base.py                    ❌ DELETE
├── legacy_booking_models.py          ❌ DELETE
├── legacy_core.py                    ❌ DELETE
├── legacy_declarative_base.py        ❌ DELETE
├── legacy_encryption.py              ❌ DELETE
├── legacy_events.py                  ❌ DELETE
├── legacy_feedback.py                ❌ DELETE
├── legacy_lead_newsletter.py         ❌ DELETE
├── legacy_models_init.py             ❌ DELETE
├── legacy_notification_groups.py     ❌ DELETE
├── legacy_qr_tracking.py             ❌ DELETE
├── legacy_social.py                  ❌ DELETE
└── legacy_stripe_models.py           ❌ DELETE
```

**Total to delete**: 13 files (~4,000 lines of duplicate code)

---

## Phase 3: Fix Modern Models to Match Production DB (2 hours)

### 3.1 Fix Customer Model ⏳

**Current Issues:**
- ❌ Uses `Integer` id (DB has `VARCHAR`)
- ❌ Has `first_name`, `last_name` (DB has single `name`)
- ❌ Missing `stripe_customer_id`, `user_id`

**Solution:** Complete rewrite to match `public.customers`

### 3.2 Fix Booking Model ⏳

**Current Issues:**
- ❌ `customer_id` is `Integer` (should be `String` to match customers.id)
- ❌ Has relationships to deleted legacy models

**Solution:** Update foreign key types

### 3.3 Fix Payment Model ⏳

**Current Issues:**
- ❌ In booking.py as nested class
- ❌ Missing fields from production

**Solution:** Extract to separate file, match production schema

---

## Phase 4: Delete Legacy Files (30 min)

### Deletion Checklist:
- [ ] Backup legacy files (move to /archive folder)
- [ ] Delete all legacy_*.py from src/models/
- [ ] Update src/models/__init__.py (remove legacy imports)
- [ ] Verify no import errors

---

## Phase 5: Fix All Imports (2 hours)

### Search & Replace Strategy:

1. **Find all legacy imports:**
```bash
grep -r "from models.legacy_" apps/backend/src/
grep -r "from .legacy_" apps/backend/src/
grep -r "import legacy_" apps/backend/src/
```

2. **Replace with modern imports:**
```python
# OLD:
from models.legacy_core import Customer, Booking
from models.legacy_stripe_models import StripeCustomer

# NEW:
from models import Customer, Booking
```

3. **Update affected files:**
- Services (repositories, services/)
- API endpoints (api/v1/, routers/)
- CQRS operations (cqrs/)
- Tests (tests/)

---

## Phase 6: Database Migration (1 hour)

### 6.1 Create Migration: Align Customer Table

```python
# Migration: align_customer_with_production

def upgrade():
    # Option A: Add missing columns to existing customers table
    op.add_column('customers', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    # ... (or use ALTER TABLE to match exactly)
    
    # Option B: Drop and recreate (if no production data to preserve)
    # Only if approved!
```

### 6.2 Drop Core Schema Tables (if empty)

```sql
-- Only if core.* tables confirmed empty
DROP SCHEMA core CASCADE;
```

---

## Phase 7: Verification & Testing (2 hours)

### 7.1 Server Startup Test
- [ ] No import errors
- [ ] No SQLAlchemy mapper errors
- [ ] All routes registered

### 7.2 Database Connection Test
- [ ] All models can query database
- [ ] No schema mismatch errors
- [ ] Foreign keys work

### 7.3 Feature 1 Test
- [ ] Booking reminders CRUD works
- [ ] Can create test data
- [ ] All endpoints respond

### 7.4 Integration Tests
- [ ] Run full test suite
- [ ] Fix any broken tests
- [ ] Update test fixtures

---

## Phase 8: Documentation (1 hour)

### 8.1 Update Documentation
- [ ] Architecture diagram (single model layer)
- [ ] Database schema documentation
- [ ] Migration history
- [ ] API documentation

### 8.2 Create Maintenance Guide
- [ ] "How to add new models" (prevent future duplication)
- [ ] Model naming conventions
- [ ] Import patterns
- [ ] Testing requirements

---

## Execution Order (Chronological)

### Hour 1-2: Model Fixes
1. ✅ Backup all legacy files
2. 🔧 Fix customer.py to match production
3. 🔧 Fix booking.py foreign keys
4. 🔧 Extract payment.py if needed

### Hour 3: Legacy Cleanup
5. ❌ Delete all legacy_*.py files
6. 🔧 Update models/__init__.py
7. ✅ Verify server starts (with warnings OK)

### Hour 4-5: Import Fixes
8. 🔍 Find all legacy imports (grep)
9. 🔧 Replace with modern imports
10. ✅ Fix compilation errors

### Hour 6: Database Migration
11. 🔧 Create alignment migration
12. ✅ Test migration on dev DB
13. ✅ Apply migration

### Hour 7: Testing
14. ✅ Manual API testing (Swagger)
15. ✅ Feature 1 end-to-end test
16. ✅ Run test suite

### Hour 8: Documentation & Cleanup
17. 📝 Document changes
18. 📝 Create prevention guide
19. ✅ Git commit with detailed message
20. 🎉 Celebrate clean architecture!

---

## Risk Mitigation

### Backup Strategy:
```bash
# Before any changes:
mkdir -p backups/pre-nuclear-cleanup-$(date +%Y%m%d)
cp -r src/models backups/pre-nuclear-cleanup-$(date +%Y%m%d)/
```

### Rollback Plan:
- Keep legacy files in /archive for 1 sprint
- Tag current commit before changes
- Document all import changes for easy revert

### Testing Gates:
- ✅ Gate 1: Server must start without errors
- ✅ Gate 2: At least 1 CRUD operation must work
- ✅ Gate 3: Feature 1 must pass manual test
- ✅ Gate 4: No regression in existing features

---

## Success Metrics

### Before (Current State):
- ❌ 26 model files (13 legacy duplicates)
- ❌ 3 Customer models
- ❌ 3 Booking models
- ❌ 2 schemas (public + core)
- ❌ Schema mismatches everywhere
- ❌ Cannot seed test data
- ❌ Circular import errors

### After (Target State):
- ✅ 13 model files (zero legacy)
- ✅ 1 Customer model (matches production)
- ✅ 1 Booking model (correct FKs)
- ✅ 1 schema (public only)
- ✅ All models match database
- ✅ Test data seeds successfully
- ✅ Zero import errors

---

## Next Steps (Immediate)

**Ready to execute?** Confirm to proceed with:

1. **Backup** all legacy files
2. **Fix** customer.py and booking.py
3. **Delete** all legacy_*.py files
4. **Fix** all imports across codebase
5. **Test** everything works

**Estimated Time**: 6-8 hours focused work  
**Point of No Return**: After deleting legacy files (but we have backups)  
**Expected Outcome**: Clean, maintainable, single-source-of-truth architecture

---

## Owner: Agent + User (Pair Programming)
**Status**: Awaiting confirmation to execute Phase 2
