# 🧪 Quality Gates & E2E Testing Standards

This document defines the quality gates that must pass before any code
reaches production.

---

## 📊 Quality Gate Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUALITY GATE PIPELINE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STAGE 1: LOCAL DEVELOPMENT                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  □ Pre-commit hooks run                                             │
│  □ Unit tests pass locally                                          │
│  □ Linting passes (ESLint/Ruff)                                     │
│  □ Type checking passes (TypeScript/mypy)                           │
│                                                                      │
│                          ▼                                           │
│                                                                      │
│  STAGE 2: PULL REQUEST (feature → dev)                              │
│  ─────────────────────────────────────────────────────────────────  │
│  □ CI Unit tests pass (100%)                                        │
│  □ Integration tests pass (95%+)                                    │
│  □ Code review approved (1+ reviewer)                               │
│  □ No security vulnerabilities                                      │
│  □ No console.log/print debug statements                            │
│  □ Documentation updated                                            │
│  □ Feature flags configured                                         │
│                                                                      │
│                          ▼                                           │
│                                                                      │
│  STAGE 3: STAGING (dev branch)                                      │
│  ─────────────────────────────────────────────────────────────────  │
│  □ Auto-deploy to staging succeeds                                  │
│  □ E2E tests pass on staging (90%+)                                 │
│  □ Manual QA testing complete                                       │
│  □ Performance benchmarks met                                       │
│  □ 24-48 hour stability observation                                 │
│                                                                      │
│                          ▼                                           │
│                                                                      │
│  STAGE 4: PRODUCTION (dev → main)                                   │
│  ─────────────────────────────────────────────────────────────────  │
│  □ All staging tests passed                                         │
│  □ Code review approved (2+ reviewers for main)                     │
│  □ Rollback plan documented                                         │
│  □ Feature flags default to OFF                                     │
│  □ Manager sign-off (if required)                                   │
│                                                                      │
│                          ▼                                           │
│                                                                      │
│  STAGE 5: POST-DEPLOYMENT                                           │
│  ─────────────────────────────────────────────────────────────────  │
│  □ Smoke tests pass                                                 │
│  □ Health checks passing                                            │
│  □ Error rate < 1%                                                  │
│  □ 48-72 hour monitoring period                                     │
│  □ Feature flags enabled gradually                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 E2E Test Categories

### API E2E Tests (`e2e/api/`)

| Test Suite        | Critical Path | Timeout | Retry |
| ----------------- | ------------- | ------- | ----- |
| `auth.spec.ts`    | Yes           | 30s     | 2     |
| `booking.spec.ts` | Yes           | 60s     | 2     |
| `quote.spec.ts`   | Yes           | 30s     | 2     |
| `payment.spec.ts` | Yes           | 60s     | 1     |
| `health.spec.ts`  | Yes           | 10s     | 3     |
| `ai-chat.spec.ts` | No            | 120s    | 1     |

### Customer Site E2E Tests (`e2e/customer/`)

| Test Suite                 | Critical Path | Timeout | Retry |
| -------------------------- | ------------- | ------- | ----- |
| `homepage.spec.ts`         | Yes           | 30s     | 2     |
| `booking-flow.spec.ts`     | Yes           | 120s    | 2     |
| `quote-calculator.spec.ts` | Yes           | 60s     | 2     |
| `review-flow.spec.ts`      | Yes           | 60s     | 2     |

### Admin Panel E2E Tests (`e2e/admin/`)

| Test Suite                   | Critical Path | Timeout | Retry |
| ---------------------------- | ------------- | ------- | ----- |
| `login.spec.ts`              | Yes           | 30s     | 2     |
| `dashboard.spec.ts`          | No            | 60s     | 2     |
| `booking-management.spec.ts` | Yes           | 90s     | 2     |

---

## ⚡ Performance Benchmarks

### API Response Times (P95)

| Endpoint Category      | Target  | Alert   | Critical |
| ---------------------- | ------- | ------- | -------- |
| Health checks          | < 50ms  | > 100ms | > 200ms  |
| Auth endpoints         | < 200ms | > 500ms | > 1s     |
| Quote calculation      | < 300ms | > 600ms | > 1s     |
| Booking CRUD           | < 200ms | > 500ms | > 1s     |
| AI Chat                | < 3s    | > 5s    | > 10s    |
| List endpoints (paged) | < 500ms | > 1s    | > 2s     |

### Frontend Performance (Lighthouse)

| Metric                   | Target | Minimum |
| ------------------------ | ------ | ------- |
| Performance Score        | > 90   | > 70    |
| First Contentful Paint   | < 1.5s | < 2.5s  |
| Largest Contentful Paint | < 2.5s | < 4s    |
| Time to Interactive      | < 3s   | < 5s    |
| Cumulative Layout Shift  | < 0.1  | < 0.25  |

---

## 🔴 Blocking vs Non-Blocking Tests

### Blocking (Must Pass to Merge)

```
✓ Unit tests (100% pass rate)
✓ Critical path E2E tests
✓ Security scans (no critical/high)
✓ Type checking
✓ Linting
```

### Non-Blocking (Warn but Allow Merge)

```
⚠ Integration tests (95%+ pass rate)
⚠ Performance benchmarks
⚠ Non-critical E2E tests
⚠ Accessibility checks
```

---

## 📋 Pre-Merge Checklist Template

Copy this checklist into your PR description:

```markdown
## Quality Gate Checklist

### Code Quality

- [ ] No console.log/print debug statements
- [ ] No TODO/FIXME left unaddressed
- [ ] No commented-out code
- [ ] Type hints complete (Python) / Types defined (TypeScript)
- [ ] Error handling implemented

### Testing

- [ ] Unit tests added/updated
- [ ] All unit tests passing
- [ ] Integration tests added (if applicable)
- [ ] E2E tests added (if new user flow)

### Security

- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified (frontend)

### Feature Flags

- [ ] New feature behind flag (if applicable)
- [ ] Flag defaults to OFF in production
- [ ] Flag documented in registry

### Documentation

- [ ] Code comments added
- [ ] API documentation updated (if endpoints changed)
- [ ] README updated (if setup changed)
```

---

## 🚨 Test Failure Response Protocol

### Critical Test Failure (Blocking)

1. **Do NOT merge** the PR
2. Review test failure logs
3. Fix the issue in the same PR
4. Re-run tests
5. Only merge when all pass

### Flaky Test Identified

1. Mark test as `@flaky` or skip temporarily
2. Create issue to fix flaky test
3. Investigate root cause within 48 hours
4. Either fix or remove the test

### False Positive/Negative

1. Review test logic
2. If false positive: fix test assertion
3. If false negative: add missing test case
4. Document the issue for future reference

---

## 📊 Test Coverage Requirements

### Backend (Python)

| Category          | Target | Minimum |
| ----------------- | ------ | ------- |
| Overall           | 80%    | 70%     |
| Critical services | 90%    | 80%     |
| API endpoints     | 85%    | 75%     |
| Models/schemas    | 70%    | 60%     |

### Frontend (TypeScript)

| Category        | Target | Minimum |
| --------------- | ------ | ------- |
| Overall         | 70%    | 60%     |
| Components      | 80%    | 70%     |
| Hooks/utilities | 90%    | 80%     |
| API clients     | 85%    | 75%     |

---

**Document Status:** Active **Last Updated:** December 6, 2025
**Enforcement:** CI/CD Pipeline
