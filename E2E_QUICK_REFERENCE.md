# 🚀 E2E Testing - Quick Reference

## Quick Commands

```bash
# Run all tests
npm run test:e2e

# Run with UI
npx playwright test --ui

# Run specific tag
npx playwright test --grep @smoke
npx playwright test --grep @payment
npx playwright test --grep @critical

# Run specific file
npx playwright test e2e/customer/smoke/homepage.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run on specific project
npx playwright test --project=customer
npx playwright test --project=admin

# Generate report
npx playwright show-report

# Production tests
BASE_URL=https://yourdomain.com npx playwright test --config=playwright.prod.config.ts
```

## Using the Helper Script

```powershell
# Windows
.\scripts\run-e2e-tests.ps1

# Linux/Mac
chmod +x scripts/run-e2e-tests.sh
./scripts/run-e2e-tests.sh
```

## Test Tags

- `@smoke` - Quick UI tests (2-5 min)
- `@critical` - Must-pass tests
- `@e2e` - Full end-to-end flows
- `@payment` - Payment processing
- `@booking` - Booking flows
- `@admin` - Admin functionality
- `@realtime` - WebSocket/real-time features
- `@slow` - Long-running tests
- `@performance` - Performance tests
- `@security` - Security tests

## Pre-Production Checklist

```bash
# 1. Start all services
docker-compose up -d

# 2. Run smoke tests
npx playwright test --grep @smoke

# 3. Run critical tests
npx playwright test --grep @critical

# 4. Run full suite
npx playwright test

# 5. Check results
npx playwright show-report
```

## Post-Deployment

```bash
# Test production
BASE_URL=https://yourdomain.com npx playwright test --config=playwright.prod.config.ts --grep "@smoke|@critical"
```

## Debugging

```bash
# Debug mode (step through)
npx playwright test --debug

# Headed mode (see browser)
npx playwright test --headed

# Specific test with debug
npx playwright test e2e/customer/payment/stripe-payment.spec.ts --debug
```

## Common Issues

**Tests timeout:**
- Increase timeout in config
- Check services are running
- Use `--headed` to see what's happening

**Element not found:**
- Use Playwright UI mode to inspect
- Check selectors in code
- Verify page loaded correctly

**Payment tests fail:**
- Check Stripe test keys
- Verify webhook endpoint
- Use Stripe test cards only

## Resources

- Full docs: `e2e/README.md`
- Playwright docs: https://playwright.dev/
- Test helpers: `e2e/helpers/`
