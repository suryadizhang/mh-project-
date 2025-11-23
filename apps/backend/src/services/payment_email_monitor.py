"""
Payment Notification Email Reader Service

Monitors myhibachichef@gmail.com for incoming payment confirmations from:
- Stripe (payment_intent.succeeded)
- Venmo (You received $X from...)
- Bank of America (Payment received...)
- Zelle (You received $X via Zelle...)

Automatically parses and updates payment/booking status in the database.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import email
from email.header import decode_header
import imaplib
import logging
import re

logger = logging.getLogger(__name__)


class PaymentEmailParser:
    """Parse payment confirmation emails from different providers"""

    # Email patterns for different payment providers
    PATTERNS = {
        "stripe": {
            "subject": r"payment.*(?:received|succeeded|confirmed)",
            "amount": r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            "transaction_id": r"(?:payment[_ ]intent|transaction[_ ]id)[:\s]+([a-zA-Z0-9_-]+)",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        },
        "venmo": {
            "subject": r"you.*received.*\$",
            "from": r"venmo",
            "amount": r"received\s+\$(\d+(?:\.\d{2})?)",
            "username": r"from\s+(@[\w-]+)",
            "phone": r"\b(\d{10})\b",  # Match 10-digit phone number
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        },
        "zelle": {
            "subject": r"you.*received.*via.*zelle",
            "from": r"zelle|alerts@",
            "amount": r"received\s+\$(\d+(?:,\d{3})*(?:\.\d{2})?)",
            "sender": r"from\s+([\w\s]+?)(?:\s|$)",
            "phone": r"\b(\d{10})\b",  # Match 10-digit phone number
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        },
        "bank_of_america": {
            "subject": r"payment.*received|deposit.*made",
            "from": r"bankofamerica|alerts@bofa",
            "amount": r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)",
            "type": r"(Zelle|ACH|Wire|Transfer)",
            "phone": r"\b(\d{10})\b",  # Match 10-digit phone number
        },
    }

    @staticmethod
    def clean_amount(amount_str: str) -> Decimal:
        """Convert amount string to Decimal, removing commas"""
        cleaned = amount_str.replace(",", "").replace("$", "").strip()
        return Decimal(cleaned)

    @staticmethod
    def parse_stripe_email(subject: str, body: str) -> dict | None:
        """Parse Stripe payment confirmation email"""
        try:
            # Extract amount
            amount_match = re.search(
                PaymentEmailParser.PATTERNS["stripe"]["amount"], body, re.IGNORECASE
            )
            if not amount_match:
                return None

            # Extract transaction ID
            tx_match = re.search(
                PaymentEmailParser.PATTERNS["stripe"]["transaction_id"], body, re.IGNORECASE
            )

            # Extract customer email from body
            email_match = re.search(
                PaymentEmailParser.PATTERNS["stripe"]["email"], body, re.IGNORECASE
            )

            return {
                "provider": "stripe",
                "amount": PaymentEmailParser.clean_amount(amount_match.group(1)),
                "transaction_id": tx_match.group(1) if tx_match else None,
                "customer_email": email_match.group(0) if email_match else None,
                "customer_phone": None,  # Stripe doesn't include phone in emails
                "status": "confirmed",
                "parsed_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.exception(f"Error parsing Stripe email: {e}")
            return None

    @staticmethod
    def parse_venmo_email(subject: str, body: str) -> dict | None:
        """
        Parse Venmo payment notification email

        Subject format: "Suryadi Zhang paid you $1.25"
        Body: HTML email with payment details and optional phone/note
        """
        try:
            # Extract amount from subject first (more reliable than HTML body)
            # Subject: "Suryadi Zhang paid you $1.25"
            subject_amount = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", subject)
            amount_match = subject_amount

            if not amount_match:
                # Fallback to body if subject doesn't have amount
                amount_match = re.search(
                    PaymentEmailParser.PATTERNS["venmo"]["amount"], body, re.IGNORECASE
                )
                if not amount_match:
                    logger.warning("Could not extract amount from Venmo email")
                    return None

            # Extract sender name from subject
            # Pattern: "Name paid you $X.XX"
            sender_from_subject = re.search(r"^(.+?)\s+paid\s+you\s+\$", subject, re.IGNORECASE)

            # Strip HTML tags from body for better text extraction
            body_text = re.sub(r"<[^>]+>", " ", body)
            body_text = re.sub(r"\s+", " ", body_text).strip()

            # Extract username from body (Venmo specific)
            username_match = re.search(
                PaymentEmailParser.PATTERNS["venmo"]["username"], body_text, re.IGNORECASE
            )
            if not username_match:
                # Try alternate pattern: @username
                username_match = re.search(r"@([\w-]+)", body_text)

            # Sender name: prioritize subject, fallback to body
            sender_name = None
            if sender_from_subject:
                sender_name = sender_from_subject.group(1).strip()
            else:
                # Try to extract from body
                sender_body = re.search(
                    r"(?:from|by)\s+([\w\s]+?)\s+(?:sent|@|paid)", body_text, re.IGNORECASE
                )
                if sender_body:
                    sender_name = sender_body.group(1).strip()

            # Extract customer phone number (10 digits) from payment note/message
            # Look for patterns like: "Note: 2103884155" or "Message: 2103884155"
            phone_match = re.search(
                r"(?:note|message|memo)[\s:]+(\d{10})", body_text, re.IGNORECASE
            )
            if not phone_match:
                # Fallback: any 10-digit number in the body
                phone_match = re.search(r"\b(\d{10})\b", body_text)

            # Extract customer email from body/note
            email_match = re.search(
                PaymentEmailParser.PATTERNS["venmo"]["email"], body_text, re.IGNORECASE
            )

            result = {
                "provider": "venmo",
                "amount": PaymentEmailParser.clean_amount(amount_match.group(1)),
                "sender_username": username_match.group(1) if username_match else None,
                "sender_name": sender_name,
                "customer_phone": (
                    phone_match.group(1) if phone_match else None
                ),  # Customer's phone from note
                "customer_email": email_match.group(0) if email_match else None,
                "status": "pending",  # Venmo requires manual confirmation
                "parsed_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Parsed Venmo email: amount=${result['amount']}, sender={result['sender_name']}, username={result.get('sender_username', 'N/A')}, phone={result.get('customer_phone', 'N/A')}, email={result.get('customer_email', 'N/A')}"
            )
            return result

        except Exception as e:
            logger.exception(f"Error parsing Venmo email: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def parse_zelle_email(subject: str, body: str) -> dict | None:
        """
        Parse Zelle payment notification email (often from Bank of America)

        Subject format: "Suryadi Zhang sent you $1.00"
        Body: HTML email with payment details and optional phone/note
        """
        try:
            # Extract amount from subject first (more reliable)
            subject_amount = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", subject)

            # Extract sender name from subject (e.g., "John Smith sent you $50")
            sender_from_subject = re.search(r"^(.+?)\s+sent\s+you\s+\$", subject, re.IGNORECASE)

            # Strip HTML tags from body for better parsing
            body_text = re.sub(r"<[^>]+>", " ", body)
            body_text = re.sub(r"\s+", " ", body_text).strip()

            # Try to extract amount from body if not in subject
            body_amount = re.search(
                PaymentEmailParser.PATTERNS["zelle"]["amount"], body_text, re.IGNORECASE
            )

            amount_match = subject_amount or body_amount
            if not amount_match:
                logger.warning("Could not extract amount from Zelle email")
                return None

            # Sender name: prioritize subject, fallback to body
            sender_name = None
            if sender_from_subject:
                sender_name = sender_from_subject.group(1).strip()
            else:
                # Try to extract from body
                sender_body = re.search(
                    PaymentEmailParser.PATTERNS["zelle"]["sender"], body_text, re.IGNORECASE
                )
                if sender_body:
                    sender_name = sender_body.group(1).strip()

            # Extract sender email (if available)
            email_match = re.search(
                PaymentEmailParser.PATTERNS["zelle"]["email"], body_text, re.IGNORECASE
            )

            # Extract customer phone number (10 digits) from payment memo/note
            # Look for patterns like: "Memo: 2103884155" or "Note: 2103884155 ady"
            phone_match = re.search(
                r"(?:memo|note|message)[\s:]+(\d{10})", body_text, re.IGNORECASE
            )
            if not phone_match:
                # Fallback: any 10-digit number in the body
                phone_match = re.search(r"\b(\d{10})\b", body_text)

            result = {
                "provider": "zelle",
                "amount": PaymentEmailParser.clean_amount(amount_match.group(1)),
                "sender_name": sender_name,
                "sender_email": email_match.group(0) if email_match else None,
                "customer_phone": (
                    phone_match.group(1) if phone_match else None
                ),  # Customer's phone from memo
                "customer_email": email_match.group(0) if email_match else None,  # Use sender email as customer email
                "status": "pending",  # Zelle requires manual confirmation
                "parsed_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Parsed Zelle email: amount=${result['amount']}, sender={result['sender_name']}, phone={result.get('customer_phone', 'N/A')}, email={result.get('customer_email', 'N/A')}"
            )
            return result

        except Exception as e:
            logger.exception(f"Error parsing Zelle email: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def parse_bofa_email(subject: str, body: str) -> dict | None:
        """Parse Bank of America payment notification email"""
        try:
            # Extract amount
            amount_match = re.search(
                PaymentEmailParser.PATTERNS["bank_of_america"]["amount"], body, re.IGNORECASE
            )
            if not amount_match:
                return None

            # Extract payment type
            type_match = re.search(
                PaymentEmailParser.PATTERNS["bank_of_america"]["type"], body, re.IGNORECASE
            )

            return {
                "provider": "bank_of_america",
                "amount": PaymentEmailParser.clean_amount(amount_match.group(1)),
                "payment_type": type_match.group(1) if type_match else "Unknown",
                "status": "confirmed",
                "parsed_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.exception(f"Error parsing Bank of America email: {e}")
            return None

    @staticmethod
    def detect_and_parse(subject: str, from_email: str, body: str) -> dict | None:
        """
        Detect provider and parse email automatically

        Recognizes:
        - Stripe: from stripe.com
        - Venmo: from venmo.com (official Venmo emails)
        - Zelle: from Bank of America or other banks (Zelle network)
        - Bank of America: Direct BofA payments (non-Zelle)
        """
        subject_lower = subject.lower()
        from_lower = from_email.lower()

        # Stripe
        if "stripe" in from_lower or re.search(
            PaymentEmailParser.PATTERNS["stripe"]["subject"], subject_lower
        ):
            return PaymentEmailParser.parse_stripe_email(subject, body)

        # Venmo (only from official venmo.com emails)
        if "venmo" in from_lower:
            return PaymentEmailParser.parse_venmo_email(subject, body)

        # Zelle payments (can come from any bank)
        # Common pattern: "John Smith sent you $X.XX" in subject
        if "sent you $" in subject_lower:
            # This is almost always a Zelle payment
            return PaymentEmailParser.parse_zelle_email(subject, body)

        # Also check for explicit "zelle" mention
        if "zelle" in from_lower or "zelle" in subject_lower:
            return PaymentEmailParser.parse_zelle_email(subject, body)

        # Bank of America (non-Zelle payments: deposits, transfers)
        if (
            "bankofamerica" in from_lower
            or "bofa" in from_lower
            or "ealerts.bankofamerica" in from_lower
        ):
            if re.search(PaymentEmailParser.PATTERNS["bank_of_america"]["subject"], subject_lower):
                return PaymentEmailParser.parse_bofa_email(subject, body)

        return None


class PaymentEmailMonitor:
    """Monitor Gmail inbox for payment notification emails"""

    MINIMUM_DEPOSIT = Decimal("100.00")  # $100 minimum deposit to lock booking date

    def __init__(self, email_address: str, app_password: str, db_session=None):
        """
        Initialize email monitor

        Args:
            email_address: Gmail address (myhibachichef@gmail.com)
            app_password: Gmail App Password (16-char code without spaces)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.mail = None
        self.db_session = db_session

    def connect(self) -> bool:
        """Connect to Gmail IMAP server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.app_password)
            logger.info(f"✅ Connected to Gmail IMAP for {self.email_address}")
            return True
        except Exception as e:
            logger.exception(f"❌ Failed to connect to Gmail IMAP: {e}")
            return False

    def disconnect(self):
        """Disconnect from Gmail IMAP server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("✅ Disconnected from Gmail IMAP")
            except Exception as e:
                logger.exception(f"Error disconnecting: {e}")

    def find_booking_by_contact_info(self, phone: str | None, email: str | None) -> dict | None:
        """
        Look up booking by customer phone or email.

        Args:
            phone: Customer phone number (10 digits)
            email: Customer email address

        Returns:
            Dict with booking info including: id, total_amount, amount_paid, amount_remaining, is_deposit_met
            None if no booking found
        """
        if not self.db_session:
            logger.error("Database session not available for booking lookup")
            return None

        if not phone and not email:
            logger.warning("No phone or email provided for booking lookup")
            return None

        try:
            from models.booking import Booking, BookingStatus
            from sqlalchemy import or_, func

            # Build query to search by phone or email
            query = self.db_session.query(Booking).filter(
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            )

            conditions = []
            if phone:
                # Normalize phone: remove non-digits, ensure 10 digits
                clean_phone = ''.join(filter(str.isdigit, phone))
                # Remove country code if present (11 digits starting with 1)
                if len(clean_phone) == 11 and clean_phone[0] == '1':
                    clean_phone = clean_phone[1:]
                # Match exact 10 digits (booking phones are stored as 10 digits)
                if len(clean_phone) == 10:
                    conditions.append(Booking.contact_phone == clean_phone)

            if email:
                conditions.append(func.lower(Booking.contact_email) == email.lower())

            if conditions:
                query = query.filter(or_(*conditions))

            # Get most recent booking
            booking = query.order_by(Booking.created_at.desc()).first()

            if not booking:
                logger.info(f"No active booking found for phone={phone}, email={email}")
                return None

            # Calculate payment totals
            from models.legacy_core import CorePayment
            payments = self.db_session.query(Payment).filter(
                Payment.booking_id == booking.id,
                Payment.status == "completed"
            ).all()

            amount_paid = sum(p.amount for p in payments)

            # Calculate total amount (assuming $55/adult pricing logic exists in booking)
            # For now, use a placeholder - should integrate with booking_service pricing
            total_amount = Decimal("550.00")  # Minimum booking amount
            if hasattr(booking, 'total_amount') and booking.total_amount:
                total_amount = booking.total_amount

            amount_remaining = total_amount - amount_paid
            is_deposit_met = amount_paid >= self.MINIMUM_DEPOSIT

            return {
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "booking_datetime": booking.booking_datetime,
                "party_size": booking.party_size,
                "status": booking.status.value,
                "total_amount": total_amount,
                "amount_paid": amount_paid,
                "amount_remaining": amount_remaining,
                "is_deposit_met": is_deposit_met,
                "deposit_required": self.MINIMUM_DEPOSIT,
                "contact_phone": booking.contact_phone,
                "contact_email": booking.contact_email,
            }

        except Exception as e:
            logger.exception(f"Error looking up booking: {e}")
            return None

    def validate_payment_amount(self, payment_data: dict, booking_info: dict) -> dict:
        """
        Validate payment amount against booking requirements.

        Args:
            payment_data: Parsed payment data with 'amount'
            booking_info: Booking data from find_booking_by_contact_info()

        Returns:
            Dict with validation results:
            - is_valid: Whether payment is acceptable
            - meets_deposit: Whether $100 minimum deposit is met with this payment
            - new_amount_paid: Total after this payment
            - amount_remaining: Remaining balance after payment
            - message: Human-readable status message
        """
        payment_amount = payment_data.get("amount", Decimal("0"))
        current_paid = booking_info.get("amount_paid", Decimal("0"))
        total_required = booking_info.get("total_amount", Decimal("550.00"))

        new_amount_paid = current_paid + payment_amount
        amount_remaining = total_required - new_amount_paid

        # Check if this payment meets the minimum deposit
        was_deposit_met = booking_info.get("is_deposit_met", False)
        meets_deposit_now = new_amount_paid >= self.MINIMUM_DEPOSIT

        # Determine validity
        is_valid = True
        if payment_amount <= 0:
            is_valid = False
            message = "Invalid payment amount"
        elif new_amount_paid > total_required:
            is_valid = False
            message = f"Overpayment: ${payment_amount} exceeds remaining ${booking_info['amount_remaining']}"
        elif not was_deposit_met and meets_deposit_now:
            message = f"✅ Deposit met! ${new_amount_paid} paid, ${amount_remaining} remaining. Booking date is LOCKED."
        elif not meets_deposit_now:
            shortage = self.MINIMUM_DEPOSIT - new_amount_paid
            message = f"⚠️ Partial payment received: ${payment_amount}. Need ${shortage} more to meet $100 deposit and lock booking date."
        elif amount_remaining <= 0:
            message = f"✅ Booking fully paid! ${new_amount_paid} total."
        else:
            message = f"✅ Payment received: ${payment_amount}. ${amount_remaining} remaining balance."

        return {
            "is_valid": is_valid,
            "meets_deposit": meets_deposit_now,
            "deposit_was_met": was_deposit_met,
            "deposit_met_by_this_payment": meets_deposit_now and not was_deposit_met,
            "payment_amount": payment_amount,
            "new_amount_paid": new_amount_paid,
            "amount_remaining": max(Decimal("0"), amount_remaining),
            "total_required": total_required,
            "message": message,
        }

    def get_unread_payment_emails(
        self, since_date: datetime | None = None, limit: int = 50
    ) -> list[dict]:
        """
        Fetch unread payment notification emails

        Args:
            since_date: Only fetch emails since this date (default: last 7 days)
            limit: Maximum number of emails to fetch

        Returns:
            List of parsed payment notifications
        """
        if not self.mail and not self.connect():
            return []

        try:
            # Select inbox
            self.mail.select("INBOX")

            # Build search criteria
            if since_date is None:
                since_date = datetime.now(timezone.utc) - timedelta(days=7)

            date_str = since_date.strftime("%d-%b-%Y")

            # Search for unread emails from payment providers
            # IMAP search format: each criterion must be properly formatted
            search_criteria = [
                "UNSEEN",  # Unread emails
                f'SINCE {date_str}',  # Since date
                "OR", "OR", "OR", "OR",  # Chain OR for multiple FROM
                'FROM "stripe"',
                'FROM "venmo"',
                'FROM "zelle"',
                'FROM "alerts@"',
                'FROM "bankofamerica"'
            ]

            _, message_numbers = self.mail.search(None, " ".join(search_criteria))

            email_ids = message_numbers[0].split()
            if not email_ids:
                logger.info("No new payment notification emails found")
                return []

            # Limit number of emails
            email_ids = email_ids[-limit:]

            parsed_emails = []

            for email_id in email_ids:
                try:
                    _, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Decode subject
                    subject, encoding = decode_header(email_message["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    from_email = email_message.get("From", "")

                    # Extract body
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(
                                    "utf-8", errors="ignore"
                                )
                                break
                    else:
                        body = email_message.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )

                    # Parse email
                    parsed = PaymentEmailParser.detect_and_parse(subject, from_email, body)

                    if parsed:
                        parsed["email_id"] = email_id.decode()
                        parsed["subject"] = subject
                        parsed["from"] = from_email
                        parsed["received_at"] = email_message.get("Date")
                        parsed_emails.append(parsed)

                        logger.info(
                            f"✅ Parsed payment email: {parsed['provider']} - ${parsed['amount']}"
                        )

                except Exception as e:
                    logger.exception(f"Error processing email {email_id}: {e}")
                    continue

            return parsed_emails

        except Exception as e:
            logger.exception(f"Error fetching emails: {e}")
            return []

    def mark_as_read(self, email_id: str):
        """Mark email as read"""
        try:
            self.mail.store(email_id.encode(), "+FLAGS", "\\Seen")
            logger.info(f"Marked email {email_id} as read")
        except Exception as e:
            logger.exception(f"Error marking email as read: {e}")


# Example usage
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()

    # Initialize monitor
    monitor = PaymentEmailMonitor(
        email_address=os.getenv("GMAIL_USER", "myhibachichef@gmail.com"),
        app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
    )

    # Fetch unread payment emails
    payment_notifications = monitor.get_unread_payment_emails()

    for _notification in payment_notifications:
        pass

    monitor.disconnect()
