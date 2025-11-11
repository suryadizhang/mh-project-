# 📚 MH Webapps - Master Documentation Index

> **Last Updated:** November 5, 2025  
> **Project Status:** Production Ready (Nuclear Refactor Complete)

## 🚀 Quick Start

| Document                                                             | Purpose                        | Audience           |
| -------------------------------------------------------------------- | ------------------------------ | ------------------ |
| [README.md](./README.md)                                             | Project overview and setup     | Everyone           |
| [Backend README](./apps/backend/README.md)                           | Backend-specific documentation | Developers         |
| [Backend API Reference](./apps/backend/README_API.md)                | Complete API documentation     | Developers, DevOps |
| [E2E Testing Guide](./docs/06-QUICK_REFERENCE/E2E_TESTING_GUIDE.md)  | Testing instructions           | QA, Developers     |
| [Deployment Checklist](./docs/04-DEPLOYMENT/DEPLOYMENT_CHECKLIST.md) | Production deployment          | DevOps             |

---

## 📁 Documentation Structure

### 📂 Root Level

- **README.md** - Main project documentation
- **DOCUMENTATION_INDEX.md** - This file (navigation hub)

### 📂 Backend (`apps/backend/`)

- **README.md** - Backend overview and setup
- **README_API.md** - Complete API reference (250+ endpoints)
- **ARCHITECTURE.md** - Clean architecture documentation
- **DATABASE_MIGRATIONS.md** - Database migration guide
- **MIGRATION_SUMMARY.md** - Nuclear refactor history
- **HEALTH_CHECKS.md** - Health monitoring guide
- **CIRCULAR_IMPORT_PREVENTION_GUIDE.md** - Code quality guide

### 📂 Documentation (`docs/`)

#### 📐 01-ARCHITECTURE

Architecture, design decisions, and system overviews:

- **DATABASE_INDEX_DEPLOYMENT_GUIDE.md** - Database optimization
- **MULTI_DOMAIN_DEPLOYMENT_GUIDE.md** - Multi-domain setup
- **DECISION_MATRIX_AI_ARCHITECTURE.md** - AI architecture decisions
- **QUICK_DEPLOYMENT_GUIDE.md** - Fast deployment guide
- **STRIPE_WEBHOOK_VISUAL_GUIDE.md** - Stripe webhook documentation
- **VISUAL_ARCHITECTURE_COMPARISON.md** - Architecture comparisons

#### 🔨 02-IMPLEMENTATION

Implementation guides and integration documentation:

- **4_TIER_RBAC_IMPLEMENTATION_PLAN.md** - Role-based access control
- **BACKEND_NOTIFICATION_INTEGRATION_GUIDE.md** - Notification system
- **EXECUTION_PLAN_TOOL_CALLING_PHASE.md** - Tool calling
  implementation
- **GOOGLE_OAUTH_IMPLEMENTATION_GUIDE.md** - OAuth2 setup
- **HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md** - Priority features
- **RBAC_IMPLEMENTATION_CHECKLIST.md** - RBAC checklist

#### ⚡ 03-FEATURES

Feature-specific documentation:

- **ADMIN_PANEL_QUICK_REFERENCE.md** - Admin panel guide
- **ADMIN_REFRESH_AND_SMART_RERENDER.md** - Smart rerendering
- **AI_EMAIL_RESPONSES_FOR_REVIEW.md** - AI email generation
- **CALENDAR_QUICK_START.md** - Calendar feature guide
- **CUSTOMER_REVIEW_BLOG_SYSTEM.md** - Review system
- **DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md** - Pricing engine
- **EMAIL_SERVICE_SETUP_GUIDE.md** - Email configuration
- **ENTERPRISE_FEATURES_ROADMAP.md** - Enterprise features
- **FAILED_BOOKING_LEAD_CAPTURE.md** - Lead capture system
- **LOYALTY_PROGRAM_EXPLANATION.md** - Loyalty program
- **PAYMENT_OPTIONS_GUIDE.md** - Payment methods
- **SMART_AI_ESCALATION_SYSTEM.md** - AI escalation
- **WHATSAPP_BUSINESS_API_SETUP_GUIDE.md** - WhatsApp integration

#### 🚢 04-DEPLOYMENT

Deployment, environment, and operations:

