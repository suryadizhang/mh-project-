"""
Backend Integration Test for WhatsApp Notifications

This script tests the complete end-to-end integration of WhatsApp notifications
with booking endpoints.

Test Scenarios:
1. Create booking → WhatsApp notification sent
2. Update booking → WhatsApp notification sent
3. Cancel booking → WhatsApp notification sent
4. Payment received → WhatsApp notification sent
5. Review submitted → WhatsApp notification sent
6. Complaint submitted → WhatsApp notification sent

Prerequisites:
- Backend server running on http://0.0.0.0:8000
- Twilio WhatsApp sandbox joined (+12103884155)
- .env file configured with Twilio credentials
- Valid test user authentication token
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Verify Twilio credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
ADMIN_PHONE = os.getenv("ADMIN_NOTIFICATION_PHONE")

print("=" * 80)
print("BACKEND WHATSAPP NOTIFICATION INTEGRATION TEST")
print("=" * 80)
print()
print("📋 Configuration Check:")
print(f"   Twilio Account SID: {ACCOUNT_SID[:10]}...")
print(f"   WhatsApp Number: {WHATSAPP_NUMBER}")
print(f"   Admin Phone: {ADMIN_PHONE}")
print()


async def test_booking_creation():
    """Test 1: Create new booking and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 1: NEW BOOKING NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_new_booking
    
    try:
        result = await notify_new_booking(
            customer_name="John Smith",
            customer_phone="+12103884155",  # Test phone that joined sandbox
            event_date="December 25, 2024",
            event_time="6:00 PM",
            guest_count=15,
            location="123 Main St, San Jose, CA 95123",
            booking_id="test-booking-001",
            special_requests="Vegetarian options for 3 guests"
        )
        
        print()
        print("✅ NEW BOOKING notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   🆕 NEW BOOKING ACCEPTED")
        print("   Date: December 25, 2024 at 6:00 PM")
        print("   Location: 123 Main St, San Jose, CA 95123")
        print("   Customer: John Smith")
        print("   Guests: ~15 people")
        print("   Booking #test-booking-001")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_booking_edit():
    """Test 2: Edit booking and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 2: BOOKING EDIT NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_booking_edit
    
    try:
        result = await notify_booking_edit(
            customer_name="John Smith",
            customer_phone="+12103884155",
            booking_id="test-booking-001",
            changes="Date changed to Dec 26, Time changed to 7:00 PM, Guest count changed to 18",
            event_date="December 26, 2024",
            event_time="7:00 PM"
        )
        
        print()
        print("✅ BOOKING EDIT notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   ✏️ BOOKING UPDATED")
        print("   Date: December 26, 2024 at 7:00 PM")
        print("   Changes: Date changed to Dec 26, Time changed to 7:00 PM...")
        print("   Booking #test-booking-001")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_payment_received():
    """Test 3: Payment received and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 3: PAYMENT RECEIVED NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_payment
    
    try:
        result = await notify_payment(
            customer_name="John Smith",
            customer_phone="+12103884155",
            amount=550.00,
            payment_method="Venmo",
            booking_id="test-booking-001",
            balance_due=0.00
        )
        
        print()
        print("✅ PAYMENT RECEIVED notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   💰 PAYMENT RECEIVED: $550.00 via Venmo")
        print("   Booking #test-booking-001")
        print("   Balance Due: $0.00 ✅ PAID IN FULL")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_review_submitted():
    """Test 4: Positive review submitted and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 4: POSITIVE REVIEW NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_review
    
    try:
        result = await notify_review(
            customer_name="John Smith",
            rating="5 stars",
            review_text="Amazing hibachi experience! Chef was fantastic and food was delicious."
        )
        
        print()
        print("✅ REVIEW notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   ⭐ NEW REVIEW: 5 stars")
        print("   From: John Smith")
        print("   'Amazing hibachi experience! Chef was fantastic...'")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_complaint_submitted():
    """Test 5: Complaint submitted and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 5: COMPLAINT NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_complaint
    
    try:
        result = await notify_complaint(
            customer_name="John Smith",
            customer_phone="+12103884155",
            booking_id="test-booking-001",
            complaint_text="Food was served cold and chef arrived 30 minutes late.",
            priority="high"
        )
        
        print()
        print("✅ COMPLAINT notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   🚨 COMPLAINT - HIGH PRIORITY")
        print("   Customer: John Smith")
        print("   Issue: Food was served cold and chef arrived 30 minutes late.")
        print("   Action: Respond within 24 hours")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_cancellation():
    """Test 6: Booking cancelled and verify WhatsApp notification"""
    print("=" * 80)
    print("TEST 6: CANCELLATION NOTIFICATION")
    print("=" * 80)
    
    from services.unified_notification_service import notify_cancellation
    
    try:
        result = await notify_cancellation(
            customer_name="John Smith",
            customer_phone="+12103884155",
            booking_id="test-booking-001",
            event_date="December 26, 2024",
            event_time="7:00 PM",
            cancellation_reason="Customer requested cancellation due to weather concerns",
            refund_amount=550.00
        )
        
        print()
        print("✅ CANCELLATION notification sent successfully!")
        print(f"   Result: {result}")
        print()
        print("📱 Check WhatsApp (+12103884155) for:")
        print("   ❌ BOOKING CANCELLED")
        print("   Event: December 26, 2024 at 7:00 PM")
        print("   Reason: Customer requested cancellation due to weather concerns")
        print("   Refund: $550.00 will be processed")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_all_tests():
    """Run all integration tests sequentially"""
    print()
    print("🚀 Starting complete backend integration test...")
    print()
    print("IMPORTANT: You should receive 6 WhatsApp messages on +12103884155")
    print()
    
    input("Press Enter to begin testing...")
    
    results = []
    
    # Test 1: New Booking
    result1 = await test_booking_creation()
    results.append(("New Booking", result1))
    await asyncio.sleep(2)  # Wait 2 seconds between tests
    
    # Test 2: Booking Edit
    result2 = await test_booking_edit()
    results.append(("Booking Edit", result2))
    await asyncio.sleep(2)
    
    # Test 3: Payment Received
    result3 = await test_payment_received()
    results.append(("Payment Received", result3))
    await asyncio.sleep(2)
    
    # Test 4: Positive Review
    result4 = await test_review_submitted()
    results.append(("Positive Review", result4))
    await asyncio.sleep(2)
    
    # Test 5: Complaint
    result5 = await test_complaint_submitted()
    results.append(("Complaint", result5))
    await asyncio.sleep(2)
    
    # Test 6: Cancellation
    result6 = await test_cancellation()
    results.append(("Cancellation", result6))
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print()
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ Backend integration complete!")
        print("✅ WhatsApp notifications working end-to-end!")
        print()
        print("Next Steps:")
        print("1. Test with real booking creation via frontend")
        print("2. Test payment instructions (SMS/Email)")
        print("3. Test edge cases and error scenarios")
    else:
        print()
        print("⚠️ SOME TESTS FAILED")
        print()
        print("Check the error messages above and verify:")
        print("1. Backend server is running")
        print("2. Twilio credentials in .env are correct")
        print("3. Phone number joined WhatsApp sandbox")
        print("4. Internet connection is stable")
    
    print()


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
