# 📚 My Hibachi Documentation Management Plan

**Created:** December 5, 2025 **Purpose:** Consolidate, organize, and
streamline 129 documentation files for easy onboarding and maintenance

---

## 🎯 Goals

1. **Fast Onboarding** - New team member productive in <1 day
2. **Single Source of Truth** - No duplicate/conflicting information
3. **Easy Navigation** - Find any info in <30 seconds
4. **Maintainability** - Update one place, not many

---

## 📊 Current State Analysis

### Total Files: 129 Markdown Files

| Location          | Count | Purpose                |
| ----------------- | ----- | ---------------------- |
| `/docs/`          | 45    | Main documentation     |
| `/apps/customer/` | 18    | Customer site-specific |
| `/apps/backend/`  | 15    | Backend-specific       |
| `/` (root)        | 12    | General/mixed          |
| `/archives/`      | 39+   | Old reports, summaries |

### Problems Identified

1. **Duplicate Content** - Same info in 3-4 places
2. **Orphaned Files** - Old docs never deleted
3. **Unclear Hierarchy** - Where does X doc go?
4. **No Index** - Hard to find specific topics
5. **Mixed Concerns** - Setup + Features + Deployment all mixed

---

## 🏗️ Proposed New Structure

```
docs/
├── README.md                          # Master index (START HERE)
├── 00-ONBOARDING/                     # New team member reads first
│   ├── QUICK_START.md                 # Get running in 30 min
│   ├── ARCHITECTURE_OVERVIEW.md       # High-level system design
│   └── TEAM_CONVENTIONS.md            # Code style, PR process
│
├── 01-ARCHITECTURE/                   # Technical deep dives
│   ├── BACKEND.md                     # FastAPI, database, services
│   ├── FRONTEND.md                    # Next.js, components, state
│   ├── AI_SYSTEM.md                   # Agents, RAG, training
│   └── DATABASE.md                    # Schema, migrations, indexes
│
├── 02-FEATURES/                       # Feature specifications
│   ├── BOOKING_SYSTEM.md              # Core booking flow
│   ├── PAYMENT_SYSTEM.md              # Stripe, tipping, tax
│   ├── AI_CHAT.md                     # Chat widget, escalation
│   ├── COMMUNICATIONS.md              # SMS, Voice, WhatsApp
│   ├── REVIEWS_LOYALTY.md             # Customer reviews, points
│   └── ADMIN_PANEL.md                 # Admin features
│
├── 03-API/                            # API documentation
│   ├── API_REFERENCE.md               # All endpoints
│   ├── AUTHENTICATION.md              # JWT, API keys
│   └── WEBHOOKS.md                    # Stripe, RingCentral, Meta
│
├── 04-DEPLOYMENT/                     # Deployment guides
│   ├── DEPLOYMENT_BATCH_STRATEGY.md   # 6-batch plan (MASTER)
│   ├── BATCH_CHECKLISTS.md            # Per-batch checklists
│   ├── CI_CD.md                       # GitHub Actions, Vercel
│   ├── VPS_SETUP.md                   # Plesk, Cloudflare
│   └── ENV_VARIABLES.md               # All env vars
│
├── 05-OPERATIONS/                     # Running in production
│   ├── MONITORING.md                  # Alerts, dashboards
│   ├── TROUBLESHOOTING.md             # Common issues
│   └── RUNBOOK.md                     # Emergency procedures
│
└── 06-INTEGRATIONS/                   # Third-party setup
    ├── STRIPE.md                      # Payment integration
    ├── RINGCENTRAL.md                 # Voice/SMS
    ├── GOOGLE.md                      # Analytics, Calendar, Ads
    └── META.md                        # WhatsApp, Facebook, IG
```

---

## 🔄 Consolidation Plan

### Phase 1: Immediate Deletions (Archive)

Move to `/archives/deprecated-docs/`:

| File                                  | Reason                     |
| ------------------------------------- | -------------------------- |
| `2K_PROBLEMS_FIXED_SUMMARY.md`        | Historical, not actionable |
| `BUG_COUNT_SUMMARY.md`                | Historical                 |
| `COMMIT_READY.md`                     | One-time use               |
| `CORRUPTION_*.md`                     | Historical                 |
| `ESLINT_FIXES_COMPLETE.md`            | One-time use               |
| `FINAL_CLEANUP_*.md`                  | Historical                 |
| All files in `/archives/old-reports/` | Already archived           |

### Phase 2: Consolidate Duplicates

