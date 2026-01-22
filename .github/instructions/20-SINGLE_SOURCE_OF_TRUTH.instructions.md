---
applyTo: '**'
---

# My Hibachi – Single Source of Truth (SSoT) Architecture

**Priority: CRITICAL** – ALL business data MUST flow from centralized
sources. **Version:** 1.0.0 **Created:** 2025-12-27 **Updated:**
2025-12-27

---

## 🎯 Purpose

This document defines the **Single Source of Truth** architecture for
the My Hibachi ecosystem. ALL business data, pricing, policies, and
configuration values MUST originate from centralized database sources
and flow through defined API channels.

**Core Principle:**

> If a value can change, it MUST come from the database. Never
> hardcode business values in frontend code, AI configurations, or
> static files.

---

## 🏗️ SSoT Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SINGLE SOURCE OF TRUTH SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    DATABASE (PostgreSQL)                         │   │
│   │  ════════════════════════════════════════════════════════════   │   │
│   │                                                                  │   │
│   │   PRICING & FEES                 POLICIES & RULES               │   │
│   │   ├── dynamic_variables          ├── business_rules             │   │
│   │   │   • adult_price_cents        │   • deposit_policy           │   │
│   │   │   • child_price_cents        │   • cancellation_policy      │   │
│   │   │   • party_minimum_cents      │   • refund_policy            │   │
│   │   │   • deposit_amount_cents     │   • reschedule_policy        │   │
│   │   │                              │   • booking_advance_hours    │   │
│   │   └── travel_fee_configs         │   • guest_count_limits       │   │
│   │       • free_miles               │                              │   │
│   │       • per_mile_cents           └── legal_documents            │   │
│   │       • service_radius               • terms_of_service         │   │
│   │                                      • privacy_policy           │   │
│   │   CONTENT & FAQS                     • liability_waiver         │   │
│   │   ├── faq_items                                                 │   │
│   │   │   • question                 SCHEDULING                     │   │
│   │   │   • answer_template          ├── slot_configurations        │   │
│   │   │   • category                 │   • slot_times               │   │
│   │   │   • variable_refs[]          │   • durations                │   │
│   │   │                              │   • buffer_minutes           │   │
│   │   └── email_templates            │                              │   │
│   │       • template_key             └── station_settings           │   │
│   │       • subject_template             • timezone                 │   │
│   │       • body_template                • operating_hours          │   │
│   │       • variable_refs[]              • service_area             │   │
│   │                                                                  │   │
│   │   NEWSLETTER & COMMS             INTEGRATIONS                   │   │
│   │   ├── newsletter_config          ├── akaunting_config           │   │
│   │   │   • sender_email             │   • sync_enabled             │   │
│   │   │   • sender_name              │   • invoice_prefix           │   │
│   │   │   • frequency_limits         │   • tax_settings             │   │
│   │   │   • template_id              │                              │   │
│   │   │                              └── payment_config             │   │
│   │   └── sms_config                     • stripe_mode              │   │
│   │       • sender_number                • webhook_secret           │   │
│   │       • daily_limit                                             │   │
│   │       • template_id                                             │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    BACKEND API (FastAPI)                         │   │
│   │  ════════════════════════════════════════════════════════════   │   │
│   │                                                                  │
│   │   CONFIG ENDPOINTS (Public)              ADMIN ENDPOINTS         │
│   │   ├── GET /api/v1/config/all            ├── PUT /api/v1/admin/  │   │
│   │   │   → Complete config bundle          │   config/{key}        │   │
│   │   ├── GET /api/v1/pricing/current       │   → Update any config │   │
│   │   │   → Pricing only                    │                       │   │
│   │   ├── GET /api/v1/policies/current      ├── GET /api/v1/admin/  │   │
│   │   │   → Policies with values            │   config/audit        │   │
│   │   ├── GET /api/v1/faqs                  │   → Change history    │   │
│   │   │   → Dynamic FAQs                    │                       │   │
│   │   └── GET /api/v1/legal/{document}      └── POST /api/v1/admin/ │   │
│   │       → Terms with current values           config/validate     │   │
│   │                                             → Validate before   │   │
│   │                                                save              │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│              ┌───────────────┼───────────────────┐                     │
│              ▼               ▼                   ▼                     │
│   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│   │   CUSTOMER APP   │ │    ADMIN APP     │ │    AI SYSTEM     │      │
│   │   ══════════════ │ │   ═══════════    │ │   ═══════════    │      │
│   │                  │ │                  │ │                  │      │
│   │  Hooks:          │ │  Hooks:          │ │  Tools:          │      │
│   │  • useConfig()   │ │  • useConfig()   │ │  • pricing_tool  │      │
│   │  • usePricing()  │ │  • usePricing()  │ │  • faq_tool      │      │
│   │  • usePolicies() │ │  • usePolicies() │ │  • policy_tool   │      │
│   │  • useFaqs()     │ │  • useFaqs()     │ │                  │      │
│   │                  │ │                  │ │  NO FALLBACKS!   │      │
│   │  Components:     │ │  Admin UI:       │ │  If API down:    │      │
│   │  • QuoteCalc     │ │  • Variables     │ │  → Graceful msg  │      │
│   │  • FAQSection    │ │  • FAQ Editor    │ │  → Log error     │      │
│   │  • TermsPage     │ │  • Policy Editor │ │  → Escalate      │      │
│   │  • PaymentPage   │ │  • Legal Editor  │ │                  │      │
│   │                  │ │                  │ │                  │      │
│   └──────────────────┘ └──────────────────┘ └──────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Tables Reference

