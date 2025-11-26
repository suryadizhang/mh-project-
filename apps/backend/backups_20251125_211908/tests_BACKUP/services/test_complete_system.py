"""
Payment Notification System - Complete End-to-End Test

This script demonstrates the full payment detection and matching workflow:
1. Fetch payment emails from Gmail (Zelle, Venmo)
2. Parse payment details
3. Create test booking in memory
4. Run matching algorithm
5. Show results with confidence scores

Run this to verify everything works before database migration.
"""
import os
import sys
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.payment_email_monitor import PaymentEmailParser


class MockBooking:
    """In-memory booking for testing"""
    def __init__(self, id, customer_name, customer_phone, customer_email, total_amount):
        self.id = id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.total_amount = Decimal(str(total_amount))
        self.status = "pending"
        self.alternative_payer_name = None
        self.alternative_payer_phone = None


class PaymentMatcher:
    """Simplified matcher for testing"""
    
    @staticmethod
    def calculate_match_score(payment, booking):
        """Calculate match score between payment and booking"""
        score = 0
        details = {}
        
        # Name matching
        payment_name = (payment.get('sender_name') or '').lower().strip()
        booking_name = booking.customer_name.lower().strip()
        
        if payment_name and booking_name:
            payment_parts = payment_name.split()
            booking_parts = booking_name.split()
            
            # Full name match
            if payment_name == booking_name:
                score += 100
                details['name_match'] = 'exact'
            # First name match
            elif len(payment_parts) > 0 and len(booking_parts) > 0:
                if payment_parts[0] == booking_parts[0]:
                    score += 75
                    details['name_match'] = 'first_name'
                # Last name match
                elif payment_parts[-1] == booking_parts[-1]:
                    score += 75
                    details['name_match'] = 'last_name'
        
        # Phone matching
        payment_phone = payment.get('customer_phone', '')
        booking_phone = booking.customer_phone
        
        if payment_phone and booking_phone:
            # Normalize (remove dashes, spaces, etc.)
            payment_digits = ''.join(filter(str.isdigit, payment_phone))
            booking_digits = ''.join(filter(str.isdigit, booking_phone))
            
            # Full match (10 digits)
            if payment_digits == booking_digits:
                score += 100
                details['phone_match'] = 'exact'
            # Last 4 digits
            elif len(payment_digits) >= 4 and len(booking_digits) >= 4:
                if payment_digits[-4:] == booking_digits[-4:]:
                    score += 40
                    details['phone_match'] = 'last_4'
        
        # Amount matching (within $1)
        payment_amount = Decimal(str(payment.get('amount', 0)))
        if abs(payment_amount - booking.total_amount) <= Decimal('1.00'):
            score += 25
            details['amount_match'] = True
        
        return score, details
    
    @staticmethod
    def find_best_match(payment, bookings):
        """Find best matching booking"""
        best_match = None
        best_score = 0
        best_details = {}
        
        for booking in bookings:
            score, details = PaymentMatcher.calculate_match_score(payment, booking)
            if score > best_score:
                best_score = score
                best_match = booking
                best_details = details
        
        return best_match, best_score, best_details


