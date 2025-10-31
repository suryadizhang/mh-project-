# Friend/Family Payment Matching Guide

## Problem: How to Match Payments When Someone Else Pays?

When booking a hibachi party, the customer may have a **friend or family member** pay on their behalf. This creates a matching challenge:

```
Customer: John Smith (books party, provides info)
    ↓
Friend: Sarah Johnson (pays $550 via Venmo)
    ↓
Email: "You received $550 from Sarah Johnson"
    ↓
❓ How do we match Sarah's payment to John's booking?
```

---

## Solution: Multi-Level Matching Strategy

### Level 1: Exact Match (Default)
**Requirements:**
- Amount matches within ±$1.00
- Same payment method
- Within 24-hour time window
- **Best for:** Customer pays themselves

**Example:**
```
Booking: John Smith, $550, Venmo, Created: Oct 29 10:00 AM
Email: "Sarah Johnson sent you $550 via Venmo" (Oct 29 10:15 AM)
✅ Match: Amount ±$1, Method matches, < 24 hours
```

### Level 2: Fuzzy Match (Friend/Family)
**Requirements:**
- **Name OR Phone match** (flexible matching)
- Amount matches within ±$60.00 (covers tip variations)
- Same payment method
- Within 72-hour time window
- **Best for:** Friend/family pays with different tip amount

**Name Matching Options:**
- ✅ **Exact full name:** "Sarah Johnson" = "Sarah Johnson" (Score: +100)
- ✅ **First name only:** "Sarah" in "Sarah Johnson" (Score: +75)
- ✅ **Last name only:** "Johnson" in "Sarah Johnson" (Score: +75)
- ✅ **Partial name:** Any word matches (Score: +50)

**Phone Matching:**
- ✅ **Full 10-digit match:** "2103884155" (Score: +100)
- ✅ **Last 4 digits:** "*4155" (Score: +40)

**Example 1 - Name Match:**
```
Booking: John Smith, $550, Venmo, Created: Oct 29 10:00 AM
Email: "Sarah Johnson sent you $560 via Venmo" (Oct 29 10:15 AM)
❌ No name match (Sarah ≠ John)
✅ Match: Amount within ±$60, Method matches, < 72 hours
⚠️ Low confidence → Admin review
```

**Example 2 - Phone Match:**
```
Booking: John Smith (phone: 2103884155), $550, Venmo
Email: "Sarah Johnson sent you $560" (payment note contains: 2103884155)
✅ Match: Phone number matches (Score: +100)
✅ Auto-confirmed: High confidence with phone
```

### Level 3: Sender Information Match (Smart)
**Scoring system** to find best match when multiple bookings exist:

| Match Type | Score | Description |
|------------|-------|-------------|
| **Exact full name match** | +100 | Sender name = customer name (e.g., "John Smith") |
| **First name match** | +75 | First name matches (e.g., "John" in "John Smith") |
| **Last name match** | +75 | Last name matches (e.g., "Smith" in "John Smith") |
| **Partial name match** | +50 | Any word in name matches |
| **Email match** | +100 | Sender email = customer email |
| **Phone match (10 digits)** | +100 | Full phone number matches (e.g., "2103884155") |
| **Phone match (last 4)** | +40 | Last 4 digits match (e.g., "*4155") |
| **Alternative payer (exact)** | +150 | Sender matches explicitly listed alternative payer (full name) |
| **Alternative payer (first)** | +125 | Alternative payer first name matches |
| **Alternative payer (last)** | +125 | Alternative payer last name matches |
| **Alternative payer email** | +150 | Alternative payer email matches |
| **Alternative payer phone** | +150 | Alternative payer phone matches |
| **Venmo username** | +100 | Sender @username matches booking metadata |
| **Exact amount** | +25 | Amount exactly matches (no rounding) |

