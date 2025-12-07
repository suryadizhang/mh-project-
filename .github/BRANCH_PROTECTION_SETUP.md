# 🔒 Branch Protection Setup Guide

This guide explains how to configure GitHub branch protection rules
for enterprise-grade security. **You must apply these settings in the
GitHub UI** (Settings → Branches → Branch protection rules).

---

## 📌 Why Branch Protection?

Without branch protection:

- ❌ Anyone can push directly to `main` or `dev`
- ❌ PRs can be merged without reviews
- ❌ Broken code can reach production
- ❌ No audit trail for changes

With branch protection:

- ✅ All changes require Pull Requests
- ✅ Mandatory code reviews before merge
- ✅ CI tests must pass before merge
- ✅ Clear audit trail for compliance

---

## 🔴 CRITICAL: Protect `main` Branch (Production)

### Step-by-Step Setup

1. Go to: **GitHub Repository → Settings → Branches**
2. Click **"Add branch protection rule"**
3. Enter branch name pattern: `main`

### Required Settings (Check ALL)

```
☑️ Require a pull request before merging
   ├── ☑️ Require approvals: 1 (or 2 for critical repos)
   ├── ☑️ Dismiss stale pull request approvals when new commits are pushed
   ├── ☑️ Require review from Code Owners
   └── ☐ Require approval of the most recent reviewable push (optional)

☑️ Require status checks to pass before merging
   ├── ☑️ Require branches to be up to date before merging
   └── Required checks:
       • Run Tests (from deploy-backend.yml)
       • [Add any linting/security checks]

☑️ Require conversation resolution before merging

☑️ Require signed commits (recommended for enterprise)

☑️ Require linear history (prevents merge commits)

☑️ Do not allow bypassing the above settings
   └── Even admins must follow rules

☐ Allow force pushes: NEVER for main
☐ Allow deletions: NEVER for main
```

### Screenshot Reference

```
┌─────────────────────────────────────────────────────────────────┐
│ Branch protection rule: main                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ☑️ Require a pull request before merging                       │
│     Required approving reviews: [1 ▼]                           │
│     ☑️ Dismiss stale approvals                                  │
│     ☑️ Require review from Code Owners                          │
│                                                                  │
│  ☑️ Require status checks to pass                               │
│     ☑️ Require branches to be up to date                        │
│     Status checks found in the last week:                       │
│     ┌──────────────────────────────────────┐                    │
│     │ ☑️ Run Tests                         │                    │
│     │ ☑️ Deploy to VPS                     │                    │
│     │ ☑️ Smoke Tests                       │                    │
│     └──────────────────────────────────────┘                    │
│                                                                  │
│  ☑️ Require conversation resolution                             │
│  ☑️ Do not allow bypassing the above settings                   │
│                                                                  │
│  ☐ Allow force pushes                                           │
│  ☐ Allow deletions                                              │
│                                                                  │
│                              [Create] [Cancel]                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🟠 Protect `dev` Branch (Staging)

### Step-by-Step Setup

1. Go to: **GitHub Repository → Settings → Branches**
2. Click **"Add branch protection rule"**
3. Enter branch name pattern: `dev`

### Required Settings

```
☑️ Require a pull request before merging
   ├── ☑️ Require approvals: 1
   └── ☐ Require review from Code Owners (optional for dev)

☑️ Require status checks to pass before merging
   └── Required checks:
       • Run Tests

☐ Require signed commits (optional for dev)

☑️ Require linear history

☐ Do not allow bypassing (can allow for emergencies)

☐ Allow force pushes: Only for admins in emergencies
☐ Allow deletions: NEVER
```

---

## 🟢 Feature Branches (No Protection Needed)

Feature branches (`feature/*`) don't need protection rules because:

- They are short-lived
- They must go through `dev` first (which is protected)
- Developers need flexibility during development

---

## 📋 Required Status Checks Reference

These are the CI jobs that must pass before merging:

### For `main` branch (Production)

| Check Name    | Workflow File      | Purpose                |
| ------------- | ------------------ | ---------------------- |
| Run Tests     | deploy-backend.yml | Unit tests             |
| Deploy to VPS | deploy-backend.yml | Deployment success     |
| Smoke Tests   | deploy-backend.yml | Post-deploy validation |

### For `dev` branch (Staging)

| Check Name        | Workflow File              | Purpose               |
| ----------------- | -------------------------- | --------------------- |
| Run Tests         | deploy-backend-staging.yml | Unit + integration    |
| Deploy to Staging | deploy-backend-staging.yml | Staging deployment    |
| E2E Tests         | deploy-backend-staging.yml | End-to-end validation |

---

## 🔐 CODEOWNERS Integration

Your existing `CODEOWNERS` file automatically assigns reviewers:

```
# .github/CODEOWNERS
* @suryadizhang

/apps/admin/     @suryadizhang
/apps/customer/  @suryadizhang
/apps/backend/   @suryadizhang
```

When "Require review from Code Owners" is enabled:

- PRs touching `/apps/backend/` require review from `@suryadizhang`
- This ensures the right person reviews each change

---

## 🚨 Emergency Bypass Procedure

If you need to bypass protection in an emergency:

### Option 1: Admin Override (if allowed)

1. Admin with bypass permission merges directly
2. Create issue documenting the bypass
3. Follow up with proper PR for audit trail

### Option 2: Temporary Rule Disable

1. Go to Settings → Branches → Edit rule
2. Uncheck "Do not allow bypassing"
3. Make emergency change
4. **IMMEDIATELY** re-enable the rule
5. Document in incident report

### Never Do This

- ❌ Leave bypass enabled
- ❌ Skip documentation
- ❌ Make emergency changes without notification

---

## ✅ Verification Checklist

After setting up branch protection, verify:

```
□ Try pushing directly to main - should be BLOCKED
□ Try pushing directly to dev - should be BLOCKED
□ Create PR to dev - should work
□ PR without tests passing - should be BLOCKED from merge
□ PR without approval - should be BLOCKED from merge
□ Approved PR with passing tests - should be MERGEABLE
```

---

## 📚 Related Documentation

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Required Status Checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging)

---

**Document Status:** Ready to Apply **Last Updated:** December 6, 2025
**Action Required:** Apply settings in GitHub UI
