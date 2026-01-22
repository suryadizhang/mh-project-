---
applyTo: '**'
---

# My Hibachi – SSoT (Single Source of Truth) Patterns

**Priority: CRITICAL** – ALL business values MUST come from SSoT.
**Version:** 1.0.0 **Created:** 2025-01-30

---

## 🎯 Purpose

This document defines canonical patterns for working with dynamic
business values in the My Hibachi codebase. These patterns ensure
consistency, maintainability, and allow business values to be changed
without code deployments.

---

## 📊 SSoT Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE SOURCE OF TRUTH                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DATABASE (PostgreSQL)                                         │
│   └── dynamic_variables table                                   │
│       ├── pricing: adult_price_cents, child_price_cents, etc.   │
│       ├── deposit: deposit_amount_cents, deposit_refundable_days│
│       ├── travel: travel_free_miles, travel_per_mile_cents      │
│       ├── booking: min_advance_hours                            │
│       ├── timing: menu_change_cutoff_hours, guest_count_hours   │
│       ├── service: standard_duration_minutes                    │
│       ├── policy: reschedule_fee_cents, free_reschedule_count   │
│       └── contact: business_phone, business_email               │
│                                                                  │
│                         ↓                                        │
│                                                                  │
│   BACKEND API (FastAPI)                                         │
│   └── GET /api/v1/pricing/current                               │
│       Returns: base_pricing, travel_fee_config, etc.            │
│       Uses: BusinessConfig service with fallback chain          │
│                                                                  │
│                         ↓                                        │
│                                                                  │
│   FRONTEND (Next.js)                                            │
│   ├── usePricing() hook → Pricing calculations                  │
│   ├── useConfig() hook → Full configuration                     │
│   ├── usePolicies() hook → Policy text with values              │
│   └── useFaqsWithPricing() hook → FAQs with interpolation       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Canonical Source Files

### Backend (Source of Truth)

| File                                                         | Purpose                              |
| ------------------------------------------------------------ | ------------------------------------ |
| `apps/backend/src/services/business_config_service.py`       | BusinessConfig dataclass, DB loading |
| `apps/backend/src/api/v1/endpoints/pricing.py`               | Pricing API endpoint                 |
| `database/migrations/005_seed_dynamic_variables_staging.sql` | Initial SSoT seed data               |
| `database/migrations/018_timing_policy_variables.sql`        | Timing/policy variables              |

### Frontend (Consumers)

| File                                            | Purpose                          |
| ----------------------------------------------- | -------------------------------- |
| `apps/customer/src/hooks/usePricing.ts`         | Primary pricing hook             |
| `apps/customer/src/hooks/useConfig.ts`          | Full config hook                 |
| `apps/customer/src/hooks/usePolicies.ts`        | Policy text with values          |
| `apps/customer/src/hooks/useFaqsWithPricing.ts` | FAQ interpolation                |
| `apps/customer/src/lib/pricingTemplates.ts`     | Fallback defaults + placeholders |

### Static Content with Placeholders

| File                                   | Purpose                                   |
| -------------------------------------- | ----------------------------------------- |
| `apps/customer/src/data/faqsData.ts`   | FAQ content with `{{PLACEHOLDER}}` syntax |
| `apps/customer/src/data/policies.json` | Policy text with placeholders             |

---

## 🏷️ Placeholder Syntax

Static content files use `{{PLACEHOLDER}}` syntax for dynamic values:

| Placeholder                   | Description                         | Source                                 |
| ----------------------------- | ----------------------------------- | -------------------------------------- |
| `{{ADULT_PRICE}}`             | Adult per-person price ($55)        | `base_pricing.adult_price`             |
| `{{CHILD_PRICE}}`             | Child (6-12) per-person price ($30) | `base_pricing.child_price`             |
| `{{CHILD_FREE_AGE}}`          | Free under age (5)                  | `base_pricing.child_free_under_age`    |
| `{{PARTY_MINIMUM}}`           | Party minimum ($550)                | `base_pricing.party_minimum`           |
| `{{DEPOSIT_AMOUNT}}`          | Fixed deposit ($100)                | `base_pricing.deposit_amount`          |
| `{{DEPOSIT_REFUNDABLE_DAYS}}` | Refund window (4 days)              | `base_pricing.deposit_refundable_days` |
| `{{FREE_TRAVEL_MILES}}`       | Free travel radius (30 mi)          | `travel_fee_config.free_miles`         |
| `{{COST_PER_MILE}}`           | Per-mile rate ($2)                  | `travel_fee_config.price_per_mile`     |

### Example Usage in faqsData.ts:

```typescript
{
  id: 'deposit-policy',
  question: "What's the deposit policy?",
  answer: '${{DEPOSIT_AMOUNT}} refundable deposit secures your date. ' +
          'Refundable if canceled {{DEPOSIT_REFUNDABLE_DAYS}}+ days before event.',
  // ...
}
```

### Interpolation Function:

```typescript
// apps/customer/src/hooks/useFaqsWithPricing.ts
const interpolatePlaceholders = (
  text: string,
  values: PricingValues
): string => {
  return text
    .replace(/\{\{ADULT_PRICE\}\}/g, `${values.adultPrice}`)
    .replace(/\{\{CHILD_PRICE\}\}/g, `${values.childPrice}`)
    .replace(/\{\{DEPOSIT_AMOUNT\}\}/g, `${values.depositAmount}`)
    .replace(
      /\{\{DEPOSIT_REFUNDABLE_DAYS\}\}/g,
      `${values.depositRefundableDays}`
    );
  // ... etc
};
```

---

## ✅ Correct Patterns

### Pattern 1: Using usePricing() Hook

```tsx
// ✅ CORRECT - Uses SSoT hook
import { usePricing } from '@/hooks/usePricing';

function PricingDisplay() {
  const { adultPrice, childPrice, depositAmount, isLoading } =
    usePricing();

  if (isLoading) return <Skeleton />;

  return (
    <div>
      <p>Adults: ${adultPrice}/person</p>
      <p>Children: ${childPrice}/person</p>
      <p>Deposit: ${depositAmount}</p>
    </div>
  );
}
```

### Pattern 2: Using usePolicies() Hook

```tsx
// ✅ CORRECT - Pre-formatted policy text
import { usePolicies } from '@/hooks/usePolicies';

function DepositPolicy() {
  const { depositPolicy, isLoading } = usePolicies();

  if (isLoading) return <Skeleton />;

  return <p>{depositPolicy.text}</p>;
  // Output: "$100 deposit required, refundable if canceled 4+ days before event."
}
```

### Pattern 3: FAQ Display with Interpolation

```tsx
// ✅ CORRECT - FAQs with values interpolated
import { useFaqsWithPricing } from '@/hooks/useFaqsWithPricing';

function FAQSection() {
  const { faqs, isLoading } = useFaqsWithPricing('Pricing');

  if (isLoading) return <Skeleton />;

  return (
    <div>
      {faqs.map(faq => (
        <div key={faq.id}>
          <h3>{faq.question}</h3>
          <p>{faq.answer}</p> {/* Values already interpolated! */}
        </div>
      ))}
    </div>
  );
}
```

### Pattern 4: Backend Service Usage

```python
# ✅ CORRECT - Uses BusinessConfig service
from services.business_config_service import get_business_config

async def calculate_deposit(db: AsyncSession) -> int:
    config = await get_business_config(db)
    return config.deposit_amount_cents  # 10000 ($100)
```

---

## ❌ Anti-Patterns (NEVER DO THESE)

### Anti-Pattern 1: Hardcoded Prices

```tsx
// ❌ WRONG - Hardcoded price
<p>Adults are $55 per person</p>;

// ✅ CORRECT - Use hook
const { adultPrice } = usePricing();
<p>Adults are ${adultPrice} per person</p>;
```

### Anti-Pattern 2: Hardcoded Timing Values

```tsx
// ❌ WRONG - Hardcoded timing
<p>Menu changes must be made at least 12 hours before your event.</p>

// ✅ CORRECT - Use placeholder in faqsData.ts
// faqsData.ts: "Menu changes must be made at least {{MENU_CHANGE_CUTOFF_HOURS}} hours before"
// Then use useFaqsWithPricing() to display
```

### Anti-Pattern 3: Magic Numbers in Validation

```tsx
// ❌ WRONG - Magic number
if (hoursUntilEvent < 48) {
  return 'Must book 48 hours in advance';
}

// ✅ CORRECT - Use SSoT value
const { minAdvanceHours } = useConfig();
if (hoursUntilEvent < minAdvanceHours) {
  return `Must book ${minAdvanceHours} hours in advance`;
}
```

### Anti-Pattern 4: Local Fallback Without Hook

```tsx
// ❌ WRONG - Using local constant instead of hook
const DEPOSIT = 100; // What if this changes?

// ✅ CORRECT - Use hook with built-in fallback
const { depositAmount } = usePricing(); // Has fallback to pricingTemplates.ts
```

---

## 🔄 Fallback Chain

When fetching SSoT values, the system uses a priority fallback chain:

```
1. API Response (/api/v1/pricing/current)
       ↓ (if unavailable)
2. pricingTemplates.ts (local defaults)
       ↓ (should never reach this in production)
3. Hardcoded fallback in hook
```

