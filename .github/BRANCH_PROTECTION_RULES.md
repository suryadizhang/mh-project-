# GitHub Branch Protection Rules (Enterprise Standard)

**Project**: My Hibachi Monorepo  
**Applies To**: All 3 apps (Customer, Admin, Backend)  
**Last Updated**: November 17, 2025

---

## Overview

This document defines the **branch protection rules** required for
enterprise-grade development in our monorepo. These rules prevent
accidental damage to production and staging environments.

---

## Protected Branches

### 1. `main` (Production)

### 2. `dev` (Staging)

---

## Rule Set for `main` Branch

### ✅ Required

#### 1. Require Pull Request Reviews

- **Minimum approvals**: 1
- **Dismiss stale reviews**: ✅ Yes (when new commits pushed)
- **Require review from Code Owners**: ✅ Yes (see
  `.github/CODEOWNERS`)
- **Restrict who can dismiss reviews**: Admins only

#### 2. Require Status Checks to Pass

- **Require branches to be up to date**: ✅ Yes
- **Required status checks**:
  - `ci/customer-build` - Customer site build
  - `ci/customer-test` - Customer site tests
  - `ci/admin-build` - Admin panel build
  - `ci/admin-test` - Admin panel tests
  - `ci/backend-test` - Backend tests (pytest)
  - `ci/backend-lint` - Backend linting (ruff)
  - `ci/feature-flag-validation` - Feature flag existence check
  - `ci/type-check` - TypeScript + mypy validation

#### 3. Require Conversation Resolution

- ✅ All conversations must be resolved before merge

#### 4. Require Signed Commits

- ✅ All commits must be signed (GPG/SSH)

#### 5. Require Linear History

- ✅ Prevent merge commits
- **Merge strategy**: Squash and merge OR Rebase and merge
- **No merge commits allowed**

#### 6. Include Administrators

- ✅ Apply rules to administrators too

### ❌ Prohibited

- ❌ No force push
- ❌ No deletions
- ❌ No direct commits (must use PR)

---

## Rule Set for `dev` Branch

### ✅ Required

#### 1. Require Pull Request Reviews

- **Minimum approvals**: 1
- **Dismiss stale reviews**: ✅ Yes
- **Require review from Code Owners**: ⚠️ Optional (can be disabled
  for faster iteration)

#### 2. Require Status Checks to Pass

- **Require branches to be up to date**: ✅ Yes
- **Required status checks**:
  - `ci/customer-build`
  - `ci/customer-test`
  - `ci/admin-build`
  - `ci/admin-test`
  - `ci/backend-test`
  - `ci/backend-lint`
  - `ci/feature-flag-validation`

#### 3. Require Conversation Resolution

- ⚠️ Optional (can be disabled for faster iteration)

#### 4. Require Linear History

- ✅ Prevent merge commits
- **Merge strategy**: Squash and merge

### ❌ Prohibited

- ❌ No force push (except by admins in emergency)
- ❌ No deletions
- ❌ No direct commits (must use PR)

---

## Rule Set for `feature/*` Branches

### ✅ Allowed

