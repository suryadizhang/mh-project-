# Test Suite Action Plan - Phase 2 Preparation

**Date**: November 20, 2025  
**Context**: Based on comprehensive audit of test vs implementation  
**Status**: Ready for Phase 2 (Fix Existing Tests)

---

## 📊 AUDIT FINDINGS SUMMARY

### Implementation Status:

| Category | Implemented | Aspirational | Pass Rate Expected |
|----------|-------------|--------------|-------------------|
| **Bookings** | 88% (35/40 tests) | 12% (5/40 tests) | 🟢 85%+ |
| **Customers** | 80% (24/30 tests) | 20% (6/30 tests) | 🟢 75%+ |
| **AI** | 43% (15/35 tests) | 57% (20/35 tests) | 🟡 40%+ |
| **Admin** | 12% (3/25 tests) | 88% (22/25 tests) | 🔴 10%+ |
| **Payments** | 30% (6/20 tests) | 70% (14/20 tests) | 🟡 25%+ |
| **Communications** | 40% (6/15 tests) | 60% (9/15 tests) | 🟡 35%+ |

---

## 🎯 IMMEDIATE ACTIONS (Before Phase 2)

### Action 1: Mark Aspirational Tests with Skip Decorators ⚠️

**Purpose**: Prevent false test failures for unimplemented features

**Files to Update**:
1. `test_customer_endpoints_comprehensive.py`:
   - `test_get_customer_communications()` - endpoint doesn't exist
   - `test_merge_customers()` - endpoint doesn't exist

2. `test_ai_endpoints_comprehensive.py`:
   - All voice tests (3 tests) - voice endpoints not implemented
   - All embeddings tests (2 tests) - embeddings endpoints not implemented

3. `test_admin_endpoints_comprehensive.py`:
   - All dashboard tests (2 tests)
   - All admin booking tests (3 tests)
   - All admin customer tests (3 tests)
   - All settings tests (2 tests)
   - All reports tests (3 tests)
   - All AI management tests (4 tests)
   - All bulk operation tests (2 tests)
   - **KEEP**: Auth tests (2 tests) - these exist

4. `test_payment_endpoints_comprehensive.py`:
   - All deposit CRUD tests (2 tests)
   - All Stripe payment intent tests (2 tests)
   - All Plaid tests (3 tests)
   - All refund tests (2 tests)
   - All payment history tests (3 tests)
   - **KEEP**: Payment calculator tests (3 tests) - these exist
   - **KEEP**: Stripe webhook test (1 test) - webhook exists

5. `test_communication_endpoints_comprehensive.py`:
   - SMS send test - no REST endpoint
   - Email send test - no REST endpoint
   - WhatsApp send test - no REST endpoint
   - **KEEP**: Newsletter tests (3 tests) - endpoints exist
   - **KEEP**: Campaign tests (2 tests) - endpoints exist
   - **KEEP**: Webhook tests (3 tests) - webhooks exist

**Decorator to Use**:
```python
@pytest.mark.skip(reason="Endpoint not implemented - aspirational test")
```

---

### Action 2: Fix Schema Mismatches 🔧

**Critical Mismatches Identified**:

#### Booking Schema (HIGH PRIORITY):
**Problem**: Tests may use different field names than actual schema

**Fix Required**:
1. Read `src/schemas/booking.py` to verify exact field names
2. Update test data in `test_booking_endpoints_comprehensive.py` to match
3. Common issues:
   - `event_date` vs `date` vs `booking_date`
   - `event_time` vs `time` vs `start_time`
   - `guest_count` vs `guests` vs `party_size`

#### Customer Schema (MEDIUM PRIORITY):
**Problem**: Encrypted fields not handled in tests

**Fix Required**:
1. Update tests to expect encrypted field names:
   - `name_encrypted` instead of `name`
   - `email_encrypted` instead of `email`
   - `phone_encrypted` instead of `phone`
2. Or verify if API auto-decrypts for responses

