"""
Interactive Test Script for Unified Notification Service

Tests all notification types and displays the actual messages that will be sent.
Works in MOCK mode (no API credentials needed).
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.unified_notification_service import UnifiedNotificationService


async def test_with_details():
    """Test all notification types with detailed output"""
    
    print("\n" + "="*70)
    print("📱 MY HIBACHI CHEF - UNIFIED NOTIFICATION SYSTEM TEST")
    print("="*70)
    print("\n✅ Running in MOCK mode (no API credentials needed)")
    print("✅ All notifications will be logged to console")
    print("\n" + "-"*70)
    
    service = UnifiedNotificationService()
    
    # Test Data
    test_customer = {
        "name": "Suryadi Zhang",
        "phone": "+19167408768"
    }
    
    test_booking = {
        "id": 12345,
        "event_date": "November 15, 2025",
        "event_time": "6:00 PM",
        "guest_count": 15,
        "location": "47481 Towhee Street, Fremont CA 94539"
    }
    
    # ==========================================
    # 1. NEW BOOKING NOTIFICATION
    # ==========================================
    print("\n\n1️⃣  NEW BOOKING NOTIFICATION")
    print("-"*70)
    print("Sent to: Customer + Admin")
    print("When: Customer creates a new booking")
    print("-"*70)
    
    result = await service.send_new_booking_notification(
        customer_name=test_customer["name"],
        customer_phone=test_customer["phone"],
        event_date=test_booking["event_date"],
        event_time=test_booking["event_time"],
        guest_count=test_booking["guest_count"],
        location=test_booking["location"],
        booking_id=test_booking["id"]
    )
    
    print(f"\n✅ Customer notification: {result['customer']['channel']}")
    print(f"✅ Admin notification: {result['admin']['channel']}")
    
    input("\n👉 Press ENTER to continue to next test...")
    
    # ==========================================
    # 2. BOOKING EDIT NOTIFICATION
    # ==========================================
    print("\n\n2️⃣  BOOKING EDIT NOTIFICATION")
    print("-"*70)
    print("Sent to: Customer + Admin")
    print("When: Booking details are changed")
    print("-"*70)
    
    result = await service.send_booking_edit_notification(
        customer_name=test_customer["name"],
        customer_phone=test_customer["phone"],
        booking_id=test_booking["id"],
        changes={
            "event_date": {
                "old": "November 15, 2025",
                "new": "November 20, 2025"
            },
            "guest_count": {
                "old": 15,
                "new": 20
            },
            "event_time": {
                "old": "6:00 PM",
                "new": "7:00 PM"
            }
        }
    )
    
    print(f"\n✅ Customer notification: {result['customer']['channel']}")
    print(f"✅ Admin notification: {result['admin']['channel']}")
    
    input("\n👉 Press ENTER to continue to next test...")
    
    # ==========================================
    # 3. BOOKING CANCELLATION NOTIFICATION
    # ==========================================
    print("\n\n3️⃣  BOOKING CANCELLATION NOTIFICATION")
    print("-"*70)
    print("Sent to: Customer + Admin")
    print("When: Booking is cancelled")
    print("-"*70)
    
    result = await service.send_cancellation_notification(
        customer_name=test_customer["name"],
        customer_phone=test_customer["phone"],
        booking_id=test_booking["id"],
        event_date=test_booking["event_date"],
        reason="Schedule conflict - family emergency",
        refund_amount=150.00
    )
    
    print(f"\n✅ Customer notification: {result['customer']['channel']}")
    print(f"✅ Admin notification: {result['admin']['channel']}")
    
    input("\n👉 Press ENTER to continue to next test...")
    
    # ==========================================
    # 4. PAYMENT CONFIRMATION NOTIFICATION
    # ==========================================
    print("\n\n4️⃣  PAYMENT CONFIRMATION NOTIFICATION")
    print("-"*70)
    print("Sent to: Customer + Admin")
    print("When: Payment is received and confirmed")
    print("-"*70)
    
    result = await service.send_payment_confirmation(
        customer_name=test_customer["name"],
        customer_phone=test_customer["phone"],
        amount=450.00,
        payment_method="Venmo",
        booking_id=test_booking["id"],
        event_date=test_booking["event_date"]
    )
    
    print(f"\n✅ Customer notification: {result['customer']['channel']}")
    print(f"✅ Admin notification: {result['admin']['channel']}")
    
    input("\n👉 Press ENTER to continue to next test...")
    
    # ==========================================
    # 5. REVIEW NOTIFICATION
    # ==========================================
    print("\n\n5️⃣  REVIEW NOTIFICATION")
    print("-"*70)
    print("Sent to: Admin only (customer wrote the review)")
    print("When: Customer submits a review")
    print("-"*70)
    
    result = await service.send_review_notification(
        customer_name=test_customer["name"],
        rating=5,
        review_text="Amazing experience! The chef was incredibly professional and the food was absolutely delicious. Everyone at our party loved it! Would definitely book again for our next event.",
        booking_id=test_booking["id"]
    )
    
    print(f"\n✅ Admin notification: {result['admin']['channel']}")
    
    input("\n👉 Press ENTER to continue to next test...")
    
    # ==========================================
    # 6. COMPLAINT NOTIFICATION (HIGH PRIORITY)
    # ==========================================
    print("\n\n6️⃣  COMPLAINT NOTIFICATION (HIGH PRIORITY)")
    print("-"*70)
    print("Sent to: Customer (acknowledgment) + Admin (urgent action)")
    print("When: Customer files a complaint")
    print("-"*70)
    
    result = await service.send_complaint_notification(
        customer_name=test_customer["name"],
        customer_phone=test_customer["phone"],
        complaint_text="The chef arrived 20 minutes late and didn't bring all the equipment. We had to provide our own griddle.",
        booking_id=test_booking["id"],
        priority="high"
    )
    
    print(f"\n✅ Customer notification: {result['customer']['channel']}")
    print(f"✅ Admin notification: {result['admin']['channel']}")
    
    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n\n" + "="*70)
    print("✅ ALL NOTIFICATION TESTS COMPLETE!")
    print("="*70)
    print("\n📊 Summary:")
    print("   • 6 notification types tested")
    print("   • Customer messages: 5 (booking, edit, cancel, payment, complaint)")
    print("   • Admin messages: 6 (all events)")
    print("   • All messages formatted professionally with emojis")
    print("   • Phone number prominent in all communications")
    print("\n🚀 Next Steps:")
    print("   1. Set WHATSAPP_PROVIDER=twilio in .env")
    print("   2. Add Twilio credentials (see WHATSAPP_BUSINESS_API_SETUP_GUIDE.md)")
    print("   3. Restart backend server")
    print("   4. Real WhatsApp/SMS notifications will be sent!")
    print("\n💡 Or keep using mock mode for development (no API costs)")
    print("="*70 + "\n")


async def quick_test():
    """Quick test - all notifications at once"""
    print("\n🚀 QUICK TEST - All notifications\n")
    
    service = UnifiedNotificationService()
    
    # Run all tests
    await service.send_new_booking_notification(
        "Suryadi Zhang", "+19167408768",
        event_date="Nov 15, 2025", event_time="6 PM",
        guest_count=15, location="Fremont CA", booking_id=123
    )
    
    await service.send_booking_edit_notification(
        "Suryadi Zhang", "+19167408768", booking_id=123,
        changes={"guest_count": {"old": 15, "new": 20}}
    )
    
    await service.send_cancellation_notification(
        "Suryadi Zhang", "+19167408768",
        booking_id=123, event_date="Nov 15", refund_amount=150.00
    )
    
    await service.send_payment_confirmation(
        "Suryadi Zhang", "+19167408768",
        amount=450.00, payment_method="Venmo",
        booking_id=123, event_date="Nov 15"
    )
    
    await service.send_review_notification(
        "Suryadi Zhang", rating=5,
        review_text="Amazing service!", booking_id=123
    )
    
    await service.send_complaint_notification(
        "Suryadi Zhang", "+19167408768",
        complaint_text="Chef was late", booking_id=123, priority="medium"
    )
    
    print("\n✅ All notifications sent!\n")


if __name__ == "__main__":
    print("\n🎯 Choose test mode:")
    print("   1. Interactive (step-by-step with message preview)")
    print("   2. Quick (all at once)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_with_details())
    elif choice == "2":
        asyncio.run(quick_test())
    else:
        print("❌ Invalid choice. Running quick test...")
        asyncio.run(quick_test())
