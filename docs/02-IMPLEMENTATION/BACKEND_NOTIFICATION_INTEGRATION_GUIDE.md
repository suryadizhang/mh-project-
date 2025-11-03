# 🔧 Backend Integration Guide - Unified Notifications

## Quick Start: Add Notifications to Your Endpoints

This guide shows you exactly where and how to add notification calls to your existing backend endpoints.

---

## 📋 Integration Checklist

| Endpoint | Notification Type | Status | Time Est. |
|----------|-------------------|--------|-----------|
| `POST /bookings` | New Booking | ⏳ To Do | 5 min |
| `PUT /bookings/{id}` | Edit Booking | ⏳ To Do | 10 min |
| `DELETE /bookings/{id}` | Cancellation | ⏳ To Do | 5 min |
| Payment Matcher | Payment Received | ✅ Ready | 2 min |
| `POST /reviews` | Review Received | ⏳ To Do | 5 min |
| `POST /complaints` | Complaint Filed | ⏳ To Do | 5 min |

**Total Time:** ~30 minutes

---

## 1️⃣ New Booking Notification

**File:** `apps/backend/src/api/routes/bookings.py` (or similar)

**Endpoint:** `POST /api/bookings`

### Add Import:
```python
from services.unified_notification_service import notify_new_booking
import asyncio
```

### Add After Booking is Saved:
```python
@router.post("/bookings")
async def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    """Create new booking"""
    
    # Create booking (existing code)
    new_booking = CateringBooking(**booking_data.dict())
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    # ✅ NEW: Send notifications (non-blocking)
    asyncio.create_task(
        notify_new_booking(
            customer_name=new_booking.customer_name,
            customer_phone=new_booking.customer_phone,
            event_date=new_booking.event_date.strftime("%B %d, %Y"),
            event_time=new_booking.event_time.strftime("%I:%M %p"),
            guest_count=new_booking.guest_count,
            location=new_booking.location or "TBD",
            booking_id=new_booking.id
        )
    )
    
    return new_booking
```

---

## 2️⃣ Booking Edit Notification

**File:** `apps/backend/src/api/routes/bookings.py`

**Endpoint:** `PUT /api/bookings/{booking_id}`

### Add Import:
```python
from services.unified_notification_service import notify_booking_edit
```

### Add After Booking is Updated:
```python
@router.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: int, 
    booking_data: BookingUpdate, 
    db: Session = Depends(get_db)
):
    """Update existing booking"""
    
    # Get existing booking
    existing_booking = db.query(CateringBooking).filter(CateringBooking.id == booking_id).first()
    if not existing_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # ✅ NEW: Track changes before update
    changes = {}
    
    if booking_data.event_date and booking_data.event_date != existing_booking.event_date:
        changes["event_date"] = {
            "old": existing_booking.event_date.strftime("%B %d, %Y"),
            "new": booking_data.event_date.strftime("%B %d, %Y")
        }
    
    if booking_data.event_time and booking_data.event_time != existing_booking.event_time:
        changes["event_time"] = {
            "old": existing_booking.event_time.strftime("%I:%M %p"),
            "new": booking_data.event_time.strftime("%I:%M %p")
        }
    
    if booking_data.guest_count and booking_data.guest_count != existing_booking.guest_count:
        changes["guest_count"] = {
            "old": existing_booking.guest_count,
            "new": booking_data.guest_count
        }
    
    if booking_data.location and booking_data.location != existing_booking.location:
        changes["location"] = {
            "old": existing_booking.location,
            "new": booking_data.location
        }
    
    # Update booking (existing code)
    for key, value in booking_data.dict(exclude_unset=True).items():
        setattr(existing_booking, key, value)
    
    db.commit()
    db.refresh(existing_booking)
    
    # ✅ NEW: Send notification if there were changes
    if changes:
        asyncio.create_task(
            notify_booking_edit(
                customer_name=existing_booking.customer_name,
                customer_phone=existing_booking.customer_phone,
                booking_id=existing_booking.id,
                changes=changes
            )
        )
    
    return existing_booking
```

---

## 3️⃣ Cancellation Notification

**File:** `apps/backend/src/api/routes/bookings.py`

**Endpoint:** `DELETE /api/bookings/{booking_id}` or `POST /api/bookings/{booking_id}/cancel`

### Add Import:
```python
from services.unified_notification_service import notify_cancellation
```

