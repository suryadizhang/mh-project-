# 🎯 My Hibachi - Current Batch Status

**Last Updated:** December 27, 2025 **Purpose:** Single source of truth
for current batch status

---

## 📊 ACTIVE BATCH

| Field       | Value                                 |
| ----------- | ------------------------------------- |
| **Batch**   | **BATCH 1.x**                         |
| **Name**    | Core Booking Engine + Security + SSoT |
| **Status**  | 🔄 SSoT IMPLEMENTATION                |
| **Branch**  | `feature/batch-1-core-infrastructure` |
| **Started** | December 7, 2025                      |
| **ETA**     | January 10, 2026                      |

---

## 🔐 SSoT DECISIONS (December 27, 2025)

**SINGLE SOURCE OF TRUTH - User decisions for implementation**

| Decision | Choice | Impact | Batch |
|----------|--------|--------|-------|
| **AI Fallback Behavior** | B) Collect info first, THEN escalate | Better UX, graceful degradation | 1.x |
| **Akaunting Structure** | Separate company per station | Multi-station tax compliance | 2 |
| **Newsletter Template Editor** | A) Simple markdown editor | Faster development | 3-4 |
| **Chef Payroll** | A) Akaunting vendors | Leverage existing system | 2 |
| **FAQ Edit Permissions** | C) Customer Support can suggest (approval required) | Quality control | 1.x |

**Full Implementation Plan:** [SSOT_IMPLEMENTATION_PLAN.md](./docs/04-DEPLOYMENT/SSOT_IMPLEMENTATION_PLAN.md)

---

## 🛡️ LEGAL PROTECTION DECISIONS (December 27, 2025)

**FOOD SAFETY & LIABILITY PROTECTION - User decisions for implementation**

| Decision | Choice | Batch |
|----------|--------|-------|
| **Digital Signature** | D1) Hybrid SignaturePad + timestamp + email PDF (7yr retention) | 1.x |
| **Allergen System** | D1) Required + SMS confirmation (all booking channels) | 1.x |
| **Chef Dashboard** | C1) GCal sync + Web dashboard (supplies, menu, checklist) | 2-3 |
| **Claim Policy** | E1) Enhanced policy + pre-event health notice | 1.x |
| **Photo Documentation** | Manual uploads + thermometer photos (required at 4 checkpoints) | 2-3 |
| **Third-Party Disclaimer** | Include in Terms of Service | 1.x |
| **Chef Certification** | Database tracking + expiration alerts (block if expired) | 2 |
| **Incident Response** | Full investigation workflow | 3-4 |
| **Chef Health Attestation** | Required before each event (48hr symptom check) | 2-3 |

**Full Implementation Plan:** [LEGAL_PROTECTION_IMPLEMENTATION.md](./docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md)

### Legal Protection Implementation Phases

| Phase | Focus | Priority | Batch | Status |
|-------|-------|----------|-------|--------|
| 1.1 | Digital Agreement System (SignaturePad + PDF) | 🔴 CRITICAL | 1.x | ⏳ PENDING |
| 1.2 | Allergen Disclosure System | 🔴 CRITICAL | 1.x | ⏳ PENDING |
| 1.3 | Terms of Service Updates (liability, claims) | 🔴 CRITICAL | 1.x | ⏳ PENDING |
| 2.1 | Chef Certification Tracking | 🟠 HIGH | 2 | ⏳ PENDING |
| 2.2 | Chef Event Dashboard + GCal | 🟠 HIGH | 2-3 | ⏳ PENDING |
| 2.3 | Photo Documentation System | 🟠 HIGH | 2-3 | ⏳ PENDING |
| 3.1 | Incident Response System | 🟡 MEDIUM | 3-4 | ⏳ PENDING |
| 3.2 | Chef Health Attestation | 🟡 MEDIUM | 3-4 | ⏳ PENDING |

### Key Legal Points

