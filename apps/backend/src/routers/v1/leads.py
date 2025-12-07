"""Lead management API endpoints."""

from datetime import date, datetime, timezone
import logging
from typing import Any
from uuid import UUID

from core.database import get_db

# FIXED: Import from db.models (NEW system) instead of models (OLD system)
# Enums from crm.py, models from lead.py
from db.models.crm import (
    Lead,
    ContactChannel,
    LeadQuality,
    LeadSource,
    LeadStatus,
    SocialPlatform,
)
from db.models.lead import (
    LeadContact,
    LeadContext,
)
from db.models.core import SocialThread
from services.ai_lead_management import (
    get_ai_lead_manager,
    get_social_media_ai,
)
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["leads"])  # No prefix - added in main.py


# Pydantic models for API
class LeadContactCreate(BaseModel):
    channel: ContactChannel
    handle_or_address: str
    verified: bool = False


class LeadContextCreate(BaseModel):
    party_size_adults: int | None = None
    party_size_kids: int | None = None
    estimated_budget_dollars: float | None = None
    event_date_pref: date | None = None
    event_date_range_start: date | None = None
    event_date_range_end: date | None = None
    zip_code: str | None = None
    service_type: str | None = None
    notes: str | None = None


class LeadCreate(BaseModel):
    source: LeadSource
    contacts: list[LeadContactCreate]
    context: LeadContextCreate | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    quality: LeadQuality | None = None
    assigned_to: str | None = None
    follow_up_date: datetime | None = None
    lost_reason: str | None = None


class LeadResponse(BaseModel):
    id: UUID
    source: LeadSource
    status: LeadStatus
    quality: LeadQuality | None
    score: float
    assigned_to: str | None
    last_contact_date: datetime | None
    follow_up_date: datetime | None
    conversion_date: datetime | None
    lost_reason: str | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadDetailResponse(LeadResponse):
    contacts: list[dict[str, Any]]
    context: dict[str, Any] | None
    events: list[dict[str, Any]]


class SocialThreadCreate(BaseModel):
    platform: SocialPlatform
    account_id: str
    thread_ref: str
    lead_id: UUID | None = None
    customer_id: UUID | None = None