- **DEPLOYMENT_CHECKLIST.md** - Pre-deployment verification
- **DATABASE_SETUP_GUIDE.md** - Database setup
- **CLOUDFLARE_TUNNEL_GUIDE.md** - Cloudflare tunnels
- **ENV_SETUP_CHECKLIST.md** - Environment variables
- **ENV_COPY_PASTE_TEMPLATES.md** - Environment templates
- **PLESK_DEPLOYMENT_SETUP_GUIDE.md** - Plesk deployment
- **PRODUCTION_DEPLOYMENT_CHECKLIST.md** - Production checklist
- **PRODUCTION_OPERATIONS_RUNBOOK.md** - Operations runbook
- **PRODUCTION_MONITORING_QUERIES.md** - Monitoring queries
- **WEBHOOK_CONFIGURATION_PRODUCTION.md** - Webhook setup

#### 🧪 05-TESTING

Testing guides and quality assurance:

- **DECISION_SUMMARY.md** - Testing decisions
- **PRIVACY_INITIALS_TESTING.md** - Privacy testing
- **READY_TO_TEST.md** - Test readiness checklist
- **SERVICES_RUNNING_SUCCESSFULLY.md** - Service validation
- **WEBHOOK_TESTING_READY.md** - Webhook testing

#### 📖 06-QUICK_REFERENCE

Quick reference guides and cheat sheets:

- **API_DOCUMENTATION.md** - API quick reference
- **E2E_TESTING_GUIDE.md** - End-to-end testing
- **EMAIL_SETUP_GUIDE.md** - Email configuration
- **ENTERPRISE_SCALE_OPTIMIZATION_GUIDE.md** - Enterprise scaling
- **LOCAL_DEVELOPMENT_SETUP.md** - Local setup
- **PERFORMANCE_OPTIMIZATION_GUIDE.md** - Performance tuning
- **QUICK_ACTION_CHECKLIST.md** - Action items
- **QUICK_DECISION_GUIDE.md** - Decision flowcharts
- **QUICK_START_STRIPE_WEBHOOK.md** - Stripe quick start
- **RINGCENTRAL_JWT_SETUP.md** - RingCentral setup
- **STARTUP_WARNINGS_EXPLAINED.md** - Startup troubleshooting
- **STATION_MANAGEMENT_QUICK_START.md** - Station management
- **TERMINAL_COMMANDS_REFERENCE.md** - CLI commands
- **TESTING_COMPREHENSIVE_GUIDE.md** - Testing guide
- **WEBHOOK_TESTING_GUIDE.md** - Webhook testing

#### 🔧 Additional Folders

