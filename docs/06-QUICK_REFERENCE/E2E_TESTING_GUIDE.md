# 🧪 E2E Testing Guide - Admin Dashboard Cursor Pagination

**Date**: October 25, 2025  
**Focus**: Test cursor pagination implementation in admin dashboard  
**Time**: 30-45 minutes

---

## 🎯 Test Objectives

Verify that cursor pagination is working correctly in the admin dashboard:
1. ✅ Backend returns cursor format correctly
2. ✅ Frontend receives and parses cursor data
3. ✅ Navigation works (next/prev pages)
4. ✅ No OFFSET queries in backend logs
5. ✅ TypeScript types match backend response

---

## 🚀 Setup Instructions

### Step 1: Start Backend (Terminal 1)

```powershell
# Navigate to backend
cd "C:\Users\surya\projects\MH webapps\apps\backend"

# Activate virtual environment
.venv\Scripts\activate

# Start backend with reload
uvicorn src.api.app.main:app --reload --log-level debug

# Expected output:
# INFO: Uvicorn running on http://127.0.0.1:8000
# INFO: Application startup complete
```

### Step 2: Start Admin App (Terminal 2)

```powershell
# Navigate to admin app
cd "C:\Users\surya\projects\MH webapps\apps\admin"

# Start dev server
pnpm dev

# Expected output:
# ▲ Next.js 15.5.4
# Local: http://localhost:3000
```

### Step 3: Open Browser Developer Tools

1. Open Chrome/Edge
2. Navigate to: http://localhost:3000/admin
3. Open DevTools (F12)
4. Go to **Network** tab
5. Filter by: `XHR` or `Fetch`

---

## ✅ Test Case 1: Verify Backend Response Format

### Steps:
1. Navigate to http://localhost:3000/admin/bookings
2. In DevTools Network tab, find request to `/api/bookings/`
3. Click on the request
4. Go to **Response** tab

### Expected Response Format:
```json
{
  "items": [
    {
      "id": 1,
      "customer_name": "John Doe",
      "booking_date": "2025-11-01",
      "status": "confirmed"
      // ... other booking fields
    }
    // ... more bookings
  ],
  "next_cursor": "eyJ2YWx1ZSI6IjIwMjQtMTAtMjVUMTA6MzA6MDAiLCJpZCI6MTUsImRpcmVjdGlvbiI6Im5leHQifQ==",
  "prev_cursor": null,
  "has_next": true,
  "has_prev": false,
  "count": 20
}
```

### ✅ Pass Criteria:
- [x] Response includes `next_cursor` field
- [x] Response includes `prev_cursor` field
- [x] Response includes `has_next` and `has_prev` booleans
- [x] Response includes `count` field
- [x] Response includes `items` array
- [x] Status code is 200

### ❌ Fail Indicators:
- Missing cursor fields (old page-based format)
- Status code 500 (backend error)
- TypeScript errors in browser console

---

## ✅ Test Case 2: Verify Request Parameters

### Steps:
1. Still on bookings page
2. In DevTools Network tab, find `/api/bookings/` request
3. Go to **Headers** or **Payload** tab
4. Check **Query String Parameters**

### Expected Parameters (First Page):
```
No cursor parameter (first page)
Or:
limit=20
order=desc
```

### After Clicking "Next Page":
```
cursor=eyJ2YWx1ZSI6IjIwMjQtMTAtMjVUMTA6MzA6MDAiLCJpZCI6MTUsImRpcmVjdGlvbiI6Im5leHQifQ==
limit=20
order=desc
```

### ✅ Pass Criteria:
- [x] First page has no cursor parameter
- [x] Next page has cursor parameter (base64 string)
- [x] No `page` or `offset` parameters (legacy)

### ❌ Fail Indicators:
- Using `page=1`, `page=2` (old pagination)
- Using `offset=0`, `offset=20` (slow pagination)

---

## ✅ Test Case 3: Navigation Testing

