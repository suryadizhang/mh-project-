"""
Lead Service Layer
Handles lead generation, tracking, and scoring
"""

from datetime import date, datetime
import logging
from typing import Any
from uuid import UUID, uuid4

from api.app.models.lead_newsletter import (
    ContactChannel,
    Lead,
    LeadContact,
    LeadContext,
    LeadEvent,
    LeadQuality,
    LeadSource,
    LeadStatus,
)
from core.cache import CacheService
from core.exceptions import (
    BusinessLogicException,
    ErrorCode,
    NotFoundException,
)
from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class LeadService:
    """
    Service layer for lead management

    Handles:
    - Lead creation from multiple sources
    - Lead scoring and qualification
    - Contact management
    - Event tracking
    """

    def __init__(self, db: AsyncSession, cache: CacheService | None = None):
        """
        Initialize lead service

        Args:
            db: Database session
            cache: Optional cache service
        """
        self.db = db
        self.cache = cache

    async def create_lead(
        self,
        source: LeadSource,
        contact_info: dict[str, Any],
        context: dict[str, Any] | None = None,
        utm_params: dict[str, str] | None = None,
    ) -> Lead:
        """
        Create a new lead with contacts and context

        Args:
            source: Lead acquisition source
            contact_info: Dict with email, phone, instagram_handle, etc.
            context: Optional event context (party size, budget, dates, notes)
            utm_params: Optional UTM tracking parameters

        Returns:
            Created Lead object
        """
        try:
            # Create lead
            lead = Lead(
                id=uuid4(),
                source=source,
                status=LeadStatus.NEW,
                utm_source=utm_params.get("utm_source") if utm_params else None,
                utm_medium=utm_params.get("utm_medium") if utm_params else None,
                utm_campaign=utm_params.get("utm_campaign") if utm_params else None,
            )
            self.db.add(lead)

            # Add contacts
            if contact_info.get("email"):
                contact = LeadContact(
                    id=uuid4(),
                    lead_id=lead.id,
                    channel=ContactChannel.EMAIL,
                    handle_or_address=contact_info["email"],
                    verified=False,
                )
                self.db.add(contact)

            if contact_info.get("phone"):
                contact = LeadContact(
                    id=uuid4(),
                    lead_id=lead.id,
                    channel=ContactChannel.SMS,
                    handle_or_address=contact_info["phone"],
                    verified=False,
                )
                self.db.add(contact)

            if contact_info.get("instagram_handle"):
                contact = LeadContact(
                    id=uuid4(),
                    lead_id=lead.id,
                    channel=ContactChannel.INSTAGRAM,
                    handle_or_address=contact_info["instagram_handle"],
                    verified=False,
                )
                self.db.add(contact)

            if contact_info.get("facebook_handle"):
                contact = LeadContact(
                    id=uuid4(),
                    lead_id=lead.id,
                    channel=ContactChannel.FACEBOOK,
                    handle_or_address=contact_info["facebook_handle"],
                    verified=False,
                )
                self.db.add(contact)

            # Add context if provided
            if context:
                lead_context = LeadContext(
                    lead_id=lead.id,
                    party_size_adults=context.get("party_size_adults"),
                    party_size_kids=context.get("party_size_kids"),
                    estimated_budget_cents=context.get("estimated_budget_cents"),
                    event_date_pref=context.get("event_date"),
                    event_date_range_start=context.get("date_range_start"),
                    event_date_range_end=context.get("date_range_end"),
                    zip_code=context.get("zip_code"),
                    service_type=context.get("service_type"),
                    notes=context.get("notes"),
                )
                self.db.add(lead_context)

            # Calculate initial score
            await self.db.flush()  # Ensure relationships are loaded
            await self.db.refresh(lead, ["contacts", "context", "events"])  # Load all relationships
            score = lead.calculate_score()
            lead.score = score

            # Determine quality based on score
            if score >= 70:
                lead.quality = LeadQuality.HOT
            elif score >= 40:
                lead.quality = LeadQuality.WARM
            else:
                lead.quality = LeadQuality.COLD

            # Add creation event
            event = LeadEvent(
                id=uuid4(),
                lead_id=lead.id,
                type="created",
                payload={"source": source.value, "initial_score": float(score)},
            )
            self.db.add(event)

            await self.db.commit()
            await self.db.refresh(lead)

            logger.info(f"Created lead {lead.id} from source {source.value} with score {score}")

            # Invalidate cache
            if self.cache:
                await self.cache.delete_pattern("leads:*")

            return lead

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error creating lead: {e}")
            raise BusinessLogicException(
                message="Failed to create lead", error_code=ErrorCode.BUSINESS_RULE_VIOLATION
            )

    async def capture_failed_booking(
        self, contact_info: dict[str, Any], booking_data: dict[str, Any], failure_reason: str
    ) -> Lead:
        """
        Create lead from failed booking attempt

        Args:
            contact_info: Customer contact information
            booking_data: Original booking request data
            failure_reason: Why the booking failed

        Returns:
            Created Lead object
        """
        context = {
            "party_size_adults": booking_data.get("party_size", booking_data.get("guest_count")),
            "event_date": booking_data.get("event_date", booking_data.get("booking_datetime")),
            "notes": f"Failed booking: {failure_reason}\nOriginal request: {booking_data.get('special_requests', '')}",
        }

        lead = await self.create_lead(
            source=LeadSource.WEB_QUOTE, contact_info=contact_info, context=context
        )

        # Add failure event
        event = LeadEvent(
            id=uuid4(),
            lead_id=lead.id,
            type="booking_failed",
            payload={
                "reason": failure_reason,
                "requested_date": str(booking_data.get("event_date")),
                "party_size": booking_data.get("party_size"),
            },
        )
        self.db.add(event)
        await self.db.commit()

        logger.info(f"Captured failed booking as lead {lead.id}: {failure_reason}")

        return lead

    async def capture_quote_request(
        self,
        name: str,
        phone: str,  # Required for lead generation
        email: str | None = None,
        event_date: date | None = None,
        guest_count: int | None = None,
        budget: str | None = None,
        message: str | None = None,
        location: str | None = None,
    ) -> Lead:
        """
        Create lead from quote request form

        Args:
            name: Customer name (required)
            phone: Phone number (required - primary contact method)
            email: Email address (optional but recommended)
            event_date: Preferred event date
            guest_count: Number of guests
            budget: Budget range string (e.g., "$500-1000")
            message: Customer message
            location: Event location

        Returns:
            Created Lead object
        """
        # Validate required fields
        if not phone:
            raise BusinessLogicException(
                message="Phone number is required for lead generation",
                error_code=ErrorCode.VALIDATION_ERROR,
            )
        # Parse budget to cents
        budget_cents = None
        if budget:
            try:
                # Extract numbers from budget string
                import re

                numbers = re.findall(r"\d+", budget.replace(",", ""))
                if numbers:
                    # Use average of range or single value
                    if len(numbers) >= 2:
                        budget_cents = int((int(numbers[0]) + int(numbers[1])) / 2 * 100)
                    else:
                        budget_cents = int(numbers[0]) * 100
            except:
                pass

        # Phone is required, email is optional
        contact_info = {"phone": phone}  # Always present (required)
        if email:
            contact_info["email"] = email

        context = {
            "party_size_adults": guest_count,
            "event_date": event_date,
            "estimated_budget_cents": budget_cents,
            "zip_code": location,
            "notes": f"Quote request from {name}\n{message or ''}",
        }

        lead = await self.create_lead(
            source=LeadSource.WEB_QUOTE, contact_info=contact_info, context=context
        )

        logger.info(f"Captured quote request as lead {lead.id} from {name}")

        return lead

    async def capture_social_inquiry(
        self, platform: str, handle: str, message: str, thread_id: str | None = None
    ) -> Lead:
        """
        Create lead from social media inquiry

        Args:
            platform: Social platform (instagram, facebook)
            handle: User's social handle
            message: Their message
            thread_id: External thread ID for tracking

        Returns:
            Created Lead object
        """
        source_map = {
            "instagram": LeadSource.INSTAGRAM,
            "facebook": LeadSource.FACEBOOK,
            "google": LeadSource.GOOGLE,
            "yelp": LeadSource.YELP,
        }

        contact_key = f"{platform}_handle"
        contact_info = {contact_key: handle}

        context = {"notes": f"Social inquiry from {platform}\n{message}", "service_type": platform}

        lead = await self.create_lead(
            source=source_map.get(platform, LeadSource.CHAT),
            contact_info=contact_info,
            context=context,
        )

        # Add thread_id to event payload if provided
        if thread_id:
            event = LeadEvent(
                id=uuid4(),
                lead_id=lead.id,
                type="social_inquiry",
                payload={"platform": platform, "thread_id": thread_id, "handle": handle},
            )
            self.db.add(event)
            await self.db.commit()

        logger.info(f"Captured social inquiry from {platform} as lead {lead.id}")

        return lead

    async def capture_phone_inquiry(
        self,
        phone: str,
        call_type: str,  # 'inbound', 'outbound', 'sms'
        message: str | None = None,
        duration_seconds: int | None = None,
    ) -> Lead:
        """
        Create lead from phone/SMS inquiry

        Args:
            phone: Phone number
            call_type: Type of communication
            message: Message content (for SMS)
            duration_seconds: Call duration

        Returns:
            Created Lead object
        """
        contact_info = {"phone": phone}

        context = {
            "notes": f"Phone inquiry ({call_type})\n{message or f'Call duration: {duration_seconds}s'}"
        }

        source = LeadSource.SMS if call_type == "sms" else LeadSource.PHONE

        lead = await self.create_lead(source=source, contact_info=contact_info, context=context)

        # Add communication event
        event = LeadEvent(
            id=uuid4(),
            lead_id=lead.id,
            type=f"phone_{call_type}",
            payload={
                "call_type": call_type,
                "duration_seconds": duration_seconds,
                "message": message,
            },
        )
        self.db.add(event)
        await self.db.commit()

        logger.info(f"Captured phone inquiry ({call_type}) as lead {lead.id}")

        return lead

    async def get_lead(self, lead_id: UUID) -> Lead:
        """Get lead by ID with all relationships"""
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()

        if not lead:
            raise NotFoundException(f"Lead {lead_id} not found")

        return lead

    async def update_lead_status(
        self, lead_id: UUID, status: LeadStatus, notes: str | None = None
    ) -> Lead:
        """Update lead status and log event"""
        lead = await self.get_lead(lead_id)

        old_status = lead.status
        lead.status = status
        lead.updated_at = datetime.utcnow()

        if status == LeadStatus.CONVERTED:
            lead.conversion_date = datetime.utcnow()

        # Log status change event
        event = LeadEvent(
            id=uuid4(),
            lead_id=lead.id,
            type="status_changed",
            payload={"old_status": old_status.value, "new_status": status.value, "notes": notes},
        )
        self.db.add(event)

        await self.db.commit()
        await self.db.refresh(lead)

        logger.info(f"Updated lead {lead_id} status: {old_status.value} → {status.value}")

        # Invalidate cache
        if self.cache:
            await self.cache.delete_pattern("leads:*")

        return lead

    async def update_lead_score(self, lead_id: UUID) -> Lead:
        """Recalculate and update lead score"""
        lead = await self.get_lead(lead_id)

        # Recalculate score
        new_score = lead.calculate_score()
        old_score = lead.score

        lead.score = new_score
        lead.updated_at = datetime.utcnow()

        # Update quality based on new score
        if new_score >= 70:
            lead.quality = LeadQuality.HOT
        elif new_score >= 40:
            lead.quality = LeadQuality.WARM
        else:
            lead.quality = LeadQuality.COLD

        # Log score change
        event = LeadEvent(
            id=uuid4(),
            lead_id=lead.id,
            type="score_updated",
            payload={
                "old_score": float(old_score) if old_score else 0,
                "new_score": float(new_score),
            },
        )
        self.db.add(event)

        await self.db.commit()
        await self.db.refresh(lead)

        logger.info(f"Updated lead {lead_id} score: {old_score} → {new_score}")

        return lead

    async def list_leads(
        self,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        quality: LeadQuality | None = None,
        assigned_to: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Lead], int]:
        """
        List leads with filters and pagination

        Returns:
            Tuple of (leads list, total count)
        """
        # Build query
        query = select(Lead)
        count_query = select(func.count(Lead.id))

        filters = []

        if status:
            filters.append(Lead.status == status)
        if source:
            filters.append(Lead.source == source)
        if quality:
            filters.append(Lead.quality == quality)
        if assigned_to:
            filters.append(Lead.assigned_to == assigned_to)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Search by contact information (join with contacts table)
        if search:
            search_filter = or_(
                Lead.id.cast(String).ilike(f"%{search}%"), Lead.assigned_to.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        leads = result.scalars().all()

        return list(leads), total

    async def get_pipeline_stats(self) -> dict[str, Any]:
        """Get lead pipeline statistics"""
        # Count by status
        status_query = select(Lead.status, func.count(Lead.id).label("count")).group_by(Lead.status)

        result = await self.db.execute(status_query)
        status_counts = {row.status.value: row.count for row in result}

        # Calculate conversion rate
        total_query = select(func.count(Lead.id))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        converted = status_counts.get("converted", 0)
        conversion_rate = (converted / total * 100) if total > 0 else 0

        # Get total estimated value (sum of budgets)
        value_query = select(func.sum(LeadContext.estimated_budget_cents))
        value_result = await self.db.execute(value_query)
        total_value_cents = value_result.scalar() or 0

        return {
            "new": status_counts.get("new", 0),
            "working": status_counts.get("working", 0),
            "qualified": status_counts.get("qualified", 0),
            "disqualified": status_counts.get("disqualified", 0),
            "converted": converted,
            "nurturing": status_counts.get("nurturing", 0),
            "customer": status_counts.get("customer", 0),
            "total_value": total_value_cents / 100,  # Convert to dollars
            "conversion_rate": round(conversion_rate, 2),
            "total": total,
        }
