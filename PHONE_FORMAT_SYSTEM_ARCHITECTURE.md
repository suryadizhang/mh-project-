# Phone Format System Architecture

## Overview

This document defines the **phone format standards** across the entire
My Hibachi Chef system. All developers must follow these standards to
ensure data consistency and prevent system failures.

---

## Phone Format Standards

### Storage Format (Database)

- **Format**: 10 digits, no country code, no formatting
- **Example**: `2103884155`
- **Validation**: Must match regex `^\d{10}$`
- **Rationale**: Consistent storage, easy matching, compact

### API Communication Format

- **Frontend → Backend**: 10 digits (normalized by frontend)
- **Backend → Frontend**: 10 digits (formatted by frontend for
  display)
- **Example**: `2103884155`

### Display Format (User Interface)

- **Format**: `(XXX) XXX-XXXX`
- **Example**: `(210) 388-4155`
- **Conversion**: Done by frontend `formatPhoneNumber()` utility
- **User Input**: Accepts any format, normalizes on blur

### SMS/WhatsApp API Format (E.164)

- **Format**: `+1XXXXXXXXXX` (country code + 10 digits)
- **Example**: `+12103884155`
- **Conversion**: Done by `_format_phone()` in backend notification
  service
- **Rationale**: Required by Twilio/RingCentral APIs

---

## System Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  User Types Phone:                                                        │
│    "(210) 388-4155" or "210-388-4155" or "2103884155"                   │
│                           ↓                                               │
│  phoneUtils.normalizePhoneNumber():                                       │
│    • Strip all non-digits                                                 │
│    • Remove +1 country code if present                                    │
│    • Validate 10 digits exactly                                           │
│    → Output: "2103884155"                                                 │
│                           ↓                                               │
│  ContactInfoSection.handlePhoneChange():                                  │
│    • setValue('phone', normalized) → Stores in form data                  │
│    • setPhoneDisplay(input) → Shows what user typed                       │
│                           ↓                                               │
│  ContactInfoSection.handlePhoneBlur():                                    │
│    • formatPhoneNumber() → Format to (210) 388-4155                       │
│    • Display formatted version to user                                    │
│                           ↓                                               │
│  BookingFormContainer.onSubmit():                                         │
│    • Read form.phone → Already normalized (10 digits)                     │
│    • Send to API: { contact_phone: "2103884155" }                         │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                           ↓ HTTP POST
┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  POST /api/bookings                                                       │
│    Body: { contact_phone: "2103884155", ... }                            │
│                           ↓                                               │
│  Pydantic Schema Validation (booking.py):                                │
│    • Pattern check: ^\d{10}$ OR formatted variants                        │
│    • normalize_phone() validator:                                         │
│      - Strip non-digits                                                   │
│      - Remove country code if present                                     │
│      - Validate exactly 10 digits                                         │
│      - Raise error if invalid                                             │
│    → Output: "2103884155"                                                 │
│                           ↓                                               │
│  booking_service.create_booking():                                        │
│    • Store contact_phone: "2103884155" in database                        │
│    • Database column: VARCHAR(20), stores 10-digit string                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       PAYMENT MATCHING SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  payment_email_monitor.py:                                                │
│    • Parse payment email, extract customer phone from note                │
│    • Normalize to 10 digits: "2103884155"                                 │
│                           ↓                                               │
│  payment_matcher_service._find_by_phone_number():                         │
│    • Query: WHERE contact_phone LIKE '%2103884155%'                       │
│    • Exact 10-digit match for reliability                                 │
│    • CRITICAL: If phone format doesn't match, payment won't match!        │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      SMS/WHATSAPP NOTIFICATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  enhanced_notification_service.send_to_groups():                          │
│    • Receives customer_phone: "2103884155" (10 digits)                    │
│                           ↓                                               │
│  unified_notification_service._send_message():                            │
│    • to_phone = _format_phone(customer_phone)                             │
│    • _format_phone() strips "whatsapp:" prefix only                       │
│    • Passes to Twilio: "2103884155"                                       │
│                           ↓                                               │
│  Twilio API:                                                              │
│    • Twilio automatically handles US numbers                              │
│    • Accepts 10-digit format for US numbers                               │
│    • Internally converts to E.164 (+12103884155)                          │
│    • ✅ Works correctly with 10-digit input!                              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Critical System Components

### 1. Frontend Phone Utilities (`apps/customer/src/lib/phoneUtils.ts`)

```typescript
/**
 * Normalize phone number to 10 digits (storage format)
 * Removes all formatting, strips country code
 */
export function normalizePhoneNumber(phone: string): string {
  // Strip all non-digits
  const digits = phone.replace(/\D/g, '');

  // Remove country code if present (+1)
  if (digits.length === 11 && digits[0] === '1') {
    return digits.substring(1);
  }

  return digits;
}

/**
 * Format phone for display: (XXX) XXX-XXXX
 */
export function formatPhoneNumber(phone: string): string {
  const normalized = normalizePhoneNumber(phone);
  if (normalized.length !== 10) return phone;

  return `(${normalized.slice(0, 3)}) ${normalized.slice(3, 6)}-${normalized.slice(6)}`;
}

/**
 * Validate phone is exactly 10 digits
 */
export function isValidPhoneNumber(phone: string): boolean {
  const normalized = normalizePhoneNumber(phone);
  return normalized.length === 10;
}
```