**Matching Strategy:**
- ✅ **Name OR Phone** - Either one can match (not both required)
- ✅ **Flexible Name Matching** - First, last, or full name works
- ✅ **Best match threshold:** Score > 50 required for confident match
- ✅ **Multiple matches:** Pick highest score

---

## How to Handle Friend/Family Payments

### Option 1: Customer Provides Friend's Info (Recommended ✅)

**During booking, customer can add "Alternative Payer" information:**

```javascript
// Frontend: Add option during checkout
{
  "customer_name": "John Smith",
  "customer_email": "john@email.com",
  "customer_phone": "+19165551234",
  "payment_method": "venmo",
  "alternative_payer": {
    "name": "Sarah Johnson",
    "email": "sarah@email.com",
    "phone": "+19165555678",
    "venmo_username": "@sarahjohnson",
    "relationship": "friend"  // Optional
  }
}
```

**Matching logic:**
1. Email arrives: "Sarah Johnson sent you $550"
2. Parser extracts: `sender_name = "Sarah Johnson"`
3. Matcher finds booking with `alternative_payer.name = "Sarah Johnson"`
4. **Score: 150** (alternative payer match)
5. ✅ **Auto-confirmed!**

### Option 2: Customer Doesn't Provide Info (Fuzzy Match)

**Without alternative payer info, system uses fuzzy matching:**

1. **Expanded amount tolerance:** ±$60 (catches tip variations)
2. **Extended time window:** 72 hours (more flexibility)
3. **Multiple matches:** Admin gets notification to manually review

**Example:**
```
Booking 1: John Smith, $550, Venmo, Oct 29 10:00 AM
Booking 2: Alice Brown, $560, Venmo, Oct 29 11:00 AM
Email: "Sarah Johnson sent you $555 via Venmo" (Oct 29 2:00 PM)

Matcher finds: Both bookings within ±$60, same method, < 72 hours
⚠️ Multiple matches → Sends admin notification for manual review
```

### Option 3: Manual Matching (Admin Dashboard)

**Admin can manually link payments:**

**API Endpoint:**
```bash
POST /api/v1/payments/email-notifications/manual-match
{
  "email_id": "msg_abc123",
  "payment_id": "pay_456",
  "confirm_payment": true
}
```

**Use cases:**
- Multiple possible matches (system unsure)
- Payment outside 72-hour window
- Amount significantly different (> $60)
- Customer paid via different method than expected

---

## Implementation: Adding Alternative Payer Field

### 1. Database Schema (Already Supported via `metadata` JSON field)

```python
# models/booking.py
class Booking:
    # ... existing fields ...
    metadata: Dict = Column(JSON, nullable=True, default={})
    
    # Example metadata:
    # {
    #   "alternative_payer": {
    #     "name": "Sarah Johnson",
    #     "email": "sarah@email.com",
    #     "phone": "+19165555678",
    #     "venmo_username": "@sarahjohnson",
    #     "relationship": "friend"
    #   }
    # }
```

### 2. Frontend: Add Optional Field

**File:** `apps/customer/src/app/payment/page.tsx`

