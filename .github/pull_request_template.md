# Pull Request

## 📋 Change Summary

<!-- Provide a clear and concise description of your changes -->

**Related Issues**:

<!-- Link to related issues using #issue-number -->

## 🎯 Change Type

<!-- Check all that apply -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing
      functionality to change)
- [ ] 📝 Documentation update
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] 🎨 UI/UX improvements
- [ ] ⚡ Performance improvements
- [ ] 🔒 Security improvements
- [ ] 🧪 Test improvements
- [ ] 🔧 Configuration changes

---

## 🏢 Monorepo Impact

---

## 🏢 Monorepo Impact

**Apps Affected** (check all that apply):

- [ ] 🌐 Customer Site (`apps/customer/`)
- [ ] 👨‍💼 Admin Panel (`apps/admin/`)
- [ ] 🔌 Backend API (`apps/backend/`)
- [ ] 📦 Shared packages/utilities

**Cross-App Dependencies**:

<!-- Explain how changes in one app affect others (API contracts, shared types, feature flags) -->

---

## 🚩 Feature Flag Compliance

**Feature Flags** (check all that apply):

- [ ] ✅ No new functionality (doc/test/refactor only)
- [ ] 🚩 Added new feature flag(s) - list below
- [ ] 🔄 Modified existing feature flag(s) - list below
- [ ] 🗑️ Removed feature flag(s) - list below

**Flag Details** (if applicable):

<!-- List all feature flags added/modified/removed -->

| Flag Name               | App(s)   | Default (prod) | Purpose           |
| ----------------------- | -------- | -------------- | ----------------- |
| `NEXT_PUBLIC_FEATURE_X` | Customer | `false`        | Enables X feature |
| `FEATURE_FLAG_Y`        | Backend  | `false`        | Enables Y logic   |

**Feature Flag Checklist**:

- [ ] Flags follow naming convention:
      `FEATURE_<SCOPE>_<DESCRIPTION>_<VERSION>`
- [ ] Defaults are `false` in production environments
- [ ] New flags added to:
  - [ ] `apps/customer/src/lib/env.ts` (if customer affected)
  - [ ] `apps/admin/src/lib/env.ts` (if admin affected)
  - [ ] `apps/backend/src/core/config.py` (if backend affected)
- [ ] Shared flags (FEATURE*SHARED*\*) exist in ALL apps with matching
      defaults
- [ ] Legacy fallback behavior works when flag is OFF
- [ ] New behavior only active when flag is ON
- [ ] Flag documented in `.github/FEATURE_FLAGS.md` registry
- [ ] Tests cover BOTH flag states (enabled + disabled)
- [ ] Rollout plan documented (dev → staging → gradual production)

---

## 🔍 A–H Deep Audit Compliance

**I have applied ALL 8 audit techniques** (required before requesting
review):

- [ ] **A. Static Analysis** - Line-by-line syntax, types, imports,
      dead code, validation
- [ ] **B. Runtime Simulation** - Datetime issues, None propagation,
      type coercion, exceptions
- [ ] **C. Concurrency & Transaction Safety** - Race conditions
      (TOCTOU), locking, idempotency
- [ ] **D. Data Flow Tracing** - Input → processing → output
      validation
- [ ] **E. Error Path & Exception Handling** - Proper try/except, no
      silent failures
- [ ] **F. Dependency & Enum Validation** - All imported symbols/enums
      exist
- [ ] **G. Business Logic Validation** - Pricing, booking, travel
      fees, scheduling correctness
- [ ] **H. Helper/Utility Analysis** - Private method validation, edge
      cases

**Audit Findings**:

<!-- Summarize what you found during self-audit -->

**Severity Classification**:

- 🔴 CRITICAL:
  <!-- Production-breaking, data loss, security issues -->
- 🟠 HIGH: <!-- Major functionality broken, bad UX -->
- 🟡 MEDIUM: <!-- Minor bugs, edge cases -->
- 🟢 LOW: <!-- Code quality, optimization -->

**All findings resolved**:

<!-- Yes/No - explain any remaining issues -->

---

## 🎨 Affected Areas (Legacy Section - Use Monorepo Impact Above)

<!-- Check all areas that your changes affect -->

- [ ] Customer App (`apps/customer`)
- [ ] Admin Dashboard (`apps/admin`)
- [ ] Core API (`apps/api`)
- [ ] AI API (`apps/ai-api`)
- [ ] Shared Packages (`packages/`)
- [ ] Infrastructure (`docker/`, `.github/`, etc.)
- [ ] Documentation (`docs/`, `README.md`)
- [ ] Database Schema/Migrations
- [ ] Testing (unit, integration, e2e)

## 🔗 Related Issues

<!-- Link to any related issues -->

Fixes #(issue_number) Closes #(issue_number) Related to
#(issue_number)

## 🧪 Testing

<!-- Describe the tests you've added or run -->

**Test Coverage**:

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated (if applicable)
- [ ] Manual testing completed
- [ ] All existing tests pass

**Test Results**:

```
Customer Site:
  ✅ Build: Passing
  ✅ Tests: XX/XX passing
  ✅ Coverage: XX%

Admin Panel:
  ✅ Build: Passing
  ✅ Tests: XX/XX passing
  ✅ Coverage: XX%

Backend API:
  ✅ Tests: XX/XX passing
  ✅ Coverage: XX%
  ✅ Type Check: Passing
```

