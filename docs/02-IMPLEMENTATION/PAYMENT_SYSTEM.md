# Payment System Architecture

**Last Updated:** 2025-01-31 **Status:** Active **Relates To:**
[Business Model](../../.github/instructions/21-BUSINESS_MODEL.instructions.md),
[SSoT Architecture](../../.github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md)

---

## Overview

The My Hibachi payment system handles all monetary transactions for
hibachi catering bookings. It integrates with Stripe for card payments
and supports Zelle/Venmo as free alternatives.

## Payment Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PAYMENT FLOW OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BOOKING CREATED                                                             │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────┐                                                        │
│  │  DEPOSIT PHASE   │ $100 fixed deposit (refundable 7+ days before event)  │
│  │  ─────────────── │                                                        │
│  │  • Stripe Card   │ 2.9% + $0.30 fee                                       │
│  │  • Zelle/Venmo   │ FREE (0% fee) - saves ~$3                             │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │  BALANCE PHASE   │ Remaining amount due before/on event day              │
│  │  ─────────────── │                                                        │
│  │  balance_due =   │                                                        │
│  │  total_amount    │ (adults × $55) + (children × $30) + upgrades          │
│  │  - deposit       │ - $100                                                │
│  │  + travel_fee    │ $2/mile after 30 free miles (NOT TAXABLE)             │
│  │  + tax           │ Location-based sales tax on food only                 │
│  │  ─────────────── │                                                        │
│  │  • Stripe Card   │ 2.9% + $0.30 fee                                       │
│  │  • Zelle/Venmo   │ FREE (0% fee)                                         │
│  │  • Cash          │ On-site                                                │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │   TIPS PHASE     │ Optional gratuity (20-35% suggested)                  │
│  │  ─────────────── │                                                        │
│  │  • NOT TAXABLE   │ Goes directly to chef                                 │
│  │  • Cash/Venmo    │ Preferred (direct to chef)                            │
│  │  • Card (Stripe) │ Processed through system                              │
│  └──────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Fee Structure

### Payment Method Fees

| Payment Method     | Fee          | Customer Sees | Notes                |
| ------------------ | ------------ | ------------- | -------------------- |
| **Stripe (Card)**  | 2.9% + $0.30 | Full price    | Standard Stripe fees |
| **Zelle**          | 0%           | Full price    | FREE for customer    |
| **Venmo Business** | 0%           | Full price    | FREE for customer    |
| **Cash**           | 0%           | Full price    | On-site only         |

### Fee Calculation Example

For a $500 balance payment:

| Method | Fee Absorbed | Customer Pays | Business Receives |
| ------ | ------------ | ------------- | ----------------- |
| Card   | $14.80       | $500.00       | $485.20           |
| Zelle  | $0.00        | $500.00       | $500.00           |

**💡 Zelle/Venmo saves ~3% in processing fees!**

## Tax Rules

### What's Taxable

| Item                           | Taxable? | Reason                               |
| ------------------------------ | -------- | ------------------------------------ |
| **Food/Service (balance_due)** | ✅ YES   | Catering services are taxable        |
| **Upgrades (Filet, Lobster)**  | ✅ YES   | Part of food service                 |
| **Tips/Gratuity**              | ❌ NO    | Tips are not subject to sales tax    |
| **Travel Fee**                 | ❌ NO    | Reimbursement for chef's gas/mileage |

### Tax Calculation

```
tax_amount = (balance_due - travel_fee) × local_sales_tax_rate

// Example (8.25% CA tax):
balance_due = $500
travel_fee = $30
taxable_amount = $500 - $30 = $470
tax = $470 × 0.0825 = $38.78
```

## Stripe Package Structure

```
apps/backend/src/routers/v1/stripe/
├── __init__.py          # Package exports and router composition
├── schemas.py           # Pydantic request/response models
├── utils.py             # Helper functions (fee rates, loyalty)
├── checkout.py          # Checkout Session creation
├── payment_intents.py   # Payment Intent creation + Customer Portal
├── payments.py          # Payment listing
├── invoices.py          # Invoice listing
├── refunds.py           # Refund processing (admin only)
├── analytics.py         # Payment analytics (admin only)
├── dashboard.py         # Customer payment dashboard
└── webhooks.py          # Consolidated webhook handler
```

## API Endpoints

### Customer Endpoints

| Endpoint                               | Method | Description                    |
| -------------------------------------- | ------ | ------------------------------ |
| `/api/v1/stripe/checkout/session`      | POST   | Create Checkout Session        |
| `/api/v1/stripe/checkout/session/{id}` | GET    | Verify session status          |
| `/api/v1/stripe/payment-intent`        | POST   | Create Payment Intent          |
| `/api/v1/stripe/payment-intent/{id}`   | GET    | Get Payment Intent details     |
| `/api/v1/stripe/portal`                | POST   | Create Customer Portal session |
| `/api/v1/stripe/payments`              | GET    | List customer's payments       |
| `/api/v1/stripe/invoices`              | GET    | List customer's invoices       |
| `/api/v1/stripe/dashboard`             | GET    | Customer payment dashboard     |
| `/api/v1/stripe/calculate-total`       | GET    | Calculate total with tax       |
| `/api/v1/stripe/suggested-tips`        | GET    | Get suggested tip amounts      |
| `/api/v1/stripe/lookup`                | POST   | Lookup customer by phone/email |

