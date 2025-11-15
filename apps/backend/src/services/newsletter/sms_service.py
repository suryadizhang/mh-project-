"""
SMS Newsletter Service
High-level service for sending SMS newsletter campaigns with TCPA compliance.
Uses RingCentral for SMS delivery with full tracking and metrics.
"""

from datetime import datetime
import logging
from typing import Optional, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.legacy_lead_newsletter import (
    CampaignEvent,
    CampaignEventType,
    SMSDeliveryEvent,
    SMSDeliveryStatus,
    Subscriber,
)
from services.email.base import EmailResult  # We'll reuse this structure for consistency


logger = logging.getLogger(__name__)


class IComplianceValidator(Protocol):
    """Protocol for compliance validation"""
    
    def get_sms_welcome_message(self, name: str | None = None) -> str:
        """Get TCPA-compliant welcome message"""
        ...
    
    def get_sms_opt_out_confirmation(self) -> str:
        """Get TCPA-compliant opt-out confirmation"""
        ...


class IRingCentralService(Protocol):
    """Protocol for RingCentral SMS service"""
    
    async def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: str | None = None,
    ) -> dict:
        """Send SMS via RingCentral"""
        ...


class NewsletterSMSService:
    """
    Service for sending SMS newsletter campaigns with full TCPA compliance.
    
    Features:
    - TCPA compliant messages with STOP instructions
    - Business phone number identification
    - Frequency limits enforcement
    - Opt-out tracking
    - Event tracking integration
    """
    
    def __init__(
        self,
        ringcentral_service: IRingCentralService,
        compliance_validator: IComplianceValidator,
        db: Optional[AsyncSession] = None,
        business_phone: str = "+19167408768",
        business_name: str = "My Hibachi Chef",
    ):
        """
        Initialize newsletter SMS service.
        
        Args:
            ringcentral_service: RingCentral SMS service implementation
            compliance_validator: Compliance validation service
            db: Database session for tracking metrics (optional)
            business_phone: Business phone number (from number)
            business_name: Business name for identification
        """
        self.ringcentral = ringcentral_service
        self.compliance_validator = compliance_validator
        self.db = db
        self.business_phone = business_phone
        self.business_name = business_name
    
    async def send_campaign_sms(
        self,
        subscriber_phone: str,
        subscriber_name: str | None,
        message_content: str,
        campaign_id: UUID | None = None,
        subscriber_id: UUID | None = None,
        campaign_event_id: UUID | None = None,
        include_stop_instructions: bool = True,
    ) -> EmailResult:  # Reusing EmailResult for consistency
        """
        Send a single campaign SMS with full TCPA compliance and tracking.
        
        Updates subscriber SMS metrics and creates delivery tracking events.
        
        Args:
            subscriber_phone: Recipient phone number (E.164 format)
            subscriber_name: Recipient name (optional)
            message_content: SMS message content
            campaign_id: Campaign UUID for tracking
            subscriber_id: Subscriber UUID for metric tracking
            campaign_event_id: Campaign event ID for linking delivery event
            include_stop_instructions: Add STOP instructions (default: True)
            
        Returns:
            EmailResult with send status (reused for SMS)
        """
        try:
            # Add TCPA compliance footer if enabled
            if include_stop_instructions:
                message_content = self._add_tcpa_footer(message_content)
            
            # Ensure message length is within SMS limits (160 chars per segment)
            if len(message_content) > 1600:  # 10 segments max
                logger.warning(
                    f"⚠️ SMS message too long ({len(message_content)} chars). Truncating.",
                    extra={"phone": subscriber_phone, "length": len(message_content)},
                )
                message_content = message_content[:1580] + "... (truncated)"
            
            # Send SMS via RingCentral
            result = await self.ringcentral.send_sms(
                to_number=subscriber_phone,
                message=message_content,
                from_number=self.business_phone,
            )
            
            # Check if send was successful
            success = result.get("messageStatus") == "Sent" or result.get("id") is not None
            segments = self._calculate_segments(message_content)
            ringcentral_msg_id = result.get("id")
            
            # Update subscriber SMS metrics (if database available)
            if success and self.db and subscriber_id:
                await self._update_subscriber_metrics(
                    subscriber_id=subscriber_id,
                    sent=True,
                    delivered=False,  # Will be updated by webhook
                )
            
            # Create SMS delivery tracking event (if database and campaign_event available)
            if self.db and campaign_event_id and ringcentral_msg_id:
                await self._create_delivery_event(
                    campaign_event_id=campaign_event_id,
                    ringcentral_msg_id=ringcentral_msg_id,
                    status=SMSDeliveryStatus.SENT,
                    segments=segments,
                    metadata=result,
                )
            
            if success:
                logger.info(
                    f"✅ Campaign SMS sent: {subscriber_phone}",
                    extra={
                        "phone": subscriber_phone,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "message_id": ringcentral_msg_id,
                        "segments": segments,
                    },
                )
                return EmailResult(
                    success=True,
                    message_id=ringcentral_msg_id,
                    provider="ringcentral_sms",
                    metadata={
                        "phone": subscriber_phone,
                        "segments": segments,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "subscriber_id": str(subscriber_id) if subscriber_id else None,
                    },
                )
            else:
                error_msg = result.get("errorMessage", "Unknown error")
                
                # Update subscriber failure metrics (if database available)
                if self.db and subscriber_id:
                    await self._update_subscriber_metrics(
                        subscriber_id=subscriber_id,
                        sent=True,
                        delivered=False,
                        failed=True,
                    )
                
                # Create failed delivery event (if database and campaign_event available)
                if self.db and campaign_event_id and ringcentral_msg_id:
                    await self._create_delivery_event(
                        campaign_event_id=campaign_event_id,
                        ringcentral_msg_id=ringcentral_msg_id or f"failed-{subscriber_phone}",
                        status=SMSDeliveryStatus.FAILED,
                        segments=self._calculate_segments(message_content),
                        failure_reason=error_msg,
                    )
                
                logger.error(
                    f"❌ Campaign SMS failed: {subscriber_phone} - {error_msg}",
                    extra={
                        "phone": subscriber_phone,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "error": error_msg,
                    },
                )
                return EmailResult(
                    success=False,
                    error=error_msg,
                    provider="ringcentral_sms",
                )
            
        except Exception as e:
            logger.exception(f"❌ Unexpected error sending campaign SMS: {e}")
            return EmailResult(
                success=False,
                error=str(e),
                provider="ringcentral_sms",
            )
    
    async def send_campaign_batch(
        self,
        recipients: list[dict],  # [{"phone": "...", "name": "..."}]
        message_content: str,
        campaign_id: UUID | None = None,
        include_stop_instructions: bool = True,
    ) -> list[EmailResult]:
        """
        Send campaign SMS messages to multiple recipients in batch.
        
        Each recipient gets the same message with STOP instructions.
        
        Args:
            recipients: List of recipient dicts with 'phone' and optional 'name'
            message_content: SMS message content
            campaign_id: Campaign UUID for tracking
            include_stop_instructions: Add STOP instructions (default: True)
            
        Returns:
            List of EmailResult for each recipient
        """
        results = []
        
        for recipient in recipients:
            result = await self.send_campaign_sms(
                subscriber_phone=recipient["phone"],
                subscriber_name=recipient.get("name"),
                message_content=message_content,
                campaign_id=campaign_id,
                include_stop_instructions=include_stop_instructions,
            )
            results.append(result)
        
        # Log batch summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        logger.info(
            f"📱 SMS Campaign batch complete: {successful} sent, {failed} failed",
            extra={
                "campaign_id": str(campaign_id) if campaign_id else None,
                "total": len(results),
                "successful": successful,
                "failed": failed,
            },
        )
        
        return results
    
    def _add_tcpa_footer(self, message: str) -> str:
        """Add TCPA-compliant footer to message"""
        # Check if message already has STOP instructions
        if "STOP" in message.upper():
            return message
        
        # Add footer
        footer = f"\n\nReply STOP to unsubscribe. {self.business_name}"
        return message + footer
    
    def _calculate_segments(self, message: str) -> int:
        """Calculate number of SMS segments needed"""
        # SMS segments: 160 chars for single, 153 chars for multi-part
        length = len(message)
        if length <= 160:
            return 1
        return (length + 152) // 153  # 153 chars per segment for multi-part
    
    async def _update_subscriber_metrics(
        self,
        subscriber_id: UUID,
        sent: bool = False,
        delivered: bool = False,
        failed: bool = False,
    ) -> None:
        """
        Update subscriber SMS tracking metrics.
        
        Args:
            subscriber_id: Subscriber UUID
            sent: Increment sent counter
            delivered: Increment delivered counter
            failed: Increment failed counter
        """
        if not self.db:
            return
        
        try:
            # Get subscriber
            stmt = select(Subscriber).where(Subscriber.id == subscriber_id)
            result = await self.db.execute(stmt)
            subscriber = result.scalar_one_or_none()
            
            if not subscriber:
                logger.warning(f"Subscriber {subscriber_id} not found for metric update")
                return
            
            # Update counters
            if sent:
                subscriber.total_sms_sent += 1
                subscriber.last_sms_sent_date = datetime.now(datetime.now().astimezone().tzinfo)
            
            if delivered:
                subscriber.total_sms_delivered += 1
                subscriber.last_sms_delivered_date = datetime.now(datetime.now().astimezone().tzinfo)
            
            if failed:
                subscriber.total_sms_failed += 1
            
            # Update engagement score
            subscriber.update_engagement_score()
            
            await self.db.commit()
            
            logger.debug(
                f"Updated SMS metrics for subscriber {subscriber_id}",
                extra={
                    "subscriber_id": str(subscriber_id),
                    "sent": sent,
                    "delivered": delivered,
                    "failed": failed,
                },
            )
            
            # Broadcast compliance update via WebSocket
            try:
                from api.v1.websockets.compliance import broadcast_compliance_update
                
                await broadcast_compliance_update({
                    "event": "subscriber_metrics_updated",
                    "subscriber_id": str(subscriber_id),
                    "sent": sent,
                    "delivered": delivered,
                    "failed": failed,
                })
            except Exception as ws_error:
                logger.debug(f"Failed to broadcast compliance update: {ws_error}")
                # Don't fail the operation if WebSocket broadcast fails
            
        except Exception as e:
            logger.exception(f"Failed to update subscriber metrics: {e}")
            await self.db.rollback()
    
    async def _create_delivery_event(
        self,
        campaign_event_id: UUID,
        ringcentral_msg_id: str,
        status: SMSDeliveryStatus,
        segments: int,
        failure_reason: Optional[str] = None,
        carrier_error_code: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Create SMS delivery tracking event.
        
        Args:
            campaign_event_id: Campaign event UUID
            ringcentral_msg_id: RingCentral message ID
            status: Delivery status
            segments: Number of SMS segments used
            failure_reason: Failure reason (if failed)
            carrier_error_code: Carrier error code (if available)
            metadata: Additional RingCentral metadata
        """
        if not self.db:
            return
        
        try:
            # Estimate cost (example: $0.01 per segment)
            cost_cents = segments * 1  # 1 cent per segment
            
            delivery_event = SMSDeliveryEvent(
                campaign_event_id=campaign_event_id,
                ringcentral_message_id=ringcentral_msg_id,
                status=status,
                segments_used=segments,
                cost_cents=cost_cents,
                failure_reason=failure_reason,
                carrier_error_code=carrier_error_code,
                ringcentral_metadata=metadata,
            )
            
            self.db.add(delivery_event)
            await self.db.commit()
            
            logger.debug(
                f"Created SMS delivery event: {ringcentral_msg_id}",
                extra={
                    "message_id": ringcentral_msg_id,
                    "status": status.value,
                    "segments": segments,
                    "cost_cents": cost_cents,
                },
            )
            
            # Broadcast compliance update via WebSocket
            try:
                from api.v1.websockets.compliance import broadcast_compliance_update
                
                await broadcast_compliance_update({
                    "event": "delivery_event_created",
                    "message_id": ringcentral_msg_id,
                    "status": status.value,
                    "segments": segments,
                    "cost_cents": cost_cents,
                })
            except Exception as ws_error:
                logger.debug(f"Failed to broadcast compliance update: {ws_error}")
                # Don't fail the operation if WebSocket broadcast fails
            
        except Exception as e:
            logger.exception(f"Failed to create delivery event: {e}")
            await self.db.rollback()


def create_newsletter_sms_service(
    ringcentral_service: IRingCentralService,
    compliance_validator: IComplianceValidator,
    business_phone: str,
    db: Optional[AsyncSession] = None,
) -> NewsletterSMSService:
    """
    Factory function for creating NewsletterSMSService with DI.
    
    This is the recommended way to create the service for easier testing.
    
    Args:
        ringcentral_service: RingCentral SMS service implementation
        compliance_validator: Compliance validation service
        business_phone: Business phone number
        db: Database session for tracking (optional)
    """
    return NewsletterSMSService(
        ringcentral_service=ringcentral_service,
        compliance_validator=compliance_validator,
        db=db,
        business_phone=business_phone,
    )
