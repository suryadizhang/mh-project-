"""
Enhanced Notification Service with Group Management Integration

Extends unified_notification_service.py to send notifications to groups.
Integrates with notification_group_service.py for smart routing.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from services.unified_notification_service import UnifiedNotificationService, NotificationEventType as EventType
from services.notification_group_service import NotificationGroupService
from api.app.models.notification_groups import NotificationEventType
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GroupAwareNotificationService:
    """
    Enhanced notification service that sends to groups instead of single admin.
    
    Features:
    - Sends to all group members subscribed to event type
    - Station-based filtering for station managers
    - Priority-based filtering for complaints
    - Respects individual member preferences (WhatsApp/SMS/Email)
    - Deduplicates recipients by phone number
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_service = UnifiedNotificationService()
        self.group_service = NotificationGroupService(db)
    
    async def send_to_groups(
        self,
        event_type: NotificationEventType,
        message: str,
        station_id: Optional[UUID] = None,
        priority: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification to all groups subscribed to this event.
        
        Args:
            event_type: Type of event (NEW_BOOKING, PAYMENT_RECEIVED, etc.)
            message: Admin-formatted message to send
            station_id: Optional station ID for filtering
            priority: Optional priority for priority-based filtering
            customer_phone: Optional customer phone (for customer notification)
            customer_name: Optional customer name (for customer notification)
        
        Returns:
            Dictionary with delivery results
        """
        # Get all recipients for this event
        recipients = await self.group_service.get_recipients_for_event(
            event_type=event_type,
            station_id=station_id,
            priority=priority
        )
        
        if not recipients:
            logger.warning(f"⚠️ No recipients found for {event_type.value}")
            return {"success": False, "reason": "no_recipients"}
        
        logger.info(f"📧 Sending {event_type.value} notification to {len(recipients)} group members")
        
        # Send to all recipients
        results = []
        for recipient in recipients:
            result = await self._send_to_recipient(recipient, message)
            results.append(result)
        
        # Send to customer if provided
        customer_result = None
        if customer_phone and customer_name:
            customer_result = await self._send_to_customer(
                customer_phone=customer_phone,
                customer_name=customer_name,
                event_type=event_type,
                message=message  # Will be reformatted for customer
            )
        
        return {
            "success": True,
            "group_deliveries": results,
            "customer_delivery": customer_result,
            "total_recipients": len(recipients)
        }
    
    async def _send_to_recipient(
        self,
        recipient: Dict[str, Any],
        message: str
    ) -> Dict[str, Any]:
        """Send notification to a single group member"""
        phone = recipient["phone_number"]
        name = recipient["name"]
        
        # Respect member preferences
        if recipient["receive_whatsapp"]:
            try:
                result = await self.base_service._send_whatsapp(
                    to_number=phone,
                    message=message
                )
                logger.info(f"✅ WhatsApp sent to {name} ({phone[-4:]})")
                return {"phone": phone, "name": name, "channel": "whatsapp", "success": True}
            except Exception as e:
                logger.error(f"❌ WhatsApp failed for {name}: {e}")
                
                # Try SMS fallback if enabled
                if recipient["receive_sms"]:
                    try:
                        result = await self.base_service._send_sms(
                            to_number=phone,
                            message=message
                        )
                        logger.info(f"✅ SMS fallback sent to {name}")
                        return {"phone": phone, "name": name, "channel": "sms", "success": True}
                    except Exception as e2:
                        logger.error(f"❌ SMS fallback failed for {name}: {e2}")
        
        elif recipient["receive_sms"]:
            try:
                result = await self.base_service._send_sms(
                    to_number=phone,
                    message=message
                )
                logger.info(f"✅ SMS sent to {name}")
                return {"phone": phone, "name": name, "channel": "sms", "success": True}
            except Exception as e:
                logger.error(f"❌ SMS failed for {name}: {e}")
        
        return {"phone": phone, "name": name, "channel": "failed", "success": False}
    
    async def _send_to_customer(
        self,
        customer_phone: str,
        customer_name: str,
        event_type: NotificationEventType,
        message: str
    ) -> Dict[str, Any]:
        """Send customer-facing notification (friendly format)"""
        # Check quiet hours
        if self.base_service._is_quiet_hours():
            logger.info(f"🌙 Quiet hours - skipping customer notification")
            return {"success": False, "reason": "quiet_hours"}
        
        # Reformat message for customer (friendly format)
        customer_message = self._format_customer_message(
            event_type=event_type,
            customer_name=customer_name,
            admin_message=message
        )
        
        try:
            result = await self.base_service._send_whatsapp(
                to_number=customer_phone,
                message=customer_message
            )
            logger.info(f"✅ Customer notification sent to {customer_name}")
            return {"success": True, "channel": "whatsapp"}
        except Exception as e:
            logger.error(f"❌ Customer notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_customer_message(
        self,
        event_type: NotificationEventType,
        customer_name: str,
        admin_message: str
    ) -> str:
        """Convert admin message to customer-friendly format"""
        # Extract key info from admin message
        admin_phone = self.base_service.admin_phone
        
        # Customer-facing templates
        templates = {
            NotificationEventType.NEW_BOOKING: f"""🎉 Booking Confirmed!

Thank you for your reservation, {customer_name}!

We'll send payment instructions shortly.

Questions? Call {admin_phone}

- My Hibachi Chef Team""",
            
            NotificationEventType.BOOKING_EDIT: f"""✏️ Booking Updated

Your reservation has been updated, {customer_name}.

Questions? Call {admin_phone}

- My Hibachi Chef Team""",
            
            NotificationEventType.PAYMENT_RECEIVED: f"""💰 Payment Received!

Thank you, {customer_name}!

We've received your payment and will confirm shortly.

Questions? Call {admin_phone}

- My Hibachi Chef Team""",
            
            NotificationEventType.REVIEW_RECEIVED: f"""⭐ Thank You!

We appreciate your feedback, {customer_name}!

Questions? Call {admin_phone}

- My Hibachi Chef Team""",
            
            NotificationEventType.COMPLAINT_RECEIVED: f"""🙏 We're Sorry

Thank you for your feedback, {customer_name}.

A team member will contact you within 24 hours.

Questions? Call {admin_phone} immediately.

- My Hibachi Chef Team""",
            
            NotificationEventType.BOOKING_CANCELLATION: f"""❌ Booking Cancelled

Your reservation has been cancelled, {customer_name}.

Refund (if applicable) will be processed within 3-5 business days.

Questions? Call {admin_phone}

- My Hibachi Chef Team""",
        }
        
        return templates.get(event_type, admin_message)


# ============================================================================
# CONVENIENCE FUNCTIONS FOR BACKEND INTEGRATION
# ============================================================================

async def send_group_notification(
    db: AsyncSession,
    event_type: str,
    message: str,
    station_id: Optional[UUID] = None,
    priority: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send notification to groups.
    
    Example usage in booking endpoints:
    ```python
    from services.enhanced_notification_service import send_group_notification
    
    await send_group_notification(
        db=db,
        event_type="new_booking",
        message="🆕 NEW BOOKING ACCEPTED\\n\\nDate: Sep 8...",
        station_id=booking.station_id,
        customer_phone=booking.customer_phone,
        customer_name=booking.customer_name
    )
    ```
    """
    service = GroupAwareNotificationService(db)
    
    return await service.send_to_groups(
        event_type=NotificationEventType(event_type),
        message=message,
        station_id=station_id,
        priority=priority,
        customer_phone=customer_phone,
        customer_name=customer_name
    )
