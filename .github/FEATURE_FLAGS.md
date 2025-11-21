# Feature Flag Registry

This document tracks all active feature flags across the My Hibachi
monorepo.

**Last Updated**: 2025-01-13

---

## Overview

| Status            | Customer | Admin | Backend | Total |
| ----------------- | -------- | ----- | ------- | ----- |
| 🟢 Active         | 6        | 7     | 16      | 29    |
| 🟡 In Rollout     | 0        | 0     | 0       | 0     |
| 🔴 Cleanup Needed | 0        | 0     | 0       | 0     |

---

## Active Feature Flags

### Customer Site (`apps/customer/`)

| Flag Name                                          | Status      | Created    | Owner         | Rollout Plan    | Cleanup Date | Notes                                                 |
| -------------------------------------------------- | ----------- | ---------- | ------------- | --------------- | ------------ | ----------------------------------------------------- |
| `NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR`         | 🔴 Dev-only | 2025-01-13 | Backend Team  | Staging Q1 2025 | TBD          | New booking calendar UI with improved UX              |
| `NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE`            | 🔴 Dev-only | 2025-01-13 | Backend Team  | Staging Q1 2025 | TBD          | New pricing calculation engine with dynamic pricing   |
| `NEXT_PUBLIC_FEATURE_CUSTOMER_PORTAL_BETA`         | 🔴 Dev-only | 2025-01-13 | Frontend Team | Staging Q2 2025 | TBD          | Customer self-service portal for bookings management  |
| `NEXT_PUBLIC_FEATURE_NEW_MENU_SELECTOR`            | 🔴 Dev-only | 2025-01-13 | Frontend Team | Staging Q1 2025 | TBD          | Enhanced menu selection interface                     |
| `NEXT_PUBLIC_FEATURE_BETA_PAYMENT_FLOW`            | 🔴 Dev-only | 2025-01-13 | Backend Team  | Staging Q2 2025 | TBD          | New payment flow with Stripe integration improvements |
| `NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING` | 🔴 Dev-only | 2025-01-13 | Backend Team  | Staging Q2 2025 | TBD          | **SHARED**: Multi-chef scheduling system              |

---

### Admin Panel (`apps/admin/`)

| Flag Name                                          | Status      | Created    | Owner            | Rollout Plan    | Cleanup Date | Notes                                                     |
| -------------------------------------------------- | ----------- | ---------- | ---------------- | --------------- | ------------ | --------------------------------------------------------- |
| `NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2`           | 🔴 Dev-only | 2025-01-13 | Frontend Team    | Staging Q1 2025 | TBD          | New admin dashboard with improved analytics               |
| `NEXT_PUBLIC_FEATURE_ADMIN_ANALYTICS_BETA`         | 🔴 Dev-only | 2025-01-13 | Data Team        | Staging Q2 2025 | TBD          | Advanced analytics and reporting features                 |
| `NEXT_PUBLIC_FEATURE_ADMIN_BOOKING_MANAGER_V2`     | 🔴 Dev-only | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | Enhanced booking management interface                     |
| `NEXT_PUBLIC_FEATURE_ADMIN_TRAVEL_FEE_EDITOR`      | 🔴 Dev-only | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | Visual travel fee editor with map                         |
| `NEXT_PUBLIC_FEATURE_ADMIN_AI_INSIGHTS`            | 🔴 Dev-only | 2025-01-13 | AI Team          | Staging Q2 2025 | TBD          | **SHARED**: AI-powered admin insights and recommendations |
| `NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING` | 🔴 Dev-only | 2025-01-13 | Backend Team     | Staging Q2 2025 | TBD          | **SHARED**: Multi-chef scheduling system                  |
| `NEXT_PUBLIC_FEATURE_SHARED_ONEDRIVE_SYNC`         | 🔴 Dev-only | 2025-01-13 | Integration Team | Staging Q2 2025 | TBD          | **SHARED**: OneDrive Excel sync                           |

---

