# My Hibachi - Operational Priority List

**Last Updated**: November 20, 2025  
**Current Branch**: `nuclear-refactor-clean-architecture`  
**Status**: Ready for Staging Deployment ✅

---

## 🎯 Executive Summary

**Current State**:

- ✅ Code corruption fixed (47 malformed async insertions)
- ✅ Comprehensive bug audit complete (0 CRITICAL, 0 HIGH, 0 MEDIUM
  bugs)
- ✅ Enterprise standards implemented
- ✅ Security hardened (no secrets in git)
- ✅ All tests passing (24/24 - 100%)

**Next Milestone**: Deploy to staging environment

---

## 🔴 CRITICAL - Before Staging Deployment (Do First)

### 1. **Rotate Test API Keys** (SECURITY - HIGH PRIORITY)

**Why**: Current test keys are exposed in git history (commits
removed, but still in GitHub's secret scanning)

**Action Items**:

```bash
# 1. Stripe Keys
- Login to Stripe Dashboard → API Keys
- Generate new test secret key
- Generate new test publishable key
- Update in GSM: prod-global-STRIPE_SECRET_KEY
- Update in GSM: prod-frontend-web-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

# 2. OpenAI API Key
- Login to OpenAI Platform → API Keys
- Create new secret key with name "MH-Production-Nov2025"
- Update in GSM: prod-global-OPENAI_API_KEY

# 3. Google Maps API Key
- Login to Google Cloud Console → APIs & Services → Credentials
- Create new API key with name "MH-Production-Nov2025"
- Restrict to:
  - Geocoding API
  - Maps JavaScript API
  - Places API
- Add HTTP referrer restrictions:
  - https://myhibachichef.com/*
  - https://admin.myhibachichef.com/*
- Update in GSM: prod-global-GOOGLE_MAPS_SERVER_KEY
```

**Estimated Time**: 30 minutes  
**Owner**: DevOps/Security Team  
**Verification**: Run `verify_all_secrets.py` after rotation

---

### 2. **Configure Production Environment Variables** (REQUIRED)

**Why**: Staging and production need separate configurations

**Action Items**:

```bash
# Create staging environment file
apps/customer/.env.staging
apps/admin/.env.staging
apps/backend/.env.staging

# Key variables to set:
- NEXT_PUBLIC_API_URL=https://api-staging.myhibachichef.com
- NEXT_PUBLIC_APP_URL=https://staging.myhibachichef.com
- DATABASE_URL=<staging_db_url>
- REDIS_URL=<staging_redis_url>
- STRIPE_SECRET_KEY=<test_key>
- OPENAI_API_KEY=<test_key>
```

**Estimated Time**: 1 hour  
**Owner**: DevOps Team  
**Verification**: Check that `.env.staging` is in `.gitignore`

---

### 3. **Set Up GSM (Google Secret Manager) Integration** (REQUIRED)

**Why**: Production secrets must be managed securely, not in `.env`
files

**Action Items**:

```bash
# 1. Install Google Cloud SDK (if not already installed)
# See: scripts/setup-gcloud.md

# 2. Authenticate with GCP
gcloud auth login
gcloud config set project my-hibachi-crm

# 3. Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# 4. Upload secrets using template
# IMPORTANT: Use scripts/secrets-template.json as guide
# DO NOT commit the filled version to git
# Fill it locally, upload to GSM, then delete

# 5. Test GSM access
bash scripts/test-gsm-access.sh

# 6. Configure backend to use GSM
# See: apps/backend/src/start_with_gsm.py
```

**Estimated Time**: 2 hours  
**Owner**: DevOps Team  
**Dependencies**: Google Cloud Project access  
**Verification**: Run `test_gsm_integration.py`

---

### 4. **Database Migration Review** (REQUIRED)

**Why**: Ensure all schema changes are production-ready

**Action Items**:

```bash
# 1. Review pending migrations
cd apps/backend
alembic history

# 2. Test migrations on staging database
alembic upgrade head

# 3. Verify critical migrations:
- 011_add_audit_logging.py ✅
- 012_add_2fa_ip_verification.py ✅
- 013_add_deposit_deadline.py ✅
- 014_add_sms_consent.py ✅
- 015_add_terms_acknowledgment.py ✅

# 4. Check for race condition fix
- 20250113_fix_booking_race_condition.py ✅
```

**Estimated Time**: 1 hour  
**Owner**: Backend Team  
**Verification**: Run migration tests on staging DB

---

### 5. **Enable Feature Flags for Staging** (REQUIRED)

**Why**: Test new features in staging before production rollout

**Feature Flags to Enable in Staging**:

```typescript
// apps/customer/.env.staging
NEXT_PUBLIC_FEATURE_AI_BOOKING_V3 = true;
NEXT_PUBLIC_FEATURE_SMS_CONSENT = true;
NEXT_PUBLIC_FEATURE_MATH_CAPTCHA = true;
NEXT_PUBLIC_FEATURE_2FA_VERIFICATION = true;

// apps/backend/.env.staging
FEATURE_FLAG_TRAVEL_FEE_V2 = false; // Keep disabled until tested
FEATURE_FLAG_AI_BOOKING_V3 = true;
FEATURE_FLAG_AUDIT_LOGGING = true;
```

**Feature Flags to KEEP DISABLED in Production**:

```typescript
// apps/customer/.env.production
NEXT_PUBLIC_FEATURE_AI_BOOKING_V3 = false; // Enable gradually
NEXT_PUBLIC_FEATURE_SMS_CONSENT = true;
NEXT_PUBLIC_FEATURE_MATH_CAPTCHA = true;

// apps/backend/.env.production
FEATURE_FLAG_TRAVEL_FEE_V2 = false; // Not ready yet
FEATURE_FLAG_AI_BOOKING_V3 = false; // Enable gradually
FEATURE_FLAG_AUDIT_LOGGING = true;
```

**Estimated Time**: 30 minutes  
**Owner**: Product Team  
**Reference**: `.github/FEATURE_FLAGS.md`

---

## 🟠 HIGH PRIORITY - Before Staging Tests

### 6. **Configure Monitoring & Logging** (REQUIRED)

**Why**: Must have visibility into staging environment

**Action Items**:

```bash
# 1. Set up error tracking
- Configure Sentry DSN
- Test error reporting
- Set up alerts for critical errors

# 2. Set up logging
- Configure structured logging
- Set log levels (DEBUG for staging, INFO for production)
- Set up log aggregation (CloudWatch/GCP Logging)

# 3. Set up performance monitoring
- Configure APM (Application Performance Monitoring)
- Set up slow query alerts (>500ms)
- Monitor API response times
```

**Estimated Time**: 2 hours  
**Owner**: DevOps Team  
**Verification**: Trigger test error, verify it appears in monitoring

---

### 7. **Run Integration Tests on Staging** (REQUIRED)

**Why**: Verify all systems work together

**Test Suites to Run**:

```bash
# 1. Backend API Tests
cd apps/backend
pytest tests/ -v --cov

# 2. Booking Service Tests (Critical)
pytest tests/services/test_booking_service_comprehensive.py

# 3. Payment Integration Tests
pytest tests/unit/test_payment_email_parser.py

# 4. AI Booking Tests
python test_ai_booking.py

# 5. Terms Acknowledgment Tests
pytest tests/test_terms_reply_variations.py

# 6. Race Condition Tests
pytest tests/test_race_condition_fix.py
```

**Estimated Time**: 1 hour  
**Owner**: QA Team  
**Success Criteria**: All tests pass (100%)

---

### 8. **Security Audit** (REQUIRED)

**Why**: Ensure production-ready security posture

**Action Items**:

```bash
# 1. Review SECURITY_AUDIT_CRITICAL.md
# Address any open items

# 2. Verify HTTPS enforcement
- Check SSL certificates
- Verify redirects (HTTP → HTTPS)
- Test HSTS headers

# 3. Verify CORS configuration
- Check allowed origins
- Verify credentials handling
- Test preflight requests

# 4. Verify rate limiting
- Test API rate limits
- Verify IP-based throttling
- Test 2FA rate limits

# 5. Verify input validation
- Test SQL injection protection
- Test XSS protection
- Test CSRF protection
```

**Estimated Time**: 2 hours  
**Owner**: Security Team  
**Reference**: `SECURITY_AUDIT_CRITICAL.md`

---

### 9. **Load Testing** (RECOMMENDED)

**Why**: Ensure staging can handle production-like traffic

**Action Items**:

```bash
# 1. Set up load testing tools
- Artillery / k6 / Locust

# 2. Test scenarios:
- 100 concurrent users browsing
- 50 concurrent booking requests
- 20 concurrent AI chat sessions

# 3. Monitor during tests:
- Response times (p50, p95, p99)
- Error rates
- Database connection pool usage
- Memory usage
```

**Estimated Time**: 3 hours  
**Owner**: DevOps/Backend Team  
**Success Criteria**:

- p95 response time < 500ms
- Error rate < 0.1%
- No memory leaks

---

## 🟡 MEDIUM PRIORITY - Before Production

### 10. **Documentation Updates** (REQUIRED)

**Why**: Team needs accurate deployment guides

**Documents to Update**:

```markdown
✅ DEPLOYMENT_GUIDE.md (already updated) ✅
DEPLOYMENT_READY_SUMMARY.md (already updated) ✅ GSM_TESTING_GUIDE.md
(already created) ✅ GSM_ENHANCED_VARIABLES_SETUP_GUIDE.md (already
created)

TODO:

- [ ] Update README.md with staging/production URLs
- [ ] Update API documentation with new endpoints
- [ ] Create runbook for common issues
- [ ] Document rollback procedures
```

**Estimated Time**: 2 hours  
**Owner**: Tech Lead

---

### 11. **Admin Panel Configuration** (REQUIRED)

**Why**: Admin users need production access

**Action Items**:

```bash
# 1. Create admin users in production DB
- Set up initial super admin account
- Configure 2FA for admin accounts
- Set up role-based access control

# 2. Configure admin environment
apps/admin/.env.production:
- NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
- NEXT_PUBLIC_APP_URL=https://admin.myhibachichef.com

# 3. Test admin features:
- Variables management page
- Booking management
- Customer management
- Audit logs
```

**Estimated Time**: 1 hour  
**Owner**: Product Team

---

### 12. **CDN & Caching Setup** (RECOMMENDED)

**Why**: Improve performance and reduce costs

**Action Items**:

```bash
# 1. Configure Vercel Edge Caching
- Set cache headers for static assets
- Configure ISR (Incremental Static Regeneration)
- Set cache TTL policies

# 2. Configure API caching
- Redis caching for frequently accessed data
- Cache invalidation strategies
- Cache warming for critical data

# 3. Configure CDN
- CloudFlare / AWS CloudFront
- Set up cache purging
- Configure cache bypass for admin
```

**Estimated Time**: 2 hours  
**Owner**: DevOps Team

---

### 13. **Backup & Disaster Recovery** (REQUIRED)

**Why**: Protect against data loss

**Action Items**:

```bash
# 1. Database backups
- Configure automated daily backups
- Test restore procedure
- Set retention policy (30 days)

# 2. Code backups
- Verify git repository backups
- Set up GitHub backup (additional remote)

# 3. Secrets backups
- Export GSM secrets to encrypted backup
- Store in secure location (offline)
- Test recovery procedure

# 4. Disaster recovery plan
- Document recovery steps
- Test full system recovery
- Set RTO (Recovery Time Objective): < 4 hours
- Set RPO (Recovery Point Objective): < 1 hour
```

**Estimated Time**: 3 hours  
**Owner**: DevOps Team

---

## 🟢 LOW PRIORITY - Code Quality Improvements

### 14. **Add Missing Type Hints** (529 functions)

**Why**: Improve code maintainability and IDE support

**Findings from Bug Audit**:

```python
# 529 functions missing complete type hints
# Examples:
def process_booking(data):  # ❌ Missing types
    ...

def process_booking(data: dict) -> BookingResult:  # ✅ With types
    ...
```

**Action Items**:

```bash
# 1. Prioritize by criticality:
- Critical business logic functions (booking, payment, pricing)
- Public API functions
- Service layer functions
- Utility functions

# 2. Use automated tools:
mypy --strict apps/backend/src/
ruff check --select ANN apps/backend/src/

# 3. Add type stubs for third-party libraries
```

**Estimated Time**: 8-10 hours (spread over multiple sprints)  
**Owner**: Backend Team  
**Priority**: Can be done incrementally

---

### 15. **Refactor Legacy Code** (DEFERRED)

**Why**: Improve maintainability, but not blocking deployment

**Items Identified**:

```python
# See: apps/backend/LEGACY_ARCHITECTURE_AUDIT_REPORT.md
# See: apps/backend/LEGACY_CONSOLIDATION_PLAN.md

Key legacy items:
- Old notification group system (can be removed after migration)
- Legacy QR tracking (replaced by new system)
- Deprecated AI orchestrator patterns
```

**Estimated Time**: 20+ hours  
**Owner**: Backend Team  
**Priority**: Post-launch cleanup

---

### 16. **Performance Optimizations** (NICE-TO-HAVE)

**Why**: Improve user experience, but not blocking

**Potential Optimizations**:

```bash
# 1. Database query optimization
- Add missing indexes
- Optimize N+1 queries
- Use SELECT FOR UPDATE where needed

# 2. Frontend bundle optimization
- Code splitting
- Lazy loading
- Image optimization

# 3. API response optimization
- Reduce payload sizes
- Add compression
- Optimize JSON serialization
```

**Estimated Time**: 10+ hours  
**Owner**: Full-Stack Team  
**Priority**: Monitor performance first, optimize if needed

---

## 📋 SKIPPED ITEMS - Postponed Features

### 17. **Features Postponed to V2** (DOCUMENTED)

**Why**: Not critical for MVP, can be added post-launch

**Postponed Features**:

```markdown
1. ❌ Travel Fee V2 Calculation (Complex algorithm, needs more
   testing)
   - Status: Code exists, feature flag OFF
   - Timeline: 2-3 weeks after launch
   - Reference: AI_BOOKING_V3_PRODUCTION_SAFETY_UPGRADE.md

2. ❌ Multi-Chef Scheduling (Scaling feature)
   - Status: Not implemented
   - Timeline: Q1 2026
   - Reference: Business requirements not finalized

3. ❌ OneDrive Excel Sync (Admin feature)
   - Status: Prototype exists
   - Timeline: 4-6 weeks after launch
   - Reference: ADMIN_UI_SYNC_DASHBOARD_COMPLETE.md

4. ❌ Advanced AI Analytics (Marketing feature)
   - Status: Framework exists
   - Timeline: Q1 2026
   - Reference: AI_ML_ENHANCEMENT_ANALYSIS.md

5. ❌ Customer Loyalty Program (Business feature)
   - Status: Not started
   - Timeline: Q2 2026
   - Dependency: Business team approval
```

**Documentation**: All postponed features are documented in their
respective files

---

## 🔄 API Key Rotation Plan (Using GSM)

### 18. **Automated Key Rotation Setup** (POST-LAUNCH)

**Why**: Security best practice, but not needed for initial launch

**Implementation Plan**:

```bash
# Phase 1: Manual Rotation (Launch)
- Rotate keys manually using scripts/rotate-secret.sh
- Document rotation procedures
- Set rotation schedule (every 90 days)

# Phase 2: Semi-Automated (Month 2)
- Create rotation scripts
- Set up notifications for expiring keys
- Test rotation without downtime

# Phase 3: Fully Automated (Month 4)
- Implement automatic rotation
- Zero-downtime rotation
- Automatic verification
```

**Estimated Time**: 15 hours (spread over 4 months)  
**Owner**: DevOps/Security Team  
**Priority**: Low (manual rotation is sufficient for now)

---

## 📊 Deployment Checklist Summary

### **Before Staging** (MUST DO - 1-2 days)

- [ ] Rotate test API keys (30 min)
- [ ] Configure environment variables (1 hour)
- [ ] Set up GSM integration (2 hours)
- [ ] Review database migrations (1 hour)
- [ ] Configure feature flags (30 min)
- [ ] Set up monitoring & logging (2 hours)
- [ ] Run integration tests (1 hour)
- [ ] Security audit (2 hours)

**Total Estimated Time**: 10 hours  
**Timeline**: 1-2 business days

---

### **Staging Testing** (SHOULD DO - 2-3 days)

- [ ] Load testing (3 hours)
- [ ] End-to-end testing (4 hours)
- [ ] User acceptance testing (8 hours)
- [ ] Bug fixes from testing (varies)

**Total Estimated Time**: 15-20 hours  
**Timeline**: 2-3 business days

---

### **Before Production** (MUST DO - 1 day)

- [ ] Update documentation (2 hours)
- [ ] Configure admin panel (1 hour)
- [ ] Set up CDN & caching (2 hours)
- [ ] Backup & disaster recovery (3 hours)
- [ ] Final security review (1 hour)
- [ ] Stakeholder sign-off (1 hour)

**Total Estimated Time**: 10 hours  
**Timeline**: 1 business day

---

### **Post-Production** (NICE TO HAVE - Ongoing)

- [ ] Add type hints (10 hours - incremental)
- [ ] Refactor legacy code (20 hours - sprint 2)
- [ ] Performance optimizations (10 hours - as needed)
- [ ] Automated key rotation (15 hours - months 2-4)

**Total Estimated Time**: 55+ hours  
**Timeline**: Ongoing over 3-4 months

---

## 🎯 Final Deployment Timeline

### **Week 1: Staging Deployment**

- Day 1-2: Pre-staging setup (API keys, GSM, environment)
- Day 3-5: Staging deployment + testing
- Day 5: Staging sign-off

### **Week 2: Production Deployment**

- Day 1: Pre-production setup (CDN, backups, docs)
- Day 2: Production deployment
- Day 3-5: Production monitoring + bug fixes

### **Week 3+: Post-Launch**

- Ongoing monitoring
- User feedback collection
- Bug fixes
- Code quality improvements (incremental)

---

## 📞 Escalation & Support

### **Critical Issues** (Production Down)

- Contact: DevOps Team Lead
- Response Time: < 15 minutes
- Escalation: CTO

### **High Priority Issues** (Feature Broken)

- Contact: Engineering Team Lead
- Response Time: < 1 hour
- Escalation: VP Engineering

### **Medium Priority Issues** (Performance)

- Contact: Backend Team
- Response Time: < 4 hours
- Escalation: Engineering Team Lead

### **Low Priority Issues** (Code Quality)

- Contact: Assigned Developer
- Response Time: Next sprint
- Escalation: Team Lead

---

## ✅ Success Criteria

### **Staging Success**

- [ ] All integration tests passing (100%)
- [ ] Security audit passed
- [ ] Load test passed (p95 < 500ms)
- [ ] No critical bugs found

### **Production Success**

- [ ] Zero downtime deployment
- [ ] Error rate < 0.1% (first 24 hours)
- [ ] Response time p95 < 300ms
- [ ] No customer-reported critical bugs (first week)
- [ ] Successful booking completion rate > 95%

---

**Document Version**: 1.0  
**Last Reviewed**: November 20, 2025  
**Next Review**: Before staging deployment  
**Owner**: Engineering Team  
**Approved By**: [Pending]
