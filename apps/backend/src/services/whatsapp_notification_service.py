"""
WhatsApp Notification Service

Implements WhatsApp Business API integration for payment notifications.
Fallback to SMS if WhatsApp fails or customer doesn't have WhatsApp.

WhatsApp Options Evaluated:
1. WhatsApp Business API (Official) - RECOMMENDED
   - Requires: Business verification, phone number
   - Setup: 1-2 days approval
   - Cost: Free for first 1000 conversations/month
   - Features: Templates, webhooks, groups, media

2. Twilio WhatsApp API - ALTERNATIVE
   - Setup: 30 minutes
   - Cost: $0.005/message
   - Features: Easy integration, reliable

3. WhatsApp Web Automation - NOT RECOMMENDED
   - Risk: Violates ToS, account ban risk
   - Not suitable for production

Implementation Strategy:
1. Start with Twilio WhatsApp (quick setup)
2. Fallback to SMS if WhatsApp unavailable
3. Migrate to official API when business verified

Message Flow:
Payment Detected → Try WhatsApp → If fail, send SMS → Log result
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import os
from typing import Any

import httpx
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    FAILED = "failed"


class WhatsAppNotificationService:
    """
    Handles WhatsApp and SMS notifications for payment alerts.

    Features:
    - WhatsApp via Twilio (official provider)
    - Automatic fallback to SMS
    - Template support
    - Delivery tracking
    - Group notifications

    Environment Variables Required:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_WHATSAPP_NUMBER (format: whatsapp:+14155238886)
    - TWILIO_SMS_NUMBER (format: +19167408768)
    - WHATSAPP_GROUP_WEBHOOK (optional, for group notifications)
    """

    def __init__(self):
        """Initialize WhatsApp/SMS notification service"""
        try:
            # Get Twilio credentials
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")

            if not account_sid or not auth_token:
                logger.warning("Twilio credentials not found - notifications will use SMS only")
                self.client = None
            else:
                self.client = Client(account_sid, auth_token)
                logger.info("Twilio client initialized successfully")

            # Get phone numbers
            self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
            self.sms_from = os.getenv("TWILIO_SMS_NUMBER") or os.getenv(
                "RC_SMS_FROM", "+19167408768"
            )
            self.group_webhook = os.getenv("WHATSAPP_GROUP_WEBHOOK")

            logger.info(f"WhatsApp from: {self.whatsapp_from}")
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
            "message_sid": None,
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
            if self.client:
                whatsapp_result = await self._send_whatsapp(formatted_phone, message)

                if whatsapp_result["success"]:
                    result.update(whatsapp_result)
                    logger.info(
                        f"WhatsApp sent to {formatted_phone}: {whatsapp_result['message_sid']}"
                    )
                else:
                    # Fallback to SMS
                    logger.warning(
                        f"WhatsApp failed, falling back to SMS: {whatsapp_result['error']}"
                    )
                    sms_result = await self._send_sms(formatted_phone, message)
                    result.update(sms_result)
            else:
                # No Twilio client, use SMS directly
                sms_result = await self._send_sms(formatted_phone, message)
                result.update(sms_result)

            # Send to admin group if enabled
            if admin_group and self.group_webhook:
                await self._send_to_admin_group(message)
            elif admin_group and self.client:
                # Send to admin phone as fallback
                admin_phone = os.getenv("BUSINESS_PHONE", "+19167408768")
                await self._send_sms(admin_phone, f"[ADMIN] {message}")

            return result

        except Exception as e:
            logger.error(f"Payment notification failed: {e}", exc_info=True)
            result["error"] = str(e)
            return result

    async def _send_whatsapp(self, to: str, message: str) -> dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        try:
            if not self.client:
                return {"success": False, "error": "Twilio client not initialized"}

            # Format number for WhatsApp
            whatsapp_to = f"whatsapp:{to}"

            # Send message
            twilio_message = self.client.messages.create(
                from_=self.whatsapp_from, to=whatsapp_to, body=message
            )

            return {
                "success": True,
                "channel": NotificationChannel.WHATSAPP,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
            }

        except TwilioRestException as e:
            logger.exception(f"Twilio WhatsApp error: {e.msg}")
            return {"success": False, "error": e.msg}
        except Exception as e:
            logger.exception(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_sms(self, to: str, message: str) -> dict[str, Any]:
        """Send SMS via Twilio (fallback)"""
        try:
            if not self.client:
                # Try RingCentral as last resort
                return await self._send_ringcentral_sms(to, message)

            # Send SMS
            twilio_message = self.client.messages.create(from_=self.sms_from, to=to, body=message)

            return {
                "success": True,
                "channel": NotificationChannel.SMS,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
            }

        except TwilioRestException as e:
            logger.exception(f"Twilio SMS error: {e.msg}")
            return {"success": False, "error": e.msg}
        except Exception as e:
            logger.exception(f"SMS send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_ringcentral_sms(self, to: str, message: str) -> dict[str, Any]:
        """Fallback to RingCentral SMS"""
        try:
            # Import RingCentral service
            from services.ringcentral_service import send_sms

            result = await send_sms(to, message)

            if result.get("success"):
                return {
                    "success": True,
                    "channel": NotificationChannel.SMS,
                    "message_sid": result.get("message_id"),
                    "status": "sent",
                }
            else:
                return {"success": False, "error": result.get("error", "RingCentral SMS failed")}

        except Exception as e:
            logger.exception(f"RingCentral SMS fallback failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_to_admin_group(self, message: str) -> bool:
        """Send notification to admin WhatsApp group via webhook"""
        try:
            if not self.group_webhook:
                return False

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.group_webhook, json={"message": message}, timeout=10.0
                )

                if response.status_code == 200:
                    logger.info("Admin group notification sent")
                    return True
                else:
                    logger.warning(f"Admin group webhook failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.exception(f"Admin group notification failed: {e}")
            return False

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
                "View dashboard: https://admin.myhibachichef.com/payments",
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
                result = await self._send_sms(admin_phone, message)

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
                # Fallback to SMS
                logger.warning("WhatsApp failed for escalation alert, falling back to SMS")
                result = await self._send_sms(on_call_phone, message)

            logger.info(
                f"Escalation alert sent for {escalation_id} to {on_call_phone} "
                f"via {result.get('channel', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.exception(f"Escalation alert failed: {e}")
            return {"success": False, "error": str(e), "channel": NotificationChannel.FAILED}


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

    asyncio.run(test())
