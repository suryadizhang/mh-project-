# 🧪 Customer Review Privacy & Initials Testing - October 26, 2025

## 🎯 Testing Objectives
1. ✅ Verify database migration successful (customer contact fields + show_initials_only)
2. ⏳ Test backend API endpoints (initials vs full name display)
3. ⏳ Test frontend form (checkbox works, preview accurate)
4. ⏳ Test admin panel (always shows full name)
5. ⏳ Submit real review with both options

---

## ✅ Database Migration (PASSED)

### Migration 008: Customer Contact Fields
```bash
✓ Adding customer_name column...
✓ Adding customer_email column...
✓ Adding customer_phone column...
✓ Adding show_initials_only column...
✅ Migration completed successfully!

Verification:
   ✓ customer_name: Added successfully
   ✓ customer_email: Added successfully
   ✓ customer_phone: Added successfully
   ✓ show_initials_only: Added successfully
```

**Result:** ✅ PASSED - All 4 columns added successfully

---

## 🔧 Backend API Testing

### Test 1: Model Helper Methods
**Testing:** `get_initials()` and `get_display_name()` methods

**Expected Behavior:**
- `get_initials()`:
  - "John Doe" → "JD"
  - "Sarah" → "S"
  - "Mary Jane Watson" → "MJ" (first + last)
  
- `get_display_name()`:
  - If `show_initials_only=True` → returns initials
  - If `show_initials_only=False` → returns full name

**Test Commands:**
```python
# Will test via API submissions
```

**Status:** ⏳ PENDING

---

### Test 2: Submit Review Endpoint - Full Name
**Endpoint:** `POST /api/customer-reviews/submit-review`

**Test Payload:**
```bash
curl -X POST http://localhost:8000/api/customer-reviews/submit-review \
  -F "customer_id=1" \
  -F "customer_name=John Doe" \
  -F "customer_email=john@test.com" \
  -F "customer_phone=555-1234" \
  -F "show_initials_only=false" \
  -F "title=Great Experience" \
  -F "content=Lorem ipsum dolor sit amet consectetur adipisicing elit. Wonderful service!" \
  -F "rating=5"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Review submitted successfully!",
  "review_id": 1,
  "status": "pending",
  "media_uploaded": 0
}
```

**Expected Database State:**
- `customer_name`: "John Doe"
- `customer_email`: "john@test.com"
- `customer_phone`: "555-1234"
- `show_initials_only`: false
- `status`: "pending"

**Status:** ⏳ PENDING

---

### Test 3: Submit Review Endpoint - Initials Only
**Endpoint:** `POST /api/customer-reviews/submit-review`

**Test Payload:**
```bash
curl -X POST http://localhost:8000/api/customer-reviews/submit-review \
  -F "customer_id=1" \
  -F "customer_name=Sarah Johnson" \
  -F "customer_email=sarah@test.com" \
  -F "customer_phone=555-5678" \
  -F "show_initials_only=true" \
  -F "title=Amazing Food" \
  -F "content=The hibachi experience was absolutely fantastic! Chef was amazing and food was perfect!" \
  -F "rating=5"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Review submitted successfully!",
  "review_id": 2,
  "status": "pending",
  "media_uploaded": 0
}
```

**Expected Database State:**
- `customer_name`: "Sarah Johnson"
- `customer_email`: "sarah@test.com"
- `customer_phone`: "555-5678"
- `show_initials_only`: true
- `status`: "pending"

**Status:** ⏳ PENDING

---

### Test 4: Approve Reviews (Admin)
**Endpoint:** `POST /api/admin/review-moderation/approve-review/1`

**Test Commands:**
```bash
# Approve review #1 (Full name)
curl -X POST http://localhost:8000/api/admin/review-moderation/approve-review/1 \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1}'

# Approve review #2 (Initials only)
curl -X POST http://localhost:8000/api/admin/review-moderation/approve-review/2 \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Review approved successfully",
  "review_id": 1,
  "status": "approved"
}
```

**Status:** ⏳ PENDING

---

### Test 5: Get Approved Reviews (Public API)
**Endpoint:** `GET /api/customer-reviews/approved-reviews`

