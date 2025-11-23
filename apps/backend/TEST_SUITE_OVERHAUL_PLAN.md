# Test Suite Overhaul Plan - November 20, 2025

## 📊 Current Test Inventory

**Total Test Files**: 61 files **Total Lines**: ~600K+ lines of test
code

---

## 🎯 Phase 1: Delete Corrupted/Outdated Tests

### Files to DELETE (already corrupted or deleted services):

1. ❌ **tests/test_monitoring_comprehensive.py** - Imports deleted
   `ai_monitoring_service`
2. ❌ **tests/test_terms_reply_variations.py** - Imports deleted
   `terms_acknowledgment_service`
3. ❌ **tests/test_voice_ai_comprehensive.py** - Uses non-existent
   `CallState` enum
4. ❌ **tests/test_performance_comprehensive.py** - Missing `load`
   marker (fixed in pytest.ini)
5. ❌ **tests/services/test_booking_service.py.old** - Backup file
   (outdated)

### Files to REVIEW (may be outdated):

- **tests/services/test_booking_service_comprehensive.py** - Check if
  matches current schema
- **tests/services/test_booking_service_isolated.py** - Check if
  matches current schema

---

## 🔧 Phase 2: Fix Remaining Tests

### High Priority (Core Functionality):

1. ✅ **test_additional_scenarios.py** - PASSING (6/6)
2. ✅ **test_all_integrations.py** - PASSING (8/8)
3. ✅ **test_api_quick.py** - PASSING (1/1)
4. ⚠️ **test*booking_service*\*.py** - NEEDS FIXING (schema mismatch)

### Medium Priority (Services):

- **test_race_condition_fix.py** - Test concurrency fixes
- **test_referral_service.py** - Referral system
- **test_newsletter_unit.py** - Newsletter service
- **test_nurture_campaign_service.py** - Campaign automation
- **test_sms_tracking_comprehensive.py** - SMS tracking

### Low Priority (Integrations):

- **test*ringcentral*\*.py** - RingCentral auth tests
- **test_stripe_quick.py** - Stripe integration
- **test*payment*\*.py** - Payment processing
- **test_cloudinary.py** - Image uploads

---

## 🚀 Phase 3: Create Comprehensive Test Suites

### New Test Files to CREATE:

1. **test_booking_endpoints_comprehensive.py**
   - All booking API endpoints
   - CRUD operations
   - Validation tests
   - Error handling

2. **test_customer_endpoints_comprehensive.py**
   - Customer registration
   - Profile management
   - Authentication

3. **test_admin_endpoints_comprehensive.py**
   - Admin operations
   - Dashboard stats
   - Report generation

4. **test_ai_endpoints_comprehensive.py**
   - AI booking assistant
   - SMS conversation handling
   - Intent classification

5. **test_payment_endpoints_comprehensive.py**
   - Stripe integration
   - Zelle detection
   - Payment confirmation

6. **test_communication_endpoints_comprehensive.py**
   - SMS sending (RingCentral)
   - Email sending (Gmail)
   - WhatsApp notifications (Twilio)

---

## 📋 Execution Plan

### Step 1: Cleanup (10 min)

- Delete 5 corrupted test files
- Delete backup files (.old)
- Clear all pytest cache

### Step 2: Fix Core Tests (30 min)

- Fix booking service tests (schema updates)
- Verify integration tests pass
- Fix any import errors

### Step 3: Run Full Test Suite (15 min)

- Run all tests
- Document passing/failing tests
- Create issue list

### Step 4: Create New Comprehensive Tests (90 min)

- Create 6 new endpoint test files
- Cover all major features
- Achieve 85%+ coverage

---

## ✅ Success Criteria

- [ ] All corrupted tests deleted
- [ ] All existing tests passing (or documented as TODO)
- [ ] 6 new comprehensive test suites created
- [ ] Test coverage > 85%
- [ ] All critical endpoints tested
- [ ] CI/CD ready

---

## 📊 Expected Final State

**Estimated Test Count**: 200+ tests **Estimated Coverage**: 85-90%
**Est. Execution Time**: < 2 minutes (full suite)

**Test Structure**:

```
tests/
├── conftest.py (fixtures)
├── endpoints/
│   ├── test_booking_endpoints_comprehensive.py (40 tests)
│   ├── test_customer_endpoints_comprehensive.py (30 tests)
│   ├── test_admin_endpoints_comprehensive.py (25 tests)
│   ├── test_ai_endpoints_comprehensive.py (35 tests)
│   ├── test_payment_endpoints_comprehensive.py (20 tests)
│   └── test_communication_endpoints_comprehensive.py (15 tests)
├── services/ (existing, fixed)
├── integration/ (existing, fixed)
└── unit/ (existing, fixed)
```

---

**Status**: READY TO EXECUTE **Estimated Time**: 2-3 hours total
**Priority**: HIGH (blocking production deployment)