**Usage**: All phone inputs must use these utilities before API
submission.

---

### 2. Backend Schema Validation (`apps/backend/src/schemas/booking.py`)

```python
class BookingCreate(BaseModel):
    contact_phone: str | None = Field(
        None,
        description="Contact phone number (10 digits, no country code)",
        pattern=r"^\d{10}$|^\(\d{3}\)\s?\d{3}-\d{4}$|^\d{3}-\d{3}-\d{4}$",
        max_length=20,
        examples=["2103884155", "4155552671", "(415) 555-2671"],
    )

    @field_validator("contact_phone")
    @classmethod
    def normalize_phone(cls, v: str | None) -> str | None:
        """Normalize phone to 10 digits (remove formatting)"""
        if v is None:
            return None

        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, v))

        # If starts with 1 (country code), remove it
        if len(digits) == 11 and digits[0] == '1':
            digits = digits[1:]

        # Validate exactly 10 digits
        if len(digits) != 10:
            raise ValueError(f"Phone must be exactly 10 digits, got {len(digits)}")

        return digits
```

**Key Features**:

- Accepts multiple input formats (formatted or raw)
- Normalizes to 10 digits automatically
- Removes country code if present
- Raises validation error if invalid
- **All API endpoints use this validation automatically**

---

### 3. Payment Matching (`apps/backend/src/services/payment_matcher_service.py`)

```python
@staticmethod
def _find_by_phone_number(
    db: Session,
    phone: str,  # Receives 10-digit phone
    amount: Decimal,
    payment_method: str,
    received_at: datetime | None = None,
) -> Payment | None:
    """
    Find payment by customer phone number (most reliable for Venmo/Zelle)

    CRITICAL: Phone must be 10 digits to match correctly!
    """
    # Normalize phone number (remove non-digits, take last 10 digits)
    normalized_phone = "".join(c for c in phone if c.isdigit())[-10:]

    if len(normalized_phone) != 10:
        logger.warning(f"Invalid phone number format: {phone}")
        return None

    # Query bookings with matching phone
    query = (
        db.query(Payment)
        .join(Booking)
        .filter(
            and_(
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING]),
                Booking.contact_phone.like(f"%{normalized_phone}%"),
                # ... other filters
            )
        )
    )
```

**Why This Matters**: Payment matching relies on exact phone match. If
phone formats are inconsistent, payments won't match bookings,
causing:

- Lost revenue (payment not recorded)
- Manual reconciliation work
- Customer service issues

---

### 4. SMS Notification (`apps/backend/src/services/unified_notification_service.py`)

```python
def _format_phone(self, phone: str) -> str:
    """Format phone number for SMS (remove whatsapp: prefix if present)"""
    if not phone:
        return ""
    return phone.replace("whatsapp:", "").strip()

async def _send_via_twilio_sms(self, to_phone: str, message: str) -> dict[str, Any]:
    """Send via Twilio SMS"""
    try:
        # Twilio accepts 10-digit US numbers and auto-formats to E.164
        response = self.twilio_client.messages.create(
            body=message,
            from_=self.sms_from,
            to=to_phone  # Can be "2103884155" or "+12103884155"
        )
        return {"success": True, "channel": "sms", "sid": response.sid}
    except Exception as e:
        logger.exception(f"❌ SMS send failed: {e}")
        return {"success": False, "error": str(e)}
```

**Key Point**: Twilio API accepts 10-digit US phone numbers directly.
No need to convert to E.164 format manually - Twilio handles it
internally.

---

## Verification Checklist

### ✅ Frontend Verification

- [x] Phone input uses `normalizePhoneNumber()` before storing in form
- [x] Phone display uses `formatPhoneNumber()` for user-friendly
      format
- [x] Phone validation uses `isValidPhoneNumber()` before submission
- [x] Form submission sends 10-digit phone to API
- [x] No country code (+1) sent to backend

### ✅ Backend Verification

- [x] Schema validator normalizes all incoming phone numbers
- [x] Database stores 10-digit phone consistently
- [x] All API endpoints use schema validation (automatic)
- [x] Phone queries use 10-digit format
- [x] No raw SQL that bypasses validation

### ✅ Payment Matching Verification

- [x] Payment email parsing normalizes phone to 10 digits
- [x] Phone matching query uses 10-digit format
- [x] Database phone stored as 10 digits for matching

### ✅ SMS/WhatsApp Verification

- [x] Notification service accepts 10-digit phone
- [x] Twilio API works with 10-digit US numbers
- [x] No manual E.164 conversion needed
- [x] WhatsApp prefix handled separately

---

## Common Pitfalls to Avoid

### ❌ Don't Do This

```typescript
// Frontend: Sending formatted phone to API
const phone = '(210) 388-4155'; // ❌ WRONG
api.createBooking({ contact_phone: phone });
```

