# ⚡ URGENCY MATRIX - QUICK REFERENCE

**Created:** November 23, 2025
**Total Work:** 280-350 hours (7-9 weeks)
**Current Completion:** 18%

---

## 🔥 URGENCY LEVELS

```
🔴 LEVEL 1: CRITICAL    → DO FIRST  (10 items, 60-75 hours)  - Production blockers
🟠 LEVEL 2: HIGH        → DO NEXT   (8 items, 85-110 hours)  - Business value
🟡 LEVEL 3: MEDIUM      → DO AFTER  (12 items, 95-120 hours) - Nice to have
🟢 LEVEL 4: LOW         → DO LAST   (6 items, 40-45 hours)   - Polish only
```

---

## 🔴 LEVEL 1: CRITICAL (DO FIRST)

**Total Time:** 60-75 hours (1 week)
**Must Complete Before:** Production deployment

| # | Task | Time | Why Critical |
|---|------|------|--------------|
| 1.1 | Fix 4 Production Safety Tests | 4-6 hrs | **Prevents double bookings, payment failures** |
| 1.2 | Fix 257 Python Undefined Names | 8-12 hrs | **App crashes at runtime** |
| 1.3 | Fix 18 Integration Test Failures | 8-12 hrs | **Features broken in production** |
| 1.4 | Rotate API Keys | 30 min | **Keys exposed in git history** |
| 1.5 | Set Up Google Secret Manager | 2 hrs | **Secrets in code/env vars** |
| 1.6 | Fix Backend Deployment Blockers | 2-4 hrs | **Server won't start** |
| 1.7 | Deploy to Staging | 6-8 hrs | **Must test before production** |
| 1.8 | Set Up Production Monitoring | 4 hrs | **Can't detect issues** |
| 1.9 | Run Smoke Tests | 2 hrs | **Validate before go-live** |
| 1.10 | Database Backups & Recovery | 1 hr | **Data loss protection** |

**Start with:** 1.1 (Production Safety Tests) - MOST CRITICAL

---

## 🟠 LEVEL 2: HIGH (DO NEXT)

**Total Time:** 85-110 hours (2-3 weeks)
**Business Impact:** Revenue, retention, sales

| # | Task | Time | Business Value |
|---|------|------|----------------|
| 2.1 | Fix 15 Service Test Failures | 4-6 hrs | Service reliability |
| 2.2 | Fix 185 Python Unused Imports | 2-3 hrs | Code quality |
| 2.3 | Fix 78 Python Import Order | 1-2 hrs | Code quality |
| 2.4 | Fix 39 Customer ESLint Warnings | 1-2 hrs | Type safety |
| 2.5 | Fix Admin ESLint Issues | 1 hr | Code quality |
| 2.6 | **Customer Review System** | **14-20 hrs** | **SEO, content, trust** |
| 2.7 | **Loyalty Program** | **20-28 hrs** | **Customer retention** |
| 2.8 | **Lead Scoring Dashboard** | **11-16 hrs** | **Sales automation** |

**Prioritize:** 2.6, 2.7, 2.8 (customer-facing features)

---

## 🟡 LEVEL 3: MEDIUM (DO AFTER)

**Total Time:** 95-120 hours (2-3 weeks)
**Business Impact:** Cost savings, automation, analytics

| # | Task | Time | Business Value |
|---|------|------|----------------|
| 3.1 | Shadow Learning AI Frontend | 35-40 hrs | 75% cost savings on AI |
| 3.2 | Newsletter Management UI | 20-28 hrs | Save $100/mo on MailChimp |
| 3.3 | Social Media Scheduling UI | 7-10 hrs | Social automation |
| 3.4 | Analytics Dashboard Completion | 10 hrs | Data-driven decisions |
| 3.5 | Smart Re-render & Manual Refresh | 5-7 hrs | Admin UX improvement |
| 3.6 | Station Management UI | 7-10 hrs | Multi-location support |
| 3.7 | Fix Performance Test Failures | 3-4 hrs | Performance tracking |
| 3.8 | Fix 49 Python Boolean Errors | 30 min | Code style |
| 3.9 | Fix Remaining Python Linting | 2-3 hrs | Code quality |

