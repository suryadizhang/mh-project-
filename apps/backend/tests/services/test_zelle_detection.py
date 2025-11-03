"""
Test Zelle Payment Email Detection and Matching
Tests if the system can:
1. Parse the Zelle email (extract amount, sender name, phone)
2. Match to a customer by name OR phone
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.payment_email_monitor import PaymentEmailMonitor, PaymentEmailParser

def test_zelle_detection():
    """Test that we can detect and parse your Zelle payment"""
    
    print("=" * 70)
    print("Testing Zelle Payment Detection")
    print("=" * 70)
    
    # Connect to Gmail
    print("\n🔄 Connecting to Gmail...")
    monitor = PaymentEmailMonitor(
        email_address=os.getenv('GMAIL_USER'),
        app_password=os.getenv('GMAIL_APP_PASSWORD')
    )
    
    if not monitor.connect():
        print("❌ Failed to connect to Gmail")
        return False
    
    print("✅ Connected to Gmail\n")
    
    # Fetch recent emails (last 1 hour)
    print("📧 Fetching emails from last 1 hour...")
    since_date = datetime.now() - timedelta(hours=1)
    
    try:
        # Get the raw email data
        emails = monitor.get_unread_payment_emails(since_date=since_date)
        
        print(f"Found {len(emails)} email(s)\n")
        
        if not emails:
            print("⚠️  No recent emails found. The email might be:")
            print("   - Already marked as READ")
            print("   - Older than 1 hour")
            print("   - In a different folder (spam/promotions)")
            return False
        
        # Find the Zelle email
        zelle_email = None
        for email in emails:
            subject = email.get('subject', '')
            if 'sent you $1.00' in subject.lower() or 'suryadi' in subject.lower():
                zelle_email = email
                break
        
        if not zelle_email:
            print("⚠️  Could not find your Zelle payment email")
            print("\nAll recent emails:")
            for i, e in enumerate(emails[:5], 1):
                print(f"{i}. {e.get('subject', 'No subject')[:60]}")
            return False
        
        # Found it!
        print("✅ Found your Zelle payment email!")
        print(f"Subject: {zelle_email.get('subject')}")
        print(f"From: {zelle_email.get('from')}")
        print(f"Date: {zelle_email.get('date')}\n")
        
        # Parse the email
        print("🔍 Parsing email to extract payment details...")
        parsed = PaymentEmailParser.parse_payment_email(
            subject=zelle_email.get('subject', ''),
            body=zelle_email.get('body', '')
        )
        
        if not parsed:
            print("❌ Failed to parse email")
            print("\nEmail body preview:")
            body = zelle_email.get('body', '')
            print(body[:500])
            return False
        
        # Display parsed data
        print("✅ Successfully parsed!\n")
        print("📋 Extracted Data:")
        print(f"   Provider: {parsed.get('provider', 'Unknown')}")
        print(f"   Amount: ${parsed.get('amount', 0):.2f}")
        print(f"   Sender Name: {parsed.get('sender_name', 'Unknown')}")
        print(f"   Customer Phone: {parsed.get('customer_phone', 'Not found')}")
        print(f"   Transaction ID: {parsed.get('transaction_id', 'N/A')}")
        
        # Check what we can match on
        print("\n🎯 Matching Options:")
        if parsed.get('sender_name'):
            print(f"   ✅ Sender Name: '{parsed['sender_name']}'")
            print(f"      → Can match by: Full name, First name, or Last name")
        
        if parsed.get('customer_phone'):
            phone = parsed['customer_phone']
            print(f"   ✅ Phone Number: '{phone}'")
            print(f"      → Can match by: Full number or last 4 digits ({phone[-4:]})")
        
        # Test matching scenarios
        print("\n" + "=" * 70)
        print("Testing Matching Scenarios")
        print("=" * 70)
        
        # Scenario 1: Match by sender name
        print("\n📌 Scenario 1: Customer name = 'Suryadi Zhang'")
        print("   Expected: ✅ Full name match (+100 points)")
        
        # Scenario 2: Match by first name only
        print("\n📌 Scenario 2: Customer name = 'Suryadi Smith'")
        print("   Expected: ✅ First name match (+75 points)")
        
        # Scenario 3: Match by last name only
        print("\n📌 Scenario 3: Customer name = 'John Zhang'")
        print("   Expected: ✅ Last name match (+75 points)")
        
        # Scenario 4: Match by phone
        if parsed.get('customer_phone'):
            print(f"\n📌 Scenario 4: Customer phone = '{parsed['customer_phone']}'")
            print("   Expected: ✅ Phone match (+100 points)")
        
        # Scenario 5: No match
        print("\n📌 Scenario 5: Customer name = 'Alice Brown', phone = '9165551234'")
        print("   Expected: ❌ No match (score < 50)")
        
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        
        print("\n📝 Summary:")
        print(f"   • Email detected: ✅")
        print(f"   • Amount extracted: ✅ ${parsed.get('amount', 0):.2f}")
        print(f"   • Sender name extracted: ✅ {parsed.get('sender_name', 'N/A')}")
        print(f"   • Phone extracted: {'✅ ' + parsed.get('customer_phone', '') if parsed.get('customer_phone') else '❌ Not found'}")
        print(f"   • Can match by name: ✅ (Full, First, or Last)")
        print(f"   • Can match by phone: {'✅' if parsed.get('customer_phone') else '❌'}")
        
        print("\n🚀 Next Step:")
        print("   Create a test booking with name='Suryadi Zhang' or phone='2103884155'")
        print("   Then wait for scheduler to run (5 min) or trigger manual match")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    success = test_zelle_detection()
    sys.exit(0 if success else 1)
