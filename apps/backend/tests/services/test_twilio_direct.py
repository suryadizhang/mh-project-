"""
Direct Twilio WhatsApp test without service layer
"""
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

print("\n" + "="*70)
print("📱 DIRECT TWILIO WHATSAPP TEST")
print("="*70)
print(f"\nAccount SID: {account_sid}")
print(f"Auth Token: {'*' * 20 if auth_token else 'NOT FOUND'}")
print(f"WhatsApp From: {whatsapp_from}\n")

if not account_sid or not auth_token:
    print("❌ ERROR: Credentials not found in environment!")
    print("   Check that .env file exists and has correct values")
    exit(1)

# Get phone number
phone = input("Enter your phone number (format: +12103884155): ").strip()
if not phone:
    phone = "+12103884155"

print(f"\n🚀 Sending WhatsApp message to {phone}...")
print("-"*70)

try:
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Send message
    message = client.messages.create(
        body="""🎉 Booking Confirmed!

Hello Suryadi Zhang!

Your hibachi event is confirmed:

📅 Date: November 15, 2025
🕐 Time: 6:00 PM
👥 Guests: 15
📍 Location: 47481 Towhee Street, Fremont CA 94539

Booking #12345

We'll send payment instructions shortly.

Questions? Reply here or call +19167408768

- My Hibachi Chef Team""",
        from_=whatsapp_from,
        to=f"whatsapp:{phone}"
    )
    
    print("\n✅ SUCCESS!")
    print(f"   Message SID: {message.sid}")
    print(f"   Status: {message.status}")
    print(f"   To: {phone}")
    print("\n📱 Check your WhatsApp now!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Make sure you joined the sandbox: send 'join bus-pot' to +1 415 523 8886")
    print("   2. Phone number format: +1XXXXXXXXXX")
    print("   3. Check Twilio console for error details")

print("\n" + "="*70 + "\n")