**Prioritize:** 3.1 (AI cost savings), 3.2 (marketing automation)

---

## 🟢 LEVEL 4: LOW (DO LAST)

**Total Time:** 40-45 hours (1 week)
**Business Impact:** Polish, optimization, documentation

| # | Task | Time | Business Value |
|---|------|------|----------------|
| 4.1 | Performance Optimization | 7-14 hrs | Speed improvement |
| 4.2 | SEO Improvements | 5-6 hrs | Organic traffic |
| 4.3 | Accessibility Audit | 14-20 hrs | Inclusivity |
| 4.4 | Delete Redundant CI/CD | 30 min | Cleanup |
| 4.5 | Documentation Updates | 4-6 hrs | Developer onboarding |
| 4.6 | Create E2E Test Suite | 8-12 hrs | Automated testing |

**Prioritize:** 4.1 (performance), 4.2 (SEO)

---

## 📅 RECOMMENDED TIMELINE

### Week 1: CRITICAL BLOCKERS (60-75 hours)

**Goal:** Production deployment ready

```
Day 1-2 (16-20 hrs):
  ✓ Fix production safety tests (4-6 hrs)
  ✓ Fix Python undefined names (8-12 hrs)
  ✓ Rotate API keys (30 min)
  ✓ Set up GSM (2 hrs)

Day 3-5 (20-25 hrs):
  ✓ Fix integration tests (8-12 hrs)
  ✓ Fix deployment blockers (2-4 hrs)
  ✓ Deploy to staging (6-8 hrs)
  ✓ Set up monitoring (4 hrs)

Day 6-7 (8-10 hrs):
  ✓ Run smoke tests (2 hrs)
  ✓ Database backups (1 hr)
  ✓ Fix service tests (4-6 hrs)

RESULT: ✅ PRODUCTION READY
```

---

### Week 2: HIGH PRIORITY FEATURES (40-50 hours)

**Goal:** First major features live

```
Day 8-10 (14-20 hrs):
  ✓ Customer Review System

Day 11-13 (18-22 hrs):
  ✓ Loyalty Program (backend + frontend start)

Day 14 (8-10 hrs):
  ✓ Fix all linting issues
  ✓ Fix service tests

RESULT: ✅ CUSTOMER REVIEW SYSTEM LIVE
```

---

### Week 3: COMPLETE HIGH PRIORITY (45-60 hours)

**Goal:** Loyalty + Lead Scoring operational

```
Day 15-17 (18 hrs):
  ✓ Loyalty Program (frontend completion)

Day 18-20 (11-16 hrs):
  ✓ Lead Scoring Dashboard

Day 21 (16-26 hrs):
  ✓ Shadow Learning AI (start)

RESULT: ✅ LOYALTY PROGRAM + LEAD SCORING LIVE
```

---

### Week 4-5: MEDIUM PRIORITY (95-120 hours)

**Goal:** Admin features complete

```
Week 4:
  ✓ Shadow Learning AI (finish)
  ✓ Newsletter Management UI

Week 5:
  ✓ Social Media Scheduling
  ✓ Analytics Dashboard
  ✓ Smart Re-render
  ✓ Station Management

RESULT: ✅ ALL ADMIN FEATURES COMPLETE
```

---

### Week 6: POLISH (40-45 hours)

**Goal:** Production optimized

```
Day 1-3:
  ✓ Performance optimization
  ✓ SEO improvements
  ✓ Accessibility audit (start)

Day 4-5:
  ✓ Accessibility audit (finish)
  ✓ Documentation
  ✓ E2E tests
  ✓ Cleanup

RESULT: ✅ PRODUCTION OPTIMIZED
```

---

## 🎯 QUICK START GUIDE

### RIGHT NOW (5 minutes)

1. **Choose your path:**

```
[ ] Option A: Production ASAP (1 week, 60-75 hrs)
[ ] Option B: Features First (3 weeks, 145-185 hrs)
[✓] Option C: Hybrid (4 weeks, 145-185 hrs) ← RECOMMENDED
[ ] Option D: Complete (6 weeks, 280-350 hrs)
```

2. **Open terminal and run:**

```bash
cd apps/backend
pytest tests/services/test_production_safety.py -vv --tb=long
```

3. **Fix the 4 failing tests:**

