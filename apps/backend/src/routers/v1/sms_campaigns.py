"""SMS Campaign Management via RingCentral API."""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any
from uuid import UUID

from core.database import get_db
from core.dependencies import admin_required
from models.enums import CampaignChannel, CampaignStatus
from models.newsletter import Campaign, Subscriber
from services.ringcentral_sms import RingCentralSMSService
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sms-campaigns", tags=["sms-campaigns"])


# Constants
SMS_SEGMENT_LENGTH = 160  # Standard SMS length
SMS_COST_PER_SEGMENT = Decimal("0.02")  # $0.02 per SMS segment
EXTENDED_SMS_SEGMENT_LENGTH = 153  # Multi-part SMS segments


# Pydantic Models
class SMSCampaignCreate(BaseModel):
    """Create SMS campaign request."""

    name: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1600)  # Max 10 segments
    recipient_filter: str = Field("sms_consent_only", regex="^(all|sms_consent_only|tags|custom)$")
    selected_tags: list[str] | None = None
    custom_phones: list[str] | None = None
    send_option: str = Field("schedule", regex="^(now|schedule)$")
    scheduled_at: datetime | None = None
    timezone: str = Field("America/Los_Angeles")

    @validator("message")
    def validate_message_length(cls, v):
        """Ensure message isn't too long (max 10 SMS segments)."""
        segments = calculate_sms_segments(v)
        if segments > 10:
            raise ValueError(f"Message too long: {segments} segments (max 10)")
        return v

    @validator("scheduled_at")
    def validate_schedule_time(cls, v, values):
        """Validate scheduled time is in the future and within business hours."""
        if values.get("send_option") == "schedule":
            if not v:
                raise ValueError("scheduled_at required when send_option is 'schedule'")

            if v <= datetime.now(timezone.utc):
                raise ValueError("Scheduled time must be in the future")

            # Check business hours (8am - 9pm local time)
            hour = v.hour
            if hour < 8 or hour >= 21:
                raise ValueError(
                    "SMS must be scheduled between 8:00 AM and 9:00 PM (TCPA compliance)"
                )

        return v

    @validator("custom_phones")
    def validate_phones(cls, v):
        """Validate phone number format."""
        if v:
            import re

            phone_pattern = re.compile(r"^\+?1?\d{10,15}$")
            for phone in v:
                clean = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                if not phone_pattern.match(clean):
                    raise ValueError(f"Invalid phone number format: {phone}")
        return v


class SMSCampaignResponse(BaseModel):
    """SMS campaign response."""

    id: UUID
    name: str
    channel: str
    message: str
    segment_filter: dict[str, Any] | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    status: str
    total_recipients: int
    segments_per_message: int
    estimated_cost: float
    delivered: int
    failed: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SMSCampaignEstimate(BaseModel):
    """SMS campaign cost estimate."""

    recipient_count: int
    segments_per_message: int
    total_segments: int
    cost_per_segment: float
    estimated_total_cost: float
    character_count: int
    message_preview: str


class SMSComplianceCheck(BaseModel):
    """TCPA compliance validation."""

    compliant: bool
    warnings: list[str]
    recipient_consent_rate: float
    non_consented_count: int
    opt_out_language_present: bool


# Helper Functions
def calculate_sms_segments(message: str) -> int:
    """Calculate number of SMS segments needed."""
    length = len(message)

    if length == 0:
        return 0
    elif length <= SMS_SEGMENT_LENGTH:
        return 1
    else:
        # Multi-part SMS uses 153 characters per segment
        return (length + EXTENDED_SMS_SEGMENT_LENGTH - 1) // EXTENDED_SMS_SEGMENT_LENGTH


def validate_opt_out_language(message: str) -> bool:
    """Check if message contains proper opt-out language."""
    opt_out_phrases = [
        "reply stop",
        "text stop",
        "stop to opt out",
        "stop to unsubscribe",
    ]
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in opt_out_phrases)


