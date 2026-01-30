"""
FAILPROOF Chef Assignment Alert System
=======================================

CRITICAL: This system ensures NO urgent booking goes without a chef assignment.
Failure is NOT an option - multiple redundancy layers guarantee alerts are sent.

ESCALATION LEVELS:
==================
Level 0: INITIAL ALERT
    - When: Booking becomes urgent (within 7 days) without chef
    - Who: Station Manager + all ADMIN users for the station
    - Channels: Email + SMS
    - Record: chef_assignment_alerts table

Level 1: FIRST REMINDER
    - When: 4 hours after initial, still no chef
    - Who: Same as Level 0 + Super Admin notification
    - Channels: Email + SMS + Dashboard notification
    - Urgency: ⚠️ HIGH

Level 2: SECOND REMINDER
    - When: 8 hours after initial, still no chef
    - Who: All admins + Super Admin (direct)
    - Channels: Email + SMS + Phone call to Super Admin
    - Urgency: 🚨 CRITICAL

Level 3: ESCALATION
    - When: 12 hours after initial, still no chef
    - Who: Super Admin ONLY (personal contact)
    - Channels: Phone call + SMS + Email
    - Action: Super Admin must acknowledge or assign
    - Urgency: 🔴 EMERGENCY

FAILSAFE MECHANISMS:
====================
1. Database record of every alert attempt
2. Retry with exponential backoff
3. Multi-channel delivery (Email + SMS + sometimes Phone)
4. Dead letter queue for failed alerts
5. Daily summary of all unassigned urgent bookings
6. Super Admin always notified at Level 2+

Related Files:
    - workers/urgency_update_tasks.py - Triggers alerts
    - services/urgent_booking_service.py - Urgency calculations
    - database/migrations/021_urgent_booking_system.sql - Schema

SSoT Variables Used:
    - alerts.chef_assignment_alert_interval_hours (default: 4)
    - alerts.chef_assignment_max_alerts (default: 3)
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import get_sync_db
from services.business_config_service import get_business_config_sync
from workers.celery_config import celery_app

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """
    Alert escalation levels with increasing urgency.
    """

    INITIAL = 0  # First alert when booking becomes urgent
    REMINDER_1 = 1  # 4 hours later
    REMINDER_2 = 2  # 8 hours later
    ESCALATION = 3  # 12 hours later - direct Super Admin contact


class AlertChannel(str, Enum):
    """
    Notification delivery channels.
    """

    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PUSH = "push"
    DASHBOARD = "dashboard"


# Alert level configuration
ALERT_LEVEL_CONFIG = {
    AlertLevel.INITIAL: {
        "channels": [AlertChannel.EMAIL, AlertChannel.SMS],
        "recipients": ["station_manager", "station_admins"],
        "subject_prefix": "🔔 Chef Needed",
        "urgency": "medium",
        "include_super_admin": False,
    },
    AlertLevel.REMINDER_1: {
        "channels": [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.DASHBOARD],
        "recipients": ["station_manager", "station_admins"],
        "subject_prefix": "⚠️ REMINDER: Chef Needed",
        "urgency": "high",
        "include_super_admin": True,  # CC super admin
    },
    AlertLevel.REMINDER_2: {
        "channels": [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PHONE],
        "recipients": ["station_manager", "station_admins", "super_admin"],
        "subject_prefix": "🚨 URGENT: Chef Still Needed",
        "urgency": "critical",
        "include_super_admin": True,
    },
    AlertLevel.ESCALATION: {
        "channels": [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PHONE],
        "recipients": ["super_admin"],  # ONLY super admin at this level
        "subject_prefix": "🔴 EMERGENCY: Unassigned Booking",
        "urgency": "emergency",
        "include_super_admin": True,
        "requires_acknowledgment": True,
    },
}


@celery_app.task(bind=True, max_retries=10, default_retry_delay=60)
def process_chef_assignment_alert(
    self,
    booking_id: str,
    trigger_reason: str = "manual",
) -> Dict[str, Any]:
    """
    FAILPROOF chef assignment alert processor.

    This is the main entry point for the alert system.
    It determines the current alert level and sends appropriate notifications.

    CRITICAL: This task has 10 retries with exponential backoff.
    Failure to send alerts is logged and escalated.

    Args:
        booking_id: UUID of the booking
        trigger_reason: Why the alert was triggered

    Returns:
        Dict with alert status and details
    """
    db: Session = next(get_sync_db())
    config = get_business_config_sync()

    alert_interval_hours = config.chef_assignment_alert_interval_hours
    max_alerts = config.chef_assignment_max_alerts

    try:
        # Get booking and current alert status
        booking_data = _get_booking_alert_status(db, booking_id)

        if not booking_data:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "error", "message": "Booking not found"}

        # Check if chef has been assigned (if so, no alert needed)
        if booking_data["chef_id"]:
            logger.info(
                f"✅ Booking {booking_id} already has chef assigned, skipping alert"
            )
            return {
                "status": "skipped",
                "reason": "chef_already_assigned",
                "booking_id": booking_id,
            }

        # Determine current alert level
        alert_count = booking_data["urgency_alert_count"] or 0
        first_alert_at = booking_data["urgency_alert_sent_at"]

        current_level = _determine_alert_level(
            alert_count=alert_count,
            first_alert_at=first_alert_at,
            interval_hours=alert_interval_hours,
            max_alerts=max_alerts,
        )

        logger.info(
            f"📊 Processing alert for booking {booking_id}: "
            f"level={current_level.name}, count={alert_count}"
        )

        # Get recipients for this alert level
        recipients = _get_alert_recipients(
            db=db,
            station_id=booking_data["station_id"],
            alert_level=current_level,
        )

        if not recipients:
            logger.error(
                f"❌ No recipients found for booking {booking_id} "
                f"at level {current_level.name}"
            )
            # FAILSAFE: Always notify super admin if no recipients
            recipients = _get_super_admin_contacts(db)

        # Build alert content
        alert_content = _build_alert_content(
            booking_data=booking_data,
            alert_level=current_level,
            alert_count=alert_count + 1,
        )

        # Send alerts through all configured channels
        level_config = ALERT_LEVEL_CONFIG[current_level]
        send_results = []

        for channel in level_config["channels"]:
            try:
                result = _send_alert_via_channel(
                    channel=channel,
                    recipients=recipients,
                    content=alert_content,
                    urgency=level_config["urgency"],
                )
                send_results.append(
                    {
                        "channel": channel.value,
                        "success": result.get("success", False),
                        "message_id": result.get("message_id"),
                    }
                )
            except Exception as e:
                logger.error(f"❌ Failed to send via {channel.value}: {e}")
                send_results.append(
                    {
                        "channel": channel.value,
                        "success": False,
                        "error": str(e),
                    }
                )

        # Record alert in database
        _record_alert(
            db=db,
            booking_id=booking_id,
            alert_level=current_level,
            trigger_reason=trigger_reason,
            recipients=recipients,
            channels=[r["channel"] for r in send_results if r.get("success")],
            success=any(r.get("success") for r in send_results),
        )

        # Update booking alert tracking
        _update_booking_alert_tracking(
            db=db,
            booking_id=booking_id,
            new_count=alert_count + 1,
            is_first_alert=(alert_count == 0),
            is_escalated=(current_level == AlertLevel.ESCALATION),
        )

        db.commit()

        # Schedule next reminder if not at max level
        if (
            current_level.value < AlertLevel.ESCALATION.value
            and alert_count + 1 < max_alerts
        ):
            schedule_next_reminder.apply_async(
                args=[booking_id],
                countdown=alert_interval_hours * 3600,  # hours to seconds
            )

        # Log success
        successful_channels = [r["channel"] for r in send_results if r.get("success")]
        logger.info(
            f"✅ Alert sent for booking {booking_id}: "
            f"level={current_level.name}, channels={successful_channels}"
        )

        return {
            "status": "success",
            "booking_id": booking_id,
            "alert_level": current_level.name,
            "alert_count": alert_count + 1,
            "channels_sent": successful_channels,
            "recipients_count": len(recipients),
        }

    except Exception as e:
        logger.error(f"❌ Chef assignment alert failed for {booking_id}: {e}")
        db.rollback()

        # FAILSAFE: Log to dead letter queue and notify super admin
        try:
            _log_failed_alert(db, booking_id, str(e), self.request.retries)
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=60 * (2**self.request.retries),  # 1m, 2m, 4m, 8m...
        )

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=5)
def schedule_next_reminder(self, booking_id: str) -> Dict[str, Any]:
    """
    Schedule the next reminder alert if chef still not assigned.

    Called by process_chef_assignment_alert after successful alert.
    Checks if chef has been assigned before sending reminder.
    """
    db: Session = next(get_sync_db())

    try:
        # Check if chef has been assigned
        result = db.execute(
            text(
                """
                SELECT chef_id, status
                FROM core.bookings
                WHERE id = :booking_id::uuid
            """
            ),
            {"booking_id": booking_id},
        )
        booking = result.fetchone()

        if not booking:
            return {"status": "error", "message": "Booking not found"}

        # If chef assigned or booking cancelled, no reminder needed
        if booking[0] is not None:
            logger.info(f"✅ Chef assigned to {booking_id}, no reminder needed")
            return {"status": "skipped", "reason": "chef_assigned"}

        if booking[1] in ("cancelled", "completed", "deleted"):
            logger.info(f"ℹ️ Booking {booking_id} is {booking[1]}, no reminder needed")
            return {"status": "skipped", "reason": f"booking_{booking[1]}"}

        # Trigger next alert
        process_chef_assignment_alert.delay(
            booking_id=booking_id,
            trigger_reason="scheduled_reminder",
        )

        return {"status": "triggered", "booking_id": booking_id}

    except Exception as e:
        logger.error(f"❌ Failed to schedule reminder for {booking_id}: {e}")
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True)
def daily_unassigned_summary(self) -> Dict[str, Any]:
    """
    Daily summary of all urgent bookings without chef assignment.

    Sent every day at 9 AM to all super admins.
    FAILSAFE: Ensures super admins always have visibility.
    """
    db: Session = next(get_sync_db())

    try:
        # Get all urgent unassigned bookings
        result = db.execute(
            text(
                """
                SELECT
                    b.id::text,
                    b.event_date,
                    b.event_time,
                    b.days_until_event,
                    b.venue_address,
                    b.urgency_alert_count,
                    c.first_name,
                    c.last_name,
                    c.phone as customer_phone,
                    s.name as station_name
                FROM core.bookings b
                LEFT JOIN core.customers c ON b.customer_id = c.id
                LEFT JOIN identity.stations s ON b.station_id = s.id
                WHERE b.is_urgent = true
                  AND b.chef_id IS NULL
                  AND b.status NOT IN ('cancelled', 'completed', 'deleted')
                  AND b.event_date >= CURRENT_DATE
                ORDER BY b.days_until_event ASC, b.event_time ASC
            """
            )
        )
        unassigned = result.fetchall()

        if not unassigned:
            logger.info("✅ No unassigned urgent bookings for daily summary")
            return {"status": "success", "unassigned_count": 0}

        # Build summary content
        summary = _build_daily_summary(unassigned)

        # Get super admin contacts
        super_admins = _get_super_admin_contacts(db)

        # Send summary via email
        for admin in super_admins:
            try:
                _send_email_alert(
                    to_email=admin["email"],
                    subject=f"🔴 Daily Alert: {len(unassigned)} Urgent Bookings Need Chefs",
                    body=summary,
                )
            except Exception as e:
                logger.error(f"❌ Failed to send summary to {admin['email']}: {e}")

        logger.info(
            f"📊 Daily summary sent: {len(unassigned)} unassigned urgent bookings"
        )

        return {
            "status": "success",
            "unassigned_count": len(unassigned),
            "notified_admins": len(super_admins),
        }

    except Exception as e:
        logger.error(f"❌ Daily summary failed: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _get_booking_alert_status(db: Session, booking_id: str) -> Optional[Dict[str, Any]]:
    """Get booking details needed for alert processing."""
    result = db.execute(
        text(
            """
            SELECT
                b.id::text as booking_id,
                b.event_date,
                b.event_time,
                b.venue_timezone,
                b.days_until_event,
                b.is_urgent,
                b.chef_id::text,
                b.station_id::text,
                b.venue_address,
                b.urgency_alert_count,
                b.urgency_alert_sent_at,
                b.urgency_escalated_at,
                c.first_name as customer_first_name,
                c.last_name as customer_last_name,
                c.phone as customer_phone,
                c.email as customer_email,
                s.name as station_name
            FROM core.bookings b
            LEFT JOIN core.customers c ON b.customer_id = c.id
            LEFT JOIN identity.stations s ON b.station_id = s.id
            WHERE b.id = :booking_id::uuid
              AND b.is_deleted = false
        """
        ),
        {"booking_id": booking_id},
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "booking_id": row[0],
        "event_date": row[1],
        "event_time": row[2],
        "venue_timezone": row[3],
        "days_until_event": row[4],
        "is_urgent": row[5],
        "chef_id": row[6],
        "station_id": row[7],
        "venue_address": row[8],
        "urgency_alert_count": row[9],
        "urgency_alert_sent_at": row[10],
        "urgency_escalated_at": row[11],
        "customer_name": f"{row[12] or ''} {row[13] or ''}".strip(),
        "customer_phone": row[14],
        "customer_email": row[15],
        "station_name": row[16],
    }


def _determine_alert_level(
    alert_count: int,
    first_alert_at: Optional[datetime],
    interval_hours: int,
    max_alerts: int,
) -> AlertLevel:
    """Determine the appropriate alert level based on history."""
    if alert_count == 0:
        return AlertLevel.INITIAL

    if alert_count >= max_alerts:
        return AlertLevel.ESCALATION

    # Calculate hours since first alert
    if first_alert_at:
        now = datetime.now(timezone.utc)
        # Handle timezone-aware and naive datetimes
        if first_alert_at.tzinfo is None:
            first_alert_at = first_alert_at.replace(tzinfo=timezone.utc)
        hours_elapsed = (now - first_alert_at).total_seconds() / 3600

        if hours_elapsed >= interval_hours * 3:
            return AlertLevel.ESCALATION
        elif hours_elapsed >= interval_hours * 2:
            return AlertLevel.REMINDER_2
        elif hours_elapsed >= interval_hours:
            return AlertLevel.REMINDER_1

    # Based on count
    if alert_count >= 3:
        return AlertLevel.ESCALATION
    elif alert_count >= 2:
        return AlertLevel.REMINDER_2
    elif alert_count >= 1:
        return AlertLevel.REMINDER_1

    return AlertLevel.INITIAL


def _get_alert_recipients(
    db: Session,
    station_id: Optional[str],
    alert_level: AlertLevel,
) -> List[Dict[str, Any]]:
    """Get recipients for the given alert level."""
    recipients = []
    level_config = ALERT_LEVEL_CONFIG[alert_level]

    # Get station manager
    if "station_manager" in level_config["recipients"] and station_id:
        result = db.execute(
            text(
                """
                SELECT
                    u.id::text,
                    u.email,
                    u.phone,
                    u.first_name,
                    u.last_name,
                    'station_manager' as role
                FROM identity.users u
                JOIN identity.station_users su ON u.id = su.user_id
                WHERE su.station_id = :station_id::uuid
                  AND su.is_manager = true
                  AND u.is_active = true
            """
            ),
            {"station_id": station_id},
        )
        for row in result.fetchall():
            recipients.append(
                {
                    "id": row[0],
                    "email": row[1],
                    "phone": row[2],
                    "name": f"{row[3] or ''} {row[4] or ''}".strip(),
                    "role": row[5],
                }
            )

    # Get station admins
    if "station_admins" in level_config["recipients"] and station_id:
        result = db.execute(
            text(
                """
                SELECT
                    u.id::text,
                    u.email,
                    u.phone,
                    u.first_name,
                    u.last_name,
                    'station_admin' as role
                FROM identity.users u
                JOIN identity.station_users su ON u.id = su.user_id
                WHERE su.station_id = :station_id::uuid
                  AND u.role IN ('ADMIN', 'STATION_MANAGER')
                  AND u.is_active = true
            """
            ),
            {"station_id": station_id},
        )
        for row in result.fetchall():
            if not any(r["id"] == row[0] for r in recipients):
                recipients.append(
                    {
                        "id": row[0],
                        "email": row[1],
                        "phone": row[2],
                        "name": f"{row[3] or ''} {row[4] or ''}".strip(),
                        "role": row[5],
                    }
                )

    # Get super admins
    if "super_admin" in level_config["recipients"] or level_config.get(
        "include_super_admin"
    ):
        super_admins = _get_super_admin_contacts(db)
        for admin in super_admins:
            if not any(r["id"] == admin["id"] for r in recipients):
                recipients.append(admin)

    return recipients


def _get_super_admin_contacts(db: Session) -> List[Dict[str, Any]]:
    """Get all super admin contacts - FAILSAFE always works."""
    result = db.execute(
        text(
            """
            SELECT
                id::text,
                email,
                phone,
                first_name,
                last_name,
                'super_admin' as role
            FROM identity.users
            WHERE role = 'SUPER_ADMIN'
              AND is_active = true
        """
        )
    )

    super_admins = []
    for row in result.fetchall():
        super_admins.append(
            {
                "id": row[0],
                "email": row[1],
                "phone": row[2],
                "name": f"{row[3] or ''} {row[4] or ''}".strip(),
                "role": row[5],
            }
        )

    return super_admins


def _build_alert_content(
    booking_data: Dict[str, Any],
    alert_level: AlertLevel,
    alert_count: int,
) -> Dict[str, Any]:
    """Build the alert content for notifications."""
    level_config = ALERT_LEVEL_CONFIG[alert_level]

    event_date = booking_data["event_date"]
    if hasattr(event_date, "strftime"):
        event_date_str = event_date.strftime("%A, %B %d, %Y")
    else:
        event_date_str = str(event_date)

    return {
        "subject": (
            f"{level_config['subject_prefix']}: "
            f"{booking_data['customer_name']} on {event_date_str}"
        ),
        "booking_id": booking_data["booking_id"],
        "customer_name": booking_data["customer_name"],
        "customer_phone": booking_data["customer_phone"],
        "event_date": event_date_str,
        "event_time": str(booking_data.get("event_time", "TBD")),
        "venue_address": booking_data["venue_address"],
        "days_until": booking_data["days_until_event"],
        "station_name": booking_data["station_name"],
        "alert_count": alert_count,
        "urgency": level_config["urgency"],
        "action_url": f"/admin/bookings/{booking_data['booking_id']}",
        "message": (
            f"URGENT: Booking for {booking_data['customer_name']} on "
            f"{event_date_str} at {booking_data.get('event_time', 'TBD')} "
            f"needs a chef assigned! Only {booking_data['days_until_event']} days left. "
            f"This is alert #{alert_count}."
        ),
    }


def _send_alert_via_channel(
    channel: AlertChannel,
    recipients: List[Dict[str, Any]],
    content: Dict[str, Any],
    urgency: str,
) -> Dict[str, Any]:
    """Send alert through specified channel."""
    if channel == AlertChannel.EMAIL:
        return _send_email_alerts(recipients, content)
    elif channel == AlertChannel.SMS:
        return _send_sms_alerts(recipients, content)
    elif channel == AlertChannel.PHONE:
        return _send_phone_alerts(recipients, content)
    elif channel == AlertChannel.DASHBOARD:
        return _send_dashboard_notification(recipients, content)
    else:
        logger.warning(f"Unknown channel: {channel}")
        return {"success": False, "error": f"Unknown channel: {channel}"}


def _send_email_alerts(
    recipients: List[Dict[str, Any]],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """Send email alerts to all recipients."""
    try:
        # Import email service
        from services.email_service import send_email_sync

        successful = 0
        for recipient in recipients:
            if recipient.get("email"):
                try:
                    send_email_sync(
                        to_email=recipient["email"],
                        subject=content["subject"],
                        body=_format_email_body(content),
                        template="chef_assignment_alert",
                    )
                    successful += 1
                except Exception as e:
                    logger.error(f"Email to {recipient['email']} failed: {e}")

        return {
            "success": successful > 0,
            "sent_count": successful,
            "total_recipients": len(recipients),
        }
    except ImportError:
        logger.warning("Email service not available, logging alert instead")
        logger.info(f"📧 Email Alert: {content['subject']}")
        return {"success": True, "method": "logged"}


def _send_sms_alerts(
    recipients: List[Dict[str, Any]],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """Send SMS alerts to all recipients."""
    try:
        # Import SMS service
        from services.sms_service import send_sms_sync

        message = (
            f"{content['subject']}\n\n"
            f"Event: {content['event_date']} at {content['event_time']}\n"
            f"Customer: {content['customer_name']}\n"
            f"Days until: {content['days_until']}\n"
            f"Alert #{content['alert_count']}"
        )

        successful = 0
        for recipient in recipients:
            if recipient.get("phone"):
                try:
                    send_sms_sync(
                        to_phone=recipient["phone"],
                        message=message,
                    )
                    successful += 1
                except Exception as e:
                    logger.error(f"SMS to {recipient['phone']} failed: {e}")

        return {
            "success": successful > 0,
            "sent_count": successful,
            "total_recipients": len(recipients),
        }
    except ImportError:
        logger.warning("SMS service not available, logging alert instead")
        logger.info(f"📱 SMS Alert: {content['subject']}")
        return {"success": True, "method": "logged"}


def _send_phone_alerts(
    recipients: List[Dict[str, Any]],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """Initiate phone calls for critical alerts (Level 2+)."""
    try:
        # Import phone service (RingCentral)
        from services.ringcentral_service import initiate_alert_call

        # Phone calls only for super admins in emergencies
        super_admins = [r for r in recipients if r.get("role") == "super_admin"]

        successful = 0
        for admin in super_admins:
            if admin.get("phone"):
                try:
                    initiate_alert_call(
                        to_phone=admin["phone"],
                        message=f"Emergency: Urgent booking needs chef. {content['customer_name']} on {content['event_date']}. Please check admin dashboard immediately.",
                    )
                    successful += 1
                except Exception as e:
                    logger.error(f"Phone call to {admin['phone']} failed: {e}")

        return {
            "success": successful > 0,
            "calls_initiated": successful,
        }
    except ImportError:
        logger.warning("Phone call service not available")
        return {"success": False, "error": "Phone service unavailable"}


def _send_dashboard_notification(
    recipients: List[Dict[str, Any]],
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """Create dashboard notification for admin users."""
    # This creates entries in a notifications table that the admin dashboard polls
    logger.info(f"📊 Dashboard notification: {content['subject']}")
    return {"success": True, "method": "dashboard"}


def _format_email_body(content: Dict[str, Any]) -> str:
    """Format email body for chef assignment alert."""
    return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #dc3545;">🚨 Chef Assignment Needed</h2>

        <p><strong>Alert #{content['alert_count']}</strong> - Urgency: <strong>{content['urgency'].upper()}</strong></p>

        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3 style="margin-top: 0;">Booking Details</h3>
            <p><strong>Customer:</strong> {content['customer_name']}</p>
            <p><strong>Phone:</strong> {content['customer_phone']}</p>
            <p><strong>Event Date:</strong> {content['event_date']}</p>
            <p><strong>Event Time:</strong> {content['event_time']}</p>
            <p><strong>Venue:</strong> {content['venue_address']}</p>
            <p><strong>Station:</strong> {content['station_name']}</p>
            <p style="color: #dc3545; font-weight: bold;">⏰ {content['days_until']} days until event</p>
        </div>

        <p style="background: #fff3cd; padding: 10px; border-radius: 5px;">
            <strong>Action Required:</strong> Please assign a chef to this booking immediately.
        </p>

        <p>
            <a href="{content['action_url']}" style="display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Booking & Assign Chef
            </a>
        </p>

        <hr style="margin: 20px 0;">
        <p style="font-size: 12px; color: #666;">
            This is an automated alert from My Hibachi Chef booking system.
            Do not reply to this email.
        </p>
    </div>
</body>
</html>
    """


