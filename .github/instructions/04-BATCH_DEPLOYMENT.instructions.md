---
applyTo: '**'
---

# My Hibachi – Batch Deployment Context

**Priority: HIGH** – Always check current batch before working.

---

## 📊 Batch Overview

| Batch | Focus                          | Duration   | Branch Pattern              |
| ----- | ------------------------------ | ---------- | --------------------------- |
| **0** | Repo Cleanup & Branch Strategy | 1-2 days   | `nuclear-refactor` → `main` |
| **1** | Core Booking + Security        | Week 1-2   | `feature/batch-1-*`         |
| **2** | Payment Processing             | Week 3-4   | `feature/batch-2-*`         |
| **3** | Core AI                        | Week 5-6   | `feature/batch-3-*`         |
| **4** | Communications                 | Week 7-8   | `feature/batch-4-*`         |
| **5** | Advanced AI + Marketing        | Week 9-10  | `feature/batch-5-*`         |
| **6** | AI Training & Scaling          | Week 11-12 | `feature/batch-6-*`         |

---

## 🎯 Current Batch (Check CURRENT_BATCH_STATUS.md)

**Always read `CURRENT_BATCH_STATUS.md` at repo root** for:

- Active batch number
- What's in scope
- What's blocked
- Current branch
- Next milestones

---

## 📋 Batch 0: Repository Cleanup (CURRENT)

### Scope:

- ✅ Commit all uncommitted changes
- ✅ Merge `nuclear-refactor-clean-architecture` → `main`
- ✅ Create `dev` branch from new `main`
- ✅ Apply branch protection rules
- ✅ Split deployment docs into hierarchy
- ✅ Clean up instruction files
- ✅ Delete backup/temp files

### Out of Scope:

- ❌ New features
- ❌ Code changes (except cleanup)
- ❌ Database migrations
- ❌ API changes

---

## 📋 Batch 1: Core Booking + Security

### Scope:

- Core booking CRUD
- Authentication (JWT + API keys)
- 4-tier RBAC system
- Audit trail
- Failed booking lead capture
- Cloudflare security setup
- Scaling measurement system

### Key Files:

- `apps/backend/src/routers/v1/bookings.py`
- `apps/backend/src/services/booking_service.py`
- `apps/backend/src/core/security.py`
- `database/migrations/add_security_tables.sql`

---

## 📋 Batch 2: Payment Processing

### Scope:

- Stripe integration
- Payment intents
- Deposit collection
- Invoice generation
- Refund processing
- Dynamic pricing management
- Internal tax collection

### Key Files:

- `apps/backend/src/db/models/stripe.py`
- `apps/backend/src/services/payment_service.py`
- `apps/backend/src/routers/v1/stripe.py`

---

## 📋 Batch 3: Core AI

### Scope:

- OpenAI integration
- Smart escalation system
- AI conversation handling
- Knowledge base
- pgvector embeddings

### Key Files:

- `apps/backend/src/api/ai/`
- `apps/backend/src/services/ai_service.py`
- `database/migrations/create_ai_tables.sql`

---

## 📋 Batch 4: Communications

### Scope:

- RingCentral voice/SMS
- Deepgram transcription
- Meta (WhatsApp/FB/IG)
- Google Business messages
- Omnichannel inbox

### Key Files:

- `apps/backend/src/routers/v1/webhooks/`
- `apps/backend/src/services/ringcentral_*.py`
- `apps/backend/src/api/v1/inbox/`

---

## 📋 Batch 5: Advanced AI + Marketing

### Scope:

- Emotion detection
- Psychology agents
- Tool calling
- RAG system
- Customer reviews
- Marketing intelligence
- Google integrations

---

## 📋 Batch 6: AI Training & Scaling

### Scope:

- Multi-LLM ensemble
- Shadow learning
- Training pipeline
- Loyalty program
- Google Calendar sync

---

## 🚦 Batch Rules

### DO:

- ✅ Check `CURRENT_BATCH_STATUS.md` before starting work
- ✅ Only work on current batch scope
- ✅ Reference batch-specific docs in `docs/04-DEPLOYMENT/batches/`
- ✅ Update batch status when completing milestones

### DON'T:

- ❌ Work on future batch features
- ❌ Skip batch prerequisites
- ❌ Merge without batch tests passing
- ❌ Deploy partial batch work

---

## 📦 Strict One-PR-Per-Batch Deployment (CRITICAL)

**OPTION A: Industry-standard strict batch deployment.**

Each batch = ONE Pull Request to main. No exceptions.

### The Workflow:

