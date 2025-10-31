"""
Check for recent emails in Gmail inbox (including Zelle payment)
"""
import os
import sys
import email
from datetime import datetime, timedelta
from dotenv import load_dotenv
import imaplib

load_dotenv()

def check_recent_emails():
    """Check for all recent emails, especially Zelle"""
    
    print("=" * 60)
    print("Checking Gmail Inbox for Recent Emails")
    print("=" * 60)
    
    email_addr = os.getenv('GMAIL_USER', 'myhibachichef@gmail.com')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    print(f"\n📧 Connecting to {email_addr}...")
    
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(email_addr, password)
        print("✅ Connected successfully!\n")
        
        # Select inbox
        mail.select('INBOX')
        
        # Search for recent emails (last 1 day)
        print("🔍 Searching for emails from last 24 hours...\n")
        
        # Get all emails from today
        today = datetime.now().strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {today})')
        
        if status != 'OK':
            print(f"❌ Search failed: {status}")
            return
        
        email_ids = messages[0].split()
        print(f"📬 Found {len(email_ids)} email(s) from today\n")
        
        if not email_ids:
            print("No emails received today yet.")
            print("\n💡 Tips:")
            print("  1. Zelle emails can take 1-5 minutes to arrive")
            print("  2. Check if you sent to correct email: myhibachichef@gmail.com")
            print("  3. Check your sent items to confirm Zelle was sent")
            return
        
        # Fetch and display last 10 emails
        print("Recent emails:")
        print("-" * 60)
        
        for email_id in email_ids[-10:]:  # Last 10 emails
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject = msg.get('Subject', 'No Subject')
                    from_addr = msg.get('From', 'Unknown')
                    date = msg.get('Date', 'Unknown')
                    
                    # Decode if needed
                    if subject:
                        subject = str(subject)[:70]
                    
                    print(f"\n📧 Email #{email_id.decode()}")
                    print(f"   From: {from_addr[:50]}")
                    print(f"   Subject: {subject}")
                    print(f"   Date: {date[:40]}")
                    
                    # Check if it's a Zelle email
                    from_lower = from_addr.lower()
                    subject_lower = subject.lower()
                    
                    if 'zelle' in from_lower or 'zelle' in subject_lower:
                        print("   🎯 **ZELLE PAYMENT EMAIL!**")
                        
                        # Try to get body
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    # Look for amount and phone
                                    if '2103884155' in body:
                                        print("   ✅ Contains phone number: 2103884155")
                                    if '$1' in body or '$1.' in body:
                                        print("   ✅ Contains amount: $1.00")
                                    break
                        else:
                            body = msg.get_payload(decode=True)
                            if body:
                                body = body.decode('utf-8', errors='ignore')
                                if '2103884155' in body:
                                    print("   ✅ Contains phone number: 2103884155")
                                if '$1' in body or '$1.' in body:
                                    print("   ✅ Contains amount: $1.00")
        
        mail.close()
        mail.logout()
        
        print("\n" + "=" * 60)
        print("✅ Check Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_emails()
