# My Hibachi – Pricing Business Rules

**Last Updated:** 2025-01-26
**Status:** Active
**Use Case:** AI System Knowledge Base, Dynamic Variables Integration

---

> ⚠️ **DYNAMIC PRICING NOTICE**
> All prices in this document are managed by the **Dynamic Variables System** and can be updated at any time via the admin panel. Values shown are defaults as of the last update date. Always verify current pricing via `GET /api/v1/pricing/current` or the `usePricing()` hook.

---

## 📋 Overview

This document defines the pricing business rules for My Hibachi Chef catering services.
These rules are used across the customer website, quote calculator, booking system,
and AI chat assistant.

---

## 💰 Core Pricing Structure

### Per-Person Pricing

| Category | Price | Age Range | Notes |
|----------|-------|-----------|-------|
| **Adult** | $55 | Ages 13+ | Full hibachi experience, 2 protein choices |
| **Child** | $30 | Ages 6-12 | Kid-friendly portions, 1 protein choice |
| **Toddler** | FREE | Ages 5 & under | With adult purchase, small portions |

### Dynamic Variable Keys

```typescript
// Frontend: usePricing hook → pricingTemplates.ts
adultPrice: number          // Default: 55
childPrice: number          // Default: 30
childFreeUnderAge: number   // Default: 5 (free for 5 & under)

// Backend: dynamic_variables_service.py
ADULT_PRICE = "adult_price"           // cents: 5500
CHILD_PRICE = "child_price"           // cents: 3000
CHILD_FREE_UNDER_AGE = "child_free_under_age"  // 5
```

---

## 🎯 Minimum Order Requirement

### Rule

**Minimum food order total: $550**

If the calculated food subtotal (adults × $55 + children × $30) is less than $550,
the system automatically adjusts the total to meet the minimum.

### Logic (Backend - public_quote.py)

```python
if subtotal < party_minimum:
    subtotal = party_minimum
    applied_minimum = True
```

### Customer Communication

When minimum is applied, display:

> **Minimum order: $550**
> (Your selections $440 → adjusted to $550)

### Dynamic Variable Keys

```typescript
// Frontend
partyMinimum: number        // Default: 550

// Backend
PARTY_MINIMUM = "party_minimum"       // cents: 55000
party_minimum_cents: int = 55000
```

---

## 💵 Deposit Policy

### Current Rule

**Fixed deposit: $100** (refundable)

The deposit secures the booking date and is applied toward the final balance.

### Refund & Reschedule Policy

- **Full refund**: Cancellation 7+ days before event
- **Reschedule**: Allowed 1 time, must be at least 24 hours before event
- **No refund**: Less than 7 days notice

### Previous Rule (Changed 2025-01-26)

Previous: 30% of total
New: Fixed $100 amount

### Dynamic Variable Keys

```typescript
// Frontend
depositAmount: number       // Default: 100

// Backend
DEPOSIT_AMOUNT = "deposit_amount"     // cents: 10000
```

---

## 🚗 Travel Fee Structure

### Rule

| Distance | Fee |
|----------|-----|
| 0-30 miles | **FREE** |
| 30+ miles | **$2 per additional mile** |

### Example Calculations

| Distance | Calculation | Travel Fee |
|----------|-------------|------------|
| 15 miles | Within free zone | $0 |
| 35 miles | (35 - 30) × $2 | $10 |
| 50 miles | (50 - 30) × $2 | $40 |
| 80 miles | (80 - 30) × $2 | $100 |

### Maximum Service Radius

**200 miles** - Requests beyond this distance require special approval.

### Dynamic Variable Keys

```typescript
// travel_fee_configurations table
free_miles: 30
per_mile_rate: 2.00
max_service_distance: 200
```

---

## 🍖 Premium Upgrades

**Source:** `faqsData.ts` (lines 98-111, 517-545)

### Premium Protein Upgrades (Per Person)

| Upgrade | Price | Notes |
|---------|-------|-------|
| Salmon | +$5 | Upgrades existing protein choice |
| Scallops | +$5 | Upgrades existing protein choice |
| Filet Mignon | +$5 | Upgrades existing protein choice |
| Lobster Tail | +$15 | Premium seafood upgrade |

### Add-On Options

| Add-On | Price | Description |
|--------|-------|-------------|
| Yakisoba Noodles | +$5 | Japanese-style lo mein |
| Extra Fried Rice | +$5 | Additional rice portion |
| Extra Vegetables | +$5 | Mixed seasonal vegetables |
| Edamame | +$5 | Steamed soybeans with sea salt |
| Gyoza | +$10 | Pan-fried Japanese dumplings |
| Extra Protein | +$10 | Additional protein (any type) |

