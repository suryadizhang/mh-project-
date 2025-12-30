---
applyTo: '**'
---

# My Hibachi – Business Model & Operational Rules

**Priority: CRITICAL** – All business values come from SSoT. NEVER invent data.
**Version:** 1.0.0
**Created:** 2025-12-27

---

## 🔴 CRITICAL: SINGLE SOURCE OF TRUTH (SSoT)

**ALL business values in this document are DYNAMIC and managed via the SSoT system.**

> ⚠️ **NEVER HARDCODE** business values. ALWAYS reference the SSoT system.
>
> If you need a specific value, **SEARCH THE CODEBASE FIRST** or **ASK THE USER**.

### SSoT Data Flow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE SOURCE OF TRUTH                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DATABASE (PostgreSQL)                                         │
│   ├── dynamic_variables table ──► Pricing, fees, limits         │
│   ├── business_rules table ────► Policies, time rules           │
│   ├── travel_fee_configurations ► Station-based travel fees     │
│   └── faq_items table ─────────► FAQ content with templates     │
│                                                                  │
│                         ↓                                        │
│                                                                  │
│   BACKEND API (FastAPI)                                         │
│   ├── GET /api/v1/config/all ───► Complete config bundle        │
│   ├── GET /api/v1/pricing/current ► Pricing only                │
│   └── GET /api/v1/policies/current ► Policies with values       │
│                                                                  │
│                         ↓                                        │
│                                                                  │
│   FRONTEND + AI                                                  │
│   ├── useConfig() hook ─────────► All apps use same source      │
│   ├── usePricing() hook ────────► Pricing calculations          │
│   └── AI tools call API ────────► NO HARDCODED FALLBACKS        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Template Placeholder System:

**Frontend files use `{{PLACEHOLDER}}` syntax for dynamic values:**

| Placeholder | Current Default | Source |
|-------------|-----------------|--------|
| `{{ADULT_PRICE}}` | 55 | `dynamic_variables.adult_price_cents / 100` |
| `{{CHILD_PRICE}}` | 30 | `dynamic_variables.child_price_cents / 100` |
| `{{CHILD_FREE_AGE}}` | 5 | `dynamic_variables.child_free_under_age` |
| `{{PARTY_MINIMUM}}` | 550 | `dynamic_variables.party_minimum_cents / 100` |
| `{{FREE_TRAVEL_MILES}}` | 30 | `travel_fee_configurations.free_miles` |
| `{{COST_PER_MILE}}` | 2 | `travel_fee_configurations.per_mile_cents / 100` |

### Key Source Files:

| Data Type | Frontend Source | Backend Source |
|-----------|-----------------|----------------|
| **Pricing/FAQ** | `apps/customer/src/data/faqsData.ts` | `services/business_config_service.py` |
| **Menu Structure** | `apps/customer/src/data/menu.ts` | `db/models/menu.py` |
| **Policies** | `apps/customer/src/data/policies.json` | `business_rules` table |
| **Config Service** | `hooks/useConfig.ts` | `services/business_config_service.py` |

**Full SSoT Spec:** See `20-SINGLE_SOURCE_OF_TRUTH.instructions.md`

---

## 🍱 CORE BUSINESS MODEL: 2 PROTEINS PER PERSON

### The Fundamental Rule:

> **Each guest chooses 2 PROTEINS from the base selection.**
>
> This is NOT "1 protein per order" or "protein counts = guest counts".

### What's Included Per Guest:

| Item | Quantity | Notes |
|------|----------|-------|
| **Proteins** | 2 selections | Guest's choice from base menu |
| **Hibachi Fried Rice** | 1 portion | Included |
| **Fresh Vegetables** | 1 portion | Hibachi-style |
| **Side Salad** | 1 portion | House salad |
| **Signature Sauces** | Served family-style | Yum Yum, Ginger, etc. |
| **Sake** | For 21+ guests | Complimentary |

### Pricing Model (Dynamic - from SSoT):

| Guest Type | Price | Protein Selection |
|------------|-------|-------------------|
| **Adults (13+)** | `{{ADULT_PRICE}}` per person | 2 proteins |
| **Children (6-12)** | `{{CHILD_PRICE}}` per person | 2 proteins (same as adults) |
| **Under {{CHILD_FREE_AGE}}** | FREE | 1 protein + small rice |