### Core Configuration Tables

| Table                       | Schema       | Purpose                       | Admin Editable |
| --------------------------- | ------------ | ----------------------------- | -------------- |
| `dynamic_variables`         | `public`     | All pricing, fees, limits     | ✅ Yes         |
| `business_rules`            | `public`     | Policies, time rules          | ✅ Yes         |
| `travel_fee_configurations` | `core`       | Travel zones, per-mile rates  | ✅ Yes         |
| `slot_configurations`       | `ops`        | Time slots, durations         | ✅ Yes         |
| `faq_items`                 | `public`     | FAQ content with templates    | ✅ Yes         |
| `legal_documents`           | `public`     | Terms, privacy with templates | ✅ Yes         |
| `email_templates`           | `newsletter` | Email content templates       | ✅ Yes         |
| `newsletter_config`         | `newsletter` | Newsletter settings           | ✅ Yes         |
| `sms_config`                | `comms`      | SMS settings                  | ✅ Yes         |

### Variable Reference Format

All content that references dynamic values uses template syntax:

```
Answer: "Adults are {{adult_price}} per person, children {{child_price}}."
→ Rendered: "Adults are $55 per person, children $30."
```

---

## 🔌 API Endpoints

### Public Configuration Endpoints

```yaml
GET /api/v1/config/all:
  description: Complete configuration bundle for app initialization
  cache: 5 minutes
  response:
    pricing:
      adult_price_cents: 5500
      child_price_cents: 3000
      party_minimum_cents: 55000
      deposit_amount_cents: 10000
    travel:
      free_miles: 30
      per_mile_cents: 200
    policies:
      advance_booking_hours: 48
      refund_days: 4
      reschedule_allowed: true
    guest_limits:
      minimum: 1
      maximum: 100
      minimum_for_hibachi: 10

GET /api/v1/pricing/current:
  description: Pricing only (lightweight)
  cache: 5 minutes

GET /api/v1/policies/current:
  description: Policies with rendered values
  cache: 15 minutes

GET /api/v1/faqs:
  description: FAQs with dynamic values injected
  cache: 15 minutes
  query_params:
    category: string (optional)

GET /api/v1/legal/{document_type}:
  description: Legal document with current values
  document_type: terms | privacy | liability
  cache: 1 hour
```

### Admin Configuration Endpoints

```yaml
PUT /api/v1/admin/config/{category}/{key}:
  description: Update single configuration value
  auth: Super Admin only
  audit: All changes logged
  validation: Type-specific validation before save

POST /api/v1/admin/config/bulk:
  description: Update multiple values atomically
  auth: Super Admin only
  body:
    changes:
      - category: pricing
        key: adult_price_cents
        value: 5500
      - category: travel
        key: free_miles
        value: 30
  response:
    success: true
    applied: 2
    cache_invalidated: true

GET /api/v1/admin/config/audit:
  description: Configuration change history
  auth: Admin+
  query_params:
    category: string (optional)
    from_date: datetime
    to_date: datetime
```

---

## 🎨 Frontend Hooks

### useConfig() - Complete Configuration

```typescript
// apps/customer/src/hooks/useConfig.ts

interface ConfigBundle {
  pricing: {
    adultPrice: number; // Dollars (converted from cents)
    childPrice: number;
    partyMinimum: number;
    depositAmount: number;
  };
  travel: {
    freeMiles: number;
    perMileRate: number;
  };
  policies: {
    advanceBookingHours: number;
    refundDays: number;
    rescheduleAllowed: boolean;
  };
  guestLimits: {
    minimum: number;
    maximum: number;
    minimumForHibachi: number;
  };
  isLoading: boolean;
  error: Error | null;
}

export function useConfig(): ConfigBundle {
  // Fetches from /api/v1/config/all
  // Caches in React Query for 5 minutes
  // Returns loading state while fetching
}
```