### Public Endpoints (No Auth Required)

| Endpoint                         | Method | Description              |
| -------------------------------- | ------ | ------------------------ |
| `/api/v1/public/quote/calculate` | POST   | Calculate quote estimate |

### Admin Endpoints

| Endpoint                   | Method | Description       | Permission      |
| -------------------------- | ------ | ----------------- | --------------- |
| `/api/v1/stripe/refund`    | POST   | Process refund    | MANAGE_PAYMENTS |
| `/api/v1/stripe/analytics` | GET    | Payment analytics | VIEW_ANALYTICS  |

### Webhook Endpoint

| Endpoint                 | Method | Description           |
| ------------------------ | ------ | --------------------- |
| `/api/v1/stripe/webhook` | POST   | Receive Stripe events |

### New Endpoint Details

#### Calculate Total with Tax

**GET** `/api/v1/stripe/calculate-total`

Calculates total payment including tax. Tips and travel fees are
excluded from taxable amount.

**Query Parameters:**

| Parameter          | Type | Required | Description                       |
| ------------------ | ---- | -------- | --------------------------------- |
| `balance_cents`    | int  | Yes      | Remaining balance in cents        |
| `travel_fee_cents` | int  | Yes      | Travel fee in cents (not taxable) |
| `tip_cents`        | int  | Yes      | Tip amount in cents (not taxable) |

**Response:**

```json
{
  "taxable_amount_cents": 48000,
  "tax_amount_cents": 3960,
  "travel_fee_cents": 2000,
  "tip_cents": 1000,
  "subtotal_cents": 50000,
  "total_cents": 54960,
  "tax_rate": 0.0825
}
```

#### Suggested Tips

**GET** `/api/v1/stripe/suggested-tips`

Returns suggested tip amounts based on percentage of subtotal.

**Query Parameters:**

| Parameter      | Type | Required | Description       |
| -------------- | ---- | -------- | ----------------- |
| `amount_cents` | int  | Yes      | Subtotal in cents |

**Response:**

```json
{
  "tip_20_percent": 10000,
  "tip_25_percent": 12500,
  "tip_30_percent": 15000,
  "tip_35_percent": 17500
}
```

#### Customer Lookup

**POST** `/api/v1/stripe/lookup`

Lookup customer and their unpaid bookings by phone or email.

**Request Body:**

```json
{
  "phone": "+15551234567",
  "email": "customer@example.com"
}
```

_At least one of `phone` or `email` is required._

**Query Parameters:**

| Parameter  | Type  | Required | Description                |
| ---------- | ----- | -------- | -------------------------- |
| `tax_rate` | float | No       | Tax rate (default: 0.0825) |

**Response:**

```json
{
  "customer_id": "uuid",
  "customer_name": "John Doe",
  "unpaid_bookings": [
    {
      "booking_id": "uuid",
      "event_date": "2025-02-15",
      "balance_due_cents": 50000,
      "total_cents": 60000,
      "deposit_paid_cents": 10000
    }
  ],
  "loyalty_tier": "Gold",
  "total_lifetime_spent_cents": 250000
}
```

#### Public Quote Calculator

**POST** `/api/v1/public/quote/calculate`

Calculate an instant quote without authentication.

**Request Body:**

```json
{
  "adults": 10,
  "children": 2,
  "salmon": 2,
  "filet_mignon": 3,
  "lobster_tail": 1,
  "venue_address": "123 Main St, Fremont, CA 94539"
}
```

**Required Fields:** `adults` (1-100)

**Optional Fields:** `children`, `salmon`, `scallops`, `filet_mignon`,
`lobster_tail`, `extra_proteins`, `yakisoba_noodles`,
`extra_fried_rice`, `extra_vegetables`, `edamame`, `gyoza`,
`venue_address`, `zip_code`, `venue_lat`, `venue_lng`

**Response:**

```json
{
  "subtotal_cents": 68500,
  "travel_fee_cents": 2000,
  "tax_cents": 5651,
  "total_cents": 76151,
  "breakdown": {
    "base_price_cents": 55000,
    "children_price_cents": 6000,
    "upgrades_cents": 5500,
    "addons_cents": 2000
  }
}
```

## Receipt Emails

Stripe automatically sends receipt emails when configured:

```python
# checkout.py - Checkout Session
session = stripe.checkout.Session.create(
    payment_intent_data={
        "receipt_email": customer_email,  # ✅ Receipt sent automatically
    },
)

# payment_intents.py - Direct Payment Intent
intent = stripe.PaymentIntent.create(
    receipt_email=request.customer_email or current_user.email,  # ✅ Receipt sent
)
```

**Note:** Receipt emails can be sent to email OR phone (via Stripe SMS
receipts).

## Webhook Handling

### Supported Events

