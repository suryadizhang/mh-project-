"""
Direct test of Zelle email parsing using the most recent email
"""
import os
import sys
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.payment_email_monitor import PaymentEmailParser

def fetch_latest_email():
    """Fetch the most recent email directly using IMAP"""
    
    print("=" * 70)
    print("Fetching Latest Email from Gmail")
    print("=" * 70)
    
    # Connect to Gmail
    print("\n🔄 Connecting to Gmail IMAP...")
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    
    email_user = os.getenv('GMAIL_USER')
    email_pass = os.getenv('GMAIL_APP_PASSWORD')
    
    try:
        mail.login(email_user, email_pass)
        print("✅ Connected!\n")
        
        # Select inbox
        mail.select('INBOX')
        
        # Search for ALL emails (get the most recent)
        print("📧 Searching for recent emails...")
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK':
            print("❌ Failed to search emails")
            return None
        
        # Get list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            print("❌ No emails found")
            return None
        
        # Get the last 5 emails
        latest_ids = email_ids[-5:]
        print(f"✅ Found {len(email_ids)} total emails. Checking last 5...\n")
        
        for email_id in reversed(latest_ids):
            # Fetch the email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                continue
            
            # Parse email
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get subject
                    subject_header = msg['Subject']
                    if subject_header:
                        subject, encoding = decode_header(subject_header)[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or 'utf-8')
                    else:
                        subject = "No Subject"
                    
                    # Get from
                    from_header = msg['From']
                    
                    # Get date
                    date_header = msg['Date']
                    
                    print(f"📧 Email ID: {email_id.decode()}")
                    print(f"   From: {from_header}")
                    print(f"   Subject: {subject}")
                    print(f"   Date: {date_header}")
                    
                    # Check if this is the Zelle email
                    if 'suryadi' in subject.lower() and '$1.00' in subject:
                        print(f"\n✅ FOUND YOUR ZELLE EMAIL!\n")
                        
                        # Get body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        print("=" * 70)
                        print("Testing Payment Email Parser")
                        print("=" * 70)
                        
                        print(f"\n📋 Input:")
                        print(f"   Subject: {subject}")
                        print(f"   Body length: {len(body)} characters\n")
                        
                        # Parse the email
                        print("🔍 Parsing Zelle email...")
                        parsed = PaymentEmailParser.parse_zelle_email(subject, body)
                        
                        if parsed:
                            print("✅ Successfully parsed!\n")
                            print("📊 Extracted Data:")
                            print(f"   Provider: {parsed.get('provider', 'Unknown')}")
                            print(f"   Amount: ${parsed.get('amount', 0):.2f}")
                            print(f"   Sender Name: {parsed.get('sender_name', 'Not found')}")
                            print(f"   Customer Phone: {parsed.get('customer_phone', 'Not found')}")
                            print(f"   Transaction ID: {parsed.get('transaction_id', 'N/A')}")
                            
                            # Show matching capabilities
                            print("\n" + "=" * 70)
                            print("🎯 Matching Capabilities")
                            print("=" * 70)
                            
                            sender = parsed.get('sender_name', '')
                            phone = parsed.get('customer_phone', '')
                            
                            if sender:
                                print(f"\n✅ Can match by SENDER NAME: '{sender}'")
                                names = sender.split()
                                if len(names) >= 2:
                                    print(f"   • Full name match: '{sender}' → +100 points")
                                    print(f"   • First name match: '{names[0]}' → +75 points")
                                    print(f"   • Last name match: '{names[-1]}' → +75 points")
                            
                            if phone:
                                print(f"\n✅ Can match by PHONE NUMBER: '{phone}'")
                                print(f"   • Full match: '{phone}' → +100 points")
                                print(f"   • Last 4 digits: '*{phone[-4:]}' → +40 points")
                            
                            if not sender and not phone:
                                print("\n⚠️  No name or phone extracted!")
                                print("   Will need to rely on amount matching only")
                            
                            # Test scenarios
                            print("\n" + "=" * 70)
                            print("📝 Test Scenarios (what would match)")
                            print("=" * 70)
                            
                            if sender:
                                names = sender.split()
                                print(f"\n✅ WOULD MATCH:")
                                print(f"   • Customer name = '{sender}' (exact)")
                                if len(names) >= 2:
                                    print(f"   • Customer name = '{names[0]} Smith' (first name)")
                                    print(f"   • Customer name = 'John {names[-1]}' (last name)")
                            
                            if phone:
                                print(f"   • Customer phone = '{phone}' (exact)")
                                print(f"   • Customer phone ends with '{phone[-4:]}' (partial)")
                            
                            print(f"\n❌ WOULD NOT MATCH:")
                            print(f"   • Customer name = 'Alice Brown' AND phone = '9165551234'")
                            print(f"     (neither name nor phone matches)")
                            
                            return True
                        else:
                            print("❌ Failed to parse email\n")
                            print("Email body preview (first 500 chars):")
                            print("-" * 70)
                            print(body[:500])
                            print("-" * 70)
                            return False
                    
                    print()
        
        print("⚠️  Could not find the Zelle email with 'Suryadi' and '$1.00'")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        mail.logout()

if __name__ == "__main__":
    success = fetch_latest_email()
    sys.exit(0 if success else 1)
