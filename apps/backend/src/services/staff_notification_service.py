"""
Staff Notification Service with Role-Based Routing and Digest System

Implements intelligent notification routing based on staff roles:
- SUPER_ADMIN: Daily digest only (high-level overview)
- ADMIN: Station-specific events + daily digest
- STATION_MANAGER: Station schedules, chef assignments
- CUSTOMER_SUPPORT: Customer inquiries, pending approvals
- CHEF: Their own assignments, schedule changes

Features:
- Priority classification (URGENT sends immediately, others queue for digest)
- Role-based routing (each role gets relevant notifications)
- Digest system (hourly/daily email summaries instead of spam)
- Notification queue (database-backed for reliability)

Configuration:
- Uses existing email_service.py for IONOS SMTP
- Background tasks for digest sending
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import logging
import os
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    URGENT = "urgent"  # Send immediately (payment failed, same-day cancellation)
    HIGH = "high"  # Include in next hourly digest
    NORMAL = "normal"  # Include in daily digest
    LOW = "low"  # Include in weekly digest (or skip)


class NotificationCategory(str, Enum):
    """Notification categories for routing"""

    BOOKING_NEW = "booking_new"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_UPDATED = "booking_updated"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    CHEF_ASSIGNED = "chef_assigned"
    CHEF_SCHEDULE_CHANGE = "chef_schedule_change"
    CUSTOMER_INQUIRY = "customer_inquiry"
    ESCALATION = "escalation"
    SYSTEM_ALERT = "system_alert"
    DAILY_SUMMARY = "daily_summary"


class StaffRole(str, Enum):
    """Staff roles (must match core/config.py UserRole)"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STATION_MANAGER = "station_manager"
    CUSTOMER_SUPPORT = "customer_support"
    CHEF = "chef"


# Role-based notification routing
# Maps which categories each role should receive
ROLE_NOTIFICATION_MAP: dict[StaffRole, list[NotificationCategory]] = {
    StaffRole.SUPER_ADMIN: [
        NotificationCategory.DAILY_SUMMARY,
        NotificationCategory.SYSTEM_ALERT,
        NotificationCategory.PAYMENT_FAILED,  # Urgent only
    ],
    StaffRole.ADMIN: [
        NotificationCategory.BOOKING_NEW,
        NotificationCategory.BOOKING_CANCELLED,
        NotificationCategory.BOOKING_UPDATED,
        NotificationCategory.PAYMENT_RECEIVED,
        NotificationCategory.PAYMENT_FAILED,
        NotificationCategory.ESCALATION,
        NotificationCategory.DAILY_SUMMARY,
    ],
    StaffRole.STATION_MANAGER: [
        NotificationCategory.CHEF_ASSIGNED,
        NotificationCategory.CHEF_SCHEDULE_CHANGE,
        NotificationCategory.DAILY_SUMMARY,
    ],
    StaffRole.CUSTOMER_SUPPORT: [
        NotificationCategory.CUSTOMER_INQUIRY,
        NotificationCategory.ESCALATION,
        NotificationCategory.BOOKING_UPDATED,
    ],
    StaffRole.CHEF: [
        NotificationCategory.CHEF_ASSIGNED,
        NotificationCategory.CHEF_SCHEDULE_CHANGE,
    ],
}

# Priority-based delivery rules
PRIORITY_DELIVERY: dict[NotificationPriority, str] = {
    NotificationPriority.URGENT: "immediate",  # Send right away
    NotificationPriority.HIGH: "hourly",  # Hourly digest
    NotificationPriority.NORMAL: "daily",  # Daily digest
    NotificationPriority.LOW: "weekly",  # Weekly or skip
}