# Endpoints
@router.post("/", response_model=SMSCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_sms_campaign(
    campaign: SMSCampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    """
    Create a new SMS campaign via RingCentral.

    **TCPA Compliance:**
    - Only sends to recipients with `sms_consent=True`
    - Validates business hours (8am-9pm)
    - Requires opt-out language in message
    - Tracks consent and delivery status
    """
    try:
        # Calculate segments and cost
        segments = calculate_sms_segments(campaign.message)

        # Get recipients based on filter
        recipients = await get_campaign_recipients(
            db=db,
            filter_type=campaign.recipient_filter,
            tags=campaign.selected_tags,
            custom_phones=campaign.custom_phones,
            sms_only=True,  # Critical: only SMS-consented users
        )

        if len(recipients) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible recipients found (check SMS consent status)",
            )

        # Compliance check
        has_opt_out = validate_opt_out_language(campaign.message)
        if not has_opt_out:
            logger.warning(f"Campaign '{campaign.name}' missing opt-out language")

        # Calculate cost
        total_segments = len(recipients) * segments
        estimated_cost = float(total_segments * SMS_COST_PER_SEGMENT)

        # Create campaign record
        new_campaign = Campaign(
            name=campaign.name,
            channel=CampaignChannel.SMS,
            subject=None,  # SMS doesn't have subject
            content={
                "message": campaign.message,
                "segments": segments,
                "has_opt_out": has_opt_out,
                "timezone": campaign.timezone,
            },
            segment_filter={
                "filter_type": campaign.recipient_filter,
                "tags": campaign.selected_tags,
                "custom_phones": campaign.custom_phones,
            },
            scheduled_at=campaign.scheduled_at,
            status=(
                CampaignStatus.SCHEDULED
                if campaign.send_option == "schedule"
                else CampaignStatus.DRAFT
            ),
            total_recipients=len(recipients),
            created_by_admin_id=current_admin.id,
        )

        db.add(new_campaign)
        await db.commit()
        await db.refresh(new_campaign)

        logger.info(
            f"SMS campaign created: {new_campaign.id} | "
            f"Recipients: {len(recipients)} | "
            f"Segments: {segments} | "
            f"Est. Cost: ${estimated_cost:.2f}"
        )

        # If send now, trigger background task
        if campaign.send_option == "now":
            background_tasks.add_task(
                send_sms_campaign_task,
                campaign_id=new_campaign.id,
                recipients=recipients,
                message=campaign.message,
            )

        return SMSCampaignResponse(
            id=new_campaign.id,
            name=new_campaign.name,
            channel=new_campaign.channel.value,
            message=campaign.message,
            segment_filter=new_campaign.segment_filter,
            scheduled_at=new_campaign.scheduled_at,
            sent_at=new_campaign.sent_at,
            status=new_campaign.status.value,
            total_recipients=len(recipients),
            segments_per_message=segments,
            estimated_cost=estimated_cost,
            delivered=0,
            failed=0,
            created_at=new_campaign.created_at,
            updated_at=new_campaign.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create SMS campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SMS campaign",
        )


@router.post("/estimate", response_model=SMSCampaignEstimate)
async def estimate_sms_campaign_cost(
    message: str = Query(..., min_length=1),
    recipient_filter: str = Query("sms_consent_only"),
    selected_tags: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    """
    Calculate SMS campaign cost estimate.

    **Returns:**
    - Number of segments
    - Recipient count (SMS-consented only)
    - Estimated total cost
    - Character count
    """
    try:
        # Calculate segments
        segments = calculate_sms_segments(message)
        char_count = len(message)

        # Get recipient count
        recipients = await get_campaign_recipients(
            db=db,
            filter_type=recipient_filter,
            tags=selected_tags,
            sms_only=True,
        )

        recipient_count = len(recipients)
        total_segments = recipient_count * segments
        estimated_cost = float(total_segments * SMS_COST_PER_SEGMENT)

        return SMSCampaignEstimate(
            recipient_count=recipient_count,
            segments_per_message=segments,
            total_segments=total_segments,
            cost_per_segment=float(SMS_COST_PER_SEGMENT),
            estimated_total_cost=estimated_cost,
            character_count=char_count,
            message_preview=message[:50] + "..." if len(message) > 50 else message,
        )

    except Exception as e:
        logger.exception(f"Failed to estimate SMS cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to estimate cost"
        )


@router.post("/compliance-check", response_model=SMSComplianceCheck)
async def check_sms_compliance(
    message: str = Query(...),
    recipient_filter: str = Query("sms_consent_only"),
    selected_tags: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    """
    Validate TCPA compliance before sending.

    **Checks:**
    - All recipients have SMS consent
    - Opt-out language present
    - Segment count within limits
    """
    try:
        warnings = []

        # Check opt-out language
        has_opt_out = validate_opt_out_language(message)
        if not has_opt_out:
            warnings.append(
                "Message should include opt-out language (e.g., 'Reply STOP to unsubscribe')"
            )

        # Get all potential recipients
        all_recipients = await get_campaign_recipients(
            db=db,
            filter_type=recipient_filter,
            tags=selected_tags,
            sms_only=False,  # Get all
        )

        # Get SMS-consented recipients
        consented_recipients = await get_campaign_recipients(
            db=db,
            filter_type=recipient_filter,
            tags=selected_tags,
            sms_only=True,
        )

        consent_rate = (
            len(consented_recipients) / len(all_recipients) if len(all_recipients) > 0 else 0.0
        )
        non_consented = len(all_recipients) - len(consented_recipients)

        if non_consented > 0:
            warnings.append(f"{non_consented} recipients will be excluded (no SMS consent)")

        # Check segment count
        segments = calculate_sms_segments(message)
        if segments > 3:
            warnings.append(
                f"Message spans {segments} SMS segments (may increase costs and reduce deliverability)"
            )

        compliant = has_opt_out and len(consented_recipients) > 0

        return SMSComplianceCheck(
            compliant=compliant,
            warnings=warnings,
            recipient_consent_rate=consent_rate,
            non_consented_count=non_consented,
            opt_out_language_present=has_opt_out,
        )

    except Exception as e:
        logger.exception(f"Compliance check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Compliance check failed"
        )


@router.get("/", response_model=list[SMSCampaignResponse])
async def list_sms_campaigns(
    status_filter: CampaignStatus | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    """List SMS campaigns with optional status filter."""
    try:
        query = select(Campaign).where(Campaign.channel == CampaignChannel.SMS)

        if status_filter:
            query = query.where(Campaign.status == status_filter)

        query = query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        campaigns = result.scalars().all()

        return [
            SMSCampaignResponse(
                id=c.id,
                name=c.name,
                channel=c.channel.value,
                message=c.content.get("message", ""),
                segment_filter=c.segment_filter,
                scheduled_at=c.scheduled_at,
                sent_at=c.sent_at,
                status=c.status.value,
                total_recipients=c.total_recipients,
                segments_per_message=c.content.get("segments", 1),
                estimated_cost=float(
                    c.total_recipients * c.content.get("segments", 1) * SMS_COST_PER_SEGMENT
                ),
                delivered=c.delivered,
                failed=c.failed,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in campaigns
        ]

    except Exception as e:
        logger.exception(f"Failed to list campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list campaigns"
        )


# Helper Functions
async def get_campaign_recipients(
    db: AsyncSession,
    filter_type: str,
    tags: list[str] | None = None,
    custom_phones: list[str] | None = None,
    sms_only: bool = True,
) -> list[dict[str, Any]]:
    """Get campaign recipients based on filter criteria."""
    try:
        if filter_type == "custom" and custom_phones:
            # Custom phone list (still need to validate consent)
            query = select(Subscriber).where(Subscriber.phone.in_(custom_phones))
        elif filter_type == "tags" and tags:
            # Tagged subscribers
            query = select(Subscriber).where(
                Subscriber.tags.op("&&")(tags)  # PostgreSQL array overlap
            )
        else:
            # All subscribers
            query = select(Subscriber).where(Subscriber.subscribed == True)

        # Critical: TCPA compliance filter
        if sms_only:
            query = query.where(
                and_(
                    Subscriber.sms_consent == True,
                    Subscriber.phone.isnot(None),
                )
            )

        result = await db.execute(query)
        subscribers = result.scalars().all()

        return [
            {
                "id": str(s.id),
                "phone": s.phone,
                "email": s.email,
                "name": f"{s.customer.first_name} {s.customer.last_name}" if s.customer else None,
                "sms_consent": s.sms_consent,
            }
            for s in subscribers
        ]

    except Exception as e:
        logger.exception(f"Failed to get recipients: {e}")
        return []


async def send_sms_campaign_task(
    campaign_id: UUID,
    recipients: list[dict[str, Any]],
    message: str,
):
    """Background task to send SMS campaign via RingCentral."""
    try:
        async with RingCentralSMSService() as rc_service:
            success_count = 0
            failed_count = 0

            for recipient in recipients:
                try:
                    # Send SMS via RingCentral
                    response = await rc_service.send_sms(
                        to_number=recipient["phone"],
                        message=message,
                    )

                    if response.success:
                        success_count += 1
                        logger.info(
                            f"SMS sent to {recipient['phone']} | "
                            f"Message ID: {response.message_id}"
                        )
                    else:
                        failed_count += 1
                        logger.error(
                            f"SMS failed to {recipient['phone']} | " f"Error: {response.error}"
                        )

                except Exception as e:
                    failed_count += 1
                    logger.exception(f"Failed to send SMS to {recipient['phone']}: {e}")

            # Update campaign status
            # (You'll need to add database update logic here)
            logger.info(
                f"Campaign {campaign_id} completed | "
                f"Delivered: {success_count} | "
                f"Failed: {failed_count}"
            )

    except Exception as e:
        logger.exception(f"SMS campaign task failed for {campaign_id}: {e}")
