# My Hibachi Feature Flag Standard (Unified)

**Version**: 1.0 **Last Updated**: November 17, 2025 **Applies To**:
Customer Site, Admin Panel, Backend API

---

## Overview

This document defines the **unified feature flag system** used across
all My Hibachi applications to safely deploy new features, experiment
with changes, and maintain production stability.

---

## 1. Naming Convention

### Format

```
FEATURE_<SCOPE>_<DESCRIPTION>_<VERSION>
```

### Components

**Scope** (Required):

- `NEW` - Brand new feature
- `BETA` - Experimental/testing
- `V2`, `V3` - Version upgrade
- `ADMIN` - Admin-only feature
- `CUSTOMER` - Customer-only feature
- `SHARED` - Used by multiple apps

**Description** (Required):

- Use UPPER_SNAKE_CASE
- Be descriptive but concise
- Max 40 characters

**Version** (Optional):

- Only if multiple versions exist
- Format: `_V2`, `_V3`, `_BETA`

### Examples

✅ **Good Names**:

```bash
FEATURE_NEW_BOOKING_CALENDAR
FEATURE_BETA_TRAVEL_FEE_CALCULATOR
FEATURE_V2_PRICING_ENGINE
FEATURE_ADMIN_DASHBOARD_ANALYTICS
FEATURE_CUSTOMER_PORTAL_BETA
FEATURE_SHARED_MULTI_CHEF_SCHEDULING
```

❌ **Bad Names**:

```bash
NEW_FEATURE                    # Too vague
booking_calendar              # Wrong case
EXPERIMENTAL_STUFF            # Not descriptive
feature_new_booking_calendar  # Wrong prefix
```

---

## 2. Environment-Specific Defaults

| Environment     | Default Value | Purpose                                       |
| --------------- | ------------- | --------------------------------------------- |
| **Production**  | `false`       | Safety first - nothing new enabled by default |
| **Staging**     | `true`        | Test all features before production           |
| **Development** | `true`        | Full access for developers                    |
| **Preview**     | `true`        | Show features in PR previews                  |

---

## 3. Implementation by App

### 3.1 Customer Site (Next.js)

**File**: `apps/customer/src/lib/env.ts`

```typescript
import { z } from 'zod';

const envSchema = z.object({
  // Environment
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
  NEXT_PUBLIC_ENV: z
    .enum(['development', 'staging', 'production'])
    .default('development'),

  // Feature Flags - Customer Site
  NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),

  NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),

  NEXT_PUBLIC_FEATURE_CUSTOMER_PORTAL_BETA: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),
});

export const env = envSchema.parse(process.env);

// Type-safe feature flag checker
export function isFeatureEnabled(flag: keyof typeof env): boolean {
  if (!flag.startsWith('NEXT_PUBLIC_FEATURE_')) {
    throw new Error(`Invalid feature flag: ${flag}`);
  }
  return env[flag] as boolean;
}
```

**Usage**:

```typescript
import { isFeatureEnabled } from "@/lib/env";

// In component
if (isFeatureEnabled("NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR")) {
  return <NewBookingCalendar />;
}
return <LegacyBookingCalendar />;
```

**Environment Files**:

```bash
# .env.local (development)
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=true
NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE=true

# .env.staging
NEXT_PUBLIC_ENV=staging
NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=true
NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE=true

# .env.production
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=false  # OFF by default
NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE=false     # OFF by default
```

---

### 3.2 Admin Panel (Next.js)

**File**: `apps/admin/src/lib/env.ts`

```typescript
import { z } from 'zod';

const envSchema = z.object({
  // Environment
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
  NEXT_PUBLIC_ENV: z
    .enum(['development', 'staging', 'production'])
    .default('development'),

  // Feature Flags - Admin Panel
  NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),

  NEXT_PUBLIC_FEATURE_ADMIN_ANALYTICS_BETA: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),

  NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING: z
    .enum(['true', 'false'])
    .default('false')
    .transform(val => val === 'true'),
});

export const env = envSchema.parse(process.env);

// Type-safe feature flag checker
export function isFeatureEnabled(flag: keyof typeof env): boolean {
  if (!flag.startsWith('NEXT_PUBLIC_FEATURE_')) {
    throw new Error(`Invalid feature flag: ${flag}`);
  }
  return env[flag] as boolean;
}
```

