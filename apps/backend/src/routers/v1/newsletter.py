"""Newsletter and campaign management API endpoints."""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from core.database import get_db
from models import Campaign, CampaignEvent, Subscriber
from models.enums import CampaignChannel, CampaignEventType, CampaignStatus
from services.ai_lead_management import get_social_media_ai
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/newsletter", tags=["newsletter"])
analytics_router = APIRouter(prefix="/newsletter/analytics", tags=["newsletter-analytics"])


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
    """Subscriber information response model.
    
    IMPORTANT Field Usage Clarification:
    - email: Used for identification, NOT for marketing newsletters
    - sms_consent: Controls SMS newsletters (primary marketing channel via RingCentral)
    - email_consent: Controls admin emails only (invoices, booking confirmations)
    - total_emails_sent: Tracks admin emails, NOT marketing newsletters
    - total_sms_sent: Would track SMS newsletters (primary marketing channel)
    """
    id: UUID
    customer_id: UUID | None
    email: str  # For identification, NOT newsletters
    phone: str | None
    subscribed: bool
    source: str | None
    sms_consent: bool  # SMS newsletters (RingCentral)
    email_consent: bool  # Admin emails only
    tags: list[str] | None
    engagement_score: int
    total_emails_sent: int  # Admin emails only
    total_emails_opened: int  # Admin email tracking
    total_clicks: int
    last_email_sent_date: datetime | None  # Admin emails
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