- **Record Retention:** 7 YEARS for all signed agreements
- **Digital Signature Validity:** ESIGN Act + UETA compliant
- **Claim Window:** 72 hours to report, 3+ guests required
- **Pre-Event Health Notice:** 24hr before event (SMS/Email)

**Spec File:** [20-SINGLE_SOURCE_OF_TRUTH.instructions.md](./.github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md)

### SSoT Implementation Phases (Batch 1.x)

| Phase | Focus | Priority | Est. Hours | Status |
|-------|-------|----------|------------|--------|
| 1 | AI Critical Fixes (remove hardcoded PRICING) | 🔴 CRITICAL | 4-6 hrs | ⏳ PENDING |
| 2 | Legal Documents Template System | 🔴 CRITICAL | 3-4 hrs | ⏳ PENDING |
| 3 | Digital Agreement + Allergen System | 🔴 CRITICAL | 12-16 hrs | ⏳ PENDING |
| 4 | Terms of Service Updates (liability) | 🔴 CRITICAL | 2-3 hrs | ⏳ PENDING |
| 5 | FAQ System with Approval Workflow | 🟠 HIGH | 4-6 hrs | ⏳ PENDING |
| 6 | UI Text Centralization | 🟠 HIGH | 2-3 hrs | ⏳ PENDING |
| 7 | Akaunting Install & Setup (No wiring yet) | 🟡 MEDIUM | 2-3 hrs | ⏳ PENDING |
| 8 | Akaunting Integration (Wiring) | 🟡 MEDIUM | 8-10 hrs | Batch 2 |
| 9 | Newsletter System | 🟢 LOWER | 6-8 hrs | Batch 3-4 |

---

## 🧠 KEY STRATEGIC DECISIONS (December 21, 2025)

**⚠️ IMPORTANT: These decisions apply to future batches. Don't forget!**

| Decision | Details | Impact |
|----------|---------|--------|
| **3-Model LLM Strategy** | GPT-4o + Claude 3.5 + Mistral (NO GROK) | Batch 3, 6 |
| **$300/mo Threshold** | Rent GPU only when API costs > $300/mo | Batch 6 |
| **Laptop Fine-Tuning** | Phi-4 14B, Qwen3 8B, DeepSeek 7B fit on laptop | Batch 6 |
| **Shadow Learning** | Collect 50K pairs from API LLMs before training | Batch 3-6 |
| **Free-Tier Training** | Use Kaggle (30hrs/wk), Colab before renting GPU | Batch 6 |

### API Keys Needed (Batch 3):
```
OPENAI_API_KEY=xxx       # Tier 1 - Complex reasoning
ANTHROPIC_API_KEY=xxx    # Tier 2 - Empathy, brand voice
MISTRAL_API_KEY=xxx      # Tier 3 - Cost-effective, FAQ
```

---

## ✅ Batch 1 Progress

### Phase 1.1: Backend Core (COMPLETED ✅)

- [x] Customer CRUD (~20 routes)
- [x] Chef CRUD (~15 routes)
- [x] Booking CRUD (~30 routes)
- [x] Quote/Pricing (~15 routes)
- [x] Calendar/Scheduling (~10 routes)
- [x] Authentication (JWT + API keys)
- [x] Health endpoints (~5 routes)
- [x] 4-Tier RBAC System
- [x] Audit Trail System

### Phase 1.2: Security Infrastructure (PENDING DEVOPS 🔧)

**Requires:** Server access (VPS/Plesk) and Cloudflare dashboard

| Task | Time | Priority | Instructions |
|------|------|----------|--------------|
| Cloudflare Tunnel | 2 hrs | HIGH | `cloudflared tunnel create myhibachi` → Configure `/etc/cloudflared/config.yml` |
| Cloudflare Access | 2 hrs | HIGH | Cloudflare dashboard → Access → Applications → Add myhibachi-admin |
| WAF Rules | 3 hrs | MEDIUM | Cloudflare → Security → WAF → Enable OWASP ruleset |
| Admin Protection | 2 hrs | HIGH | Access policy: Require email in @myhibachi.com |
| SSL Full Strict | 1 hr | HIGH | Cloudflare → SSL/TLS → Full (strict) mode |