class SocialThreadResponse(BaseModel):
    id: UUID
    platform: SocialPlatform
    account_id: str
    thread_ref: str
    lead_id: UUID | None
    customer_id: UUID | None
    status: str
    last_message_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new lead with contacts and context."""

    try:
        # Create lead
        lead = Lead(
            source=lead_data.source,
            utm_source=lead_data.utm_source,
            utm_medium=lead_data.utm_medium,
            utm_campaign=lead_data.utm_campaign,
        )
        db.add(lead)
        await db.flush()  # Get the lead ID

        # Add contacts
        for contact_data in lead_data.contacts:
            contact = LeadContact(
                lead_id=lead.id,
                channel=contact_data.channel,
                handle_or_address=contact_data.handle_or_address,
                verified=contact_data.verified,
            )
            db.add(contact)

        # Add context if provided
        if lead_data.context:
            context = LeadContext(
                lead_id=lead.id,
                party_size_adults=lead_data.context.party_size_adults,
                party_size_kids=lead_data.context.party_size_kids,
                estimated_budget_cents=(
                    int(lead_data.context.estimated_budget_dollars * 100)
                    if lead_data.context.estimated_budget_dollars
                    else None
                ),
                event_date_pref=lead_data.context.event_date_pref,
                event_date_range_start=lead_data.context.event_date_range_start,
                event_date_range_end=lead_data.context.event_date_range_end,
                zip_code=lead_data.context.zip_code,
                service_type=lead_data.context.service_type,
                notes=lead_data.context.notes,
            )
            db.add(context)

        # Add creation event
        lead.add_event(
            "lead_created",
            {
                "source": lead_data.source.value,
                "utm_data": {
                    "source": lead_data.utm_source,
                    "medium": lead_data.utm_medium,
                    "campaign": lead_data.utm_campaign,
                },
            },
        )

        await db.commit()

        # Background tasks
        background_tasks.add_task(_process_new_lead, lead.id)

        return lead

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {e!s}",
        )


@router.get("/", response_model=list[LeadResponse])
async def list_leads(
    status: LeadStatus | None = Query(None),
    quality: LeadQuality | None = Query(None),
    source: LeadSource | None = Query(None),
    assigned_to: str | None = Query(None),
    score_min: float | None = Query(None),
    score_max: float | None = Query(None),
    follow_up_overdue: bool | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    sort_by: str = Query(
        "score",
        pattern=r"^(score|created_at|follow_up_date|last_contact_date)$",
    ),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List leads with filtering and sorting."""

    # Build SQLAlchemy 2.0 async query
    stmt = select(Lead)

    # Apply filters
    if status:
        stmt = stmt.where(Lead.status == status)
    if quality:
        stmt = stmt.where(Lead.quality == quality)
    if source:
        stmt = stmt.where(Lead.source == source)
    if assigned_to:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
    if score_min is not None:
        stmt = stmt.where(Lead.score >= score_min)
    if score_max is not None:
        stmt = stmt.where(Lead.score <= score_max)
    if follow_up_overdue:
        stmt = stmt.where(
            and_(
                Lead.follow_up_date.isnot(None),
                Lead.follow_up_date < datetime.now(timezone.utc),
            )
        )

    # Apply sorting
    sort_column = getattr(Lead, sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(desc(sort_column))
    else:
        stmt = stmt.order_by(asc(sort_column))

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(stmt)
    leads = result.scalars().all()

    return leads


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed lead information."""

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    # Convert to response model with nested data
    lead_dict = {
        **lead.__dict__,
        "contacts": [contact.__dict__ for contact in lead.contacts],
        "context": lead.context.__dict__ if lead.context else None,
        "events": [event.__dict__ for event in lead.events],
    }

    return lead_dict


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Update lead information."""

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    # Track changes for events
    changes = {}

    if lead_update.status and lead_update.status != lead.status:
        changes["status"] = {
            "from": lead.status.value,
            "to": lead_update.status.value,
        }
        lead.status = lead_update.status

        # Special handling for status changes
        if lead_update.status == LeadStatus.CONVERTED:
            lead.conversion_date = datetime.now(timezone.utc)

    if lead_update.quality and lead_update.quality != lead.quality:
        changes["quality"] = {
            "from": lead.quality.value if lead.quality else None,
            "to": lead_update.quality.value,
        }
        lead.quality = lead_update.quality

    if lead_update.assigned_to and lead_update.assigned_to != lead.assigned_to:
        changes["assigned_to"] = {
            "from": lead.assigned_to,
            "to": lead_update.assigned_to,
        }
        lead.assigned_to = lead_update.assigned_to

    if lead_update.follow_up_date:
        changes["follow_up_date"] = {
            "to": lead_update.follow_up_date.isoformat()
        }
        lead.follow_up_date = lead_update.follow_up_date

    if lead_update.lost_reason:
        lead.lost_reason = lead_update.lost_reason

    # Add update event
    if changes:
        lead.add_event("lead_updated", changes)

    await db.commit()

    # Background processing
    background_tasks.add_task(_recalculate_lead_score, lead_id)

    return lead


@router.post("/{lead_id}/events")
async def add_lead_event(
    lead_id: UUID,
    event_type: str,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Add an event to a lead."""

    if payload is None:
        payload = {}
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    lead.add_event(event_type, payload)
    lead.last_contact_date = datetime.now(timezone.utc)

    await db.commit()

    return {"success": True, "message": "Event added successfully"}


@router.post("/{lead_id}/ai-analysis")
async def analyze_lead_with_ai(
    lead_id: UUID,
    conversation_data: list[dict[str, str]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Analyze lead using AI and update scoring."""

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    # Schedule AI analysis
    background_tasks.add_task(_ai_analyze_lead, lead_id, conversation_data)

    return {"success": True, "message": "AI analysis scheduled"}


@router.get("/{lead_id}/nurture-sequence")
async def get_nurture_sequence(
    lead_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Get AI-generated nurture sequence for lead."""

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    from services.ai_lead_management import get_lead_nurture_ai

    nurture_ai = await get_lead_nurture_ai()
    sequence = await nurture_ai.create_nurture_sequence(lead)

    return {"sequence": sequence}


# Social Media Thread endpoints
@router.post("/social-threads", response_model=SocialThreadResponse)
async def create_social_thread(
    thread_data: SocialThreadCreate, db: AsyncSession = Depends(get_db)
):
    """Create or link a social media thread."""

    # Check if thread already exists
    result = await db.execute(
        select(SocialThread).where(
            and_(
                SocialThread.platform == thread_data.platform,
                SocialThread.thread_ref == thread_data.thread_ref,
            )
        )
    )
    existing_thread = result.scalar_one_or_none()

    if existing_thread:
        return existing_thread

    thread = SocialThread(
        platform=thread_data.platform,
        account_id=thread_data.account_id,
        thread_ref=thread_data.thread_ref,
        lead_id=thread_data.lead_id,
        customer_id=thread_data.customer_id,
    )

    db.add(thread)
    await db.commit()

    return thread


@router.get("/social-threads", response_model=list[SocialThreadResponse])
async def list_social_threads(
    platform: SocialPlatform | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List social media threads."""

    stmt = select(SocialThread)

    if platform:
        stmt = stmt.where(SocialThread.platform == platform)
    if status:
        stmt = stmt.where(SocialThread.status == status)

    stmt = stmt.order_by(desc(SocialThread.last_message_at))
    result = await db.execute(stmt)
    threads = result.scalars().all()
    return threads


@router.post("/social-threads/{thread_id}/respond")
async def respond_to_social_thread(
    thread_id: UUID,
    message_content: str,
    context: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI response for social media thread."""

    if context is None:
        context = {}
    result = await db.execute(
        select(SocialThread).where(SocialThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social thread not found",
        )

    social_ai = await get_social_media_ai()
    response = await social_ai.generate_response(message_content, context)

    return {"suggested_response": response}


# Background task functions
async def _process_new_lead(lead_id: UUID):
    """Process new lead in background."""
    from core.database import get_db_context

    async with get_db_context() as db:
        try:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
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

                await db.commit()

        except Exception as e:
            logger.exception(f"Error processing new lead {lead_id}: {e}")


async def _recalculate_lead_score(lead_id: UUID):
    """Recalculate lead score in background."""
    from core.database import get_db_context

    async with get_db_context() as db:
        try:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if lead:
                score = lead.calculate_score()
                lead.score = score
                await db.commit()

        except Exception as e:
            logger.exception(f"Error recalculating lead score {lead_id}: {e}")


async def _ai_analyze_lead(lead_id: UUID, conversation_data: list[dict]):
    """Analyze lead with AI in background."""
    from core.database import get_db_context

    async with get_db_context() as db:
        try:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if lead:
                ai_manager = await get_ai_lead_manager()

                # Get AI insights
                insights = await ai_manager.analyze_conversation(
                    conversation_data
                )

                # Update lead with AI insights
                ai_score = await ai_manager.score_lead_with_ai(
                    lead, conversation_data
                )
                lead.score = ai_score

                # Update quality based on AI score
                lead.quality = await ai_manager.determine_lead_quality(
                    lead, ai_score
                )

                # Add AI analysis event
                lead.add_event(
                    "ai_analysis",
                    {
                        "insights": {
                            "intent_score": insights.intent_score,
                            "urgency_level": insights.urgency_level,
                            "sentiment": insights.sentiment,
                            "next_action": insights.next_best_action,
                        },
                        "ai_score": ai_score,
                    },
                )

                await db.commit()

        except Exception as e:
            logger.exception(f"Error analyzing lead {lead_id} with AI: {e}")