| Keep                                              | Delete/Merge                     |
| ------------------------------------------------- | -------------------------------- |
| `docs/04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md` | ← Merge all deployment plans     |
| `docs/CONSOLIDATED_MASTER_ROADMAP.md`             | ← Single roadmap file            |
| `docs/01-ARCHITECTURE/ARCHITECTURE.md`            | ← Merge backend ARCHITECTURE.md  |
| `docs/06-INTEGRATIONS/STRIPE.md`                  | ← Merge `STRIPE_*.md` files      |
| `docs/06-INTEGRATIONS/RINGCENTRAL.md`             | ← Merge `RINGCENTRAL_*.md` files |

### Phase 3: Create Missing Docs

| New File                             | Content Source                |
| ------------------------------------ | ----------------------------- |
| `docs/00-ONBOARDING/QUICK_START.md`  | Extract from scattered guides |
| `docs/README.md`                     | Master index with links       |
| `docs/02-FEATURES/PAYMENT_SYSTEM.md` | Consolidate 5+ payment docs   |

---

## 📋 File-by-File Decisions

### Root Level (/) - 12 Files

| File                                    | Decision | Action                                |
| --------------------------------------- | -------- | ------------------------------------- |
| `README.md`                             | ✅ Keep  | Main project readme                   |
| `ONBOARDING.md`                         | 📦 Move  | → `docs/00-ONBOARDING/`               |
| `LOCAL_DEVELOPMENT_GUIDE.md`            | 📦 Move  | → `docs/00-ONBOARDING/`               |
| `QUICK_START_EXISTING_ENV.md`           | 🔀 Merge | → `docs/00-ONBOARDING/QUICK_START.md` |
| `DEPLOYMENT_GUIDE.md`                   | 🔀 Merge | → `docs/04-DEPLOYMENT/`               |
| `VPS_DEPLOYMENT_GUIDE.md`               | 🔀 Merge | → `docs/04-DEPLOYMENT/VPS_SETUP.md`   |
| `GSM_ENHANCED_VARIABLES_SETUP_GUIDE.md` | 📦 Move  | → `docs/04-DEPLOYMENT/`               |

### docs/03-FEATURES/ - 14 Files

| File                                   | Decision | Action                           |
| -------------------------------------- | -------- | -------------------------------- |
| `CALENDAR_QUICK_START.md`              | 🔀 Merge | → `BOOKING_SYSTEM.md`            |
| `CUSTOMER_REVIEW_BLOG_SYSTEM.md`       | 🔀 Merge | → `REVIEWS_LOYALTY.md`           |
| `CUSTOMER_REVIEW_NEWSFEED.md`          | 🔀 Merge | → `REVIEWS_LOYALTY.md`           |
| `QUICK_START_CUSTOMER_REVIEWS.md`      | 🔀 Merge | → `REVIEWS_LOYALTY.md`           |
| `DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md` | 🔀 Merge | → `PAYMENT_SYSTEM.md`            |
| `PAYMENT_OPTIONS_GUIDE.md`             | 🔀 Merge | → `PAYMENT_SYSTEM.md`            |
| `LOYALTY_PROGRAM_EXPLANATION.md`       | 🔀 Merge | → `REVIEWS_LOYALTY.md`           |
| `SMART_AI_ESCALATION_SYSTEM.md`        | 🔀 Merge | → `AI_CHAT.md`                   |
| `FAILED_BOOKING_LEAD_CAPTURE.md`       | 🔀 Merge | → `BOOKING_SYSTEM.md`            |
| `EMAIL_SERVICE_SETUP_GUIDE.md`         | 📦 Move  | → `docs/06-INTEGRATIONS/`        |
| `WHATSAPP_BUSINESS_API_SETUP_GUIDE.md` | 📦 Move  | → `docs/06-INTEGRATIONS/META.md` |
| `NOTIFICATION_GROUPS_*.md`             | 🔀 Merge | → `COMMUNICATIONS.md`            |
| `ENTERPRISE_FEATURES_ROADMAP.md`       | ✅ Keep  | Reference for batch strategy     |

### docs/04-DEPLOYMENT/ - 14 Files