**Cloudflare Tunnel Quick Start:**
```bash
# On VPS server:
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
cloudflared tunnel login
cloudflared tunnel create myhibachi
cloudflared tunnel route dns myhibachi api.myhibachi.com
# Create /etc/cloudflared/config.yml with tunnel config
sudo cloudflared service install
```

### Phase 1.3: Scaling Measurement (COMPLETED ✅)

- [x] Scaling Metrics API endpoint - /api/v1/health/detailed
- [x] Database Pool Metrics - Included in health check
- [x] Redis Metrics Collector - Included in health check
- [x] Scaling Health Dashboard - Admin panel at /superadmin/scaling
- [ ] WhatsApp Alert Service (2 hrs) - Batch 4 feature
- [ ] Cron Job (5-min check) - Can use external monitoring

### Phase 1.4: Frontend Fixes (COMPLETED ✅)

- [x] ProtectedPhone component (1 hr)
- [x] ProtectedPaymentEmail component
- [x] Remove hardcoded phone/email from 13+ files (1.5 hrs)
- [x] ESLint root config for monorepo lint-staged
- [x] Dynamic pricing audit - fix incorrect prices in JSON/AI files
- [x] Dynamic pricing templates for FAQ/policy content (single source
      of truth)
- [x] Remove Yelp from Footer (15 min)
- [x] RBAC UI in Admin Panel (6 hrs) - Already exists in
      superadmin/roles and superadmin/users
- [x] Audit Log Viewer (4 hrs) - Enhanced /logs page with API
      integration
- [x] Scaling Health Dashboard (4 hrs)

### Phase 1.5: Performance (COMPLETED ✅)

- [x] N+1 Query Prevention (lead_service.py)
- [x] Redis caching for business_config_service.py (15min TTL)
- [x] Redis caching for knowledge_service.py (30min TTL)
- [x] Cache invalidation helpers
- [x] Lazy DatePicker wrapper component (2 hrs)
- [x] API Caching Headers (2 hrs) - CachingMiddleware with ETag
      support
- [x] Client-Side Data Caching (4 hrs) - React Query already
      configured
- [x] Response Compression (1 hr) - GZip middleware

### Phase 1.6: UI/UX Polish (COMPLETED ✅)

- [x] Global Skeleton Loaders (4 hrs)
- [x] Error Boundary System (already exists)
- [x] Toast Notification System (sonner) (3 hrs)
- [x] Form Auto-Save (4 hrs) - useAutoSave hook
- [x] Accessibility Audit (6 hrs) - ARIA labels, semantic HTML

### Phase 1.7: Database Migrations (READY TO DEPLOY 📦)

**Combined migration file:** `/database/migrations/BATCH_1_COMBINED_MIGRATION.sql`

**Deployment steps:**
```bash
# 1. Take backup
pg_dump myhibachi_staging > backup_$(date +%Y%m%d_%H%M).sql

# 2. Run on STAGING first
psql -h <staging-host> -U <user> -d myhibachi_staging -f database/migrations/BATCH_1_COMBINED_MIGRATION.sql

# 3. Verify tables created (check verification output)
# 4. Test application on staging for 24-48 hours
# 5. Then run on PRODUCTION with same steps
```

**What gets created:**
- [x] error_logs table - Admin dashboard error tracking
- [x] MFA columns (identity.users) - WebAuthn + PIN authentication
- [x] security.security_events - Security event logging
- [x] security.admin_alerts - Admin alert notifications
- [x] Performance indexes - bookings, customers, payments
- [x] ai.conversations - AI conversation tracking (Batch 3 foundation)
- [x] ai.messages - AI message storage
- [x] ai.feedback - AI feedback/ratings