### Backend API (`apps/backend/`)

| Flag Name                                   | Status            | Created    | Owner            | Rollout Plan    | Cleanup Date | Notes                                                           |
| ------------------------------------------- | ----------------- | ---------- | ---------------- | --------------- | ------------ | --------------------------------------------------------------- |
| `FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR`     | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | New travel fee calculation with improved accuracy               |
| `FEATURE_FLAG_BETA_DYNAMIC_PRICING`         | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | Dynamic pricing based on demand/season                          |
| `FEATURE_FLAG_NEW_BOOKING_VALIDATION`       | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | Enhanced booking validation with race condition fixes (Bug #13) |
| `FEATURE_FLAG_V2_DEPOSIT_CALCULATION`       | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q1 2025 | TBD          | New deposit calculation logic                                   |
| `FEATURE_FLAG_SHARED_MULTI_CHEF_SCHEDULING` | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q2 2025 | TBD          | **SHARED**: Multi-chef scheduling system                        |
| `FEATURE_FLAG_BETA_SMART_AVAILABILITY`      | 🔴 Dev-only       | 2025-01-13 | AI Team          | Staging Q2 2025 | TBD          | AI-powered availability suggestions                             |
| `FEATURE_FLAG_ADMIN_AI_INSIGHTS`            | 🔴 Dev-only       | 2025-01-13 | AI Team          | Staging Q2 2025 | TBD          | **SHARED**: AI-powered admin insights                           |
| `FEATURE_FLAG_BETA_AI_CUSTOMER_TONE`        | 🔴 Dev-only       | 2025-01-13 | AI Team          | Staging Q2 2025 | TBD          | Adaptive AI tone based on customer profile                      |
| `FEATURE_FLAG_V2_AI_BOOKING_ASSISTANT`      | 🔴 Dev-only       | 2025-01-13 | AI Team          | Staging Q2 2025 | TBD          | Enhanced AI booking assistance                                  |
| `FEATURE_FLAG_SHARED_ONEDRIVE_SYNC`         | 🔴 Dev-only       | 2025-01-13 | Integration Team | Staging Q2 2025 | TBD          | **SHARED**: OneDrive Excel sync                                 |
| `FEATURE_FLAG_BETA_STRIPE_CONNECT`          | 🔴 Dev-only       | 2025-01-13 | Backend Team     | Staging Q3 2025 | TBD          | Stripe Connect for multi-chef payments                          |
| `FEATURE_FLAG_NEW_RINGCENTRAL_INTEGRATION`  | 🔴 Dev-only       | 2025-01-13 | Integration Team | Staging Q2 2025 | TBD          | Enhanced RingCentral SMS integration                            |
| `FEATURE_FLAG_ENABLE_RATE_LIMITING`         | 🟢 Enabled (Prod) | 2025-01-13 | Security Team    | Production      | N/A          | Rate limiting for API endpoints (security)                      |
| `FEATURE_FLAG_ENABLE_FIELD_ENCRYPTION`      | 🔴 Dev-only       | 2025-01-13 | Security Team    | Staging Q2 2025 | TBD          | Field-level encryption for sensitive data                       |
| `FEATURE_FLAG_ENABLE_AUDIT_LOGGING`         | 🔴 Dev-only       | 2025-01-13 | Security Team    | Staging Q2 2025 | TBD          | Detailed audit logging for compliance                           |

---

## Shared Flags (Must Sync Across Apps)

These flags **MUST** exist in ALL affected apps with matching default
values:

| Flag Name                                   | Customer | Admin | Backend | Purpose                                    |
| ------------------------------------------- | -------- | ----- | ------- | ------------------------------------------ |
| `FEATURE_FLAG_SHARED_MULTI_CHEF_SCHEDULING` | ✅       | ✅    | ✅      | Multi-chef scheduling system               |
| `FEATURE_FLAG_SHARED_ONEDRIVE_SYNC`         | ❌       | ✅    | ✅      | OneDrive Excel sync (admin + backend only) |
| `FEATURE_FLAG_ADMIN_AI_INSIGHTS`            | ❌       | ✅    | ✅      | AI insights (admin + backend only)         |

---

## Status Definitions

| Status         | Icon | Description                                                      |
| -------------- | ---- | ---------------------------------------------------------------- |
| Dev-only       | 🔴   | Flag exists, default OFF, only enabled in dev/staging            |
| In Rollout     | 🟡   | Flag enabled in production for subset of users (gradual rollout) |
| Enabled (Prod) | 🟢   | Flag enabled in production for all users                         |
| Cleanup Needed | ⚠️   | Flag ready for removal (feature stable, no longer needed)        |

---

## Lifecycle Stages

Each flag progresses through these stages:

1. **Development** (🔴 Dev-only)
   - Flag created, default = `false`
   - Only enabled in dev environment
   - Testing in progress

2. **Staging** (🔴 Dev-only)
   - Flag enabled in staging
   - QA and integration testing
   - Still OFF in production

3. **Gradual Rollout** (🟡 In Rollout)
   - Flag ON in production for small % of users
   - Monitoring metrics and errors
   - Incrementally increase %

4. **Fully Enabled** (🟢 Enabled)
   - Flag ON for 100% of production users
   - Feature is stable
   - Keep flag for 2 weeks for quick rollback

5. **Cleanup** (⚠️ Cleanup Needed)
   - 2+ weeks stable in production
   - Create PR to remove flag
   - Remove from code + env configs

---

## Adding a New Flag

When adding a new feature flag:

1. **Choose Scope**:
   - `NEW` = Brand new feature
   - `V2`/`V3` = New version of existing feature
   - `BETA` = Experimental/preview feature
   - `ADMIN` = Admin-only feature
   - `CUSTOMER` = Customer-facing feature
   - `SHARED` = Used across multiple apps

2. **Add to All Affected Apps**:
   - Customer: `apps/customer/src/lib/env.ts`
   - Admin: `apps/admin/src/lib/env.ts`
   - Backend: `apps/backend/src/core/config.py`

3. **Update This Registry**:
   - Add row to appropriate section
   - Set status to 🔴 Dev-only
   - Fill in owner, rollout plan

4. **Document Rollout Plan**:
   - Target dates for staging → production
   - Success metrics
   - Rollback criteria

5. **Write Tests**:
   - Test both flag states (ON and OFF)
   - Verify fallback behavior works

---

## Removing a Flag

When removing a feature flag:

1. **Verify Stability** (2+ weeks in production)
2. **Create PR** with changes:
   - Remove flag from all env files
   - Remove conditional logic (keep new behavior)
   - Update tests (remove flag checks)
3. **Update This Registry** (remove row)
4. **Deploy** following normal process

---

## Monitoring

### CI/CD Validation

The monorepo CI/CD workflow validates:

- ✅ Shared flags exist in ALL apps
- ✅ Default values match across apps
- ✅ Naming conventions followed
- ✅ No undefined flags referenced in code

See: `.github/workflows/monorepo-ci.yml`

### Production Monitoring

Monitor feature flag usage:

- **Datadog/Sentry**: Tag errors by feature flag state
- **Analytics**: Track feature adoption rates
- **Alerts**: Flag-related errors trigger notifications

---

## References

- **Standard**: `.github/FEATURE_FLAG_STANDARD.md`
- **Rulebook**: `.github/instructions/01-AGENT_RULES.instructions.md`
  (Section 3)
- **CI/CD**: `.github/workflows/monorepo-ci.yml`
  (feature-flag-validation job)
- **Customer Flags**: `apps/customer/src/lib/env.ts`
- **Admin Flags**: `apps/admin/src/lib/env.ts`
- **Backend Flags**: `apps/backend/src/core/config.py`

---

## Questions?

Contact the Dev Team lead or see `.github/FEATURE_FLAG_STANDARD.md`
for detailed guidance.
