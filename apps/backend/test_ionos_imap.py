#!/usr/bin/env python3
"""
Test IONOS IMAP connection for customer support email monitoring.
Tests cs@myhibachichef.com inbox (IONOS).
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)

from src.services.customer_email_monitor import customer_email_monitor

print("=" * 70)
print("🧪 IONOS IMAP CONNECTION TEST")
print("=" * 70)
print()

# Test connection
print("1️⃣ Testing IONOS IMAP connection...")
print(f"   Server: {customer_email_monitor.imap_server}")
print(f"   Email: {customer_email_monitor.email_address}")
print()

if customer_email_monitor.connect():
    print("   ✅ Connected successfully!")
    print()

    # Get email counts
    print("2️⃣ Checking inbox...")
    counts = customer_email_monitor.get_email_count()
    print(f"   📬 Total emails: {counts['total']}")
    print(f"   📭 Unread emails: {counts['unread']}")
    print()

    # Fetch unread emails (without marking as read)
    if counts['unread'] > 0:
        print("3️⃣ Fetching unread emails (preview only)...")
        emails = customer_email_monitor.fetch_unread_emails(mark_as_read=False)

        for i, email_data in enumerate(emails[:5], 1):  # Show first 5
            print(f"\n   📧 Email #{i}:")
            print(f"      From: {email_data['from_name']} <{email_data['from_address']}>")
            print(f"      Subject: {email_data['subject']}")
            print(f"      Body Preview: {email_data['text_body'][:100]}...")
            print(f"      Has Attachments: {email_data['has_attachments']}")

        if len(emails) > 5:
            print(f"\n   ... and {len(emails) - 5} more unread emails")
    else:
        print("3️⃣ No unread emails - inbox is clean! ✅")

    print()

    # Disconnect
    customer_email_monitor.disconnect()
    print("✅ Disconnected from IONOS IMAP")

else:
    print("   ❌ Connection failed!")
    print()
    print("   Troubleshooting:")
    print("   1. Check SMTP_USER in .env (should be cs@myhibachichef.com)")
    print("   2. Check SMTP_PASSWORD in .env")
    print("   3. Check IMAP_SERVER in .env (should be imap.ionos.com)")
    print("   4. Verify IONOS email account is active")

print()
print("=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print()
print("This service monitors cs@myhibachichef.com for:")
print("  • Customer support inquiries")
print("  • Booking questions")
print("  • General correspondence")
print()
print("Separate from:")
print("  • myhibachichef@gmail.com → Payment notifications only")
print("  • Resend API → Sending emails only")
print()
