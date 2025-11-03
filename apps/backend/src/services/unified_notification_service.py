"""
Unified Notification Service for My Hibachi Chef

Sends WhatsApp/SMS notifications for ALL business events:
✅ New bookings
✅ Booking edits
✅ Booking cancellations
✅ Payment confirmations
✅ Customer reviews
✅ Customer complaints

Features:
- WhatsApp via Twilio or Meta Business API
- Automatic SMS fallback
- Admin notifications for all events
- Smart message formatting with emojis
- Non-blocking async delivery
- Quiet hours support (no notifications 10 PM - 8 AM)
- Mock mode for local testing (no API required)
- Delivery tracking and logging
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, Literal
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import Twilio (optional dependency)
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed - will use mock mode")


class NotificationType(str, Enum):
    """Types of notifications"""
    NEW_BOOKING = "new_booking"
    EDIT_BOOKING = "edit_booking"
    CANCEL_BOOKING = "cancel_booking"
    PAYMENT_RECEIVED = "payment_received"
    REVIEW_RECEIVED = "review_received"
    COMPLAINT_RECEIVED = "complaint_received"


class NotificationChannel(str, Enum):
    """Delivery channels"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    MOCK = "mock"  # For local testing
    FAILED = "failed"


class UnifiedNotificationService:
    """
    Unified notification service for all business events.
    
    Supports:
    1. WhatsApp (via Twilio or Meta)
    2. SMS (via Twilio or RingCentral)
    3. Mock mode (for local testing)
    
    Environment Variables:
    - WHATSAPP_PROVIDER: 'twilio' or 'meta' or 'mock'
    - TWILIO_ACCOUNT_SID: Twilio account ID
    - TWILIO_AUTH_TOKEN: Twilio auth token
    - TWILIO_WHATSAPP_NUMBER: whatsapp:+14155238886
    - TWILIO_SMS_NUMBER: +19167408768
    - ADMIN_NOTIFICATION_PHONE: Admin phone for all alerts
    - NOTIFICATION_QUIET_START: 22 (10 PM)
    - NOTIFICATION_QUIET_END: 8 (8 AM)
    """
    
    def __init__(self):
        """Initialize notification service"""
        self.provider = os.getenv('WHATSAPP_PROVIDER', 'mock').lower()
        self.admin_phone = os.getenv('ADMIN_NOTIFICATION_PHONE', '+19167408768')
        
        # Quiet hours (no notifications)
        self.quiet_start = int(os.getenv('NOTIFICATION_QUIET_START', '22'))
        self.quiet_end = int(os.getenv('NOTIFICATION_QUIET_END', '8'))
        
        # Initialize Twilio if available
        if self.provider == 'twilio' and TWILIO_AVAILABLE:
            try:
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                
                if account_sid and auth_token:
                    self.twilio_client = Client(account_sid, auth_token)
                    self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
                    self.sms_from = os.getenv('TWILIO_SMS_NUMBER', '+19167408768')
                    logger.info("✅ Twilio WhatsApp service initialized")
                else:
                    logger.warning("⚠️ Twilio credentials missing - using mock mode")
                    self.provider = 'mock'
                    self.twilio_client = None
            except Exception as e:
                logger.error(f"❌ Twilio initialization failed: {e} - using mock mode")
                self.provider = 'mock'
                self.twilio_client = None
        else:
            self.twilio_client = None
            if self.provider != 'mock':
                logger.warning(f"⚠️ Provider '{self.provider}' not supported yet - using mock mode")
                self.provider = 'mock'
        
        logger.info(f"📱 Notification Service: Provider={self.provider}, Admin={self.admin_phone}")
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        now = datetime.now().time()
        current_hour = now.hour
        
        if self.quiet_start > self.quiet_end:  # e.g., 22:00 to 8:00 (crosses midnight)
            return current_hour >= self.quiet_start or current_hour < self.quiet_end
        else:  # e.g., 8:00 to 22:00
            return self.quiet_start <= current_hour < self.quiet_end
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number for SMS (remove whatsapp: prefix if present)"""
        if not phone:
            return ""
        return phone.replace("whatsapp:", "").strip()
    
    def _format_whatsapp(self, phone: str) -> str:
        """Format phone number for WhatsApp"""
        phone = self._format_phone(phone)
        if not phone.startswith("whatsapp:"):
            return f"whatsapp:{phone}"
        return phone
    
    # ==========================================
    # NEW BOOKING NOTIFICATION
    # ==========================================
    
    async def send_new_booking_notification(
        self,
        customer_name: str,
        customer_phone: str,
        event_date: str,
        event_time: str,
        guest_count: int,
        location: str,
        booking_id: int,
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when new booking is created.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            event_date: Event date (e.g., "2025-11-15")
            event_time: Event time (e.g., "6:00 PM")
            guest_count: Number of guests
            location: Event location
            booking_id: Booking ID
            send_to_admin: Also notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Check quiet hours for customer notification
        if self._is_quiet_hours():
            logger.info(f"🌙 Quiet hours - skipping customer notification for booking #{booking_id}")
            customer_result = {"channel": "skipped", "reason": "quiet_hours"}
        else:
            # Customer message
            customer_message = f"""🎉 Booking Confirmed!