**Usage**:

```typescript
import { isFeatureEnabled } from "@/lib/env";

// In admin component
if (isFeatureEnabled("NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2")) {
  return <DashboardV2 />;
}
return <DashboardV1 />;
```

---

### 3.3 Backend (FastAPI)

**File**: `apps/backend/src/core/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with feature flags."""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Feature Flags - Backend
    FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR: bool = False
    FEATURE_FLAG_BETA_DYNAMIC_PRICING: bool = False
    FEATURE_FLAG_NEW_BOOKING_VALIDATION: bool = False
    FEATURE_FLAG_SHARED_MULTI_CHEF_SCHEDULING: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

def is_feature_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        flag_name: Name of the feature flag (without FEATURE_FLAG_ prefix)

    Returns:
        bool: True if enabled, False otherwise

    Raises:
        ValueError: If flag_name doesn't exist
    """
    settings = get_settings()
    full_flag_name = f"FEATURE_FLAG_{flag_name}"

    if not hasattr(settings, full_flag_name):
        raise ValueError(f"Unknown feature flag: {full_flag_name}")

    return getattr(settings, full_flag_name)
```

**Usage**:

```python
from src.core.config import is_feature_enabled

# In service
def calculate_travel_fee(distance: float) -> float:
    if is_feature_enabled("V2_TRAVEL_FEE_CALCULATOR"):
        return calculate_travel_fee_v2(distance)
    return calculate_travel_fee_legacy(distance)
```

**Environment Files**:

```bash
# .env.local (development)
ENVIRONMENT=development
FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR=true
FEATURE_FLAG_BETA_DYNAMIC_PRICING=true

# .env.staging
ENVIRONMENT=staging
FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR=true
FEATURE_FLAG_BETA_DYNAMIC_PRICING=true

# .env.production
ENVIRONMENT=production
FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR=false  # OFF by default
FEATURE_FLAG_BETA_DYNAMIC_PRICING=false     # OFF by default
```

---

## 4. Vercel Environment Variables

### Naming Convention

```
NEXT_PUBLIC_FEATURE_<NAME> = true | false
```

### Configuration Locations

1. **Vercel Dashboard** → Project Settings → Environment Variables
2. **Vercel CLI**:
   `vercel env add NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR`
3. **vercel.json**: Reference env vars in build settings

### Example vercel.json

```json
{
  "env": {
    "NEXT_PUBLIC_ENV": "production"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR": "false"
    }
  }
}
```

### Environment-Specific Settings

| Environment Type | Vercel Setting     | Default Flags |
| ---------------- | ------------------ | ------------- |
| Production       | `main` branch      | All `false`   |
| Preview          | `dev` branch       | All `true`    |
| Development      | Local `.env.local` | All `true`    |

---

## 5. Feature Flag Lifecycle

### Stage 1: Development

```bash
# Create flag (default: false in production)
FEATURE_NEW_BOOKING_CALENDAR=true  # Local only
```

### Stage 2: Staging

```bash
# Enable on staging for testing
NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=true  # Staging
```

### Stage 3: Gradual Rollout (Production)

```bash
# Enable for admins first
if (user.isAdmin && isFeatureEnabled("NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR")) {
  return <NewFeature />;
}

# Then enable for 10% of users
if (user.id % 10 === 0 && isFeatureEnabled("...")) {
  return <NewFeature />;
}

# Then enable for everyone
NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR=true  # Production
```

### Stage 4: Cleanup

```typescript
// After 2 weeks of stable production:
// 1. Remove flag checks from code
// 2. Remove env variable
// 3. Delete legacy code
```

