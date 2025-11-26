"""
Email Notification Service - WhatsApp Integration + Database Sync

Monitors email inboxes for new messages and sends WhatsApp alerts to admins.
Integrates with existing customer_email_monitor and payment_email_monitor.
NOW ALSO syncs emails to PostgreSQL database for fast access.

Features:
- Real-time email monitoring via IMAP IDLE
- WhatsApp notifications for new customer support emails
- **Database sync for all incoming emails**
- Deduplication (don't spam same email notification)
- Configurable notification hours (9am-9pm by default)
- Admin settings to enable/disable
- Priority-based alerts (high priority for urgent emails)

Architecture:
┌──────────────────┐
│  IONOS IMAP      │ → New customer email arrives
│  cs@myhibachi... │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│ EmailNotificationService     │ → IMAP IDLE callback
│ - handle_new_email()         │ → Sync to PostgreSQL ✨
│ - send_whatsapp_alert()      │
│ - deduplicate_notifications()│
│ - check_notification_hours() │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ WhatsAppNotificationService  │ → Send alert to admin
│ EmailSyncService             │ → Save to PostgreSQL ✨
│ - send_email_alert()         │
└──────────────────────────────┘

Usage:
    # In background worker/scheduler:
    from services.email_notification_service import EmailNotificationService

    service = EmailNotificationService()
    await service.check_and_notify()  # Run every 60 seconds
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from services.customer_email_monitor import customer_email_monitor
from services.payment_email_monitor import PaymentEmailMonitor
from services.whatsapp_notification_service import get_whatsapp_service, NotificationChannel
from services.email_sync_service import EmailSyncService

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailNotificationService:
    """
    Monitors email inboxes and sends WhatsApp notifications for new emails.

    Features:
    - Monitors cs@myhibachichef.com for customer support emails
    - Monitors myhibachichef@gmail.com for payment notifications
    - Sends WhatsApp alerts to admin team
    - Deduplicates notifications (tracks sent message IDs)
    - Respects quiet hours (configurable)
    - Priority-based alerting (urgent keywords trigger high-priority alerts)
    """

    # Urgent keywords that trigger high-priority alerts
    URGENT_KEYWORDS = [
        "urgent",
        "emergency",
        "asap",
        "complaint",
        "refund",
        "cancel",
        "problem",
        "issue",
        "help",
        "immediately",
    ]

    def __init__(self):
        """Initialize email notification service"""
        self.whatsapp = get_whatsapp_service()

        # Track sent notifications to avoid duplicates
        # Format: {message_id: timestamp}
        self._sent_notifications: dict[str, datetime] = {}

        # Notification settings
        self.enabled = True  # Can be toggled via admin settings
        self.notification_start_hour = 9  # 9am
        self.notification_end_hour = 21  # 9pm
        self.check_interval_seconds = 60  # Check every 60 seconds

        # Admin phone numbers (comma-separated in env)
        admin_phones = settings.BUSINESS_PHONE or "+19167408768"
        self.admin_phones = [p.strip() for p in admin_phones.split(",")]

        logger.info("✅ EmailNotificationService initialized")
        logger.info(f"   - Notification hours: {self.notification_start_hour}:00 - {self.notification_end_hour}:00")
        logger.info(f"   - Check interval: {self.check_interval_seconds}s")
        logger.info(f"   - Admin phones: {len(self.admin_phones)}")

    def is_within_notification_hours(self) -> bool:
        """Check if current time is within notification hours"""
        now = datetime.now(timezone.utc)
        current_hour = now.hour

        # Simple check: between start and end hour
        return self.notification_start_hour <= current_hour < self.notification_end_hour

    def is_urgent_email(self, subject: str, body: str) -> bool:
        """Check if email contains urgent keywords"""
        search_text = f"{subject} {body}".lower()
        return any(keyword in search_text for keyword in self.URGENT_KEYWORDS)

    def should_notify(self, message_id: str) -> bool:
        """
        Check if we should send notification for this email.

        Returns False if:
        - Notification already sent for this message_id
        - Outside notification hours (unless urgent)
        - Service is disabled
        """
        # Check if disabled
        if not self.enabled:
            logger.debug("Email notifications disabled")
            return False

        # Check if already notified
        if message_id in self._sent_notifications:
            logger.debug(f"Already notified for message_id: {message_id}")
            return False

        # Allow notifications (will check urgency in send method)
        return True

    def cleanup_old_notifications(self, hours: int = 24):
        """Remove notification records older than N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Remove old entries
        old_count = len(self._sent_notifications)
        self._sent_notifications = {
            msg_id: ts
            for msg_id, ts in self._sent_notifications.items()
            if ts > cutoff
        }

        removed = old_count - len(self._sent_notifications)
        if removed > 0:
            logger.info(f"Cleaned up {removed} old notification records")

    async def send_email_alert(
        self,
        message_id: str,
        from_address: str,
        from_name: Optional[str],
        subject: str,
        preview: str,
        is_urgent: bool = False,
        inbox: str = "customer_support",
    ) -> dict[str, Any]:
        """
        Send WhatsApp alert for new email.

        Args:
            message_id: Email message ID
            from_address: Sender email
            from_name: Sender name
            subject: Email subject
            preview: First 100 characters of email body
            is_urgent: High-priority alert
            inbox: "customer_support" or "payments"

        Returns:
            Dict with notification result
        """
        # Check notification hours (urgent emails always notify)
        if not is_urgent and not self.is_within_notification_hours():
            logger.info(f"Outside notification hours, skipping: {message_id}")
            return {"success": False, "reason": "outside_hours"}

        # Build notification message
        emoji = "🚨" if is_urgent else "📧"
        priority = "URGENT" if is_urgent else "NEW"
        inbox_label = "Customer Support" if inbox == "customer_support" else "Payment"

        sender = from_name or from_address

        message_lines = [
            f"{emoji} {priority} EMAIL - {inbox_label}",
            "",
            f"From: {sender}",
            f"Email: {from_address}",
            f"Subject: {subject[:100]}",
            "",
            f"Preview:",
            f"{preview[:150]}{'...' if len(preview) > 150 else ''}",
            "",
            f"🔗 View in Admin:",
            f"https://admin.myhibachichef.com/emails?tab={inbox}&id={message_id}",
        ]

        notification_message = "\n".join(message_lines)

        # Send to all admin phones
        results = []
        for admin_phone in self.admin_phones:
            try:
                result = await self.whatsapp._send_whatsapp(admin_phone, notification_message)

                if not result["success"]:
                    # Fallback to SMS
                    result = await self.whatsapp._send_sms(admin_phone, notification_message)

                results.append(result)
                logger.info(
                    f"Email alert sent to {admin_phone}: {result.get('channel')} "
                    f"(message_id: {message_id})"
                )

            except Exception as e:
                logger.error(f"Failed to send email alert to {admin_phone}: {e}")
                results.append({"success": False, "error": str(e)})

        # Mark as notified
        self._sent_notifications[message_id] = datetime.now(timezone.utc)

        # Return combined result
        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": success_count > 0,
            "notified_count": success_count,
            "total_admins": len(self.admin_phones),
            "is_urgent": is_urgent,
            "message_id": message_id,
        }

    async def check_customer_support_emails(self) -> list[dict[str, Any]]:
        """
        Check for new customer support emails and send notifications.

        Returns:
            List of notification results
        """
        try:
            # Connect to IONOS IMAP
            if not customer_email_monitor.connect():
                logger.error("Failed to connect to customer email IMAP")
                return []

            # Fetch unread emails (don't mark as read)
            unread_emails = customer_email_monitor.fetch_unread_emails(mark_as_read=False)

            logger.info(f"Found {len(unread_emails)} unread customer support emails")

            # Send notifications for new emails
            notifications = []
            for email in unread_emails:
                message_id = email.get("message_id", "")

                # Check if should notify
                if not self.should_notify(message_id):
                    continue

                # Extract email data
                from_address = email.get("from_address", "unknown")
                from_name = email.get("from_name")
                subject = email.get("subject", "(No Subject)")
                text_body = email.get("text_body", "")
                html_body = email.get("html_body", "")

                # Use text body for preview, fallback to HTML
                body = text_body or html_body or ""
                preview = body[:200]  # First 200 chars

                # Check if urgent
                is_urgent = self.is_urgent_email(subject, body)

                # Send notification
                result = await self.send_email_alert(
                    message_id=message_id,
                    from_address=from_address,
                    from_name=from_name,
                    subject=subject,
                    preview=preview,
                    is_urgent=is_urgent,
                    inbox="customer_support",
                )

                notifications.append(result)

            # Disconnect
            customer_email_monitor.disconnect()

            return notifications

        except Exception as e:
            logger.exception(f"Error checking customer support emails: {e}")
            return []

    async def check_payment_emails(self) -> list[dict[str, Any]]:
        """
        Check for new payment notification emails.

        Note: Payment emails are already handled by payment_matcher_service,
        so this is optional. Only enable if you want WhatsApp alerts for ALL
        payment emails (not just matched ones).

        Returns:
            List of notification results
        """
        # For now, skip payment email notifications
        # (payment_matcher_service already handles this)
        logger.debug("Payment email notifications handled by payment_matcher_service")
        return []

    async def check_and_notify(self) -> dict[str, Any]:
        """
        Main method: Check all inboxes and send notifications.

        This should be called by a background scheduler every 60 seconds.

        Returns:
            Summary of notifications sent
        """
        logger.info("🔍 Checking for new emails...")

        # Cleanup old notification records
        self.cleanup_old_notifications(hours=24)

        # Check customer support emails
        customer_notifications = await self.check_customer_support_emails()

        # Check payment emails (optional)
        payment_notifications = await self.check_payment_emails()

        # Summary
        total_notifications = len(customer_notifications) + len(payment_notifications)

        if total_notifications > 0:
            logger.info(f"✅ Sent {total_notifications} email notifications")
        else:
            logger.debug("No new emails requiring notification")

        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "customer_support_notifications": len(customer_notifications),
            "payment_notifications": len(payment_notifications),
            "total_notifications": total_notifications,
            "results": customer_notifications + payment_notifications,
        }

    async def handle_new_email(
        self,
        email_data: dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> dict[str, Any]:
        """
        Handle new email from IMAP IDLE callback.

        This is called by email_idle_monitor when a new email arrives.

        **NEW**: Now syncs email to PostgreSQL database for fast access!

        Args:
            email_data: Email data from IMAP IDLE monitor
                {
                    'message_id': str,
                    'from_address': str,
                    'from_name': str,
                    'subject': str,
                    'text_body': str,
                    'html_body': str,
                    'received_at': datetime,
                    'inbox': 'customer_support' | 'payments',
                    'to_addresses': List[str],  # Optional
                    'cc_addresses': List[str],  # Optional
                    'has_attachments': bool,   # Optional
                    'attachments': List[dict], # Optional
                    'labels': List[str],       # Optional
                }
            db: AsyncSession for database operations (optional, required for sync)

        Returns:
            Notification result + sync result
        """
        message_id = email_data.get("message_id", "")

        # ✨ NEW: Sync email to PostgreSQL database
        sync_result = None
        if db is not None:
            try:
                sync_service = EmailSyncService(db)
                sync_result = await sync_service.sync_email_from_idle(email_data)
                logger.info(f"✅ Email synced to database: {sync_result.get('action', 'unknown')}")
            except Exception as e:
                logger.exception(f"❌ Failed to sync email to database: {e}")
                sync_result = {"success": False, "error": str(e)}

        # Check if should notify
        if not self.should_notify(message_id):
            logger.debug(f"Skipping notification for {message_id}")
            return {
                "success": False,
                "reason": "already_notified",
                "sync_result": sync_result
            }

        # Extract email data
        from_address = email_data.get("from_address", "unknown")
        from_name = email_data.get("from_name")
        subject = email_data.get("subject", "(No Subject)")
        text_body = email_data.get("text_body", "")
        html_body = email_data.get("html_body", "")
        inbox = email_data.get("inbox", "customer_support")

        # Use text body for preview, fallback to HTML
        body = text_body or html_body or ""
        preview = body[:200]  # First 200 chars

        # Check if urgent
        is_urgent = self.is_urgent_email(subject, body)

        # Send notification
        result = await self.send_email_alert(
            message_id=message_id,
            from_address=from_address,
            from_name=from_name,
            subject=subject,
            preview=preview,
            is_urgent=is_urgent,
            inbox=inbox,
        )

        # Include sync result
        result["sync_result"] = sync_result

        return result

    async def run_scheduler(self):
        """
        DEPRECATED: Use IMAP IDLE monitors instead.

        This method is kept for backward compatibility but should not be used.
        The new IMAP IDLE approach uses push notifications via handle_new_email().
        """
        logger.warning("⚠️  run_scheduler() is deprecated. Use IMAP IDLE monitors instead.")
        logger.info(f"📬 Email notification scheduler started (interval: {self.check_interval_seconds}s)")

        while True:
            try:
                await self.check_and_notify()
            except Exception as e:
                logger.exception(f"Error in email notification scheduler: {e}")

            # Wait before next check
            await asyncio.sleep(self.check_interval_seconds)


# Module-level instance
_email_notification_service: Optional[EmailNotificationService] = None


def get_email_notification_service() -> EmailNotificationService:
    """Get or create email notification service instance"""
    global _email_notification_service
    if _email_notification_service is None:
        _email_notification_service = EmailNotificationService()
    return _email_notification_service


# Convenience functions
async def check_and_notify() -> dict[str, Any]:
    """Convenience function to check emails and send notifications"""
    service = get_email_notification_service()
    return await service.check_and_notify()


async def start_email_notification_scheduler():
    """Start background email notification scheduler"""
    service = get_email_notification_service()
    await service.run_scheduler()


if __name__ == "__main__":
    # Test email notification service
    async def test():
        service = EmailNotificationService()

        # Test notification
        result = await service.send_email_alert(
            message_id="test-123",
            from_address="customer@example.com",
            from_name="John Doe",
            subject="Question about booking",
            preview="Hi, I have a question about my upcoming hibachi booking...",
            is_urgent=False,
            inbox="customer_support",
        )

        print("Notification result:", result)

    asyncio.run(test())
