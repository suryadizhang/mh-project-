"""
Booking Notification Helpers
============================

Async notification functions for booking events.
Abstracts WhatsApp/SMS integration from endpoint logic.

File Size: ~100 lines (within limit)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def notify_new_booking(
    customer_name: str,
    customer_phone: str,
    event_date: str,
    event_time: str,
    guest_count: int,
    location: str,
    booking_id: str,
    special_requests: Optional[str] = None,
) -> bool:
    """
    Send notification for new booking creation.

    Sends to:
    1. Admin team (via WhatsApp Business)
    2. Customer confirmation (optional)

    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from services.whatsapp_service import get_whatsapp_service

        whatsapp = get_whatsapp_service()

        message = f"""🎉 NEW BOOKING!

📅 {event_date} at {event_time}
👥 {guest_count} guests
📍 {location}
👤 {customer_name}
📞 {customer_phone}

Booking ID: {booking_id[:8]}...

{f"📝 Special requests: {special_requests}" if special_requests else ""}
"""

        await whatsapp.send_admin_notification(
            message=message,
            priority="normal",
        )

        logger.info(f"✅ New booking notification sent for {booking_id}")
        return True

    except ImportError:
        logger.warning("WhatsApp service not available, skipping notification")
        return False
    except Exception as e:
        # Non-blocking: log but don't fail the booking
        logger.error(f"❌ Failed to send new booking notification: {e}")
        return False


async def notify_booking_edit(
    customer_name: str,
    customer_phone: str,
    booking_id: str,
    changes: str,
    event_date: str,
    event_time: str,
) -> bool:
    """
    Send notification for booking edit/update.

    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        from services.whatsapp_service import get_whatsapp_service

        whatsapp = get_whatsapp_service()

        message = f"""✏️ BOOKING UPDATED

Booking: {booking_id[:8]}...
📅 {event_date} at {event_time}
👤 {customer_name}

Changes: {changes}
"""

        await whatsapp.send_admin_notification(
            message=message,
            priority="low",
        )

        logger.info(f"✅ Edit notification sent for booking {booking_id}")
        return True

    except ImportError:
        logger.warning("WhatsApp service not available, skipping notification")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send edit notification: {e}")
        return False


async def notify_cancellation(
    customer_name: str,
    customer_phone: str,
    booking_id: str,
    event_date: str,
    event_time: str,
    cancelled_by: str,
    reason: Optional[str] = None,
) -> bool:
    """
    Send notification for booking cancellation.

    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        from services.whatsapp_service import get_whatsapp_service

        whatsapp = get_whatsapp_service()

        message = f"""❌ BOOKING CANCELLED

Booking: {booking_id[:8]}...
📅 {event_date} at {event_time}
👤 {customer_name}
📞 {customer_phone}

Cancelled by: {cancelled_by}
{f"Reason: {reason}" if reason else ""}
"""

        await whatsapp.send_admin_notification(
            message=message,
            priority="high",
        )

        logger.info(f"✅ Cancellation notification sent for booking {booking_id}")
        return True

    except ImportError:
        logger.warning("WhatsApp service not available, skipping notification")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send cancellation notification: {e}")
        return False


async def notify_reschedule(
    customer_name: str,
    customer_phone: str,
    booking_id: str,
    old_date: str,
    old_time: str,
    new_date: str,
    new_time: str,
    rescheduled_by: str,
) -> bool:
    """
    Send notification for booking reschedule.

    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        from services.whatsapp_service import get_whatsapp_service

        whatsapp = get_whatsapp_service()

        message = f"""📅 BOOKING RESCHEDULED

Booking: {booking_id[:8]}...
👤 {customer_name}

Old: {old_date} at {old_time}
New: {new_date} at {new_time}

Rescheduled by: {rescheduled_by}
"""

        await whatsapp.send_admin_notification(
            message=message,
            priority="normal",
        )

        logger.info(f"✅ Reschedule notification sent for booking {booking_id}")
        return True

    except ImportError:
        logger.warning("WhatsApp service not available, skipping notification")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send reschedule notification: {e}")
        return False