---

## 6. Documentation Requirements

Every feature flag MUST have:

### 6.1 Inline Documentation

```typescript
/**
 * Feature Flag: NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR
 *
 * Purpose: Enables the new React-based booking calendar with improved UX
 * Status: Beta testing (staging only)
 * Created: 2025-11-15
 * Owner: @engineering-team
 *
 * Rollout Plan:
 * - [x] Staging (2025-11-15)
 * - [ ] Admin users (2025-11-20)
 * - [ ] 10% of customers (2025-11-25)
 * - [ ] 100% of customers (2025-12-01)
 *
 * Cleanup: Remove after 2 weeks of stable 100% rollout
 */
export const FEATURE_NEW_BOOKING_CALENDAR =
  'NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR';
```

### 6.2 Feature Flag Registry

**File**: `.github/FEATURE_FLAGS.md`

```markdown
# Active Feature Flags

| Flag                                     | App      | Status  | Created    | Owner | Cleanup Date |
| ---------------------------------------- | -------- | ------- | ---------- | ----- | ------------ |
| NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR | Customer | Beta    | 2025-11-15 | @team | 2025-12-15   |
| FEATURE_FLAG_V2_TRAVEL_FEE_CALCULATOR    | Backend  | Testing | 2025-11-10 | @team | TBD          |
```

---

## 7. Testing Requirements

Every feature behind a flag MUST have:

### 7.1 Unit Tests (Both States)

```typescript
describe('BookingCalendar', () => {
  it('renders new calendar when flag enabled', () => {
    mockFeatureFlag('NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR', true);
    // ... test new calendar
  });

  it('renders legacy calendar when flag disabled', () => {
    mockFeatureFlag(
      'NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR',
      false
    );
    // ... test legacy calendar
  });
});
```

### 7.2 Integration Tests

```python
def test_travel_fee_with_v2_flag():
    with override_feature_flag("V2_TRAVEL_FEE_CALCULATOR", True):
        fee = calculate_travel_fee(10.5)
        assert fee == expected_v2_fee

def test_travel_fee_without_v2_flag():
    with override_feature_flag("V2_TRAVEL_FEE_CALCULATOR", False):
        fee = calculate_travel_fee(10.5)
        assert fee == expected_legacy_fee
```

---

## 8. CI/CD Validation

See `.github/workflows/feature-flag-validation.yml` for automated
checks.

---

## 9. Quick Reference

### Adding a New Feature Flag

1. **Choose a name** (follow naming convention)
2. **Add to env schema** (customer/admin/backend)
3. **Set default to `false`** in production
4. **Document in code** (inline comment)
5. **Add to registry** (.github/FEATURE_FLAGS.md)
6. **Write tests** (both flag states)
7. **Deploy to staging first**
8. **Gradual production rollout**
9. **Clean up after 2 weeks**

### Checking Flag Status

```bash
# Customer/Admin (Next.js)
isFeatureEnabled("NEXT_PUBLIC_FEATURE_NAME")

# Backend (FastAPI)
is_feature_enabled("FEATURE_NAME")
```

---

## 10. Troubleshooting

### Flag Not Working in Production

- ✅ Check Vercel dashboard environment variables
- ✅ Verify `.env.production` has correct value
- ✅ Check for typos in flag name
- ✅ Ensure flag is in env schema
- ✅ Redeploy after changing env vars

### Flag Works Locally But Not in Vercel Preview

- ✅ Check `dev` branch environment variables
- ✅ Verify `NEXT_PUBLIC_` prefix (required for client-side)
- ✅ Check Vercel build logs for env var list

### TypeScript Error "Property does not exist"

- ✅ Add flag to `envSchema` in `env.ts`
- ✅ Restart TypeScript server
- ✅ Check for typos in flag name

---

**Questions?** See `01-AGENT_RULES.instructions.md` Section 3 or
contact @engineering-team