### pricingTemplates.ts (Fallback Defaults):

```typescript
// apps/customer/src/lib/pricingTemplates.ts
export const PRICING_DEFAULTS = {
  ADULT_PRICE: 55,
  CHILD_PRICE: 30,
  CHILD_FREE_UNDER_AGE: 5,
  PARTY_MINIMUM: 550,
  DEPOSIT_AMOUNT: 100,
  DEPOSIT_REFUNDABLE_DAYS: 4,
  FREE_TRAVEL_MILES: 30,
  COST_PER_MILE: 2,
};
```

---

## 📋 Dynamic Variables Categories

| Category  | Variables                                                 | Admin Editable |
| --------- | --------------------------------------------------------- | -------------- |
| `pricing` | adult_price_cents, child_price_cents, party_minimum_cents | ✅ Yes         |
| `deposit` | deposit_amount_cents, deposit_refundable_days             | ✅ Yes         |
| `travel`  | travel_free_miles, travel_per_mile_cents                  | ✅ Yes         |
| `booking` | min_advance_hours                                         | ✅ Yes         |
| `timing`  | menu_change_cutoff_hours, guest_count_finalize_hours      | ✅ Yes         |
| `service` | standard_duration_minutes, chef_arrival_minutes_before    | ✅ Yes         |
| `policy`  | reschedule_fee_cents, free_reschedule_count               | ✅ Yes         |
| `contact` | business_phone, business_email                            | ✅ Yes         |

---

## 🧪 Testing SSoT Integration

### Verify API Response:

```bash
curl https://mhapi.mysticdatanode.net/api/v1/pricing/current | jq '.base_pricing'
```

Expected output:

```json
{
  "adult_price": 55,
  "child_price": 30,
  "child_free_under_age": 5,
  "party_minimum": 550,
  "deposit_amount": 100,
  "deposit_refundable_days": 4
}
```

### Verify Database Values:

```sql
SELECT category, key, value, display_name
FROM dynamic_variables
WHERE is_active = true
ORDER BY category, key;
```

---

## 📝 Adding New SSoT Variables

### Step 1: Add to Database

```sql
-- database/migrations/0XX_new_variable.sql
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('category', 'new_variable', '100', 'Display Name', 'Description', true)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value;
```

### Step 2: Add to BusinessConfig (if needed)

```python
# apps/backend/src/services/business_config_service.py
@dataclass
class BusinessConfig:
    # ... existing fields ...
    new_variable: int = 100  # Default fallback
```

### Step 3: Add to API Response (if needed)

```python
# apps/backend/src/api/v1/endpoints/pricing.py
response = {
    "base_pricing": {
        # ... existing fields ...
        "new_variable": config.new_variable,
    },
}
```

### Step 4: Add Placeholder (if used in static content)

```typescript
// apps/customer/src/lib/pricingTemplates.ts
export const PLACEHOLDERS = {
  // ... existing ...
  NEW_VARIABLE: '{{NEW_VARIABLE}}',
};

export const PRICING_DEFAULTS = {
  // ... existing ...
  NEW_VARIABLE: 100,
};
```

### Step 5: Add to Interpolation Function

```typescript
// apps/customer/src/hooks/useFaqsWithPricing.ts
const interpolatePlaceholders = (
  text: string,
  values: PricingValues
): string => {
  return (
    text
      // ... existing ...
      .replace(/\{\{NEW_VARIABLE\}\}/g, `${values.newVariable}`)
  );
};
```

---

## 🔍 Pre-Commit SSoT Check

Before committing, search for potential hardcoded values:

```bash
# Search for dollar amounts (potential hardcoded prices)
grep -rn '\$[0-9]\+' apps/customer/src --include="*.tsx" --include="*.ts"

# Search for hardcoded timing (hours/minutes)
grep -rn '[0-9]\+ hours\|[0-9]\+ minutes' apps/customer/src --include="*.tsx"

# Search for hardcoded phone numbers
grep -rn '916.*740.*8768\|(916)' apps/customer/src --include="*.tsx"
```

---

## 🔗 Related Documentation

- [20-SINGLE_SOURCE_OF_TRUTH.instructions.md](./20-SINGLE_SOURCE_OF_TRUTH.instructions.md)
  – Full SSoT architecture
- [21-BUSINESS_MODEL.instructions.md](./21-BUSINESS_MODEL.instructions.md)
  – Business rules reference
- [22-QUALITY_CONTROL.instructions.md](./22-QUALITY_CONTROL.instructions.md)
  – SSoT compliance checks

---

**Remember:** If a value can change, it MUST come from SSoT. Never
hardcode business values. Use the hooks!