- ✅ Direct commits (developer's working branch)
- ✅ Force push (developer can rewrite history)
- ✅ Deletions (after merge)

### ❌ Prohibited

- ❌ Cannot be set as base for PRs (must merge to `dev` first)

---

## Applying These Rules in GitHub

### Via GitHub Web UI

1. Go to **Settings** → **Branches**
2. Click **Add rule** or **Edit** existing rule
3. **Branch name pattern**: `main`
4. Enable the following:

```
☑ Require a pull request before merging
  ☑ Require approvals: 1
  ☑ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require review from Code Owners
  ☑ Restrict who can dismiss pull request reviews

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  ☑ Status checks that are required:
    - ci/customer-build
    - ci/customer-test
    - ci/admin-build
    - ci/admin-test
    - ci/backend-test
    - ci/backend-lint
    - ci/feature-flag-validation
    - ci/type-check

☑ Require conversation resolution before merging

☑ Require signed commits

☑ Require linear history

☑ Do not allow bypassing the above settings

☑ Restrict who can push to matching branches
  - Only allow: (leave empty to block all direct pushes)

☑ Lock branch (prevent any changes)
```

5. Click **Create** or **Save changes**
6. Repeat for `dev` branch with adjusted settings

---

### Via GitHub CLI

```bash
# Protect main branch
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_pull_request_reviews[dismiss_stale_reviews]=true \
  --field required_status_checks[strict]=true \
  --field required_status_checks[contexts][]=ci/customer-build \
  --field required_status_checks[contexts][]=ci/customer-test \
  --field required_status_checks[contexts][]=ci/admin-build \
  --field required_status_checks[contexts][]=ci/admin-test \
  --field required_status_checks[contexts][]=ci/backend-test \
  --field required_status_checks[contexts][]=ci/backend-lint \
  --field required_status_checks[contexts][]=ci/feature-flag-validation \
  --field enforce_admins=true \
  --field required_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false

# Protect dev branch (similar but slightly relaxed)
gh api repos/{owner}/{repo}/branches/dev/protection \
  --method PUT \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_pull_request_reviews[dismiss_stale_reviews]=true \
  --field required_status_checks[strict]=true \
  --field required_status_checks[contexts][]=ci/customer-build \
  --field required_status_checks[contexts][]=ci/customer-test \
  --field required_status_checks[contexts][]=ci/admin-build \
  --field required_status_checks[contexts][]=ci/admin-test \
  --field required_status_checks[contexts][]=ci/backend-test \
  --field required_status_checks[contexts][]=ci/backend-lint \
  --field enforce_admins=false \
  --field required_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

---

## CODEOWNERS File

Create `.github/CODEOWNERS` to enforce reviews from specific
teams/people:

```
# Global owners (entire monorepo)
* @suryadizhang @engineering-team

# Frontend owners
/apps/customer/ @suryadizhang @frontend-team
/apps/admin/ @suryadizhang @frontend-team

# Backend owners
/apps/backend/ @suryadizhang @backend-team

# Infrastructure & DevOps
/.github/workflows/ @suryadizhang @devops-team
/docker/ @suryadizhang @devops-team
/deploy*.sh @suryadizhang @devops-team

# Feature flags (require extra scrutiny)
**/*env.ts @suryadizhang @tech-lead
**/config.py @suryadizhang @tech-lead
.github/FEATURE_FLAGS.md @suryadizhang @tech-lead

# Critical business logic
/apps/backend/src/services/booking_service.py @suryadizhang @tech-lead
/apps/backend/src/services/pricing_service.py @suryadizhang @tech-lead
```

---

## Merge Strategies

### For `main` branch:

**Recommended**: **Squash and merge**

Why?

- Clean linear history
- Each PR = 1 commit on main
- Easier to revert if needed
- Better git log readability

### For `dev` branch:

**Recommended**: **Squash and merge** or **Rebase and merge**

Why?

- Keeps dev history clean
- Easier to cherry-pick fixes
- Simpler to track feature additions

### ❌ Never Use:

**Merge commit** (creates messy history with merge bubbles)

---

## Emergency Procedures

### Hotfix Process (Bypassing Rules)

In true production emergencies:

1. **Contact**: @suryadizhang (repository admin)
2. **Temporarily disable** branch protection
3. **Push hotfix directly** to `main`
4. **Re-enable** branch protection immediately
5. **Document** in incident log
6. **Backport** to `dev` branch

**This should be rare** (< 1% of deployments).

---

## Enforcement Timeline

### Phase 1 (Immediate):

- ✅ Enable for `main` branch
- ✅ Require status checks
- ✅ Require 1 approval

### Phase 2 (Week 2):

- ✅ Enable for `dev` branch
- ✅ Add signed commits requirement

### Phase 3 (Month 1):

- ✅ Add CODEOWNERS
- ✅ Require linear history
- ✅ Apply to administrators

---

## Monitoring & Compliance

### Weekly Audit:

- Check for any force pushes (should be none)
- Review bypassed rules (should be zero)
- Verify all PRs have required approvals

### Monthly Review:

- Adjust required status checks as needed
- Update CODEOWNERS
- Review emergency hotfix procedures

---

## FAQ

### Q: Can I push directly to `dev` for quick fixes?

**A**: No. All changes must go through PRs, even on `dev`. Use
`feature/quick-fix-*` branches.

### Q: What if CI is broken and blocking merges?

**A**: Fix CI first. Don't bypass checks. If urgent, contact admin for
temporary bypass.

### Q: Can I force push to my feature branch?

**A**: Yes! Feature branches have no protection. Rewrite history as
needed.

### Q: What if I need to merge multiple PRs quickly?

**A**: Queue them. GitHub will merge them in order once CI passes.
Don't bypass reviews.

### Q: What happens if I try to force push to `main`?

**A**: GitHub will reject it with an error. Branch protection prevents
this.

---

## References

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [CODEOWNERS Syntax](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Required Status Checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging)

---

**Maintained by**: @suryadizhang  
**Last Review**: November 17, 2025  
**Next Review**: December 17, 2025
