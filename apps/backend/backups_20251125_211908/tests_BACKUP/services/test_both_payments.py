"""
Test both Zelle and Venmo payment detection
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

def test_recent_payments():
    """Check for both Zelle and Venmo payments"""
    
    print("=" * 70)
    print("Testing Recent Payment Emails (Zelle + Venmo)")
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
            return False
        
        # Get list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            print("❌ No emails found")
            return False
        
        # Get the last 10 emails
        latest_ids = email_ids[-10:]
        print(f"✅ Found {len(email_ids)} total emails. Checking last 10...\n")
        
        found_payments = []
        
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
                    
                    # Check if this is a payment email
                    is_zelle = 'sent you $' in subject.lower()
                    is_venmo = 'venmo' in from_header.lower() and '$' in subject
                    
                    if is_zelle or is_venmo:
                        # Get body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                                elif part.get_content_type() == "text/html":
                                    body = part.get_payload(decode=True).decode()
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        payment_type = "Zelle" if is_zelle else "Venmo"
                        
                        print(f"{'='*70}")
                        print(f"📧 Found {payment_type} Email!")
                        print(f"{'='*70}")
                        print(f"From: {from_header}")
                        print(f"Subject: {subject}\n")
                        
                        # Parse the email
                        print(f"🔍 Parsing {payment_type} email...")
                        
                        if is_venmo:
                            parsed = PaymentEmailParser.parse_venmo_email(subject, body)
                        else:
                            parsed = PaymentEmailParser.parse_zelle_email(subject, body)
                        
                        if parsed:
                            print("✅ Successfully parsed!\n")
                            print("📊 Extracted Data:")
                            print(f"   Provider: {parsed.get('provider', 'Unknown')}")
                            print(f"   Amount: ${parsed.get('amount', 0):.2f}")
                            print(f"   Sender Name: {parsed.get('sender_name', 'Not found')}")
                            print(f"   Username: {parsed.get('sender_username', 'N/A')}")
                            print(f"   Customer Phone: {parsed.get('customer_phone', 'Not found')}")
                            
                            # Show matching capabilities
                            print(f"\n🎯 Can Match By:")
                            
                            sender = parsed.get('sender_name', '')
                            phone = parsed.get('customer_phone', '')
                            username = parsed.get('sender_username', '')
                            
                            if sender:
                                names = sender.split()
                                print(f"   ✅ Sender Name: '{sender}'")
                                if len(names) >= 2:
                                    print(f"      • Full: '{sender}' (+100)")
                                    print(f"      • First: '{names[0]}' (+75)")
                                    print(f"      • Last: '{names[-1]}' (+75)")
                            
                            if phone:
                                print(f"   ✅ Phone: '{phone}' (+100)")
                            
                            if username:
                                print(f"   ✅ Venmo Username: '{username}' (+100)")
                            
                            found_payments.append({
                                'type': payment_type,
                                'amount': parsed.get('amount'),
                                'sender': sender,
                                'phone': phone,
                                'username': username
                            })
                        else:
                            print("❌ Failed to parse email\n")
                            print("Body preview (first 300 chars):")
                            print("-" * 70)
                            print(body[:300])
                            print("-" * 70)
                        
                        print()
        
        # Summary
        if found_payments:
            print("=" * 70)
            print(f"✅ Summary: Found {len(found_payments)} Payment(s)")
            print("=" * 70)
            
            for i, payment in enumerate(found_payments, 1):
                print(f"\n{i}. {payment['type']} - ${payment['amount']:.2f}")
                print(f"   Sender: {payment['sender'] or 'N/A'}")
                print(f"   Phone: {payment['phone'] or 'N/A'}")
                if payment.get('username'):
                    print(f"   Username: {payment['username']}")
            
            print("\n" + "=" * 70)
            print("🎯 Matching Strategy:")
            print("=" * 70)
            print("System will match payments using (NAME OR PHONE):")
            print("  • Full name match: +100 points")
            print("  • First or last name: +75 points")
            print("  • Phone number: +100 points")
            print("  • Venmo username: +100 points")
            print("  • Amount match: +25 points")
            print("\nMinimum score for auto-confirm: 50 points")
            print("Your payments have enough data to match! ✅")
            
        else:
            print("⚠️  No payment emails found in last 10 emails")
        
        return len(found_payments) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        mail.logout()

if __name__ == "__main__":
    success = test_recent_payments()
    sys.exit(0 if success else 1)