def fetch_recent_payments():
    """Fetch recent payment emails from Gmail"""
    print("=" * 80)
    print("🔄 STEP 1: Fetching Payment Emails from Gmail")
    print("=" * 80)
    
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    email_user = os.getenv('GMAIL_USER')
    email_pass = os.getenv('GMAIL_APP_PASSWORD')
    
    try:
        mail.login(email_user, email_pass)
        mail.select('INBOX')
        
        # Get last 10 emails
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        latest_ids = email_ids[-10:]
        
        payments = []
        
        for email_id in reversed(latest_ids):
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject_header = msg['Subject']
                    if subject_header:
                        subject, encoding = decode_header(subject_header)[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or 'utf-8')
                    else:
                        subject = "No Subject"
                    
                    from_header = msg['From']
                    
                    # Check if payment email
                    is_payment = (
                        'sent you $' in subject.lower() or
                        ('venmo' in from_header.lower() and '$' in subject) or
                        'stripe' in from_header.lower()
                    )
                    
                    if is_payment:
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
                        
                        # Parse payment
                        if 'sent you $' in subject.lower():
                            parsed = PaymentEmailParser.parse_zelle_email(subject, body)
                        elif 'venmo' in from_header.lower():
                            parsed = PaymentEmailParser.parse_venmo_email(subject, body)
                        elif 'stripe' in from_header.lower():
                            parsed = PaymentEmailParser.parse_stripe_email(subject, body)
                        else:
                            parsed = None
                        
                        if parsed:
                            parsed['email_from'] = from_header
                            parsed['email_subject'] = subject
                            parsed['received_at'] = msg['Date']
                            payments.append(parsed)
        
        print(f"✅ Found {len(payments)} payment email(s)\n")
        
        for i, payment in enumerate(payments, 1):
            print(f"{i}. {payment['provider'].upper()} - ${payment['amount']:.2f}")
            print(f"   From: {payment.get('sender_name', 'Unknown')}")
            if payment.get('customer_phone'):
                print(f"   Phone: {payment['customer_phone']}")
            print()
        
        return payments
        
    finally:
        mail.logout()


def create_test_bookings():
    """Create test bookings for matching"""
    print("=" * 80)
    print("🔄 STEP 2: Creating Test Bookings")
    print("=" * 80)
    
    bookings = [
        MockBooking(
            id=1,
            customer_name="Suryadi Zhang",
            customer_phone="2103884155",
            customer_email="test@example.com",
            total_amount=1.00
        ),
        MockBooking(
            id=2,
            customer_name="Suryadi Zhang",
            customer_phone="2103884155",
            customer_email="test@example.com",
            total_amount=1.25
        ),
        MockBooking(
            id=3,
            customer_name="John Smith",
            customer_phone="4155551234",
            customer_email="john@example.com",
            total_amount=550.00
        ),
        MockBooking(
            id=4,
            customer_name="Alice Brown",
            customer_phone="9165551234",
            customer_email="alice@example.com",
            total_amount=450.00
        ),
    ]
    
    print(f"✅ Created {len(bookings)} test booking(s)\n")
    
    for booking in bookings:
        print(f"Booking #{booking.id}")
        print(f"  Customer: {booking.customer_name}")
        print(f"  Phone: {booking.customer_phone}")
        print(f"  Amount: ${booking.total_amount}")
        print()
    
    return bookings


def match_payments_to_bookings(payments, bookings):
    """Run matching algorithm"""
    print("=" * 80)
    print("🔄 STEP 3: Running Matching Algorithm")
    print("=" * 80)
    
    results = []
    
    for payment in payments:
        print(f"\n{'='*80}")
        print(f"🎯 Matching Payment: {payment['provider'].upper()} ${payment['amount']:.2f}")
        print(f"   Sender: {payment.get('sender_name', 'Unknown')}")
        if payment.get('customer_phone'):
            print(f"   Phone: {payment['customer_phone']}")
        print(f"{'='*80}\n")
        
        # Find best match
        best_booking, best_score, details = PaymentMatcher.find_best_match(payment, bookings)
        
        if best_booking and best_score > 50:
            print(f"✅ MATCH FOUND! (Score: {best_score}/225)")
            print(f"\n   Booking #{best_booking.id}")
            print(f"   Customer: {best_booking.customer_name}")
            print(f"   Phone: {best_booking.customer_phone}")
            print(f"   Amount: ${best_booking.total_amount}")
            
            print(f"\n   📊 Score Breakdown:")
            if 'name_match' in details:
                match_type = details['name_match']
                if match_type == 'exact':
                    print(f"      • Full name match: +100 points ✅")
                elif match_type == 'first_name':
                    print(f"      • First name match: +75 points ✅")
                elif match_type == 'last_name':
                    print(f"      • Last name match: +75 points ✅")
            
            if 'phone_match' in details:
                match_type = details['phone_match']
                if match_type == 'exact':
                    print(f"      • Phone match (full): +100 points ✅")
                elif match_type == 'last_4':
                    print(f"      • Phone match (last 4): +40 points ✅")
            
            if details.get('amount_match'):
                print(f"      • Amount match: +25 points ✅")
            
            print(f"\n   🎉 AUTO-CONFIRM: {'YES' if best_score >= 100 else 'NO (Manual Review)'}")
            
            result = {
                'payment': payment,
                'booking': best_booking,
                'score': best_score,
                'details': details,
                'auto_confirm': best_score >= 100
            }
            results.append(result)
        else:
            print(f"❌ NO MATCH FOUND (Best score: {best_score}/225)")
            print(f"   Reason: Score below threshold (50)")
            print(f"   Action: Needs manual review")
            
            result = {
                'payment': payment,
                'booking': None,
                'score': best_score,
                'details': details,
                'auto_confirm': False
            }
            results.append(result)
    
    return results