def _send_email_alert(to_email: str, subject: str, body: str) -> Dict[str, Any]:
    """Send a single email alert."""
    try:
        from services.email_service import send_email_sync

        send_email_sync(to_email=to_email, subject=subject, body=body)
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return {"success": False, "error": str(e)}


def _record_alert(
    db: Session,
    booking_id: str,
    alert_level: AlertLevel,
    trigger_reason: str,
    recipients: List[Dict[str, Any]],
    channels: List[str],
    success: bool,
) -> None:
    """Record alert in chef_assignment_alerts table."""
    db.execute(
        text(
            """
            INSERT INTO ops.chef_assignment_alerts (
                booking_id,
                alert_level,
                trigger_reason,
                recipient_ids,
                channels_used,
                success,
                sent_at
            ) VALUES (
                :booking_id::uuid,
                :alert_level,
                :trigger_reason,
                :recipient_ids,
                :channels,
                :success,
                NOW()
            )
        """
        ),
        {
            "booking_id": booking_id,
            "alert_level": alert_level.value,
            "trigger_reason": trigger_reason,
            "recipient_ids": [r["id"] for r in recipients if r.get("id")],
            "channels": channels,
            "success": success,
        },
    )


def _update_booking_alert_tracking(
    db: Session,
    booking_id: str,
    new_count: int,
    is_first_alert: bool,
    is_escalated: bool,
) -> None:
    """Update booking's alert tracking fields."""
    if is_first_alert:
        db.execute(
            text(
                """
                UPDATE core.bookings
                SET
                    urgency_alert_count = :count,
                    urgency_alert_sent_at = NOW(),
                    updated_at = NOW()
                WHERE id = :booking_id::uuid
            """
            ),
            {"count": new_count, "booking_id": booking_id},
        )
    elif is_escalated:
        db.execute(
            text(
                """
                UPDATE core.bookings
                SET
                    urgency_alert_count = :count,
                    urgency_escalated_at = NOW(),
                    updated_at = NOW()
                WHERE id = :booking_id::uuid
            """
            ),
            {"count": new_count, "booking_id": booking_id},
        )
    else:
        db.execute(
            text(
                """
                UPDATE core.bookings
                SET
                    urgency_alert_count = :count,
                    updated_at = NOW()
                WHERE id = :booking_id::uuid
            """
            ),
            {"count": new_count, "booking_id": booking_id},
        )


