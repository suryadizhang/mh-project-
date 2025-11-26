#!/usr/bin/env python3
"""
Quick test script to verify Resend email integration.
Tests all 4 email types: welcome, approval, rejection, suspension.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file FIRST before importing anything else
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)

from src.services.email_service import email_service


def test_resend_integration():
    """Test Resend email service with all email types."""

    print("=" * 60)
    print("🧪 RESEND EMAIL INTEGRATION TEST")
    print("=" * 60)
    print()

    # Test email recipient (use your real email to receive test)
    test_email = input("Enter your email to receive test emails: ").strip()

    if not test_email or "@" not in test_email:
        print("❌ Invalid email address")
        return

    print(f"\n📧 Sending test emails to: {test_email}")
    print()

    # Test 1: Welcome Email
    print("1️⃣ Testing Welcome Email...")
    try:
        result = email_service.send_welcome_email(
            email=test_email,
            full_name="Test Admin"
        )
        if result:
            print(f"   ✅ Welcome email sent successfully!")
        else:
            print(f"   ❌ Failed to send welcome email")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print()

    # Test 2: Approval Email
    print("2️⃣ Testing Approval Email...")
    try:
        result = email_service.send_approval_email(
            email=test_email,
            full_name="Test Admin"
        )
        if result:
            print(f"   ✅ Approval email sent successfully!")
        else:
            print(f"   ❌ Failed to send approval email")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print()

    # Test 3: Rejection Email
    print("3️⃣ Testing Rejection Email...")
    try:
        result = email_service.send_rejection_email(
            email=test_email,
            full_name="Test Admin",
            reason="This is a test rejection email - please disregard"
        )
        if result:
            print(f"   ✅ Rejection email sent successfully!")
        else:
            print(f"   ❌ Failed to send rejection email")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print()

    # Test 4: Suspension Email
    print("4️⃣ Testing Suspension Email...")
    try:
        result = email_service.send_suspension_email(
            email=test_email,
            full_name="Test Admin",
            reason="This is a test suspension email - please disregard"
        )
        if result:
            print(f"   ✅ Suspension email sent successfully!")
        else:
            print(f"   ❌ Failed to send suspension email")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print()
    print("=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)
    print()
    print("📊 Check your inbox and Resend dashboard:")
    print("   - Inbox: Look for 4 emails from cs@myhibachichef.com")
    print("   - Dashboard: https://resend.com/logs")
    print()


if __name__ == "__main__":
    test_resend_integration()