### usePolicies() - Policies with Formatted Text

```typescript
// apps/customer/src/hooks/usePolicies.ts

interface PolicyBundle {
  deposit: {
    amount: number;
    text: string; // "Your $100 deposit is fully refundable..."
  };
  cancellation: {
    refundDays: number;
    text: string; // "Full refund if canceled 4+ days before..."
  };
  travel: {
    freeMiles: number;
    perMileRate: number;
    text: string; // "First 30 miles free, then $2/mile"
  };
  booking: {
    advanceHours: number;
    text: string; // "Book at least 48 hours in advance"
  };
}

export function usePolicies(): PolicyBundle {
  // Fetches from /api/v1/policies/current
  // Returns pre-formatted text strings with values injected
}
```

### useFaqs() - Dynamic FAQs

```typescript
// apps/customer/src/hooks/useFaqs.ts

interface FAQ {
  id: string;
  question: string;
  answer: string; // Values already injected
  category: string;
}

interface FAQBundle {
  faqs: FAQ[];
  categories: string[];
  isLoading: boolean;
  error: Error | null;
}

export function useFaqs(category?: string): FAQBundle {
  // Fetches from /api/v1/faqs
  // Values are server-side rendered into answers
}
```

---

## 🤖 AI System Integration

### NO HARDCODED FALLBACKS

The AI system MUST NOT have any hardcoded pricing or policy values. If
the pricing API is unavailable:

```python
# apps/backend/src/api/ai/orchestrator/tools/pricing_tool.py

class PricingTool:
    """
    Pricing calculation tool for AI assistant.

    CRITICAL: NO FALLBACK VALUES!
    If pricing API fails, return graceful error message.
    """

    async def calculate_quote(self, adults: int, children: int) -> dict:
        try:
            config = await get_business_config(self.db)
            # Calculate using live values
            return {
                "success": True,
                "quote": {...},
                "source": "live_database"
            }
        except DatabaseError as e:
            logger.error(f"Pricing API unavailable: {e}")
            return {
                "success": False,
                "error": "pricing_unavailable",
                "message": "I'm unable to calculate an exact quote right now. "
                          "Let me connect you with our team who can help!",
                "action": "escalate_to_human"
            }

    async def get_policies(self) -> dict:
        try:
            policies = await get_policies_from_db(self.db)
            return {"success": True, "policies": policies}
        except DatabaseError as e:
            logger.error(f"Policy API unavailable: {e}")
            return {
                "success": False,
                "message": "I want to make sure I give you accurate information. "
                          "Let me have someone from our team confirm the details for you.",
                "action": "escalate_to_human"
            }
```

### AI Graceful Degradation Protocol

```python
# When SSoT is unavailable, AI follows this protocol:

AI_FALLBACK_RESPONSES = {
    "pricing_unavailable": {
        "message": "I'd love to give you an exact quote, but I'm having "
                  "trouble accessing our current pricing. Let me connect "
                  "you with our team - they'll get you accurate numbers "
                  "right away! 🙏",
        "action": "escalate_to_human",
        "priority": "high",
        "reason": "pricing_api_down"
    },
    "policy_unavailable": {
        "message": "I want to make sure I give you 100% accurate policy "
                  "information. Let me have someone from our team confirm "
                  "the details for you!",
        "action": "escalate_to_human",
        "priority": "medium",
        "reason": "policy_api_down"
    },
    "faq_unavailable": {
        "message": "Great question! Let me get you the most current answer "
                  "from our team.",
        "action": "escalate_to_human",
        "priority": "low",
        "reason": "faq_api_down"
    }
}

# AI NEVER says:
# ❌ "Our standard price is $55 per person..."
# ❌ "The deposit is typically $100..."
# ❌ "Usually you need to book 48 hours in advance..."

# AI ALWAYS says:
# ✅ "Let me check our current pricing for you..." *calls pricing_tool*
# ✅ "I'm getting the latest policy information..." *calls policy_tool*
```

---

## 📝 FAQ Template System

### Database Schema

```sql
CREATE TABLE faq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer_template TEXT NOT NULL,  -- Contains {{variable}} placeholders
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    variable_refs TEXT[],  -- List of variables used in template
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example row:
INSERT INTO faq_items (question, answer_template, category, variable_refs) VALUES (
    'How much does it cost?',
    'Adults (13+) are {{adult_price}} per person. Children ages 6-12 are {{child_price}}. Kids 5 and under eat FREE! We have a {{party_minimum}} minimum order.',
    'Pricing',
    ARRAY['adult_price', 'child_price', 'party_minimum']
);
```

