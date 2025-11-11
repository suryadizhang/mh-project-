"""
Quick test to verify Twilio WhatsApp is working
"""
import asyncio
import sys
import os

# Load environment variables first!
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.unified_notification_service import UnifiedNotificationService
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')


async def test_whatsapp():
    """Test WhatsApp notification with Twilio"""
    
    print("\n" + "="*70)
    print("📱 TESTING TWILIO WHATSAPP INTEGRATION")
    print("="*70)
    print("\n⚠️  Make sure you've joined the WhatsApp sandbox first!")
    print("   Send 'join <code>' to +1 415 523 8886 on WhatsApp\n")
    
    # Get phone number from user
    phone = input("Enter your phone number (format: +19167408768): ").strip()
    
    if not phone:
        phone = "+19167408768"  # Default
    
    print(f"\n🚀 Sending test notification to {phone}...")
    print("-"*70)
    
    service = UnifiedNotificationService()
    
    # Send a new booking notification
    result = await service.send_new_booking_notification(
        customer_name="Suryadi Zhang",
        customer_phone=phone,
        event_date="November 15, 2025",
        event_time="6:00 PM",
        guest_count=15,
        location="47481 Towhee Street, Fremont CA 94539",
        booking_id=12345
    )
    
    print("\n" + "="*70)
    print("📊 RESULT:")
    print("="*70)
    print(f"Customer notification: {result['customer']}")
    print(f"Admin notification: {result['admin']}")
    
    if result['customer']['success']:
        print("\n✅ SUCCESS! Check your WhatsApp for the message!")
    else:
        print("\n⚠️  Issue occurred:")
        print(f"   Error: {result['customer'].get('error', 'Unknown')}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you joined the sandbox (send 'join <code>' to +1 415 523 8886)")
        print("   2. Verify your phone number format: +1XXXXXXXXXX")
        print("   3. Check Twilio console for error messages")
    
    print("\n")


if __name__ == "__main__":
    asyncio.run(test_whatsapp())