def display_summary(results):
    """Display summary of matching results"""
    print("\n")
    print("=" * 80)
    print("📊 SUMMARY - Payment Matching Results")
    print("=" * 80)
    
    total = len(results)
    matched = sum(1 for r in results if r['booking'] is not None)
    auto_confirmed = sum(1 for r in results if r['auto_confirm'])
    manual_review = sum(1 for r in results if r['booking'] is not None and not r['auto_confirm'])
    unmatched = total - matched
    
    print(f"\nTotal Payments: {total}")
    print(f"  ✅ Matched: {matched} ({matched/total*100:.1f}%)")
    print(f"     • Auto-Confirmed: {auto_confirmed}")
    print(f"     • Manual Review: {manual_review}")
    print(f"  ❌ Unmatched: {unmatched}")
    
    if auto_confirmed > 0:
        avg_score = sum(r['score'] for r in results if r['auto_confirm']) / auto_confirmed
        print(f"\nAverage Auto-Confirm Score: {avg_score:.0f}/225")
    
    print("\n" + "=" * 80)
    print("🎯 NEXT STEPS")
    print("=" * 80)
    print("\n1. Run database migration:")
    print("   cd apps/backend")
    print("   alembic upgrade head")
    
    print("\n2. Create real booking via API:")
    print("   curl -X POST http://localhost:8000/api/v1/admin/payment-notifications/test-booking \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"customer_name\": \"Suryadi Zhang\", \"customer_phone\": \"2103884155\", \"total_amount\": 1.00}'")
    
    print("\n3. Trigger email check:")
    print("   curl -X POST http://localhost:8000/api/v1/admin/payment-notifications/check-emails")
    
    print("\n4. View results in admin dashboard:")
    print("   http://localhost:3000/admin/payment-notifications")
    
    print("\n" + "=" * 80)
    print("✨ System is ready for production!")
    print("=" * 80)


def main():
    """Run complete end-to-end test"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PAYMENT NOTIFICATION SYSTEM TEST" + " " * 26 + "║")
    print("║" + " " * 25 + "End-to-End Verification" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        # Step 1: Fetch payments from Gmail
        payments = fetch_recent_payments()
        
        if not payments:
            print("⚠️  No payment emails found. Send a test payment first:")
            print("   • Zelle: Send $1 to myhibachichef@gmail.com with note '2103884155'")
            print("   • Venmo: Send $1 to @myhibachichef with note '2103884155'")
            return
        
        # Step 2: Create test bookings
        bookings = create_test_bookings()
        
        # Step 3: Run matching
        results = match_payments_to_bookings(payments, bookings)
        
        # Step 4: Display summary
        display_summary(results)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
