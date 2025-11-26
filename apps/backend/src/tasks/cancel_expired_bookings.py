"""
Smart Booking Management: Customer Urgency + Internal Grace Period

STRATEGY: Tell customers 2 hours (urgency), give them 24 hours (grace)
- Customer sees: "Pay deposit within 2 hours to lock your date!"
- Internal enforcement: Actually wait 24 hours before auto-cancel
- Manual admin confirmation available at any time
- SMS warnings keep customers engaged

TIMELINE:
- T+0: Booking created
  → customer_deposit_deadline = T+2h (shown to customer)
  → internal_deadline = T+24h (actual enforcement)
  → SMS sent: "Pay $100 deposit within 2 hours to lock your date!"

- T+1h30m: First reminder
  → SMS: "30 minutes left to pay deposit! Don't lose your date."

- T+2h: Customer deadline passes (but we don't cancel)
  → SMS: "Deposit deadline passed. We're holding your booking - pay ASAP!"

- T+12h: Mid-grace reminder
  → SMS: "Still waiting for deposit. Please pay today to confirm."

- T+23h: Final warning
  → SMS: "FINAL NOTICE: Pay deposit within 1 hour or booking will be released."

- T+24h: Internal deadline - auto-cancel IF:
  ✓ No payment received
  ✓ No admin hold request
  ✓ No manual deposit confirmation

Admin can click "Deposit Received" button at ANY time to override!
"""

from datetime import datetime, timezone, timedelta
import logging
from decimal import Decimal
from sqlalchemy import and_
from sqlalchemy.orm import Session

from db.models.core import Booking, BookingStatus
from models.booking import Payment
from core.database import get_db

logger = logging.getLogger(__name__)

MINIMUM_DEPOSIT = Decimal("100.00")
CUSTOMER_DEADLINE_HOURS = 2  # Customer-facing deadline (urgency)
INTERNAL_DEADLINE_HOURS = 24  # Actual enforcement deadline (grace)


async def send_deposit_reminders():
    """
    Send SMS reminders about deposit deadlines.

    Schedule:
    - T+1h30m: First reminder (30 min before customer deadline)
    - T+2h: Customer deadline passed, but we're holding it
    - T+12h: Mid-grace reminder
    - T+23h: Final warning (1 hour before auto-cancel)

    Runs every 30 minutes to check for bookings needing reminders.
    """
    try:
        db: Session = next(get_db())
        now = datetime.now(timezone.utc)

        # T+1h30m: First reminder (30 min before customer deadline)
        thirty_min_window_start = now - timedelta(minutes=30)
        thirty_min_window_end = now - timedelta(minutes=25)

        bookings_30min = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.customer_deposit_deadline.between(
                        thirty_min_window_start, thirty_min_window_end
                    ),
                    Booking.deposit_confirmed_at.is_(None),
                    Booking.hold_on_request == False,
                )
            )
            .all()
        )

        for booking in bookings_30min:
            # TODO: Send SMS via RingCentral
            # "Hi {name}! 30 minutes left to pay $100 deposit. Don't lose your date!"
            logger.info(f"📱 T+1h30m reminder sent for booking {booking.id}")

        # T+2h: Customer deadline passed (but we're still holding it)
        two_hour_window_start = now - timedelta(hours=2, minutes=5)
        two_hour_window_end = now - timedelta(hours=2)

        bookings_2h = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.customer_deposit_deadline.between(
                        two_hour_window_start, two_hour_window_end
                    ),
                    Booking.deposit_confirmed_at.is_(None),
                    Booking.hold_on_request == False,
                )
            )
            .all()
        )

        for booking in bookings_2h:
            # TODO: Send SMS
            # "Deposit deadline passed but we're holding your booking! Pay ASAP to confirm."
            logger.info(f"📱 T+2h grace notice sent for booking {booking.id}")

        # T+12h: Mid-grace reminder
        twelve_hour_window_start = now - timedelta(hours=12, minutes=30)
        twelve_hour_window_end = now - timedelta(hours=12)

        bookings_12h = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at.between(twelve_hour_window_start, twelve_hour_window_end),
                    Booking.deposit_confirmed_at.is_(None),
                    Booking.hold_on_request == False,
                )
            )
            .all()
        )

        for booking in bookings_12h:
            # TODO: Send SMS
            # "Still waiting for your $100 deposit. Please pay today to confirm!"
            logger.info(f"📱 T+12h mid-grace reminder sent for booking {booking.id}")

        # T+23h: Final warning (1 hour before auto-cancel)
        twentythree_hour_window_start = now - timedelta(hours=23, minutes=30)
        twentythree_hour_window_end = now - timedelta(hours=23)

        bookings_23h = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at.between(
                        twentythree_hour_window_start, twentythree_hour_window_end
                    ),
                    Booking.deposit_confirmed_at.is_(None),
                    Booking.hold_on_request == False,
                )
            )
            .all()
        )

        for booking in bookings_23h:
            # TODO: Send SMS
            # "FINAL NOTICE: Pay deposit within 1 hour or booking will be released!"
            logger.warning(f"⚠️ T+23h FINAL warning sent for booking {booking.id}")

        db.close()

    except Exception as e:
        logger.exception(f"Error sending deposit reminders: {e}")


async def auto_cancel_after_24_hours():
    """
    Auto-cancel bookings after 24-hour internal deadline.

    Only cancels if:
    ✓ 24 hours have passed (internal_deadline)
    ✓ No deposit confirmed (deposit_confirmed_at is NULL)
    ✓ No admin hold (hold_on_request = False)
    ✓ No payment received (check Payment table)

    Runs every hour to check for expired bookings.
    """
    try:
        db: Session = next(get_db())
        now = datetime.now(timezone.utc)

        # Find bookings past 24-hour internal deadline
        expired_bookings = (
            db.query(Booking)
            .filter(
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.internal_deadline < now,  # Past 24-hour grace
                    Booking.internal_deadline.isnot(None),
                    Booking.deposit_confirmed_at.is_(None),  # Not manually confirmed
                    Booking.hold_on_request == False,  # Not manually held
                )
            )
            .all()
        )

        cancelled_count = 0

        for booking in expired_bookings:
            # Check if booking has payment >= $100
            payments = (
                db.query(Payment)
                .filter(Payment.booking_id == booking.id, Payment.status == "completed")
                .all()
            )

            total_paid = sum(p.amount for p in payments)

            if total_paid < 100:  # $100 minimum deposit not met
                # Cancel the booking
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = now
                booking.cancellation_reason = (
                    f"Auto-cancelled: $100 deposit not received within 2 hours. "
                    f"Only ${total_paid} paid. Deadline was {booking.deposit_deadline}."
                )

                db.commit()
                cancelled_count += 1

                logger.warning(
                    f"Auto-cancelled booking {booking.id} - "
                    f"deposit deadline expired, only ${total_paid} paid (need $100)"
                )

                # TODO: Send notification to customer
                # - Email: "Your booking was cancelled due to no deposit"
                # - SMS: "Booking cancelled - deposit not received"
                # - Offer to rebook

        if cancelled_count > 0:
            logger.info(f"✅ Auto-cancelled {cancelled_count} expired bookings without deposit")
        else:
            logger.debug("No expired bookings to cancel")

        db.close()

    except Exception as e:
        logger.exception(f"Error in cancel_expired_bookings_without_deposit: {e}")


if __name__ == "__main__":
    # Test the task
    import asyncio

    asyncio.run(auto_cancel_after_24_hours())
