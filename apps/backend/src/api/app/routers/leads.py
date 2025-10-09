"""Lead management API endpoints."""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.lead_newsletter import (
    Lead, LeadContact, LeadContext, LeadEvent, SocialThread,
    LeadSource, LeadStatus, LeadQuality, ContactChannel, SocialPlatform
)
from ..services.ai_lead_management import get_ai_lead_manager, get_social_media_ai
from ..services.ringcentral_sms import send_sms_notification


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


# Pydantic models for API
class LeadContactCreate(BaseModel):
    channel: ContactChannel
    handle_or_address: str
    verified: bool = False


class LeadContextCreate(BaseModel):
    party_size_adults: Optional[int] = None
    party_size_kids: Optional[int] = None
    estimated_budget_dollars: Optional[float] = None
    event_date_pref: Optional[date] = None
    event_date_range_start: Optional[date] = None
    event_date_range_end: Optional[date] = None
    zip_code: Optional[str] = None
    service_type: Optional[str] = None
    notes: Optional[str] = None


class LeadCreate(BaseModel):
    source: LeadSource
    contacts: List[LeadContactCreate]
    context: Optional[LeadContextCreate] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    quality: Optional[LeadQuality] = None
    assigned_to: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    lost_reason: Optional[str] = None


class LeadResponse(BaseModel):
    id: UUID
    source: LeadSource
    status: LeadStatus
    quality: Optional[LeadQuality]
    score: float
    assigned_to: Optional[str]
    last_contact_date: Optional[datetime]
    follow_up_date: Optional[datetime]
    conversion_date: Optional[datetime]
    lost_reason: Optional[str]
    utm_source: Optional[str]
    utm_medium: Optional[str]
    utm_campaign: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadDetailResponse(LeadResponse):
    contacts: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    events: List[Dict[str, Any]]


class SocialThreadCreate(BaseModel):
    platform: SocialPlatform
    account_id: str
    thread_ref: str
    lead_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None


class SocialThreadResponse(BaseModel):
    id: UUID
    platform: SocialPlatform
    account_id: str
    thread_ref: str
    lead_id: Optional[UUID]
    customer_id: Optional[UUID]
    status: str
    last_message_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new lead with contacts and context."""
    
    try:
        # Create lead
        lead = Lead(
            source=lead_data.source,
            utm_source=lead_data.utm_source,
            utm_medium=lead_data.utm_medium,
            utm_campaign=lead_data.utm_campaign
        )
        db.add(lead)
        db.flush()  # Get the lead ID

        # Add contacts
        for contact_data in lead_data.contacts:
            contact = LeadContact(
                lead_id=lead.id,
                channel=contact_data.channel,
                handle_or_address=contact_data.handle_or_address,
                verified=contact_data.verified
            )
            db.add(contact)

        # Add context if provided
        if lead_data.context:
            context = LeadContext(
                lead_id=lead.id,
                party_size_adults=lead_data.context.party_size_adults,
                party_size_kids=lead_data.context.party_size_kids,
                estimated_budget_cents=int(lead_data.context.estimated_budget_dollars * 100) if lead_data.context.estimated_budget_dollars else None,
                event_date_pref=lead_data.context.event_date_pref,
                event_date_range_start=lead_data.context.event_date_range_start,
                event_date_range_end=lead_data.context.event_date_range_end,
                zip_code=lead_data.context.zip_code,
                service_type=lead_data.context.service_type,
                notes=lead_data.context.notes
            )
            db.add(context)

        # Add creation event
        lead.add_event("lead_created", {
            "source": lead_data.source.value,
            "utm_data": {
                "source": lead_data.utm_source,
                "medium": lead_data.utm_medium,
                "campaign": lead_data.utm_campaign
            }
        })

        db.commit()

        # Background tasks
        background_tasks.add_task(_process_new_lead, lead.id)

        return lead

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = Query(None),
    quality: Optional[LeadQuality] = Query(None),
    source: Optional[LeadSource] = Query(None),
    assigned_to: Optional[str] = Query(None),
    score_min: Optional[float] = Query(None),
    score_max: Optional[float] = Query(None),
    follow_up_overdue: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    sort_by: str = Query("score", regex="^(score|created_at|follow_up_date|last_contact_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """List leads with filtering and sorting."""
    
    query = db.query(Lead)
    
    # Apply filters
    if status:
        query = query.filter(Lead.status == status)
    if quality:
        query = query.filter(Lead.quality == quality)
    if source:
        query = query.filter(Lead.source == source)
    if assigned_to:
        query = query.filter(Lead.assigned_to == assigned_to)
    if score_min is not None:
        query = query.filter(Lead.score >= score_min)
    if score_max is not None:
        query = query.filter(Lead.score <= score_max)
    if follow_up_overdue:
        query = query.filter(
            and_(
                Lead.follow_up_date.isnot(None),
                Lead.follow_up_date < datetime.now()
            )
        )
    
    # Apply sorting
    sort_column = getattr(Lead, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Apply pagination
    leads = query.offset(offset).limit(limit).all()
    
    return leads


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    """Get detailed lead information."""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Convert to response model with nested data
    lead_dict = {
        **lead.__dict__,
        "contacts": [contact.__dict__ for contact in lead.contacts],
        "context": lead.context.__dict__ if lead.context else None,
        "events": [event.__dict__ for event in lead.events]
    }
    
    return lead_dict


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update lead information."""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Track changes for events
    changes = {}
    
    if lead_update.status and lead_update.status != lead.status:
        changes["status"] = {"from": lead.status.value, "to": lead_update.status.value}
        lead.status = lead_update.status
        
        # Special handling for status changes
        if lead_update.status == LeadStatus.CONVERTED:
            lead.conversion_date = datetime.now()
    
    if lead_update.quality and lead_update.quality != lead.quality:
        changes["quality"] = {"from": lead.quality.value if lead.quality else None, "to": lead_update.quality.value}
        lead.quality = lead_update.quality
    
    if lead_update.assigned_to and lead_update.assigned_to != lead.assigned_to:
        changes["assigned_to"] = {"from": lead.assigned_to, "to": lead_update.assigned_to}
        lead.assigned_to = lead_update.assigned_to
    
    if lead_update.follow_up_date:
        changes["follow_up_date"] = {"to": lead_update.follow_up_date.isoformat()}
        lead.follow_up_date = lead_update.follow_up_date
    
    if lead_update.lost_reason:
        lead.lost_reason = lead_update.lost_reason
    
    # Add update event
    if changes:
        lead.add_event("lead_updated", changes)
    
    db.commit()
    
    # Background processing
    background_tasks.add_task(_recalculate_lead_score, lead_id)
    
    return lead


