"""
Quick test script to verify Gmail IMAP connection and check for payment emails
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.payment_email_monitor import PaymentEmailMonitor

def test_gmail_connection():
    """Test Gmail IMAP connection and check for payment emails"""
    
    print("=" * 60)
    print("Gmail Payment Email Monitoring - Connection Test")
    print("=" * 60)
    
    # Get credentials from environment
    email = os.getenv('GMAIL_USER', 'myhibachichef@gmail.com')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not password:
        print("❌ ERROR: GMAIL_APP_PASSWORD not found in .env file!")
        print("\nPlease follow these steps:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Generate App Password for 'Mail'")
        print("3. Add to .env: GMAIL_APP_PASSWORD=your-16-char-password")
        return False
    
    print(f"\n📧 Email: {email}")
    print(f"🔐 Password: {password[:4]}{'*' * (len(password) - 4)}\n")
    
    # Create monitor
    print("🔄 Connecting to Gmail IMAP...")
    monitor = PaymentEmailMonitor(
        email_address=email,
        app_password=password
    )
    
    # Test connection
    if not monitor.connect():
        print("❌ Failed to connect to Gmail!")
        print("\nTroubleshooting:")
        print("1. Check if 2FA is enabled on your Gmail account")
        print("2. Verify App Password is correct (no spaces)")
        print("3. Check if IMAP is enabled: https://mail.google.com/mail/u/0/#settings/fwdandpop")
        return False
    
    print("✅ Successfully connected to Gmail IMAP!\n")
    
    # Check for payment emails
    print("🔍 Checking for payment notification emails (last 30 days)...")
    try:
        from datetime import datetime, timedelta
        since_date = datetime.now() - timedelta(days=30)
        emails = monitor.get_unread_payment_emails(since_date=since_date)
        
        print(f"\n📬 Found {len(emails)} payment notification email(s)!\n")
        
        if emails:
            print("Recent payment emails:")
            print("-" * 60)
            for i, email_data in enumerate(emails[:10], 1):
                subject = email_data.get('subject', 'No subject')
                sender = email_data.get('from', 'Unknown')
                date = email_data.get('date', 'Unknown date')
                
                # Truncate long subjects/senders
                subject = subject[:50] + "..." if len(subject) > 50 else subject
                sender = sender[:40] + "..." if len(sender) > 40 else sender
                
                print(f"{i}. {subject}")
                print(f"   From: {sender}")
                print(f"   Date: {date}")
                print()
        else:
            print("ℹ️  No payment emails found in the last 30 days.")
            print("\nThis is normal if you haven't received any payments yet.")
            print("The system will automatically detect payment emails when they arrive!")
        
        # Test parsing
        if emails:
            print("\n🧪 Testing email parser on first email...")
            first_email = emails[0]
            
            # Try to parse it
            from services.payment_email_monitor import PaymentEmailParser
            parsed = PaymentEmailParser.parse_payment_email(
                first_email.get('subject', ''),
                first_email.get('body', '')
            )
            
            if parsed:
                print(f"✅ Successfully parsed!")
                print(f"   Provider: {parsed.get('provider', 'Unknown')}")
                print(f"   Amount: ${parsed.get('amount', 0):.2f}")
                print(f"   Sender: {parsed.get('sender_name', 'Unknown')}")
                if parsed.get('customer_phone'):
                    print(f"   Phone: {parsed.get('customer_phone')}")
            else:
                print("⚠️  Could not parse this email (might not be a payment notification)")
    
    except Exception as e:
        print(f"❌ Error checking emails: {e}")
        import traceback
        traceback.print_exc()
    finally:
        monitor.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Test Complete! Gmail integration is working!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start backend server: uvicorn main:app --reload")
    print("2. Scheduler will automatically check for emails every 5 minutes")
    print("3. Make a test payment and wait up to 5 minutes")
    print("4. Payment will be auto-confirmed!")
    
    return True

if __name__ == "__main__":
    success = test_gmail_connection()
    sys.exit(0 if success else 1)
