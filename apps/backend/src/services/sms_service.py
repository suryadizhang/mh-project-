"""
SMS Service Wrapper
===================

Provides synchronous interface to the async RingCentral SMS service.
Used by Celery tasks that require synchronous execution.

Usage:
    from services.sms_service import send_sms_sync

    success = send_sms_sync(
        to_phone="+14155551234",
        message="Your chef assignment alert..."
    )

See: services/ringcentral_sms.py for async implementation
See: workers/chef_assignment_alert_tasks.py for usage in alerts
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_sms_sync(
    to_phone: str,
    message: str,
    from_number: Optional[str] = None,
) -> bool:
    """
    Send SMS message synchronously.

    This wraps the async RingCentral SMS service for use in Celery tasks.

    Args:
        to_phone: Destination phone number (E.164 format preferred, e.g., +14155551234)
        message: SMS message content (max 160 chars for single SMS)
        from_number: Optional sender number (uses default from settings if not provided)

    Returns:
        True if SMS sent successfully, False otherwise

    Example:
        success = send_sms_sync(
            to_phone="+14155551234",
            message="Chef assignment needed for event on Jan 30!"
        )
        if success:
            print("SMS sent!")
    """
    try:
        # Run the async send_sms in a new event loop
        return asyncio.run(_send_sms_async(to_phone, message, from_number))
    except RuntimeError as e:
        # If we're already in an event loop (shouldn't happen in Celery, but handle it)
        if "cannot be called from a running event loop" in str(e):
            logger.warning("Already in event loop, using nested run")
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.run(_send_sms_async(to_phone, message, from_number))
        raise
    except Exception as e:
        logger.exception(f"SMS send failed: {e}")
        return False


async def _send_sms_async(
    to_phone: str,
    message: str,
    from_number: Optional[str] = None,
) -> bool:
    """
    Internal async implementation for sending SMS.

    Uses RingCentralSMSService with proper context manager pattern.
    """
    from services.ringcentral_sms import RingCentralSMSService

    try:
        async with RingCentralSMSService() as sms_service:
            response = await sms_service.send_sms(
                to_number=to_phone,
                message=message,
                from_number=from_number,
            )

            if response.success:
                logger.info(
                    f"✅ SMS sent successfully to {to_phone[:4]}***{to_phone[-4:]}, "
                    f"message_id: {response.message_id}"
                )
                return True
            else:
                logger.error(
                    f"❌ SMS failed to {to_phone[:4]}***{to_phone[-4:]}: {response.error}"
                )
                return False

    except Exception as e:
        logger.exception(f"SMS service error: {e}")
        return False


def send_sms_batch_sync(
    recipients: list[dict],
    message: str,
) -> dict:
    """
    Send SMS to multiple recipients synchronously.

    Args:
        recipients: List of dicts with 'phone' key
        message: SMS message content

    Returns:
        Dict with 'sent' and 'failed' counts

    Example:
        recipients = [
            {"name": "John", "phone": "+14155551234"},
            {"name": "Jane", "phone": "+14155555678"},
        ]
        result = send_sms_batch_sync(recipients, "Alert message!")
        # result = {"sent": 2, "failed": 0}
    """
    sent = 0
    failed = 0

    for recipient in recipients:
        phone = recipient.get("phone")
        if not phone:
            logger.warning(
                f"Recipient missing phone: {recipient.get('name', 'unknown')}"
            )
            failed += 1
            continue

        try:
            if send_sms_sync(to_phone=phone, message=message):
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            failed += 1

    logger.info(f"SMS batch complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed}


# Convenience function for common alert patterns
def send_alert_sms(
    to_phone: str,
    subject: str,
    body: str,
    urgency: str = "normal",
) -> bool:
    """
    Send formatted alert SMS.

    Args:
        to_phone: Destination phone number
        subject: Alert subject/title
        body: Alert body text
        urgency: Alert urgency level ("normal", "high", "critical")

    Returns:
        True if sent successfully
    """
    # Format message with urgency indicator
    urgency_prefix = {
        "critical": "🚨 CRITICAL: ",
        "high": "⚠️ URGENT: ",
        "normal": "📋 ",
    }.get(urgency, "")

    message = f"{urgency_prefix}{subject}\n\n{body}"

    # Truncate to SMS limit (leaving room for "..." if needed)
    if len(message) > 157:
        message = message[:157] + "..."

    return send_sms_sync(to_phone=to_phone, message=message)