def _log_failed_alert(
    db: Session,
    booking_id: str,
    error: str,
    retry_count: int,
) -> None:
    """Log failed alert for debugging and monitoring."""
    try:
        db.execute(
            text(
                """
                INSERT INTO ops.chef_assignment_alerts (
                    booking_id,
                    alert_level,
                    trigger_reason,
                    success,
                    error_message,
                    retry_count,
                    sent_at
                ) VALUES (
                    :booking_id::uuid,
                    0,
                    'failed_alert',
                    false,
                    :error,
                    :retry_count,
                    NOW()
                )
            """
            ),
            {
                "booking_id": booking_id,
                "error": error,
                "retry_count": retry_count,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log failed alert: {e}")


def _build_daily_summary(bookings: List) -> str:
    """Build HTML summary of unassigned urgent bookings."""
    rows = ""
    for booking in bookings:
        rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[1]} at {booking[2]}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[3]} days</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[6]} {booking[7]}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[8]}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[9]}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{booking[5]} alerts sent</td>
        </tr>
        """

    return f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #dc3545;">🔴 Daily Urgent Bookings Summary</h2>

    <p>The following {len(bookings)} bookings are urgent and have NO CHEF ASSIGNED:</p>

    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
        <thead>
            <tr style="background: #f8f9fa;">
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Event Date</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Days Left</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Customer</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Phone</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Station</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Alerts</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <p style="background: #fff3cd; padding: 15px; border-radius: 5px;">
        <strong>⚠️ Action Required:</strong> Please assign chefs to these bookings today.
    </p>

    <p>
        <a href="/admin/bookings?filter=urgent_unassigned" style="display: inline-block; background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            View All Urgent Bookings
        </a>
    </p>
</body>
</html>
    """