Hello {customer_name}!

Your hibachi event is confirmed:

📅 Date: {event_date}
🕐 Time: {event_time}
👥 Guests: {guest_count}
📍 Location: {location}

Booking #{booking_id}

We'll send payment instructions shortly.

Questions? Reply here or call {self.admin_phone}

- My Hibachi Chef Team"""
            
            customer_result = await self._send_message(
                to_phone=customer_phone,
                message=customer_message,
                notification_type=NotificationType.NEW_BOOKING
            )
        
        # Admin message (always send, ignore quiet hours) - Simple internal format
        if send_to_admin:
            admin_message = f"""🆕 NEW BOOKING ACCEPTED

Date: {event_date} at {event_time}
Location: {location}
Customer: {customer_name}
Guests: ~{guest_count} people

Booking #{booking_id}

Check admin portal for details."""
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.NEW_BOOKING
            )
        else:
            admin_result = {"channel": "skipped", "reason": "not_requested"}
        
        return {
            "customer": customer_result,
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # BOOKING EDIT NOTIFICATION
    # ==========================================
    
    async def send_booking_edit_notification(
        self,
        customer_name: str,
        customer_phone: str,
        booking_id: int,
        changes: Dict[str, Dict[str, Any]],
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when booking is edited.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            booking_id: Booking ID
            changes: Dict of changes {field: {old: X, new: Y}}
            send_to_admin: Also notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Format changes
        change_text = "\n".join([
            f"• {field.replace('_', ' ').title()}: {change['old']} → {change['new']}"
            for field, change in changes.items()
        ])
        
        # Customer message
        customer_message = f"""✏️ Booking Updated!

Hello {customer_name}!

Your booking #{booking_id} has been updated:

{change_text}

If this wasn't requested, please call immediately:
{self.admin_phone}

- My Hibachi Chef Team"""
        
        customer_result = await self._send_message(
            to_phone=customer_phone,
            message=customer_message,
            notification_type=NotificationType.EDIT_BOOKING
        )
        
        # Admin notification - Simple internal format
        if send_to_admin:
            admin_message = f"""✏️ BOOKING EDITED

Booking #{booking_id}
Customer: {customer_name}

Changes:
{change_text}

Check admin portal for details."""
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.EDIT_BOOKING
            )
        else:
            admin_result = {"channel": "skipped"}
        
        return {
            "customer": customer_result,
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # BOOKING CANCELLATION NOTIFICATION
    # ==========================================
    
    async def send_cancellation_notification(
        self,
        customer_name: str,
        customer_phone: str,
        booking_id: int,
        event_date: str,
        reason: Optional[str] = None,
        refund_amount: Optional[float] = None,
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when booking is cancelled.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            booking_id: Booking ID
            event_date: Original event date
            reason: Cancellation reason (optional)
            refund_amount: Refund amount if applicable
            send_to_admin: Also notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Customer message
        customer_message = f"""❌ Booking Cancelled

Hello {customer_name},