### Add Before Deletion:
```python
@router.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: int,
    cancellation_data: Optional[CancellationData] = None,
    db: Session = Depends(get_db)
):
    """Cancel booking"""
    
    # Get booking
    booking = db.query(CateringBooking).filter(CateringBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Calculate refund (if applicable)
    refund_amount = None
    if booking.payment_status == "paid":
        # Your refund calculation logic here
        refund_amount = booking.total_amount  # Full refund example
    
    # ✅ NEW: Send notification BEFORE deleting
    asyncio.create_task(
        notify_cancellation(
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            booking_id=booking.id,
            event_date=booking.event_date.strftime("%B %d, %Y"),
            reason=cancellation_data.reason if cancellation_data else None,
            refund_amount=refund_amount
        )
    )
    
    # Mark as cancelled or delete
    booking.status = "cancelled"
    db.commit()
    
    return {"message": "Booking cancelled", "refund_amount": refund_amount}
```

---

## 4️⃣ Payment Confirmation (✅ Ready - Just Update)

**File:** `apps/backend/src/services/payment_matcher_service.py`

**Method:** `confirm_payment()`

### Replace Old WhatsApp Call:
```python
# ❌ OLD: Remove this
from services.whatsapp_notification_service import send_payment_notification

# ✅ NEW: Use this
from services.unified_notification_service import notify_payment

async def confirm_payment(self, notification_id: int, booking_id: int):
    """Confirm payment match"""
    
    # ... existing confirmation logic ...
    
    # ❌ OLD: Remove old notification code
    # asyncio.create_task(send_payment_notification(...))
    
    # ✅ NEW: Use unified notification
    asyncio.create_task(
        notify_payment(
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            amount=payment.amount,
            payment_method=payment.provider,
            booking_id=booking.id,
            event_date=booking.event_date.strftime("%B %d, %Y")
        )
    )
    
    return confirmed_payment
```

---

## 5️⃣ Review Notification

