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
