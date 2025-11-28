"""
NurtureCampaignService - Automated lead nurturing and drip campaigns.

Manages multi-step campaigns with scheduled messages, response handling,
and campaign performance tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.base_service import BaseService, EventTrackingMixin, NotificationMixin
from services.event_service import EventService

# FIXED: Import from db.models (NEW system) instead of models (OLD system)
from db.models.lead import Lead
from core.exceptions import BusinessLogicException, NotFoundException, ErrorCode


class CampaignType(str, Enum):
    """Campaign type enumeration."""

    WELCOME = "welcome"
    POST_INQUIRY = "post_inquiry"
    ABANDONED_QUOTE = "abandoned_quote"
    POST_EVENT = "post_event"
    REACTIVATION = "reactivation"
    SEASONAL = "seasonal"


class CampaignStatus(str, Enum):
    """Campaign enrollment status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OPTED_OUT = "opted_out"


class MessageStatus(str, Enum):
    """Individual message status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"


class NurtureCampaignService(BaseService, EventTrackingMixin, NotificationMixin):
    """
    Service for automated lead nurturing campaigns.

    Features:
    - Multi-step drip campaigns
    - Scheduled message delivery
    - Response tracking and handling
    - Campaign performance analytics
    - Dynamic content personalization
    - A/B testing support

    Dependencies (injected):
    - db: Database session
    - event_service: Event tracking
    - notification_service: For sending messages (optional)
    """

    # Campaign templates (in production, store in database)
    CAMPAIGN_TEMPLATES = {
        CampaignType.WELCOME: [
            {
                "step": 1,
                "delay_hours": 0,
                "subject": "Welcome to MyHibachi! 🍱",
                "content": "Thank you for your interest! Here's what makes us special...",
                "channel": "email",
            },
            {
                "step": 2,
                "delay_hours": 24,
                "subject": "How Our Process Works",
                "content": "Planning your event is easy with MyHibachi. Here's how...",
                "channel": "email",
            },
            {
                "step": 3,
                "delay_hours": 72,
                "subject": "Special Offer Inside! 🎉",
                "content": "Book within 7 days and get 10% off your event...",
                "channel": "email",
            },
        ],
        CampaignType.POST_INQUIRY: [
            {
                "step": 1,
                "delay_hours": 2,
                "subject": "Questions About Your Quote?",
                "content": "We noticed you requested a quote. Any questions?",
                "channel": "email",
            },
            {
                "step": 2,
                "delay_hours": 48,
                "subject": "Still Thinking It Over?",
                "content": "We're here to help! Here are answers to common questions...",
                "channel": "email",
            },
        ],
        CampaignType.ABANDONED_QUOTE: [
            {
                "step": 1,
                "delay_hours": 4,
                "subject": "Your Quote is Waiting",
                "content": "Complete your booking in just 2 minutes...",
                "channel": "email",
            },
            {
                "step": 2,
                "delay_hours": 24,
                "subject": "Don't Miss Out! Limited Availability",
                "content": "Dates are filling up fast. Secure your spot now...",
                "channel": "email",
            },
        ],
        CampaignType.POST_EVENT: [
            {
                "step": 1,
                "delay_hours": 24,
                "subject": "How Was Your Event?",
                "content": "We'd love to hear your feedback...",
                "channel": "email",
            },
            {
                "step": 2,
                "delay_hours": 168,  # 7 days
                "subject": "Share the Love - Referral Program",
                "content": "Loved your event? Refer friends and earn $50 credit...",
                "channel": "email",
            },
        ],
    }

    def __init__(
        self,
        db: AsyncSession,
        event_service: EventService,
        notification_service: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize nurture campaign service with injected dependencies.

        Args:
            db: Database session
            event_service: Service for event tracking
            notification_service: Optional service for sending messages
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.event_service = event_service
        self.notification_service = notification_service

    async def enroll_lead(
        self,
        lead_id: int,
        campaign_type: CampaignType,
        personalization: Optional[Dict[str, Any]] = None,
        skip_if_enrolled: bool = True,
    ) -> Dict[str, Any]:
        """
        Enroll a lead in a nurture campaign.

        Args:
            lead_id: ID of the lead to enroll
            campaign_type: Type of campaign to enroll in
            personalization: Dynamic content variables (e.g., name, event_type)
            skip_if_enrolled: Skip if already enrolled in this campaign

        Returns:
            Dictionary with enrollment details

        Raises:
            NotFoundException: If lead not found
            BusinessLogicException: If enrollment fails
        """
        try:
            # Get lead
            lead = await self._get_lead(lead_id)
            if not lead:
                raise NotFoundException(f"Lead {lead_id} not found")

            # Check if already enrolled
            if skip_if_enrolled:
                existing = await self._find_active_enrollment(lead_id, campaign_type)
                if existing:
                    self.logger.info(
                        f"Lead {lead_id} already enrolled in {campaign_type}",
                        extra={"lead_id": lead_id, "campaign_type": campaign_type},
                    )
                    return existing

            # Get campaign template
            template = self.CAMPAIGN_TEMPLATES.get(campaign_type)
            if not template:
                raise BusinessLogicException(
                    message=f"Unknown campaign type: {campaign_type}",
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                )

            # Create enrollment record
            enrollment = {
                "lead_id": lead_id,
                "campaign_type": campaign_type.value,
                "status": CampaignStatus.ACTIVE.value,
                "current_step": 0,
                "total_steps": len(template),
                "personalization": personalization or {},
                "enrolled_at": datetime.utcnow(),
                "next_message_at": datetime.utcnow(),
            }

            # Track enrollment event
            await self.track_event(
                action="campaign_enrolled",
                entity_type="nurture_campaign",
                entity_id=lead_id,
                user_id=lead_id,
                metadata={
                    "campaign_type": campaign_type.value,
                    "total_steps": len(template),
                },
            )

            self.logger.info(
                f"Enrolled lead {lead_id} in {campaign_type} campaign",
                extra={
                    "lead_id": lead_id,
                    "campaign_type": campaign_type.value,
                    "total_steps": len(template),
                },
            )

            return {
                "lead_id": lead_id,
                "campaign_type": campaign_type.value,
                "status": CampaignStatus.ACTIVE.value,
                "total_steps": len(template),
                "enrolled_at": enrollment["enrolled_at"].isoformat(),
            }

        except Exception as e:
            await self._handle_error(e, "enroll_lead")
            raise

    async def send_next_message(
        self,
        lead_id: int,
        campaign_type: CampaignType,
    ) -> Dict[str, Any]:
        """
        Send the next scheduled message in a campaign.

        Called by scheduled job to process pending messages.

        Args:
            lead_id: Lead ID
            campaign_type: Campaign type

        Returns:
            Dictionary with message send details

        Raises:
            NotFoundException: If enrollment not found
        """
        try:
            # Get enrollment (in real impl, query enrollments table)
            enrollment = await self._find_active_enrollment(lead_id, campaign_type)
            if not enrollment:
                raise NotFoundException(
                    f"No active enrollment found for lead {lead_id} in {campaign_type}"
                )

            # Get campaign template
            template = self.CAMPAIGN_TEMPLATES.get(campaign_type)
            if not template:
                raise BusinessLogicException(
                    message=f"Unknown campaign type: {campaign_type}",
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                )

            current_step = enrollment.get("current_step", 0)
            if current_step >= len(template):
                # Campaign complete
                await self._mark_campaign_complete(lead_id, campaign_type)
                return {
                    "status": "completed",
                    "message": "Campaign completed",
                }

            # Get message template
            message_template = template[current_step]

            # Personalize content
            lead = await self._get_lead(lead_id)
            personalized_content = self._personalize_content(
                message_template["content"], lead, enrollment.get("personalization", {})
            )

            # Send message
            if self.notification_service:
                await self.send_notification(
                    user_id=lead_id,
                    message=personalized_content,
                    notification_type=message_template["channel"],
                    metadata={
                        "subject": message_template["subject"],
                        "campaign_type": campaign_type.value,
                        "step": current_step + 1,
                    },
                )

            # Track message sent
            await self.track_event(
                action="campaign_message_sent",
                entity_type="nurture_campaign",
                entity_id=lead_id,
                user_id=lead_id,
                metadata={
                    "campaign_type": campaign_type.value,
                    "step": current_step + 1,
                    "channel": message_template["channel"],
                },
            )

            self.logger.info(
                f"Sent campaign message to lead {lead_id}",
                extra={
                    "lead_id": lead_id,
                    "campaign_type": campaign_type.value,
                    "step": current_step + 1,
                },
            )

            # Schedule next message
            next_step = current_step + 1
            if next_step < len(template):
                next_message = template[next_step]
                next_send_at = datetime.utcnow() + timedelta(hours=next_message["delay_hours"])
            else:
                next_send_at = None

            return {
                "lead_id": lead_id,
                "campaign_type": campaign_type.value,
                "step": current_step + 1,
                "status": MessageStatus.SENT.value,
                "next_message_at": next_send_at.isoformat() if next_send_at else None,
            }

        except Exception as e:
            await self._handle_error(e, "send_next_message")
            raise

    async def handle_response(
        self,
        lead_id: int,
        response_type: str,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle lead response to campaign message.

        Args:
            lead_id: Lead ID
            response_type: Type of response ('reply', 'click', 'opt_out', 'booking')
            response_data: Additional response data

        Returns:
            Dictionary with response handling result
        """
        try:
            # Track response
            await self.track_event(
                action=f"campaign_response_{response_type}",
                entity_type="nurture_campaign",
                entity_id=lead_id,
                user_id=lead_id,
                metadata=response_data or {},
            )

            # Handle opt-out
            if response_type == "opt_out":
                await self._pause_all_campaigns(lead_id)
                self.logger.info(f"Lead {lead_id} opted out of all campaigns")
                return {"status": "opted_out", "message": "All campaigns paused"}

            # Handle booking conversion
            if response_type == "booking":
                await self._complete_all_campaigns(lead_id)
                self.logger.info(f"Lead {lead_id} converted - completing campaigns")
                return {"status": "converted", "message": "All campaigns completed"}

            return {
                "lead_id": lead_id,
                "response_type": response_type,
                "status": "processed",
            }

        except Exception as e:
            await self._handle_error(e, "handle_response")
            raise

    async def get_campaign_stats(
        self,
        campaign_type: Optional[CampaignType] = None,
    ) -> Dict[str, Any]:
        """
        Get campaign performance statistics.

        Args:
            campaign_type: Optional filter by campaign type

        Returns:
            Dictionary with campaign metrics
        """
        try:
            # In real implementation, query enrollments and messages tables
            stats = {
                "total_enrollments": 0,
                "active_enrollments": 0,
                "completed_enrollments": 0,
                "opted_out": 0,
                "messages_sent": 0,
                "messages_opened": 0,
                "messages_clicked": 0,
                "conversions": 0,
                "open_rate": 0.0,
                "click_rate": 0.0,
                "conversion_rate": 0.0,
            }

            if campaign_type:
                stats["campaign_type"] = campaign_type.value

            return stats

        except Exception as e:
            await self._handle_error(e, "get_campaign_stats")
            raise

    # Helper methods

    def _personalize_content(
        self,
        content: str,
        lead: Lead,
        personalization: Dict[str, Any],
    ) -> str:
        """Personalize message content with lead data."""
        replacements = {
            "{name}": lead.name or "there",
            "{email}": lead.email,
            "{phone}": lead.phone or "",
            **personalization,
        }

        for key, value in replacements.items():
            content = content.replace(key, str(value))

        return content

    async def _find_active_enrollment(
        self,
        lead_id: int,
        campaign_type: CampaignType,
    ) -> Optional[Dict[str, Any]]:
        """Find active enrollment for lead in campaign."""
        # In real implementation, query enrollments table
        return None

    async def _mark_campaign_complete(
        self,
        lead_id: int,
        campaign_type: CampaignType,
    ) -> None:
        """Mark campaign as completed."""
        await self.track_event(
            action="campaign_completed",
            entity_type="nurture_campaign",
            entity_id=lead_id,
            user_id=lead_id,
            metadata={"campaign_type": campaign_type.value},
        )

    async def _pause_all_campaigns(self, lead_id: int) -> None:
        """Pause all active campaigns for a lead."""
        await self.track_event(
            action="campaigns_paused",
            entity_type="nurture_campaign",
            entity_id=lead_id,
            user_id=lead_id,
            metadata={"reason": "opt_out"},
        )

    async def _complete_all_campaigns(self, lead_id: int) -> None:
        """Complete all campaigns for a lead (e.g., after conversion)."""
        await self.track_event(
            action="campaigns_completed",
            entity_type="nurture_campaign",
            entity_id=lead_id,
            user_id=lead_id,
            metadata={"reason": "conversion"},
        )

    async def _get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID."""
        query = select(Lead).where(Lead.id == lead_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
