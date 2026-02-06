"""
Slot Hold Auto-Cancel Celery Tasks
===================================

Periodic tasks for managing slot hold expiration:
- Phase 1: 2 hours to sign agreement (from hold creation)
- Phase 2: 4 hours to pay deposit (from agreement signing)
- 1-hour warning notifications before each deadline

User Decision (from batch 1 audit):
"if the agreement is not signed within 2 hours and after signed
if deposit is not paid within 4 hours after the agreement signed
with a warning to user 1 hour before auto cancel"

Tasks run every 15 minutes to check for:
1. Holds needing signing warning (1 hour before 2-hour deadline)
2. Holds needing payment warning (1 hour before 4-hour deadline)
3. Holds past signing deadline (auto-cancel)
4. Holds past payment deadline (auto-cancel)

Related:
- Migration: 009_slot_holds_auto_cancel.sql
- Service: services/agreements/slot_hold_service.py
- Table: core.slot_holds
"""

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from sqlalchemy import and_, select

from core.database import SessionLocal
from db.models.slot_hold import SlotHold


@contextmanager
def get_db_sync():
    """Sync database session for Celery tasks."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


logger = logging.getLogger(__name__)

# =====================================================
# CONSTANTS
# =====================================================

# Warning thresholds (from user decision)
SIGNING_DEADLINE_HOURS = 2
PAYMENT_DEADLINE_HOURS = 4
WARNING_BEFORE_DEADLINE_HOURS = 1

# Task names for routing
TASK_CHECK_SIGNING_WARNINGS = "slot_holds.check_signing_warnings"
TASK_CHECK_PAYMENT_WARNINGS = "slot_holds.check_payment_warnings"
TASK_EXPIRE_UNSIGNED_HOLDS = "slot_holds.expire_unsigned_holds"
TASK_EXPIRE_UNPAID_HOLDS = "slot_holds.expire_unpaid_holds"
TASK_SEND_WARNING = "slot_holds.send_warning"


# =====================================================
# MAIN PERIODIC TASKS (Called by Celery Beat)
# =====================================================


@shared_task(name=TASK_CHECK_SIGNING_WARNINGS, bind=True, max_retries=3)
def check_signing_warnings(self) -> dict:
    """
    Check for holds approaching the 2-hour signing deadline.

    Runs every 15 minutes to find holds that:
    - Are still pending (status = 'pending')
    - Have NOT signed the agreement yet (agreement_signed_at IS NULL)
    - Are within 1 hour of signing deadline
    - Have NOT already received a signing warning

    Returns:
        dict: Summary of warnings sent
    """
    logger.info("🔔 Checking for holds needing signing warning...")

    now = datetime.utcnow()
    warning_threshold = now + timedelta(hours=WARNING_BEFORE_DEADLINE_HOURS)

    warnings_sent = 0
    errors = []

    with get_db_sync() as db:
        # Find holds approaching signing deadline (within 1 hour)
        # but haven't received warning yet
        holds = (
            db.execute(
                select(SlotHold).where(
                    and_(
                        SlotHold.status == "pending",
                        SlotHold.agreement_signed_at.is_(None),
                        SlotHold.signing_deadline_at <= warning_threshold,
                        SlotHold.signing_deadline_at > now,  # Not yet expired
                        SlotHold.signing_warning_sent_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )

        logger.info(f"Found {len(holds)} holds needing signing warning")

        for hold in holds:
            try:
                # Send warning notification
                send_hold_warning.delay(
                    hold_id=str(hold.id),
                    warning_type="signing",
                    deadline_at=hold.signing_deadline_at.isoformat(),
                    customer_email=hold.customer_email,
                    customer_name=hold.customer_name,
                )

                # Mark warning as sent
                hold.signing_warning_sent_at = now
                db.commit()

                warnings_sent += 1
                logger.info(f"✅ Queued signing warning for hold {hold.id}")

            except Exception as e:
                errors.append(str(e))
                logger.error(f"❌ Failed to send signing warning for {hold.id}: {e}")
                db.rollback()

    result = {
        "task": "check_signing_warnings",
        "timestamp": now.isoformat(),
        "warnings_sent": warnings_sent,
        "errors": errors,
    }

    logger.info(f"📊 Signing warnings check complete: {warnings_sent} warnings sent")
    return result


@shared_task(name=TASK_CHECK_PAYMENT_WARNINGS, bind=True, max_retries=3)
def check_payment_warnings(self) -> dict:
    """
    Check for holds approaching the 4-hour payment deadline.

    Runs every 15 minutes to find holds that:
    - Are still pending (status = 'pending')
    - HAVE signed the agreement (agreement_signed_at IS NOT NULL)
    - Have NOT paid the deposit yet (deposit_paid_at IS NULL)
    - Are within 1 hour of payment deadline
    - Have NOT already received a payment warning

    Returns:
        dict: Summary of warnings sent
    """
    logger.info("🔔 Checking for holds needing payment warning...")

    now = datetime.utcnow()
    warning_threshold = now + timedelta(hours=WARNING_BEFORE_DEADLINE_HOURS)

    warnings_sent = 0
    errors = []

    with get_db_sync() as db:
        # Find signed holds approaching payment deadline
        holds = (
            db.execute(
                select(SlotHold).where(
                    and_(
                        SlotHold.status == "pending",
                        SlotHold.agreement_signed_at.isnot(None),
                        SlotHold.deposit_paid_at.is_(None),
                        SlotHold.payment_deadline_at <= warning_threshold,
                        SlotHold.payment_deadline_at > now,  # Not yet expired
                        SlotHold.payment_warning_sent_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )

        logger.info(f"Found {len(holds)} holds needing payment warning")

        for hold in holds:
            try:
                # Send warning notification
                send_hold_warning.delay(
                    hold_id=str(hold.id),
                    warning_type="payment",
                    deadline_at=hold.payment_deadline_at.isoformat(),
                    customer_email=hold.customer_email,
                    customer_name=hold.customer_name,
                )

                # Mark warning as sent
                hold.payment_warning_sent_at = now
                db.commit()

                warnings_sent += 1
                logger.info(f"✅ Queued payment warning for hold {hold.id}")

            except Exception as e:
                errors.append(str(e))
                logger.error(f"❌ Failed to send payment warning for {hold.id}: {e}")
                db.rollback()

    result = {
        "task": "check_payment_warnings",
        "timestamp": now.isoformat(),
        "warnings_sent": warnings_sent,
        "errors": errors,
    }

    logger.info(f"📊 Payment warnings check complete: {warnings_sent} warnings sent")
    return result


@shared_task(name=TASK_EXPIRE_UNSIGNED_HOLDS, bind=True, max_retries=3)
def expire_unsigned_holds(self) -> dict:
    """
    Auto-cancel holds that missed the 2-hour signing deadline.

    Runs every 15 minutes to find and cancel holds that:
    - Are still pending (status = 'pending')
    - Have NOT signed the agreement (agreement_signed_at IS NULL)
    - Are past signing deadline (signing_deadline_at < now)

    Returns:
        dict: Summary of expired holds
    """
    logger.info("⏰ Checking for unsigned holds past deadline...")

    now = datetime.utcnow()
    expired_count = 0
    errors = []

    with get_db_sync() as db:
        # Find holds past signing deadline
        holds = (
            db.execute(
                select(SlotHold).where(
                    and_(
                        SlotHold.status == "pending",
                        SlotHold.agreement_signed_at.is_(None),
                        SlotHold.signing_deadline_at < now,
                    )
                )
            )
            .scalars()
            .all()
        )

        logger.info(f"Found {len(holds)} unsigned holds past deadline")

        for hold in holds:
            try:
                # Update status to expired
                hold.status = "expired"
                hold.cancellation_reason = "signing_timeout"
                db.commit()

                # Send expiration notification
                send_hold_expired_notification.delay(
                    hold_id=str(hold.id),
                    expiration_reason="signing_timeout",
                    customer_email=hold.customer_email,
                    customer_name=hold.customer_name,
                )

                expired_count += 1
                logger.info(f"❌ Expired unsigned hold {hold.id} (signing timeout)")

            except Exception as e:
                errors.append(str(e))
                logger.error(f"❌ Failed to expire hold {hold.id}: {e}")
                db.rollback()

    result = {
        "task": "expire_unsigned_holds",
        "timestamp": now.isoformat(),
        "expired_count": expired_count,
        "errors": errors,
    }

    logger.info(f"📊 Unsigned holds expiration check: {expired_count} expired")
    return result


@shared_task(name=TASK_EXPIRE_UNPAID_HOLDS, bind=True, max_retries=3)
def expire_unpaid_holds(self) -> dict:
    """
    Auto-cancel signed holds that missed the 4-hour payment deadline.

    Runs every 15 minutes to find and cancel holds that:
    - Are still pending (status = 'pending')
    - HAVE signed the agreement (agreement_signed_at IS NOT NULL)
    - Have NOT paid the deposit (deposit_paid_at IS NULL)
    - Are past payment deadline (payment_deadline_at < now)

    Returns:
        dict: Summary of expired holds
    """
    logger.info("⏰ Checking for unpaid signed holds past deadline...")

    now = datetime.utcnow()
    expired_count = 0
    errors = []

    with get_db_sync() as db:
        # Find signed holds past payment deadline
        holds = (
            db.execute(
                select(SlotHold).where(
                    and_(
                        SlotHold.status == "pending",
                        SlotHold.agreement_signed_at.isnot(None),
                        SlotHold.deposit_paid_at.is_(None),
                        SlotHold.payment_deadline_at < now,
                    )
                )
            )
            .scalars()
            .all()
        )

        logger.info(f"Found {len(holds)} unpaid signed holds past deadline")

        for hold in holds:
            try:
                # Update status to expired
                hold.status = "expired"
                hold.cancellation_reason = "payment_timeout"
                db.commit()

                # Send expiration notification
                send_hold_expired_notification.delay(
                    hold_id=str(hold.id),
                    expiration_reason="payment_timeout",
                    customer_email=hold.customer_email,
                    customer_name=hold.customer_name,
                )

                expired_count += 1
                logger.info(f"❌ Expired unpaid hold {hold.id} (payment timeout)")

            except Exception as e:
                errors.append(str(e))
                logger.error(f"❌ Failed to expire hold {hold.id}: {e}")
                db.rollback()

    result = {
        "task": "expire_unpaid_holds",
        "timestamp": now.isoformat(),
        "expired_count": expired_count,
        "errors": errors,
    }

    logger.info(f"📊 Unpaid holds expiration check: {expired_count} expired")
    return result


# =====================================================
# NOTIFICATION TASKS
# =====================================================


@shared_task(name=TASK_SEND_WARNING, bind=True, max_retries=3)
def send_hold_warning(
    self,
    hold_id: str,
    warning_type: str,  # "signing" or "payment"
    deadline_at: str,
    customer_email: str,
    customer_name: Optional[str] = None,
) -> dict:
    """
    Send warning notification to customer about approaching deadline.

    Args:
        hold_id: UUID of the slot hold
        warning_type: "signing" or "payment"
        deadline_at: ISO format deadline timestamp
        customer_email: Customer's email address
        customer_name: Customer's name (optional)

    Returns:
        dict: Notification result
    """
    logger.info(f"📧 Sending {warning_type} warning to {customer_email}")

    try:
        # Import notification service
        from services.notification_service import NotificationService

        deadline = datetime.fromisoformat(deadline_at)
        time_remaining = deadline - datetime.utcnow()
        minutes_remaining = int(time_remaining.total_seconds() / 60)

        if warning_type == "signing":
            subject = "⚠️ Your reservation hold expires soon - Please sign to confirm"
            message = f"""