### Upgrade vs Add-On Distinction

- **Upgrade**: Replaces your existing protein choice with premium option
- **Add-On (Extra Protein)**: Adds MORE food (+$10), doesn't replace
- **Combo Example**: Extra protein (+$10) as Lobster Tail (+$15) = +$25 total

---

## 📊 Quote Calculation Formula

### Total Calculation

```
Food Subtotal = (Adults × $55) + (Children × $30)
                → Apply minimum if < $550

Upgrades Total = Σ(upgrade_price × quantity)

Travel Fee = max(0, distance - 30) × $2

Grand Total = Food Subtotal + Upgrades Total + Travel Fee

Deposit Required = $100 (fixed)
Balance Due = Grand Total - Deposit
```

### Example Quote

```
Party: 8 adults, 4 children
Location: 45 miles from station

Food:     8 × $55 = $440
          4 × $30 = $120
          Subtotal = $560 (above $550 minimum ✓)

Travel:   (45 - 30) × $2 = $30

Grand Total:    $590
Deposit:        $100
Balance Due:    $490
```

---

## 🤖 AI System Usage Notes

### When Customer Asks About Pricing

1. **Always quote current prices** from dynamic variables
2. **Always mention the $550 minimum** upfront
3. **Calculate travel fee** based on their location
4. **Recommend the quote calculator** for accurate estimates

### Example AI Responses

**Q: "How much for 6 adults?"**
> For 6 adults, that would be $330 (6 × $55). However, we have a $550 minimum order, so your total would be $550. Would you like to add more guests or upgrades to get full value?

**Q: "What's included in the price?"**
> Each adult ($55) includes: 2 protein choices, fried rice, vegetables, salad, signature sauces, live hibachi show, and complimentary sake. Children ($30) get 1 protein and all sides. Kids 5 & under eat free!

**Q: "How much is deposit?"**
> We require a $100 refundable deposit to secure your date. It's fully refundable if you cancel 7+ days before your event. You can also reschedule one time as long as it's at least 24 hours before the original date.

**Q: "What upgrades do you have?"**
> We offer premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5/person, Lobster Tail is +$15/person. For add-ons: Yakisoba Noodles, Extra Fried Rice, Extra Vegetables, and Edamame are +$5 each. Gyoza and Extra Protein are +$10 each.

### Escalation Triggers

- Requests for discounts → Escalate to human
- Large parties (30+ guests) → Escalate for custom pricing
- Corporate events → Escalate for business accounts
- Travel 100+ miles → Escalate for special logistics

---

## 🔄 How to Update Prices

### Step 1: Update Backend Dynamic Variables

```sql
-- Update party minimum (in cents)
UPDATE dynamic_variables
SET value = '60000' -- $600
WHERE key = 'party_minimum';

-- Update adult price (in cents)
UPDATE dynamic_variables
SET value = '5800' -- $58
WHERE key = 'adult_price';
```

### Step 2: Frontend Updates Automatically

The `usePricing` hook fetches from `/api/v1/pricing/current` which reads
from dynamic variables. No code changes needed.

### Step 3: Verify Across Pages

- [ ] Quote Calculator displays new values
- [ ] Menu page displays new values
- [ ] Booking page enforces new minimum
- [ ] ValueProposition section shows new values
- [ ] FAQs reflect new pricing

---

## 📁 Implementation Files

### Frontend

| File | Purpose |
|------|---------|
| `hooks/usePricing.ts` | Centralized pricing data access |
| `lib/data/pricingTemplates.ts` | Default values & fallbacks |
| `components/quote/QuoteCalculator.tsx` | Quote calculation UI |
| `components/booking/modules/EventDetailsSection.tsx` | Booking cost display |

### Backend

| File | Purpose |
|------|---------|
| `services/dynamic_variables_service.py` | Dynamic variables CRUD |
| `routers/v1/public_quote.py` | Quote calculation endpoint |
| `schemas/pricing.py` | Pricing data models |
| `db/models/dynamic_variables.py` | Database model |

---

## ✅ Validation Checklist

Before changing any pricing:

- [ ] Update backend dynamic variables
- [ ] Test quote calculator with various scenarios
- [ ] Verify minimum order enforcement
- [ ] Check travel fee calculations
- [ ] Update this documentation
- [ ] Notify AI system of changes

---

## 🔗 Related Docs

- [Dynamic Variables System](../02-IMPLEMENTATION/DYNAMIC_VARIABLES.md)
- [Booking Flow](../02-IMPLEMENTATION/BOOKING_SYSTEM.md)
- [AI Knowledge Base](../03-FEATURES/AI_KNOWLEDGE_BASE.md)