### Steps:
1. On bookings page (page 1)
2. Click **"Next"** button (if available)
3. Verify you see page 2 of results
4. Click **"Previous"** button
5. Verify you're back on page 1

### Expected Behavior:
- **Page 1**: 
  - ✅ "Next" button enabled (if has_next=true)
  - ✅ "Previous" button disabled or hidden (has_prev=false)
  - ✅ Shows first 20 bookings

- **Page 2**:
  - ✅ "Next" button enabled/disabled based on has_next
  - ✅ "Previous" button enabled
  - ✅ Shows next 20 bookings
  - ✅ URL updated with cursor (or state maintained)

- **Back to Page 1**:
  - ✅ Shows original first 20 bookings
  - ✅ "Previous" button disabled again

### ✅ Pass Criteria:
- [x] Navigation works smoothly
- [x] No page reloads (SPA behavior)
- [x] Data updates correctly
- [x] Buttons enable/disable correctly

### ❌ Fail Indicators:
- Page reloads on navigation
- Same data on different pages
- Buttons don't update state
- Errors in console

---

## ✅ Test Case 4: Backend Performance Check

### Steps:
1. In Terminal 1 (backend), watch the logs
2. Navigate through 3-4 pages in admin dashboard
3. Look for SQL query logs

### Expected Backend Logs:
```
INFO: GET /api/bookings/ - cursor=None
DEBUG: SELECT bookings.* FROM bookings 
       WHERE created_at > '2024-10-25T10:30:00' 
       ORDER BY created_at DESC, id DESC 
       LIMIT 21

INFO: Response time: 45ms
INFO: Query time: 12ms
```

### ✅ Pass Criteria:
- [x] No OFFSET in SQL queries
- [x] Uses `WHERE created_at > X` (cursor-based)
- [x] Queries are fast (<50ms)
- [x] No N+1 query warnings
- [x] Uses composite ORDER BY (created_at, id)

### ❌ Fail Indicators:
- SQL contains `OFFSET 20`, `OFFSET 40` (bad!)
- Queries slow down on later pages
- Multiple queries for same data (N+1 problem)

---

## ✅ Test Case 5: TypeScript Type Safety

### Steps:
1. Open admin app code in VS Code
2. Navigate to: `apps/admin/src/services/api.ts`
3. Find the `getBookings` method
4. Check for TypeScript errors

### Expected Code:
```typescript
// apps/admin/src/services/api.ts
async getBookings(filters?: BookingFilters): Promise<CursorPaginatedResponse<Booking>> {
  const params = new URLSearchParams();
  
  if (filters?.cursor) {
    params.append('cursor', filters.cursor);
  }
  
  // ... rest of implementation
}
```

### ✅ Pass Criteria:
- [x] No TypeScript errors in VS Code
- [x] CursorPaginatedResponse type exists
- [x] BookingFilters includes cursor field
- [x] Method signature matches backend response

### ❌ Fail Indicators:
- Red squiggly lines in VS Code
- Type 'any' used instead of proper types
- Missing cursor field in interface

---

## ✅ Test Case 6: Error Handling

### Steps:
1. In browser DevTools, go to **Console** tab
2. Navigate to bookings page
3. Click "Next" several times
4. Try to go past the last page

### Expected Behavior:
- **Last page reached**:
  - ✅ "Next" button disabled (has_next=false)
  - ✅ No error messages
  - ✅ Graceful end of pagination

- **Invalid cursor** (manually modify URL if possible):
  - ✅ Shows error message or redirects to page 1
  - ✅ No app crash
  - ✅ Backend returns 400 Bad Request

### ✅ Pass Criteria:
- [x] No JavaScript errors in console
- [x] Graceful handling of edge cases
- [x] User-friendly error messages

### ❌ Fail Indicators:
- Console errors/warnings
- White screen (app crash)
- Infinite loading state

---

## 📊 Test Results Summary