@router.post("/{lead_id}/events")
async def add_lead_event(
    lead_id: UUID,
    event_type: str,
    payload: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """Add an event to a lead."""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    lead.add_event(event_type, payload)
    lead.last_contact_date = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "Event added successfully"}


@router.post("/{lead_id}/ai-analysis")
async def analyze_lead_with_ai(
    lead_id: UUID,
    conversation_data: List[Dict[str, str]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze lead using AI and update scoring."""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Schedule AI analysis
    background_tasks.add_task(_ai_analyze_lead, lead_id, conversation_data)
    
    return {"success": True, "message": "AI analysis scheduled"}


@router.get("/{lead_id}/nurture-sequence")
async def get_nurture_sequence(lead_id: UUID, db: Session = Depends(get_db)):
    """Get AI-generated nurture sequence for lead."""
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    from ..services.ai_lead_management import get_lead_nurture_ai
    
    nurture_ai = await get_lead_nurture_ai()
    sequence = await nurture_ai.create_nurture_sequence(lead)
    
    return {"sequence": sequence}


# Social Media Thread endpoints
@router.post("/social-threads", response_model=SocialThreadResponse)
async def create_social_thread(
    thread_data: SocialThreadCreate,
    db: Session = Depends(get_db)
):
    """Create or link a social media thread."""
    
    # Check if thread already exists
    existing_thread = db.query(SocialThread).filter(
        and_(
            SocialThread.platform == thread_data.platform,
            SocialThread.thread_ref == thread_data.thread_ref
        )
    ).first()
    
    if existing_thread:
        return existing_thread
    
    thread = SocialThread(
        platform=thread_data.platform,
        account_id=thread_data.account_id,
        thread_ref=thread_data.thread_ref,
        lead_id=thread_data.lead_id,
        customer_id=thread_data.customer_id
    )
    
    db.add(thread)
    db.commit()
    
    return thread


@router.get("/social-threads", response_model=List[SocialThreadResponse])
async def list_social_threads(
    platform: Optional[SocialPlatform] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List social media threads."""
    
    query = db.query(SocialThread)
    
    if platform:
        query = query.filter(SocialThread.platform == platform)
    if status:
        query = query.filter(SocialThread.status == status)
    
    threads = query.order_by(desc(SocialThread.last_message_at)).all()
    return threads


@router.post("/social-threads/{thread_id}/respond")
async def respond_to_social_thread(
    thread_id: UUID,
    message_content: str,
    context: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """Generate AI response for social media thread."""
    
    thread = db.query(SocialThread).filter(SocialThread.id == thread_id).first()
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social thread not found"
        )
    
    social_ai = await get_social_media_ai()
    response = await social_ai.generate_response(message_content, context)
    
    return {"suggested_response": response}


# Background task functions
async def _process_new_lead(lead_id: UUID):
    """Process new lead in background."""
    db = next(get_db())
    
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            # Calculate initial score
            score = lead.calculate_score()
            lead.score = score
            
            # Determine quality
            if score >= 80:
                lead.quality = LeadQuality.HOT
            elif score >= 60:
                lead.quality = LeadQuality.WARM
            else:
                lead.quality = LeadQuality.COLD
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error processing new lead {lead_id}: {e}")
    finally:
        db.close()


async def _recalculate_lead_score(lead_id: UUID):
    """Recalculate lead score in background."""
    db = next(get_db())
    
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            score = lead.calculate_score()
            lead.score = score
            db.commit()
            
    except Exception as e:
        logger.error(f"Error recalculating lead score {lead_id}: {e}")
    finally:
        db.close()


async def _ai_analyze_lead(lead_id: UUID, conversation_data: List[Dict]):
    """Analyze lead with AI in background."""
    db = next(get_db())
    
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            ai_manager = await get_ai_lead_manager()
            
            # Get AI insights
            insights = await ai_manager.analyze_conversation(conversation_data)
            
            # Update lead with AI insights
            ai_score = await ai_manager.score_lead_with_ai(lead, conversation_data)
            lead.score = ai_score
            
            # Update quality based on AI score
            lead.quality = await ai_manager.determine_lead_quality(lead, ai_score)
            
            # Add AI analysis event
            lead.add_event("ai_analysis", {
                "insights": {
                    "intent_score": insights.intent_score,
                    "urgency_level": insights.urgency_level,
                    "sentiment": insights.sentiment,
                    "next_action": insights.next_best_action
                },
                "ai_score": ai_score
            })
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error analyzing lead {lead_id} with AI: {e}")
    finally:
        db.close()