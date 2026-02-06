# 🧪 End-to-End Testing Plan - MyHibachi Full Stack

## 📋 Overview

This E2E testing suite validates the entire MyHibachi system as it
would run in production, testing all integrations between:

- **Customer Frontend** (Next.js)
- **Admin Frontend** (Next.js)
- **Backend API** (FastAPI)
- **Database** (PostgreSQL)
- **Redis** (Caching & WebSocket)
- **Celery** (Background tasks)
- **Stripe** (Payments)
- **WhatsApp** (Notifications)

---

## 🎯 Testing Strategy

### **Phase 1: Quick Tests (Frontend Only)**

Tests UI, navigation, component rendering

- **Runtime:** 2-5 minutes
- **Services needed:** Frontend apps only

### **Phase 2: Integration Tests (Frontend + Backend)**

Tests API calls, booking creation, data flow

- **Runtime:** 10-15 minutes
- **Services needed:** Frontend + Backend + Database

### **Phase 3: Full E2E Tests (Production Simulation)**

Tests complete user journeys including payments, notifications,
real-time updates

- **Runtime:** 20-30 minutes
- **Services needed:** All services running

---

## 🚀 Quick Start

### **1. Run Quick Tests (Development)**

```bash
# Start only customer frontend
npm run dev:customer

# Run frontend-only tests
npx playwright test --project=customer --grep @smoke
```

### **2. Run Full Local Tests (Pre-Production)**

```bash
# Option A: Using Docker Compose (Recommended)
docker-compose up -d

# Option B: Manual start all services
# Terminal 1: Backend
cd apps/backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Redis
redis-server

# Terminal 3: Celery
cd apps/backend
celery -A workers.celery_config worker -l info --pool=solo

# Terminal 4: Customer Frontend
npm run dev:customer

# Terminal 5: Admin Frontend
npm run dev:admin

# Then run all E2E tests
npx playwright test
```

### **3. Run Production Tests (After Deploy)**

```bash
# Test live production site
BASE_URL=https://yourdomain.com npx playwright test --config=playwright.prod.config.ts
```

---

## 📊 Test Organization

```
e2e/
├── customer/              # Customer-facing tests
│   ├── smoke/            # Quick UI tests (@smoke tag)
│   │   ├── homepage.spec.ts
│   │   ├── navigation.spec.ts
│   │   └── menu.spec.ts
│   ├── booking/          # Booking flow tests (@booking tag)
│   │   ├── booking-flow.spec.ts
│   │   ├── date-selection.spec.ts
│   │   └── guest-count.spec.ts
│   ├── payment/          # Payment tests (@payment tag)
│   │   ├── stripe-payment.spec.ts
│   │   ├── zelle-payment.spec.ts
│   │   └── venmo-payment.spec.ts
│   └── integration/      # Full journey tests (@e2e tag)
│       ├── complete-booking.spec.ts
│       └── booking-with-payment.spec.ts
│
├── admin/                 # Admin dashboard tests
│   ├── smoke/            # Quick UI tests (@smoke tag)
│   │   ├── dashboard.spec.ts
│   │   └── navigation.spec.ts
│   ├── bookings/         # Booking management (@admin tag)
│   │   ├── view-bookings.spec.ts
│   │   ├── edit-booking.spec.ts
│   │   └── cancel-booking.spec.ts
│   ├── realtime/         # Real-time features (@realtime tag)
│   │   ├── websocket-updates.spec.ts
│   │   └── notifications.spec.ts
│   └── integration/      # Full admin flows (@e2e tag)
│       └── booking-lifecycle.spec.ts
│
├── api/                   # API-only tests (@api tag)
│   ├── auth.spec.ts
│   ├── bookings.spec.ts
│   ├── payments.spec.ts
│   └── webhooks.spec.ts
│
└── helpers/              # Shared utilities
    ├── auth-helpers.ts
    ├── booking-helpers.ts
    ├── payment-helpers.ts
    └── test-data.ts
```

---

## 🏷️ Test Tags & Filtering

Run specific test groups:

```bash
# Smoke tests only (fastest)
npx playwright test --grep @smoke

# Payment tests only
npx playwright test --grep @payment

# Full E2E tests only
npx playwright test --grep @e2e

# Admin tests only
npx playwright test --project=admin

# Exclude slow tests
npx playwright test --grep-invert @slow
```

---

## 📝 Test Scenarios by Priority

### **Critical Path Tests (Must Pass)**

#### 1. **Customer Booking Flow** (@e2e @critical)