#### AI Chat Schema (LOW PRIORITY):
**Problem**: Need to verify exact endpoint path

**Fix Required**:
1. Check if chat endpoint is `/v1/ai/chat` or different path
2. Update test URLs if needed

---

### Action 3: Update Newsletter/Campaign Tests ✅

**Good News**: These endpoints EXIST and are well-implemented!

**Routes Found**:

**Newsletters** (`/v1/marketing/newsletters`):
- `GET /newsletters/generate` - Generate AI newsletters ✅
- `POST /newsletters/generate-content` - Generate specific content ✅
- `POST /newsletters/send` - Send newsletter ✅
- `GET /newsletters/preview/{holiday_key}` - Preview ✅

**Campaigns** (`/v1/marketing/campaigns`):
- `GET /campaigns/annual` - Generate annual campaigns ✅
- `POST /campaigns/generate-content` - Generate multi-channel content ✅
- `POST /campaigns/launch` - Launch campaign ✅
- `GET /campaigns/budget-recommendations` - Budget AI ✅

**Test Updates Needed**:
1. Change base URL from `/v1/communications` to `/v1/marketing`
2. Update test assertions to match actual response schemas
3. These tests should PASS after URL fix

---

### Action 4: Update Payment Tests 🔧

**Good News**: Payment endpoints exist, but different from tests!

**Routes Found**:

**Payment Calculator** (`/v1/payments/calculator`):
- `POST /calculate` - Calculate payment breakdown ✅
- `POST /compare` - Compare all payment methods ✅
- `GET /methods` - Get available payment methods ✅

**Payment Notifications Admin** (`/v1/admin/payment-notifications`):
- `GET /stats` - Payment notification stats ✅
- `GET /list` - List payment notifications ✅
- `GET /{notification_id}` - Get notification detail ✅
- `POST /check-emails` - Check for new payment emails ✅
- `POST /test-booking` - Test payment matching ✅
- `POST /manual-match` - Manually match payment ✅
- `DELETE /{notification_id}` - Delete notification ✅

**Stripe Webhook** (`/v1/webhooks/stripe`):
- Webhook handler exists ✅

**Test Updates Needed**:
1. Update payment tests to use `/v1/payments/calculator` routes
2. Create new tests for `/v1/admin/payment-notifications` routes
3. Tests should target actual implemented endpoints

---

## 📋 PHASE 2 EXECUTION PLAN

### Step 1: Apply Skip Decorators (15 min)

**Command**:
```python
# Edit test files and add @pytest.mark.skip decorators
# to all aspirational tests identified above
```

**Expected Outcome**:
- ~50 tests marked as skipped
- Remaining ~115 tests target implemented features
- No false failures from missing endpoints

---

### Step 2: Fix Schema Mismatches (20 min)

**Commands**:
```bash
# Read schemas to verify field names
cat apps/backend/src/schemas/booking.py
cat apps/backend/src/schemas/customer.py

# Update test data dictionaries in test files
```

**Expected Outcome**:
- Test data matches actual API schemas
- No validation errors from wrong field names
- Tests can deserialize responses correctly

---

### Step 3: Update Marketing Endpoint Paths (10 min)

**Changes**:
```python
# In test_communication_endpoints_comprehensive.py

# OLD:
client.post("/v1/communications/newsletters/subscribe")

# NEW:
client.post("/v1/marketing/newsletters/generate")
```

**Expected Outcome**:
- Newsletter tests find correct endpoints
- Campaign tests find correct endpoints
- Marketing tests should PASS

---

### Step 4: Update Payment Endpoint Paths (10 min)

**Changes**:
```python
# In test_payment_endpoints_comprehensive.py

# OLD:
client.post("/v1/payments/deposits")

# NEW:
client.post("/v1/payments/calculator/calculate")
```

**Expected Outcome**:
- Payment calculator tests find correct endpoints
- Payment admin tests target admin routes
- Payment tests should PASS

---