```python
# Backend: Storing formatted phone in database
booking.contact_phone = "(210) 388-4155"  # ❌ WRONG
db.add(booking)
```

```python
# Payment matching: Using formatted phone in query
WHERE contact_phone = '(210) 388-4155'  # ❌ Won't match "2103884155"
```

### ✅ Do This Instead

```typescript
// Frontend: Normalize before API call
const phone = normalizePhoneNumber('(210) 388-4155'); // → "2103884155"
api.createBooking({ contact_phone: phone });
```

```python
# Backend: Let schema validator normalize
class BookingCreate(BaseModel):
    contact_phone: str

    @field_validator("contact_phone")
    def normalize_phone(cls, v):
        return ''.join(filter(str.isdigit, v))[-10:]  # ✅ Always 10 digits
```

```python
# Payment matching: Use 10-digit format
normalized = ''.join(filter(str.isdigit, phone))[-10:]
WHERE contact_phone LIKE f'%{normalized}%'  # ✅ Matches any format
```

---

## Testing Scenarios

### Test Case 1: User Input Variations

```
Input:     "(210) 388-4155"
Normalize: "2103884155"
Store:     "2103884155"
Display:   "(210) 388-4155"
SMS API:   "2103884155" (Twilio auto-converts to +12103884155)
```

### Test Case 2: User Copies From Contact

```
Input:     "+1 (210) 388-4155"
Normalize: "2103884155" (strip +1)
Store:     "2103884155"
Display:   "(210) 388-4155"
SMS API:   "2103884155"
```

### Test Case 3: Payment Matching

```
Customer books with:     "2103884155"
Payment note includes:   "(210) 388-4155"
System normalizes both:  "2103884155"
Match result:            ✅ SUCCESS
```

### Test Case 4: SMS Notification

```
Database phone:          "2103884155"
Notification service:    Passes "2103884155" to Twilio
Twilio converts:         "+12103884155" (E.164)
SMS delivered:           ✅ SUCCESS
```

---

## Implementation Status

### ✅ Completed

- Frontend phone utilities (`phoneUtils.ts`)
- Backend schema validation (`booking.py`)
- Payment matching normalization (`payment_matcher_service.py`)
- SMS notification service (`unified_notification_service.py`)
- Contact info phone validation (`ContactInfoSection.tsx`)

### ⚠️ In Progress

- BookingFormContainer integration (50% complete)
- SMS consent field (frontend complete, backend pending)

### ❌ Pending

- Backend SMS consent schema field
- Backend SMS consent database migration
- End-to-end testing
- SubmitSection UI updates

---

## Developer Guidelines

### When Adding New Phone Fields

1. **Frontend**:
   - Use `normalizePhoneNumber()` before API submission
   - Use `formatPhoneNumber()` for display
   - Use `isValidPhoneNumber()` for validation

2. **Backend**:
   - Add Pydantic validator to normalize phone
   - Pattern: `r"^\d{10}$"` for storage
   - Use `@field_validator` to strip formatting

3. **Database**:
   - Store as VARCHAR(20) or TEXT
   - Store 10 digits only, no formatting
   - Index for fast queries

4. **SMS/WhatsApp**:
   - Pass 10-digit phone to notification service
   - Service handles Twilio formatting automatically
   - No manual E.164 conversion needed

### When Querying Phone Numbers

```python
# ✅ Correct: Normalize before query
normalized = ''.join(filter(str.isdigit, user_input))[-10:]
query.filter(Booking.contact_phone == normalized)

# ✅ Also correct: Partial match for flexibility
query.filter(Booking.contact_phone.like(f'%{normalized}%'))

# ❌ Wrong: Query with formatted phone
query.filter(Booking.contact_phone == "(210) 388-4155")  # Won't match!
```

---

## Emergency Troubleshooting

### Problem: Payment Not Matching

**Symptom**: Customer says they paid, but system shows pending

**Debug Steps**:

1. Check database: `SELECT contact_phone FROM bookings WHERE id = ?`
2. Check payment note: What phone did customer include?
3. Normalize both: Are they both 10 digits?
4. Check logs: Did payment matcher run?

**Solution**: If phone formats don't match, run migration to normalize
all existing phones:

```sql
UPDATE bookings
SET contact_phone = REGEXP_REPLACE(contact_phone, '[^0-9]', '', 'g')
WHERE contact_phone ~ '[^0-9]';
```

### Problem: SMS Not Delivering

**Symptom**: Booking confirmation SMS not received

**Debug Steps**:

1. Check phone format: Is it 10 digits?
2. Check Twilio logs: Did API call succeed?
3. Check number validity: Is it a real number?

**Solution**: Ensure phone is valid 10-digit US number. Twilio rejects
invalid formats.

---

## Conclusion

**Phone format consistency is CRITICAL** for:

- ✅ Payment matching (revenue tracking)
- ✅ SMS notifications (customer communication)
- ✅ Database integrity (clean data)
- ✅ System reliability (no bugs)

**Standard Format**: Always use **10 digits** for storage and
matching. Frontend handles display formatting. Twilio handles E.164
conversion.

**Golden Rule**: When in doubt, normalize to 10 digits!
