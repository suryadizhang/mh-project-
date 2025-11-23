# Booking Page Analysis & Missing Features

## Current State Analysis

### ✅ What's Working

**1. Terms & Conditions Modal**

- ✅ **EXISTS** in `BookingModals.tsx`
- ✅ Shows comprehensive agreement before booking submission
- ✅ Customer must click "I Agree - Submit Booking" button
- ✅ Covers:
  - Service Agreement
  - Pricing & Payment ($100 deposit requirement)
  - Cancellation Policy (7 days, reschedule fees)
  - Client Responsibilities
- ✅ Prevents submission until user explicitly agrees

**2. Terms & Conditions Page**

- ✅ Full terms page at `/terms`
  (`apps/customer/src/app/terms/page.tsx`)
- ✅ Includes SMS Terms of Service (TCPA compliance)
- ✅ Covers all legal requirements:
  - SMS opt-in/opt-out (STOP, START, HELP)
  - Message frequency disclosure
  - Data rates disclosure
  - Third-party sharing disclaimer
  - Contact information
- ✅ Last updated: October 8, 2025

**3. Form Validation**

- ✅ Comprehensive field validation
- ✅ Modal shows missing fields before submission
- ✅ Prevents empty submissions

**4. Failed Booking Lead Capture**

- ✅ Captures leads when booking fails
- ✅ Different failure reasons tracked (slot unavailable, date
  unavailable, error)
- ✅ Customer information preserved for follow-up

---

## ❌ Missing Critical Features

### 1. **NO CAPTCHA/Bot Protection** ⚠️ CRITICAL

**Current State:**

- ❌ No math captcha
- ❌ No Google reCAPTCHA
- ❌ No hCaptcha
- ❌ No Cloudflare Turnstile
- ❌ No honeypot fields
- ❌ No rate limiting visible in frontend

**Risk:**

- Bots can spam bookings
- Fake bookings waste time slots
- DDoS attack vulnerability
- Database pollution with fake data

**Recommended Solutions:**

#### Option A: Simple Math Captcha (No external dependencies)

```tsx
// Add to BookingFormContainer.tsx
const [mathAnswer, setMathAnswer] = useState('');
const [mathQuestion, setMathQuestion] = useState({
  num1: 0,
  num2: 0,
  answer: 0,
});

useEffect(() => {
  // Generate random math question on component mount
  const num1 = Math.floor(Math.random() * 10) + 1;
  const num2 = Math.floor(Math.random() * 10) + 1;
  setMathQuestion({ num1, num2, answer: num1 + num2 });
}, []);

// In form validation (onSubmit):
if (parseInt(mathAnswer) !== mathQuestion.answer) {
  alert('Please solve the math problem to verify you are human.');
  return;
}
```

#### Option B: Google reCAPTCHA v3 (Invisible, better UX)

```bash
npm install react-google-recaptcha-v3
```

```tsx
import { useGoogleReCaptcha } from 'react-google-recaptcha-v3';

const { executeRecaptcha } = useGoogleReCaptcha();

// In onSubmit:
const token = await executeRecaptcha('booking_submit');
// Send token to backend for verification
```

#### Option C: hCaptcha (Privacy-focused alternative)

```bash
npm install @hcaptcha/react-hcaptcha
```

```tsx
import HCaptcha from '@hcaptcha/react-hcaptcha';

<HCaptcha
  sitekey="YOUR_SITE_KEY"
  onVerify={token => setCaptchaToken(token)}
/>;
```

---

### 2. **Terms Acknowledgment Checkbox Missing** ⚠️ MEDIUM

**Current State:**

- ✅ Modal shows terms before submission
- ✅ "I Agree" button exists
- ❌ No checkbox to acknowledge terms

**Legal Best Practice:**

- Explicit checkbox provides stronger legal consent
- Shows user actively read and agreed (not just clicked)
- Industry standard for terms acceptance

**Recommended Addition:**