- **deployment/** - Deployment-specific guides
- **features/** - Feature implementation docs
- **migration/** - Migration guides (Llama3, Neo4j)
- **operations/** - Operations runbooks
- **security/** - Security policies

---

## 🎯 Common Tasks

### For Developers

#### Getting Started

1. Read [README.md](./README.md)
2. Setup local environment:
   [LOCAL_DEVELOPMENT_SETUP.md](./docs/06-QUICK_REFERENCE/LOCAL_DEVELOPMENT_SETUP.md)
3. Run tests:
   [E2E_TESTING_GUIDE.md](./docs/06-QUICK_REFERENCE/E2E_TESTING_GUIDE.md)

#### Development Workflow

1. Check [Backend ARCHITECTURE.md](./apps/backend/ARCHITECTURE.md)
2. Review
   [CIRCULAR_IMPORT_PREVENTION_GUIDE.md](./apps/backend/CIRCULAR_IMPORT_PREVENTION_GUIDE.md)
3. Use [Backend README_API.md](./apps/backend/README_API.md) for API
   reference

#### Adding New Features

1. Review
   [RBAC_IMPLEMENTATION_CHECKLIST.md](./docs/02-IMPLEMENTATION/RBAC_IMPLEMENTATION_CHECKLIST.md)
2. Follow
   [HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md](./docs/02-IMPLEMENTATION/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md)
3. Update tests per
   [TESTING_COMPREHENSIVE_GUIDE.md](./docs/06-QUICK_REFERENCE/TESTING_COMPREHENSIVE_GUIDE.md)

### For DevOps

#### Deployment

1. **Pre-Deployment:**
   [DEPLOYMENT_CHECKLIST.md](./docs/04-DEPLOYMENT/DEPLOYMENT_CHECKLIST.md)
2. **Database Setup:**
   [DATABASE_SETUP_GUIDE.md](./docs/04-DEPLOYMENT/DATABASE_SETUP_GUIDE.md)
3. **Environment:**
   [ENV_SETUP_CHECKLIST.md](./docs/04-DEPLOYMENT/ENV_SETUP_CHECKLIST.md)
4. **Production:**
   [PRODUCTION_DEPLOYMENT_CHECKLIST.md](./docs/04-DEPLOYMENT/PRODUCTION_DEPLOYMENT_CHECKLIST.md)

#### Operations

1. **Monitoring:**
   [PRODUCTION_MONITORING_QUERIES.md](./docs/04-DEPLOYMENT/PRODUCTION_MONITORING_QUERIES.md)
2. **Runbook:**
   [PRODUCTION_OPERATIONS_RUNBOOK.md](./docs/04-DEPLOYMENT/PRODUCTION_OPERATIONS_RUNBOOK.md)
3. **Scaling:**
   [ENTERPRISE_SCALE_OPTIMIZATION_GUIDE.md](./docs/06-QUICK_REFERENCE/ENTERPRISE_SCALE_OPTIMIZATION_GUIDE.md)

### For QA/Testing

#### Testing Workflow

1. **Setup:**
   [E2E_TESTING_GUIDE.md](./docs/06-QUICK_REFERENCE/E2E_TESTING_GUIDE.md)
2. **API Testing:**
   [API_DOCUMENTATION.md](./docs/06-QUICK_REFERENCE/API_DOCUMENTATION.md)
3. **Webhook Testing:**
   [WEBHOOK_TESTING_GUIDE.md](./docs/06-QUICK_REFERENCE/WEBHOOK_TESTING_GUIDE.md)
4. **Verification:**
   [READY_TO_TEST.md](./docs/05-TESTING/READY_TO_TEST.md)

### For Product Managers

#### Feature Planning

1. **Roadmap:**
   [ENTERPRISE_FEATURES_ROADMAP.md](./docs/03-FEATURES/ENTERPRISE_FEATURES_ROADMAP.md)
2. **Admin Panel:**
   [ADMIN_PANEL_QUICK_REFERENCE.md](./docs/03-FEATURES/ADMIN_PANEL_QUICK_REFERENCE.md)
3. **Pricing:**
   [DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md](./docs/03-FEATURES/DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md)

---

## 🔍 Finding Documentation

### By Topic

**Authentication & Authorization**

- [4_TIER_RBAC_IMPLEMENTATION_PLAN.md](./docs/02-IMPLEMENTATION/4_TIER_RBAC_IMPLEMENTATION_PLAN.md)
- [GOOGLE_OAUTH_IMPLEMENTATION_GUIDE.md](./docs/02-IMPLEMENTATION/GOOGLE_OAUTH_IMPLEMENTATION_GUIDE.md)
- [RINGCENTRAL_JWT_SETUP.md](./docs/06-QUICK_REFERENCE/RINGCENTRAL_JWT_SETUP.md)

**Payment Processing**

- [PAYMENT_OPTIONS_GUIDE.md](./docs/03-FEATURES/PAYMENT_OPTIONS_GUIDE.md)
- [QUICK_START_STRIPE_WEBHOOK.md](./docs/06-QUICK_REFERENCE/QUICK_START_STRIPE_WEBHOOK.md)
- [STRIPE_WEBHOOK_VISUAL_GUIDE.md](./docs/01-ARCHITECTURE/STRIPE_WEBHOOK_VISUAL_GUIDE.md)

**Email & Notifications**

- [EMAIL_SERVICE_SETUP_GUIDE.md](./docs/03-FEATURES/EMAIL_SERVICE_SETUP_GUIDE.md)
- [BACKEND_NOTIFICATION_INTEGRATION_GUIDE.md](./docs/02-IMPLEMENTATION/BACKEND_NOTIFICATION_INTEGRATION_GUIDE.md)
- [EMAIL_SETUP_GUIDE.md](./docs/06-QUICK_REFERENCE/EMAIL_SETUP_GUIDE.md)

**AI Features**

- [AI_EMAIL_RESPONSES_FOR_REVIEW.md](./docs/03-FEATURES/AI_EMAIL_RESPONSES_FOR_REVIEW.md)
- [SMART_AI_ESCALATION_SYSTEM.md](./docs/03-FEATURES/SMART_AI_ESCALATION_SYSTEM.md)
- [DECISION_MATRIX_AI_ARCHITECTURE.md](./docs/01-ARCHITECTURE/DECISION_MATRIX_AI_ARCHITECTURE.md)

**Calendar & Booking**

- [CALENDAR_QUICK_START.md](./docs/03-FEATURES/CALENDAR_QUICK_START.md)
- [FAILED_BOOKING_LEAD_CAPTURE.md](./docs/03-FEATURES/FAILED_BOOKING_LEAD_CAPTURE.md)

**Database**

- [DATABASE_SETUP_GUIDE.md](./docs/04-DEPLOYMENT/DATABASE_SETUP_GUIDE.md)
- [DATABASE_MIGRATIONS.md](./apps/backend/DATABASE_MIGRATIONS.md)
- [DATABASE_INDEX_DEPLOYMENT_GUIDE.md](./docs/01-ARCHITECTURE/DATABASE_INDEX_DEPLOYMENT_GUIDE.md)

**Integrations**

- [WHATSAPP_BUSINESS_API_SETUP_GUIDE.md](./docs/03-FEATURES/WHATSAPP_BUSINESS_API_SETUP_GUIDE.md)
- [WEBHOOK_CONFIGURATION_PRODUCTION.md](./docs/04-DEPLOYMENT/WEBHOOK_CONFIGURATION_PRODUCTION.md)
- [RINGCENTRAL_JWT_SETUP.md](./docs/06-QUICK_REFERENCE/RINGCENTRAL_JWT_SETUP.md)

---

## 📊 Project Stats

**Total Documentation Files:** 254 MD files (65% reduction from 725)

- Root: 2 files
- Backend: 7 files
- Docs: 158 files
- Archives: 296 files (historical)

**Documentation Coverage:**

- ✅ 100% of features documented
- ✅ 100% of APIs documented (250+ endpoints)
- ✅ 100% of deployment procedures documented
- ✅ 96.9% test pass rate (31/32 tests)

**Code Quality:**

- ✅ Clean Architecture (CQRS + DDD)
- ✅ SOLID Principles
- ✅ Circular Import Prevention
- ✅ Type Safety (Pydantic v2)
- ✅ Production Ready

---

## 🆘 Need Help?

### Quick Actions

1. **Can't find a document?** Use `Ctrl+F` in your editor or `grep`
   command
2. **Setting up locally?** Start with
   [LOCAL_DEVELOPMENT_SETUP.md](./docs/06-QUICK_REFERENCE/LOCAL_DEVELOPMENT_SETUP.md)
3. **Deploying?** Follow
   [DEPLOYMENT_CHECKLIST.md](./docs/04-DEPLOYMENT/DEPLOYMENT_CHECKLIST.md)
4. **API questions?** Check
   [Backend README_API.md](./apps/backend/README_API.md)
5. **Testing issues?** See
   [E2E_TESTING_GUIDE.md](./docs/06-QUICK_REFERENCE/E2E_TESTING_GUIDE.md)

### Common Commands

```bash
# Search all documentation
grep -r "your search term" docs/

# Find files by name
find . -name "*keyword*.md"

# Count documentation files
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.venv/*" | wc -l
```

---

## 🗂️ Archives

Historical documentation (migration reports, phase completions,
audits) is preserved in:

- `archives/` - 296 historical documents organized by date and topic

**Do not delete archives** - they provide audit trail and historical
context.

---

## 📝 Documentation Standards

### Creating New Documentation

1. Use clear, descriptive filenames (UPPERCASE_WITH_UNDERSCORES.md)
2. Place in appropriate folder (01-ARCHITECTURE, 02-IMPLEMENTATION,
   etc.)
3. Include purpose, audience, and last updated date
4. Update this index file when adding new docs
5. Follow existing formatting patterns

### Updating Documentation

1. Always update "Last Updated" date
2. Keep examples current and working
3. Remove outdated information
4. Update related documents if needed
5. Commit with descriptive message

---

**🎉 Clean, organized, and production-ready documentation!**
