"""Newsletter and campaign management API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from pydantic import BaseModel, Field, EmailStr

from ..database import get_db
from ..models.lead_newsletter import (
    Subscriber, Campaign, CampaignEvent,
    CampaignChannel, CampaignStatus, CampaignEventType
)
from ..services.ai_lead_management import get_social_media_ai

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/newsletter", tags=["newsletter"])


# Pydantic models
class SubscriberCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    source: Optional[str] = None
    sms_consent: bool = False
    email_consent: bool = True
    tags: Optional[List[str]] = None


class SubscriberUpdate(BaseModel):
    phone: Optional[str] = None
    sms_consent: Optional[bool] = None
    email_consent: Optional[bool] = None
    tags: Optional[List[str]] = None
    subscribed: Optional[bool] = None


class SubscriberResponse(BaseModel):
    id: UUID
    customer_id: Optional[UUID]
    email: str
    phone: Optional[str]
    subscribed: bool
    source: Optional[str]
    sms_consent: bool
    email_consent: bool
    tags: Optional[List[str]]
    engagement_score: int
    total_emails_sent: int
    total_emails_opened: int
    total_clicks: int
    last_email_sent_date: Optional[datetime]
    last_opened_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    channel: CampaignChannel
    subject: Optional[str] = None
    content: Dict[str, Any]
    segment_filter: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    segment_filter: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    channel: CampaignChannel
    subject: Optional[str]
    content: Dict[str, Any]
    segment_filter: Optional[Dict[str, Any]]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
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
    payload: Optional[Dict[str, Any]]
    occurred_at: datetime

    class Config:
        from_attributes = True


# Subscriber endpoints
@router.post("/subscribers", response_model=SubscriberResponse)
async def create_subscriber(
    subscriber_data: SubscriberCreate,
    db: Session = Depends(get_db)
):
    """Create a new newsletter subscriber."""
    
    # Check if subscriber already exists
    existing = db.query(Subscriber).filter(
        Subscriber.email_enc == Subscriber._encrypt_email(subscriber_data.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscriber already exists"
        )
    
    subscriber = Subscriber(
        email=subscriber_data.email,
        phone=subscriber_data.phone,
        source=subscriber_data.source,
        sms_consent=subscriber_data.sms_consent,
        email_consent=subscriber_data.email_consent,
        tags=subscriber_data.tags or [],
        consent_updated_at=datetime.now()
    )
    
    db.add(subscriber)
    db.commit()
    
    return subscriber


@router.get("/subscribers", response_model=List[SubscriberResponse])
async def list_subscribers(
    subscribed: Optional[bool] = Query(None),
    tags: Optional[List[str]] = Query(None),
    engagement_min: Optional[int] = Query(None),
    engagement_max: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """List newsletter subscribers with filtering."""
    
    query = db.query(Subscriber)
    
    if subscribed is not None:
        query = query.filter(Subscriber.subscribed == subscribed)
    
    if tags:
        query = query.filter(Subscriber.tags.overlap(tags))
    
    if engagement_min is not None:
        query = query.filter(Subscriber.engagement_score >= engagement_min)
    
    if engagement_max is not None:
        query = query.filter(Subscriber.engagement_score <= engagement_max)
    
    subscribers = query.order_by(desc(Subscriber.engagement_score)).offset(offset).limit(limit).all()
    
    return subscribers


@router.get("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(subscriber_id: UUID, db: Session = Depends(get_db)):
    """Get subscriber details."""
    
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )
    
    return subscriber


@router.put("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: UUID,
    subscriber_update: SubscriberUpdate,
    db: Session = Depends(get_db)
):
    """Update subscriber information."""
    
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
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
    
    db.commit()
    
    return subscriber


@router.delete("/subscribers/{subscriber_id}")
async def unsubscribe_subscriber(subscriber_id: UUID, db: Session = Depends(get_db)):
    """Unsubscribe a subscriber."""
    
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )
    
    subscriber.subscribed = False
    subscriber.unsubscribed_at = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "Subscriber unsubscribed successfully"}


# Campaign endpoints
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Create a new marketing campaign."""
    
    campaign = Campaign(
        name=campaign_data.name,
        channel=campaign_data.channel,
        subject=campaign_data.subject,
        content=campaign_data.content,
        segment_filter=campaign_data.segment_filter,
        scheduled_at=campaign_data.scheduled_at,
        created_by=current_user
    )
    
    db.add(campaign)
    db.commit()
    
    return campaign


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = Query(None),
    channel: Optional[CampaignChannel] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """List marketing campaigns."""
    
    query = db.query(Campaign)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    if channel:
        query = query.filter(Campaign.channel == channel)
    
    campaigns = query.order_by(desc(Campaign.created_at)).offset(offset).limit(limit).all()
    
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    """Get campaign details."""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_update: CampaignUpdate,
    db: Session = Depends(get_db)
):
    """Update campaign information."""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status in [CampaignStatus.SENT, CampaignStatus.SENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update sent or sending campaign"
        )
    
    for field, value in campaign_update.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    db.commit()
    
    return campaign


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send campaign to subscribers."""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign must be in draft status to send"
        )
    
    # Update campaign status
    campaign.status = CampaignStatus.SCHEDULED
    if not campaign.scheduled_at:
        campaign.scheduled_at = datetime.now()
    
    db.commit()
    
    # Schedule campaign sending
    background_tasks.add_task(_send_campaign_async, campaign_id)
    
    return {"success": True, "message": "Campaign scheduled for sending"}


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(campaign_id: UUID, db: Session = Depends(get_db)):
    """Get campaign performance statistics."""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Count events by type
    event_counts = db.query(
        CampaignEvent.type,
        func.count(CampaignEvent.id).label('count')
    ).filter(
        CampaignEvent.campaign_id == campaign_id
    ).group_by(CampaignEvent.type).all()
    
    counts = {event_type.value: 0 for event_type in CampaignEventType}
    for event_type, count in event_counts:
        counts[event_type.value] = count
    
    total_recipients = campaign.total_recipients or 1  # Avoid division by zero
    
    return CampaignStatsResponse(
        campaign_id=campaign_id,
        total_recipients=total_recipients,
        delivered=counts['delivered'],
        opened=counts['opened'],
        clicked=counts['clicked'],
        bounced=counts['bounced'],
        unsubscribed=counts['unsubscribed'],
        delivery_rate=counts['delivered'] / total_recipients,
        open_rate=counts['opened'] / total_recipients,
        click_rate=counts['clicked'] / total_recipients,
        bounce_rate=counts['bounced'] / total_recipients
    )


@router.get("/campaigns/{campaign_id}/events", response_model=List[CampaignEventResponse])
async def get_campaign_events(
    campaign_id: UUID,
    event_type: Optional[CampaignEventType] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get campaign events."""
    
    query = db.query(CampaignEvent).filter(CampaignEvent.campaign_id == campaign_id)
    
    if event_type:
        query = query.filter(CampaignEvent.type == event_type)
    
    events = query.order_by(desc(CampaignEvent.occurred_at)).offset(offset).limit(limit).all()
    
    return events


