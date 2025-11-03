"""
Get detailed content of the Zelle email
"""
import os
import sys
import email
from dotenv import load_dotenv
import imaplib

load_dotenv()

def get_zelle_email_detail():
    """Get full content of the most recent Zelle email"""
    
    print("=" * 60)
    print("Zelle Email - Detailed View")
    print("=" * 60)
    
    email_addr = os.getenv('GMAIL_USER', 'myhibachichef@gmail.com')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    try:
        # Connect
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(email_addr, password)
        mail.select('INBOX')
        
        # Get email #212 (the Zelle one)
        status, msg_data = mail.fetch(b'212', '(RFC822)')
        
        if status != 'OK':
            print("❌ Could not fetch email")
            return
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                print(f"\n📧 From: {msg.get('From')}")
                print(f"📧 Subject: {msg.get('Subject')}")
                print(f"📧 Date: {msg.get('Date')}")
                print("\n" + "-" * 60)
                print("EMAIL BODY:")
                print("-" * 60)
                
                # Get body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            print(body)
                            print("\n" + "-" * 60)
                            
                            # Check for phone
                            if '2103884155' in body:
                                print("✅ PHONE NUMBER FOUND: 2103884155")
                            else:
                                print("⚠️  Phone number NOT found in body")
                                print("   Note/memo might not be included in Bank of America Zelle emails")
                            
                            # Check for amount
                            if '$1' in body:
                                print("✅ AMOUNT FOUND: $1.00")
                            
                            break
                        elif content_type == "text/html":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            # Check HTML version for phone
                            if '2103884155' in body:
                                print("\n✅ PHONE NUMBER FOUND IN HTML: 2103884155")
                else:
                    body = msg.get_payload(decode=True)
                    if body:
                        body = body.decode('utf-8', errors='ignore')
                        print(body)
                        
                        if '2103884155' in body:
                            print("\n✅ PHONE NUMBER FOUND: 2103884155")
                        else:
                            print("\n⚠️  Phone number NOT found")
        
        mail.close()
        mail.logout()
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_zelle_email_detail()
