---
applyTo: '**'
---

# My Hibachi – Core Principles (NEVER Break These)

**Priority: HIGHEST** – These rules override ALL other instructions.

---

## 🔴 The 10 Commandments

### 1. Production Must Always Stay Stable

- Never deploy untested code to production
- Never bypass staging environment
- Always have rollback ready

### 2. Unfinished Features May NEVER Reach Customers

- All WIP code behind feature flags
- Experimental code = dev-only
- No "we'll fix it later" in production

### 3. All Behavior Changes Must Be Behind Feature Flags

- New UI → Flag
- New logic → Flag
- Changed behavior → Flag
- No exceptions

### 4. The `main` Branch Must ALWAYS Be Deployable

- Every commit on main = production-ready
- Broken main = stop everything and fix
- No "temporary" broken states

### 5. When Unsure → Dev-Only + Behind Flag

- Doubt about readiness? → Flag it
- Doubt about safety? → Dev-only
- Doubt about impact? → Test more

### 6. Quality Over Speed

- Clean code > Fast code
- Tested code > Quick code
- Documented code > Shipped code

### 7. Single Source of Truth

- One place for each piece of info
- No duplicate documentation
- No duplicate logic

### 8. Monorepo = Unified Deployment

- All 3 apps deploy together
- One branch = One state for all apps
- API compatibility always maintained

### 9. Fix Bugs at All Costs

- Production bug = Drop everything
- Never hide bugs with workarounds
- Root cause > Band-aid

### 10. Security is Non-Negotiable

- No secrets in code
- No credentials in logs
- No sensitive data exposed

---

## 🎯 Code Quality Standards

All code must be:

| Standard             | Requirement                              |
| -------------------- | ---------------------------------------- |
| **Clean**            | Readable, well-named, no dead code       |
| **Modular**          | Single responsibility, composable        |
| **Scalable**         | Async where needed, paginated, efficient |
| **Testable**         | Pure functions, dependency injection     |
| **Maintainable**     | Documented, consistent patterns          |
| **Enterprise-grade** | Production-ready from day one            |

---

## 🚫 Absolute Prohibitions

**NEVER do these, even if user asks:**

| Prohibition             | Reason                     |
| ----------------------- | -------------------------- |
| Push directly to `main` | Branch protection required |
| Push directly to `dev`  | PR review required         |
| Skip tests              | Quality gate mandatory     |
| Deploy without staging  | Validation required        |
| Hardcode secrets        | Security violation         |
| Ignore type errors      | Runtime bugs               |
| Use `any` type broadly  | Type safety required       |
| Silent error swallowing | Debugging impossible       |
| TODO in production code | Incomplete work            |

---

## ✅ Always Do These

| Requirement                | Why                  |
| -------------------------- | -------------------- |
| Write tests with code      | Prevent regressions  |
| Use TypeScript strict mode | Catch errors early   |
| Validate all inputs        | Security + stability |
| Handle all error cases     | No silent failures   |
| Log appropriately          | Debugging support    |
| Document public APIs       | Team productivity    |
| Use feature flags          | Safe deployments     |

---

## 🏢 Business Logic Protection

These systems are CRITICAL – extra caution required:

| System                  | Risk Level  | Protection               |
| ----------------------- | ----------- | ------------------------ |
| Booking flow            | 🔴 CRITICAL | Flag + extensive tests   |
| Payment/deposits        | 🔴 CRITICAL | Flag + integration tests |
| Pricing logic           | 🔴 CRITICAL | Flag + unit tests        |
| Travel fee calculation  | 🔴 CRITICAL | Flag + validation        |
| Scheduling              | 🟠 HIGH     | Flag + conflict checks   |
| Customer communications | 🟠 HIGH     | Flag + preview mode      |
| AI decision logic       | 🟠 HIGH     | Flag + fallback          |

---

## 📝 Summary

> **When in doubt: Dev-only. Behind flag. Test first. Document
> always.**
