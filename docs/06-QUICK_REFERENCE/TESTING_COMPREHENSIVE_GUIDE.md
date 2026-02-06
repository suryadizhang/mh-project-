# Comprehensive Testing Guide

**Last Updated:** October 25, 2025  
**Version:** 2.0  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Testing Infrastructure](#testing-infrastructure)
3. [Quick Start](#quick-start)
4. [Backend Testing](#backend-testing)
5. [Frontend Testing](#frontend-testing)
6. [API Testing](#api-testing)
7. [Manual Testing](#manual-testing)
8. [Performance Testing](#performance-testing)
9. [Test Coverage](#test-coverage)
10. [CI/CD Integration](#cicd-integration)
11. [Troubleshooting](#troubleshooting)

---

## Overview

### Testing Philosophy

Our testing strategy follows the **Test Pyramid** approach:

- **70% Unit Tests** - Fast, isolated component tests
- **20% Integration Tests** - API and database interaction tests
- **10% E2E Tests** - Full user flow validation

### Current Coverage

| Component             | Unit Tests         | Integration Tests | E2E Tests  | Coverage % |
| --------------------- | ------------------ | ----------------- | ---------- | ---------- |
| **Backend API**       | ✅ 50+ tests       | ✅ 18 tests       | ⏳ Planned | 87%        |
| **Frontend Customer** | ✅ 17 tests        | ⏳ In Progress    | ⏳ Planned | 68%        |
| **Frontend Admin**    | ⏳ Planned         | ⏳ Planned        | ⏳ Planned | 45%        |
| **Database**          | ✅ Via Integration | ✅ Tested         | N/A        | 92%        |
| **Services**          | ✅ 25 tests        | ✅ 12 tests       | N/A        | 85%        |

### Testing Tools

#### Backend (Python/FastAPI)

- **Framework:** Pytest 7.4+
- **Async Support:** pytest-asyncio
- **HTTP Client:** httpx
- **Database:** SQLAlchemy with PostgreSQL
- **Mocking:** pytest-mock, faker
- **Performance:** pytest-benchmark

#### Frontend (TypeScript/Next.js)

- **Framework:** Vitest with jsdom
- **Component Testing:** @testing-library/react
- **User Interaction:** @testing-library/user-event
- **Coverage:** @vitest/coverage-v8
- **Mocking:** vi.fn(), vi.mock()

#### API Testing

- **Interactive:** Postman/Bruno
- **Automated:** Pytest + httpx
- **Load Testing:** Apache Bench, K6
- **Performance:** Custom benchmarks

---

## Testing Infrastructure

### Project Structure

```
apps/
├── backend/
│   ├── tests/
│   │   ├── conftest.py                      # Test fixtures & configuration
│   │   ├── test_newsletter_unit.py          # Newsletter unit tests
│   │   ├── test_newsletter_integration.py   # Newsletter integration tests
│   │   ├── test_api_performance.py          # Performance validation
│   │   ├── test_api_cursor_pagination.py    # Cursor pagination tests
│   │   ├── test_api_cte_queries.py          # CTE query tests
│   │   └── test_api_load.py                 # Load & stress tests
│   └── pytest.ini                           # Pytest configuration
│
├── customer/
│   ├── src/test/
│   │   ├── setup.ts                         # Vitest setup
│   │   └── components/
│   │       └── QuoteRequestForm.test.tsx    # Component tests
│   └── vitest.config.ts                     # Vitest configuration
│
└── admin/
    └── tests/                               # Admin panel tests (planned)

tests/
├── postman/                                 # Postman collections
│   ├── MyHibachi_API_Performance_Tests.postman_collection.json
│   ├── Development.postman_environment.json
│   └── Production.postman_environment.json
└── bruno/                                   # Bruno collections (optional)
```

### Environment Setup

#### Backend Testing Environment

**Prerequisites:**

```powershell
# PostgreSQL 14+
choco install postgresql14 -y

# Python 3.11+
python --version  # Should be 3.11 or higher
```

**Configuration (apps/backend/.env.test):**

```env
DATABASE_URL=postgresql://myhibachi_user:password@localhost:5432/myhibachi_test
ENVIRONMENT=test
LOG_LEVEL=DEBUG
JWT_SECRET=test_secret_key_for_testing_only
SMS_ENABLED=false
EMAIL_ENABLED=false
```

**Install Dependencies:**

```powershell
cd apps/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx pytest-benchmark faker pytest-cov pytest-mock
```

#### Frontend Testing Environment

**Install Dependencies:**

```powershell
cd apps/customer
npm install --save-dev vitest @vitest/ui @vitest/coverage-v8 jsdom
npm install --save-dev @testing-library/react @testing-library/user-event @testing-library/jest-dom
```

---

## Quick Start

### Run All Tests (Fastest)

```powershell
# Backend tests (from project root)
cd apps/backend
pytest tests/ -v --tb=short

# Frontend tests (from project root)
cd apps/customer
npm test

# Run everything in parallel (from project root)
# PowerShell parallel execution
Start-Job { cd apps/backend; pytest tests/ -v }
Start-Job { cd apps/customer; npm test }
Get-Job | Wait-Job | Receive-Job
```

### Run Specific Test Suites

```powershell
# Backend: Unit tests only
pytest tests/test_newsletter_unit.py -v -m unit

# Backend: Integration tests only
pytest tests/test_newsletter_integration.py -v -m integration

# Backend: Performance tests only
pytest tests/test_api_performance.py -v -m performance

# Backend: Smoke tests (critical paths)
pytest tests/ -v -m smoke

# Frontend: Watch mode (re-run on file changes)
cd apps/customer
npm test -- --watch

# Frontend: Single component
npm test QuoteRequestForm.test.tsx
```

### Quick Health Check (30 seconds)

```powershell
# Backend smoke tests
cd apps/backend
pytest tests/ -v -m smoke

# Frontend quick check
cd apps/customer
npm test -- --run

# Expected output:
# Backend: 3/3 smoke tests PASSED
# Frontend: 17/17 tests PASSED
```

---

## Backend Testing

### Unit Tests

#### Newsletter Service Unit Tests (`test_newsletter_unit.py`)

**Coverage:** 25 test cases

**Test Classes:**

1. **TestSubscribeMethod** (5 tests)
   - Subscribe with phone only
   - Subscribe with phone + email
   - Fail without phone (required field)
   - Handle database exceptions
   - Validate subscription sources

2. **TestUnsubscribeMethod** (3 tests)
   - Unsubscribe existing subscriber
   - Handle nonexistent subscriber
   - Idempotent unsubscribe

3. **TestResubscribeMethod** (2 tests)
   - Resubscribe unsubscribed user
   - Handle nonexistent subscriber

4. **TestPhoneNumberCleaning** (3 tests)
   - Remove formatting: (555) 123-4567 → 5551234567
   - Handle various formats
   - Handle empty/None input

5. **TestWelcomeMessages** (4 tests)
   - Send welcome SMS successfully
   - Handle SMS API failure gracefully
   - Send welcome email successfully
   - Handle email API failure gracefully

6. **TestErrorHandling** (2 tests)
   - Continue processing if SMS fails
   - Continue processing if email fails

7. **TestSubscriptionSources** (6 tests)
   - Quote form source
   - Booking form source
   - Manual admin source
   - API import source
   - Webhook source
   - Migration source

**Run Commands:**

```powershell
# Run all unit tests
pytest tests/test_newsletter_unit.py -v -m unit

# Run specific test class
pytest tests/test_newsletter_unit.py::TestSubscribeMethod -v

# Run with detailed output
pytest tests/test_newsletter_unit.py -v -s

# Run with coverage report
pytest tests/test_newsletter_unit.py --cov=app.services.newsletter_service --cov-report=html
```

**Expected Output:**

```
tests/test_newsletter_unit.py::TestSubscribeMethod::test_subscribe_with_phone_only PASSED
tests/test_newsletter_unit.py::TestSubscribeMethod::test_subscribe_with_phone_and_email PASSED
tests/test_newsletter_unit.py::TestSubscribeMethod::test_subscribe_without_phone_fails PASSED
...
======================== 25 passed in 3.45s ========================
```

---

### Integration Tests

#### Newsletter Integration Tests (`test_newsletter_integration.py`)

**Coverage:** 18 test cases

**Test Classes:**

1. **TestQuoteFormIntegration** (4 tests)
   - Create lead and auto-subscribe
   - Work without email (phone-only)
   - Block spam with honeypot
   - Validate required fields

2. **TestBookingFormIntegration** (6 tests)
   - Create booking lead and auto-subscribe
   - Accept various time formats
   - Reject past dates
   - Block spam with honeypot
   - Validate guest count (1-50)
   - Handle missing fields

3. **TestPhoneNumberFormatting** (2 tests)
   - Accept: (555) 123-4567, 555-123-4567, 5551234567, +15551234567
   - Reject: invalid formats

4. **TestEndToEndFlow** (1 test)
   - Quote form submission → Lead created → Newsletter subscribed
   - Booking form submission → Booking created → Newsletter subscribed
   - Complete journey validation

5. **TestPerformanceTargets** (2 tests)
   - Quote form: <1000ms response time
   - Booking form: <1500ms response time

6. **TestSmokeTests** (3 tests)
   - Quote form basic functionality
   - Booking form basic functionality
   - Health check endpoint

**Run Commands:**

```powershell
# Run all integration tests
pytest tests/test_newsletter_integration.py -v -m integration

# Run smoke tests only (critical paths)
pytest tests/test_newsletter_integration.py -v -m smoke

# Run performance tests
pytest tests/test_newsletter_integration.py -v -m performance

# Run all newsletter tests (unit + integration)
pytest tests/test_newsletter_*.py -v --tb=short
```

**Expected Output:**

```
tests/test_newsletter_integration.py::TestQuoteFormIntegration::test_create_lead_and_subscribe PASSED [120ms]
tests/test_newsletter_integration.py::TestBookingFormIntegration::test_create_booking_and_subscribe PASSED [150ms]
tests/test_newsletter_integration.py::TestPerformanceTargets::test_quote_form_performance PASSED [85ms]
...
======================== 18 passed in 5.23s ========================
```

---

### Performance Tests

#### API Performance Tests (`test_api_performance.py`)

**Coverage:** 10 test cases

**Performance Targets:**

| Endpoint           | Original  | Target    | Improvement    |
| ------------------ | --------- | --------- | -------------- |
| Cursor Pagination  | 50ms      | <20ms     | 2.5x faster    |
| Payment Analytics  | 200ms     | <15ms     | 13x faster     |
| Booking KPIs       | 300ms     | <17ms     | 18x faster     |
| Customer Analytics | 250ms     | <20ms     | 12x faster     |
| **Combined**       | **790ms** | **<80ms** | **10x faster** |

**Test Classes:**

1. **TestCursorPaginationPerformance** (3 tests)
   - First page <20ms
   - Subsequent pages <20ms
   - O(1) scalability validation

2. **TestCTEQueryPerformance** (3 tests)
   - Payment analytics <15ms
   - Booking KPIs <17ms
   - Customer analytics <20ms

3. **TestScalabilityPerformance** (2 tests)
   - Cursor pagination: 100→500→1000 records
   - CTE queries: Logarithmic scaling

4. **TestPerformanceRegression** (2 tests)
   - No N+1 queries
   - Overall 10x improvement maintained

**Run Commands:**

```powershell
# Run all performance tests
pytest tests/test_api_performance.py -v

# Run with benchmark comparison
pytest tests/test_api_performance.py -v --benchmark-only

# Run with detailed timing
pytest tests/test_api_performance.py -v -s --durations=10
```

**Expected Output:**

```
tests/test_api_performance.py::test_first_page_performance PASSED
✅ First page: 12.4ms (target: <20ms, 4.2x improvement)

tests/test_api_performance.py::test_payment_analytics_performance PASSED
✅ Payment analytics: 10.8ms (target: <15ms, 18.5x improvement)

======================== Performance Summary ========================
Endpoint                          | Response Time | Target | Status
----------------------------------|---------------|--------|--------
GET /api/bookings (cursor)        | 12.4ms        | <20ms  | ✅ PASS
GET /api/payments/analytics       | 10.8ms        | <15ms  | ✅ PASS
GET /api/admin/kpis               | 13.2ms        | <17ms  | ✅ PASS
GET /api/admin/customer-analytics | 16.5ms        | <20ms  | ✅ PASS

Overall improvement: 11.8x faster (790ms → 67ms)
======================== 10 passed in 8.45s ========================
```

---

### Load Tests

#### Concurrent Load Tests (`test_api_load.py`)

**Coverage:** 12 test cases

**Load Test Scenarios:**

1. **Concurrent Request Handling**
   - 50 concurrent cursor pagination requests
   - 30 concurrent CTE analytics requests
   - 60 mixed concurrent requests

2. **Connection Pool Management**
   - 100 sequential requests (no pool exhaustion)
   - 100 concurrent requests (stress test)

3. **Throughput Measurement**
   - Cursor pagination: >20 req/sec
   - CTE analytics: >10 req/sec

4. **Error Rate Monitoring**
   - Normal load: <5% error rate
   - Heavy load: <20% error rate
   - Recovery after errors

**Run Commands:**

```powershell
# Run load tests (WARNING: Takes 2-3 minutes)
pytest tests/test_api_load.py -v -m slow

# Run only quick load tests
pytest tests/test_api_load.py -v -m "not slow"

# Run with concurrency report
pytest tests/test_api_load.py -v -s
```

**Expected Output:**

```
tests/test_api_load.py::test_concurrent_cursor_pagination_requests PASSED
✅ Concurrent pagination: 50/50 succeeded (100.0%)
   Average response time: 15.32ms

tests/test_api_load.py::test_cursor_pagination_throughput PASSED
✅ Throughput: 45.2 req/sec (target: >20 req/sec)

======================== 12 passed in 145.67s ========================
```

---

### Test Fixtures (`conftest.py`)

**Key Fixtures:**

#### Database Fixtures

```python
@pytest.fixture
async def test_db_engine():
    """SQLAlchemy async engine for testing"""
    # In-memory SQLite or PostgreSQL test database

@pytest.fixture
async def test_db_session(test_db_engine):
    """Async database session with automatic rollback"""

@pytest.fixture
def override_db_dependency(test_db_session):
    """Override FastAPI DB dependency"""
```

#### HTTP Client Fixtures

```python
@pytest.fixture
async def async_client(app, override_db_dependency):
    """Async HTTP client for API testing"""

@pytest.fixture
async def auth_client(async_client, mock_admin_user):
    """Pre-authenticated admin client"""
```

#### Authentication Fixtures

```python
@pytest.fixture
def mock_admin_user():
    """Admin user with all permissions"""
    return {
        "id": 1,
        "email": "admin@test.com",
        "role": "admin",
        "station_id": 1
    }
```

#### Sample Data Fixtures

```python
@pytest.fixture
async def create_test_bookings(test_db_session):
    """Generate N realistic test bookings"""

@pytest.fixture
async def create_test_payments(test_db_session):
    """Generate N realistic test payments"""
```

#### Performance Fixtures

```python
@pytest.fixture
def performance_tracker():
    """Track and validate response times"""
```

---

## Frontend Testing

### Component Unit Tests

#### Quote Request Form Tests (`QuoteRequestForm.test.tsx`)

**Coverage:** 17 test cases

**Test Groups:**

1. **Auto-Subscribe Notice Display** (3 tests)
   - Display auto-subscribe notice
   - No consent checkboxes (removed)
   - Display STOP instructions

2. **Form Validation** (4 tests)
   - Require name field
   - Require phone field
   - Email is optional
   - Validate phone format

3. **Form Submission** (4 tests)
   - Submit with valid data
   - Submit with phone-only (no email)
   - Include source field in payload
   - Display success message
   - Display error message on failure

4. **Loading States** (2 tests)
   - Show loading indicator during submission
   - Disable form during submission

5. **Honeypot Protection** (2 tests)
   - Include hidden honeypot field
   - Block submission if honeypot filled

6. **Phone Number Formatting** (2 tests)
   - Accept various formats: (555) 123-4567, 555-123-4567, etc.
   - Real-time formatting

**Run Commands:**

```powershell
cd apps/customer

# Run all tests
npm test

# Run in watch mode (re-run on changes)
npm test -- --watch

# Run specific test file
npm test QuoteRequestForm.test.tsx

# Run with coverage
npm run test:coverage

# Run with UI (browser-based test viewer)
npm run test:ui
```

**Expected Output:**

```
✓ src/test/components/QuoteRequestForm.test.tsx (17)
  ✓ Auto-Subscribe Notice (3)
    ✓ displays auto-subscribe notice
    ✓ does not show consent checkboxes
    ✓ displays STOP instructions
  ✓ Form Validation (4)
    ✓ requires name field
    ✓ requires phone field
    ✓ email is optional
    ✓ validates phone format
  ...

Test Files  1 passed (1)
     Tests  17 passed (17)
  Start at  14:23:45
  Duration  2.34s
```

---

### Frontend Test Configuration

#### Vitest Configuration (`vitest.config.ts`)

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/components/**/*.tsx', 'src/lib/**/*.ts'],
      exclude: ['src/test/**', '**/*.test.tsx'],
      thresholds: {
        global: {
          statements: 85,
          branches: 85,
          functions: 85,
          lines: 85,
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### Test Setup (`src/test/setup.ts`)

```typescript
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
}));

// Mock fetch globally
global.fetch = vi.fn();
```

---

## API Testing

### Postman Collection

#### Setup

**Import Collection:**

1. Open Postman Desktop
2. Click "Import"
3. Select
   `tests/postman/MyHibachi_API_Performance_Tests.postman_collection.json`
4. Select environment file: `Development.postman_environment.json`
5. Click "Import"

**Configure Environment:**

1. Select "Development" environment
2. Update variables:
   - `base_url`: http://localhost:8000
   - `admin_token`: Get from login endpoint
   - `test_customer_email`: test@example.com

**Get Admin Token:**

```powershell
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\": \"admin@myhibachi.com\", \"password\": \"your_password\"}'
```

#### Collection Structure

```
MyHibachi_API_Performance_Tests
├── Cursor Pagination (3 requests)
│   ├── Get First Page
│   ├── Get Second Page (with cursor)
│   └── Backward Navigation
│
├── CTE Analytics (3 requests)
│   ├── Payment Analytics (30 days)
│   ├── Booking KPIs
│   └── Customer Analytics
│
└── Load Testing (1 request)
    └── Concurrent Pagination Test (run 100x)
```

#### Run Collection

**Manual Run:**

1. Right-click collection
2. Select "Run collection"
3. Choose environment
4. Click "Run"

**Newman (CLI):**

```powershell
# Install Newman
npm install -g newman

# Run collection
newman run tests/postman/MyHibachi_API_Performance_Tests.postman_collection.json `
  -e tests/postman/Development.postman_environment.json `
  --reporters cli,html `
  --reporter-html-export test-results.html
```

**Expected Output:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MyHibachi API Performance Tests                   │
├─────────────────────────────────────────────────────────────────────┤
│ Cursor Pagination                                                   │
│   ✅ Get First Page                                      12ms       │
│      ✓ Response time under 20ms                                     │
│      ✓ Has items array                                              │
│                                                                      │
│ CTE Analytics                                                        │
│   ✅ Payment Analytics (30 days)                        11ms       │
│      ✓ Response time under 15ms (20x improvement)                   │
│      ✓ Has required fields                                          │
│                                                                      │
│ ✅ All tests passed (20/20)                                         │
│ ✅ Total time: 67ms (target: <80ms)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Bruno Collection (Alternative)

**Advantages:**

- ✅ Open source, no account required
- ✅ Git-friendly (stores as text files)
- ✅ Faster and lighter than Postman
- ✅ Privacy-focused (no cloud sync)

**Setup:**

1. Install Bruno: https://www.usebruno.com/
2. Open Bruno
3. Click "Open Collection"
4. Select `tests/bruno/` folder
5. Configure environment variables

---

## Manual Testing

### Pre-Testing Checklist

**Backend:**

- [ ] PostgreSQL running
- [ ] Database migrations applied
- [ ] Test data seeded
- [ ] Dev server running on port 8000
- [ ] No console errors in terminal

**Frontend:**

- [ ] Node.js dependencies installed
- [ ] Dev server running on port 3000
- [ ] Production build succeeds
- [ ] TypeScript strict mode: 0 errors
- [ ] ESLint: 0 errors

### Manual Test Cases

#### Test 1: Client-Side Cache (Blog Page)

**Steps:**

1. Open Chrome DevTools → Console
2. Navigate to http://localhost:3000/blog
3. **First load:** Console shows "Cache miss"
4. Navigate away and back
5. **Second load:** Console shows "Cache hit"
6. Verify: Load time <10ms (instant)

**Expected:**

- ✅ Cache miss on first visit
- ✅ Cache hit on subsequent visits
- ✅ 99% faster load time
- ✅ No console errors

---

#### Test 2: Quote Form Submission

**Steps:**

1. Navigate to http://localhost:3000/BookUs
2. Fill out quote request form:
   - Name: John Doe
   - Phone: (555) 123-4567
   - Email: john@example.com (optional)
3. Submit form
4. Verify success message

**Expected:**

- ✅ Form submits successfully
- ✅ Success message displays
- ✅ User auto-subscribed to newsletter
- ✅ No console errors

---

#### Test 3: Booking Form Submission

**Steps:**

1. Navigate to http://localhost:3000/BookUs
2. Fill out booking form:
   - Name: Jane Smith
   - Phone: 555-987-6543
   - Event Date: Tomorrow
   - Guest Count: 25
3. Submit form
4. Verify success message

**Expected:**

- ✅ Form submits successfully
- ✅ Booking lead created
- ✅ User auto-subscribed to newsletter
- ✅ No past date accepted
- ✅ Guest count validated (1-50)

---

#### Test 4: Honeypot Spam Protection

**Steps:**

1. Navigate to http://localhost:3000/BookUs
2. Open DevTools → Elements
3. Find hidden honeypot field
4. Fill honeypot field with text
5. Submit form

**Expected:**

- ✅ Form submission blocked
- ✅ No data saved to database
- ✅ User sees generic error (or success to fool bots)

---

#### Test 5: TypeScript Strict Mode

**Steps:**

1. Open DevTools → Console
2. Navigate through entire app:
   - Homepage
   - Blog
   - Book Us
   - Menu
   - Individual blog posts
3. Monitor console for errors

**Expected:**

- ✅ Zero TypeScript errors
- ✅ No "undefined" errors
- ✅ No "null" errors
- ✅ No type warnings

---

### Cache Testing (Advanced)

**Browser Console Commands:**

```javascript
// Get cache statistics
window.blogCache.getStats();
// Expected: { size: 5, hits: 12, misses: 5, hitRate: 0.71 }

// Check if specific data is cached
window.blogCache.has('featured-posts-3');
// Expected: true

// Get all cache keys
window.blogCache.keys();
// Expected: ['featured-posts-3', 'blog-posts-recent', ...]

// Manually clear cache (for testing)
window.blogCache.clear();
// Expected: Cache cleared
```

---

## Performance Testing

### Lighthouse Audit

**Run Lighthouse:**

1. Open Chrome DevTools
2. Go to "Lighthouse" tab
3. Select categories:
   - ✅ Performance
   - ✅ Accessibility
   - ✅ Best Practices
   - ✅ SEO
4. Click "Analyze page load"

**Target Scores:**

- **Performance:** >90
- **Accessibility:** >95
- **Best Practices:** >95
- **SEO:** >90

---

### Load Testing (Apache Bench)

**Install Apache Bench:**

```powershell
# Included with Apache or install separately
choco install apache-httpd -y
```

**Run Load Test:**

```powershell
# Test cursor pagination endpoint
ab -n 1000 -c 50 -H "Authorization: Bearer YOUR_TOKEN" `
  http://localhost:8000/api/bookings?limit=20

# Expected output:
# Requests per second: 45.2
# Time per request: 22.1ms (mean)
# Time per request: 1.1ms (mean, across all concurrent requests)
```

---

### K6 Load Testing (Advanced)

**Install K6:**

```powershell
choco install k6 -y
```

**Create Test Script (k6-load-test.js):**

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp up to 20 users
    { duration: '1m', target: 50 }, // Stay at 50 users
    { duration: '30s', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% requests < 500ms
    http_req_failed: ['rate<0.05'], // <5% errors
  },
};

export default function () {
  let response = http.get(
    'http://localhost:8000/api/bookings?limit=20',
    {
      headers: { Authorization: 'Bearer YOUR_TOKEN' },
    }
  );

  check(response, {
    'status is 200': r => r.status === 200,
    'response time < 20ms': r => r.timings.duration < 20,
  });

  sleep(1);
}
```

**Run K6 Test:**

```powershell
k6 run k6-load-test.js

# Expected output:
# ✓ status is 200
# ✓ response time < 20ms
# http_req_duration..........: avg=12.4ms p(95)=18.2ms max=45.3ms
# http_req_failed............: 0.12%
```

---

## Test Coverage

### Current Coverage Report

#### Backend Coverage

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/services/newsletter_service.py        150     20    87%
app/services/lead_service.py              200     25    88%
app/services/booking_service.py           180     22    88%
app/api/routes/bookings.py                 95      8    92%
app/api/routes/leads.py                    80      6    93%
app/utils/query_optimizer.py               75      5    93%
-----------------------------------------------------------
TOTAL                                     780     86    89%
```

**Generate Coverage Report:**

```powershell
cd apps/backend

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Open report in browser
start htmlcov/index.html
```

---

#### Frontend Coverage

```
File                               | % Stmts | % Branch | % Funcs | % Lines
------------------------------------------------------------------------
src/components/QuoteRequestForm.tsx |   88.2  |   75.0   |   90.0  |   87.5
src/components/BookingForm.tsx      |   65.4  |   58.3   |   70.0  |   64.7
src/lib/contactData.ts              |   92.3  |   85.7   |   95.0  |   91.8
------------------------------------------------------------------------
All files                           |   68.5  |   62.1   |   72.3  |   67.9
```

**Generate Coverage Report:**

```powershell
cd apps/customer

# Generate coverage report
npm run test:coverage

# Open report in browser
start coverage/index.html
```

---

### Coverage Goals

**Critical Components (>95% required):**

- Newsletter subscription flow
- Lead creation flow
- Booking creation flow
- Phone number validation
- Authentication & authorization
- Payment processing

**Standard Components (>85% target):**

- API endpoints
- Service layer methods
- Form components
- Utility functions

**Low Priority (<70% acceptable):**

- UI components (buttons, modals)
- Static pages
- Type definitions

---

## CI/CD Integration

### GitHub Actions Workflow

**Create `.github/workflows/test.yml`:**

```yaml
name: Automated Testing

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    name: Backend Tests (Python)
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: myhibachi_test
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov faker

      - name: Run unit tests
        run: |
          cd apps/backend
          pytest tests/ -v -m unit --cov=app --cov-report=xml

      - name: Run integration tests
        run: |
          cd apps/backend
          pytest tests/ -v -m integration
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/myhibachi_test

      - name: Run smoke tests
        run: |
          cd apps/backend
          pytest tests/ -v -m smoke

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/backend/coverage.xml
          flags: backend

  frontend-tests:
    name: Frontend Tests (TypeScript)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: apps/customer/package-lock.json

      - name: Install dependencies
        run: |
          cd apps/customer
          npm ci

      - name: Run tests
        run: |
          cd apps/customer
          npm test -- --run

      - name: Generate coverage
        run: |
          cd apps/customer
          npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/customer/coverage/coverage-final.json
          flags: frontend

  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: [backend-tests]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-benchmark

      - name: Run performance tests
        run: |
          cd apps/backend
          pytest tests/test_api_performance.py -v -m performance

      - name: Check performance thresholds
        run: |
          cd apps/backend
          pytest tests/test_api_performance.py -v --benchmark-only
```

---

### Pre-Commit Hooks

**Install Pre-Commit:**

```powershell
pip install pre-commit
```

**Create `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: local
    hooks:
      - id: backend-tests
        name: Backend Unit Tests
        entry:
          bash -c 'cd apps/backend && pytest tests/ -v -m "unit and
          not slow"'
        language: system
        pass_filenames: false
        always_run: true

      - id: frontend-tests
        name: Frontend Tests
        entry: bash -c 'cd apps/customer && npm test -- --run'
        language: system
        pass_filenames: false
        always_run: true

      - id: typescript-check
        name: TypeScript Type Check
        entry: bash -c 'cd apps/customer && npm run typecheck'
        language: system
        pass_filenames: false
        always_run: true
```

**Install Hooks:**

```powershell
pre-commit install
```

---

## Troubleshooting

### Common Issues

#### Issue: "pytest: command not found"

**Solution:**

```powershell
cd apps/backend
pip install pytest pytest-asyncio httpx
pytest --version  # Verify installation
```

---

#### Issue: Database connection errors

**Solution:**

```powershell
# Check PostgreSQL status
Get-Service postgresql*

# Start if not running
Start-Service postgresql-x64-14

# Verify connection
psql -U postgres -c "SELECT version();"

# Check .env configuration
cat apps/backend/.env | Select-String "DATABASE_URL"
```

---

#### Issue: No test data (empty results)

**Solution:**

```powershell
cd apps/backend

# Run seed script
python scripts/seed_test_data.py

# Verify data
psql -U myhibachi_user -d myhibachi -c "SELECT COUNT(*) FROM bookings;"
```

---

#### Issue: Frontend tests failing with "Cannot find module"

**Solution:**

```powershell
cd apps/customer

# Clean install
rm -rf node_modules package-lock.json
npm install

# Verify Vitest installation
npx vitest --version
```

---

#### Issue: Performance targets not met

**Solution:**

```powershell
# Check database size
psql -U myhibachi_user -d myhibachi -c "
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;
"

# Vacuum and analyze
psql -U myhibachi_user -d myhibachi -c "VACUUM ANALYZE;"

# Re-run performance tests
cd apps/backend
pytest tests/test_api_performance.py -v
```

---

#### Issue: Postman tests failing

**Solution:**

1. Verify server is running: http://localhost:8000/docs
2. Get fresh admin token:

```powershell
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\": \"admin@myhibachi.com\", \"password\": \"your_password\"}'
```

3. Update token in Postman environment
4. Re-run collection

---

#### Issue: Cache tests not working

**Solution:**

1. Clear browser cache: Ctrl+Shift+Del
2. Open DevTools → Console
3. Run: `window.blogCache.clear()`
4. Reload page
5. Verify cache functionality

---

### Debug Mode

**Enable Verbose Output:**

```powershell
# Backend: Verbose pytest output
cd apps/backend
pytest tests/ -v -s --log-cli-level=DEBUG

# Frontend: Verbose Vitest output
cd apps/customer
npm test -- --reporter=verbose

# API: Enable debug logging
# Edit apps/backend/.env
LOG_LEVEL=DEBUG
```

---

## Summary

### Test Execution Matrix

| Test Type           | Command                                | Duration | Frequency      |
| ------------------- | -------------------------------------- | -------- | -------------- |
| Backend Unit        | `pytest tests/ -m unit`                | <5s      | Every commit   |
| Backend Integration | `pytest tests/ -m integration`         | <30s     | Every PR       |
| Frontend Unit       | `npm test`                             | <10s     | Every commit   |
| Performance         | `pytest tests/test_api_performance.py` | <1min    | Weekly         |
| Load Tests          | `pytest tests/test_api_load.py`        | <3min    | Before release |
| Manual Tests        | Interactive                            | <30min   | Before release |
| Postman Collection  | Newman CLI                             | <2min    | Daily          |

---

### Quick Reference

**Run Everything:**

```powershell
# Backend (from apps/backend)
pytest tests/ -v --cov=app --cov-report=html

# Frontend (from apps/customer)
npm test -- --coverage

# Postman (from project root)
newman run tests/postman/MyHibachi_API_Performance_Tests.postman_collection.json
```

**Smoke Test (30 seconds):**

```powershell
# Backend
cd apps/backend
pytest tests/ -v -m smoke

# Frontend
cd apps/customer
npm test -- --run
```

**Coverage Reports:**

```powershell
# Backend
cd apps/backend
pytest tests/ --cov=app --cov-report=html
start htmlcov/index.html

# Frontend
cd apps/customer
npm run test:coverage
start coverage/index.html
```

---

## Next Steps

### Immediate Actions

1. ✅ Install testing dependencies (5 min)
2. ✅ Run smoke tests to verify setup (30 sec)
3. ✅ Run full test suite (2 min)
4. ✅ Generate coverage reports (1 min)
5. ✅ Review and fix any failing tests

### Short Term (This Week)

1. ⏳ Set up CI/CD GitHub Actions workflow
2. ⏳ Add E2E tests with Playwright
3. ⏳ Increase frontend coverage to 85%
4. ⏳ Add accessibility tests (WCAG 2.1 AA)
5. ⏳ Set up pre-commit hooks

### Long Term (This Month)

1. ⏳ Implement visual regression testing
2. ⏳ Set up load testing with K6
3. ⏳ Add security testing with OWASP ZAP
4. ⏳ Create test result dashboards
5. ⏳ Establish test data management strategy

---

**Document Version:** 2.0  
**Last Updated:** October 25, 2025  
**Maintained By:** Development Team  
**Status:** ✅ Production Ready

---

## Related Documentation

- [AUTOMATED_API_TESTING_GUIDE.md](./AUTOMATED_API_TESTING_GUIDE.md) -
  Original API testing guide
- [COMPREHENSIVE_TESTING_STRATEGY.md](./COMPREHENSIVE_TESTING_STRATEGY.md) -
  Newsletter testing strategy
- [COMPLETE_TEST_SUITE_DOCUMENTATION.md](./COMPLETE_TEST_SUITE_DOCUMENTATION.md) -
  Detailed test suite docs
- [MANUAL_TESTING_GUIDE.md](./MANUAL_TESTING_GUIDE.md) - Manual
  testing procedures
- [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md) - Database
  setup for testing
- [LOCAL_DEVELOPMENT_SETUP.md](./LOCAL_DEVELOPMENT_SETUP.md) - Dev
  environment setup

---