```typescript
// Add state for alternative payer
const [showAlternativePayer, setShowAlternativePayer] = useState(false);
const [alternativePayer, setAlternativePayer] = useState({
  name: '',
  email: '',
  phone: '',
  venmo_username: '',
  relationship: 'friend'
});

// Add UI toggle
<div className="mb-6">
  <label className="flex items-center gap-2">
    <input
      type="checkbox"
      checked={showAlternativePayer}
      onChange={(e) => setShowAlternativePayer(e.target.checked)}
    />
    <span>Someone else will pay for this booking</span>
  </label>
</div>

{showAlternativePayer && (
  <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
    <h3 className="font-semibold">Alternative Payer Information</h3>
    <p className="text-sm text-gray-600">
      This helps us automatically confirm the payment when your friend/family member pays
    </p>
    
    <input
      type="text"
      placeholder="Their Name"
      value={alternativePayer.name}
      onChange={(e) => setAlternativePayer({...alternativePayer, name: e.target.value})}
      className="w-full p-2 border rounded"
    />
    
    <input
      type="email"
      placeholder="Their Email (optional)"
      value={alternativePayer.email}
      onChange={(e) => setAlternativePayer({...alternativePayer, email: e.target.value})}
      className="w-full p-2 border rounded"
    />
    
    <input
      type="tel"
      placeholder="Their Phone (optional)"
      value={alternativePayer.phone}
      onChange={(e) => setAlternativePayer({...alternativePayer, phone: e.target.value})}
      className="w-full p-2 border rounded"
    />
    
    {selectedMethod === 'venmo' && (
      <input
        type="text"
        placeholder="Their Venmo @username (optional)"
        value={alternativePayer.venmo_username}
        onChange={(e) => setAlternativePayer({...alternativePayer, venmo_username: e.target.value})}
        className="w-full p-2 border rounded"
      />
    )}
  </div>
)}

// Include in booking submission
const bookingData = {
  // ... other fields ...
  metadata: {
    alternative_payer: showAlternativePayer ? alternativePayer : null
  }
};
```

### 3. Backend: Update Booking Creation

**File:** `apps/backend/src/routes/bookings.py`

```python
@router.post("/")
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
):
    # Validate alternative payer if provided
    if booking_data.metadata and booking_data.metadata.get("alternative_payer"):
        alt_payer = booking_data.metadata["alternative_payer"]
        
        # At least name is required
        if not alt_payer.get("name"):
            raise HTTPException(
                status_code=400,
                detail="Alternative payer name is required"
            )
        
        logger.info(
            f"Booking created with alternative payer: {alt_payer.get('name')} "
            f"(paying for {booking_data.customer_name})"
        )
    
    # ... rest of booking creation ...
```

---

## Testing Scenarios

### Scenario 1: Friend Pays (With Info Provided)

**Setup:**
```python
# Create booking with alternative payer
booking = {
    "customer_name": "John Smith",
    "customer_email": "john@email.com",
    "amount": 550.00,
    "payment_method": "venmo",
    "metadata": {
        "alternative_payer": {
            "name": "Sarah Johnson",
            "venmo_username": "@sarahjohnson"
        }
    }
}
```

**Test:**
1. Create booking (status: pending)
2. Simulate Venmo email: "Sarah Johnson (@sarahjohnson) sent you $550"
3. Scheduler runs
4. ✅ **Expected:** Auto-matched (score: 150+), status: paid

### Scenario 2: Friend Pays (No Info Provided)

**Setup:**
```python
# Create booking without alternative payer
booking = {
    "customer_name": "John Smith",
    "customer_email": "john@email.com",
    "amount": 550.00,
    "payment_method": "venmo"
}
```

**Test:**
1. Create booking (status: pending)
2. Simulate Venmo email: "Sarah Johnson sent you $550"
3. Scheduler runs with fuzzy matching
4. ⚠️ **Expected:** Matched (±$60 tolerance), admin notification sent

### Scenario 3: Multiple Possible Matches

**Setup:**
```python
# Create two similar bookings
booking1 = {"customer_name": "John Smith", "amount": 550.00, "method": "venmo"}
booking2 = {"customer_name": "Alice Brown", "amount": 555.00, "method": "venmo"}
```

**Test:**
1. Both bookings pending
2. Simulate email: "Sarah Johnson sent you $552"
3. Scheduler finds 2 matches (both within ±$60)
4. ⚠️ **Expected:** Admin notification with manual match UI

---

## Admin Dashboard for Unmatched Payments

### View Unmatched Emails

