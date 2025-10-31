"""
Email System Test Script

Tests the dual SMTP setup:
- IONOS SMTP for customer emails
- Gmail SMTP for admin emails
- Automatic routing logic
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent / "src"
sys.path.insert(0, str(backend_src))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify email is enabled
if os.getenv("EMAIL_NOTIFICATIONS_ENABLED") != "true":
    print("⚠️  EMAIL_NOTIFICATIONS_ENABLED is not set to 'true'")
    print("   Please update .env file and try again.")
    sys.exit(1)

from services.email_service import email_service


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_test(name: str, result: bool, details: str = ""):
    """Print test result"""
    icon = "✅" if result else "❌"
    print(f"\n{icon} {name}")
    if details:
        print(f"   {details}")


async def test_customer_email():
    """Test IONOS SMTP for customer emails"""
    print_header("Test 1: Customer Email via IONOS SMTP")
    
    # This should route to IONOS - using a valid test email
    email = "test.customer@outlook.com"  # Using outlook.com instead of example.com
    print(f"Sending to: {email}")
    print(f"Expected: IONOS SMTP (cs@myhibachichef.com)")
    
    success = email_service.send_welcome_email(
        email=email,
        full_name="Test Customer"
    )
    
    print_test(
        "Customer Email",
        success,
        f"Check backend logs for 'Routing email to {email} via IONOS SMTP'"
    )
    
    return success


async def test_admin_email():
    """Test Gmail SMTP for admin emails"""
    print_header("Test 2: Admin Email via Gmail SMTP")
    
    # This should route to Gmail
    email = "admin@myhibachichef.com"
    print(f"Sending to: {email}")
    print(f"Expected: Gmail SMTP (myhibachichef@gmail.com)")
    
    success = email_service.send_approval_email(
        email=email,
        full_name="Test Admin"
    )
    
    print_test(
        "Admin Email",
        success,
        "Check backend logs for 'Routing email to admin@myhibachichef.com via GMAIL SMTP'"
    )
    
    return success


async def test_routing_logic():
    """Test email routing logic"""
    print_header("Test 3: Email Routing Logic")
    
    test_cases = [
        ("customer@gmail.com", "ionos", "Customer Gmail (should use IONOS)"),
        ("user@outlook.com", "ionos", "Customer Outlook"),
        ("admin@myhibachichef.com", "gmail", "Admin MyHibachi"),
        ("staff@myhibachichef.com", "gmail", "Staff MyHibachi"),
        ("myhibachichef@gmail.com", "gmail", "Business Gmail (specific)"),
        ("support.admin@company.com", "gmail", "Admin keyword"),
    ]
    
    all_passed = True
    
    for email, expected_provider, description in test_cases:
        is_admin = email_service._is_admin_email(email)
        provider = email_service._get_smtp_provider(email)
        
        passed = provider == expected_provider
        all_passed = all_passed and passed
        
        print_test(
            description,
            passed,
            f"{email} → {provider.upper()} (expected: {expected_provider.upper()})"
        )
    
    return all_passed


async def test_smtp_configuration():
    """Test SMTP configuration"""
    print_header("Test 4: SMTP Configuration")
    
    # Check IONOS config
    ionos_host = os.getenv("SMTP_HOST")
    ionos_port = os.getenv("SMTP_PORT")
    ionos_user = os.getenv("SMTP_USERNAME")
    ionos_password = os.getenv("SMTP_PASSWORD")
    
    print("\nIONOS SMTP Configuration:")
    print(f"  Host: {ionos_host}")
    print(f"  Port: {ionos_port}")
    print(f"  Username: {ionos_user}")
    print(f"  Password: {'*' * len(ionos_password) if ionos_password else 'NOT SET'}")
    
    ionos_configured = all([ionos_host, ionos_port, ionos_user, ionos_password])
    print_test("IONOS Configuration", ionos_configured)
    
    # Check Gmail config
    gmail_user = os.getenv("GMAIL_USERNAME")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    print("\nGmail SMTP Configuration:")
    print(f"  Username: {gmail_user}")
    print(f"  App Password: {'*' * len(gmail_password) if gmail_password else 'NOT SET'}")
    
    gmail_configured = all([gmail_user, gmail_password])
    
    if not gmail_configured:
        print("\n⚠️  Gmail not configured. To set up:")
        print("   1. Go to https://myaccount.google.com/apppasswords")
        print("   2. Create App Password for 'Mail'")
        print("   3. Add to .env: GMAIL_APP_PASSWORD=your_16_char_password")
    
    print_test("Gmail Configuration", gmail_configured)
    
    return ionos_configured and gmail_configured


async def main():
    """Run all email tests"""
    print_header("Email System Test Suite")
    print("\nTesting dual SMTP configuration:")
    print("  - IONOS SMTP for customer emails")
    print("  - Gmail SMTP for admin emails")
    print("  - Automatic routing based on recipient")
    
    results = {}
    
    # Test SMTP configuration
    results["config"] = await test_smtp_configuration()
    
    if not results["config"]:
        print("\n❌ SMTP configuration incomplete. Please update .env file.")
        print("   See EMAIL_SETUP_GUIDE.md for instructions.")
        return
    
    # Test routing logic (no actual emails sent)
    results["routing"] = await test_routing_logic()
    
    # Test actual email sending
    print("\n⚠️  The following tests will send REAL emails:")
    response = input("\nContinue with email sending tests? (y/n): ")
    
    if response.lower() == 'y':
        results["customer"] = await test_customer_email()
        results["admin"] = await test_admin_email()
    else:
        print("\n⏭️  Skipping email sending tests")
        results["customer"] = None
        results["admin"] = None
    
    # Summary
    print_header("Test Summary")
    
    for test_name, result in results.items():
        if result is None:
            icon = "⏭️ "
            status = "SKIPPED"
        elif result:
            icon = "✅"
            status = "PASSED"
        else:
            icon = "❌"
            status = "FAILED"
        
        print(f"{icon} {test_name.upper()}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n✅ Email system is working correctly!")
    else:
        print("\n❌ Some tests failed. Check logs for details.")
        print("   Log file: apps/backend/logs/app.log")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
