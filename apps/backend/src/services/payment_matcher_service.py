"""
Payment Matching Service

Automatically matches payment notification emails to pending bookings/payments.
Updates payment status and sends confirmation notifications.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging

from models.booking import Booking, Payment, PaymentStatus
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.payment_email_monitor import PaymentEmailMonitor
from services.unified_notification_service import notify_payment
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PaymentMatcher:
    """Match payment notifications to pending bookings"""

    # Tolerance for amount matching (e.g., $550.00 ± $1.00)
    AMOUNT_TOLERANCE = Decimal("1.00")

    # Expanded tolerance for friend/family payments with tips ($550 ± $60 to catch $500 base + varying tips)
    EXPANDED_AMOUNT_TOLERANCE = Decimal("60.00")

    # Time window for matching payments (e.g., within 24 hours)
    TIME_WINDOW_HOURS = 24

    # Extended time window for friend/family payments (e.g., within 72 hours)
    EXTENDED_TIME_WINDOW_HOURS = 72

    @staticmethod
    def find_matching_payment(
        db: Session,
        amount: Decimal,
        payment_method: str,
        received_at: datetime | None = None,
        sender_info: dict | None = None,
        use_fuzzy_matching: bool = False,
    ) -> Payment | None:
        """
        Find pending payment matching the notification

        Enhanced matching logic with phone number priority:
        1. **Phone match (Venmo/Zelle):** If customer phone in payment note → EXACT MATCH
        2. Exact match: Amount ±$1, same method, within 24 hours
        3. Fuzzy match: Amount ±$60, same method, within 72 hours (for friend/family)
        4. If multiple matches → pick closest booking by date/time

        Args:
            db: Database session
            amount: Payment amount from email
            payment_method: Payment method (stripe, venmo, zelle, plaid)
            received_at: When payment was received
            sender_info: Optional sender details (name, email, phone, username, **customer_phone**)
            use_fuzzy_matching: Enable expanded matching for friend/family payments

        Returns:
            Matching Payment record or None
        """
        try:
            # PRIORITY 1: Phone number matching (Venmo/Zelle)
            # If customer included their phone number in payment note, this is most reliable
            if sender_info and sender_info.get("customer_phone"):
                customer_phone = sender_info.get("customer_phone")
                phone_match = PaymentMatcher._find_by_phone_number(
                    db=db,
                    phone=customer_phone,
                    amount=amount,
                    payment_method=payment_method,
                    received_at=received_at,
                )
                if phone_match:
                    logger.info(
                        f"✅ PHONE MATCH: Found payment by customer phone {customer_phone[-4:]}: "
                        f"ID={phone_match.id}, Amount=${phone_match.total_amount}"
                    )
                    return phone_match

            # PRIORITY 2: Exact/Fuzzy amount matching
            # Calculate amount range
            tolerance = (
                PaymentMatcher.EXPANDED_AMOUNT_TOLERANCE
                if use_fuzzy_matching
                else PaymentMatcher.AMOUNT_TOLERANCE
            )
            min_amount = amount - tolerance
            max_amount = amount + tolerance

            # Calculate time window
            if received_at is None:
                received_at = datetime.now(timezone.utc)

            time_window = (
                PaymentMatcher.EXTENDED_TIME_WINDOW_HOURS
                if use_fuzzy_matching
                else PaymentMatcher.TIME_WINDOW_HOURS
            )
            time_start = received_at - timedelta(hours=time_window)
            time_end = received_at + timedelta(hours=1)  # Allow 1 hour future

            # Build base query
            query = (
                db.query(Payment)
                .filter(
                    and_(
                        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING]),
                        Payment.payment_method == payment_method,
                        Payment.total_amount >= min_amount,
                        Payment.total_amount <= max_amount,
                        Payment.created_at >= time_start,
                        Payment.created_at <= time_end,
                    )
                )
                .order_by(Payment.created_at.desc())
            )

            # Get all potential matches
            potential_matches = query.all()

            if not potential_matches:
                logger.warning(
                    f"❌ No matching payment found for: "
                    f"Amount=${amount}, Method={payment_method}, Time={received_at}"
                )
                return None

            # If only one match, return it
            if len(potential_matches) == 1:
                payment = potential_matches[0]
                logger.info(
                    f"✅ Found matching payment: ID={payment.id}, "
                    f"Amount=${payment.total_amount}, Method={payment.payment_method}"
                )
                return payment

            # Multiple matches - use sender info to find best match
            if sender_info:
                best_match = PaymentMatcher._find_best_match_by_sender(
                    potential_matches, sender_info, db
                )
                if best_match:
                    logger.info(
                        f"✅ Found best matching payment using sender info: ID={best_match.id}, "
                        f"Amount=${best_match.total_amount}, Method={best_match.payment_method}"
                    )
                    return best_match

            # No sender info or no match - return closest booking by date
            payment = PaymentMatcher._pick_closest_booking(potential_matches, received_at)
            logger.warning(
                f"⚠️ Multiple matches found, returning closest booking: ID={payment.id}, "
                f"Amount=${payment.total_amount}, Created={payment.created_at}"
            )
            return payment

        except Exception as e:
            logger.exception(f"Error finding matching payment: {e}")
            return None

    @staticmethod
    def _find_by_phone_number(
        db: Session,
        phone: str,
        amount: Decimal,
        payment_method: str,
        received_at: datetime | None = None,
    ) -> Payment | None:
        """
        Find payment by customer phone number (most reliable for Venmo/Zelle)

        Args:
            db: Database session
            phone: Customer's phone number (10 digits, e.g., "2103884155")
            amount: Payment amount
            payment_method: Payment method
            received_at: When payment was received

        Returns:
            Best matching Payment or None
        """
        try:
            # Normalize phone number (remove non-digits, take last 10 digits)
            normalized_phone = "".join(c for c in phone if c.isdigit())[-10:]

            if len(normalized_phone) != 10:
                logger.warning(f"Invalid phone number format: {phone}")
                return None

            # Calculate time window (extended for phone matching - 7 days)
            if received_at is None:
                received_at = datetime.now(timezone.utc)

            time_start = received_at - timedelta(days=7)
            time_end = received_at + timedelta(hours=1)

            # Find all pending payments with matching phone
            query = (
                db.query(Payment)
                .join(Booking)
                .filter(
                    and_(
                        Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING]),
                        Payment.payment_method == payment_method,
                        Payment.created_at >= time_start,
                        Payment.created_at <= time_end,
                        or_(
                            Booking.customer_phone.like(f"%{normalized_phone}"),
                            Booking.customer_phone.like(
                                f"%{normalized_phone[-4:]}%"
                            ),  # Match last 4 digits
                        ),
                    )
                )
                .order_by(Payment.created_at.desc())
            )

            matches = query.all()

            if not matches:
                return None

            # If single match, return it
            if len(matches) == 1:
                return matches[0]

            # Multiple matches - pick closest booking by date + best amount match
            best_match = None
            best_score = -1

            for payment in matches:
                # Score based on amount difference and time difference
                amount_diff = abs(float(payment.total_amount - amount))
                time_diff = abs((payment.created_at - received_at).total_seconds() / 3600)  # Hours

                # Lower is better (smaller diff = better match)
                # Weight amount more heavily (amount_diff * 10 + time_diff)
                score = 1000 - (amount_diff * 10 + time_diff)

                if score > best_score:
                    best_score = score
                    best_match = payment

            return best_match

        except Exception as e:
            logger.exception(f"Error finding payment by phone: {e}")
            return None

    @staticmethod
    def _pick_closest_booking(potential_matches: list[Payment], received_at: datetime) -> Payment:
        """
        Pick the closest booking by date/time when multiple matches exist

        Args:
            potential_matches: List of potential payment matches
            received_at: When payment was received

        Returns:
            Payment closest to received_at
        """
        closest_payment = None
        smallest_diff = None

        for payment in potential_matches:
            time_diff = abs((payment.created_at - received_at).total_seconds())

            if smallest_diff is None or time_diff < smallest_diff:
                smallest_diff = time_diff
                closest_payment = payment

        return closest_payment if closest_payment else potential_matches[0]

    @staticmethod
    def _find_best_match_by_sender(
        potential_matches: list[Payment], sender_info: dict, db: Session
    ) -> Payment | None:
        """
        Find best matching payment using sender information

        Matches sender name/email/phone against:
        1. Customer name in booking
        2. Customer email in booking
        3. Customer phone in booking
        4. Alternative contact info in booking metadata

        Args:
            potential_matches: List of potential payment matches
            sender_info: Sender details from email (name, email, phone, username)
            db: Database session

        Returns:
            Best matching Payment or None
        """
        sender_name = sender_info.get("sender_name", "").lower().strip()
        sender_email = sender_info.get("sender_email", "").lower().strip()
        sender_phone = sender_info.get("sender_phone", "").lower().strip()
        sender_username = sender_info.get("sender_username", "").lower().strip()

        scored_matches = []

        for payment in potential_matches:
            score = 0
            booking = payment.booking

            if not booking:
                continue

            # Match customer name (exact full name, first name, or last name)
            if sender_name and booking.customer_name:
                customer_name = booking.customer_name.lower().strip()
                sender_parts = [p.strip() for p in sender_name.split() if len(p) > 1]
                customer_parts = [p.strip() for p in customer_name.split() if len(p) > 1]

                # Exact full name match
                if sender_name == customer_name:
                    score += 100
                    logger.debug(f"✅ Exact full name match: '{sender_name}' = '{customer_name}'")

                # First name match (compare first word)
                elif sender_parts and customer_parts and sender_parts[0] == customer_parts[0]:
                    score += 75
                    logger.debug(
                        f"✅ First name match: '{sender_parts[0]}' = '{customer_parts[0]}'"
                    )

                # Last name match (compare last word)
                elif sender_parts and customer_parts and sender_parts[-1] == customer_parts[-1]:
                    score += 75
                    logger.debug(
                        f"✅ Last name match: '{sender_parts[-1]}' = '{customer_parts[-1]}'"
                    )

                # Partial match (any word in sender name matches any word in customer name)
                elif any(sp in customer_parts for sp in sender_parts if len(sp) > 2):
                    score += 50
                    logger.debug(
                        f"✅ Partial name match: sender={sender_parts}, customer={customer_parts}"
                    )

            # Match customer email
            if sender_email and booking.customer_email:
                if sender_email == booking.customer_email.lower():
                    score += 100
                    logger.debug(f"✅ Email match: '{sender_email}'")

            # Match customer phone (most reliable)
            if sender_phone and booking.customer_phone:
                # Normalize phone numbers (remove +1, spaces, dashes, parentheses)
                normalized_sender = "".join(c for c in sender_phone if c.isdigit())[-10:]
                normalized_customer = "".join(c for c in booking.customer_phone if c.isdigit())[
                    -10:
                ]
                if normalized_sender == normalized_customer:
                    score += 100
                    logger.debug(f"✅ Phone match: '{normalized_sender}' = '{normalized_customer}'")
                # Match last 4 digits (fallback)
                elif len(normalized_sender) >= 4 and len(normalized_customer) >= 4:
                    if normalized_sender[-4:] == normalized_customer[-4:]:
                        score += 40
                        logger.debug(f"✅ Last 4 digits match: '*{normalized_sender[-4:]}'")

            # Check booking metadata for friend/family info
            if booking.metadata:
                # Check alternative payer info
                alt_payer = booking.metadata.get("alternative_payer", {})
                if alt_payer:
                    # Alternative payer name match (first name, last name, or full name)
                    if sender_name and alt_payer.get("name"):
                        alt_name = alt_payer.get("name", "").lower().strip()
                        alt_parts = [p.strip() for p in alt_name.split() if len(p) > 1]

                        # Exact full name match
                        if sender_name == alt_name:
                            score += 150  # Higher score for explicit alternative payer
                            logger.debug(
                                f"✅ Alternative payer exact match: '{sender_name}' = '{alt_name}'"
                            )

                        # First name match
                        elif sender_parts and alt_parts and sender_parts[0] == alt_parts[0]:
                            score += 125
                            logger.debug(
                                f"✅ Alternative payer first name match: '{sender_parts[0]}'"
                            )

                        # Last name match
                        elif sender_parts and alt_parts and sender_parts[-1] == alt_parts[-1]:
                            score += 125
                            logger.debug(
                                f"✅ Alternative payer last name match: '{sender_parts[-1]}'"
                            )

                        # Partial match
                        elif any(sp in alt_parts for sp in sender_parts if len(sp) > 2):
                            score += 100
                            logger.debug("✅ Alternative payer partial name match")

                    # Alternative payer email match
                    if sender_email and alt_payer.get("email"):
                        if sender_email == alt_payer.get("email", "").lower():
                            score += 150
                            logger.debug(f"✅ Alternative payer email match: '{sender_email}'")

                    # Alternative payer phone match
                    if sender_phone and alt_payer.get("phone"):
                        normalized_alt = "".join(
                            c for c in alt_payer.get("phone", "") if c.isdigit()
                        )[-10:]
                        if normalized_sender == normalized_alt:
                            score += 150
                            logger.debug(f"✅ Alternative payer phone match: '{normalized_alt}'")

            # Match Venmo username if available
            if sender_username and booking.metadata:
                venmo_username = booking.metadata.get("venmo_username", "").lower()
                if sender_username == venmo_username:
                    score += 100

            # Amount exact match bonus
            if payment.total_amount == Decimal(str(sender_info.get("amount", 0))):
                score += 25

            scored_matches.append((payment, score))

        # Sort by score descending
        scored_matches.sort(key=lambda x: x[1], reverse=True)

        # Return best match if score is significant (> 50)
        if scored_matches and scored_matches[0][1] > 50:
            best_payment, best_score = scored_matches[0]
            logger.info(
                f"🎯 Best match found with confidence score {best_score}: "
                f"Payment ID={best_payment.id}, Booking ID={best_payment.booking.id}"
            )
            return best_payment

        return None

    @staticmethod
    def confirm_payment(
        db: Session,
        payment: Payment,
        notification_data: dict,
        email_service: EmailService | None = None,
        notify_service: NotificationService | None = None,
    ) -> bool:
        """
        Confirm payment and update booking status

        Args:
            db: Database session
            payment: Payment record to confirm
            notification_data: Parsed email notification data
            email_service: Email service for sending confirmations
            notify_service: Notification service for admin alerts

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.payment_confirmed_at = datetime.now(timezone.utc)

            # Add metadata
            if not payment.metadata:
                payment.metadata = {}

            payment.metadata["email_notification"] = {
                "provider": notification_data.get("provider"),
                "transaction_id": notification_data.get("transaction_id"),
                "received_at": notification_data.get("received_at"),
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Update booking status
            booking = payment.booking
            if booking:
                booking.payment_status = "paid"
                booking.updated_at = datetime.now(timezone.utc)

            db.commit()

            logger.info(
                f"✅ Payment confirmed: Payment ID={payment.id}, "
                f"Booking ID={booking.id if booking else 'N/A'}, "
                f"Amount=${payment.total_amount}"
            )

            # Send customer confirmation email
            if email_service and booking:
                try:
                    email_service.send_payment_confirmation(
                        to_email=booking.customer_email,
                        booking_id=booking.id,
                        amount=float(payment.total_amount),
                        payment_method=payment.payment_method,
                    )
                    logger.info(f"📧 Sent payment confirmation to {booking.customer_email}")
                except Exception as e:
                    logger.exception(f"Error sending confirmation email: {e}")

            # Send admin notification
            if notify_service:
                try:
                    notify_service.send_payment_received_notification(
                        payment_id=payment.id,
                        booking_id=booking.id if booking else None,
                        amount=float(payment.total_amount),
                        method=payment.payment_method,
                    )
                    logger.info(f"🔔 Sent admin notification for payment {payment.id}")
                except Exception as e:
                    logger.exception(f"Error sending admin notification: {e}")

            # Send WhatsApp notification (async, non-blocking)
            if booking and booking.customer_phone:
                try:
                    import asyncio

                    # Create task to send WhatsApp notification using unified service
                    asyncio.create_task(
                        notify_payment(
                            customer_name=booking.customer_name,
                            customer_phone=booking.customer_phone,
                            amount=float(payment.total_amount),
                            payment_method=payment.payment_method,
                            booking_id=str(booking.id),
                            balance_due=(
                                float(booking.balance_due_cents / 100.0)
                                if hasattr(booking, "balance_due_cents")
                                and booking.balance_due_cents
                                else 0.0
                            ),
                        )
                    )
                    logger.info(
                        f"📱 WhatsApp payment notification queued for {booking.customer_phone}"
                    )
                except Exception as e:
                    logger.exception(f"Error sending WhatsApp notification: {e}")
                    # Don't fail the payment confirmation if WhatsApp fails

            return True

        except Exception as e:
            db.rollback()
            logger.exception(f"Error confirming payment: {e}")
            return False


class PaymentEmailService:
    """
    Main service for monitoring and processing payment emails

    This service:
    1. Monitors Gmail inbox for payment notifications
    2. Parses payment details from emails
    3. Matches notifications to pending payments
    4. Auto-confirms payments and updates bookings
    5. Sends confirmation emails and admin notifications
    """

    def __init__(
        self,
        db: Session,
        email_monitor: PaymentEmailMonitor,
        email_service: EmailService | None = None,
        notify_service: NotificationService | None = None,
    ):
        """
        Initialize payment email service

        Args:
            db: Database session
            email_monitor: Email monitoring service
            email_service: Email service for confirmations
            notify_service: Notification service for admin alerts
        """
        self.db = db
        self.email_monitor = email_monitor
        self.email_service = email_service
        self.notify_service = notify_service

    def process_payment_emails(
        self,
        since_date: datetime | None = None,
        auto_confirm: bool = True,
        mark_as_read: bool = True,
    ) -> dict:
        """
        Process all unread payment notification emails

        Args:
            since_date: Only process emails since this date
            auto_confirm: Automatically confirm matched payments
            mark_as_read: Mark processed emails as read

        Returns:
            Summary of processing results
        """
        logger.info("🔍 Starting payment email processing...")

        results = {
            "emails_found": 0,
            "emails_parsed": 0,
            "payments_matched": 0,
            "payments_confirmed": 0,
            "errors": [],
        }

        try:
            # Fetch unread payment emails
            notifications = self.email_monitor.get_unread_payment_emails(since_date=since_date)
            results["emails_found"] = len(notifications)

            if not notifications:
                logger.info("No new payment emails to process")
                return results

            logger.info(f"📧 Found {len(notifications)} payment notification(s)")

            # Process each notification
            for notification in notifications:
                try:
                    results["emails_parsed"] += 1

                    # Map provider to payment method
                    provider_map = {
                        "stripe": "stripe",
                        "venmo": "venmo",
                        "zelle": "zelle",
                        "bank_of_america": "zelle",  # BofA uses Zelle
                    }

                    payment_method = provider_map.get(notification["provider"])
                    if not payment_method:
                        logger.warning(f"Unknown provider: {notification['provider']}")
                        continue

                    # Find matching payment
                    payment = PaymentMatcher.find_matching_payment(
                        db=self.db,
                        amount=notification["amount"],
                        payment_method=payment_method,
                        received_at=None,  # Use current time
                    )

                    if not payment:
                        results["errors"].append(
                            {
                                "email_id": notification.get("email_id"),
                                "error": "No matching payment found",
                                "amount": str(notification["amount"]),
                                "provider": notification["provider"],
                            }
                        )
                        continue

                    results["payments_matched"] += 1

                    # Auto-confirm payment if enabled
                    if auto_confirm:
                        success = PaymentMatcher.confirm_payment(
                            db=self.db,
                            payment=payment,
                            notification_data=notification,
                            email_service=self.email_service,
                            notify_service=self.notify_service,
                        )

                        if success:
                            results["payments_confirmed"] += 1

                            # Mark email as read
                            if mark_as_read:
                                self.email_monitor.mark_as_read(notification["email_id"])
                        else:
                            results["errors"].append(
                                {
                                    "payment_id": payment.id,
                                    "error": "Failed to confirm payment",
                                }
                            )

                except Exception as e:
                    logger.exception(f"Error processing notification: {e}")
                    results["errors"].append(
                        {
                            "error": str(e),
                            "notification": notification,
                        }
                    )
                    continue

            # Log summary
            logger.info(
                f"✅ Processing complete: "
                f"{results['payments_confirmed']}/{results['payments_matched']} payments confirmed, "
                f"{len(results['errors'])} errors"
            )

            return results

        except Exception as e:
            logger.exception(f"Error in payment email processing: {e}")
            results["errors"].append({"error": str(e)})
            return results

    def get_unmatched_notifications(self, since_date: datetime | None = None) -> list[dict]:
        """
        Get payment notifications that couldn't be matched

        Args:
            since_date: Only check emails since this date

        Returns:
            List of unmatched payment notifications
        """
        notifications = self.email_monitor.get_unread_payment_emails(since_date=since_date)

        unmatched = []

        for notification in notifications:
            provider_map = {
                "stripe": "stripe",
                "venmo": "venmo",
                "zelle": "zelle",
                "bank_of_america": "zelle",
            }

            payment_method = provider_map.get(notification["provider"])
            if not payment_method:
                continue

            payment = PaymentMatcher.find_matching_payment(
                db=self.db,
                amount=notification["amount"],
                payment_method=payment_method,
            )

            if not payment:
                unmatched.append(notification)

        return unmatched


# Background task for periodic email checking
async def check_payment_emails_task(
    db: Session,
    email_monitor: PaymentEmailMonitor,
    email_service: EmailService | None = None,
    notify_service: NotificationService | None = None,
):
    """
    Background task to periodically check for payment emails

    Run this every 1-5 minutes via scheduler
    """
    service = PaymentEmailService(
        db=db,
        email_monitor=email_monitor,
        email_service=email_service,
        notify_service=notify_service,
    )

    # Process emails from last 7 days
    since_date = datetime.now(timezone.utc) - timedelta(days=7)

    results = service.process_payment_emails(
        since_date=since_date,
        auto_confirm=True,
        mark_as_read=True,
    )

    logger.info(f"Payment email check complete: {results}")

    return results