| File                                  | Decision | Action                      |
| ------------------------------------- | -------- | --------------------------- |
| `DEPLOYMENT_BATCH_STRATEGY.md`        | ✅ Keep  | **MASTER deployment doc**   |
| `BATCH_CHECKLISTS.md`                 | ✅ Keep  | Per-batch tasks             |
| `CI_CD_STRATEGY.md`                   | 🔀 Merge | → `CI_CD.md`                |
| `DATABASE_SETUP_GUIDE.md`             | ✅ Keep  | Standalone guide            |
| `CLOUDFLARE_TUNNEL_GUIDE.md`          | 🔀 Merge | → `VPS_SETUP.md`            |
| `PLESK_DEPLOYMENT_SETUP_GUIDE.md`     | 🔀 Merge | → `VPS_SETUP.md`            |
| `ENV_*.md` (4 files)                  | 🔀 Merge | → `ENV_VARIABLES.md`        |
| `PRODUCTION_*.md` (3 files)           | 🔀 Merge | → `docs/05-OPERATIONS/`     |
| `WEBHOOK_CONFIGURATION_PRODUCTION.md` | 📦 Move  | → `docs/03-API/WEBHOOKS.md` |

### apps/customer/ - 18 Files

| File                                   | Decision   | Action                                 |
| -------------------------------------- | ---------- | -------------------------------------- |
| `README.md`                            | ✅ Keep    | App-specific readme                    |
| `PAYMENT_SYSTEM_DOCUMENTATION.md`      | 🔀 Merge   | → `docs/02-FEATURES/PAYMENT_SYSTEM.md` |
| `STRIPE_*.md` (4 files)                | 🔀 Merge   | → `docs/06-INTEGRATIONS/STRIPE.md`     |
| `GA4_SEARCH_CONSOLE_COMPLETE_GUIDE.md` | 📦 Move    | → `docs/06-INTEGRATIONS/GOOGLE.md`     |
| `FACEBOOK_MESSENGER_SETUP_GUIDE.md`    | 📦 Move    | → `docs/06-INTEGRATIONS/META.md`       |
| `BOOKING_SYSTEM_README.md`             | 🔀 Merge   | → `docs/02-FEATURES/BOOKING_SYSTEM.md` |
| `GO_LIVE_CHECKLIST.md`                 | 📦 Archive | One-time use                           |
| `CSS_CONFLICTS_FIX_PLAN.md`            | 📦 Archive | Historical                             |
| `SEO_*.md`, `LOCATION_*.md`            | 📦 Archive | SEO reference                          |

### apps/backend/ - 15 Files

| File                     | Decision | Action                               |
| ------------------------ | -------- | ------------------------------------ |
| `README.md`              | ✅ Keep  | App-specific readme                  |
| `ARCHITECTURE.md`        | 🔀 Merge | → `docs/01-ARCHITECTURE/BACKEND.md`  |
| `STRIPE_INTEGRATION.md`  | 🔀 Merge | → `docs/06-INTEGRATIONS/STRIPE.md`   |
| `DATABASE_MIGRATIONS.md` | 📦 Move  | → `docs/01-ARCHITECTURE/DATABASE.md` |
| `docs/PHASE_2_*.md`      | ✅ Keep  | RingCentral reference                |
| `HEALTH_CHECKS.md`       | 📦 Move  | → `docs/05-OPERATIONS/MONITORING.md` |
| `*_GUIDE.md`             | 🔀 Merge | Into appropriate docs                |

---

## 📝 Master Index Template (docs/README.md)

