"""Newsletter and campaign management API endpoints."""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from core.database import get_db
from models.legacy_lead_newsletter import (
    Campaign,
    CampaignChannel,
    CampaignEvent,
    CampaignEventType,
    CampaignStatus,
    Subscriber,
)
from services.ai_lead_management import get_social_media_ai
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/newsletter", tags=["newsletter"])


# Pydantic models
class SubscriberCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    source: str | None = None
    sms_consent: bool = False
    email_consent: bool = True
    tags: list[str] | None = None


class SubscriberUpdate(BaseModel):
    phone: str | None = None
    sms_consent: bool | None = None
    email_consent: bool | None = None
    tags: list[str] | None = None
    subscribed: bool | None = None


class SubscriberResponse(BaseModel):
    id: UUID
    customer_id: UUID | None
    email: str
    phone: str | None
    subscribed: bool
    source: str | None
    sms_consent: bool
    email_consent: bool
    tags: list[str] | None
    engagement_score: int
    total_emails_sent: int
    total_emails_opened: int
    total_clicks: int
    last_email_sent_date: datetime | None
    last_opened_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    channel: CampaignChannel
    subject: str | None = None
    content: dict[str, Any]
    segment_filter: dict[str, Any] | None = None
    scheduled_at: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    content: dict[str, Any] | None = None
    segment_filter: dict[str, Any] | None = None
    scheduled_at: datetime | None = None
    status: CampaignStatus | None = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    channel: CampaignChannel
    subject: str | None
    content: dict[str, Any]
    segment_filter: dict[str, Any] | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    status: CampaignStatus
    total_recipients: int
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class CampaignStatsResponse(BaseModel):
    campaign_id: UUID
    total_recipients: int
    delivered: int
    opened: int
    clicked: int
    bounced: int
    unsubscribed: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float


class CampaignEventResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    subscriber_id: UUID
    type: CampaignEventType
    payload: dict[str, Any] | None
    occurred_at: datetime

    class Config:
        from_attributes = True