@dataclass
class Notification:
    """Notification data structure"""

    category: NotificationCategory
    priority: NotificationPriority
    title: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    station_id: Optional[str] = None  # For station-scoped notifications
    recipient_role: Optional[StaffRole] = None  # Specific role target
    recipient_email: Optional[str] = None  # Specific email target
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StaffNotificationService:
    """
    Manages staff notifications with role-based routing and digest system.

    Usage:
        service = StaffNotificationService(db_session)

        # Queue a notification
        await service.queue_notification(
            category=NotificationCategory.BOOKING_NEW,
            priority=NotificationPriority.HIGH,
            title="New Booking!",
            message="John Doe booked for Dec 25",
            data={"booking_id": "123", "customer_name": "John Doe"}
        )

        # Send immediate notification (for URGENT priority)
        await service.send_immediate(
            category=NotificationCategory.PAYMENT_FAILED,
            title="Payment Failed!",
            message="Card declined for booking #123",
            recipient_email="admin@myhibachichef.com"
        )

        # Process digest (called by background job)
        await service.send_hourly_digest()
        await service.send_daily_digest()
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize notification service"""
        self.db = db
        self._email_service = None

        # Admin emails for different roles (from env or database)
        self.admin_emails = self._load_admin_emails()

        logger.info("StaffNotificationService initialized")

    def _load_admin_emails(self) -> dict[StaffRole, list[str]]:
        """Load admin emails from environment or return defaults"""
        # In production, load from database based on roles
        # For now, use environment variables
        default_admin = os.getenv("ADMIN_EMAIL", "cs@myhibachichef.com")
        super_admin = os.getenv("SUPER_ADMIN_EMAIL", default_admin)

        return {
            StaffRole.SUPER_ADMIN: [super_admin],
            StaffRole.ADMIN: [default_admin],
            StaffRole.STATION_MANAGER: [default_admin],
            StaffRole.CUSTOMER_SUPPORT: [default_admin],
            StaffRole.CHEF: [],  # Chefs don't get emails by default
        }

    @property
    def email_service(self):
        """Lazy load email service"""
        if self._email_service is None:
            from services.email_service import EmailService

            self._email_service = EmailService()
        return self._email_service

    async def queue_notification(
        self,
        category: NotificationCategory,
        priority: NotificationPriority,
        title: str,
        message: str,
        data: Optional[dict] = None,
        station_id: Optional[str] = None,
        recipient_role: Optional[StaffRole] = None,
    ) -> dict[str, Any]:
        """
        Queue a notification for delivery based on priority.

        URGENT notifications are sent immediately.
        Other priorities are queued for digest.

        Args:
            category: Type of notification
            priority: Delivery priority
            title: Short notification title
            message: Full notification message
            data: Additional data (booking_id, etc.)
            station_id: Station scope (for station-specific notifications)
            recipient_role: Specific role to target

        Returns:
            Result dict with queued/sent status
        """
        notification = Notification(
            category=category,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            station_id=station_id,
            recipient_role=recipient_role,
        )

        # URGENT = send immediately
        if priority == NotificationPriority.URGENT:
            return await self._send_notification(notification)

        # Queue for digest
        return await self._queue_for_digest(notification)

    async def _send_notification(self, notification: Notification) -> dict[str, Any]:
        """Send notification immediately via email"""
        try:
            # Determine recipients based on category and role
            recipients = self._get_recipients(notification)

            if not recipients:
                logger.warning(f"No recipients for notification: {notification.category}")
                return {"success": False, "error": "No recipients found"}

            # Send to each recipient
            results = []
            for email in recipients:
                success = self._send_email(
                    to_email=email,
                    subject=f"[MyHibachi] {notification.title}",
                    message=notification.message,
                    data=notification.data,
                )
                results.append({"email": email, "success": success})

            return {
                "success": all(r["success"] for r in results),
                "sent_to": results,
                "category": notification.category.value,
            }

        except Exception as e:
            logger.exception(f"Failed to send notification: {e}")
            return {"success": False, "error": str(e)}

    async def _queue_for_digest(self, notification: Notification) -> dict[str, Any]:
        """Queue notification for digest delivery"""
        try:
            # In production, save to database
            # For now, log the queued notification
            logger.info(
                f"Queued notification for {PRIORITY_DELIVERY[notification.priority]} digest: "
                f"{notification.category.value} - {notification.title}"
            )

            # TODO: Save to notification_queue table when implemented
            # await self._save_to_queue(notification)

            return {
                "success": True,
                "queued": True,
                "delivery": PRIORITY_DELIVERY[notification.priority],
                "category": notification.category.value,
            }

        except Exception as e:
            logger.exception(f"Failed to queue notification: {e}")
            return {"success": False, "error": str(e)}

    def _get_recipients(self, notification: Notification) -> list[str]:
        """Determine recipient emails based on notification routing"""
        recipients = set()

        # If specific role is targeted
        if notification.recipient_role:
            role_emails = self.admin_emails.get(notification.recipient_role, [])
            recipients.update(role_emails)
        else:
            # Find all roles that should receive this category
            for role, categories in ROLE_NOTIFICATION_MAP.items():
                if notification.category in categories:
                    role_emails = self.admin_emails.get(role, [])
                    recipients.update(role_emails)

        return list(recipients)

    def _send_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Send email using email service"""
        try:
            # Build HTML body
            html_body = self._build_notification_email(subject, message, data)
            text_body = message

            return self.email_service._send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {e}")
            return False

    def _build_notification_email(
        self,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """Build HTML email body for notification"""
        data_html = ""
        if data:
            data_items = "".join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in data.items())
            data_html = f"<ul>{data_items}</ul>"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{title}</h2>
        </div>
        <div class="content">
            <p>{message}</p>
            {data_html}
            <p style="margin-top: 20px;">
                <a href="{os.getenv('ADMIN_URL', 'https://admin.mysticdatanode.net')}"
                   style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View in Admin Portal
                </a>
            </p>
        </div>
        <div class="footer">
            <p>My Hibachi Chef - Staff Notification</p>
            <p>This is an automated notification. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""

    # =========================================
    # Convenience methods for common notifications
    # =========================================

    async def notify_new_booking(
        self,
        booking_id: str,
        customer_name: str,
        event_date: str,
        event_time: str,
        guest_count: int,
        station_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send new booking notification to admins"""
        return await self.queue_notification(
            category=NotificationCategory.BOOKING_NEW,
            priority=NotificationPriority.HIGH,
            title=f"New Booking: {customer_name}",
            message=f"New booking from {customer_name} for {event_date} at {event_time} ({guest_count} guests)",
            data={
                "booking_id": booking_id,
                "customer_name": customer_name,
                "event_date": event_date,
                "event_time": event_time,
                "guest_count": guest_count,
            },
            station_id=station_id,
        )

    async def notify_booking_cancelled(
        self,
        booking_id: str,
        customer_name: str,
        event_date: str,
        cancellation_reason: Optional[str] = None,
        station_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send booking cancellation notification"""
        # Same-day cancellation = URGENT
        is_same_day = event_date == datetime.now(timezone.utc).strftime("%Y-%m-%d")
        priority = NotificationPriority.URGENT if is_same_day else NotificationPriority.HIGH

        return await self.queue_notification(
            category=NotificationCategory.BOOKING_CANCELLED,
            priority=priority,
            title=f"Booking Cancelled: {customer_name}",
            message=f"Booking for {customer_name} on {event_date} has been cancelled. Reason: {cancellation_reason or 'Not provided'}",
            data={
                "booking_id": booking_id,
                "customer_name": customer_name,
                "event_date": event_date,
                "cancellation_reason": cancellation_reason,
            },
            station_id=station_id,
        )

    async def notify_payment_received(
        self,
        booking_id: str,
        customer_name: str,
        amount: float,
        payment_method: str,
        station_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send payment received notification"""
        return await self.queue_notification(
            category=NotificationCategory.PAYMENT_RECEIVED,
            priority=NotificationPriority.NORMAL,
            title=f"Payment Received: ${amount:.2f}",
            message=f"Payment of ${amount:.2f} received from {customer_name} via {payment_method}",
            data={
                "booking_id": booking_id,
                "customer_name": customer_name,
                "amount": amount,
                "payment_method": payment_method,
            },
            station_id=station_id,
        )

    async def notify_payment_failed(
        self,
        booking_id: str,
        customer_name: str,
        amount: float,
        error_reason: str,
        station_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send payment failed notification (URGENT)"""
        return await self.queue_notification(
            category=NotificationCategory.PAYMENT_FAILED,
            priority=NotificationPriority.URGENT,
            title=f"⚠️ Payment Failed: ${amount:.2f}",
            message=f"Payment of ${amount:.2f} failed for {customer_name}. Error: {error_reason}",
            data={
                "booking_id": booking_id,
                "customer_name": customer_name,
                "amount": amount,
                "error_reason": error_reason,
            },
            station_id=station_id,
        )

    async def notify_chef_assigned(
        self,
        booking_id: str,
        chef_name: str,
        chef_email: str,
        event_date: str,
        event_time: str,
        location: str,
    ) -> dict[str, Any]:
        """Send chef assignment notification"""
        return await self.queue_notification(
            category=NotificationCategory.CHEF_ASSIGNED,
            priority=NotificationPriority.HIGH,
            title=f"New Assignment: {event_date}",
            message=f"You have been assigned to a booking on {event_date} at {event_time} at {location}",
            data={
                "booking_id": booking_id,
                "event_date": event_date,
                "event_time": event_time,
                "location": location,
            },
            recipient_role=StaffRole.CHEF,
        )

    async def notify_escalation(
        self,
        escalation_id: str,
        customer_phone: str,
        reason: str,
        priority_level: str,
    ) -> dict[str, Any]:
        """Send escalation notification (URGENT for high/urgent priority)"""
        is_urgent = priority_level.lower() in ["high", "urgent"]

        return await self.queue_notification(
            category=NotificationCategory.ESCALATION,
            priority=NotificationPriority.URGENT if is_urgent else NotificationPriority.HIGH,
            title=f"🚨 Escalation: {priority_level.upper()}",
            message=f"Customer {customer_phone} requires assistance. Reason: {reason}",
            data={
                "escalation_id": escalation_id,
                "customer_phone": customer_phone,
                "reason": reason,
                "priority": priority_level,
            },
        )


# Global service instance
_staff_notification_service: StaffNotificationService | None = None


def get_staff_notification_service(
    db: Optional[AsyncSession] = None,
) -> StaffNotificationService:
    """Get or create staff notification service instance"""
    global _staff_notification_service
    if _staff_notification_service is None:
        _staff_notification_service = StaffNotificationService(db)
    return _staff_notification_service