Hi {customer_name or 'there'},

Your My Hibachi reservation hold expires in approximately {minutes_remaining} minutes.

⏰ DEADLINE: {deadline.strftime('%B %d, %Y at %I:%M %p')} UTC

To secure your date, please sign the service agreement now using the link we sent earlier.

If you don't sign before the deadline, your hold will be automatically released and the time slot may be booked by someone else.

Need help? Reply to this email or text us at (916) 740-8768.

- My Hibachi Team
"""
        else:  # payment warning
            subject = "⚠️ Final step - Pay your deposit to confirm booking"
            message = f"""
Hi {customer_name or 'there'},

Thank you for signing your agreement! 🎉

Your booking is almost confirmed, but we need your $100 deposit within {minutes_remaining} minutes.

⏰ DEADLINE: {deadline.strftime('%B %d, %Y at %I:%M %p')} UTC

💳 Pay now to secure your date. You can pay via:
- Credit Card (fastest)
- Venmo Business: @MyHibachiChef
- Zelle: cs@myhibachichef.com

If you don't pay before the deadline, your hold will be automatically released.

Need help? Reply to this email or text us at (916) 740-8768.

- My Hibachi Team
"""

        # Send email notification
        notification_service = NotificationService()
        _result = notification_service.send_email(
            to_email=customer_email, subject=subject, body=message
        )

        # Also send SMS if we have phone number
        # TODO: Add SMS sending here when phone is available

        logger.info(f"✅ Sent {warning_type} warning to {customer_email}")

        return {
            "success": True,
            "hold_id": hold_id,
            "warning_type": warning_type,
            "customer_email": customer_email,
            "sent_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to send {warning_type} warning: {e}")
        # Retry the task
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute


@shared_task(name="slot_holds.send_expired_notification", bind=True, max_retries=3)
def send_hold_expired_notification(
    self,
    hold_id: str,
    expiration_reason: str,  # "signing_timeout" or "payment_timeout"
    customer_email: str,
    customer_name: Optional[str] = None,
) -> dict:
    """
    Notify customer that their hold has expired.

    Args:
        hold_id: UUID of the expired slot hold
        expiration_reason: Why it expired
        customer_email: Customer's email
        customer_name: Customer's name (optional)

    Returns:
        dict: Notification result
    """
    logger.info(f"📧 Sending expiration notice to {customer_email}")

    try:
        from services.notification_service import NotificationService

        if expiration_reason == "signing_timeout":
            subject = "Your My Hibachi reservation hold has expired"
            message = f"""
