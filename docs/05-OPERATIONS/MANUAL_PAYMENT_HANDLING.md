# Manual Payment Handling Guide

**Last Updated:** 2025-01-30 **Status:** Active **Relates To:**
Payment reconciliation, Venmo/Zelle deposits, booking management

---

## Overview

My Hibachi accepts multiple payment methods including **Venmo
Business**, **Zelle Business**, **Cash**, and **Credit Card
(Stripe)**. This document explains how to handle manual payments that
occur outside of the automated Stripe system.

---

## 🏦 Accepted Payment Methods

| Method                   | Automated?         | Reconciliation                 |
| ------------------------ | ------------------ | ------------------------------ |
| **Stripe (Credit Card)** | ✅ Fully automated | Automatic via webhooks         |
| **Venmo Business**       | ❌ Manual          | Requires manual database entry |
| **Zelle Business**       | ❌ Manual          | Requires manual database entry |
| **Cash**                 | ❌ Manual          | Recorded at event completion   |

---

## ⚠️ Understanding "No Matching Payment Found" Errors

### Why This Happens

When you see `"No matching payment found for booking X"` in logs or
admin dashboards, this is **EXPECTED BEHAVIOR** for:

1. **Phone/Text Bookings** - Customer books via text (916) 740-8768
   and pays via Venmo/Zelle
2. **Venmo Business Deposits** - Payment received in Venmo, booking
   created manually
3. **Zelle Business Deposits** - Payment received in Zelle, booking
   created manually
4. **Cash Deposits** - Customer pays deposit in person, booking
   created without Stripe

### This is NOT an Error

The payment reconciliation system looks for Stripe `payment_intent_id`
in the database. Manual payments don't have Stripe IDs, so they appear
as "unmatched."

**Correct interpretation:**

- ❌ "Error! Payment missing!"
- ✅ "This is a manual payment booking - payment was received outside
  Stripe"

---

## 📝 Manual Booking Workflow

### Step 1: Receive Payment via Venmo/Zelle

1. Customer contacts (916) 740-8768 to book
2. Customer sends $100 deposit via Venmo or Zelle
3. Confirm receipt in Venmo Business or Zelle Business app
4. Save transaction ID for records

### Step 2: Create Booking in Database

**Option A: Via Admin Panel (Preferred)**

1. Go to Admin Panel → Bookings → Create Booking
2. Fill in customer details, event date, guest count
3. In Payment section, select "Manual Payment"
4. Enter payment notes: "Venmo deposit received - Transaction #XXXXX"
5. Save booking

**Option B: Direct Database Entry (Advanced)**

```sql
-- Insert booking with manual payment flag
INSERT INTO core.bookings (
    customer_id,
    event_date,
    event_time,
    venue_address,
    total_guests,
    status,
    payment_method,
    deposit_paid,
    deposit_amount_cents,
    notes,
    created_at
) VALUES (
    'customer-uuid',
    '2025-02-15',
    '18:00',
    '123 Main St, City, CA 12345',
    15,
    'confirmed',
    'venmo',  -- or 'zelle', 'cash'
    true,
    10000,  -- $100 in cents
    'Deposit via Venmo - Txn #12345',
    NOW()
);
```

### Step 3: Record Payment in Payments Table

```sql
-- Record the manual payment
INSERT INTO core.payments (
    booking_id,
    amount_cents,
    payment_type,
    payment_method,
    status,
    external_reference,
    notes,
    created_at
) VALUES (
    'booking-uuid',
    10000,  -- $100 in cents
    'deposit',
    'venmo',  -- or 'zelle', 'cash'
    'completed',
    'venmo-txn-12345',  -- From Venmo app
    'Received via Venmo Business',
    NOW()
);
```

---

## 🔄 Payment Reconciliation Process

### Daily Reconciliation Steps

1. **Check Venmo Business transactions**

   - Open Venmo Business app
   - Note all deposits received
   - Cross-reference with bookings in admin panel

2. **Check Zelle Business transactions**

   - Log into business banking
   - Note all Zelle deposits
   - Cross-reference with bookings

3. **Update booking records**
   - For each payment, ensure matching booking exists
   - If booking missing, create it
   - If payment recorded, mark as reconciled

### Monthly Audit Query

```sql
-- Find bookings without linked payments (potential manual payments)
SELECT
    b.id,
    b.customer_id,
    b.event_date,
    b.status,
    b.payment_method,
    b.deposit_paid,
    b.notes
FROM core.bookings b
LEFT JOIN core.payments p ON b.id = p.booking_id
WHERE p.id IS NULL
AND b.deposit_paid = true
ORDER BY b.event_date DESC;
```

---

## 📊 Payment Status Reference

| Status         | Meaning                                          |
| -------------- | ------------------------------------------------ |
| `pending`      | Awaiting payment (Stripe checkout not completed) |
| `deposit_paid` | Deposit received (manual or Stripe)              |
| `confirmed`    | Booking confirmed, deposit verified              |
| `paid_in_full` | Full payment received                            |
| `completed`    | Event completed, all payments settled            |
| `refunded`     | Deposit refunded                                 |
| `cancelled`    | Booking cancelled                                |

---

## 🛠️ Troubleshooting

### Scenario 1: Customer says "I paid" but no record exists

**Steps:**

1. Ask for Venmo/Zelle transaction screenshot
2. Check Venmo Business app for transaction
3. If found, create booking + payment records
4. If not found, ask customer to resend with note

### Scenario 2: Double-booking with same payment

**Prevention:**

- Always check for existing booking before creating new one
- Use customer phone number as unique identifier

**Fix:**

```sql
-- Check for duplicate bookings
SELECT * FROM core.bookings
WHERE customer_phone = '555-123-4567'
AND event_date = '2025-02-15';
```

### Scenario 3: Refund requested for manual payment

**Process:**

1. Verify original payment in Venmo/Zelle
2. Issue refund via same platform
3. Update database:

```sql
UPDATE core.payments
SET status = 'refunded',
    refund_amount_cents = 10000,
    refund_date = NOW(),
    notes = notes || ' | Refunded via Venmo'
WHERE id = 'payment-uuid';

UPDATE core.bookings
SET status = 'cancelled',
    deposit_paid = false
WHERE id = 'booking-uuid';
```

---

## 📋 Best Practices

### DO ✅

- Record payment method in booking notes
- Save Venmo/Zelle transaction IDs
- Reconcile payments weekly at minimum
- Use consistent payment_method values: `venmo`, `zelle`, `cash`,
  `stripe`

### DON'T ❌

- Create bookings without recording payment source
- Assume "no payment found" = actual error
- Delete manual payment records (mark as cancelled instead)
- Mix personal and business Venmo/Zelle accounts

---

## 📞 Venmo/Zelle Business Contact Info

**Venmo Business:** @MyHibachi (linked to business email) **Zelle
Business:** cs@myhibachichef.com (linked to business bank)

---

## Related Documentation

- [Booking System](../02-IMPLEMENTATION/BOOKING_SYSTEM.md)
- [Payment Processing](../02-IMPLEMENTATION/PAYMENT_FLOW.md)
- [Stripe Integration](./STRIPE_WEBHOOKS.md)
- [Admin Panel Guide](../03-FEATURES/ADMIN_PANEL.md)

---

## Changelog

| Date       | Change                        |
| ---------- | ----------------------------- |
| 2025-01-30 | Initial documentation created |