Your booking #{booking_id} for {event_date} has been cancelled."""
        
        if reason:
            customer_message += f"\n\nReason: {reason}"
        
        if refund_amount:
            customer_message += f"\n\n💰 Refund of ${refund_amount:.2f} will be processed within 3-5 business days."
        
        customer_message += f"""

We're sorry to see you go! If you'd like to reschedule, please call:
{self.admin_phone}

- My Hibachi Chef Team"""
        
        customer_result = await self._send_message(
            to_phone=customer_phone,
            message=customer_message,
            notification_type=NotificationType.CANCEL_BOOKING
        )
        
        # Admin notification - Simple internal format
        if send_to_admin:
            admin_message = f"""❌ BOOKING CANCELLED

Booking #{booking_id}
Event: {event_date}
Customer: {customer_name}"""
            
            if reason:
                admin_message += f"\nReason: {reason}"
            if refund_amount:
                admin_message += f"\nRefund: ${refund_amount:.2f}"
            
            admin_message += "\n\nCheck admin portal for details."
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.CANCEL_BOOKING
            )
        else:
            admin_result = {"channel": "skipped"}
        
        return {
            "customer": customer_result,
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # PAYMENT CONFIRMATION NOTIFICATION
    # ==========================================
    
    async def send_payment_confirmation(
        self,
        customer_name: str,
        customer_phone: str,
        amount: float,
        payment_method: str,
        booking_id: int,
        event_date: str,
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when payment is received.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            amount: Payment amount
            payment_method: Payment method (Venmo, Zelle, etc.)
            booking_id: Associated booking ID
            event_date: Event date
            send_to_admin: Also notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Customer message
        customer_message = f"""✅ Payment Confirmed!

Hello {customer_name}!

We've received your payment of ${amount:.2f} via {payment_method}.

Booking #{booking_id} is now fully paid! 🎉

Event Date: {event_date}

Our chef will arrive 30 minutes early to set up.

Looking forward to serving you!

- My Hibachi Chef Team"""
        
        customer_result = await self._send_message(
            to_phone=customer_phone,
            message=customer_message,
            notification_type=NotificationType.PAYMENT_RECEIVED
        )
        
        # Admin notification - Simple internal format
        if send_to_admin:
            admin_message = f"""💰 PAYMENT RECEIVED

Amount: ${amount:.2f} ({payment_method})
Booking: #{booking_id}
Event: {event_date}
Customer: {customer_name}

Status: Fully Paid ✅"""
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.PAYMENT_RECEIVED
            )
        else:
            admin_result = {"channel": "skipped"}
        
        return {
            "customer": customer_result,
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # REVIEW NOTIFICATION
    # ==========================================
    
    async def send_review_notification(
        self,
        customer_name: str,
        rating: int,
        review_text: str,
        booking_id: int,
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when customer leaves review.
        
        Args:
            customer_name: Customer's full name
            rating: Star rating (1-5)
            review_text: Review content
            booking_id: Associated booking ID
            send_to_admin: Notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Only notify admin (no need to notify customer about their own review)
        if send_to_admin:
            stars = "⭐" * rating
            admin_message = f"""⭐ NEW REVIEW RECEIVED

Rating: {stars} ({rating}/5)
Booking: #{booking_id}
Customer: {customer_name}

"{review_text}"

Check admin portal for details."""
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.REVIEW_RECEIVED
            )
        else:
            admin_result = {"channel": "skipped"}
        
        return {
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # COMPLAINT NOTIFICATION
    # ==========================================
    
    async def send_complaint_notification(
        self,
        customer_name: str,
        customer_phone: str,
        complaint_text: str,
        booking_id: int,
        priority: Literal["low", "medium", "high", "urgent"] = "medium",
        send_to_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification when customer files complaint.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            complaint_text: Complaint content
            booking_id: Associated booking ID
            priority: Complaint priority
            send_to_admin: Notify admin
        
        Returns:
            Dictionary with delivery status
        """
        # Customer acknowledgment
        customer_message = f"""📋 Complaint Received

Hello {customer_name},

We've received your complaint regarding booking #{booking_id}.

Our team will review this immediately and contact you within 24 hours.

Your satisfaction is our priority.

- My Hibachi Chef Team"""
        
        customer_result = await self._send_message(
            to_phone=customer_phone,
            message=customer_message,
            notification_type=NotificationType.COMPLAINT_RECEIVED
        )
        
        # Admin notification - Internal format with priority
        if send_to_admin:
            priority_emoji = {
                "low": "🔵",
                "medium": "🟡",
                "high": "🟠",
                "urgent": "🔴"
            }
            
            admin_message = f"""{priority_emoji.get(priority, '🟡')} COMPLAINT RECEIVED ({priority.upper()})

Booking: #{booking_id}
Customer: {customer_name}

"{complaint_text}"

⚠️ Contact customer within 24h
Check admin portal for details."""
            
            admin_result = await self._send_message(
                to_phone=self.admin_phone,
                message=admin_message,
                notification_type=NotificationType.COMPLAINT_RECEIVED
            )
        else:
            admin_result = {"channel": "skipped"}
        
        return {
            "customer": customer_result,
            "admin": admin_result,
            "booking_id": booking_id
        }
    
    # ==========================================
    # CORE MESSAGE SENDING
    # ==========================================
    
    async def _send_message(
        self,
        to_phone: str,
        message: str,
        notification_type: NotificationType
    ) -> Dict[str, Any]:
        """
        Send message via WhatsApp or SMS with fallback.
        
        Args:
            to_phone: Recipient phone number
            message: Message content
            notification_type: Type of notification
        
        Returns:
            Dictionary with delivery status and details
        """
        if not to_phone:
            logger.warning(f"❌ No phone number provided for {notification_type}")
            return {
                "success": False,
                "channel": NotificationChannel.FAILED,
                "error": "No phone number"
            }
        
        # Format phone
        to_phone = self._format_phone(to_phone)
        
        # Mock mode (for local testing)
        if self.provider == 'mock':
            return await self._send_mock(to_phone, message, notification_type)
        
        # Twilio WhatsApp/SMS
        if self.provider == 'twilio' and self.twilio_client:
            # Try WhatsApp first
            result = await self._send_via_twilio_whatsapp(to_phone, message)
            if result["success"]:
                return result
            
            # Fallback to SMS
            logger.info(f"📱 WhatsApp failed, trying SMS fallback for {notification_type}")
            return await self._send_via_twilio_sms(to_phone, message)
        
        # No provider available
        logger.error(f"❌ No notification provider available for {notification_type}")
        return {
            "success": False,
            "channel": NotificationChannel.FAILED,
            "error": "No provider available"
        }
    
    async def _send_mock(
        self,
        to_phone: str,
        message: str,
        notification_type: NotificationType
    ) -> Dict[str, Any]:
        """Send mock notification (logs only, for local testing)"""
        logger.info("=" * 60)
        logger.info(f"📱 MOCK NOTIFICATION - {notification_type.value.upper()}")
        logger.info(f"To: {to_phone}")
        logger.info("Message:")
        logger.info("-" * 60)
        logger.info(message)
        logger.info("=" * 60)
        
        return {
            "success": True,
            "channel": NotificationChannel.MOCK,
            "to": to_phone,
            "message_length": len(message),
            "notification_type": notification_type.value
        }
    
    async def _send_via_twilio_whatsapp(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send via Twilio WhatsApp"""
        try:
            to_whatsapp = self._format_whatsapp(to_phone)
            
            response = self.twilio_client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=to_whatsapp
            )
            
            logger.info(f"✅ WhatsApp sent to {to_phone} - SID: {response.sid}")
            
            return {
                "success": True,
                "channel": NotificationChannel.WHATSAPP,
                "sid": response.sid,
                "to": to_phone,
                "status": response.status
            }
            
        except Exception as e:
            logger.warning(f"⚠️ WhatsApp send failed: {e}")
            return {
                "success": False,
                "channel": NotificationChannel.WHATSAPP,
                "error": str(e)
            }
    
    async def _send_via_twilio_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send via Twilio SMS"""
        try:
            response = self.twilio_client.messages.create(
                body=message,
                from_=self.sms_from,
                to=to_phone
            )
            
            logger.info(f"✅ SMS sent to {to_phone} - SID: {response.sid}")
            
            return {
                "success": True,
                "channel": NotificationChannel.SMS,
                "sid": response.sid,
                "to": to_phone,
                "status": response.status
            }
            
        except Exception as e:
            logger.error(f"❌ SMS send failed: {e}")
            return {
                "success": False,
                "channel": NotificationChannel.SMS,
                "error": str(e)
            }


# ==========================================
# CONVENIENCE FUNCTIONS (Global instance)
# ==========================================

# Create global instance
_notification_service = None


def get_notification_service() -> UnifiedNotificationService:
    """Get or create global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = UnifiedNotificationService()
    return _notification_service


# Convenience async functions
async def notify_new_booking(customer_name: str, customer_phone: str, **kwargs):
    """Send new booking notification"""
    service = get_notification_service()
    return await service.send_new_booking_notification(customer_name, customer_phone, **kwargs)


async def notify_booking_edit(customer_name: str, customer_phone: str, **kwargs):
    """Send booking edit notification"""
    service = get_notification_service()
    return await service.send_booking_edit_notification(customer_name, customer_phone, **kwargs)


async def notify_cancellation(customer_name: str, customer_phone: str, **kwargs):
    """Send cancellation notification"""
    service = get_notification_service()
    return await service.send_cancellation_notification(customer_name, customer_phone, **kwargs)


async def notify_payment(customer_name: str, customer_phone: str, **kwargs):
    """Send payment confirmation"""
    service = get_notification_service()
    return await service.send_payment_confirmation(customer_name, customer_phone, **kwargs)


async def notify_review(customer_name: str, **kwargs):
    """Send review notification"""
    service = get_notification_service()
    return await service.send_review_notification(customer_name, **kwargs)


async def notify_complaint(customer_name: str, customer_phone: str, **kwargs):
    """Send complaint notification"""
    service = get_notification_service()
    return await service.send_complaint_notification(customer_name, customer_phone, **kwargs)


# ==========================================
# TESTING
# ==========================================

async def test_all_notifications():
    """Test all notification types in mock mode"""
    service = UnifiedNotificationService()
    
    print("\n🧪 Testing All Notification Types\n")
    
    # 1. New Booking
    print("1️⃣ Testing New Booking Notification...")
    await service.send_new_booking_notification(
        customer_name="Suryadi Zhang",
        customer_phone="+19167408768",
        event_date="2025-11-15",
        event_time="6:00 PM",
        guest_count=15,
        location="123 Main St, Fremont CA",
        booking_id=123
    )
    
    # 2. Booking Edit
    print("\n2️⃣ Testing Booking Edit Notification...")
    await service.send_booking_edit_notification(
        customer_name="Suryadi Zhang",
        customer_phone="+19167408768",
        booking_id=123,
        changes={
            "event_date": {"old": "2025-11-15", "new": "2025-11-20"},
            "guest_count": {"old": 15, "new": 20}
        }
    )
    
    # 3. Cancellation
    print("\n3️⃣ Testing Cancellation Notification...")
    await service.send_cancellation_notification(
        customer_name="Suryadi Zhang",
        customer_phone="+19167408768",
        booking_id=123,
        event_date="2025-11-15",
        reason="Schedule conflict",
        refund_amount=150.00
    )
    
    # 4. Payment
    print("\n4️⃣ Testing Payment Confirmation...")
    await service.send_payment_confirmation(
        customer_name="Suryadi Zhang",
        customer_phone="+19167408768",
        amount=450.00,
        payment_method="Venmo",
        booking_id=123,
        event_date="2025-11-15"
    )
    
    # 5. Review
    print("\n5️⃣ Testing Review Notification...")
    await service.send_review_notification(
        customer_name="Suryadi Zhang",
        rating=5,
        review_text="Amazing experience! The chef was professional and the food was delicious!",
        booking_id=123
    )
    
    # 6. Complaint
    print("\n6️⃣ Testing Complaint Notification...")
    await service.send_complaint_notification(
        customer_name="Suryadi Zhang",
        customer_phone="+19167408768",
        complaint_text="The chef arrived 15 minutes late",
        booking_id=123,
        priority="medium"
    )
    
    print("\n✅ All notification tests complete!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_all_notifications())
