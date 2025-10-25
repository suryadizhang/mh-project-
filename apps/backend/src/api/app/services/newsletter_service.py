"""
Subscriber Service
Handles Subscriber subscriptions, unsubscriptions, and STOP command processing
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from api.app.models.lead_newsletter import Subscriber, LeadSource
import logging
import re

logger = logging.getLogger(__name__)


class SubscriberService:
    """Service for managing Subscriber subscriptions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def subscribe(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        source: str = "web_quote",
        auto_subscribed: bool = True
    ) -> Subscriber:
        """
        Subscribe user to Subscriber (opt-out system)
        
        Args:
            phone: User's phone number
            email: User's email address
            name: User's name (not stored in Subscriber model, used for messages)
            source: Lead source
            auto_subscribed: Whether user was auto-subscribed (True) or manually opted in (False)
        
        Returns:
            Subscriber record
        """
        
        if not phone and not email:
            raise ValueError("Either phone or email is required for Subscriber subscription")
        
        # Check if already subscribed
        existing = await self.find_by_contact(phone=phone, email=email)
        
        if existing:
            # Reactivate if previously unsubscribed
            if existing.unsubscribed_at:
                existing.unsubscribed_at = None
                existing.subscribed = True
                self.db.commit()
                
                logger.info(f"Reactivated Subscriber subscription", extra={
                    "subscriber_id": str(existing.id),
                    "phone": phone,
                    "email": email,
                    "source": source
                })
                
                # Send resubscribe confirmation
                await self._send_welcome_message(existing, name=name, resubscribe=True)
                
            return existing
        
        # Create new subscription
        subscription = Subscriber(
            phone=phone,  # Will be encrypted by property setter
            email=email,  # Will be encrypted by property setter
            source=source,
            subscribed=True,
            email_consent=True if email else False,
            sms_consent=True if phone else False,
            consent_updated_at=datetime.utcnow()
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        logger.info(f"Created Subscriber subscription", extra={
            "subscription_id": str(subscription.id),
            "phone": phone,
            "email": email,
            "source": source,
            "auto_subscribed": auto_subscribed
        })
        
        # Send welcome message with STOP instructions
        await self._send_welcome_message(subscription, name=name)
        
        return subscription
    
    async def unsubscribe(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        reason: str = "user_requested"
    ) -> bool:
        """
        Unsubscribe user from Subscriber
        
        Args:
            phone: User's phone number
            email: User's email address
            reason: Reason for unsubscribe
        
        Returns:
            True if unsubscribed, False if not found
        """
        
        subscription = await self.find_by_contact(phone=phone, email=email)
        
        if not subscription:
            logger.warning(f"Subscriber subscription not found for unsubscribe", extra={
                "phone": phone,
                "email": email
            })
            return False
        
        if subscription.unsubscribed_at:
            logger.info(f"User already unsubscribed", extra={
                "subscription_id": str(subscription.id)
            })
            return True
        
        # Mark as unsubscribed
        subscription.unsubscribed_at = datetime.utcnow()
        subscription.unsubscribe_reason = reason
        self.db.commit()
        
        logger.info(f"Unsubscribed from Subscriber", extra={
            "subscription_id": str(subscription.id),
            "phone": phone,
            "email": email,
            "reason": reason
        })
        
        # Send confirmation
        await self._send_unsubscribe_confirmation(subscription)
        
        return True
    
    async def process_stop_command(
        self,
        phone: str,
        channel: str = "sms"
    ) -> tuple[bool, str]:
        """
        Process STOP/UNSUBSCRIBE command
        
        Args:
            phone: User's phone number
            channel: Communication channel (sms, facebook, instagram)
        
        Returns:
            Tuple of (success, message)
        """
        
        phone = self._clean_phone(phone)
        
        # Find subscription
        subscription = await self.find_by_contact(phone=phone)
        
        if not subscription:
            return False, "You're not currently subscribed to our Subscriber."
        
        if subscription.unsubscribed_at:
            return True, "You're already unsubscribed from our Subscriber."
        
        # Unsubscribe
        await self.unsubscribe(phone=phone, reason=f"stop_command_{channel}")
        
        return True, "You've been successfully removed from our Subscriber. We're sorry to see you go! 😢 Reply START anytime to resubscribe."
    
    async def process_start_command(
        self,
        phone: str,
        name: Optional[str] = None,
        channel: str = "sms"
    ) -> tuple[bool, str]:
        """
        Process START/SUBSCRIBE command
        
        Args:
            phone: User's phone number
            name: User's name (if available)
            channel: Communication channel
        
        Returns:
            Tuple of (success, message)
        """
        
        phone = self._clean_phone(phone)
        
        # Check if already subscribed
        subscription = await self.find_by_contact(phone=phone)
        
        if subscription and not subscription.unsubscribed_at:
            return True, "You're already subscribed to our Subscriber! 🎉"
        
        # Subscribe or resubscribe
        source_map = {
            "sms": LeadSource.SMS,
            "facebook": LeadSource.FACEBOOK,
            "instagram": LeadSource.INSTAGRAM
        }
        
        await self.subscribe(
            phone=phone,
            name=name,
            source=source_map.get(channel, LeadSource.SMS),
            auto_subscribed=False  # Manual opt-in
        )
        
        return True, "Welcome back! 🎉 You're now subscribed to our Subscriber for exclusive hibachi deals and updates. Reply STOP anytime to unsubscribe."
    
    async def find_by_contact(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Subscriber]:
        """Find Subscriber subscription by phone or email"""
        
        if not phone and not email:
            return None
        
        query = self.db.query(Subscriber)
        
        conditions = []
        if phone:
            conditions.append(Subscriber.phone == self._clean_phone(phone))
        if email:
            conditions.append(Subscriber.email == email.lower().strip())
        
        return query.filter(or_(*conditions)).first()
    
    async def get_active_subscriptions(
        self,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Subscriber]:
        """Get all active Subscriber subscriptions"""
        
        return self.db.query(Subscriber).filter(
            Subscriber.unsubscribed_at.is_(None)
        ).limit(limit).offset(offset).all()
    
    async def _send_welcome_message(
        self,
        subscription: Subscriber,
        resubscribe: bool = False
    ):
        """Send welcome message with STOP instructions"""
        
        if resubscribe:
            message = (
                f"Welcome back, {subscription.name or 'friend'}! 🎉\n\n"
                "You're now resubscribed to MyHibachi Subscriber. "
                "Get ready for exclusive hibachi deals, cooking tips, and event updates!\n\n"
                "Reply STOP anytime to unsubscribe."
            )
        else:
            message = (
                f"Thanks for connecting with MyHibachi, {subscription.name or 'friend'}! 🎉\n\n"
                "You've been added to our Subscriber for exclusive deals and updates. "
                "We promise to only send you the good stuff!\n\n"
                "Reply STOP anytime to unsubscribe."
            )
        
        # Send via appropriate channel
        if subscription.phone:
            await self._send_sms(subscription.phone, message)
        
        if subscription.email:
            await self._send_email(subscription.email, "Welcome to MyHibachi Subscriber! 🎉", message)
    
    async def _send_unsubscribe_confirmation(self, subscription: Subscriber):
        """Send unsubscribe confirmation"""
        
        message = (
            f"You've been removed from MyHibachi Subscriber. "
            "We're sorry to see you go! 😢\n\n"
            "Reply START anytime to resubscribe and get exclusive hibachi deals."
        )
        
        # Send via appropriate channel
        if subscription.phone:
            await self._send_sms(subscription.phone, message)
        
        if subscription.email:
            await self._send_email(subscription.email, "Subscriber Unsubscribed", message)
    
    async def _send_sms(self, phone: str, message: str):
        """Send SMS message"""
        try:
            # Import here to avoid circular dependencies
            from api.app.services.ringcentral_sms import RingCentralSMS
            
            sms_service = RingCentralSMS()
            await sms_service.send_sms(phone, message)
            
            logger.info(f"Sent Subscriber SMS", extra={"phone": phone})
        except Exception as e:
            logger.error(f"Failed to send Subscriber SMS: {str(e)}", extra={"phone": phone})
    
    async def _send_email(self, email: str, subject: str, message: str):
        """Send email message"""
        try:
            # Import here to avoid circular dependencies
            from api.app.services.email_service import EmailService
            
            email_service = EmailService()
            await email_service.send_email(
                to=email,
                subject=subject,
                body=message
            )
            
            logger.info(f"Sent Subscriber email", extra={"email": email})
        except Exception as e:
            logger.error(f"Failed to send Subscriber email: {str(e)}", extra={"email": email})
    
    def _clean_phone(self, phone: str) -> str:
        """Clean phone number to digits only"""
        if not phone:
            return None
        return re.sub(r'\D', '', phone)
    
    @staticmethod
    def is_stop_command(message: str) -> bool:
        """Check if message is a STOP command"""
        message_lower = message.lower().strip()
        stop_keywords = [
            'stop', 'unsubscribe', 'cancel', 'end', 'quit',
            'stopall', 'unsubscribe', 'cancel', 'opt out', 'optout'
        ]
        return message_lower in stop_keywords
    
    @staticmethod
    def is_start_command(message: str) -> bool:
        """Check if message is a START command"""
        message_lower = message.lower().strip()
        start_keywords = ['start', 'subscribe', 'yes', 'join', 'opt in', 'optin']
        return message_lower in start_keywords


# Alias for backwards compatibility
NewsletterService = SubscriberService