# Knowledge Sync Dashboard - Testing Guide

**Created**: November 12, 2025  
**Status**: Week 2, Day 3 - Testing Phase  
**Component**: Admin UI - Superadmin Knowledge Sync Dashboard

---

## 📋 Table of Contents

1. [Testing Prerequisites](#testing-prerequisites)
2. [Backend API Testing](#backend-api-testing)
3. [Frontend Integration Testing](#frontend-integration-testing)
4. [Role-Based Access Testing](#role-based-access-testing)
5. [Real-Time Features Testing](#real-time-features-testing)
6. [Error Handling Testing](#error-handling-testing)
7. [Performance Testing](#performance-testing)
8. [Bug Report Template](#bug-report-template)
9. [QA Checklist](#qa-checklist)

---

## Testing Prerequisites

### Environment Setup

**Backend Requirements:**
```bash
# Navigate to backend directory
cd apps/backend

# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source .venv/bin/activate    # Linux/Mac

# Ensure all dependencies are installed
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Requirements:**
```bash
# Navigate to admin frontend directory
cd apps/admin

# Install dependencies
npm install

# Start development server
npm run dev
```

**Required Test Users:**
- **Super Admin**: Email with `is_super_admin=true` flag in database
- **Regular Admin**: Email with `role=admin` but `is_super_admin=false`
- **Station Manager**: Email with `role=station_manager`

### Test Data Setup

**Seed Knowledge Base Data:**
```sql
-- FAQs
INSERT INTO faqs (question, answer, category, display_order, is_active)
VALUES 
  ('What areas do you serve?', 'We serve Bay Area, Sacramento, and San Jose.', 'service', 1, true),
  ('What is your pricing?', 'Our pricing starts at $50 per person.', 'pricing', 1, true);

-- Services
INSERT INTO services (name, description, base_price, duration_minutes, is_active)
VALUES
  ('Standard Hibachi', 'Classic hibachi experience with chef', 50.00, 90, true),
  ('Premium Hibachi', 'Enhanced hibachi with premium ingredients', 80.00, 120, true);

-- Policies
INSERT INTO policies (name, content, category, version, is_active)
VALUES
  ('Cancellation Policy', 'Cancellations must be made 48 hours in advance.', 'booking', 1, true),
  ('Refund Policy', 'Full refunds available within 24 hours of booking.', 'payment', 1, true);
```

---

## Backend API Testing

### 1. GET /api/knowledge/sync/status

**Purpose**: Retrieve synchronization status for all sources

**Test Cases:**

#### TC-API-001: Successful Status Retrieval
```bash
# Request
curl -X GET http://localhost:8000/api/knowledge/sync/status \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json"

# Expected Response (200 OK)
{
  "success": true,
  "sources": {
    "faqs": {
      "last_sync": "2025-11-12T10:30:00Z",
      "status": "synced",
      "item_count": 45,
      "changes_pending": false
    },
    "services": {
      "last_sync": "2025-11-12T10:30:00Z",
      "status": "synced",
      "item_count": 12,
      "changes_pending": false
    },
    "policies": {
      "last_sync": "2025-11-12T10:30:00Z",
      "status": "synced",
      "item_count": 8,
      "changes_pending": false
    }
  },
  "overall_status": "healthy",
  "last_sync_time": "2025-11-12T10:30:00Z"
}
```

**Validation:**
- ✅ Status code is 200
- ✅ Response contains all 3 sources (faqs, services, policies)
- ✅ Each source has valid timestamps
- ✅ Item counts match database records
- ✅ `overall_status` is one of: healthy, warning, error

#### TC-API-002: Unauthorized Access
```bash
# Request without token
curl -X GET http://localhost:8000/api/knowledge/sync/status

# Expected Response (401 Unauthorized)
{
  "detail": "Not authenticated"
}
```

**Validation:**
- ✅ Status code is 401
- ✅ Error message indicates authentication required

#### TC-API-003: Non-Superadmin Access
```bash
# Request with regular admin token
curl -X GET http://localhost:8000/api/knowledge/sync/status \
  -H "Authorization: Bearer {admin_token}"

# Expected Response (403 Forbidden)
{
  "detail": "Insufficient permissions. Super admin access required."
}
```

**Validation:**
- ✅ Status code is 403
- ✅ Error message indicates insufficient permissions

---

### 2. POST /api/knowledge/sync/auto

**Purpose**: Trigger automatic synchronization with change detection

**Test Cases:**

#### TC-API-004: Auto Sync All Sources
```bash
# Request
curl -X POST http://localhost:8000/api/knowledge/sync/auto \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected Response (200 OK)
{
  "success": true,
  "message": "Auto sync completed successfully",
  "synced_items": 65,
  "sources_synced": ["faqs", "services", "policies"],
  "timestamp": "2025-11-12T10:35:00Z"
}
```

**Validation:**
- ✅ Status code is 200
- ✅ `success` is true
- ✅ `synced_items` count is accurate
- ✅ All 3 sources are listed
- ✅ Database records are updated with new sync timestamps

#### TC-API-005: Auto Sync Single Source
```bash
# Request
curl -X POST http://localhost:8000/api/knowledge/sync/auto \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["faqs"]}'

# Expected Response (200 OK)
{
  "success": true,
  "message": "Auto sync completed successfully",
  "synced_items": 45,
  "sources_synced": ["faqs"],
  "timestamp": "2025-11-12T10:36:00Z"
}
```

**Validation:**
- ✅ Only specified source is synced
- ✅ Other sources remain unchanged
- ✅ Sync history records only FAQs sync

#### TC-API-006: Auto Sync with No Changes
```bash
# Request (when DB and TS files are already in sync)
curl -X POST http://localhost:8000/api/knowledge/sync/auto \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected Response (200 OK)
{
  "success": true,
  "message": "No changes detected. Database is already in sync.",
  "synced_items": 0,
  "sources_synced": [],
  "timestamp": "2025-11-12T10:37:00Z"
}
```

**Validation:**
- ✅ `synced_items` is 0
- ✅ `sources_synced` is empty array
- ✅ Message indicates no changes

---

### 3. POST /api/knowledge/sync/force

**Purpose**: Force synchronization, overriding manual database changes

**Test Cases:**

#### TC-API-007: Force Sync All Sources
```bash
# Request
curl -X POST http://localhost:8000/api/knowledge/sync/force \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected Response (200 OK)
{
  "success": true,
  "message": "Force sync completed successfully",
  "synced_items": 65,
  "sources_synced": ["faqs", "services", "policies"],
  "overridden_items": 3,
  "timestamp": "2025-11-12T10:40:00Z"
}
```

**Validation:**
- ✅ Status code is 200
- ✅ All sources are synced
- ✅ `overridden_items` count shows manual changes reverted
- ✅ Database records match TypeScript files exactly

#### TC-API-008: Force Sync Single Source
```bash
# Request
curl -X POST http://localhost:8000/api/knowledge/sync/force \
  -H "Authorization: Bearer {super_admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["services"]}'

# Expected Response (200 OK)
{
  "success": true,
  "message": "Force sync completed successfully",
  "synced_items": 12,
  "sources_synced": ["services"],
  "overridden_items": 1,
  "timestamp": "2025-11-12T10:41:00Z"
}
```

**Validation:**
- ✅ Only services are synced
- ✅ FAQs and policies remain unchanged

---

### 4. GET /api/knowledge/sync/diff

**Purpose**: Get differences between TypeScript files and database

**Test Cases:**

#### TC-API-009: Diff with Changes
```bash
# Request (after manually modifying a DB record)
curl -X GET http://localhost:8000/api/knowledge/sync/diff \
  -H "Authorization: Bearer {super_admin_token}"

# Expected Response (200 OK)
{
  "success": true,
  "sources": {
    "faqs": {
      "added": [
        {
          "question": "New question from TS",
          "answer": "Answer from TypeScript file",
          "category": "general"
        }
      ],
      "modified": [
        {
          "id": "faq-001",
          "field": "answer",
          "old_value": "Old answer from DB",
          "new_value": "Updated answer from TS"
        }
      ],
      "removed": [
        {
          "id": "faq-002",
          "question": "Removed question",
          "reason": "Not in TypeScript file"
        }
      ]
    },
    "services": {
      "added": [],
      "modified": [],
      "removed": []
    },
    "policies": {
      "added": [],
      "modified": [],
      "removed": []
    }
  },
  "has_changes": true,
  "total_changes": 3
}
```

**Validation:**
- ✅ Status code is 200
- ✅ Changes are categorized by type (added, modified, removed)
- ✅ Modified items show old vs new values
- ✅ `has_changes` accurately reflects presence of differences
- ✅ `total_changes` count is correct

#### TC-API-010: Diff with No Changes
```bash
# Request (when DB and TS are in sync)
curl -X GET http://localhost:8000/api/knowledge/sync/diff \
  -H "Authorization: Bearer {super_admin_token}"

# Expected Response (200 OK)
{
  "success": true,
  "sources": {
    "faqs": {"added": [], "modified": [], "removed": []},
    "services": {"added": [], "modified": [], "removed": []},
    "policies": {"added": [], "modified": [], "removed": []}
  },
  "has_changes": false,
  "total_changes": 0
}
```

**Validation:**
- ✅ All sources have empty change arrays
- ✅ `has_changes` is false

---

### 5. GET /api/knowledge/sync/history

**Purpose**: Retrieve synchronization history with pagination and filters

**Test Cases:**

#### TC-API-011: History with Default Pagination
```bash
# Request
curl -X GET "http://localhost:8000/api/knowledge/sync/history?page=1&per_page=20" \
  -H "Authorization: Bearer {super_admin_token}"

# Expected Response (200 OK)
{
  "success": true,
  "items": [
    {
      "id": "sync-001",
      "timestamp": "2025-11-12T10:40:00Z",
      "sync_type": "force",
      "source": "all",
      "initiated_by": "admin@example.com",
      "status": "completed",
      "items_synced": 65,
      "duration_ms": 1234
    },
    // ... more items
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

**Validation:**
- ✅ Status code is 200
- ✅ Items are sorted by timestamp (newest first)
- ✅ Pagination metadata is correct
- ✅ Each item has all required fields

#### TC-API-012: History with Source Filter
```bash
# Request
curl -X GET "http://localhost:8000/api/knowledge/sync/history?source=faqs&page=1&per_page=10" \
  -H "Authorization: Bearer {super_admin_token}"

# Expected Response (200 OK)
{
  "success": true,
  "items": [
    // Only FAQs sync records
  ],
  "total": 15,
  "page": 1,
  "per_page": 10,
  "pages": 2
}
```

**Validation:**
- ✅ All items have `source: "faqs"` or `source: "all"`
- ✅ Other sources are excluded

#### TC-API-013: History with Sync Type Filter
```bash
# Request
curl -X GET "http://localhost:8000/api/knowledge/sync/history?sync_type=auto&page=1&per_page=10" \
  -H "Authorization: Bearer {super_admin_token}"

# Expected Response (200 OK)
{
  "success": true,
  "items": [
    // Only auto sync records
  ],
  "total": 30,
  "page": 1,
  "per_page": 10,
  "pages": 3
}
```

**Validation:**
- ✅ All items have `sync_type: "auto"`
- ✅ Force syncs are excluded

---

## Frontend Integration Testing

### UI Components Testing

#### TC-UI-001: Status Cards Display
**Steps:**
1. Navigate to `/dashboard/superadmin/knowledge-sync`
2. Wait for status cards to load

**Expected Results:**
- ✅ 3 status cards are visible (FAQs, Services, Policies)
- ✅ Each card shows:
  - Source name
  - Last sync timestamp (formatted as "2 minutes ago")
  - Item count (e.g., "45 items")
  - Sync status badge (Success, Warning, or Error)
  - "Changes pending" indicator (if applicable)
- ✅ Loading skeletons are shown during data fetch
- ✅ No console errors

#### TC-UI-002: Auto Sync Buttons
**Steps:**
1. Click "Auto Sync All" button
2. Observe loading state
3. Wait for completion

**Expected Results:**
- ✅ Button shows loading spinner during sync
- ✅ Button is disabled during sync
- ✅ Toast notification appears on success
- ✅ Status cards update with new timestamps
- ✅ Item counts refresh
- ✅ Sync operation completes within 5 seconds

#### TC-UI-003: Force Sync Confirmation
**Steps:**
1. Click "Force Sync All" button
2. Observe confirmation dialog

**Expected Results:**
- ✅ Alert dialog appears with warning message
- ✅ Dialog title: "Force Sync Confirmation"
- ✅ Dialog description warns about overriding manual changes
- ✅ "Cancel" button closes dialog without action
- ✅ "Force Sync" button is styled as destructive (red)
- ✅ Clicking "Force Sync" triggers sync operation

#### TC-UI-004: Differences Tab
**Steps:**
1. Click "Differences" tab
2. Wait for diff data to load

**Expected Results:**
- ✅ Tab switches to diff view
- ✅ Collapsible sections for each source
- ✅ Each section shows:
  - Source name
  - Total changes count
  - Expand/collapse arrow
- ✅ Expanded section shows:
  - Added items (green background)
  - Modified items (yellow background)
  - Removed items (red background)
- ✅ Code formatting is preserved (syntax highlighting)
- ✅ "No changes" message when sources are in sync

#### TC-UI-005: History Tab
**Steps:**
1. Click "History" tab
2. Wait for history data to load

**Expected Results:**
- ✅ Tab switches to history view
- ✅ Table displays sync records
- ✅ Columns: Timestamp, Type, Source, User, Status, Items, Duration
- ✅ Timestamps are formatted (e.g., "Nov 12, 2025 10:40 AM")
- ✅ Status badges have appropriate colors (Success=green, Error=red)
- ✅ Pagination controls at bottom
- ✅ Filters dropdown (Source, Sync Type)

#### TC-UI-006: Pagination
**Steps:**
1. On History tab, click "Next Page" button
2. Verify page 2 loads
3. Click "Previous Page"

**Expected Results:**
- ✅ Next page button loads page 2
- ✅ URL updates with `?page=2` parameter
- ✅ Table content updates
- ✅ Current page indicator shows "Page 2 of X"
- ✅ Previous button navigates back
- ✅ First/last page buttons work correctly

#### TC-UI-007: Filter Application
**Steps:**
1. On History tab, select "FAQs" from source filter
2. Observe table update
3. Clear filter

**Expected Results:**
- ✅ Table shows only FAQ-related syncs
- ✅ Filter badge appears showing active filter
- ✅ Clear button removes filter
- ✅ Table returns to unfiltered state
- ✅ Multiple filters can be applied simultaneously

#### TC-UI-008: Real-Time Updates
**Steps:**
1. Open Knowledge Sync Dashboard
2. Leave page open for 30+ seconds
3. Observe status cards

**Expected Results:**
- ✅ Status cards auto-refresh every 30 seconds
- ✅ Timestamps update without page reload
- ✅ No flickering or visual jumps
- ✅ Active tab content is preserved during refresh

#### TC-UI-009: Refresh Button
**Steps:**
1. Click "Refresh" button in header
2. Observe all components reload

**Expected Results:**
- ✅ Button shows loading spinner
- ✅ Current tab data refreshes
- ✅ Toast notification: "Data refreshed"
- ✅ Refresh completes within 2 seconds

---

## Role-Based Access Testing

### TC-RBAC-001: Super Admin Access
**User**: Super Admin (is_super_admin=true)

**Steps:**
1. Log in as super admin
2. Navigate to `/dashboard/superadmin/knowledge-sync`

**Expected Results:**
- ✅ Page loads successfully
- ✅ All features are accessible
- ✅ No permission errors

### TC-RBAC-002: Regular Admin Access Denied
**User**: Admin (role=admin, is_super_admin=false)

**Steps:**
1. Log in as regular admin
2. Attempt to navigate to `/dashboard/superadmin/knowledge-sync`

**Expected Results:**
- ✅ Access denied toast notification appears
- ✅ User is redirected to `/dashboard`
- ✅ Error message: "This page is only accessible to super administrators."

### TC-RBAC-003: Station Manager Access Denied
**User**: Station Manager (role=station_manager)

**Steps:**
1. Log in as station manager
2. Attempt to navigate to `/dashboard/superadmin/knowledge-sync`

**Expected Results:**
- ✅ Access denied toast notification appears
- ✅ User is redirected to `/dashboard`
- ✅ Navigation menu does not show link to sync dashboard

### TC-RBAC-004: Unauthenticated Access
**User**: Not logged in

**Steps:**
1. Navigate directly to `/dashboard/superadmin/knowledge-sync`

**Expected Results:**
- ✅ Redirect to login page
- ✅ Return URL preserved (redirects back after login)

---

## Real-Time Features Testing

### TC-RT-001: Auto-Refresh Polling
**Steps:**
1. Open Knowledge Sync Dashboard
2. Monitor network requests for 2 minutes
3. Check browser DevTools Network tab

**Expected Results:**
- ✅ Status API called every 30 seconds
- ✅ Polling continues while page is active
- ✅ Polling stops when navigating away
- ✅ No duplicate requests
- ✅ Request timing is consistent (±2 seconds)

### TC-RT-002: Background Tab Behavior
**Steps:**
1. Open Knowledge Sync Dashboard
2. Switch to another browser tab
3. Wait 1 minute
4. Switch back to sync dashboard

**Expected Results:**
- ✅ Polling may pause while tab is inactive (browser optimization)
- ✅ Data refreshes immediately upon returning to tab
- ✅ No accumulated requests fire at once

### TC-RT-003: Concurrent Syncs Prevention
**Steps:**
1. Click "Auto Sync All"
2. Immediately click "Force Sync All"

**Expected Results:**
- ✅ Second button is disabled during first sync
- ✅ Only one sync operation runs at a time
- ✅ Second operation queues or shows error
- ✅ No race conditions or data corruption

---

## Error Handling Testing

### TC-ERR-001: Network Timeout
**Steps:**
1. Simulate slow network (Chrome DevTools: Network > Throttling > Slow 3G)
2. Click "Auto Sync All"
3. Wait for timeout

**Expected Results:**
- ✅ Loading state persists during slow request
- ✅ Timeout after 30 seconds
- ✅ Error toast: "Request timed out. Please try again."
- ✅ UI returns to normal state
- ✅ No stuck loading spinners

### TC-ERR-002: Backend Server Down
**Steps:**
1. Stop backend server
2. Refresh Knowledge Sync Dashboard

**Expected Results:**
- ✅ Error toast: "Failed to load sync status. Please try again."
- ✅ Status cards show error state
- ✅ Retry button is available
- ✅ No app crash or white screen

### TC-ERR-003: Invalid API Response
**Steps:**
1. Mock backend to return malformed JSON
2. Load sync dashboard

**Expected Results:**
- ✅ Error is caught and handled gracefully
- ✅ User-friendly error message
- ✅ Sentry logs error for debugging
- ✅ App remains functional

### TC-ERR-004: Token Expiration
**Steps:**
1. Wait for JWT token to expire (or manually invalidate)
2. Attempt to trigger sync

**Expected Results:**
- ✅ 401 Unauthorized response
- ✅ Redirect to login page
- ✅ Return URL preserved
- ✅ Toast: "Session expired. Please log in again."

### TC-ERR-005: Sync Operation Failure
**Steps:**
1. Mock backend sync endpoint to return error
2. Trigger sync operation

**Expected Results:**
- ✅ Error toast with specific message
- ✅ Sync history records failure
- ✅ Status cards show error state
- ✅ User can retry operation

---

## Performance Testing

### TC-PERF-001: Initial Load Time
**Metrics:**
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.5s

**Steps:**
1. Open Chrome DevTools > Lighthouse
2. Run performance audit on sync dashboard
3. Analyze metrics

**Expected Results:**
- ✅ Performance score > 90
- ✅ All metrics within target ranges
- ✅ No layout shifts (CLS < 0.1)

### TC-PERF-002: Large Dataset Handling
**Steps:**
1. Seed database with 10,000+ records
2. Load sync dashboard
3. Trigger sync operation
4. Monitor performance

**Expected Results:**
- ✅ Status cards load within 2 seconds
- ✅ Diff rendering completes within 5 seconds
- ✅ History table pagination loads quickly
- ✅ No browser freezing or UI lag
- ✅ Memory usage remains stable (< 200 MB)

### TC-PERF-003: Concurrent User Load
**Steps:**
1. Simulate 10 concurrent super admin users
2. All trigger sync operations simultaneously
3. Monitor backend performance

**Expected Results:**
- ✅ All requests complete successfully
- ✅ Average response time < 2 seconds
- ✅ No deadlocks or race conditions
- ✅ Database locks release properly

---

## Bug Report Template

Use this template when reporting bugs:

```markdown
### Bug Report: [Brief Description]

**Reporter**: [Your Name]
**Date**: [Date Found]
**Environment**: [Development/Staging/Production]
**Browser**: [Browser + Version]
**User Role**: [Super Admin/Admin/etc.]

#### Summary
[2-3 sentence description of the bug]

#### Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

#### Expected Behavior
[What should happen]

#### Actual Behavior
[What actually happens]

#### Screenshots/Videos
[Attach screenshots or screen recordings]

#### Console Errors
```
[Paste any console errors or logs]
```

#### Network Logs
[Include relevant API request/response if applicable]

#### Impact/Severity
- [ ] Critical (blocks core functionality)
- [ ] High (major feature broken)
- [ ] Medium (minor feature issue)
- [ ] Low (cosmetic or edge case)

#### Reproducibility
- [ ] Always (100%)
- [ ] Often (50-99%)
- [ ] Sometimes (10-49%)
- [ ] Rare (< 10%)

#### Related Issues
[Link any related bugs or tickets]

#### Suggested Fix (Optional)
[If you have ideas on how to fix]
```

---

## QA Checklist

### Pre-Deployment Checklist

#### Functionality
- [ ] All 5 API endpoints return correct responses
- [ ] Status cards display accurate data
- [ ] Auto sync successfully updates database
- [ ] Force sync overrides manual changes
- [ ] Diff viewer shows all change types (added/modified/removed)
- [ ] History table loads with pagination
- [ ] Filters work correctly
- [ ] Real-time polling updates every 30 seconds
- [ ] All buttons and interactions work as expected

#### Security
- [ ] Super admin role protection enforced
- [ ] Non-superadmins cannot access dashboard
- [ ] API endpoints require authentication
- [ ] JWT tokens validated on all requests
- [ ] No sensitive data exposed in console logs
- [ ] CORS headers configured correctly
- [ ] Rate limiting applied to sync endpoints

#### Performance
- [ ] Initial page load < 3 seconds
- [ ] Sync operations complete within 5 seconds
- [ ] No memory leaks during extended use
- [ ] Large datasets render without lag
- [ ] Real-time polling doesn't impact performance

#### Error Handling
- [ ] Network errors show user-friendly messages
- [ ] Backend errors don't crash the app
- [ ] Loading states prevent duplicate requests
- [ ] Token expiration redirects to login
- [ ] All edge cases handled gracefully

#### UI/UX
- [ ] Consistent with admin design system
- [ ] Responsive on all screen sizes (mobile, tablet, desktop)
- [ ] Accessible (keyboard navigation, screen readers)
- [ ] Toast notifications are clear and actionable
- [ ] Loading indicators show during async operations
- [ ] No layout shifts or visual jumps
- [ ] Colors follow brand guidelines

#### Documentation
- [ ] API documentation complete
- [ ] Component usage documented
- [ ] Test cases written for all features
- [ ] README updated with setup instructions
- [ ] Deployment guide includes sync dashboard

#### Code Quality
- [ ] No ESLint errors
- [ ] No TypeScript errors
- [ ] All imports properly sorted
- [ ] No unused variables (except documented TODOs)
- [ ] Code follows project style guide
- [ ] All functions have type annotations
- [ ] Complex logic has comments

### Post-Deployment Verification

#### Production Smoke Tests
- [ ] Dashboard accessible via production URL
- [ ] Super admin can log in and access
- [ ] Status cards load with real data
- [ ] At least one sync operation completes successfully
- [ ] History table shows production sync records
- [ ] No console errors in production build
- [ ] Performance metrics meet targets

#### Monitoring Setup
- [ ] Sentry error tracking active
- [ ] API endpoint monitoring configured
- [ ] Performance metrics tracked (Lighthouse CI)
- [ ] Alert notifications set up for failures

---

## Test Results Template

Use this template to record test execution:

```markdown
### Test Execution Report

**Date**: [Date]
**Tester**: [Name]
**Environment**: [Dev/Staging/Prod]
**Build Version**: [Version/Commit Hash]

#### Test Summary
- Total Tests: [Number]
- Passed: [Number]
- Failed: [Number]
- Blocked: [Number]
- Pass Rate: [Percentage]

#### Failed Tests
| Test ID | Test Name | Failure Reason | Severity | Bug Ticket |
|---------|-----------|----------------|----------|------------|
| TC-001  | ...       | ...            | High     | BUG-123    |

#### Blocked Tests
| Test ID | Test Name | Blocking Issue | Resolution ETA |
|---------|-----------|----------------|----------------|
| TC-002  | ...       | Backend down   | Tomorrow       |

#### Notes
[Any additional observations or comments]

#### Sign-Off
- [ ] QA Lead Approval
- [ ] Product Owner Approval
- [ ] Ready for Production
```

---

## Continuous Testing

### Automated Test Scenarios

**Unit Tests** (Jest/Vitest):
```typescript
// Example: SyncStatusCards component test
describe('SyncStatusCards', () => {
  it('displays loading state initially', () => {
    render(<SyncStatusCards isLoading={true} status={null} />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('displays status cards after load', () => {
    const mockStatus = { sources: { faqs: {...}, services: {...}, policies: {...} } };
    render(<SyncStatusCards isLoading={false} status={mockStatus} />);
    expect(screen.getByText('FAQs')).toBeInTheDocument();
  });
});
```

**Integration Tests** (Playwright):
```typescript
// Example: End-to-end sync flow test
test('complete sync flow', async ({ page }) => {
  await page.goto('/dashboard/superadmin/knowledge-sync');
  await page.click('button:has-text("Auto Sync All")');
  await expect(page.locator('.toast-success')).toBeVisible();
  await expect(page.locator('[data-testid="sync-timestamp"]')).toContainText('Just now');
});
```

### Regression Testing Checklist

Run these tests before every release:

1. **Core Sync Functionality** (30 min)
   - Auto sync all sources
   - Force sync single source
   - Verify database updates

2. **UI Navigation** (15 min)
   - Tab switching
   - Filter application
   - Pagination

3. **Access Control** (10 min)
   - Super admin access
   - Non-superadmin denial
   - Unauthenticated redirect

4. **Error Scenarios** (20 min)
   - Network timeout
   - Invalid responses
   - Backend errors

5. **Performance** (10 min)
   - Page load time
   - Sync operation speed
   - Memory usage

**Total Regression Time**: ~85 minutes

---

## Support & Troubleshooting

### Common Issues

**Issue**: Status cards show "Error" state
- **Cause**: Backend API unreachable or returning errors
- **Fix**: Check backend logs, verify API endpoints, check CORS

**Issue**: Sync operation times out
- **Cause**: Large dataset or slow database
- **Fix**: Optimize database queries, add indexes, increase timeout

**Issue**: Real-time updates not working
- **Cause**: Polling disabled or browser tab inactive
- **Fix**: Check useEffect dependencies, verify polling interval

**Issue**: Diff viewer shows no changes when changes exist
- **Cause**: Timestamp comparison issue or caching
- **Fix**: Clear browser cache, check timestamp precision in DB

### Debug Mode

Enable verbose logging:
```typescript
// Add to knowledge-sync.service.ts
const DEBUG = process.env.NEXT_PUBLIC_DEBUG_SYNC === 'true';

if (DEBUG) {
  console.log('[SYNC DEBUG]', operation, payload);
}
```

### Contact

- **Dev Team**: #knowledge-sync-dev on Slack
- **QA Team**: qa@myhibachichef.com
- **Emergency**: On-call engineer via PagerDuty

---

**Document Version**: 1.0  
**Last Updated**: November 12, 2025  
**Next Review**: After Week 2 completion