```
┌─────────────────────────────────────────────────────────────┐
│                  STRICT BATCH PR WORKFLOW                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  feature/batch-1-*  ──PR──►  dev  ──PR──►  main             │
│       (work)              (test)        (production)        │
│                                                              │
│  ⚠️  ONE PR per batch to main                               │
│  ⚠️  Batch 2 PR cannot merge until Batch 1 is in main      │
│  ⚠️  No mixing batch files in same PR                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Process:

| Step | Action                       | Branch                  | Target |
| ---- | ---------------------------- | ----------------------- | ------ |
| 1    | Create feature branch        | `feature/batch-X-*`     | -      |
| 2    | Develop all batch X features | `feature/batch-X-*`     | -      |
| 3    | PR to dev for staging        | `feature/batch-X-*`     | `dev`  |
| 4    | Test in staging (48+ hours)  | `dev`                   | -      |
| 5    | **Single PR to main**        | `dev` or `feature/*`    | `main` |
| 6    | Monitor production           | `main`                  | -      |
| 7    | Start Batch X+1              | `feature/batch-(X+1)-*` | -      |

### The Golden Rules:

| Rule                           | Description                       |
| ------------------------------ | --------------------------------- |
| **ONE batch = ONE PR to main** | Never combine batches             |
| **Sequential only**            | Batch 2 waits for Batch 1 in main |
| **Complete batches only**      | No partial batch merges           |
| **All tests must pass**        | 100% batch tests before PR        |
| **48-hour staging**            | Mandatory staging verification    |

### Why This Matters:

1. **Traceability** – Each batch = one identifiable deployment
2. **Rollback** – Revert entire batch with one `git revert`
3. **Bug hunting** – `git bisect` finds exact batch that broke
4. **Clean history** – Clear audit trail per deployment
5. **Accountability** – Know exactly what shipped when

### Batch File Manifests:

**Batch 1 (Core Booking + Security) adds:**

```
apps/backend/src/routers/v1/bookings.py
apps/backend/src/services/booking_service.py
apps/backend/src/core/security.py
apps/backend/src/core/rbac.py
apps/backend/src/db/models/audit.py
database/migrations/add_security_tables.sql
apps/customer/src/components/booking/*
apps/admin/src/components/booking/*
```

**Batch 2 (Payment Processing) adds:**

```
apps/backend/src/db/models/stripe.py
apps/backend/src/services/payment_service.py
apps/backend/src/routers/v1/stripe.py
apps/backend/src/routers/v1/webhooks/stripe.py
apps/customer/src/components/payment/*
apps/admin/src/components/payments/*
```

**Batch 3 (Core AI) adds:**

```
apps/backend/src/api/ai/*
apps/backend/src/services/ai_service.py
apps/backend/src/db/models/ai.py
database/migrations/create_ai_tables.sql
apps/admin/src/components/ai/*
```

**Batch 4 (Communications) adds:**

```
apps/backend/src/routers/v1/webhooks/ringcentral.py
apps/backend/src/routers/v1/webhooks/meta.py
apps/backend/src/services/ringcentral_*.py
apps/backend/src/services/deepgram_service.py
apps/backend/src/api/v1/inbox/*
apps/admin/src/components/inbox/*
```

### PR Scope Rules (STRICTLY ENFORCED):

| Rule                      | Description                           | Violation = |
| ------------------------- | ------------------------------------- | ----------- |
| **ONE batch per PR**      | Never combine Batch 1 + Batch 2 files | PR Rejected |
| **Only batch files**      | No unrelated changes allowed          | PR Rejected |
| **Complete batch only**   | All batch features or none            | PR Rejected |
| **All tests passing**     | 100% of batch tests must pass         | PR Blocked  |
| **48-hour staging**       | Must be stable in dev first           | PR Blocked  |
| **Batch commit messages** | All commits: `feat(batch-X): ...`     | PR Rejected |

### What CAN Be Included:

| ✅ Allowed               | Example                                   |
| ------------------------ | ----------------------------------------- |
| Batch-specific code      | `booking_service.py` for Batch 1          |
| Batch-specific tests     | `test_booking_service.py`                 |
| Shared utils (first use) | `utils/validators.py` if Batch 1 needs it |
| Config for batch         | Feature flags for this batch              |
| Docs for batch features  | API docs for new endpoints                |

### What CANNOT Be Included:

| ❌ NOT Allowed      | Why                        |
| ------------------- | -------------------------- |
| Future batch code   | Batch 2 code in Batch 1 PR |
| Unrelated fixes     | Random bug fixes           |
| Planning docs       | `*_PLAN.md`, `*_STATUS.md` |
| Incomplete features | Partial implementations    |

### What About Shared/Common Code?

Some code is needed by multiple batches:

| Code Type         | When to Add                         |
| ----------------- | ----------------------------------- |
| Core utils        | First batch that needs it           |
| Shared types      | First batch that needs it           |
| Base classes      | First batch that needs it           |
| Config extensions | With batch that adds the feature    |
| Shared components | With batch that introduces use case |

### Feature Flags for Cross-Batch Code:

If Batch 2 code must exist before Batch 2 is ready:

```python
# Code can exist, but is disabled by flag
if settings.FEATURE_STRIPE_ENABLED:  # False until Batch 2
    process_payment()
else:
    raise NotImplementedError("Payments not yet enabled")
```

### PR Review Checklist for Batch Deployment:

- [ ] PR only contains files for THIS batch
- [ ] No future batch code included (unless behind flag)
- [ ] Tests only for THIS batch's features
- [ ] Documentation only for THIS batch's features
- [ ] Feature flags configured for THIS batch
- [ ] Commit messages reference batch: `feat(batch-X): description`

---

## 🔄 Batch Transition Checklist

Before moving to next batch:

- [ ] All batch features implemented
- [ ] All batch tests passing
- [ ] PR merged to `dev`
- [ ] Staging verified 48+ hours
- [ ] PR merged to `main`
- [ ] Production verified
- [ ] Feature flags configured
- [ ] Documentation updated
- [ ] `CURRENT_BATCH_STATUS.md` updated

---

## 📁 Batch Documentation

Each batch has dedicated docs:

```
docs/04-DEPLOYMENT/
├── batches/
│   ├── BATCH-0-REPO-CLEANUP.md
│   ├── BATCH-1-CORE-BOOKING.md
│   ├── BATCH-2-PAYMENTS.md
│   ├── BATCH-3-CORE-AI.md
│   ├── BATCH-4-COMMUNICATIONS.md
│   ├── BATCH-5-MARKETING-AI.md
│   └── BATCH-6-TRAINING-SCALING.md
└── checklists/
    ├── BATCH-1-CHECKLIST.md
    ├── BATCH-2-CHECKLIST.md
    └── ...
```

---

## 🔗 Related Docs

- `CURRENT_BATCH_STATUS.md` – Live status
- `docs/04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md` – Master plan
- `docs/04-DEPLOYMENT/batches/` – Per-batch details
