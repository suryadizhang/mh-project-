# Batch 2 Addendum: Akaunting Integration & Chef Payroll

**Created:** December 27, 2025 **Purpose:** Extends Batch 2 scope with
Akaunting integration per SSoT decisions **Parent Doc:**
[BATCH_CHECKLISTS.md](./BATCH_CHECKLISTS.md)

---

## Scope Addition: Akaunting Integration

**User Decision:** Separate Akaunting company per station (for
multi-station tax compliance)

### Pre-Development Checklist (Add to Batch 2)

```markdown
□ Docker ready on VPS □ Cloudflare tunnel for
accounting.mysticdatanode.net configured □ Akaunting Docker image
pulled □ Initial company data prepared (Fremont station) □ Chart of
Accounts for catering business defined
```

### Akaunting Deployment Tasks

```markdown
AKAUNTING SETUP □ Configure Cloudflare tunnel for
accounting.mysticdatanode.net □ Run docker/akaunting/install.sh □
Create initial company: "My Hibachi - Fremont" □ Configure California
state tax settings □ Set up Chart of Accounts:

- Revenue: Catering Services, Tips Received, Merchandise
- Expenses: Chef Wages, Travel Reimbursement, Food Costs, Equipment
- Assets: Bank Account, Stripe Pending, Petty Cash
- Liabilities: Deposits Held, Taxes Payable □ Create admin user for
  accounting access □ Set up backup schedule for Akaunting database
```

### Sync Services Development

```markdown
AKAUNTING CLIENT □ Create
apps/backend/src/services/akaunting/akaunting_client.py

- HTTP client with API authentication
- Company selection based on station_id
- Error handling and retry logic □ Add AKAUNTING_API_KEY to GSM
  secrets □ Add station_id → company_id mapping table

INVOICE SYNC (Booking → Akaunting Invoice) □ Create
apps/backend/src/services/akaunting/invoice_sync_service.py □ On
booking completion (status = COMPLETED):

- Create Akaunting invoice with:
  - Customer name, contact
  - Service date
  - Line items (adults × price, children × price)
  - Add-ons (upgrades, extras)
  - Travel fee (if applicable)
  - Tax calculation
  - Deposit already paid
  - Balance due
- Link invoice_id to booking record □ Handle invoice updates (if
  booking modified) □ Handle invoice void (if booking canceled)

PAYMENT SYNC (Stripe → Akaunting) □ Create
apps/backend/src/services/akaunting/payment_sync_service.py □ On
Stripe webhook payment_intent.succeeded:

- Find linked Akaunting invoice
- Record payment against invoice
- Handle partial payments (deposit vs balance)
- Record payment method (Stripe reference) □ On Stripe webhook
  charge.refunded:
- Create refund record in Akaunting
- Link to original payment
- Update invoice status

TIP TRACKING □ Tips recorded as separate income line □ Link tip to
chef for payout tracking □ Tip income reporting for tax purposes
```

### Chef Payroll via Akaunting Vendors (Per User Decision)

**Decision:** Chefs are Akaunting Vendors (not custom payroll system)

```markdown
VENDOR SETUP □ Create
apps/backend/src/services/akaunting/vendor_sync_service.py □ When chef
onboarded:

- Create Akaunting vendor record
- Set up vendor contact info
- Link vendor_id to chef record □ Vendor fields: name, email, phone,
  address, tax_id (if contractor)

CHEF PAYMENT BILLS □ On booking completion, create vendor bill:

- Vendor: Assigned chef
- Line items:
  - Base event pay: $X per event
  - Mileage reimbursement: $0.67/mile × distance
  - Tips collected: 100% to chef
- Due date: Next payroll date □ Aggregate bills for weekly/bi-weekly
  payroll □ Mark bills as paid when chef paid

PAYROLL REPORTING □ GET /api/v1/admin/chef-payroll - List pending
payments □ GET /api/v1/admin/chef-payroll/{chef_id}/history - Payment
history □ Generate payroll summary report (per period) □ Export for
external payroll processing

ADMIN UI □ Chef payment dashboard (pending, completed) □
Approve/schedule payments □ View payment history per chef □ Tips
breakdown report
```

### Multi-Station Company Structure

```markdown
STATION → COMPANY MAPPING □ Create station_akaunting_companies table:

- station_id (FK to identity.stations)
- akaunting_company_id
- company_name
- tax_settings (JSON)
- is_active □ Each station gets own Akaunting company □ Sync services
  use station_id to select company

FUTURE STATION EXPANSION □ When new station created:

- Create new Akaunting company
- Configure tax settings for jurisdiction
- Create Chart of Accounts (copy from template)
- Update station_akaunting_companies
```

### Testing Checklist

```markdown
AKAUNTING INTEGRATION TESTS □ Booking creates Akaunting invoice
correctly □ Invoice line items match booking details □ Stripe payment
recorded in Akaunting □ Partial payments (deposit + balance) handled □
Refund creates refund record □ Chef vendor created on onboard □ Chef
bill created on booking completion □ Tips correctly attributed to chef

MULTI-STATION TESTS □ Bookings route to correct Akaunting company □
Station A invoice goes to Company A □ Station B invoice goes to
Company B □ Reports filter by station/company
```

### Acceptance Criteria

- [ ] Akaunting accessible at accounting.mysticdatanode.net
- [ ] All completed bookings sync to Akaunting invoices
- [ ] All Stripe payments recorded in Akaunting
- [ ] Chefs set up as vendors
- [ ] Chef payments tracked via vendor bills
- [ ] Multi-station company structure working
- [ ] Admin can access accounting reports

---

## Integration with Existing Batch 2 Tasks

The Akaunting integration should be done AFTER:

1. Stripe payment flow complete
2. Webhook handling stable
3. Invoice generation working

Then:

1. Connect invoice generation to Akaunting sync
2. Add payment sync to Stripe webhook handlers
3. Implement chef payroll on booking completion

---

## Related Files

- [SSOT_IMPLEMENTATION_PLAN.md](./SSOT_IMPLEMENTATION_PLAN.md) - Phase
  5 details
- [BATCH_CHECKLISTS.md](./BATCH_CHECKLISTS.md) - Main Batch 2
  checklist
- `docker/akaunting/` - Docker setup files