### Test Case Results
| Test Case | Status | Time | Notes |
|-----------|--------|------|-------|
| 1. Backend Response Format | ⏳ Pending | - | Check cursor fields |
| 2. Request Parameters | ⏳ Pending | - | Verify cursor usage |
| 3. Navigation Testing | ⏳ Pending | - | Test next/prev |
| 4. Backend Performance | ⏳ Pending | - | Check SQL queries |
| 5. TypeScript Types | ⏳ Pending | - | Verify no errors |
| 6. Error Handling | ⏳ Pending | - | Test edge cases |

### Overall Status
- **Passed**: 0/6
- **Failed**: 0/6
- **Pending**: 6/6
- **Score**: 0% (not tested yet)

---

## 🐛 Common Issues & Solutions

### Issue 1: Backend not returning cursor format
**Symptom**: Response has `page` and `total_pages` instead of cursors  
**Solution**: Verify using bookings router (not legacy API)
```python
# Check: apps/backend/src/api/app/routers/bookings.py
# Should use: paginate_query() with cursor support
```

### Issue 2: Frontend not sending cursor
**Symptom**: Request has `page=2` instead of cursor  
**Solution**: Update frontend to use cursor parameter
```typescript
// Check: apps/admin/src/services/api.ts
// Should append: params.append('cursor', filters.cursor)
```

### Issue 3: TypeScript errors
**Symptom**: Red squiggly lines on CursorPaginatedResponse  
**Solution**: Import from correct package
```typescript
import type { CursorPaginatedResponse } from '@mh/types';
// Or
import type { CursorPaginatedResponse } from '../../types';
```

### Issue 4: Slow pagination
**Symptom**: Each page takes longer to load  
**Solution**: Verify cursor-based queries (no OFFSET)
```sql
-- Good: Cursor-based
WHERE created_at < '2024-10-25T10:30:00'

-- Bad: Offset-based
OFFSET 100 LIMIT 20
```

---

## 🎯 Success Criteria

### Minimum for ✅ PASS:
- [x] All 6 test cases pass
- [x] No TypeScript errors
- [x] No console errors
- [x] Response times <100ms
- [x] Backend uses cursor queries (no OFFSET)

### Ideal for 🏆 EXCELLENT:
- [x] All tests pass
- [x] Response times <50ms
- [x] Smooth UX with loading states
- [x] Proper error handling
- [x] Accessible keyboard navigation

---

## 📝 Testing Checklist

Before starting:
- [ ] Backend running on http://localhost:8000
- [ ] Admin app running on http://localhost:3000
- [ ] Browser DevTools open
- [ ] Network tab visible
- [ ] Console tab visible

During testing:
- [ ] Record response format
- [ ] Check cursor parameters
- [ ] Test navigation flow
- [ ] Monitor backend logs
- [ ] Verify TypeScript types
- [ ] Test error scenarios

After testing:
- [ ] Document issues found
- [ ] Update test results table
- [ ] Calculate pass rate
- [ ] Create fix tickets if needed
- [ ] Update production checklist

---

## 📄 Test Report Template

```markdown
# E2E Test Report: Admin Dashboard Cursor Pagination
**Date**: October 25, 2025
**Tester**: [Your Name]
**Duration**: [Time taken]

## Summary
- Tests Passed: X/6
- Tests Failed: X/6
- Overall Status: [PASS/FAIL]

## Issues Found
1. [Issue description]
   - Severity: [Critical/High/Medium/Low]
   - Steps to reproduce: [Steps]
   - Expected: [Expected behavior]
   - Actual: [Actual behavior]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Conclusion
[Overall assessment and next steps]
```

---

## 🚀 Next Steps After E2E Testing

### If All Tests Pass ✅:
1. Mark "E2E cursor pagination testing" as complete
2. Update production checklist
3. Proceed with performance benchmarks
4. Document results

### If Tests Fail ❌:
1. Document failures
2. Create fix tickets
3. Prioritize fixes
4. Re-test after fixes
5. Update documentation

---

**Ready to test?** Start with Test Case 1 and work through systematically! 🧪
