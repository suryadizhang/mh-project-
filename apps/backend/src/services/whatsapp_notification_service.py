"""
Meta WhatsApp Business API Notification Service

Implements WhatsApp Business API integration for payment notifications
using the official Meta Cloud API.

Features:
- WhatsApp Business API (Official Meta Cloud API)
- Fallback to RingCentral SMS if WhatsApp fails
- Template message support
- Delivery tracking
- Group notifications
- Messenger and Instagram DM support

Message Flow:
Payment Detected → Try WhatsApp → If fail, send SMS via RingCentral → Log result

Environment Variables Required:
- META_APP_ID: Meta App ID
- META_APP_SECRET: Meta App Secret
- META_PAGE_ACCESS_TOKEN: Permanent Page Access Token
- META_VERIFY_TOKEN: Webhook verification token
- META_PHONE_NUMBER_ID: WhatsApp Business Phone Number ID
- RC_SMS_FROM: RingCentral fallback SMS number
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"
    FAILED = "failed"


class WhatsAppNotificationService:
    """
    Handles WhatsApp notifications via Meta Cloud API.

    Features:
    - WhatsApp via Meta Cloud API (official)
    - Automatic fallback to RingCentral SMS
    - Template support
    - Delivery tracking
    - Group notifications

    Environment Variables Required:
    - META_PAGE_ACCESS_TOKEN: Long-lived page access token
    - META_PHONE_NUMBER_ID: WhatsApp Business phone number ID
    - RC_SMS_FROM: RingCentral fallback SMS number
    """

    # Meta WhatsApp Cloud API base URL
    META_API_BASE = "https://graph.facebook.com/v21.0"

    def __init__(self):
        """Initialize Meta WhatsApp notification service"""
        try:
            # Get Meta credentials
            self.access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
            self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
            self.app_id = os.getenv("META_APP_ID")

            if not self.access_token or not self.phone_number_id:
                logger.warning(
                    "Meta WhatsApp credentials not found - "
                    "notifications will use RingCentral SMS only"
                )
                self.client = None
            else:
                self.client = httpx.AsyncClient(timeout=30.0)
                logger.info("Meta WhatsApp client initialized successfully")

            # RingCentral fallback
            self.sms_from = os.getenv("RC_SMS_FROM", "+19167408768")

            logger.info(f"WhatsApp Phone Number ID: {self.phone_number_id}")
            logger.info(f"SMS fallback from: {self.sms_from}")

        except Exception as e:
            logger.exception(f"Failed to initialize WhatsApp service: {e}")
            self.client = None

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
        Send payment notification via WhatsApp (with SMS fallback).

        Args:
            phone_number: Customer phone (format: +1234567890)
            customer_name: Name of customer who booked
            amount: Payment amount
            provider: Payment provider (Stripe, Venmo, Zelle, etc.)
            sender_name: Name of person who sent payment
            match_score: Confidence score (0-225)
            booking_id: Associated booking ID
            admin_group: Also send to admin group/number

        Returns:
            Dict with delivery status and details
        """
        result = {
            "success": False,
            "channel": NotificationChannel.FAILED,
            "message_id": None,
            "error": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)

            # Build message
            message = self._build_payment_message(
                customer_name=customer_name,
                amount=amount,
                provider=provider,
                sender_name=sender_name,
                match_score=match_score,
                booking_id=booking_id,
            )

            # Try WhatsApp first
            if self.client and self.access_token and self.phone_number_id:
                whatsapp_result = await self._send_whatsapp(formatted_phone, message)

                if whatsapp_result["success"]:
                    result.update(whatsapp_result)
                    logger.info(
                        f"WhatsApp sent to {formatted_phone}: {whatsapp_result['message_id']}"
                    )
                else:
                    # Fallback to RingCentral SMS
                    logger.warning(
                        f"WhatsApp failed, falling back to RingCentral SMS: "
                        f"{whatsapp_result['error']}"
                    )
                    sms_result = await self._send_ringcentral_sms(formatted_phone, message)
                    result.update(sms_result)
            else:
                # No Meta client, use RingCentral SMS directly
                sms_result = await self._send_ringcentral_sms(formatted_phone, message)
                result.update(sms_result)

            # Send to admin if enabled
            if admin_group:
                admin_phone = os.getenv("ON_CALL_ADMIN_PHONE") or os.getenv(
                    "BUSINESS_PHONE", "+19167408768"
                )
                await self._send_ringcentral_sms(admin_phone, f"[ADMIN] {message}")

            return result

        except Exception as e:
            logger.error(f"Payment notification failed: {e}", exc_info=True)
            result["error"] = str(e)
            return result

    async def _send_whatsapp(self, to: str, message: str) -> dict[str, Any]:
        """Send WhatsApp message via Meta Cloud API"""
        try:
            if not self.client:
                return {"success": False, "error": "Meta WhatsApp client not initialized"}

            # Remove + from phone number for Meta API
            phone_number = to.lstrip("+")

            # Meta Cloud API endpoint
            url = f"{self.META_API_BASE}/{self.phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # Send text message
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "text",
                "text": {"preview_url": True, "body": message},
            }

            response = await self.client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                return {
                    "success": True,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_id": message_id,
                    "status": "sent",
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logger.warning(f"Meta WhatsApp API error: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            logger.exception(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Send WhatsApp template message via Meta Cloud API.

        Template messages must be pre-approved by Meta.
        Use this for marketing, notifications, and transactional messages.

        Args:
            to: Recipient phone number (+1234567890)
            template_name: Name of approved template
            language_code: Template language (default: en_US)
            components: Optional template components (header, body, buttons)

        Returns:
            Dict with delivery status
        """
        try:
            if not self.client:
                return {"success": False, "error": "Meta WhatsApp client not initialized"}

            phone_number = to.lstrip("+")
            url = f"{self.META_API_BASE}/{self.phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                },
            }

            if components:
                payload["template"]["components"] = components

            response = await self.client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                return {
                    "success": True,
                    "channel": NotificationChannel.WHATSAPP,
                    "message_id": message_id,
                    "status": "sent",
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except Exception as e:
            logger.exception(f"Template message failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_ringcentral_sms(self, to: str, message: str) -> dict[str, Any]:
        """Fallback to RingCentral SMS"""
        try:
            # Import RingCentral service
            from services.ringcentral_sms import RingCentralSMSService

            async with RingCentralSMSService() as sms_service:
                result = await sms_service.send_sms(to, message)

                if result.success:
                    return {
                        "success": True,
                        "channel": NotificationChannel.SMS,
                        "message_id": result.message_id,
                        "status": "sent",
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error or "RingCentral SMS failed",
                    }

        except Exception as e:
            logger.exception(f"RingCentral SMS fallback failed: {e}")
            return {"success": False, "error": str(e)}

    def _build_payment_message(
        self,
        customer_name: str,
        amount: float,
        provider: str,
        sender_name: str | None = None,
        match_score: int = 0,
        booking_id: int | None = None,
    ) -> str:
        """Build payment notification message"""

        # Determine confidence level
        if match_score >= 150:
            confidence = "HIGH"
            emoji = "✅"
        elif match_score >= 100:
            confidence = "MEDIUM"
            emoji = "⚠️"
        else:
            confidence = "LOW"
            emoji = "❓"

        # Build message
        lines = [
            f"{emoji} Payment Detected - My Hibachi Chef",
            "",
            f"Amount: ${amount:.2f}",
            f"Provider: {provider}",
        ]

        if sender_name:
            lines.append(f"From: {sender_name}")

        lines.append(f"Customer: {customer_name}")

        if booking_id:
            lines.append(f"Booking ID: #{booking_id}")

        lines.extend(
            [
                "",
                f"Match Confidence: {confidence} ({match_score}/225)",
                "",
                "View dashboard: https://admin.mysticdatanode.net/payments",
            ]
        )

        return "\n".join(lines)

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to E.164 format (+1234567890)"""
        # Remove all non-digits
        digits = "".join(c for c in phone if c.isdigit())

        # Add country code if missing
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+{digits}"
        else:
            return f"+{digits}"

    async def send_manual_review_alert(
        self,
        notification_id: int,
        amount: float,
        provider: str,
        sender_name: str | None = None,
        reason: str = "Low match score",
    ) -> dict[str, Any]:
        """
        Send alert for payments requiring manual review.

        This goes ONLY to admin (not customer).
        """
        message = (
            f"🔔 Manual Review Required\n"
            f"\n"
            f"Notification ID: #{notification_id}\n"
            f"Amount: ${amount:.2f}\n"
            f"Provider: {provider}\n"
        )

        if sender_name:
            message += f"From: {sender_name}\n"

        message += (
            f"Reason: {reason}\n"
            f"\n"
            f"Review now: https://admin.myhibachichef.com/payments/{notification_id}"
        )

        # Send to admin
        admin_phone = os.getenv("BUSINESS_PHONE", "+19167408768")

        try:
            result = await self._send_whatsapp(admin_phone, message)

            if not result["success"]:
                result = await self._send_ringcentral_sms(admin_phone, message)

            return result

        except Exception as e:
            logger.exception(f"Manual review alert failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_escalation_alert(
        self,
        escalation_id: str,
        priority: str,
        customer_phone: str,
        reason: str,
        method: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send WhatsApp alert to on-call admin when escalation is created.

        Args:
            escalation_id: UUID of the escalation
            priority: Priority level (low, medium, high, urgent)
            customer_phone: Customer's phone number
            reason: Escalation reason
            method: Preferred contact method (sms, call, email)
            conversation_id: Optional conversation ID

        Returns:
            Dict with delivery status and details
        """
        # Determine emoji based on priority
        priority_emoji = {
            "low": "📋",
            "medium": "⚠️",
            "high": "🔴",
            "urgent": "🚨",
        }.get(priority.lower(), "🔔")

        # Build message
        message = (
            f"{priority_emoji} NEW ESCALATION\n"
            f"\n"
            f"Priority: {priority.upper()}\n"
            f"Customer: {customer_phone}\n"
            f"Method: {method.upper()}\n"
            f"\n"
            f"Reason:\n{reason[:200]}{'...' if len(reason) > 200 else ''}\n"
            f"\n"
            f"🔗 View Details:\n"
            f"https://admin.myhibachichef.com/inbox/escalations/{escalation_id}"
        )

        # Get on-call admin phone
        on_call_phone = os.getenv("ON_CALL_ADMIN_PHONE") or os.getenv(
            "BUSINESS_PHONE", "+19167408768"
        )

        try:
            # Try WhatsApp first
            result = await self._send_whatsapp(on_call_phone, message)

            if not result["success"]:
                # Fallback to RingCentral SMS
                logger.warning("WhatsApp failed for escalation alert, falling back to SMS")
                result = await self._send_ringcentral_sms(on_call_phone, message)

            logger.info(
                f"Escalation alert sent for {escalation_id} to {on_call_phone} "
                f"via {result.get('channel', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.exception(f"Escalation alert failed: {e}")
            return {"success": False, "error": str(e), "channel": NotificationChannel.FAILED}

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()


# Module-level instance
_whatsapp_service: WhatsAppNotificationService | None = None


def get_whatsapp_service() -> WhatsAppNotificationService:
    """Get or create WhatsApp notification service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppNotificationService()
    return _whatsapp_service


# Convenience function
async def send_payment_notification(
    phone_number: str, customer_name: str, amount: float, provider: str, **kwargs
) -> dict[str, Any]:
    """Convenience function to send payment notification"""
    service = get_whatsapp_service()
    return await service.send_payment_notification(
        phone_number=phone_number,
        customer_name=customer_name,
        amount=amount,
        provider=provider,
        **kwargs,
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        """Test WhatsApp notification"""
        service = WhatsAppNotificationService()

        await service.send_payment_notification(
            phone_number="+12103884155",
            customer_name="Suryadi Zhang",
            amount=150.00,
            provider="Venmo",
            sender_name="Friend Zhang",
            match_score=175,
            booking_id=123,
        )

        await service.close()

    asyncio.run(test())