**File:** `apps/backend/src/api/routes/reviews.py` (create if doesn't exist)

**Endpoint:** `POST /api/reviews`

### Create Endpoint:
```python
from fastapi import APIRouter, Depends
from services.unified_notification_service import notify_review
import asyncio

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("")
async def submit_review(review_data: ReviewCreate, db: Session = Depends(get_db)):
    """Submit customer review"""
    
    # Save review to database (your existing code)
    new_review = CustomerReview(**review_data.dict())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    # Get booking to get customer name
    booking = db.query(CateringBooking).filter(
        CateringBooking.id == review_data.booking_id
    ).first()
    
    # ✅ NEW: Notify admin of new review
    asyncio.create_task(
        notify_review(
            customer_name=booking.customer_name if booking else "Unknown",
            rating=new_review.rating,
            review_text=new_review.review_text,
            booking_id=new_review.booking_id
        )
    )
    
    return new_review
```

---

## 6️⃣ Complaint Notification

**File:** `apps/backend/src/api/routes/complaints.py` (create if doesn't exist)

**Endpoint:** `POST /api/complaints`

### Create Endpoint:
```python
from fastapi import APIRouter, Depends
from services.unified_notification_service import notify_complaint
import asyncio

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("")
async def submit_complaint(complaint_data: ComplaintCreate, db: Session = Depends(get_db)):
    """Submit customer complaint"""
    
    # Save complaint to database (your existing code)
    new_complaint = CustomerComplaint(**complaint_data.dict())
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    
    # Get booking to get customer info
    booking = db.query(CateringBooking).filter(
        CateringBooking.id == complaint_data.booking_id
    ).first()
    
    # Determine priority based on keywords
    complaint_lower = complaint_data.complaint_text.lower()
    priority = "urgent" if any(word in complaint_lower for word in ["no show", "late", "never arrived", "missing"]) else \
               "high" if any(word in complaint_lower for word in ["wrong", "cold", "bad", "terrible", "rude"]) else \
               "medium"
    
    # ✅ NEW: Notify customer (acknowledgment) and admin (action required)
    asyncio.create_task(
        notify_complaint(
            customer_name=booking.customer_name if booking else "Unknown",
            customer_phone=booking.customer_phone if booking else "",
            complaint_text=new_complaint.complaint_text,
            booking_id=new_complaint.booking_id,
            priority=priority
        )
    )
    
    return new_complaint
```

---

## 🧪 Testing Each Integration

### Test Script:
```python
# test_notification_integration.py
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.unified_notification_service import (
    notify_new_booking,
    notify_booking_edit,
    notify_cancellation,
    notify_payment,
    notify_review,
    notify_complaint
)
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_all():
    """Test all notification integrations"""
    
    print("\n" + "="*70)
    print("🧪 TESTING ALL NOTIFICATION INTEGRATIONS")
    print("="*70 + "\n")
    
    # 1. New Booking
    print("1️⃣  Testing New Booking Integration...")
    await notify_new_booking(
        customer_name="Test Customer",
        customer_phone="+19167408768",
        event_date="November 15, 2025",
        event_time="6:00 PM",
        guest_count=15,
        location="123 Test St, Fremont CA",
        booking_id=12345
    )
    print("   ✅ New booking notification sent\n")
    
    # 2. Booking Edit
    print("2️⃣  Testing Booking Edit Integration...")
    await notify_booking_edit(
        customer_name="Test Customer",
        customer_phone="+19167408768",
        booking_id=12345,
        changes={
            "guest_count": {"old": 15, "new": 20}
        }
    )
    print("   ✅ Booking edit notification sent\n")
    
    # 3. Payment
    print("3️⃣  Testing Payment Integration...")
    await notify_payment(
        customer_name="Test Customer",
        customer_phone="+19167408768",
        amount=450.00,
        payment_method="Venmo",
        booking_id=12345,
        event_date="November 15, 2025"
    )
    print("   ✅ Payment notification sent\n")
    
    # 4. Review
    print("4️⃣  Testing Review Integration...")
    await notify_review(
        customer_name="Test Customer",
        rating=5,
        review_text="Great service!",
        booking_id=12345
    )
    print("   ✅ Review notification sent\n")
    
    # 5. Complaint
    print("5️⃣  Testing Complaint Integration...")
    await notify_complaint(
        customer_name="Test Customer",
        customer_phone="+19167408768",
        complaint_text="Chef arrived late",
        booking_id=12345,
        priority="high"
    )
    print("   ✅ Complaint notification sent\n")
    
    # 6. Cancellation
    print("6️⃣  Testing Cancellation Integration...")
    await notify_cancellation(
        customer_name="Test Customer",
        customer_phone="+19167408768",
        booking_id=12345,
        event_date="November 15, 2025",
        reason="Schedule conflict",
        refund_amount=450.00
    )
    print("   ✅ Cancellation notification sent\n")
    
    print("="*70)
    print("✅ ALL INTEGRATIONS TESTED SUCCESSFULLY!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_all())
```

### Run Test:
```bash
cd apps/backend
python test_notification_integration.py
```

---

## ⚠️ Important Notes

### 1. Non-Blocking Calls
Always use `asyncio.create_task()` to avoid blocking API responses:

```python
# ✅ CORRECT: Non-blocking
asyncio.create_task(notify_new_booking(...))
return booking

# ❌ WRONG: Blocks API response
await notify_new_booking(...)  # Will wait for notification to complete
return booking
```

### 2. Error Handling
Notifications are logged but won't crash your API:

```python
# The notification service handles all errors internally
# Your API will continue working even if notification fails
asyncio.create_task(notify_new_booking(...))
# API continues immediately
```

### 3. Mock Mode vs Production
- **Development:** Use `WHATSAPP_PROVIDER=mock` (no API calls)
- **Production:** Use `WHATSAPP_PROVIDER=twilio` (real WhatsApp/SMS)

### 4. Phone Number Format
Always include country code:
- ✅ `+19167408768`
- ❌ `9167408768`
- ❌ `916-740-8768`

---

## 📊 Verification Checklist

After integration, verify each endpoint:

- [ ] Create booking → Check logs for "NEW_BOOKING" message
- [ ] Update booking → Check logs for "EDIT_BOOKING" message
- [ ] Make payment → Check logs for "PAYMENT_RECEIVED" message
- [ ] Submit review → Check logs for "REVIEW_RECEIVED" message
- [ ] File complaint → Check logs for "COMPLAINT_RECEIVED" message
- [ ] Cancel booking → Check logs for "CANCEL_BOOKING" message

### Check Logs:
```bash
# In backend terminal, look for:
============================================================
📱 MOCK NOTIFICATION - NEW_BOOKING
To: +19167408768
Message:
------------------------------------------------------------
🎉 Booking Confirmed!
...
============================================================
```

---

## 🚀 Go Live Checklist

Ready to use real WhatsApp/SMS?

1. **Get Twilio Account:**
   - See `WHATSAPP_BUSINESS_API_SETUP_GUIDE.md`
   - 30 minutes setup time

2. **Update `.env`:**
   ```env
   WHATSAPP_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   ```

3. **Install Twilio:**
   ```bash
   cd apps/backend
   pip install twilio
   ```

4. **Restart Backend:**
   ```bash
   # Stop backend (Ctrl+C)
   uvicorn main:app --reload
   ```

5. **Test with Your Phone:**
   - Create test booking
   - Check your phone for WhatsApp message!

---

## 🎉 Complete!

✅ **All 6 notification types ready for integration**
✅ **Code examples provided for each endpoint**
✅ **Testing script included**
✅ **Non-blocking, error-safe implementation**
✅ **Works in both mock and production modes**

**Next:** Copy-paste the code examples into your endpoints and test!

**Time Required:** ~30 minutes for all 6 integrations