### Party Minimum:

- **Minimum Total:** `{{PARTY_MINIMUM}}` (approximately 10 adults)
- Smaller groups can reach minimum via upgrades or additional proteins

---

## 🥩 PROTEIN CATEGORIES

### BASE PROTEINS (Included - Guest picks 2):

| Protein | Category | Notes |
|---------|----------|-------|
| 🐔 **Chicken** | Poultry | Most popular |
| 🥩 **NY Strip Steak** | Beef | Premium cut |
| 🦐 **Shrimp** | Seafood | Large, fresh |
| 🦑 **Calamari** | Seafood | Tender rings |
| 🥬 **Tofu** | Vegetarian | Firm, seasoned |

### PREMIUM UPGRADES (+$ per person):

| Upgrade | Price | Notes |
|---------|-------|-------|
| 🍣 **Salmon** | +$5 | Fresh Atlantic |
| 🐚 **Scallops** | +$5 | Sweet sea scallops |
| 🥩 **Filet Mignon** | +$5 | Premium tenderloin (replaces NY Strip) |
| 🦞 **Lobster Tail** | +$15 | Premium seafood |

> **Note:** Upgrades REPLACE one of the guest's 2 base protein choices.
> Example: Guest picks Chicken + Lobster Tail (+$15 upgrade).

---

## 📊 CHEF PREP SUMMARY: CORRECT FORMAT

### ❌ WRONG (Do NOT use this format):

```
PROTEINS:
├── 🐔 Hibachi Chicken .......... 8 orders
├── 🥩 Filet Mignon ............. 4 orders
= Individual "orders" (doesn't match 2-per-person model)
```

### ✅ CORRECT Format (2 proteins per person):

```
PROTEIN SELECTIONS (15 guests × 2 each = 30 total)
┌─────────────────────────────────────────────────────────────┐
│ BASE PROTEINS (included):                                   │
│ ├── 🐔 Chicken ......................... 12 selections      │
│ ├── 🥩 NY Strip Steak .................. 8 selections       │
│ ├── 🦐 Shrimp .......................... 4 selections       │
│ ├── 🦑 Calamari ........................ 3 selections       │
│ └── 🥬 Tofu ............................ 1 selection        │
│                                          = 28 base          │
│ PREMIUM UPGRADES (+$):                                      │
│ ├── 🍣 Salmon (+$5) .................... 1 selection        │
│ └── 🦞 Lobster Tail (+$15) ............. 1 selection        │
│                                          = 2 upgrades       │
└─────────────────────────────────────────────────────────────┘
                                    TOTAL: 30 selections ✓
```

### Math Verification:

- **15 guests × 2 proteins each = 30 total protein selections**
- Base selections + Upgrade selections = 30
- If the math doesn't add up to `guests × 2`, something is WRONG

---

## 🍚 INCLUDED SIDES (Every Guest Gets):

| Side | Description | Quantity |
|------|-------------|----------|
| 🍚 **Hibachi Fried Rice** | Made on grill with egg, vegetables | 1 per guest |
| 🥗 **House Salad** | Fresh with ginger dressing | 1 per guest |
| 🥒 **Hibachi Vegetables** | Zucchini, onion, mushroom, broccoli | 1 per guest |
| 🍶 **Sake** | Complimentary for 21+ guests | Per adult |

---

## ➕ ADD-ONS (Additional Purchase):

| Add-On | Price | Notes |
|--------|-------|-------|
| 🥟 **Gyoza** | Per order | Appetizer |
| 🍚 **Extra Fried Rice** | Per order | Additional portion |
| 🥒 **Extra Vegetables** | Per order | Additional portion |
| 🍜 **Yakisoba Noodles** | Per order | Japanese noodles |

---

## 🚨 ALLERGEN HANDLING PROTOCOL

### Allergen Cooking Rules:

| Allergen | Chef Action | Notes |
|----------|-------------|-------|
| 🦐 **Shellfish** | Cook shrimp/calamari **LAST** on separate section of grill | Cross-contamination prevention |
| 🌾 **Soy/Gluten** | Use **TAMARI** or **coconut aminos** instead of soy sauce | Gluten-free alternative |
| 🥛 **Dairy** | **Already dairy-free by default** | We use dairy-free butter |
| 🥚 **Eggs** | Make fried rice **WITHOUT egg** | Skip egg in rice |
| 🌱 **Sesame** | Skip sesame seeds and sesame oil | Alternative oil used |