```markdown
# 📚 My Hibachi Documentation

> **New Here?** Start with
> [Quick Start Guide](./00-ONBOARDING/QUICK_START.md)

## 🚀 Getting Started

- [Quick Start](./00-ONBOARDING/QUICK_START.md) - Running in 30
  minutes
- [Architecture Overview](./00-ONBOARDING/ARCHITECTURE_OVERVIEW.md)
- [Team Conventions](./00-ONBOARDING/TEAM_CONVENTIONS.md)

## 🏗️ Architecture

- [Backend (FastAPI)](./01-ARCHITECTURE/BACKEND.md)
- [Frontend (Next.js)](./01-ARCHITECTURE/FRONTEND.md)
- [AI System](./01-ARCHITECTURE/AI_SYSTEM.md)
- [Database](./01-ARCHITECTURE/DATABASE.md)

## ✨ Features

- [Booking System](./02-FEATURES/BOOKING_SYSTEM.md)
- [Payment System](./02-FEATURES/PAYMENT_SYSTEM.md) - Stripe, tipping,
  tax
- [AI Chat](./02-FEATURES/AI_CHAT.md)
- [Communications](./02-FEATURES/COMMUNICATIONS.md)
- [Reviews & Loyalty](./02-FEATURES/REVIEWS_LOYALTY.md)
- [Admin Panel](./02-FEATURES/ADMIN_PANEL.md)

## 🔌 API

- [API Reference](./03-API/API_REFERENCE.md)
- [Authentication](./03-API/AUTHENTICATION.md)
- [Webhooks](./03-API/WEBHOOKS.md)

## 🚢 Deployment

- [**Batch Strategy (MASTER)**](./04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md)
- [Batch Checklists](./04-DEPLOYMENT/BATCH_CHECKLISTS.md)
- [CI/CD](./04-DEPLOYMENT/CI_CD.md)
- [VPS Setup](./04-DEPLOYMENT/VPS_SETUP.md)
- [Environment Variables](./04-DEPLOYMENT/ENV_VARIABLES.md)

## 🔧 Operations

- [Monitoring](./05-OPERATIONS/MONITORING.md)
- [Troubleshooting](./05-OPERATIONS/TROUBLESHOOTING.md)
- [Runbook](./05-OPERATIONS/RUNBOOK.md)

## 🔗 Integrations

- [Stripe](./06-INTEGRATIONS/STRIPE.md)
- [RingCentral](./06-INTEGRATIONS/RINGCENTRAL.md)
- [Google](./06-INTEGRATIONS/GOOGLE.md) - Analytics, Calendar, Ads
- [Meta](./06-INTEGRATIONS/META.md) - WhatsApp, Facebook, Instagram

---

## 📅 Key Documents

| Document                                                                  | Description             | Last Updated |
| ------------------------------------------------------------------------- | ----------------------- | ------------ |
| [Deployment Batch Strategy](./04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md) | 6-batch deployment plan | Dec 2025     |
| [Consolidated Roadmap](./CONSOLIDATED_MASTER_ROADMAP.md)                  | All features mapped     | Dec 2025     |
| [API Documentation](./03-API/API_REFERENCE.md)                            | 394 routes              | Dec 2025     |
```

---

## 🗓️ Implementation Timeline

### Week 1: Archive & Cleanup

- [ ] Move 30+ historical files to `/archives/deprecated-docs/`
- [ ] Create new folder structure
- [ ] Create `docs/README.md` master index

### Week 2: Consolidation

- [ ] Merge payment docs → `PAYMENT_SYSTEM.md`
- [ ] Merge review docs → `REVIEWS_LOYALTY.md`
- [ ] Merge deployment docs → Consolidated files
- [ ] Merge integration docs by platform

### Week 3: Validation

- [ ] Verify all links work
- [ ] Remove duplicate content
- [ ] Add cross-references
- [ ] Test onboarding flow with fresh eyes

---

## 📏 Documentation Standards

### File Naming

- `FEATURE_NAME.md` - Uppercase with underscores
- No version numbers in filenames
- No dates in filenames

### File Structure

```markdown
# Title

**Last Updated:** [Date] **Related:** [Links to related docs]

## Overview

Brief description

## Prerequisites

What you need first

## [Main Content]

...

## Troubleshooting

Common issues

## Related Documentation

- [Link 1](...)
- [Link 2](...)
```

### Cross-References

Always link to related docs, never duplicate content:

```markdown
For payment setup, see
[Payment System](../02-FEATURES/PAYMENT_SYSTEM.md)
```

---

## 🎯 Success Metrics

| Metric            | Before  | Target      |
| ----------------- | ------- | ----------- |
| Total MD files    | 129     | <50         |
| Time to find info | Minutes | <30 seconds |
| Onboarding time   | Days    | <1 day      |
| Duplicate content | High    | Zero        |

---

## 📎 Quick Reference

### Where to Find...

| Topic                 | Location                                          |
| --------------------- | ------------------------------------------------- |
| How to run locally    | `docs/00-ONBOARDING/QUICK_START.md`               |
| How to deploy         | `docs/04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md` |
| API endpoints         | `docs/03-API/API_REFERENCE.md`                    |
| Environment variables | `docs/04-DEPLOYMENT/ENV_VARIABLES.md`             |
| Stripe setup          | `docs/06-INTEGRATIONS/STRIPE.md`                  |
| AI agents             | `docs/02-FEATURES/AI_CHAT.md`                     |
| Database schema       | `docs/01-ARCHITECTURE/DATABASE.md`                |

---

**Document Status:** 📋 PLAN - Ready for Implementation **Owner:**
Engineering Team **Next Action:** Start Week 1 cleanup
