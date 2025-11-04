# Corrected API Test Schemas

**Purpose:** Fix 422 validation errors by using correct request
schemas

---

## ❌ Previous Test Errors

### Issue 1: Quote Calculator

**Wrong Payload (422 Error):**

```json
{
  "guests": 30,
  "package_type": "standard",
  "add_ons": []
}
```

**✅ Correct Payload:**

```json
{
  "adults": 30,
  "children": 0,
  "salmon": 0,
  "scallops": 0,
  "filet_mignon": 5,
  "lobster_tail": 5,
  "third_proteins": 0,
  "yakisoba_noodles": 2,
  "extra_fried_rice": 0,
  "extra_vegetables": 0,
  "edamame": 0,
  "gyoza": 0,
  "venue_address": "123 Main St, Sacramento, CA 95814",
  "zip_code": "95814"
}
```

**Endpoint:** `POST /api/v1/public/quote/calculate`

**Schema Requirements:**

- `adults` (required): Number of adults, min 1, max 100
- `children` (optional): Number of children 6-12, default 0
- Protein upgrades (all optional, default 0):
  - `salmon`, `scallops`, `filet_mignon`: +$5 each
  - `lobster_tail`: +$15 each
  - `third_proteins`: +$10 each (3rd protein rule)
- Add-ons (all optional, default 0):
  - `yakisoba_noodles`: +$6 each
  - `extra_fried_rice`: +$6 each
  - `extra_vegetables`: +$5 each
  - `edamame`: +$4 each
  - `gyoza`: +$10 each
- `venue_address` (optional): Full address for travel fee calculation
- `zip_code` (optional): ZIP code for travel fee estimation

---

### Issue 2: Payment Calculator

**Wrong Payload (422 Error):**

```json
{
  "guests": 25,
  "base_price": 45.0
}
```

**✅ Correct Payload:**

```json
{
  "base_amount": 1000.0,
  "tip_amount": 200.0,
  "payment_method": "zelle"
}
```

**Endpoint:** `POST /api/v1/payments/calculate`

**Schema Requirements:**

- `base_amount` (required): Base payment amount, must be > 0, Decimal
- `tip_amount` (optional): Tip amount, must be >= 0, default 0
- `payment_method` (required): One of: "zelle", "venmo", "stripe"

**Valid Payment Methods:**

- `zelle`: 0% fee (FREE)
- `venmo`: 0% fee (FREE)
- `stripe`: 2.9% + $0.30

---

### Issue 3: Lead Capture

**Wrong Payload (422 Error):**

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "phone": "555-1234",
  "source": "website",
  "interest_type": "booking"
}
```

**✅ Correct Payload:**

```json
{
  "name": "John Doe",
  "phone": "5551234567",
  "email": "john@example.com",
  "event_date": "2025-12-15",
  "guest_count": 50,
  "budget": "$2000-3000",
  "location": "Los Angeles, CA",
  "message": "Looking for hibachi catering",
  "source": "website",
  "email_consent": true,
  "sms_consent": true
}
```

**Endpoint:** `POST /api/v1/public/leads`

**Schema Requirements:**

- `name` (required): Full name, min 2, max 100 characters
- `phone` (required): Phone number, min 10, max 20 characters
  - Accepts formats: (555) 123-4567, 555-123-4567, 5551234567,
    +15551234567
  - Cleaned to digits only (10-15 digits)
- `email` (optional but recommended): Valid email address
- `event_date` (optional): Date in format "YYYY-MM-DD"
- `guest_count` (optional): Number of guests, min 1, max 500
- `budget` (optional): Budget range string, max 50 characters
- `location` (optional): Event location or zip code, max 200
  characters
- `message` (optional): Additional message, max 2000 characters
- `source` (optional): Lead source, default "website"
- `email_consent` (optional): Boolean, default false
- `sms_consent` (optional): Boolean, default false
- `honeypot` (optional): Spam prevention field (should be empty)

---

### Issue 4: Public Bookings

**Status:** Endpoint not implemented yet

**Expected Endpoint:** `POST /api/v1/public/bookings`

**Note:** This endpoint was tested but doesn't exist in the current
backend. Need to implement or remove from tests.

---

## ✅ Corrected PowerShell Test Commands

### Test 1: Quote Calculator

```powershell
$quote = @{
    adults = 30
    children = 2
    filet_mignon = 5
    lobster_tail = 5
    yakisoba_noodles = 2
    venue_address = "123 Main St, Sacramento, CA 95814"
    zip_code = "95814"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/public/quote/calculate" `
    -Method POST `
    -Body $quote `
    -ContentType "application/json"

Write-Host "✅ Quote: $($response.grand_total)" -ForegroundColor Green
Write-Host "Travel Fee: $($response.travel_info.travel_fee)" -ForegroundColor Cyan
```

### Test 2: Payment Calculator

```powershell
$payment = @{
    base_amount = 1000.00
    tip_amount = 200.00
    payment_method = "zelle"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/payments/calculate" `
    -Method POST `
    -Body $payment `
    -ContentType "application/json"

Write-Host "✅ Total: $($response.selected_method.total_amount)" -ForegroundColor Green
Write-Host "Fee: $($response.selected_method.processing_fee)" -ForegroundColor Cyan
```

### Test 3: Lead Capture

```powershell
$lead = @{
    name = "John Doe"
    phone = "5551234567"
    email = "john@example.com"
    event_date = "2025-12-15"
    guest_count = 50
    budget = "$2000-3000"
    location = "Los Angeles, CA"
    message = "Looking for hibachi catering"
    source = "website"
    email_consent = $true
    sms_consent = $true
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/public/leads" `
    -Method POST `
    -Body $lead `
    -ContentType "application/json"

Write-Host "✅ Lead created: $($response.lead_id)" -ForegroundColor Green
```

### Test 4: Payment Method Comparison

```powershell
$compare = @{
    base_amount = 1000.00
    tip_amount = 200.00
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/payments/compare" `
    -Method POST `
    -Body $compare `
    -ContentType "application/json"

Write-Host "✅ Best value: $($response.best_value)" -ForegroundColor Green
$response.methods | ForEach-Object {
    Write-Host "  $($_.method_display_name): $($_.total_amount) (fee: $($_.processing_fee))" -ForegroundColor Cyan
}
```

---

## Summary of Schema Fixes

| Endpoint               | Previous (Wrong)         | Corrected                                                 |
| ---------------------- | ------------------------ | --------------------------------------------------------- |
| **Quote Calculator**   | `guests`, `package_type` | `adults`, `children`, upgrades                            |
| **Payment Calculator** | `guests`, `base_price`   | `base_amount`, `tip_amount`, `payment_method`             |
| **Lead Capture**       | Missing required `phone` | `name` (required), `phone` (required), `email` (optional) |
| **Public Bookings**    | Tested but doesn't exist | Need to implement or skip                                 |

---

## Next Steps

1. **Re-run Tests with Corrected Schemas** ✅
   - Update test suite to use correct payloads
   - Verify all 422 errors are fixed

2. **Document API Schemas** ✅
   - Update API documentation with correct examples
   - Add schema validation examples

3. **Frontend Alignment** 🔧
   - Verify frontend sends correct payloads
   - Update form validation to match backend schemas

4. **Test Coverage** 📊
   - Add integration tests with correct schemas
   - Verify all public endpoints work

---

**Date:** November 3, 2025  
**Status:** Schemas corrected, ready for re-testing