- [ ] User can view homepage
- [ ] User can navigate to booking page
- [ ] User can select event date
- [ ] User can select guest count
- [ ] User can select menu items
- [ ] User can submit booking form
- [ ] Booking is created in database
- [ ] Confirmation email is sent

#### 2. **Payment Processing** (@payment @critical)

- [ ] Stripe payment intent created
- [ ] User can enter card details
- [ ] Payment is processed successfully
- [ ] Webhook received and processed
- [ ] Payment status updated in database
- [ ] Receipt email sent

#### 3. **Admin Booking Management** (@admin @critical)

- [ ] Admin can log in
- [ ] Admin can view all bookings
- [ ] Admin can view booking details
- [ ] Admin can update booking status
- [ ] Admin can cancel booking
- [ ] Cancellation notification sent

### **Important Tests (Should Pass)**

#### 4. **Real-time Updates** (@realtime @important)

- [ ] New booking appears in admin dashboard (WebSocket)
- [ ] Booking status changes reflect immediately
- [ ] Notifications appear in real-time
- [ ] Read receipts update correctly

#### 5. **WhatsApp Notifications** (@notifications @important)

- [ ] Booking confirmation sent via WhatsApp
- [ ] Payment confirmation sent via WhatsApp
- [ ] Reminder sent via WhatsApp
- [ ] Admin notification sent via WhatsApp

#### 6. **Alternative Payment Methods** (@payment @important)

- [ ] Zelle payment instructions shown
- [ ] Venmo payment instructions shown
- [ ] Manual payment confirmation by admin
- [ ] Payment history displayed correctly

### **Nice to Have Tests**

#### 7. **User Experience** (@ux)

- [ ] Form validation works
- [ ] Error messages display correctly
- [ ] Loading states show properly
- [ ] Success animations play
- [ ] Mobile responsive design

#### 8. **Performance** (@performance)

- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms
- [ ] WebSocket connection < 1 second
- [ ] Payment processing < 5 seconds

---

## 🔧 Configuration

### **Local Development**

```typescript
// playwright.config.ts (current)
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    headless: true,
  },
  projects: [
    { name: 'customer', testDir: 'e2e/customer' },
    { name: 'admin', testDir: 'e2e/admin' },
  ],
});
```

### **Production Testing**

```typescript
// playwright.prod.config.ts (to be created)
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 2, // Retry failed tests on production
  use: {
    baseURL: process.env.PROD_URL || 'https://yourdomain.com',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'customer-prod',
      testDir: 'e2e/customer',
      use: { baseURL: 'https://customer.yourdomain.com' },
    },
    {
      name: 'admin-prod',
      testDir: 'e2e/admin',
      use: { baseURL: 'https://admin.yourdomain.com' },
    },
  ],
});
```

---

## ⚙️ Services Dependency Matrix

| Test Type              | Customer | Admin | Backend | DB  | Redis | Celery | Stripe | WhatsApp |
| ---------------------- | -------- | ----- | ------- | --- | ----- | ------ | ------ | -------- |
| **Smoke Tests**        | ✅       | ✅    | ❌      | ❌  | ❌    | ❌     | ❌     | ❌       |
| **Navigation**         | ✅       | ✅    | ❌      | ❌  | ❌    | ❌     | ❌     | ❌       |
| **Booking Creation**   | ✅       | ❌    | ✅      | ✅  | ❌    | ❌     | ❌     | ❌       |
| **Payment Processing** | ✅       | ❌    | ✅      | ✅  | ❌    | ❌     | ✅     | ❌       |
| **Admin Management**   | ❌       | ✅    | ✅      | ✅  | ❌    | ❌     | ❌     | ❌       |
| **Real-time Updates**  | ✅       | ✅    | ✅      | ✅  | ✅    | ❌     | ❌     | ❌       |
| **Notifications**      | ✅       | ✅    | ✅      | ✅  | ✅    | ✅     | ❌     | ✅       |
| **Full E2E**           | ✅       | ✅    | ✅      | ✅  | ✅    | ✅     | ✅     | ✅       |

---

## 📈 CI/CD Integration

### **Pre-Deployment Tests**

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Install dependencies
        run: npm install
      - name: Run E2E tests
        run: npm run test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

### **Post-Deployment Tests**

```yaml
# .github/workflows/production-tests.yml
name: Production Smoke Tests
on:
  deployment_status:

jobs:
  prod-smoke-tests:
    if: github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run production tests
        run: |
          BASE_URL=${{ secrets.PROD_URL }} \
          npx playwright test --config=playwright.prod.config.ts --grep @smoke
```