**Test Command:**
```bash
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq
```

**Expected Response:**
```json
{
  "success": true,
  "reviews": [
    {
      "id": 1,
      "title": "Great Experience",
      "content": "Lorem ipsum...",
      "rating": 5,
      "customer_name": "John Doe",  // Full name (show_initials_only=false)
      "likes_count": 0
    },
    {
      "id": 2,
      "title": "Amazing Food",
      "content": "The hibachi...",
      "rating": 5,
      "customer_name": "SJ",  // INITIALS (show_initials_only=true)
      "likes_count": 0
    }
  ]
}
```

**Expected Behavior:**
- Review #1: Shows "John Doe" (full name)
- Review #2: Shows "SJ" (initials)
- ❌ email NOT present
- ❌ phone NOT present

**Status:** ⏳ PENDING

---

### Test 6: Admin Pending Reviews API
**Endpoint:** `GET /api/admin/review-moderation/pending-reviews`

**Expected Response:**
```json
{
  "success": true,
  "reviews": [
    {
      "id": 1,
      "customer_name": "John Doe",  // ALWAYS full name in admin
      "customer_email": "john@test.com",  // SHOWN in admin
      "customer_phone": "555-1234",  // SHOWN in admin
      "show_initials_only": false
    }
  ]
}
```

**Expected Behavior:**
- Admin sees FULL customer details regardless of `show_initials_only`
- Email and phone visible for admin
- Full name always shown

**Status:** ⏳ PENDING

---

## 🎨 Frontend Form Testing

### Test 7: Checkbox Functionality
**Component:** `CustomerReviewForm.tsx`

**Test Steps:**
1. Navigate to form
2. Fill Step 1 (Rating): 5 stars
3. Fill Step 2 (Contact):
   - Name: "Michael Jordan"
   - Email: "mj@test.com"
   - Phone: "555-9999"
   - ✅ CHECK "Show only my initials publicly"
4. Verify live preview shows "MJ"
5. UNCHECK checkbox
6. Verify live preview shows "Michael Jordan"

**Expected Behavior:**
- Checkbox unchecked: "Instead of showing "Michael Jordan", your review will display "MJ""
- Preview section: Shows "MJ" when checked, "Michael Jordan" when unchecked
- Privacy message changes based on checkbox state

**Status:** ⏳ PENDING

---

### Test 8: Preview Accuracy
**Component:** `CustomerReviewForm.tsx` - Preview Modal

**Test Steps:**
1. Fill complete review
2. Check "Show only my initials"
3. Click "PREVIEW BUTTON"
4. Verify preview shows:
   - Initials only (e.g., "MJ")
   - Message: "✓ Showing initials only (full name kept private)"
   - Email/phone NOT shown

**Expected Preview:**
```
⭐⭐⭐⭐⭐
Amazing Experience!
Great food and service...

Customer Info:
MJ
✓ Showing initials only (full name kept private)
```

**Status:** ⏳ PENDING

---

### Test 9: Form Submission - Full Name
**Test Steps:**
1. Fill review form completely
2. Leave "Show only my initials" UNCHECKED
3. Click PREVIEW → SUBMIT
4. Verify success message

**Expected Network Payload:**
```
customer_name: "Michael Jordan"
customer_email: "mj@test.com"
customer_phone: "555-9999"
show_initials_only: "false"
```

**Status:** ⏳ PENDING

---

### Test 10: Form Submission - Initials Only
**Test Steps:**
1. Fill review form completely
2. CHECK "Show only my initials publicly"
3. Click PREVIEW → SUBMIT
4. Verify success message

**Expected Network Payload:**
```
customer_name: "Michael Jordan"
customer_email: "mj@test.com"
customer_phone: "555-9999"
show_initials_only: "true"
```

**Status:** ⏳ PENDING

---

## 🔐 Privacy Compliance Testing

### Test 11: Public API Privacy Check
**What:** Verify email/phone NEVER in public API responses

**Endpoints to Test:**
1. `GET /api/customer-reviews/approved-reviews`
2. `GET /api/customer-reviews/reviews/1`

