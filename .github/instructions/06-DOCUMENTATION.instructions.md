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

## 🔗 Related Docs

- `docs/README.md` – Documentation index
- `docs/DOCUMENTATION_MANAGEMENT.md` – Full guide