@router.get("/unsubscribe", response_class=HTMLResponse)
async def public_unsubscribe_email(
    email: str = Query(..., description="Email address to unsubscribe"),
    token: str = Query(..., description="Security token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public email unsubscribe endpoint for CAN-SPAM compliance.
    
    This endpoint allows users to unsubscribe from marketing emails via a link
    without requiring authentication. The token parameter prevents abuse.
    
    CAN-SPAM Requirements Met:
    - One-click unsubscribe (no login required)
    - Immediate processing (unsubscribe within 10 business days)
    - Clear confirmation message
    - Secure token prevents unauthorized unsubscribes
    
    Args:
        email: Email address to unsubscribe (from email link)
        token: HMAC token for verification (prevents abuse)
        db: Database session
    
    Returns:
        HTMLResponse with success/error message
    """
    from core.compliance import get_compliance_validator
    from core.config import get_settings
    from services.newsletter_service import SubscriberService
    from services.event_service import EventService
    
    settings = get_settings()
    compliance = get_compliance_validator()
    
    # Verify token to prevent abuse
    if not compliance.verify_unsubscribe_token(email, token, settings.SECRET_KEY):
        logger.warning(
            f"Invalid unsubscribe token attempt for email: {email}",
            extra={"email": email, "token": token[:8] + "..."},
        )
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Invalid Link - My Hibachi Chef</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                           background: #f5f5f5; padding: 40px 20px; text-align: center; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; 
                                border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 48px; margin-bottom: 20px; }
                    h1 { color: #2c3e50; margin-bottom: 20px; }
                    p { color: #7f8c8d; line-height: 1.6; margin-bottom: 30px; }
                    .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 5px; font-weight: 600; }
                    .button:hover { background: #c0392b; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">⚠️</div>
                    <h1>Invalid Unsubscribe Link</h1>
                    <p>This unsubscribe link is invalid, expired, or has been tampered with.</p>
                    <p>If you'd like to unsubscribe from our emails, please contact us:</p>
                    <p>
                        <strong>Email:</strong> cs@myhibachichef.com<br>
                        <strong>Phone:</strong> (916) 740-8768
                    </p>
                    <a href="https://myhibachichef.com" class="button">Return to Website</a>
                </div>
            </body>
            </html>
            """,
            status_code=400,
        )
    
    # Initialize subscriber service with dependencies
    try:
        event_service = EventService(db)
        subscriber_service = SubscriberService(
            db=db,
            compliance_validator=compliance,
            event_service=event_service,
        )
        
        # Attempt to unsubscribe
        success = await subscriber_service.unsubscribe(email=email)
        
        if success:
            logger.info(
                f"Successfully unsubscribed email via public endpoint: {email}",
                extra={"email": email, "method": "public_unsubscribe_link"},
            )
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Unsubscribed - My Hibachi Chef</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                               background: #f5f5f5; padding: 40px 20px; text-align: center; }
                        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; 
                                    border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .success { color: #27ae60; font-size: 48px; margin-bottom: 20px; }
                        h1 { color: #2c3e50; margin-bottom: 20px; }
                        p { color: #7f8c8d; line-height: 1.6; margin-bottom: 20px; }
                        .info-box { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 30px 0; }
                        .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; 
                                 text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 20px; }
                        .button:hover { background: #c0392b; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success">✅</div>
                        <h1>Unsubscribed Successfully</h1>
                        <p>You've been successfully removed from My Hibachi Chef's email newsletter list.</p>
                        <p>We're sorry to see you go! You will no longer receive marketing emails from us.</p>
                        
                        <div class="info-box">
                            <p style="margin: 0; font-size: 14px;">
                                <strong>Note:</strong> You may still receive transactional emails related to any active bookings 
                                or orders you have with us. These are important for your service and cannot be unsubscribed from.
                            </p>
                        </div>
                        
                        <p style="font-size: 14px; color: #95a5a6;">
                            Changed your mind? You can resubscribe anytime by visiting our website.<br>
                            Questions? Contact us at <a href="mailto:cs@myhibachichef.com" style="color: #e74c3c;">cs@myhibachichef.com</a> 
                            or call <a href="tel:+19167408768" style="color: #e74c3c;">(916) 740-8768</a>
                        </p>
                        
                        <a href="https://myhibachichef.com" class="button">Visit Our Website</a>
                    </div>
                </body>
                </html>
                """
            )
        else:
            # Email not found in system
            logger.warning(
                f"Unsubscribe attempt for non-existent email: {email}",
                extra={"email": email},
            )
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Email Not Found - My Hibachi Chef</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                               background: #f5f5f5; padding: 40px 20px; text-align: center; }
                        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; 
                                    border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .info { color: #3498db; font-size: 48px; margin-bottom: 20px; }
                        h1 { color: #2c3e50; margin-bottom: 20px; }
                        p { color: #7f8c8d; line-height: 1.6; margin-bottom: 20px; }
                        .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; 
                                 text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 20px; }
                        .button:hover { background: #c0392b; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="info">ℹ️</div>
                        <h1>Email Not Found</h1>
                        <p>This email address is not in our newsletter system.</p>
                        <p>You may have already been unsubscribed, or you never subscribed to our newsletter.</p>
                        <p style="font-size: 14px; color: #95a5a6;">
                            If you believe this is an error, please contact us:<br>
                            <a href="mailto:cs@myhibachichef.com" style="color: #e74c3c;">cs@myhibachichef.com</a> | 
                            <a href="tel:+19167408768" style="color: #e74c3c;">(916) 740-8768</a>
                        </p>
                        <a href="https://myhibachichef.com" class="button">Visit Our Website</a>
                    </div>
                </body>
                </html>
                """,
                status_code=404,
            )
    
    except Exception as e:
        logger.exception(
            f"Error processing unsubscribe request: {e}",
            extra={"email": email, "error": str(e)},
        )
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Error - My Hibachi Chef</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                           background: #f5f5f5; padding: 40px 20px; text-align: center; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; 
                                border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 48px; margin-bottom: 20px; }
                    h1 { color: #2c3e50; margin-bottom: 20px; }
                    p { color: #7f8c8d; line-height: 1.6; margin-bottom: 20px; }
                    .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; 
                             text-decoration: none; border-radius: 5px; font-weight: 600; margin-top: 20px; }
                    .button:hover { background: #c0392b; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">❌</div>
                    <h1>Processing Error</h1>
                    <p>We encountered an error processing your unsubscribe request.</p>
                    <p>Please try again later, or contact us directly:</p>
                    <p>
                        <strong>Email:</strong> cs@myhibachichef.com<br>
                        <strong>Phone:</strong> (916) 740-8768
                    </p>
                    <a href="https://myhibachichef.com" class="button">Return to Website</a>
                </div>
            </body>
            </html>
            """,
            status_code=500,
        )


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
                # Email campaigns are ONLY for admin/transactional purposes
                # Not for marketing newsletters
                query = query.where(Subscriber.email_consent)
            elif campaign.channel == CampaignChannel.SMS:
                # SMS is the PRIMARY newsletter channel (via RingCentral)
                query = query.where(
                    and_(
                        Subscriber.sms_consent,
                        Subscriber.phone_enc.isnot(None),
                    )
                )
            elif campaign.channel == CampaignChannel.BOTH:
                # Both channels: SMS for newsletter, email for admin tasks
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

            # Initialize services
            from core.compliance import get_compliance_validator
            from core.config import get_settings
            from services.ringcentral_sms import RingCentralSMSService
            from services.newsletter.sms_service import NewsletterSMSService
            
            settings = get_settings()
            compliance_validator = get_compliance_validator()
            
            # For SMS campaigns (newsletter/marketing)
            if campaign.channel in [CampaignChannel.SMS, CampaignChannel.BOTH]:
                async with RingCentralSMSService() as ringcentral:
                    sms_service = NewsletterSMSService(
                        ringcentral_service=ringcentral,
                        compliance_validator=compliance_validator,
                        business_phone=settings.ringcentral_from_number,
                    )
                    
                    # Send to SMS subscribers
                    sms_content = campaign.content.get("text", campaign.content.get("html", ""))
                    
                    for subscriber in subscribers:
                        if not subscriber.sms_consent or not subscriber.phone_enc:
                            continue
                        
                        try:
                            from utils.encryption import decrypt_phone
                            phone = decrypt_phone(subscriber.phone_enc)
                            
                            # Send SMS with TCPA compliance
                            result = await sms_service.send_campaign_sms(
                                subscriber_phone=phone,
                                subscriber_name=subscriber.email.split('@')[0],  # Use email prefix as name
                                message_content=sms_content,
                                campaign_id=campaign.id,
                                include_stop_instructions=True,
                            )
                            
                            # Create sent event
                            event = CampaignEvent(
                                campaign_id=campaign.id,
                                subscriber_id=subscriber.id,
                                type=CampaignEventType.SENT,
                            )
                            db.add(event)
                            
                            if result.success:
                                # Create delivered event
                                delivery_event = CampaignEvent(
                                    campaign_id=campaign.id,
                                    subscriber_id=subscriber.id,
                                    type=CampaignEventType.DELIVERED,
                                )
                                db.add(delivery_event)
                                
                                # Update subscriber stats
                                subscriber.total_sms_sent = (subscriber.total_sms_sent or 0) + 1
                                subscriber.last_sms_sent_date = datetime.now()
                                
                                logger.info(
                                    f"✅ SMS campaign sent: {phone[-4:]}",
                                    extra={
                                        "campaign_id": str(campaign.id),
                                        "subscriber_id": str(subscriber.id),
                                        "message_id": result.message_id,
                                    },
                                )
                            else:
                                logger.error(
                                    f"❌ SMS campaign failed: {phone[-4:]} - {result.error}",
                                    extra={
                                        "campaign_id": str(campaign.id),
                                        "subscriber_id": str(subscriber.id),
                                        "error": result.error,
                                    },
                                )
                        
                        except Exception as e:
                            logger.exception(
                                f"Failed to send SMS to subscriber {subscriber.id}: {e}"
                            )
                    
                    await db.commit()
            
            # For EMAIL campaigns (admin/transactional only - NOT newsletters)
            if campaign.channel in [CampaignChannel.EMAIL]:
                # Email service integration for admin/transactional emails
                # NOT for marketing newsletters (those go via SMS)
                logger.info(
                    "📧 Email campaigns are for admin/transactional purposes only",
                    extra={"campaign_id": str(campaign.id)},
                )
                # Email implementation would go here for transactional emails
                # (invoices, booking confirmations, etc.)

            # Mark campaign as sent
            campaign.status = CampaignStatus.SENT
            campaign.sent_at = datetime.now()
            await db.commit()

        except Exception as e:
            logger.exception(f"Campaign sending failed: {e}")
            # Mark campaign as failed
            if campaign:
                campaign.status = CampaignStatus.CANCELLED
                await db.commit()


# ============================================================================
# Analytics Endpoints
# ============================================================================


@analytics_router.get("/dashboard")
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive analytics dashboard overview.
    
    Returns metrics for:
    - Overall unsubscribe rates
    - SMS-specific metrics (primary newsletter channel)
    - Email-specific metrics (admin/transactional only)
    - Daily trend data
    - Channel comparison
    - Compliance status
    
    Args:
        days: Number of days to analyze (1-365, default: 30)
        db: Database session
        
    Returns:
        Dictionary with comprehensive dashboard metrics
    """
    from services.newsletter_analytics_service import NewsletterAnalyticsService
    
    service = NewsletterAnalyticsService(db)
    overview = await service.get_dashboard_overview(days=days)
    
    return {
        "success": True,
        "data": overview,
    }


@analytics_router.get("/campaigns/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed analytics for a specific campaign.
    
    Returns metrics for:
    - Total sent/delivered/opened/clicked
    - Delivery, open, click, and unsubscribe rates
    - Campaign details (name, channel, status, sent date)
    
    Args:
        campaign_id: Campaign UUID
        db: Database session
        
    Returns:
        Dictionary with campaign performance metrics
        
    Raises:
        HTTPException: 404 if campaign not found
    """
    from services.newsletter_analytics_service import NewsletterAnalyticsService
    
    service = NewsletterAnalyticsService(db)
    analytics = await service.get_campaign_details(campaign_id)
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    
    return {
        "success": True,
        "data": analytics,
    }


@analytics_router.get("/subscribers/{subscriber_id}")
async def get_subscriber_analytics(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get lifetime analytics for a specific subscriber.
    
    Returns metrics for:
    - Total campaigns received/opened/clicked
    - Engagement rate
    - Subscription status and consent preferences
    - Last interaction date
    
    Args:
        subscriber_id: Subscriber UUID
        db: Database session
        
    Returns:
        Dictionary with subscriber lifetime metrics
        
    Raises:
        HTTPException: 404 if subscriber not found
    """
    from services.newsletter_analytics_service import NewsletterAnalyticsService
    
    service = NewsletterAnalyticsService(db)
    analytics = await service.get_subscriber_analytics(subscriber_id)
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscriber {subscriber_id} not found",
        )
    
    return {
        "success": True,
        "data": analytics,
    }


@analytics_router.get("/trend")
async def get_unsubscribe_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    channel: str | None = Query(None, description="Filter by channel: EMAIL, SMS, or BOTH"),
    db: AsyncSession = Depends(get_db),
):
    """Get daily unsubscribe trend for the past N days.
    
    Returns daily metrics for:
    - Total sent per day
    - Total unsubscribed per day
    - Daily unsubscribe rate
    
    Args:
        days: Number of days to analyze (1-365, default: 30)
        channel: Optional channel filter (EMAIL, SMS, BOTH)
        db: Database session
        
    Returns:
        List of daily unsubscribe metrics
        
    Raises:
        HTTPException: 400 if invalid channel
    """
    from services.newsletter_analytics_service import NewsletterAnalyticsService
    
    # Validate channel parameter
    channel_enum = None
    if channel:
        try:
            channel_enum = CampaignChannel(channel.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid channel: {channel}. Must be EMAIL, SMS, or BOTH",
            )
    
    service = NewsletterAnalyticsService(db)
    trend = await service.get_unsubscribe_trend(
        days=days,
        channel=channel_enum,
    )
    
    return {
        "success": True,
        "data": trend,
    }


@analytics_router.get("/compliance")
async def get_compliance_report(
    start_date: datetime | None = Query(None, description="Start date (ISO format)"),
    end_date: datetime | None = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive compliance report.
    
    Returns compliance metrics for:
    - SMS/TCPA compliance (STOP instructions, unsubscribe rate)
    - Email/CAN-SPAM compliance (List-Unsubscribe headers, unsubscribe rate)
    - Overall health status
    - Actionable recommendations
    
    Args:
        start_date: Start of date range (default: 30 days ago)
        end_date: End of date range (default: now)
        db: Database session
        
    Returns:
        Dictionary with compliance metrics and recommendations
    """
    from services.newsletter_analytics_service import NewsletterAnalyticsService
    
    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    service = NewsletterAnalyticsService(db)
    report = await service.get_compliance_report(
        start_date=start_date,
        end_date=end_date,
    )
    
    return {
        "success": True,
        "data": report,
    }