Hi {customer_name or 'there'},

Unfortunately, your reservation hold has expired because the agreement wasn't signed within the 2-hour window.

The time slot you were holding is now available for other customers.

📅 Want to book again?
Visit our website to check availability and start a new reservation.

We'd still love to cook for you! If you have any questions, text us at (916) 740-8768.

- My Hibachi Team
"""
        else:  # payment_timeout
            subject = "Your My Hibachi reservation has been cancelled"
            message = f"""
Hi {customer_name or 'there'},

Unfortunately, your reservation has been cancelled because the deposit wasn't received within 4 hours of signing.

The time slot is now available for other customers.

📅 Want to try again?
Visit our website to check availability. Make sure to have your payment method ready so you can complete the booking quickly!

We'd still love to cook for you! If you have any questions, text us at (916) 740-8768.

- My Hibachi Team
"""

        notification_service = NotificationService()
        _result = notification_service.send_email(
            to_email=customer_email, subject=subject, body=message
        )

        logger.info(f"✅ Sent expiration notice to {customer_email}")

        return {
            "success": True,
            "hold_id": hold_id,
            "reason": expiration_reason,
            "customer_email": customer_email,
            "sent_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to send expiration notice: {e}")
        raise self.retry(exc=e, countdown=60)


# =====================================================
# UTILITY FUNCTIONS
# =====================================================


def get_holds_summary() -> dict:
    """
    Get summary of current hold statuses (for monitoring).

    Returns:
        dict: Count of holds by status and phase
    """
    with get_db_sync() as db:
        from sqlalchemy import func

        # Count by status
        status_counts = db.execute(
            select(SlotHold.status, func.count(SlotHold.id).label("count")).group_by(
                SlotHold.status
            )
        ).all()

        # Count pending by phase
        pending_unsigned = db.execute(
            select(func.count(SlotHold.id)).where(
                and_(
                    SlotHold.status == "pending", SlotHold.agreement_signed_at.is_(None)
                )
            )
        ).scalar()

        pending_unpaid = db.execute(
            select(func.count(SlotHold.id)).where(
                and_(
                    SlotHold.status == "pending",
                    SlotHold.agreement_signed_at.isnot(None),
                    SlotHold.deposit_paid_at.is_(None),
                )
            )
        ).scalar()

        return {
            "by_status": {row.status: row.count for row in status_counts},
            "pending_phase1_unsigned": pending_unsigned,
            "pending_phase2_unpaid": pending_unpaid,
        }