```tsx
// In BookingModals.tsx Agreement Modal
<div className="form-check mb-3">
  <input
    type="checkbox"
    id="termsCheckbox"
    className="form-check-input"
    checked={termsAccepted}
    onChange={(e) => setTermsAccepted(e.target.checked)}
  />
  <label htmlFor="termsCheckbox" className="form-check-label">
    I have read and agree to the{' '}
    <a href="/terms" target="_blank" rel="noopener noreferrer">
      Terms & Conditions
    </a>
    {' '}and{' '}
    <a href="/privacy" target="_blank" rel="noopener noreferrer">
      Privacy Policy
    </a>
  </label>
</div>

<button
  type="button"
  className="btn btn-primary"
  onClick={handleConfirmAgreement}
  disabled={isSubmitting || !termsAccepted} // Disable until checked
>
  <Check className="mr-2 inline-block" size={18} />
  Submit Booking
</button>
```

---

### 3. **Deposit Deadline Warning Missing** ⚠️ HIGH

**Current State:**

- ❌ Booking form doesn't mention 2-hour deposit deadline
- ❌ No warning about payment requirement
- ❌ Customer might not know to pay immediately

**Impact:**

- Higher cancellation rate
- Customers miss deadline unintentionally
- More manual follow-up needed

**Recommended Addition:**

```tsx
// In BookingModals.tsx Agreement Modal
<div className="alert alert-warning mb-3">
  <strong>⏰ Important:</strong> You must pay a $100 deposit within{' '}
  <strong>2 hours</strong> after booking to secure your date. We'll send payment
  instructions via SMS immediately.
</div>

// In terms list:
<h6 className="mt-3">Deposit Requirement:</h6>
<ul>
  <li>
    <strong className="text-danger">
      $100 deposit required within 2 hours to lock your date
    </strong>
  </li>
  <li>Payment accepted via Venmo, Zelle, Stripe, or credit card</li>
  <li>Deposit is refundable if cancelled 7+ days before event</li>
  <li>
    You'll receive SMS with payment instructions immediately after booking
  </li>
</ul>
```

---

### 4. **SMS Opt-In Consent Missing** ⚠️ CRITICAL (TCPA Compliance)

**Current State:**

- ✅ Terms page has SMS disclosure
- ❌ Booking form has NO SMS opt-in checkbox
- ❌ No explicit consent at point of collection

**Legal Risk:**

- TCPA violation (potential $500-$1,500 per message fine)
- SMS opt-in MUST be:
  - Express written consent
  - Clear and conspicuous
  - At point of collection (NOT buried in T&Cs)

**Required Addition:**

```tsx
// In ContactInfoSection or before submit button
<div className="form-check mb-3 border p-3 bg-light">
  <input
    type="checkbox"
    id="smsConsent"
    className="form-check-input"
    required
    {...register('smsConsent', { required: true })}
  />
  <label htmlFor="smsConsent" className="form-check-label">
    <strong>SMS Consent (Required):</strong> I agree to receive text
    messages from My Hibachi Chef including booking confirmations,
    event reminders, and chef updates. Message frequency varies.
    Message and data rates may apply. Reply STOP to opt-out. See{' '}
    <a href="/terms#sms" target="_blank">
      SMS Terms
    </a>
    .
  </label>
</div>
```

---

### 5. **No Phone Number Format Validation** ⚠️ MEDIUM

**Current State:**

- ❌ Phone field accepts any format
- ❌ No automatic formatting
- ❌ No validation for 10-digit requirement

**Impact:**

- Inconsistent phone format in database
- Payment matching might fail (expects 2103884155, user enters (210)
  388-4155)
- SMS delivery failures

**Recommended Solution:**

```tsx
// Install library
npm install react-phone-number-input

// Or use custom formatter
import { formatPhoneNumber, normalizePhoneNumber } from '@/lib/phoneUtils';

<input
  type="tel"
  id="phone"
  required
  pattern="[0-9]{10}"
  placeholder="2103884155"
  value={formData.phone}
  onChange={(e) => {
    const normalized = normalizePhoneNumber(e.target.value);
    setFormData({ ...formData, phone: normalized });
  }}
  onBlur={(e) => {
    // Show formatted version on blur
    e.target.value = formatPhoneNumber(e.target.value);
  }}
/>
<small className="text-muted">
  Enter 10 digits without spaces or dashes (e.g., 2103884155)
</small>
```

---

### 6. **No Email Confirmation Field** ⚠️ LOW

**Current State:**

- ❌ Email entered only once
- ❌ No confirmation field to catch typos

**Impact:**

- Typos in email = no confirmation sent
- Customer never receives booking details
- Lost bookings