```bash
GET /api/v1/payments/email-notifications/unmatched?since_hours=48

Response:
[
  {
    "email_id": "msg_123",
    "provider": "venmo",
    "amount": 552.00,
    "sender_name": "Sarah Johnson",
    "subject": "You received $552.00",
    "received_at": "2025-10-29T14:30:00Z",
    "possible_matches": [
      {
        "payment_id": "pay_456",
        "booking_id": "book_789",
        "customer_name": "John Smith",
        "amount": 550.00,
        "created_at": "2025-10-29T10:00:00Z"
      },
      {
        "payment_id": "pay_457",
        "booking_id": "book_790",
        "customer_name": "Alice Brown",
        "amount": 555.00,
        "created_at": "2025-10-29T11:00:00Z"
      }
    ]
  }
]
```

### Manual Match UI

```typescript
// Admin dashboard component
function UnmatchedPayments() {
  const [unmatched, setUnmatched] = useState([]);
  
  const handleManualMatch = async (emailId, paymentId) => {
    await fetch('/api/v1/payments/email-notifications/manual-match', {
      method: 'POST',
      body: JSON.stringify({
        email_id: emailId,
        payment_id: paymentId,
        confirm_payment: true
      })
    });
    
    // Reload list
    loadUnmatched();
  };
  
  return (
    <div>
      <h2>Unmatched Payment Notifications</h2>
      {unmatched.map(email => (
        <div key={email.email_id} className="card">
          <h3>{email.sender_name} sent ${email.amount}</h3>
          <p>Received: {email.received_at}</p>
          
          <h4>Possible Matches:</h4>
          {email.possible_matches.map(match => (
            <div key={match.payment_id}>
              <p>{match.customer_name} - ${match.amount}</p>
              <button onClick={() => handleManualMatch(email.email_id, match.payment_id)}>
                Confirm This Match
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

---

## Best Practices

### For Customers:
✅ **DO:** Provide alternative payer info if someone else will pay  
✅ **DO:** Use the same amount (including tip)  
✅ **DO:** Pay within 24 hours of booking  
❌ **DON'T:** Have multiple people split the payment (single payment only)

### For Admins:
✅ **DO:** Check unmatched payments daily  
✅ **DO:** Manually match if system is unsure  
✅ **DO:** Call customer if payment can't be matched after 48 hours  
❌ **DON'T:** Auto-confirm payments > 72 hours old without verification

### For Developers:
✅ **DO:** Log all matching attempts for debugging  
✅ **DO:** Send admin notifications for edge cases  
✅ **DO:** Test with real email samples from each provider  
❌ **DON'T:** Auto-confirm if confidence score < 50

---

## Summary: Matching Logic Flow

```
┌─────────────────────────────────────────────────────────┐
│  Payment Email Arrives                                   │
│  "Sarah Johnson sent you $550 via Venmo"                │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: Parse Email                                     │
│  ✓ Amount: $550                                          │
│  ✓ Method: Venmo                                         │
│  ✓ Sender: Sarah Johnson                                │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: Find Potential Matches                          │
│  Query: amount ±$60, method=venmo, time < 72 hours      │
│  Found: 2 pending payments                               │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: Score Each Match                                │
│  Booking #1 (John Smith):                                │
│    - Alternative payer name match: +150                  │
│    - Exact amount: +25                                   │
│    → Total Score: 175 🎯                                 │
│                                                          │
│  Booking #2 (Alice Brown):                               │
│    - No name match: 0                                    │
│    - Amount off by $5: 0                                 │
│    → Total Score: 0                                      │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: Select Best Match                               │
│  Best: Booking #1 (score 175 > threshold 50)            │
│  ✅ Auto-confirm payment                                 │
│  ✅ Update booking status: PAID                          │
│  ✅ Send confirmation email to John Smith                │
│  ✅ Send admin notification                              │
└─────────────────────────────────────────────────────────┘
```

---

**Questions? Need Help?**
- Update matching tolerance: Modify `EXPANDED_AMOUNT_TOLERANCE` in `payment_matcher_service.py`
- Adjust time window: Modify `EXTENDED_TIME_WINDOW_HOURS`
- Add more matching fields: Update `_find_best_match_by_sender()` method
- Custom email patterns: Update `PATTERNS` dict in `payment_email_monitor.py`
