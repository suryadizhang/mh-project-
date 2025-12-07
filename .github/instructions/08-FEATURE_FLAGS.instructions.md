---
applyTo: '**'
---

# My Hibachi – Feature Flag Rules

**Priority: HIGH** – ALL behavior changes must be behind flags.

---

## 🎯 Why Feature Flags?

1. **Safe deployments** – Deploy code, enable later
2. **Gradual rollout** – Enable for 10%, then 50%, then 100%
3. **Quick rollback** – Disable without redeploying
4. **A/B testing** – Compare versions
5. **Environment control** – Different behavior in staging vs prod

---

## 🚦 When to Use Feature Flags

### ALWAYS Flag:

| Change Type      | Example                    |
| ---------------- | -------------------------- |
| New UI           | New booking calendar       |
| New logic        | New pricing algorithm      |
| New endpoint     | New payment API            |
| Changed behavior | Different validation rules |
| New integration  | RingCentral setup          |
| AI features      | New AI model or prompt     |
| Admin tools      | New dashboard              |

### DON'T Need Flag:

| Change Type   | Example          |
| ------------- | ---------------- |
| Bug fix       | Fix null pointer |
| Refactor      | Rename variable  |
| Documentation | Update README    |
| Test          | Add unit test    |
| Style         | Format code      |

---

## 📁 Flag Locations

### Backend (FastAPI):

**File:** `apps/backend/src/core/config.py`

```python
class Settings(BaseSettings):
    # Feature Flags
    FEATURE_STRIPE_ENABLED: bool = False
    FEATURE_AI_CHAT_ENABLED: bool = False
    FEATURE_RINGCENTRAL_ENABLED: bool = False
    FEATURE_LOYALTY_PROGRAM: bool = False
```

**Usage:**

```python
from core.config import settings

if settings.FEATURE_AI_CHAT_ENABLED:
    response = await ai_service.generate_response(message)
else:
    response = "AI chat is not available"
```

### Frontend (Next.js):

**File:** `apps/customer/src/lib/env.ts`

```typescript
export const featureFlags = {
  newBookingCalendar:
    process.env.NEXT_PUBLIC_FEATURE_NEW_CALENDAR === 'true',
  loyaltyProgram: process.env.NEXT_PUBLIC_FEATURE_LOYALTY === 'true',
  aiChat: process.env.NEXT_PUBLIC_FEATURE_AI_CHAT === 'true',
};
```

**Usage:**

```tsx
import { featureFlags } from '@/lib/env';

function BookingPage() {
  return (
    <div>
      {featureFlags.newBookingCalendar ? (
        <NewCalendar />
      ) : (
        <LegacyCalendar />
      )}
    </div>
  );
}
```

---

## 📝 Flag Naming Convention

### Format:

```
FEATURE_<AREA>_<DESCRIPTION>
```

### Examples:

| Flag                         | Purpose                |
| ---------------------------- | ---------------------- |
| `FEATURE_STRIPE_ENABLED`     | Enable Stripe payments |
| `FEATURE_AI_CHAT_ENABLED`    | Enable AI chat         |
| `FEATURE_BOOKING_V2`         | New booking flow       |
| `FEATURE_LOYALTY_PROGRAM`    | Loyalty points system  |
| `FEATURE_RINGCENTRAL_VOICE`  | Voice integration      |
| `FEATURE_ADMIN_DASHBOARD_V2` | New admin UI           |

---

## 🔄 Flag Lifecycle

```
1. CREATE (feature/batch-X)
   │
   ▼
2. OFF in production, ON in dev
   │
   ▼
3. MERGE to main (flag still OFF)
   │
   ▼
4. ENABLE gradually (10% → 50% → 100%)
   │
   ▼
5. STABLE for 2+ weeks
   │
   ▼
6. REMOVE flag, keep feature code
```

---

## 📊 Default Values by Environment

| Environment | Default | Notes                  |
| ----------- | ------- | ---------------------- |
| Local       | `true`  | Enable all for testing |
| Staging     | `true`  | Test with flags on     |
| Production  | `false` | Enable explicitly      |

---

## ✅ Flag Implementation Checklist

Before merging code with new flag:

- [ ] Flag defined in config file
- [ ] Default is `false` for production
- [ ] Environment variable documented
- [ ] Flag used consistently in all related code
- [ ] Legacy code preserved (fallback works)
- [ ] Tests exist for both flag states

---

## 📋 Flags by Batch

### Batch 1:

```env
FEATURE_CORE_API=true
FEATURE_AUTH=true
FEATURE_CLOUDFLARE_TUNNEL=true
FEATURE_RBAC=true
FEATURE_AUDIT_TRAIL=true
FEATURE_SOFT_DELETE=true
FEATURE_FAILED_BOOKING_LEAD_CAPTURE=true
```

### Batch 2:

```env
FEATURE_STRIPE_ENABLED=true
FEATURE_DYNAMIC_PRICING=true
FEATURE_TAX_COLLECTION=true
```

### Batch 3:

```env
FEATURE_AI_CORE=true
FEATURE_OPENAI=true
FEATURE_SMART_ESCALATION=true
```

### Batch 4:

```env
FEATURE_RINGCENTRAL=true
FEATURE_VOICE_AI=true
FEATURE_DEEPGRAM=true
FEATURE_META_WHATSAPP=true
```

### Batch 5:

```env
FEATURE_ADVANCED_AI=true
FEATURE_EMOTION_DETECTION=true
FEATURE_MARKETING_INTELLIGENCE=true
FEATURE_CUSTOMER_REVIEWS=true
```

### Batch 6:

```env
FEATURE_MULTI_LLM=true
FEATURE_SHADOW_LEARNING=true
FEATURE_LOYALTY_PROGRAM=true
```

---

## ⚠️ Flag Anti-Patterns

| Don't                        | Do Instead              |
| ---------------------------- | ----------------------- |
| Default to `true` in prod    | Default to `false`      |
| Remove flag immediately      | Keep for 2+ weeks       |
| Nest flags deeply            | Flat, clear flag checks |
| Check flag in every function | Check at entry point    |
| Forget legacy fallback       | Always provide fallback |

---

## 🧹 Flag Cleanup Process

When removing a flag:

1. Verify feature stable 2+ weeks
2. Remove all flag checks in code
3. Remove legacy/fallback code
4. Remove env variable
5. Update documentation
6. Commit: `chore: remove FEATURE_X flag`

---

## 🔗 Related Docs

- `docs/06-QUICK_REFERENCE/FEATURE_FLAGS.md` – Complete flag list
- `apps/backend/src/core/config.py` – Backend flags
- `apps/customer/src/lib/env.ts` – Frontend flags
