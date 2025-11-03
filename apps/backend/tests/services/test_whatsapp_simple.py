"""
Simple Twilio WhatsApp test - using environment variables
"""
import os
from twilio.rest import Client

# Load Twilio credentials from environment variables
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid_here")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Validate credentials are set
if ACCOUNT_SID == "your_account_sid_here" or AUTH_TOKEN == "your_auth_token_here":
    print("\n❌ ERROR: Twilio credentials not configured!")
    print("Please set environment variables:")
    print("  TWILIO_ACCOUNT_SID")
    print("  TWILIO_AUTH_TOKEN")
    print("  TWILIO_WHATSAPP_FROM (optional)")
    exit(1)

print("\n" + "="*70)
print("📱 TWILIO WHATSAPP TEST")
print("="*70)
print("\n⚠️  Make sure you joined the sandbox first!")
print("   Send 'join bus-pot' to +1 415 523 8886 on WhatsApp\n")

# Get phone number
phone = input("Enter your phone number (format: +12103884155): ").strip()
if not phone:
    phone = "+12103884155"

# Add whatsapp: prefix if not present
if not phone.startswith("whatsapp:"):
    phone = f"whatsapp:{phone}"

print(f"\n🚀 Sending WhatsApp message to {phone}...")
print("-"*70)

try:
    # Initialize Twilio client
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
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
        from_=WHATSAPP_FROM,
        to=phone
    )
    
    print("\n✅ SUCCESS!")
    print(f"   Message SID: {message.sid}")
    print(f"   Status: {message.status}")
    print(f"   To: {phone}")
    print("\n📱 Check your WhatsApp NOW! You should see the booking confirmation!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Did you join the sandbox? Send 'join bus-pot' to +1 415 523 8886")
    print("   2. Is your phone number correct? Format: +1XXXXXXXXXX")
    print("   3. Check Twilio console Messages log for details")

print("\n" + "="*70 + "\n")
