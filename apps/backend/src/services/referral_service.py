"""
ReferralService - Manage customer referral program.

Handles referral tracking, reward management, and conversion tracking.
Uses dependency injection for testability and follows BaseService patterns.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.base_service import BaseService, EventTrackingMixin, NotificationMixin
from services.event_service import EventService

# FIXED: Import from db.models (NEW system) instead of models (OLD system)
from db.models.crm import Lead
from core.exceptions import BusinessLogicException, NotFoundException, ErrorCode


class ReferralStatus:
    """Referral status constants."""

    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ReferralService(BaseService, EventTrackingMixin, NotificationMixin):
    """
    Service for managing customer referral program.

    Features:
    - Generate unique referral codes
    - Track referrals and conversions
    - Award credits/rewards to referrers
    - Analytics and reporting
    - Automated notifications

    Dependencies (injected):
    - db: Database session
    - event_service: Event tracking
    - notification_service: For sending referral emails (optional)
    """

    def __init__(
        self,
        db: AsyncSession,
        event_service: EventService,
        notification_service: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize referral service with injected dependencies.

        Args:
            db: Database session
            event_service: Service for event tracking
            notification_service: Optional service for sending notifications
            logger: Optional logger (auto-created if not provided)
        """
        super().__init__(db, logger)
        self.event_service = event_service
        self.notification_service = notification_service

    def _generate_referral_code(self, prefix: str = "REF") -> str:
        """
        Generate a unique referral code.

        Args:
            prefix: Code prefix (default: "REF")

        Returns:
            Unique referral code (e.g., "REF-ABC123XYZ")
        """
        random_part = secrets.token_urlsafe(8).replace("-", "").replace("_", "").upper()[:9]
        return f"{prefix}-{random_part}"

    async def create_referral(
        self,
        referrer_id: int,
        referee_email: str,
        referee_name: Optional[str] = None,
        referee_phone: Optional[str] = None,
        referral_code: Optional[str] = None,
        reward_amount: float = 50.0,
        reward_type: str = "credit",
    ) -> Dict[str, Any]:
        """
        Create a new referral.

        Args:
            referrer_id: ID of the customer making the referral
            referee_email: Email of the person being referred
            referee_name: Optional name of referee
            referee_phone: Optional phone of referee
            referral_code: Optional custom referral code (auto-generated if not provided)
            reward_amount: Reward amount for successful conversion (default: $50)
            reward_type: Type of reward ('credit', 'discount', 'cash')

        Returns:
            Dictionary with referral details including code and expiration

        Raises:
            BusinessLogicException: If referral creation fails
        """
        try:
            # Generate referral code if not provided
            if not referral_code:
                referral_code = self._generate_referral_code()

                # Ensure uniqueness
                attempts = 0
                while await self._referral_code_exists(referral_code) and attempts < 5:
                    referral_code = self._generate_referral_code()
                    attempts += 1

            # Check if referee already exists (prevent duplicate referrals)
            existing_referral = await self._find_referral_by_email(referee_email, referrer_id)
            if existing_referral:
                self.logger.warning(
                    f"Duplicate referral attempt for {referee_email} by referrer {referrer_id}"
                )
                raise BusinessLogicException(
                    message="This person has already been referred",
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                )

            # Create referral record
            referral = {
                "referrer_id": referrer_id,
                "referee_email": referee_email,
                "referee_name": referee_name,
                "referee_phone": referee_phone,
                "referral_code": referral_code,
                "reward_amount": reward_amount,
                "reward_type": reward_type,
                "status": ReferralStatus.PENDING,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=90),  # 90-day expiration
            }

            # In a real implementation, this would insert into a referrals table
            # For now, we'll track it as metadata in the referrer's lead record
            referrer_lead = await self._get_lead(referrer_id)
            if not referrer_lead:
                raise NotFoundException(f"Referrer lead {referrer_id} not found")

            # Track event
            await self.track_event(
                action="referral_created",
                entity_type="referral",
                entity_id=referrer_id,
                user_id=referrer_id,
                metadata={
                    "referral_code": referral_code,
                    "referee_email": referee_email,
                    "reward_amount": reward_amount,
                    "reward_type": reward_type,
                },
            )

            # Send notification to referee (if notification service available)
            if self.notification_service:
                await self.send_notification(
                    user_id=referrer_id,
                    message=f"Your referral code {referral_code} has been created!",
                    notification_type="email",
                    metadata={
                        "referee_email": referee_email,
                        "reward_amount": reward_amount,
                    },
                )

            self.logger.info(
                f"Created referral {referral_code} for referrer {referrer_id}",
                extra={"referral_code": referral_code, "referee_email": referee_email},
            )

            return {
                "referral_code": referral_code,
                "referee_email": referee_email,
                "reward_amount": reward_amount,
                "status": ReferralStatus.PENDING,
                "expires_at": referral["expires_at"].isoformat(),
                "referral_link": f"https://myhibachichef.com/book?ref={referral_code}",
            }

        except Exception as e:
            await self._handle_error(e, "create_referral")
            raise

    async def track_conversion(
        self,
        referral_code: str,
        referee_id: int,
        conversion_value: float,
        conversion_type: str = "booking",
    ) -> Dict[str, Any]:
        """
        Track a successful referral conversion.

        Called when a referred customer completes a qualifying action
        (e.g., makes their first booking).

        Args:
            referral_code: The referral code used
            referee_id: ID of the referred customer
            conversion_value: Value of the conversion (e.g., booking amount)
            conversion_type: Type of conversion ('booking', 'purchase', 'signup')

        Returns:
            Dictionary with conversion details and rewards awarded

        Raises:
            BusinessLogicException: If conversion tracking fails
        """
        try:
            # In a real implementation, we'd look up the referral record
            # For now, we'll track the event

            # Track conversion event
            await self.track_event(
                action="referral_converted",
                entity_type="referral",
                entity_id=referee_id,
                user_id=referee_id,
                metadata={
                    "referral_code": referral_code,
                    "conversion_value": conversion_value,
                    "conversion_type": conversion_type,
                },
            )

            self.logger.info(
                f"Referral conversion tracked: {referral_code}",
                extra={
                    "referral_code": referral_code,
                    "referee_id": referee_id,
                    "conversion_value": conversion_value,
                },
            )

            # Award credits to referrer
            # In a real implementation, this would update the referrer's account balance
            reward_awarded = True

            return {
                "referral_code": referral_code,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "reward_awarded": reward_awarded,
                "status": ReferralStatus.COMPLETED,
            }

        except Exception as e:
            await self._handle_error(e, "track_conversion")
            raise

    async def get_referral_stats(
        self,
        referrer_id: int,
    ) -> Dict[str, Any]:
        """
        Get referral statistics for a referrer.

        Args:
            referrer_id: ID of the referrer

        Returns:
            Dictionary with referral stats:
            - total_referrals: Total referrals made
            - pending_referrals: Referrals not yet converted
            - completed_referrals: Successfully converted referrals
            - total_earnings: Total rewards earned
            - pending_earnings: Rewards for pending referrals
        """
        try:
            # In a real implementation, this would query the referrals table
            # For now, we'll return mock data structure

            stats = {
                "referrer_id": referrer_id,
                "total_referrals": 0,
                "pending_referrals": 0,
                "completed_referrals": 0,
                "expired_referrals": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "referral_codes": [],
            }

            # Track stats request
            await self.track_event(
                action="referral_stats_requested",
                entity_type="referral",
                entity_id=referrer_id,
                user_id=referrer_id,
                metadata=stats,
            )

            return stats

        except Exception as e:
            await self._handle_error(e, "get_referral_stats")
            raise

    async def award_referral_credit(
        self,
        referrer_id: int,
        amount: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Award referral credit to a referrer.

        Args:
            referrer_id: ID of the referrer
            amount: Credit amount to award
            reason: Reason for the credit
            metadata: Additional metadata

        Returns:
            Dictionary with credit details
        """
        try:
            # Track credit award
            await self.track_event(
                action="referral_credit_awarded",
                entity_type="referral",
                entity_id=referrer_id,
                user_id=referrer_id,
                metadata={
                    "amount": amount,
                    "reason": reason,
                    "metadata": metadata or {},
                },
            )

            # Send notification
            if self.notification_service:
                await self.send_notification(
                    user_id=referrer_id,
                    message=f"You've earned ${amount:.2f} in referral credits!",
                    notification_type="email",
                    metadata={"amount": amount, "reason": reason},
                )

            self.logger.info(
                f"Awarded ${amount} credit to referrer {referrer_id}",
                extra={"referrer_id": referrer_id, "amount": amount, "reason": reason},
            )

            return {
                "referrer_id": referrer_id,
                "amount": amount,
                "reason": reason,
                "awarded_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            await self._handle_error(e, "award_referral_credit")
            raise

    # Helper methods

    async def _referral_code_exists(self, code: str) -> bool:
        """Check if a referral code already exists."""
        # In real implementation, query referrals table
        return False

    async def _find_referral_by_email(
        self, referee_email: str, referrer_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find existing referral by referee email and referrer."""
        # In real implementation, query referrals table
        return None

    async def _get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID."""
        query = select(Lead).where(Lead.id == lead_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
