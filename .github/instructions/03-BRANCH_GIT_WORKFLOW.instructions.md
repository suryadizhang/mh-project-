---
applyTo: '**'
---

# My Hibachi – Branch & Git Workflow

**Priority: HIGH** – Branching rules are STRICT.

---

## 🌳 Branch Structure

```
main (production)
  │
  └── dev (staging)
        │
        ├── feature/batch-1-core
        ├── feature/batch-2-payments
        ├── feature/batch-3-ai
        └── feature/*
```

---

## 📋 Allowed Branches

| Branch      | Purpose             | Protection  | Deploy Target |
| ----------- | ------------------- | ----------- | ------------- |
| `main`      | Production code     | 🔴 STRICT   | Production    |
| `dev`       | Staging/integration | 🟠 MODERATE | Staging       |
| `feature/*` | Development work    | 🟢 NONE     | Preview/Local |

---

## 🧹 Clean Main Branch Policy

**Main branch must ONLY contain production-ready, deployed code.**

### What Goes in `main`:

| ✅ Allowed                      | ❌ NOT Allowed                    |
| ------------------------------- | --------------------------------- |
| Working source code             | `*_PLAN.md` planning documents    |
| `README.md`, `CONTRIBUTING.md`  | `*_ANALYSIS.md` development notes |
| `.github/instructions/` prompts | `*_SUMMARY.md` batch tracking     |
| CI/CD workflows                 | `*_STATUS.md` progress files      |
| Deployment guides               | `BATCH_*.md` batch documentation  |
| API documentation (`docs/`)     | Development/debug logs            |
| Essential configuration         | Temporary files, WIP notes        |

### Why Keep Main Clean:

1. **Traceability** – Each merge = one batch = findable bugs
2. **Rollback** – Clean history enables `git revert` by batch
3. **Bisect** – `git bisect` works when commits are atomic
4. **Audit** – Easy to see what changed per deployment

### Where Planning Docs Go:

```
feature/batch-X-*     ← Planning docs stay HERE during development
  └── BATCH_X_PLAN.md
  └── BATCH_X_STATUS.md
  └── Implementation notes

archives/             ← Move completed batch docs here (gitignored)
  └── batch-1/
  └── batch-2/

Local only            ← Keep development notes local
```

### Commit Message for Batches:

```bash
# Good - traceable to batch
feat(batch-1): add Stripe payment integration
fix(batch-1): resolve webhook signature validation
docs(batch-1): update payment API documentation

# Bad - not traceable
feat: add payments
fix: webhook bug
```

---

## 🚫 Branch Rules

### NEVER Do:

| Action                              | Why                         |
| ----------------------------------- | --------------------------- |
| Push directly to `main`             | PR + approval required      |
| Push directly to `dev`              | PR required                 |
| Create `hotfix/*` without emergency | Use feature branch          |
| Delete `main` or `dev`              | Protected branches          |
| Force push to protected branches    | History protection          |
| Create per-app branches             | Monorepo = unified branches |

### ❌ NEVER Create:

```
# WRONG - Per-app branches
customer-main
admin-main
backend-main
customer-feature/x
admin-feature/x
```

### ✅ ALWAYS Create:

```
# CORRECT - Unified feature branches
feature/batch-1-stripe-integration
feature/batch-2-payment-flow
feature/fix-booking-validation
```

---

## 🔄 Git Workflow

### Creating a Feature Branch

```bash
# 1. Start from dev (always!)
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/batch-X-description

# 3. Make changes, commit often
git add .
git commit -m "feat(scope): description"

# 4. Push to remote
git push -u origin feature/batch-X-description
```

### Merging to Dev (Staging)

```bash
# 1. Ensure branch is up to date
git checkout feature/batch-X-description
git pull origin dev
git merge dev  # Resolve conflicts if any

# 2. Push updates
git push origin feature/batch-X-description

# 3. Create PR: feature/* → dev
# 4. Wait for CI to pass
# 5. Get review approval
# 6. Merge PR
```

### Merging to Main (Production) - STRICT BATCH PR

**⚠️ ONE PR PER BATCH TO MAIN - NO EXCEPTIONS**

```bash
# 1. Ensure dev is stable (48+ hours minimum)
# 2. Verify ALL batch features complete
# 3. Verify ALL batch tests passing (100%)
# 4. Create PR: dev → main (or feature/batch-X → main)
#    Title: "Batch X: [Description]"
#    Example: "Batch 1: Core Booking + Security"
# 5. Wait for CI to pass
# 6. Get review approval
# 7. Merge PR (squash or merge commit)
# 8. Monitor production for 24 hours
# 9. Only THEN start Batch X+1 PR to main
```

### Batch PR Checklist (Before Creating PR to Main):

- [ ] All batch features implemented
- [ ] All batch tests passing locally
- [ ] Staged in `dev` for 48+ hours
- [ ] No other batch files included
- [ ] PR title follows: `Batch X: Description`
- [ ] All commits use `feat(batch-X):` format

---

## 📝 Commit Message Format

Use Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types:

| Type       | Use For                      |
| ---------- | ---------------------------- |
| `feat`     | New feature                  |
| `fix`      | Bug fix                      |
| `docs`     | Documentation                |
| `style`    | Formatting (no logic change) |
| `refactor` | Code restructuring           |
| `test`     | Adding tests                 |
| `chore`    | Maintenance tasks            |
| `perf`     | Performance improvement      |
| `security` | Security fix                 |

### Scopes:

| Scope      | Meaning               |
| ---------- | --------------------- |
| `customer` | Customer site changes |
| `admin`    | Admin panel changes   |
| `backend`  | Backend API changes   |
| `db`       | Database changes      |
| `ci`       | CI/CD changes         |
| `docs`     | Documentation         |

### Examples:

```bash
feat(backend): add Stripe webhook handler
fix(customer): resolve booking date picker bug
docs(deployment): update batch 1 checklist
refactor(admin): extract usePermissions hook
test(backend): add booking service unit tests
chore(ci): update deploy workflow
```

---

## 🔀 Merge Flow Diagram

```
┌─────────────────┐
│  feature/*      │ Developer works here
└────────┬────────┘
         │ PR (requires CI pass)
         ▼
┌─────────────────┐
│      dev        │ Staging environment
│   (48+ hours)   │ Test with flags ON
└────────┬────────┘
         │ PR (requires approval)
         ▼
┌─────────────────┐
│     main        │ Production
│  (monitoring)   │ Flags OFF by default
└─────────────────┘
```

---

## ✅ Before Any Git Operation

1. **Check current branch:** `git branch --show-current`
2. **Verify clean state:** `git status`
3. **Pull latest:** `git pull origin <branch>`
4. **Confirm correct base:** Usually `dev`, not `main`

---

## 🚨 Emergency Hotfix Process

Only for CRITICAL production bugs:

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix-description

# 2. Make minimal fix
# 3. PR directly to main (expedited review)
# 4. After merge, immediately merge main → dev
git checkout dev
git merge main
git push origin dev
```

---

## 📊 Branch Protection Settings

### Main Branch:

- ✅ Require PR before merging
- ✅ Require 1+ approval
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Restrict who can push
- ✅ Do not allow bypassing

### Dev Branch:

- ✅ Require PR before merging
- ✅ Require status checks to pass
- ⬜ Approval optional (expedited flow)

---

## 🔗 Related Docs

- `.github/BRANCH_PROTECTION_SETUP.md` – GitHub settings guide
- `.github/workflows/` – CI/CD pipeline definitions