**Critical Logic Tests** (if applicable):

- [ ] Booking flow
- [ ] Travel fee calculation
- [ ] Pricing logic
- [ ] Deposit handling
- [ ] Scheduling/availability
- [ ] Payment processing
- [ ] AI decision logic

---

## 🏢 Enterprise Rulebook Compliance

**I confirm that I have followed** (see
`.github/instructions/01-AGENT_RULES.instructions.md`):

**Core Principles** (Section 0):

- [ ] Production stability maintained
- [ ] No unfinished features exposed to customers
- [ ] New behavior behind feature flags
- [ ] `main` branch remains deployable
- [ ] Code is clean, modular, scalable, testable, maintainable

**Monorepo Branching** (Section 2):

- [ ] Used unified branch model (main/dev/feature/\*)
- [ ] NOT separate branches per app
- [ ] Changes across multiple apps in ONE PR (if applicable)
- [ ] All affected apps build/test together

**Feature Flag Rules** (Section 3):

- [ ] Flags exist in all affected layers
- [ ] Defaults = OFF in production
- [ ] New logic behind flags
- [ ] Legacy fallback works
- [ ] Tests exist for both states

**Readiness Classification** (Sections 4-5):

- [ ] No TODO/FIXME/debug logs
- [ ] Passed all checklist items

**Critical Logic Protection** (Section 6):

- [ ] High-risk systems use feature flags (booking, pricing, travel
      fees, deposits)
- [ ] Input validation in place
- [ ] Fallback behavior defined
- [ ] No silent behavior changes

**CI/CD Compliance** (Section 8):

- [ ] All CI checks passing
- [ ] Environment configs match branch (dev/staging/prod)
- [ ] Feature flags match env configs

---

## 🔍 Code Quality Standards

**I confirm that this code is**:

- [ ] ✨ **Clean** - No dead code, good naming, clear structure
- [ ] 🧩 **Modular** - Proper separation of concerns, reusable
      components
- [ ] 📈 **Scalable** - Handles growth in data/traffic
- [ ] 🔍 **Testable** - Unit testable, no hard dependencies
- [ ] 🛠️ **Maintainable** - Well-documented, easy to understand
- [ ] 🏢 **Enterprise-grade** - Production-ready, follows best
      practices

**No debug artifacts**:

- [ ] No `console.log()` / `print()` statements (except in designated
      logging)
- [ ] No `TODO` / `FIXME` / `HACK` comments (unless documented with
      ticket)
- [ ] No commented-out code blocks
- [ ] No test-only code paths in production logic

## 📸 Screenshots/Videos

<!-- Add screenshots or videos for UI changes -->
<!-- Before/After comparisons are especially helpful -->

## 🔄 Database Changes

<!-- If your changes affect the database -->

- [ ] No database changes
- [ ] Schema migrations included
- [ ] Data migrations included
- [ ] Rollback plan documented
- [ ] Performance impact assessed

---

## 🔒 Breaking Changes

**Does this PR introduce breaking changes?**

- [ ] ✅ No breaking changes
- [ ] ⚠️ Yes - breaking changes documented below

**Breaking Change Details** (if applicable):

<!-- Describe what breaks and migration path for dependent code -->

---

## 🚀 Deployment Readiness

**Environment Configuration**:

- [ ] `.env.example` updated with new variables (if any)
- [ ] Vercel environment variables documented
- [ ] Backend environment variables documented
- [ ] No hardcoded secrets (all via env vars)

**Production Safety**:

- [ ] Changes behind feature flag (if new functionality)
- [ ] Backwards compatible (or breaking changes documented)
- [ ] No performance regressions
- [ ] No security vulnerabilities introduced
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Monitoring/alerts considered

**Deployment Order** (if coordination required):

- [ ] ✅ All apps deploy together (standard)
- [ ] ⚠️ Requires specific order - explain below

**Rollout Plan**:

1. Deploy to `dev` branch (staging)
2. Test with feature flags ON
3. Merge to `main` (production)
4. Feature flags remain OFF in production
5. Gradual rollout: <!-- Describe plan -->

---

## 📚 Documentation Updates

- [ ] ✅ No documentation changes needed
- [ ] 📖 README updated
- [ ] 📝 API documentation updated
- [ ] 🎓 User guide updated
- [ ] 💻 Code comments added/updated
- [ ] 🏗️ Architecture diagrams updated
- [ ] 📋 Feature flag registry updated

---

## ✅ Pre-Submission Checklist Summary

Before requesting review, I confirm:

- [ ] ✅ Applied A–H audit methodology (all 8 techniques)
- [ ] ✅ Feature flags implemented correctly (if applicable)
- [ ] ✅ Tests written and passing
- [ ] ✅ Documentation updated
- [ ] ✅ CI/CD checks passing
- [ ] ✅ Enterprise rulebook followed
- [ ] ✅ No debug artifacts
- [ ] ✅ Production-ready code quality

---

## 👀 Reviewer Guidance

**Focus Areas for Review**:

<!-- Tell reviewers what to pay attention to -->

**Testing Instructions**:

<!-- Step-by-step guide to test this PR -->

## 📸 Screenshots/Videos

<!-- Add screenshots or videos for UI changes -->
<!-- Before/After comparisons are especially helpful -->

---

## 💬 Additional Notes

<!-- Any other information reviewers should know -->