**Rollback:** Restore from backup taken before migration

### Phase 1.8: Testing & QA (VALIDATED ✅)

### Phase 1.9: Lead Funnel Tracking (COMPLETED ✅)

- [x] Lead Events API endpoint (POST /api/v1/leads/{id}/events)
- [x] Frontend integration (submitLeadEvent function using apiFetch)
- [x] Quote → Availability → Booking funnel events
- [x] Lead.add_event() method on model for event sourcing

### Phase 1.10: Performance Budget Validation (VALIDATED ✅)

Bundle sizes validated (December 16, 2025):

| Page | Budget | Actual | Status |
|------|--------|--------|--------|
| Homepage `/` | <150KB | 120KB | ✅ PASS |
| BookUs `/BookUs` | <180KB | 158KB | ✅ PASS |
| Blog `/blog` | <140KB | 122KB | ✅ PASS |
| Quote `/quote` | <130KB | 143KB | ⚠️ 13KB over |
| Shared Chunks | <100KB | 103KB | ⚠️ 3KB over |

Overall: **ACCEPTABLE** - Minor overages don't block deployment

Test coverage:

- [x] 208 unit tests passing (customer app)
- [x] All builds pass (admin, customer, backend)
- [ ] Lighthouse audit >90 - See instructions below

**Lighthouse Audit Instructions:**
```
1. Open Chrome DevTools (F12)
2. Go to "Lighthouse" tab
3. Select: Performance, Accessibility, Best Practices, SEO
4. Device: Mobile
5. Run on these pages:
   - https://myhibachi.com/ (Homepage)
   - https://myhibachi.com/BookUs (Booking)
   - https://myhibachi.com/quote (Quote)
6. Target scores: All >90
7. Save reports to /docs/05-OPERATIONS/lighthouse/
```

---

## 🚦 Batch Status Overview

| Batch | Name                    | Status         | Branch                              |
| ----- | ----------------------- | -------------- | ----------------------------------- |
| **0** | Repo Cleanup            | ✅ COMPLETE    | main, dev                           |
| **1** | Core Booking + Security | ✅ CODE COMPLETE | feature/batch-1-core-infrastructure |
| **1.x** | SSoT Implementation   | 🔄 IN PROGRESS | feature/batch-1-core-infrastructure |
| 2     | Payment + Akaunting     | ⏳ Pending     | feature/batch-2-\*                  |
| 3     | Core AI                 | ⏳ Pending     | feature/batch-3-\*                  |
| 4     | Communications          | ⏳ Pending     | feature/batch-4-\*                  |
| 5     | Advanced AI + Marketing | ⏳ Pending     | feature/batch-5-\*                  |
| 6     | AI Training & Scaling   | ⏳ Pending     | feature/batch-6-\*                  |

2. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass

---

## 🎯 Current Scope

### ✅ COMPLETED (Batch 0):

- Git repository cleanup
- Instruction file restructuring
- Branch strategy setup
- Documentation organization
- Removing temp/backup files

### ❌ OUT OF SCOPE (Batch 0):

- New features
- Code changes (except cleanup)
- Database migrations
- API changes
- UI changes

---

## 📋 Next Batch Preview

**Batch 1: Core Booking + Security**

- Core booking CRUD
- Authentication (JWT + API keys)
- 4-tier RBAC system
- Audit trail
- Cloudflare security
- Scaling measurement

**Prerequisite:** Batch 0 complete, main branch updated

---

## 🔗 Related Docs

- `.github/instructions/04-BATCH_DEPLOYMENT.instructions.md` - Batch
  rules
- `docs/04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md` - Full batch plan
- `docs/04-DEPLOYMENT/batches/` - Per-batch details

---

## 📝 Update Instructions

When batch status changes:

1. Update **ACTIVE BATCH** section
2. Update **Progress** checkboxes
3. Update **Batch Status Overview** table
4. Update **Last Updated** date
5. Commit: `docs: update batch status to Batch X`