### ⚠️ Customer Responsibility Disclaimer:

> Chef allergen accommodations require **accurate information provided during booking**.
>
> If customers do not disclose all allergies, the chef may not have proper alternative ingredients available.
>
> **My Hibachi cannot guarantee allergen-free preparation for undisclosed allergies.**

### Allergen Collection Points:

1. **Booking form** - Required allergen disclosure field
2. **Confirmation email** - Allergen summary + "Is this correct?" prompt
3. **24hr reminder SMS** - "Any dietary changes?"
4. **Chef arrival** - Verbal confirmation before cooking

---

## 💰 DEPOSIT & PAYMENT POLICY

### Deposit Rules (from SSoT):

| Rule | Value | Source |
|------|-------|--------|
| **Deposit Amount** | $100 (fixed) | `dynamic_variables.deposit_amount_cents` |
| **Refundable If** | Canceled 4+ days before event | `business_rules.deposit_refundable_days` |
| **Non-Refundable** | Within 4 days of event | Policy |
| **Applied To** | Deducted from final bill | Standard |

### Payment Methods:

- ✅ Venmo Business
- ✅ Zelle Business
- ✅ Cash
- ✅ Credit Card (Stripe)

### Payment Timeline:

1. **At Booking:** $100 deposit (secures date)
2. **Before Event:** Remaining balance (or on event day)
3. **After Service:** Tips (optional, 20-35% suggested)

---

## 📍 TRAVEL FEE STRUCTURE

### Travel Fee Rules (from SSoT):

| Rule | Value | Source |
|------|-------|--------|
| **Free Miles** | `{{FREE_TRAVEL_MILES}}` miles | `travel_fee_configurations.free_miles` |
| **Per Mile Rate** | $`{{COST_PER_MILE}}` | `travel_fee_configurations.per_mile_cents / 100` |
| **Calculated From** | Nearest station | Station geocoding |

### Service Area Coverage:

- **Primary:** Bay Area, San Jose, Oakland, San Francisco
- **Extended:** Sacramento, Modesto, Stockton, Fresno
- **Custom:** Contact for locations beyond standard range

---

## ⏰ BOOKING RULES

### Time Requirements:

| Rule | Value |
|------|-------|
| **Minimum Advance Notice** | 48 hours |
| **Recommended for Weekends** | 1-2 weeks |
| **Recommended for Holidays** | 2-3 weeks |

### Time Slots (from Smart Scheduling):

| Slot | Time | Adjustment Range |
|------|------|------------------|
| 12PM | 12:00 PM | ±60 minutes |
| 3PM | 3:00 PM | ±60 minutes |
| 6PM | 6:00 PM | ±60 minutes |
| 9PM | 9:00 PM | ±60 minutes |

### Event Duration:

```python
# Duration calculation formula:
duration_minutes = min(60 + (guest_count * 3), 120)

# Examples:
# 10 guests = 60 + 30 = 90 minutes
# 20 guests = 60 + 60 = 120 minutes (max)
# 30 guests = 120 minutes (capped)
```

---

## 🧑‍🍳 CHEF REQUIREMENTS

### What Chef Brings:

- ✅ Hibachi grill (68.3"L × 27.5"W × 41.3"H)
- ✅ All cooking equipment & tools
- ✅ Propane
- ✅ All food ingredients
- ✅ Sake (for 21+ guests)
- ✅ Safety equipment
- ✅ Signature sauces

### What Customer Provides:

- ✅ Tables (2 × 8-foot OR 3 × 6-foot recommended)
- ✅ Chairs for guests
- ✅ Plates, utensils, glasses
- ✅ Napkins
- ✅ Beverages (except sake)
- ✅ Level, well-ventilated space

### Space Requirements:

| Requirement | Specification |
|-------------|---------------|
| **Grill Dimensions** | 68.3"L × 27.5"W × 41.3"H |
| **Table Setup** | U-shape with chef at open end |
| **Seating Capacity** | 2 × 8ft tables = ~10 guests, 3 × 6ft tables = 12-15 guests |
| **Ventilation** | Outdoor preferred, indoor with high ceilings + excellent ventilation |

---

## 🎫 TIPPING POLICY

### Tip Guidelines:

| Suggested Range | Notes |
|-----------------|-------|
| **20-35%** of service total | Industry standard |
| **Cash** | Preferred |
| **Venmo/Zelle** | Accepted (chef's personal) |

> Tips are paid **directly to the chef** after the party.
> 100% of tips go to the assigned chef.

---

## 🔍 BEFORE WRITING ANY BUSINESS VALUE

### Mandatory Search Checklist:

```bash
# Search for pricing data
grep -r "\$55\|\$30\|\$550\|adult.*price\|child.*price" apps/customer/src/data/

# Search for menu/protein data
grep -r "2 proteins\|protein.*choice\|chicken\|steak\|shrimp" apps/customer/src/data/

# Search for deposit/refund policy
grep -r "deposit\|refund\|cancel\|4.*days\|7.*days" apps/customer/src/data/

# Search for allergen handling
grep -r "allergen\|shellfish\|tamari\|dairy.free\|gluten" apps/customer/src/data/
```

### If You Can't Find the Data:

1. **ASK the user** - "What is the correct value for X?"
2. **Mark as TBD** - Use `[TBD - verify with owner]`
3. **NEVER INVENT** - This causes real business problems

---

## ❌ ANTI-PATTERNS (NEVER DO THESE)

### Inventing Menu Items:

```
❌ WRONG: "Wagyu beef upgrade is +$30"
❌ WRONG: "King Crab is available for +$25"
❌ WRONG: "We offer a surf and turf combo"

✅ CORRECT: Check faqsData.ts for actual upgrades:
   - Salmon (+$5), Scallops (+$5), Filet Mignon (+$5), Lobster Tail (+$15)
```

### Wrong Protein Count Logic:

```
❌ WRONG: "8 Hibachi Chicken orders, 4 Filet Mignon orders" for 15 guests
   (This implies 12 total proteins for 15 guests - WRONG!)

✅ CORRECT: 15 guests × 2 proteins each = 30 protein selections
```

### Hardcoded Prices in AI:

```python
# ❌ WRONG - Hardcoded fallback
PRICING = {
    "adult_base": 55,  # DON'T DO THIS!
}

# ✅ CORRECT - Always use SSoT
config = await get_business_config(db)
adult_price = config.adult_price_cents / 100
```

### Wrong Refund Policy:

```
❌ WRONG: "Refund within 48 hours" or "7 days"
✅ CORRECT: Check faqsData.ts - Currently "4+ days before event"
```

---

## 📋 QUICK REFERENCE CARD

| Question | Answer | Source |
|----------|--------|--------|
| How many proteins per guest? | **2** | faqsData.ts `menu-options` |
| Adult price? | `{{ADULT_PRICE}}` | dynamic_variables |
| Child price (6-12)? | `{{CHILD_PRICE}}` | dynamic_variables |
| Free under age? | `{{CHILD_FREE_AGE}}` | dynamic_variables |
| Party minimum? | `{{PARTY_MINIMUM}}` | dynamic_variables |
| Deposit amount? | **$100 fixed** | business_rules |
| Deposit refundable? | **4+ days before** | faqsData.ts |
| Free travel miles? | `{{FREE_TRAVEL_MILES}}` | travel_fee_configurations |
| Per mile rate? | `{{COST_PER_MILE}}` | travel_fee_configurations |
| Minimum booking advance? | **48 hours** | business_rules |
| Tip suggestion? | **20-35%** | faqsData.ts |
| Are we dairy-free? | **YES** (dairy-free butter) | Allergen protocol |

---

## 🔗 Related Documentation

- [20-SINGLE_SOURCE_OF_TRUTH.instructions.md](./20-SINGLE_SOURCE_OF_TRUTH.instructions.md) – SSoT architecture
- [LEGAL_PROTECTION_IMPLEMENTATION.md](../../docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md) – Legal & safety
- [apps/customer/src/data/faqsData.ts](../../apps/customer/src/data/faqsData.ts) – FAQ source data
- [apps/customer/src/data/menu.ts](../../apps/customer/src/data/menu.ts) – Menu structure
- [services/business_config_service.py](../../apps/backend/src/services/business_config_service.py) – Config service

---

**Remember:** When in doubt, **SEARCH** the codebase or **ASK** the user. Never invent business data.
