"""
Notification Service - REFACTORED

This file previously contained WhatsApp Business API integration.
WhatsApp business-initiated messaging requires pre-approved templates,
which is not suitable for our internal staff notification needs.

DECISION:
- WhatsApp sending functionality has been REMOVED
- For staff notifications, use StaffNotificationService (email-based)
- Meta webhook is KEPT for Instagram DM and Facebook Messenger (AI chat)
- RingCentral SMS can still be used for customer notifications if needed

MIGRATION GUIDE:
    # Old code:
    from services.whatsapp_notification_service import get_whatsapp_service
    service = get_whatsapp_service()
    await service.send_payment_notification(...)

    # New code:
    from services.staff_notification_service import get_staff_notification_service
    service = get_staff_notification_service()
    await service.notify_payment_received(...)

For customer-facing SMS, use RingCentral directly:
    from services.ringcentral_service import get_ringcentral_service
    sms_service = get_ringcentral_service()
    await sms_service.send_sms(to, message)
"""

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    EMAIL = "email"  # Primary: IONOS SMTP via StaffNotificationService
    SMS = "sms"  # Customer-facing via RingCentral
    MESSENGER = "messenger"  # Facebook Messenger (AI chat)
    INSTAGRAM = "instagram"  # Instagram DM (AI chat)
    WHATSAPP = "whatsapp"  # DEPRECATED - redirects to email
    FAILED = "failed"


class WhatsAppNotificationService:
    """
    DEPRECATED - This service now redirects to StaffNotificationService.

    Kept for backward compatibility with existing code that imports this class.
    All notification methods redirect to email-based notifications.

    For new code, use StaffNotificationService directly.
    """

    def __init__(self):
        """Initialize - loads the new email-based service"""
        self.client = None  # No WhatsApp client - we use email now
        self._staff_service = None
        logger.info(
            "WhatsAppNotificationService initialized - " "notifications will be sent via email"
        )

    @property
    def staff_service(self):
        """Lazy load staff notification service"""
        if self._staff_service is None:
            from services.staff_notification_service import get_staff_notification_service

            self._staff_service = get_staff_notification_service()
        return self._staff_service

    async def send_payment_notification(
        self,
        phone_number: str,
        customer_name: str,
        amount: float,
        provider: str,
        sender_name: str | None = None,
        match_score: int = 0,
        booking_id: int | None = None,
        admin_group: bool = True,
    ) -> dict[str, Any]:
        """
        REDIRECTED to email notification.

        Original: Sent WhatsApp message to admin
        Now: Sends email notification via StaffNotificationService
        """
        logger.info(
            f"Payment notification redirected to email: "
            f"${amount:.2f} from {customer_name} via {provider}"
        )

        result = await self.staff_service.notify_payment_received(
            booking_id=str(booking_id) if booking_id else "N/A",
            customer_name=customer_name,
            amount=amount,
            payment_method=provider,
        )

        return {
            "success": result.get("success", False),
            "channel": NotificationChannel.EMAIL,
            "message_id": None,
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Redirected from WhatsApp to email notification",
        }

    async def send_booking_confirmation(
        self,
        phone_number: str,
        customer_name: str,
        event_date: str,
        event_time: str,
        guest_count: int,
        venue_address: str,
        total_amount: float,
        deposit_paid: float,
        balance_due: float,
    ) -> dict[str, Any]:
        """
        REDIRECTED to email notification.

        Original: Sent WhatsApp template message to customer
        Now: Sends email notification (staff only - customer gets separate email)
        """
        logger.info(
            f"Booking confirmation notification redirected to email: "
            f"{customer_name} on {event_date}"
        )

        result = await self.staff_service.notify_new_booking(
            booking_id="N/A",  # Will be populated by caller if needed
            customer_name=customer_name,
            event_date=event_date,
            event_time=event_time,
            guest_count=guest_count,
        )

        return {
            "success": result.get("success", False),
            "channel": NotificationChannel.EMAIL,
            "message_id": None,
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Redirected from WhatsApp to email notification",
        }

    async def send_manual_review_alert(
        self,
        alert_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        REDIRECTED to email notification.

        Original: Sent WhatsApp alert for manual review needed
        Now: Sends escalation email via StaffNotificationService
        """
        logger.info("Manual review alert redirected to email")

        result = await self.staff_service.notify_escalation(
            escalation_id=str(alert_data.get("id", "N/A")),
            customer_phone=alert_data.get("phone", "Unknown"),
            reason=alert_data.get("reason", "Manual review required"),
            priority_level=alert_data.get("priority", "normal"),
        )

        return {
            "success": result.get("success", False),
            "channel": NotificationChannel.EMAIL,
            "message_id": None,
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def send_escalation_alert(
        self,
        escalation_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        REDIRECTED to email notification.

        Original: Sent WhatsApp alert for escalation
        Now: Sends escalation email via StaffNotificationService
        """
        logger.info("Escalation alert redirected to email")

        result = await self.staff_service.notify_escalation(
            escalation_id=str(escalation_data.get("id", "N/A")),
            customer_phone=escalation_data.get("phone", "Unknown"),
            reason=escalation_data.get("reason", "Escalation required"),
            priority_level="high",
        )

        return {
            "success": result.get("success", False),
            "channel": NotificationChannel.EMAIL,
            "message_id": None,
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: list | None = None,
    ) -> dict[str, Any]:
        """
        REMOVED - WhatsApp template messages no longer supported.

        For customer communication, use email or RingCentral SMS.
        """
        logger.warning(
            f"WhatsApp template message skipped (no longer supported): "
            f"template={template_name}, to={to}"
        )

        return {
            "success": False,
            "channel": NotificationChannel.FAILED,
            "error": "WhatsApp template messages removed. Use email or SMS instead.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _send_whatsapp(self, to: str, message: str) -> dict[str, Any]:
        """
        REMOVED - WhatsApp freeform messages no longer supported.

        For customer communication, use email or RingCentral SMS.
        """
        logger.warning(f"WhatsApp message skipped (no longer supported): to={to}")

        return {
            "success": False,
            "channel": NotificationChannel.FAILED,
            "error": "WhatsApp messages removed. Use email or SMS instead.",
        }

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number - kept for compatibility"""
        # Remove all non-digits
        digits = "".join(filter(str.isdigit, phone))

        # US numbers: ensure 11 digits starting with 1
        if len(digits) == 10:
            digits = "1" + digits

        return digits


# Global service instance
_notification_service: WhatsAppNotificationService | None = None


def get_whatsapp_service() -> WhatsAppNotificationService:
    """
    Get the notification service instance.

    DEPRECATED: Returns a service that redirects to email.
    For new code, use get_staff_notification_service() directly.
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = WhatsAppNotificationService()
    return _notification_service
