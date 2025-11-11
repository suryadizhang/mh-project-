"""
Test admin notifications in new concise format
"""

import os
import pytest
from twilio.rest import Client

# Load Twilio credentials from environment variables
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid_here")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Validate credentials are set
if (
    ACCOUNT_SID == "your_account_sid_here"
    or AUTH_TOKEN == "your_auth_token_here"
):
    pytest.skip("Twilio credentials not configured", allow_module_level=True)

print("\n" + "=" * 70)
print("📱 TESTING ADMIN NOTIFICATIONS (Concise Internal Format)")
print("=" * 70)
print("\n⚠️  These are the messages YOU (admin) will receive on WhatsApp\n")

# Admin phone number
phone = input("Enter admin phone (default: +12103884155): ").strip()
if not phone:
    phone = "+12103884155"

# Add whatsapp: prefix
if not phone.startswith("whatsapp:"):
    phone = f"whatsapp:{phone}"

print(f"\n🚀 Sending admin notifications to {phone}...")
print("=" * 70)

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Test all 6 admin notification types
notifications = [
    {
        "title": "1️⃣ NEW BOOKING",
        "message": """🆕 NEW BOOKING ACCEPTED

Date: Sep 8, 2025 at 6:00 PM
Location: Station CA-BAY-001
Customer: John Smith
Guests: ~15 people

Booking #12345

Check admin portal for details.""",
    },
    {
        "title": "2️⃣ BOOKING EDIT",
        "message": """✏️ BOOKING EDITED

Booking #12345
Customer: John Smith

Changes:
• Guest Count: 15 → 20
• Event Time: 6:00 PM → 7:00 PM

Check admin portal for details.""",
    },
    {
        "title": "3️⃣ PAYMENT RECEIVED",
        "message": """💰 PAYMENT RECEIVED

Amount: $450.00 (Venmo)
Booking: #12345
Event: Sep 8, 2025
Customer: John Smith

Status: Fully Paid ✅""",
    },
    {
        "title": "4️⃣ REVIEW RECEIVED",
        "message": """⭐ NEW REVIEW RECEIVED

Rating: ⭐⭐⭐⭐⭐ (5/5)
Booking: #12345
Customer: John Smith

"Amazing service! Highly recommend!"

Check admin portal for details.""",
    },
    {
        "title": "5️⃣ COMPLAINT (HIGH PRIORITY)",
        "message": """🟠 COMPLAINT RECEIVED (HIGH)

Booking: #12345
Customer: John Smith

"Chef arrived 15 minutes late"

⚠️ Contact customer within 24h
Check admin portal for details.""",
    },
    {
        "title": "6️⃣ CANCELLATION",
        "message": """❌ BOOKING CANCELLED

Booking #12345
Event: Sep 8, 2025
Customer: John Smith
Reason: Schedule conflict
Refund: $450.00

Check admin portal for details.""",
    },
]

print("\nSending 6 different notification types...\n")

for notif in notifications:
    try:
        message = client.messages.create(
            body=notif["message"], from_=WHATSAPP_FROM, to=phone
        )
        print(f"✅ {notif['title']}: Sent (SID: {message.sid})")
    except Exception as e:
        print(f"❌ {notif['title']}: Failed - {e}")

print("\n" + "=" * 70)
print("📱 Check your WhatsApp! You should receive 6 admin notifications")
print("   All in concise internal format - easy to scan quickly!")
print("=" * 70 + "\n")