### Step 5: Run Test Suite (5 min)

**Commands**:
```bash
cd apps/backend
pytest tests/endpoints/ -v --tb=short

# Or run specific test files:
pytest tests/endpoints/test_booking_endpoints_comprehensive.py -v
pytest tests/endpoints/test_customer_endpoints_comprehensive.py -v
pytest tests/endpoints/test_communication_endpoints_comprehensive.py -v
pytest tests/endpoints/test_payment_endpoints_comprehensive.py -v
```

**Expected Results**:
- Bookings: 🟢 30-35 passed, 5-10 skipped
- Customers: 🟢 20-24 passed, 6-10 skipped
- AI: 🟡 10-15 passed, 20-25 skipped
- Admin: 🟡 2-3 passed, 22-23 skipped
- Payments: 🟡 5-8 passed, 12-15 skipped
- Communications: 🟡 5-8 passed, 7-10 skipped

**Overall Target**: 🎯 **70-85 tests passing** out of 165 total

---

### Step 6: Fix Existing Test Failures (70 min - Original Phase 2)

**After new endpoint tests are stable**, fix pre-existing failures:

1. **Payment Email Monitor Tests** (30 min):
   - Fix `test_payment_email_monitor.py`
   - Issues: Schema mismatches, async problems

2. **Newsletter Service Tests** (20 min):
   - Fix `test_newsletter_service.py`
   - Issues: Missing fixtures, API changes

3. **Cache Service Tests** (20 min):
   - Fix `test_cache_service.py`
   - Issues: Redis connection, fixture setup

---

## 🎯 SUCCESS CRITERIA

### Phase 2 Complete When:

✅ **All aspirational tests marked with skip decorators**  
✅ **Schema mismatches fixed** (booking, customer)  
✅ **Marketing endpoint paths updated**  
✅ **Payment endpoint paths updated**  
✅ **Test suite runs without errors**  
✅ **70-85 tests passing** (out of 115 non-skipped)  
✅ **50 tests skipped** (aspirational features documented)  
✅ **Pre-existing test failures fixed**  
✅ **No new regressions introduced**

---

## 📈 EXPECTED METRICS

### Before Actions:
- Total tests: 165
- Expected failures: ~100+ (many aspirational)
- Expected errors: Many (wrong endpoints)
- Pass rate: Unknown (likely <30%)

### After Actions:
- Total tests: 165
- Skipped: ~50 (aspirational, documented)
- Runnable: ~115 (target implemented features)
- Passing: 70-85 (60-75% of runnable)
- Failing: 30-45 (25-40% - legitimate bugs to fix)
- Pass rate: 🎯 **60-75%** of runnable tests

---

## 🚀 NEXT STEPS AFTER PHASE 2

### Immediate (Week 1):
1. Document all test failures (legitimate bugs)
2. Prioritize bug fixes (Critical → High → Medium)
3. Create bug fix tickets for each failure

### Short-term (Weeks 2-4):
1. Fix Critical and High priority bugs
2. Implement missing business logic (deposit calc, travel fees)
3. Add missing test coverage (AI history, orchestrator health)

### Long-term (Months 1-3):
1. Implement aspirational endpoints (admin dashboard, payment REST API)
2. Un-skip tests as features are implemented
3. Target 90%+ test pass rate

---

## 📝 DOCUMENTATION UPDATES

### Files to Update:
1. `OPTION_C_PHASE1_COMPLETE.md` - Mark as superseded
2. `PHASE1_COMPLETION_SUMMARY.md` - Add link to this action plan
3. `TEST_SUITE_VS_IMPLEMENTATION_AUDIT.md` - Reference document
4. Create `PHASE2_COMPLETION_SUMMARY.md` when done

---

**Status**: ✅ READY TO EXECUTE  
**Next Action**: Apply skip decorators to aspirational tests  
**Time Estimate**: 1-1.5 hours for all actions  
**Expected Outcome**: Clean test suite with 60-75% pass rate