**Recommended Addition:**

```tsx
<div>
  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
    Email *
  </label>
  <input
    type="email"
    id="email"
    required
    value={formData.email}
    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
    className="w-full px-3 py-2 border border-gray-300 rounded-md"
  />
</div>

<div>
  <label
    htmlFor="confirmEmail"
    className="block text-sm font-medium text-gray-700 mb-2"
  >
    Confirm Email *
  </label>
  <input
    type="email"
    id="confirmEmail"
    required
    value={formData.confirmEmail}
    onChange={(e) => setFormData({ ...formData, confirmEmail: e.target.value })}
    className="w-full px-3 py-2 border border-gray-300 rounded-md"
  />
  {formData.email !== formData.confirmEmail && formData.confirmEmail && (
    <p className="text-red-600 text-sm mt-1">Emails do not match</p>
  )}
</div>
```

---

## Implementation Priority

### 🔴 CRITICAL (Implement Immediately)

1. **SMS Opt-In Checkbox** - TCPA compliance requirement
2. **Bot Protection (Captcha)** - Prevent abuse and fake bookings
3. **Deposit Deadline Warning** - Reduce cancellations

### 🟡 HIGH (Implement This Sprint)

4. **Terms Acknowledgment Checkbox** - Legal best practice
5. **Phone Number Validation** - Data consistency for payment matching

### 🟢 MEDIUM (Implement Next Sprint)

6. **Email Confirmation Field** - Reduce typos
7. **Success Page Improvements** - Show deposit instructions
   immediately

---

## Recommended Implementation Code

### File: `apps/customer/src/components/booking/CaptchaSection.tsx` (NEW)

```tsx
'use client';

import React, { useEffect, useState } from 'react';

interface MathCaptchaProps {
  onVerify: (isValid: boolean) => void;
}

export const MathCaptcha: React.FC<MathCaptchaProps> = ({
  onVerify,
}) => {
  const [num1, setNum1] = useState(0);
  const [num2, setNum2] = useState(0);
  const [answer, setAnswer] = useState('');
  const [correctAnswer, setCorrectAnswer] = useState(0);

  useEffect(() => {
    // Generate new math question
    const n1 = Math.floor(Math.random() * 10) + 1;
    const n2 = Math.floor(Math.random() * 10) + 1;
    setNum1(n1);
    setNum2(n2);
    setCorrectAnswer(n1 + n2);
  }, []);

  const handleChange = (value: string) => {
    setAnswer(value);
    const isCorrect = parseInt(value) === correctAnswer;
    onVerify(isCorrect);
  };

  return (
    <div className="captcha-container border p-3 bg-light rounded mb-4">
      <label className="form-label">
        <strong>Verify you're human:</strong> What is {num1} + {num2}?
      </label>
      <input
        type="number"
        className="form-control"
        value={answer}
        onChange={e => handleChange(e.target.value)}
        placeholder="Enter answer"
        required
      />
      {answer && parseInt(answer) !== correctAnswer && (
        <small className="text-danger">
          Incorrect answer, please try again
        </small>
      )}
    </div>
  );
};
```

### File: Update `apps/customer/src/components/booking/BookingFormContainer.tsx`

```tsx
// Add state
const [captchaVerified, setCaptchaVerified] = useState(false);
const [smsConsent, setSmsConsent] = useState(false);
const [termsAccepted, setTermsAccepted] = useState(false);

// In onSubmit validation:
if (!captchaVerified) {
  alert('Please solve the math problem to verify you are human.');
  return;
}

if (!smsConsent) {
  alert('SMS consent is required to receive booking confirmations.');
  return;
}

// Pass to form sections:
<CaptchaSection onVerify={setCaptchaVerified} />
<SMSConsentCheckbox checked={smsConsent} onChange={setSmsConsent} />
```

### File: Update `apps/customer/src/components/booking/BookingModals.tsx`

