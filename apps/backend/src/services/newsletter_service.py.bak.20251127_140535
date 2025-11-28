"""
Subscriber Service
Handles Subscriber subscriptions, unsubscriptions, and STOP command processing
"""

from datetime import datetime, timezone
import logging
import re

from models import Subscriber
from models.enums import LeadSource
from core.base_service import BaseService, EventTrackingMixin
from core.compliance import ComplianceValidator
from services.event_service import EventService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.validators import validate_email, validate_phone, ValidationError

logger = logging.getLogger(__name__)


class SubscriberService(BaseService, EventTrackingMixin):
    """
    Service for managing Subscriber subscriptions with dependency injection.
    
    Handles:
    - Newsletter subscriptions and unsubscriptions
    - STOP/START/HELP SMS commands
    - CAN-SPAM compliance
    - Subscriber tracking
    
    Dependencies (injected):
    - db: Database session
    - compliance_validator: CAN-SPAM validator
    - event_service: Centralized event tracking
    """

    def __init__(
        self,
        db: AsyncSession,
        compliance_validator: ComplianceValidator,
        event_service: EventService,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize subscriber service with injected dependencies.
        
        Args:
            db: Database session
            compliance_validator: Validator for CAN-SPAM compliance
            event_service: Service for event tracking
            logger: Optional logger (created automatically if not provided)
        """
        super().__init__(db, logger)
        self.compliance = compliance_validator
        self.event_service = event_service

    async def subscribe(
        self,
        phone: str | None = None,
        email: str | None = None,
        name: str | None = None,
        source: str = "web_quote",
        auto_subscribed: bool = True,
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

        # Validate and normalize inputs
        try:
            if phone:
                phone = validate_phone(phone)  # Validates E.164 format
            if email:
                email = validate_email(email)  # Normalizes to lowercase
        except ValidationError as e:
            # Re-raise with more context
            logger.error(
                f"Validation error in subscribe: {e}", extra={"phone": phone, "email": email}
            )
            raise

        # Check if already subscribed
        existing = await self.find_by_contact(phone=phone, email=email)

        if existing:
            # Reactivate if previously unsubscribed
            if existing.unsubscribed_at:
                existing.unsubscribed_at = None
                existing.subscribed = True
                await self.db.commit()
                await self.db.refresh(existing)

                logger.info(
                    "Reactivated Subscriber subscription",
                    extra={
                        "subscriber_id": str(existing.id),
                        "phone": phone,
                        "email": email,
                        "source": source,
                    },
                )

                # Send resubscribe confirmation
                await self._send_welcome_message(existing, name=name, resubscribe=True)

            return existing

        # Create new subscription
        subscription = Subscriber(
            phone=phone,  # Will be encrypted by property setter
            email=email,  # Will be encrypted by property setter
            source=source,
            subscribed=True,
            email_consent=bool(email),
            sms_consent=bool(phone),
            consent_updated_at=datetime.now(timezone.utc),
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(
            "Created Subscriber subscription",
            extra={
                "subscription_id": str(subscription.id),
                "phone": phone,
                "email": email,
                "source": source,
                "auto_subscribed": auto_subscribed,
            },
        )

        # Track subscription event
        await self.track_event(
            action="subscriber_created",
            entity_type="subscriber",
            entity_id=subscription.id,
            metadata={
                "source": source,
                "auto_subscribed": auto_subscribed,
                "has_email": bool(email),
                "has_phone": bool(phone),
            },
        )

        # Send welcome message with STOP instructions
        await self._send_welcome_message(subscription, name=name)

        return subscription

    async def unsubscribe(self, phone: str | None = None, email: str | None = None) -> bool:
        """
        Unsubscribe user from Subscriber

        Args:
            phone: User's phone number in E.164 format
            email: User's email address

        Returns:
            True if unsubscribed, False if not found

        Raises:
            ValidationError: If phone or email format is invalid
        """

        # Validate inputs if provided
        try:
            if phone:
                phone = validate_phone(phone)
            if email:
                email = validate_email(email)
        except ValidationError as e:
            logger.error(
                f"Validation error in unsubscribe: {e}", extra={"phone": phone, "email": email}
            )
            raise

        subscription = await self.find_by_contact(phone=phone, email=email)

        if not subscription:
            logger.warning(
                "Subscriber subscription not found for unsubscribe",
                extra={"phone": phone, "email": email},
            )
            return False

        if subscription.unsubscribed_at:
            logger.info(
                "User already unsubscribed", extra={"subscription_id": str(subscription.id)}
            )
            return True

        # Mark as unsubscribed
        subscription.unsubscribed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(
            "Unsubscribed from Subscriber",
            extra={
                "subscription_id": str(subscription.id),
                "phone": phone,
                "email": email,
            },
        )

        # Track unsubscribe event
        await self.track_event(
            action="subscriber_unsubscribed",
            entity_type="subscriber",
            entity_id=subscription.id,
            metadata={
                "phone": phone,
                "email": email,
            },
        )

        # Send confirmation
        await self._send_unsubscribe_confirmation(subscription)

        return True

    async def process_stop_command(self, phone: str, channel: str = "sms") -> tuple[bool, str]:
        """
        Process STOP/UNSUBSCRIBE command

        Args:
            phone: User's phone number in E.164 format (+15551234567)
            channel: Communication channel (sms, facebook, instagram)

        Returns:
            Tuple of (success, message)

        Raises:
            ValidationError: If phone format is invalid
        """

        # Validate phone format
        try:
            phone = validate_phone(phone)
        except ValidationError as e:
            logger.error(f"Validation error in process_stop_command: {e}", extra={"phone": phone})
            raise

        # Find subscription (phone already in E.164 format)
        subscription = await self.find_by_contact(phone=phone)

        if not subscription:
            return False, "You're not currently subscribed to our Subscriber."

        if subscription.unsubscribed_at:
            return True, "You're already unsubscribed from our Subscriber."

        # Unsubscribe
        await self.unsubscribe(phone=phone)

        return (
            True,
            "You've been successfully removed from our Subscriber. We're sorry to see you go! 😢 Reply START anytime to resubscribe.",
        )

    async def process_start_command(
        self, phone: str, name: str | None = None, channel: str = "sms"
    ) -> tuple[bool, str]:
        """
        Process START/SUBSCRIBE command

        Args:
            phone: User's phone number in E.164 format (+15551234567)
            name: User's name (if available)
            channel: Communication channel

        Returns:
            Tuple of (success, message)

        Raises:
            ValidationError: If phone format is invalid
        """

        # Validate phone format
        try:
            phone = validate_phone(phone)
        except ValidationError as e:
            logger.error(f"Validation error in process_start_command: {e}", extra={"phone": phone})
            raise

        # Check if already subscribed (phone already in E.164 format)
        subscription = await self.find_by_contact(phone=phone)

        if subscription and not subscription.unsubscribed_at:
            return True, "You're already subscribed to our Subscriber! 🎉"

        # Subscribe or resubscribe
        source_map = {
            "sms": LeadSource.SMS,
            "facebook": LeadSource.FACEBOOK,
            "instagram": LeadSource.INSTAGRAM,
        }

        await self.subscribe(
            phone=phone,
            name=name,
            source=source_map.get(channel, LeadSource.SMS),
            auto_subscribed=False,  # Manual opt-in
        )

        return (
            True,
            "Welcome back! 🎉 You're now subscribed to our Subscriber for exclusive hibachi deals and updates. Reply STOP anytime to unsubscribe.",
        )

    async def process_help_command(self, phone: str) -> tuple[bool, str]:
        """
        Process HELP command with TCPA-compliant information

        Args:
            phone: User's phone number in E.164 format (+15551234567)

        Returns:
            Tuple of (success, help_message)

        Raises:
            ValidationError: If phone format is invalid
        """

        # Validate phone format
        try:
            phone = validate_phone(phone)
        except ValidationError as e:
            logger.error(f"Validation error in process_help_command: {e}", extra={"phone": phone})
            raise

        # Get TCPA-compliant help message from compliance module
        help_message = self.compliance.get_sms_help_message()

        logger.info("Sent HELP message", extra={"phone": phone})

        return True, help_message

    async def find_by_contact(
        self, phone: str | None = None, email: str | None = None
    ) -> Subscriber | None:
        """
        Find Subscriber subscription by phone or email.

        NOTE: Since phone and email are encrypted, we need to fetch all subscribers
        and decrypt them in Python to compare. This is a performance trade-off for PII security.
        """

        if not phone and not email:
            return None

        # Normalize inputs for comparison
        # Phone: Keep as-is in E.164 format (+15551234567)
        # Email: Lowercase and trim
        normalized_phone = phone if phone else None
        normalized_email = email.lower().strip() if email else None

        logger.debug(f"Finding subscriber: phone={normalized_phone}, email={normalized_email}")

        # Expire all cached objects to ensure we get fresh data from DB
        self.db.expire_all()

        # Fetch ALL subscribers (we need to decrypt to compare)
        # TODO: Add pagination if subscriber count grows large (>10k)
        result = await self.db.execute(select(Subscriber))
        all_subscribers = list(result.scalars().all())

        logger.debug(f"Total subscribers to check: {len(all_subscribers)}")

        # Decrypt and compare in Python
        for subscriber in all_subscribers:
            try:
                # Decrypt phone and email for this subscriber
                sub_phone = subscriber.phone  # Property decrypts
                sub_email = subscriber.email  # Property decrypts

                logger.debug(
                    f"Checking subscriber {subscriber.id}: phone={sub_phone}, email={sub_email}"
                )

                # Check phone match
                if normalized_phone and sub_phone:
                    if sub_phone == normalized_phone:
                        logger.debug(f"Found match by phone: {subscriber.id}")
                        return subscriber

                # Check email match
                if normalized_email and sub_email:
                    if sub_email == normalized_email:
                        logger.debug(f"Found match by email: {subscriber.id}")
                        return subscriber
            except Exception as e:
                # If decryption fails for this subscriber, skip it
                # (could be old data with different encryption key)
                logger.warning(
                    f"Failed to decrypt subscriber {subscriber.id}: {str(e)}",
                    extra={"subscriber_id": str(subscriber.id)},
                )
                continue

        logger.debug("No matching subscriber found")
        return None

    async def get_active_subscriptions(
        self, limit: int = 1000, offset: int = 0
    ) -> list[Subscriber]:
        """Get all active Subscriber subscriptions"""

        result = await self.db.execute(
            select(Subscriber)
            .filter(Subscriber.unsubscribed_at.is_(None))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def _send_welcome_message(
        self, subscription: Subscriber, name: str | None = None, resubscribe: bool = False
    ):
        """Send TCPA-compliant welcome message with STOP instructions"""

        # Use compliance module for TCPA-compliant messaging
        message = self.compliance.get_sms_welcome_message(name)

        # Send via appropriate channel
        if subscription.phone:
            await self._send_sms(subscription.phone, message)

        if subscription.email:
            email_subject = (
                "Welcome to My Hibachi Chef! 🎉"
                if not resubscribe
                else "Welcome Back to My Hibachi Chef! 🎉"
            )
            await self._send_email(subscription.email, email_subject, message)

    async def _send_unsubscribe_confirmation(self, subscription: Subscriber):
        """Send TCPA-compliant unsubscribe confirmation"""

        # Use compliance module for TCPA-compliant messaging
        message = self.compliance.get_sms_opt_out_confirmation()

        # Send via appropriate channel
        if subscription.phone:
            await self._send_sms(subscription.phone, message)

        if subscription.email:
            await self._send_email(subscription.email, "Unsubscribed from My Hibachi Chef", message)

    async def _send_sms(self, phone: str, message: str):
        """Send SMS message"""
        try:
            # Import here to avoid circular dependencies
            from services.ringcentral_sms import (
                RingCentralSMSService,
            )  # Phase 2C: Updated from api.app.services.ringcentral_sms

            sms_service = RingCentralSMSService()
            await sms_service.send_sms(phone, message)

            logger.info("Sent Subscriber SMS", extra={"phone": phone})
        except Exception as e:
            logger.exception(f"Failed to send Subscriber SMS: {e!s}", extra={"phone": phone})

    async def _send_email(self, email: str, subject: str, message: str):
        """Send email message"""
        try:
            # Import here to avoid circular dependencies
            from services.email_service import (
                EmailService,
            )  # Phase 2C: Updated from api.app.services.email_service

            email_service = EmailService()
            await email_service.send_email(to=email, subject=subject, body=message)

            logger.info("Sent Subscriber email", extra={"email": email})
        except Exception as e:
            logger.exception(f"Failed to send Subscriber email: {e!s}", extra={"email": email})

    def _clean_phone(self, phone: str) -> str:
        """Clean phone number to digits only"""
        if not phone:
            return None
        return re.sub(r"\D", "", phone)

    @staticmethod
    def is_stop_command(message: str) -> bool:
        """Check if message is a STOP command"""
        message_lower = message.lower().strip()
        stop_keywords = [
            "stop",
            "unsubscribe",
            "cancel",
            "end",
            "quit",
            "stopall",
            "unsubscribe",
            "cancel",
            "opt out",
            "optout",
        ]
        return message_lower in stop_keywords

    @staticmethod
    def is_start_command(message: str) -> bool:
        """Check if message is a START command"""
        message_lower = message.lower().strip()
        start_keywords = ["start", "subscribe", "yes", "join", "opt in", "optin"]
        return message_lower in start_keywords


# Alias for backwards compatibility
NewsletterService = SubscriberService