**Expected:**
- ✅ `customer_name` present (or initials)
- ❌ `customer_email` NOT present
- ❌ `customer_phone` NOT present
- ✅ `show_initials_only` NOT exposed to public

**Test Command:**
```bash
# Check approved reviews
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq '.reviews[0]'

# Check if email/phone are present (should return null)
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq '.reviews[0].customer_email'
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq '.reviews[0].customer_phone'
```

**Status:** ⏳ PENDING

---

### Test 12: Admin API Full Access Check
**What:** Verify admin ALWAYS sees full contact info

**Endpoints to Test:**
1. `GET /api/admin/review-moderation/pending-reviews`

**Expected:**
- ✅ `customer_name` (full name)
- ✅ `customer_email` present
- ✅ `customer_phone` present
- ✅ `show_initials_only` field visible

**Test Command:**
```bash
curl http://localhost:8000/api/admin/review-moderation/pending-reviews | jq '.reviews[0]'
```

**Status:** ⏳ PENDING

---

## 📊 Integration Testing

### Test 13: End-to-End Flow - Initials Option
**Scenario:** User wants initials only, submits review, admin approves, public sees initials

**Steps:**
1. **User submits review:**
   - Name: "Alice Williams"
   - Checkbox: ✅ Checked (show initials)
   - Expected initials: "AW"

2. **Admin reviews:**
   - Sees: Full name "Alice Williams"
   - Sees: Email + phone
   - Action: Approves

3. **Public views:**
   - Sees: "AW" (NOT "Alice Williams")
   - Does NOT see: email, phone

**Test Commands:**
```bash
# 1. Submit
curl -X POST http://localhost:8000/api/customer-reviews/submit-review \
  -F "customer_id=1" \
  -F "customer_name=Alice Williams" \
  -F "customer_email=alice@test.com" \
  -F "show_initials_only=true" \
  -F "title=Excellent" \
  -F "content=Had a wonderful time at the hibachi restaurant!" \
  -F "rating=5"

# 2. Admin approves
curl -X POST http://localhost:8000/api/admin/review-moderation/approve-review/3 \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1}'

# 3. Public views
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq '.reviews[] | select(.id==3) | .customer_name'
# Expected output: "AW"
```

**Status:** ⏳ PENDING

---

### Test 14: End-to-End Flow - Full Name
**Scenario:** User wants full name shown, submits review, public sees full name

**Steps:**
1. **User submits review:**
   - Name: "Robert Brown"
   - Checkbox: ❌ Unchecked (show full name)

2. **Admin reviews:**
   - Sees: Full name "Robert Brown"
   - Action: Approves

3. **Public views:**
   - Sees: "Robert Brown" (full name)

**Test Commands:**
```bash
# 1. Submit
curl -X POST http://localhost:8000/api/customer-reviews/submit-review \
  -F "customer_id=1" \
  -F "customer_name=Robert Brown" \
  -F "customer_email=robert@test.com" \
  -F "show_initials_only=false" \
  -F "title=Great Service" \
  -F "content=The staff was amazing and the food was delicious!" \
  -F "rating=5"

# 2. Admin approves
curl -X POST http://localhost:8000/api/admin/review-moderation/approve-review/4 \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1}'

# 3. Public views
curl http://localhost:8000/api/customer-reviews/approved-reviews | jq '.reviews[] | select(.id==4) | .customer_name'
# Expected output: "Robert Brown"
```

**Status:** ⏳ PENDING

---

## 🎯 Summary

### Completed Tests: 0 / 14
- ✅ Database Migration: PASSED

### Pending Tests: 14
- ⏳ Backend API (6 tests)
- ⏳ Frontend Form (4 tests)
- ⏳ Privacy Compliance (2 tests)
- ⏳ Integration E2E (2 tests)

### Next Steps:
1. Run backend API tests (submit reviews, approve, verify display)
2. Test frontend form checkbox and preview
3. Verify privacy compliance
4. Run end-to-end integration tests
5. Document any issues found

---

**Testing Date:** October 26, 2025  
**Features Tested:** Privacy controls, Initials display option  
**Status:** 🟡 IN PROGRESS