- test_double_booking_prevention (Bug #13)
- test_payment_idempotency
- test_race_condition_handling
- test_data_integrity

---

## 📊 PROGRESS TRACKING

### Setup Kanban Board (Today)

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 🔴 CRITICAL │ 🟠 HIGH     │ 🟡 MEDIUM   │ 🟢 LOW      │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 10 items    │ 8 items     │ 12 items    │ 6 items     │
│ 60-75 hrs   │ 85-110 hrs  │ 95-120 hrs  │ 40-45 hrs   │
│             │             │             │             │
│ MUST DO     │ SHOULD DO   │ NICE TO DO  │ POLISH      │
│ Week 1      │ Week 2-3    │ Week 4-5    │ Week 6      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Daily Tracking

```
End of each day, update:
- [ ] Tasks completed today
- [ ] Hours spent
- [ ] Blockers encountered
- [ ] Next day plan
```

---

## 🚨 CRITICAL RULES

### DO NOT SKIP:

1. ❌ Production safety tests
2. ❌ Python undefined name errors
3. ❌ Integration test failures
4. ❌ API key rotation
5. ❌ GSM setup
6. ❌ Staging deployment
7. ❌ Smoke tests

**Why:** These will cause production failures

---

### CAN DEFER:

1. ✅ Performance optimization
2. ✅ SEO improvements
3. ✅ Accessibility audit
4. ✅ Documentation updates
5. ✅ E2E test suite

**Why:** These improve quality but don't block deployment

---

## 💡 PRO TIPS

### For Fastest Progress:

1. **Work in order:** 🔴 → 🟠 → 🟡 → 🟢
2. **Don't skip critical:** Always finish Level 1 first
3. **Batch similar tasks:** All linting together, all tests together
4. **Use auto-fix:** Let tools fix what they can
5. **Track time:** Know your actual velocity

### For Best Results:

1. **Test after every fix:** Don't accumulate issues
2. **Commit frequently:** Small commits, easy rollback
3. **Document blockers:** Note what slowed you down
4. **Ask for help:** Don't spend hours on one issue
5. **Celebrate wins:** Mark tasks complete, track progress

---

## 📞 WHEN STUCK

### If Tests Won't Pass:

1. Read error message carefully
2. Check test file for examples
3. Run single test: `pytest tests/file.py::test_name -vv`
4. Check database state
5. Verify environment variables

### If Deployment Fails:

1. Check logs: `sudo journalctl -u myhibachi-backend -n 50`
2. Verify environment variables
3. Test database connection
4. Check port availability
5. Verify SSL certificates

### If Feature Breaks:

1. Check browser console
2. Check network tab
3. Verify API response
4. Check backend logs
5. Roll back if needed

---

## ✅ SUCCESS CHECKLIST

### Week 1 (Critical):

- [ ] All 222 tests passing (100%)
- [ ] 0 Python undefined name errors
- [ ] Staging environment live
- [ ] Smoke tests passing
- [ ] Monitoring configured
- [ ] Backups working

### Week 2 (High Priority):

- [ ] Customer Review System live
- [ ] Loyalty Program backend done
- [ ] 0 linting errors (Python + TS)

### Week 3 (High Priority):

- [ ] Loyalty Program frontend live
- [ ] Lead Scoring operational
- [ ] First loyalty reward redeemed

### Week 4 (Medium Priority):

- [ ] Shadow Learning AI complete
- [ ] Newsletter Management live
- [ ] First newsletter sent

### Week 5 (Medium Priority):

- [ ] Social Media Scheduling live
- [ ] Analytics Dashboard complete
- [ ] Station Management ready

### Week 6 (Polish):

- [ ] Performance optimized
- [ ] SEO improved
- [ ] Accessibility compliant
- [ ] Documentation updated

---

## 🏆 FINAL GOAL

**By End of Week 6:**

```
✅ Production deployed and stable
✅ All 36 items complete
✅ 0 critical issues
✅ 14 major features live
✅ Full test coverage
✅ Optimized performance
✅ Professional documentation
✅ Ready to scale
```

---

**NOW:** Start with Priority 1.1 - Fix production safety tests

**QUESTION:** Which option (A/B/C/D) do you want to pursue?