# Subscriber endpoints
@router.post("/subscribers", response_model=SubscriberResponse)
async def create_subscriber(
    subscriber_data: SubscriberCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new newsletter subscriber."""

    # Check if subscriber already exists
    stmt = select(Subscriber).where(
        Subscriber.email_enc
        == Subscriber._encrypt_email(subscriber_data.email)
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscriber already exists",
        )

    subscriber = Subscriber(
        email=subscriber_data.email,
        phone=subscriber_data.phone,
        source=subscriber_data.source,
        sms_consent=subscriber_data.sms_consent,
        email_consent=subscriber_data.email_consent,
        tags=subscriber_data.tags or [],
        consent_updated_at=datetime.now(),
    )

    db.add(subscriber)
    await db.commit()
    await db.refresh(subscriber)

    return subscriber


@router.get("/subscribers", response_model=list[SubscriberResponse])
async def list_subscribers(
    subscribed: bool | None = Query(None),
    tags: list[str] | None = Query(None),
    engagement_min: int | None = Query(None),
    engagement_max: int | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List newsletter subscribers with filtering."""

    stmt = select(Subscriber)

    if subscribed is not None:
        stmt = stmt.where(Subscriber.subscribed == subscribed)

    if tags:
        stmt = stmt.where(Subscriber.tags.overlap(tags))

    if engagement_min is not None:
        stmt = stmt.where(Subscriber.engagement_score >= engagement_min)

    if engagement_max is not None:
        stmt = stmt.where(Subscriber.engagement_score <= engagement_max)

    stmt = (
        stmt.order_by(desc(Subscriber.engagement_score))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    subscribers = result.scalars().all()

    return subscribers


@router.get("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Get subscriber details."""

    stmt = select(Subscriber).where(Subscriber.id == subscriber_id)
    result = await db.execute(stmt)
    subscriber = result.scalars().first()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    return subscriber


@router.put("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: UUID,
    subscriber_update: SubscriberUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update subscriber information."""

    subscriber = (
        (
            await db.execute(
                select(Subscriber).where(Subscriber.id == subscriber_id)
            )
        )
        .scalars()
        .first()
    )
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    if subscriber_update.phone is not None:
        subscriber.phone = subscriber_update.phone

    if subscriber_update.sms_consent is not None:
        subscriber.sms_consent = subscriber_update.sms_consent
        subscriber.consent_updated_at = datetime.now()

    if subscriber_update.email_consent is not None:
        subscriber.email_consent = subscriber_update.email_consent
        subscriber.consent_updated_at = datetime.now()

    if subscriber_update.tags is not None:
        subscriber.tags = subscriber_update.tags

    if subscriber_update.subscribed is not None:
        subscriber.subscribed = subscriber_update.subscribed
        if not subscriber_update.subscribed:
            subscriber.unsubscribed_at = datetime.now()

    # Update engagement score
    subscriber.update_engagement_score()

    await db.commit()

    return subscriber


@router.delete("/subscribers/{subscriber_id}")
async def unsubscribe_subscriber(
    subscriber_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Unsubscribe a subscriber."""

    subscriber = (
        (
            await db.execute(
                select(Subscriber).where(Subscriber.id == subscriber_id)
            )
        )
        .scalars()
        .first()
    )
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    subscriber.subscribed = False
    subscriber.unsubscribed_at = datetime.now()

    await db.commit()

    return {"success": True, "message": "Subscriber unsubscribed successfully"}


# Campaign endpoints
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: AsyncSession = Depends(get_db),
):
    """Create a new marketing campaign."""

    campaign = Campaign(
        name=campaign_data.name,
        channel=campaign_data.channel,
        subject=campaign_data.subject,
        content=campaign_data.content,
        segment_filter=campaign_data.segment_filter,
        scheduled_at=campaign_data.scheduled_at,
        created_by=current_user,
    )

    db.add(campaign)
    await db.commit()

    return campaign


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    status: CampaignStatus | None = Query(None),
    channel: CampaignChannel | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List marketing campaigns."""

    query = select(Campaign)

    if status:
        query = query.where(Campaign.status == status)

    if channel:
        query = query.where(Campaign.channel == channel)

    campaigns = (
        query.order_by(desc(Campaign.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get campaign details."""

    campaign = (
        (await db.execute(select(Campaign).where(Campaign.id == campaign_id)))
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_update: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update campaign information."""

    campaign = (
        (await db.execute(select(Campaign).where(Campaign.id == campaign_id)))
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    if campaign.status in [CampaignStatus.SENT, CampaignStatus.SENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update sent or sending campaign",
        )

    for field, value in campaign_update.dict(exclude_unset=True).items():
        setattr(campaign, field, value)

    await db.commit()

    return campaign


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Send campaign to subscribers."""

    campaign = (
        (await db.execute(select(Campaign).where(Campaign.id == campaign_id)))
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign must be in draft status to send",
        )

    # Update campaign status
    campaign.status = CampaignStatus.SCHEDULED
    if not campaign.scheduled_at:
        campaign.scheduled_at = datetime.now()

    await db.commit()

    # Schedule campaign sending
    background_tasks.add_task(_send_campaign_async, campaign_id)

    return {"success": True, "message": "Campaign scheduled for sending"}


@router.get(
    "/campaigns/{campaign_id}/stats", response_model=CampaignStatsResponse
)
async def get_campaign_stats(
    campaign_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Get campaign performance statistics."""

    campaign = (
        (await db.execute(select(Campaign).where(Campaign.id == campaign_id)))
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )

    # Count events by type
    stmt = (
        select(CampaignEvent.type, func.count(CampaignEvent.id).label("count"))
        .where(CampaignEvent.campaign_id == campaign_id)
        .group_by(CampaignEvent.type)
    )
    result = await db.execute(stmt)
    event_counts = result.all()

    counts = {event_type.value: 0 for event_type in CampaignEventType}
    for event_type, count in event_counts:
        counts[event_type.value] = count

    total_recipients = campaign.total_recipients or 1  # Avoid division by zero

    return CampaignStatsResponse(
        campaign_id=campaign_id,
        total_recipients=total_recipients,
        delivered=counts["delivered"],
        opened=counts["opened"],
        clicked=counts["clicked"],
        bounced=counts["bounced"],
        unsubscribed=counts["unsubscribed"],
        delivery_rate=counts["delivered"] / total_recipients,
        open_rate=counts["opened"] / total_recipients,
        click_rate=counts["clicked"] / total_recipients,
        bounce_rate=counts["bounced"] / total_recipients,
    )


@router.get(
    "/campaigns/{campaign_id}/events",
    response_model=list[CampaignEventResponse],
)
async def get_campaign_events(
    campaign_id: UUID,
    event_type: CampaignEventType | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get campaign events."""

    query = select(CampaignEvent).where(
        CampaignEvent.campaign_id == campaign_id
    )

    if event_type:
        query = query.where(CampaignEvent.type == event_type)

    events = (
        query.order_by(desc(CampaignEvent.occurred_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return events


@router.post("/campaigns/ai-content")
async def generate_campaign_content(
    campaign_type: str,
    target_audience: str,
    additional_context: dict[str, Any] | None = None,
):
    """Generate AI-powered campaign content."""

    social_ai = await get_social_media_ai()
    content = await social_ai.create_promotional_content(
        campaign_type, target_audience
    )

    return {
        "generated_content": content,
        "campaign_type": campaign_type,
        "target_audience": target_audience,
    }


# Segmentation endpoints
@router.get("/segments/preview")
async def preview_segment(
    filter_criteria: dict[str, Any], db: AsyncSession = Depends(get_db)
):
    """Preview subscribers matching segment criteria."""

    query = select(Subscriber).where(Subscriber.subscribed)

    # Apply segment filters
    if "tags" in filter_criteria:
        query = query.where(Subscriber.tags.overlap(filter_criteria["tags"]))

    if "engagement_min" in filter_criteria:
        query = query.where(
            Subscriber.engagement_score >= filter_criteria["engagement_min"]
        )

    if "engagement_max" in filter_criteria:
        query = query.where(
            Subscriber.engagement_score <= filter_criteria["engagement_max"]
        )

    if "last_opened_days" in filter_criteria:
        cutoff_date = datetime.now() - timedelta(
            days=filter_criteria["last_opened_days"]
        )
        query = query.where(Subscriber.last_opened_date >= cutoff_date)

    # Compute total count using COUNT() and fetch a small sample asynchronously
    # Build where clause for count (re-use query filters)
    # Note: SQLAlchemy select objects do not expose a public API for extracting the where-clause
    # so we rebuild a count statement using the same filtering logic.
    count_stmt = select(func.count()).select_from(Subscriber)
    # Re-apply filters to count_stmt if present
    if "tags" in filter_criteria:
        count_stmt = count_stmt.where(
            Subscriber.tags.overlap(filter_criteria["tags"])
        )
    if "engagement_min" in filter_criteria:
        count_stmt = count_stmt.where(
            Subscriber.engagement_score >= filter_criteria["engagement_min"]
        )
    if "engagement_max" in filter_criteria:
        count_stmt = count_stmt.where(
            Subscriber.engagement_score <= filter_criteria["engagement_max"]
        )
    if "last_opened_days" in filter_criteria:
        cutoff_date = datetime.now() - timedelta(
            days=filter_criteria["last_opened_days"]
        )
        count_stmt = count_stmt.where(
            Subscriber.last_opened_date >= cutoff_date
        )

    total_res = await db.execute(count_stmt)
    total_count = int(total_res.scalar_one())

    sample_stmt = query.limit(10)
    sample_res = await db.execute(sample_stmt)
    sample = sample_res.scalars().all()

    return {"total_count": total_count, "sample_subscribers": sample}


# Background task functions
async def _send_campaign_async(campaign_id: UUID):
    """Send campaign in background."""
    from core.database import get_db_context

    async with get_db_context() as db:
        try:
            campaign = (
                (
                    await db.execute(
                        select(Campaign).where(Campaign.id == campaign_id)
                    )
                )
                .scalars()
                .first()
            )
            if not campaign:
                return

            # Get target subscribers
            query = select(Subscriber).where(Subscriber.subscribed)

            # Apply segment filters if any
            if campaign.segment_filter:
                # Apply segment filtering logic here
                pass

            # Get appropriate channel subscribers
            if campaign.channel == CampaignChannel.EMAIL:
                query = query.where(Subscriber.email_consent)
            elif campaign.channel == CampaignChannel.SMS:
                query = query.where(
                    and_(
                        Subscriber.sms_consent,
                        Subscriber.phone_enc.isnot(None),
                    )
                )
            elif campaign.channel == CampaignChannel.BOTH:
                query = query.where(
                    or_(
                        Subscriber.email_consent,
                        and_(
                            Subscriber.sms_consent,
                            Subscriber.phone_enc.isnot(None),
                        ),
                    )
                )

            subscribers = (await db.execute(query)).scalars().all()

            # Update campaign
            campaign.status = CampaignStatus.SENDING
            campaign.total_recipients = len(subscribers)
            await db.commit()

            # Send to each subscriber
            for subscriber in subscribers:
                try:
                    # Create sent event
                    event = CampaignEvent(
                        campaign_id=campaign.id,
                        subscriber_id=subscriber.id,
                        type=CampaignEventType.SENT,
                    )
                    db.add(event)

                    # Update subscriber stats
                    subscriber.total_emails_sent += 1
                    subscriber.last_email_sent_date = datetime.now()

                    # TODO: Integrate with actual email/SMS sending service
                    # For now, just simulate delivery
                    delivery_event = CampaignEvent(
                        campaign_id=campaign.id,
                        subscriber_id=subscriber.id,
                        type=CampaignEventType.DELIVERED,
                    )
                    db.add(delivery_event)

                except Exception as e:
                    logger.exception(
                        f"Failed to send to subscriber {subscriber.id}: {e}"
                    )

            # Mark campaign as sent
            campaign.status = CampaignStatus.SENT
            campaign.sent_at = datetime.now()
            await db.commit()

        except Exception as e:
            logger.exception(f"Campaign sending failed: {e}")
            # Mark campaign as failed
            campaign.status = CampaignStatus.CANCELLED
            await db.commit()
