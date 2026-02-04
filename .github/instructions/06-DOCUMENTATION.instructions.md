---
applyTo: '**'
---

# My Hibachi – Documentation Standards

**Priority: MEDIUM** – Keep docs organized and current.

---

## 📁 Documentation Hierarchy

```
docs/
├── 00-ONBOARDING/           # Getting started
│   ├── QUICK_START.md
│   ├── LOCAL_DEVELOPMENT_GUIDE.md
│   └── ONBOARDING.md
│
├── 01-ARCHITECTURE/         # System design
│   ├── SYSTEM_OVERVIEW.md
│   ├── DATABASE_ARCHITECTURE.md
│   └── API_DESIGN.md
│
├── 02-IMPLEMENTATION/       # How things work
│   ├── BOOKING_SYSTEM.md
│   ├── PAYMENT_FLOW.md
│   └── AI_INTEGRATION.md
│
├── 03-FEATURES/             # Feature specs
│   ├── PRICING_SYSTEM.md
│   ├── RBAC_SYSTEM.md
│   └── LOYALTY_PROGRAM.md
│
├── 04-DEPLOYMENT/           # Deployment guides
│   ├── 00-ENTERPRISE-STANDARDS.md
│   ├── 01-PERFORMANCE-BUDGETS.md
│   ├── batches/
│   │   ├── BATCH-0-REPO-CLEANUP.md
│   │   ├── BATCH-1-CORE-BOOKING.md
│   │   └── ...
│   └── checklists/
│       └── ...
│
├── 05-OPERATIONS/           # Runbooks
│   ├── PRODUCTION_RUNBOOK.md
│   ├── INCIDENT_RESPONSE.md
│   └── MONITORING.md
│
└── 06-QUICK_REFERENCE/      # Cheat sheets
    ├── API_ENDPOINTS.md
    ├── ENV_VARIABLES.md
    └── FEATURE_FLAGS.md
```

---

## 📝 Documentation Rules

### 1. Single Source of Truth

- ONE place for each piece of information
- NO duplicate content across files
- Reference other docs, don't copy

### 2. Keep Current

- Update docs when changing code
- Mark outdated docs as deprecated
- Archive old docs to `archives/deprecated-docs/`

### 3. Use Consistent Format

Every doc should have:

```markdown
# Title

**Last Updated:** YYYY-MM-DD **Status:** Active | Deprecated | Draft
**Relates To:** [Link to related docs]

---

## Overview

Brief description of what this doc covers.

## Content

Main content here...

## Related Docs

- [Link 1](./path)
- [Link 2](./path)
```

---

## 🚫 Documentation Anti-Patterns

| Don't                          | Do Instead                  |
| ------------------------------ | --------------------------- |
| Create new doc for each change | Update existing doc         |
| Put docs in random locations   | Follow hierarchy            |
| Leave outdated docs            | Archive or update           |
| Duplicate content              | Reference other docs        |
| Use vague names                | Use descriptive names       |
| Skip the date                  | Always include last updated |

---

## 📊 Naming Conventions

### Files:

```
# Good
BOOKING_SYSTEM.md
API_ENDPOINTS_V1.md
BATCH-1-CORE-BOOKING.md

# Bad
notes.md
temp.md
booking.md
doc1.md
```

### Headers:

```markdown
# Main Title (H1 - ONE per doc)

## Major Section (H2)

### Subsection (H3)

#### Detail (H4)
```

---

## 🗂️ Root-Level Docs

Only these docs belong at repo root:

| File                      | Purpose                       |
| ------------------------- | ----------------------------- |
| `README.md`               | Project overview, quick start |
| `CONTRIBUTING.md`         | How to contribute             |
| `LICENSE`                 | License info                  |
| `CURRENT_BATCH_STATUS.md` | Active batch tracking         |

Everything else goes in `docs/`.

---

## 📋 When to Create New Docs

Create new doc when:

- New feature system (e.g., loyalty program)
- New integration (e.g., new payment provider)
- New deployment target
- New batch/phase

DON'T create new doc for:

- Minor updates (update existing)
- Bug fixes (update existing)
- Small changes (add to existing)

---

## 🔄 Documentation Workflow

### When Adding Feature:

1. Check if relevant doc exists
2. If yes → Update it
3. If no → Create in correct folder
4. Update `docs/README.md` index
5. Cross-reference related docs

### When Deprecating:

1. Add `**Status:** Deprecated` header
2. Add deprecation notice at top
3. Point to replacement doc
4. Move to `archives/deprecated-docs/` after 30 days

---

## 📊 Documentation Quality Checklist

Before committing docs:

- [ ] Correct folder location
- [ ] Descriptive filename
- [ ] Last updated date
- [ ] Status indicator
- [ ] Clear structure (H1, H2, H3)
- [ ] No duplicate content
- [ ] Links work
- [ ] Cross-references added

---

## 🚨 Business Data Verification (CRITICAL for AI/Pricing Docs)

**When documenting business data (pricing, policies, menu items), you
MUST verify from source:**

### ⚠️ DYNAMIC PRICING WARNING

**ALL pricing values are managed by the Dynamic Variables System and
can change at any time!**

| Rule                                      | Reason                           |
| ----------------------------------------- | -------------------------------- |
| Never treat prices as permanent           | Owner can update via admin panel |
| Always include "as of [date]"             | Values may be stale              |
| Reference variable names, not just values | `adultPrice` not just `$55`      |
| Add "verify current pricing" notes        | Remind readers to check API      |

**Dynamic Variables Source of Truth:**

- **Backend:** `dynamic_variables` table →
  `dynamic_variables_service.py`
- **API:** `GET /api/v1/pricing/current`
- **Frontend:** `usePricing()` hook → `pricingTemplates.ts` (fallback
  only)

### Pre-Documentation Checklist:

- [ ] **Searched `faqsData.ts`** for pricing and policy data
- [ ] **Searched `menu.ts`** for menu item names
- [ ] **Searched `pricingTemplates.ts`** for default values
- [ ] **NO invented values** - every number has a source
- [ ] **Source cited** in document (e.g., "Source: faqsData.ts lines
      98-111")
- [ ] **Added "as of [date]"** to any specific price mentioned
- [ ] **Referenced variable names** (e.g., `adultPrice`,
      `partyMinimum`)
- [ ] **Added dynamic pricing disclaimer** if doc contains prices

### Verification Commands:

```bash
# Before writing pricing documentation
grep -r "\\$55\\|\\$30\\|deposit\\|refund" apps/customer/src/lib/data/

# Before writing menu/upgrade documentation
grep -r "filet\\|lobster\\|salmon\\|scallop\\|yakisoba\\|gyoza" apps/customer/src/lib/data/

# Before writing policy documentation
grep -r "cancel\\|reschedule\\|refund.*day" apps/customer/src/lib/data/
```

### Red Flags (STOP and Verify):

| If You're About To Write...      | STOP and Search For...                                |
| -------------------------------- | ----------------------------------------------------- |
| Any dollar amount ($X)           | Exact value in faqsData.ts or pricingTemplates.ts     |
| Menu item name not seen before   | Verify in menu.ts or faqsData.ts                      |
| Refund policy with timeframes    | Exact policy in faqsData.ts (search "refund\|cancel") |
| Upgrade names (Wagyu, King Crab) | Verify exists in faqsData.ts                          |

### If You Can't Find the Data:

1. **ASK the user** - "What is the correct value for X?"
2. **Mark as TBD** - Use `[TBD - need verified value]`
3. **NEVER invent** - This causes real business problems

---

## 🔗 Related Docs

- `docs/README.md` – Documentation index
- `docs/DOCUMENTATION_MANAGEMENT.md` – Full guide