```tsx
// Add deposit warning and terms checkbox
<div className="modal-body">
  {/* Deposit Warning */}
  <div className="alert alert-warning mb-3">
    <strong>⏰ IMPORTANT DEADLINE:</strong>
    <p className="mb-0">
      You must pay a <strong>$100 deposit within 2 HOURS</strong> after booking
      to secure your date. Payment instructions will be sent via SMS immediately.
    </p>
  </div>

  {/* Existing agreement content */}
  <div className="agreement-content">
    {/* ... existing terms ... */}
  </div>

  {/* Terms Acceptance Checkbox */}
  <div className="form-check mt-4 p-3 bg-light border rounded">
    <input
      type="checkbox"
      id="termsCheckbox"
      className="form-check-input"
      checked={termsAccepted}
      onChange={(e) => setTermsAccepted(e.target.checked)}
    />
    <label htmlFor="termsCheckbox" className="form-check-label">
      <strong>
        I have read and agree to the above Terms & Conditions, including the
        2-hour deposit deadline.
      </strong>
    </label>
  </div>
</div>

<div className="modal-footer">
  <button
    type="button"
    className="btn btn-outline-secondary me-2"
    onClick={handleCancelAgreement}
  >
    Cancel
  </button>
  <button
    type="button"
    className="btn btn-primary"
    onClick={handleConfirmAgreement}
    disabled={isSubmitting || !termsAccepted}
  >
    <Check className="mr-2 inline-block" size={18} />
    Submit Booking
  </button>
</div>
```

---

## Testing Checklist

### Terms & Conditions

- [ ] Modal appears before submission
- [ ] Customer cannot submit without checking terms box
- [ ] Terms link opens in new tab
- [ ] "I Agree" button disabled until checkbox checked

### Captcha

- [ ] Math question generates on page load
- [ ] Wrong answer shows error
- [ ] Correct answer allows submission
- [ ] New question generates on page refresh

### SMS Consent

- [ ] Checkbox appears in booking form
- [ ] Required field validation works
- [ ] Link to SMS terms opens correctly
- [ ] Consent recorded in backend

### Deposit Deadline

- [ ] Warning shows in modal
- [ ] 2-hour deadline mentioned
- [ ] Payment methods listed
- [ ] SMS notification mentioned

### Phone Validation

- [ ] Only accepts 10 digits
- [ ] Strips formatting automatically
- [ ] Shows error for invalid format
- [ ] Saves as normalized format (2103884155)

---

## Backend Requirements

### SMS Consent Recording

```python
# apps/backend/src/schemas/booking.py
class BookingCreate(BaseModel):
    # ... existing fields ...
    sms_consent: bool = Field(
        ...,
        description="Customer consent to receive SMS notifications"
    )
    sms_consent_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When SMS consent was granted"
    )
```

```python
# apps/backend/src/models/booking.py
class Booking(BaseModel):
    # ... existing fields ...
    sms_consent = Column(Boolean, nullable=False, default=False)
    sms_consent_timestamp = Column(DateTime, nullable=True)
```

### Captcha Verification (Backend)

```python
# apps/backend/src/routers/bookings.py

from core.security import verify_recaptcha

@router.post("/api/v1/public/bookings")
async def create_booking(
    booking_data: BookingCreate,
    request: Request
):
    # Verify captcha token
    captcha_token = request.headers.get("X-Captcha-Token")
    if not captcha_token:
        raise HTTPException(400, "Captcha verification required")

    is_valid = await verify_recaptcha(captcha_token)
    if not is_valid:
        raise HTTPException(400, "Captcha verification failed")

    # ... rest of booking creation ...
```

---

## Summary

### ✅ Working Features

- Terms & Conditions modal
- Full terms page with SMS disclosure
- Form validation
- Failed booking lead capture

### ❌ Missing Features (CRITICAL)

1. **No captcha/bot protection** - Implement math captcha or reCAPTCHA
2. **No SMS opt-in checkbox** - TCPA compliance violation
3. **No deposit deadline warning** - Customers unaware of 2-hour
   requirement
4. **No terms acceptance checkbox** - Legal best practice missing
5. **No phone validation** - Format inconsistency breaks payment
   matching

### 📋 Action Items

1. Add MathCaptcha component (1-2 hours)
2. Add SMS consent checkbox (30 minutes)
3. Update BookingModals with deposit warning (30 minutes)
4. Add terms acceptance checkbox (15 minutes)
5. Add phone number validation (1 hour)
6. Update backend to record SMS consent (1 hour)
7. Test all changes (2 hours)

**Total Estimated Time:** 6-7 hours

---

**Next Steps:** Shall I implement these missing features now?