### Template Rendering

```python
# apps/backend/src/services/faq_service.py

async def get_rendered_faqs(db: AsyncSession, category: str = None) -> list[dict]:
    """
    Get FAQs with dynamic values injected.

    Template variables:
    - {{adult_price}} → "$55"
    - {{child_price}} → "$30"
    - {{party_minimum}} → "$550"
    - {{deposit_amount}} → "$100"
    - {{free_miles}} → "30 miles"
    - {{per_mile_rate}} → "$2"
    - {{advance_hours}} → "48 hours"
    - {{refund_days}} → "4 days"
    """
    config = await get_business_config(db)

    # Build variable map
    variables = {
        "adult_price": f"${config.adult_price_cents // 100}",
        "child_price": f"${config.child_price_cents // 100}",
        "party_minimum": f"${config.party_minimum_cents // 100}",
        "deposit_amount": f"${config.deposit_amount_cents // 100}",
        "free_miles": f"{config.travel_free_miles} miles",
        "per_mile_rate": f"${config.travel_per_mile_cents // 100}",
        "advance_hours": f"{config.min_advance_hours} hours",
        "refund_days": f"{config.deposit_refundable_days} days",
    }

    faqs = await db.execute(
        select(FAQItem).where(FAQItem.is_active == True)
    )

    rendered = []
    for faq in faqs.scalars():
        answer = faq.answer_template
        for var_name, var_value in variables.items():
            answer = answer.replace(f"{{{{{var_name}}}}}", var_value)

        rendered.append({
            "id": str(faq.id),
            "question": faq.question,
            "answer": answer,
            "category": faq.category,
        })

    return rendered
```

---

## 📄 Legal Document Template System

### Database Schema

```sql
CREATE TABLE legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL UNIQUE,  -- 'terms', 'privacy', 'liability'
    title VARCHAR(200) NOT NULL,
    content_template TEXT NOT NULL,  -- Markdown with {{variable}} placeholders
    version VARCHAR(20) NOT NULL,
    effective_date DATE NOT NULL,
    variable_refs TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id)
);

-- Audit trail for legal changes
CREATE TABLE legal_document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id),
    version VARCHAR(20) NOT NULL,
    content_template TEXT NOT NULL,
    changed_by UUID REFERENCES identity.users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Legal Document Rendering

```python
# apps/backend/src/services/legal_service.py

async def get_rendered_legal_document(
    db: AsyncSession,
    document_type: str
) -> dict:
    """
    Get legal document with current values injected.

    Important: Legal documents maintain version history for compliance.
    When values change, the document shows current values but
    the template version is tracked.
    """
    config = await get_business_config(db)

    document = await db.execute(
        select(LegalDocument).where(
            LegalDocument.document_type == document_type
        )
    )
    doc = document.scalar_one()

    variables = {
        "deposit_amount": f"${config.deposit_amount_cents // 100}",
        "refund_days": str(config.deposit_refundable_days),
        "advance_hours": str(config.min_advance_hours),
        "party_minimum": f"${config.party_minimum_cents // 100}",
        "effective_date": doc.effective_date.strftime("%B %d, %Y"),
    }

    content = doc.content_template
    for var_name, var_value in variables.items():
        content = content.replace(f"{{{{{var_name}}}}}", var_value)

    return {
        "title": doc.title,
        "content": content,
        "version": doc.version,
        "effective_date": doc.effective_date.isoformat(),
        "rendered_at": datetime.utcnow().isoformat(),
        "values_used": variables,  # For audit trail
    }
```

---

## 📧 Newsletter Configuration

### Admin-Configurable Settings

| Setting                  | Table               | Description                      |
| ------------------------ | ------------------- | -------------------------------- |
| `sender_email`           | `newsletter_config` | From email address               |
| `sender_name`            | `newsletter_config` | Display name                     |
| `reply_to_email`         | `newsletter_config` | Reply-to address                 |
| `daily_limit`            | `newsletter_config` | Max emails per day               |
| `batch_size`             | `newsletter_config` | Emails per batch                 |
| `batch_delay_seconds`    | `newsletter_config` | Delay between batches            |
| `unsubscribe_grace_days` | `newsletter_config` | Days before re-subscribe allowed |
| `default_template_id`    | `newsletter_config` | Default email template           |

### Email Template System

```sql
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,  -- HTML with {{variable}} placeholders
    category VARCHAR(50),  -- 'marketing', 'transactional', 'reminder'
    variable_refs TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example templates:
-- booking_confirmation, reminder_48h, reminder_24h, review_request,
-- promotional_seasonal, newsletter_weekly
```

---

## 🔄 Cache Invalidation

When admin updates configuration:

```python
# apps/backend/src/services/config_admin_service.py

async def update_config(
    db: AsyncSession,
    cache: CacheService,
    category: str,
    key: str,
    value: Any,
    admin_user_id: UUID
) -> dict:
    """
    Update configuration value and invalidate all relevant caches.
    """
    # 1. Validate value
    validate_config_value(category, key, value)

    # 2. Update database
    await update_config_in_db(db, category, key, value)

    # 3. Log audit trail
    await log_config_change(db, category, key, value, admin_user_id)

    # 4. Invalidate ALL related caches
    cache_keys_to_invalidate = [
        "config:business",
        "config:pricing",
        "config:policies",
        "config:faqs",
        "config:legal:*",
    ]

    for cache_key in cache_keys_to_invalidate:
        await cache.delete_pattern(cache_key)

    # 5. Return confirmation
    return {
        "success": True,
        "category": category,
        "key": key,
        "new_value": value,
        "caches_invalidated": len(cache_keys_to_invalidate),
    }
```

---

## ✅ SSoT Compliance Checklist

### Before Creating Any Component

- [ ] Does this component display any business value (price, time,
      policy)?
- [ ] If YES → Use appropriate hook (`useConfig`, `usePricing`,
      `usePolicies`, `useFaqs`)
- [ ] If NO → Safe to use static content

### Before Creating Any Backend Endpoint

- [ ] Does this endpoint return business data?
- [ ] If YES → Use `get_business_config()` or appropriate service
- [ ] If NO → Safe to use static values

### Before Creating AI Responses

- [ ] Does the AI need to quote prices or policies?
- [ ] If YES → Use `pricing_tool` or `policy_tool` (NO FALLBACKS!)
- [ ] If unavailable → Graceful escalation to human

### Code Review Checklist

- [ ] No hardcoded prices in frontend components
- [ ] No hardcoded policies in UI text
- [ ] No hardcoded values in AI configuration
- [ ] All FAQs use template system
- [ ] Legal documents use template system
- [ ] Validation rules use dynamic limits

---

## 🚫 Anti-Patterns (NEVER DO THESE)

```typescript
// ❌ WRONG - Hardcoded price in component
<p>Adults are $55 per person</p>

// ✅ CORRECT - Use hook
const { pricing } = useConfig();
<p>Adults are ${pricing.adultPrice} per person</p>
```

```typescript
// ❌ WRONG - Hardcoded policy in text
<p>Cancel 7 days before for full refund</p>

// ✅ CORRECT - Use policies hook
const { cancellation } = usePolicies();
<p>{cancellation.text}</p>
```

```python
# ❌ WRONG - Hardcoded fallback in AI
PRICING = {
    "adult_base": 55,  # DON'T DO THIS!
}

# ✅ CORRECT - Always use live data
config = await get_business_config(db)
adult_price = config.adult_price_cents / 100
```

```typescript
// ❌ WRONG - Hardcoded validation
.max(100, 'Maximum 100 guests allowed')

// ✅ CORRECT - Use dynamic limits
const { guestLimits } = useConfig();
.max(guestLimits.maximum, `Maximum ${guestLimits.maximum} guests allowed`)
```

---

## 🔗 Related Documentation

- [02-ARCHITECTURE.instructions.md](./02-ARCHITECTURE.instructions.md)
  – System architecture
- [08-FEATURE_FLAGS.instructions.md](./08-FEATURE_FLAGS.instructions.md)
  – Feature flags
- [19-DATABASE_SCHEMA_MANAGEMENT.instructions.md](./19-DATABASE_SCHEMA_MANAGEMENT.instructions.md)
  – DB schema
- [business_config_service.py](../../apps/backend/src/services/business_config_service.py)
  – Config service

---

## 📋 Implementation Priority

### Phase 1: Critical (Legal/Revenue) - Week 1

1. Legal documents template system
2. AI graceful degradation (no fallbacks)
3. Travel fee calculation from config

### Phase 2: Content (FAQs/Policies) - Week 2

1. FAQ template migration
2. Policy text hooks
3. UI text centralization

### Phase 3: Admin UI - Week 3

1. FAQ editor in admin panel
2. Legal document editor
3. Newsletter configuration UI

### Phase 4: Validation Rules - Week 4

1. Dynamic guest limits
2. Dynamic time rules
3. Dynamic validation messages

---

**Remember:** If it can change, it MUST come from the database.