| Event                           | Handler                     | Action               |
| ------------------------------- | --------------------------- | -------------------- |
| `payment_intent.succeeded`      | Update StripePayment status | Mark booking as paid |
| `payment_intent.payment_failed` | Update StripePayment status | Log failure          |
| `payment_intent.canceled`       | Update StripePayment status | Handle cancellation  |
| `customer.created`              | Log customer creation       | Audit trail          |
| `customer.updated`              | Log customer update         | Audit trail          |
| `invoice.payment_succeeded`     | Update invoice status       | Confirm payment      |
| `invoice.payment_failed`        | Update invoice status       | Alert admin          |
| `checkout.session.completed`    | Process checkout            | Update booking       |
| `charge.refunded`               | Update refund status        | Adjust balances      |
| `charge.dispute.created`        | **CRITICAL** alert          | Dispute handling     |

### Signature Verification

All webhooks are verified using Stripe's signature:

```python
@router.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
```

## Customer Lookup Flow

Customers can lookup their remaining balance by phone or email:

```
┌────────────────────────────────────────────────────────────────┐
│                  CUSTOMER BALANCE LOOKUP                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Customer provides: Phone OR Email                              │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────┐                                        │
│  │ Lookup Customer     │ Search by encrypted PII                │
│  │ (phone_encrypted    │                                        │
│  │  or email_encrypted)│                                        │
│  └──────────┬──────────┘                                        │
│             │                                                   │
│             ▼                                                   │
│  ┌─────────────────────┐                                        │
│  │ Get Active Bookings │ Find unpaid bookings                   │
│  │ with balance_due > 0│                                        │
│  └──────────┬──────────┘                                        │
│             │                                                   │
│             ▼                                                   │
│  ┌─────────────────────┐                                        │
│  │ Return:             │                                        │
│  │ • Booking details   │                                        │
│  │ • balance_due_cents │ Amount remaining                       │
│  │ • Optional: Add tip │ Customer can add 20-35%                │
│  └─────────────────────┘                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Loyalty System

Customer loyalty tiers based on total spending:

| Tier       | Total Spent | Benefits                          |
| ---------- | ----------- | --------------------------------- |
| **VIP**    | $5,000+     | Priority booking, exclusive perks |
| **Gold**   | $2,000+     | Special offers                    |
| **Silver** | $500+       | Recognition                       |
| **New**    | $0+         | Welcome offers                    |

Determined by `determine_loyalty_status()` in `utils.py`.

## Database Models

### StripePayment (core schema)

```python
class StripePayment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "core"}

    id: UUID
    booking_id: UUID (FK to bookings)
    user_id: UUID (FK to users)  # Customer who paid
    amount_cents: int  # Amount in cents
    currency: str  # "usd"
    status: PaymentStatus  # PENDING, SUCCEEDED, FAILED, REFUNDED
    payment_method: PaymentMethod  # STRIPE, ZELLE, VENMO
    stripe_payment_intent_id: str
    stripe_customer_id: str
    description: str
    refunded_amount: int
    refunded_at: datetime
    created_at: datetime
    updated_at: datetime
```

### Payment Statuses

```python
class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
```

### Payment Methods

```python
class PaymentMethod(str, Enum):
    STRIPE = "stripe"  # Credit/debit card
    VENMO = "venmo"    # 0% fee
    ZELLE = "zelle"    # 0% fee
```

## Stripe Dashboard Features

### Customer Portal

Self-service portal for customers to:

- View payment history
- Update payment methods
- Download invoices/receipts
- Manage billing information

Created via `/api/v1/stripe/portal` endpoint.

### Stripe Tax

Location-based automatic tax calculation:

- Uses customer's event venue address
- Applies local sales tax rates
- Excludes tips and travel fees from tax base

### Stripe Radar

Fraud protection:

- Machine learning fraud detection
- Automatic blocking of suspicious payments
- Dispute/chargeback management
- Risk scoring for each transaction

## Testing

### Webhook Testing (e2e)

See `e2e/api/stripe-webhooks.spec.ts` for:

- Signature verification tests
- Event handler tests
- Idempotency checks

### Test Mode

Development uses Stripe test mode:

- Test API keys: `sk_test_...`
- Test webhook secret: `whsec_...`
- Test card numbers: `4242424242424242`

## Security

### API Key Management

- **Production keys** stored in Google Secret Manager
- **Test keys** in `.env.local` (never committed)
- Keys rotated quarterly

### PII Protection

Customer phone/email stored encrypted:

- `email_encrypted`: AES-256 encrypted email
- `phone_encrypted`: AES-256 encrypted phone
- Decryption only for authorized operations

### Webhook Security

- All webhooks verified with Stripe signature
- Events stored for audit trail
- Idempotency enforced (duplicate events ignored)

## Related Documentation

- [Business Model](../../.github/instructions/21-BUSINESS_MODEL.instructions.md) -
  Pricing, deposits, tips
- [SSoT Architecture](../../.github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md) -
  Dynamic pricing
- [Quality Control](../../.github/instructions/22-QUALITY_CONTROL.instructions.md) -
  Pre-commit checks
- [Stripe API Docs](https://stripe.com/docs/api)