@router.post("/campaigns/ai-content")
async def generate_campaign_content(
    campaign_type: str,
    target_audience: str,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Generate AI-powered campaign content."""
    
    social_ai = await get_social_media_ai()
    content = await social_ai.create_promotional_content(campaign_type, target_audience)
    
    return {
        "generated_content": content,
        "campaign_type": campaign_type,
        "target_audience": target_audience
    }


# Segmentation endpoints
@router.get("/segments/preview")
async def preview_segment(
    filter_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Preview subscribers matching segment criteria."""
    
    query = db.query(Subscriber).filter(Subscriber.subscribed == True)
    
    # Apply segment filters
    if 'tags' in filter_criteria:
        query = query.filter(Subscriber.tags.overlap(filter_criteria['tags']))
    
    if 'engagement_min' in filter_criteria:
        query = query.filter(Subscriber.engagement_score >= filter_criteria['engagement_min'])
    
    if 'engagement_max' in filter_criteria:
        query = query.filter(Subscriber.engagement_score <= filter_criteria['engagement_max'])
    
    if 'last_opened_days' in filter_criteria:
        cutoff_date = datetime.now() - timedelta(days=filter_criteria['last_opened_days'])
        query = query.filter(Subscriber.last_opened_date >= cutoff_date)
    
    count = query.count()
    sample = query.limit(10).all()
    
    return {
        "total_count": count,
        "sample_subscribers": sample
    }


# Background task functions
async def _send_campaign_async(campaign_id: UUID):
    """Send campaign in background."""
    db = next(get_db())
    
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        
        # Get target subscribers
        query = db.query(Subscriber).filter(Subscriber.subscribed == True)
        
        # Apply segment filters if any
        if campaign.segment_filter:
            # Apply segment filtering logic here
            pass
        
        # Get appropriate channel subscribers
        if campaign.channel == CampaignChannel.EMAIL:
            query = query.filter(Subscriber.email_consent == True)
        elif campaign.channel == CampaignChannel.SMS:
            query = query.filter(
                and_(
                    Subscriber.sms_consent == True,
                    Subscriber.phone_enc.isnot(None)
                )
            )
        elif campaign.channel == CampaignChannel.BOTH:
            query = query.filter(
                or_(
                    Subscriber.email_consent == True,
                    and_(
                        Subscriber.sms_consent == True,
                        Subscriber.phone_enc.isnot(None)
                    )
                )
            )
        
        subscribers = query.all()
        
        # Update campaign
        campaign.status = CampaignStatus.SENDING
        campaign.total_recipients = len(subscribers)
        db.commit()
        
        # Send to each subscriber
        for subscriber in subscribers:
            try:
                # Create sent event
                event = CampaignEvent(
                    campaign_id=campaign.id,
                    subscriber_id=subscriber.id,
                    type=CampaignEventType.SENT
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
                    type=CampaignEventType.DELIVERED
                )
                db.add(delivery_event)
                
            except Exception as e:
                logger.error(f"Failed to send to subscriber {subscriber.id}: {e}")
        
        # Mark campaign as sent
        campaign.status = CampaignStatus.SENT
        campaign.sent_at = datetime.now()
        db.commit()
        
    except Exception as e:
        logger.error(f"Campaign sending failed: {e}")
        # Mark campaign as failed
        campaign.status = CampaignStatus.CANCELLED
        db.commit()
    finally:
        db.close()