---

## 🎬 Test Execution Scripts

### **Create helper scripts:**

```bash
# scripts/test-local.sh
#!/bin/bash
echo "🚀 Starting all services..."
docker-compose up -d
sleep 10

echo "🧪 Running E2E tests..."
npx playwright test

echo "📊 Generating report..."
npx playwright show-report
```

```bash
# scripts/test-production.sh
#!/bin/bash
echo "🌐 Testing production environment..."
BASE_URL=https://yourdomain.com npx playwright test --config=playwright.prod.config.ts --grep "@smoke|@critical"

echo "📧 Sending results..."
# Add notification logic here
```

```powershell
# scripts/test-local.ps1
Write-Host "🚀 Starting all services..." -ForegroundColor Green
docker-compose up -d
Start-Sleep -Seconds 10

Write-Host "🧪 Running E2E tests..." -ForegroundColor Green
npx playwright test

Write-Host "📊 Generating report..." -ForegroundColor Green
npx playwright show-report
```

---

## 📚 Best Practices

### **1. Test Data Management**

```typescript
// e2e/helpers/test-data.ts
export const testBooking = {
  customerName: 'Test User',
  email: 'test@example.com',
  phone: '555-0123',
  eventDate: '2025-12-25',
  guestCount: 20,
  menuItems: ['Hibachi Chicken', 'Fried Rice'],
};

export const testPayment = {
  cardNumber: '4242424242424242', // Stripe test card
  expiry: '12/25',
  cvc: '123',
};
```

### **2. Authentication Helpers**

```typescript
// e2e/helpers/auth-helpers.ts
export async function loginAsAdmin(page: Page) {
  await page.goto('/admin/login');
  await page.fill('[name="email"]', 'admin@myhibachi.com');
  await page.fill(
    '[name="password"]',
    process.env.TEST_ADMIN_PASSWORD!
  );
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin/dashboard');
}
```

### **3. Wait for Backend**

```typescript
// e2e/helpers/wait-helpers.ts
export async function waitForBackend(baseURL: string) {
  const maxRetries = 30;
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`${baseURL}/health`);
      if (response.ok) return true;
    } catch (e) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('Backend not ready');
}
```

---

## 🔍 Monitoring & Reporting

### **Test Results Dashboard**

- View HTML report: `npx playwright show-report`
- Screenshots on failure: `playwright-report/screenshots/`
- Videos on failure: `playwright-report/videos/`
- Traces: `playwright-report/traces/`

### **Metrics to Track**

- Test pass rate (aim for 95%+)
- Test execution time
- Flaky test detection
- Coverage of critical paths

---

## 🚨 Troubleshooting

### **Common Issues:**

**Tests timeout:**

- Increase timeout in `playwright.config.ts`
- Check if all services are running
- Check network connectivity

**Element not found:**

- Use `--headed` mode to see what's happening
- Check if selectors changed
- Wait for proper loading states

**Payment tests fail:**

- Verify Stripe test keys are set
- Check webhook endpoint is accessible
- Use Stripe test cards only

**WebSocket tests fail:**

- Ensure Redis is running
- Check CORS settings
- Verify WebSocket port is accessible

---

## 📞 Support & Resources

- **Playwright Docs:** https://playwright.dev/
- **Test Patterns:** See `e2e/examples/` folder
- **Debug Mode:** `npx playwright test --debug`
- **UI Mode:** `npx playwright test --ui`
- **Codegen:** `npx playwright codegen http://localhost:3000`

---

## ✅ Pre-Production Checklist

Before deploying to production:

- [ ] All critical tests passing
- [ ] Payment tests with test Stripe keys
- [ ] WebSocket real-time updates working
- [ ] Email/WhatsApp notifications sending
- [ ] Error handling tested
- [ ] Performance benchmarks met
- [ ] Mobile responsive tests passing
- [ ] Cross-browser tests passing
- [ ] Security tests passing
- [ ] Database rollback tested

After deploying to production:

- [ ] Run production smoke tests
- [ ] Verify real payment processing (small test)
- [ ] Check error monitoring dashboard
- [ ] Verify webhooks receiving events
- [ ] Test real WhatsApp notifications
- [ ] Monitor performance metrics
- [ ] Schedule recurring E2E tests

---

**Last Updated:** November 10, 2025 **Maintained By:** MyHibachi Team
