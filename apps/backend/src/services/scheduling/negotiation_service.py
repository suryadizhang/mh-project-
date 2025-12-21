"""
Negotiation Service

Handles polite requests to customers to shift their booking times
when conflicts arise or for optimization purposes.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.booking import Booking


class NegotiationStatus(str, Enum):
    """Status of a negotiation request"""

    PENDING = "pending"  # Request sent, awaiting response
    ACCEPTED = "accepted"  # Customer agreed to shift
    DECLINED = "declined"  # Customer declined
    EXPIRED = "expired"  # No response within time limit
    CANCELLED = "cancelled"  # Staff cancelled the request
    AUTO_APPLIED = "auto_applied"  # System auto-applied adjustment


class NegotiationReason(str, Enum):
    """Reason for requesting time shift"""

    TRAVEL_OPTIMIZATION = "travel_optimization"
    CHEF_AVAILABILITY = "chef_availability"
    NEW_BOOKING_CONFLICT = "new_booking_conflict"
    WEATHER_DELAY = "weather_delay"
    EQUIPMENT_ISSUE = "equipment_issue"
    CUSTOMER_REQUEST = "customer_request"


# Response deadline (hours)
RESPONSE_DEADLINE_HOURS = 24

# Maximum incentive discount percentage
MAX_INCENTIVE_PERCENT = 10


@dataclass
class ShiftProposal:
    """A proposed time shift for negotiation"""

    original_time: time
    proposed_time: time
    shift_minutes: int  # Positive = later, negative = earlier
    reason: NegotiationReason
    benefit_description: str
    incentive_percent: float = 0.0  # Discount offered


@dataclass
class NegotiationRequest:
    """A request to shift a booking time"""

    id: UUID
    booking_id: UUID
    customer_email: str
    customer_name: str
    original_date: date
    original_time: time
    proposed_time: time
    shift_minutes: int
    reason: NegotiationReason
    reason_message: str
    incentive_percent: float
    status: NegotiationStatus
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime] = None
    response_note: Optional[str] = None


@dataclass
class NegotiationResult:
    """Result of a negotiation attempt"""

    success: bool
    negotiation_id: UUID
    status: NegotiationStatus
    message: str
    booking_updated: bool = False
    new_time: Optional[time] = None


class NegotiationService:
    """
    Manages polite negotiation requests for booking time shifts.

    Features:
    - Creates negotiation requests for existing bookings
    - Tracks customer responses
    - Applies incentives (discounts) for flexibility
    - Auto-expires unanswered requests
    - Respects customer preferences (some may opt-out)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_shift_request(
        self,
        booking_id: UUID,
        proposed_time: time,
        reason: NegotiationReason,
        reason_message: Optional[str] = None,
        incentive_percent: float = 0.0,
        requested_by_user_id: Optional[UUID] = None,
    ) -> NegotiationResult:
        """
        Create a request to shift an existing booking's time.

        Args:
            booking_id: The booking to potentially shift
            proposed_time: The new proposed time
            reason: Why the shift is requested
            reason_message: Custom message explaining the reason
            incentive_percent: Discount to offer (0-10%)
            requested_by_user_id: Staff member making the request

        Returns:
            NegotiationResult indicating success/failure
        """
        # Fetch the booking
        booking = await self._get_booking(booking_id)
        if not booking:
            return NegotiationResult(
                success=False,
                negotiation_id=UUID("00000000-0000-0000-0000-000000000000"),
                status=NegotiationStatus.CANCELLED,
                message="Booking not found",
            )

        # Check if booking can be negotiated
        if booking.status not in ["confirmed", "pending"]:
            return NegotiationResult(
                success=False,
                negotiation_id=UUID("00000000-0000-0000-0000-000000000000"),
                status=NegotiationStatus.CANCELLED,
                message=f"Cannot negotiate booking with status '{booking.status}'",
            )

        # Check if there's already a pending negotiation
        existing = await self._get_pending_negotiation(booking_id)
        if existing:
            return NegotiationResult(
                success=False,
                negotiation_id=existing,
                status=NegotiationStatus.PENDING,
                message="There is already a pending negotiation for this booking",
            )

        # Calculate shift
        original_minutes = booking.event_time.hour * 60 + booking.event_time.minute
        proposed_minutes = proposed_time.hour * 60 + proposed_time.minute
        shift_minutes = proposed_minutes - original_minutes

        if shift_minutes == 0:
            return NegotiationResult(
                success=False,
                negotiation_id=UUID("00000000-0000-0000-0000-000000000000"),
                status=NegotiationStatus.CANCELLED,
                message="Proposed time is the same as current time",
            )

        # Cap incentive
        incentive_percent = min(incentive_percent, MAX_INCENTIVE_PERCENT)

        # Generate message if not provided
        if not reason_message:
            reason_message = self._generate_reason_message(reason, shift_minutes)

        # Create negotiation record
        negotiation_id = uuid4()
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=RESPONSE_DEADLINE_HOURS)

        from sqlalchemy import text

        insert_query = text(
            """
            INSERT INTO core.booking_negotiations (
                id, booking_id, original_time, proposed_time, 
                shift_minutes, reason, reason_message,
                incentive_percent, status, created_at, expires_at,
                requested_by_user_id
            ) VALUES (
                :id, :booking_id, :original_time, :proposed_time,
                :shift_minutes, :reason, :reason_message,
                :incentive_percent, :status, :created_at, :expires_at,
                :requested_by
            )
        """
        )

        try:
            await self.session.execute(
                insert_query,
                {
                    "id": str(negotiation_id),
                    "booking_id": str(booking_id),
                    "original_time": booking.event_time,
                    "proposed_time": proposed_time,
                    "shift_minutes": shift_minutes,
                    "reason": reason.value,
                    "reason_message": reason_message,
                    "incentive_percent": incentive_percent,
                    "status": NegotiationStatus.PENDING.value,
                    "created_at": now,
                    "expires_at": expires_at,
                    "requested_by": str(requested_by_user_id) if requested_by_user_id else None,
                },
            )
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            return NegotiationResult(
                success=False,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.CANCELLED,
                message=f"Failed to create negotiation: {str(e)}",
            )

        # TODO: Send email/SMS notification to customer
        # await self._send_negotiation_notification(booking, proposed_time, reason_message, incentive_percent)

        return NegotiationResult(
            success=True,
            negotiation_id=negotiation_id,
            status=NegotiationStatus.PENDING,
            message=f"Negotiation request sent. Customer has {RESPONSE_DEADLINE_HOURS} hours to respond.",
        )

    async def respond_to_negotiation(
        self,
        negotiation_id: UUID,
        accepted: bool,
        customer_note: Optional[str] = None,
    ) -> NegotiationResult:
        """
        Record customer's response to a negotiation request.

        Args:
            negotiation_id: The negotiation to respond to
            accepted: True if customer accepts the time change
            customer_note: Optional note from customer

        Returns:
            NegotiationResult with outcome
        """
        from sqlalchemy import text

        # Get negotiation details
        query = text(
            """
            SELECT 
                n.booking_id, n.proposed_time, n.status, n.expires_at,
                n.incentive_percent
            FROM core.booking_negotiations n
            WHERE n.id = :neg_id
        """
        )

        try:
            result = await self.session.execute(query, {"neg_id": str(negotiation_id)})
            row = result.fetchone()
        except Exception:
            return NegotiationResult(
                success=False,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.CANCELLED,
                message="Negotiation not found",
            )

        if not row:
            return NegotiationResult(
                success=False,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.CANCELLED,
                message="Negotiation not found",
            )

        booking_id, proposed_time, current_status, expires_at, incentive = row

        # Check if already responded or expired
        if current_status != NegotiationStatus.PENDING.value:
            return NegotiationResult(
                success=False,
                negotiation_id=negotiation_id,
                status=NegotiationStatus(current_status),
                message=f"Negotiation is already {current_status}",
            )

        if expires_at and datetime.utcnow() > expires_at:
            await self._update_negotiation_status(negotiation_id, NegotiationStatus.EXPIRED)
            return NegotiationResult(
                success=False,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.EXPIRED,
                message="This request has expired",
            )

        now = datetime.utcnow()

        if accepted:
            # Update booking with new time
            booking_updated = await self._apply_time_change(
                UUID(booking_id),
                proposed_time,
                incentive,
            )

            # Update negotiation status
            await self._update_negotiation_status(
                negotiation_id,
                NegotiationStatus.ACCEPTED,
                responded_at=now,
                response_note=customer_note,
            )

            return NegotiationResult(
                success=True,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.ACCEPTED,
                message="Thank you! Your booking time has been updated.",
                booking_updated=booking_updated,
                new_time=proposed_time,
            )
        else:
            # Customer declined
            await self._update_negotiation_status(
                negotiation_id,
                NegotiationStatus.DECLINED,
                responded_at=now,
                response_note=customer_note,
            )

            return NegotiationResult(
                success=True,
                negotiation_id=negotiation_id,
                status=NegotiationStatus.DECLINED,
                message="No problem! Your original booking time remains unchanged.",
            )

    async def check_and_propose_shift(
        self,
        new_booking_venue_lat: Decimal,
        new_booking_venue_lng: Decimal,
        new_booking_date: date,
        new_booking_time: time,
        new_booking_duration: int,
    ) -> Optional[ShiftProposal]:
        """
        Check if a new booking would benefit from shifting an existing one.

        Used when a new booking creates a travel time conflict.
        Returns a proposal if shifting another booking would help.
        """
        from .travel_time_service import TravelTimeService

        travel_service = TravelTimeService(self.session)

        # Find nearby bookings on the same day
        query = select(Booking).where(
            and_(
                Booking.event_date == new_booking_date,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.venue_lat.is_not(None),
            )
        )

        result = await self.session.execute(query)
        nearby_bookings = result.scalars().all()

        for booking in nearby_bookings:
            # Check travel time between venues
            travel_time = await travel_service.get_travel_time(
                float(booking.venue_lat),
                float(booking.venue_lng),
                float(new_booking_venue_lat),
                float(new_booking_venue_lng),
                datetime.combine(new_booking_date, new_booking_time),
            )

            if travel_time is None:
                continue

            # Check if there's a conflict
            booking_end = datetime.combine(
                booking.event_date, booking.effective_start_time
            ) + timedelta(minutes=booking.calculated_duration)

            new_start = datetime.combine(new_booking_date, new_booking_time)
            gap = (new_start - booking_end).total_seconds() / 60

            buffer = 15  # minutes
            needed_gap = travel_time + buffer

            if gap < needed_gap:
                # Conflict! Propose shifting the existing booking earlier
                shift_needed = int(needed_gap - gap)

                # Check if this booking can be shifted
                original_minutes = booking.event_time.hour * 60 + booking.event_time.minute
                new_minutes = original_minutes - shift_needed

                if new_minutes < 11 * 60:  # Don't shift before 11 AM
                    continue

                new_time = time(new_minutes // 60, new_minutes % 60)

                return ShiftProposal(
                    original_time=booking.event_time,
                    proposed_time=new_time,
                    shift_minutes=-shift_needed,
                    reason=NegotiationReason.NEW_BOOKING_CONFLICT,
                    benefit_description=f"Moving your event {shift_needed} minutes earlier would help us serve you better.",
                    incentive_percent=5.0,  # Offer 5% discount
                )

        return None

    def _generate_reason_message(
        self,
        reason: NegotiationReason,
        shift_minutes: int,
    ) -> str:
        """Generate a polite message explaining the shift request."""
        direction = "earlier" if shift_minutes < 0 else "later"
        amount = abs(shift_minutes)

        messages = {
            NegotiationReason.TRAVEL_OPTIMIZATION: (
                f"To ensure our chef arrives fresh and on time, we'd like to "
                f"start your event {amount} minutes {direction}. This helps us "
                f"avoid rush hour traffic and ensures the best experience."
            ),
            NegotiationReason.CHEF_AVAILABILITY: (
                f"Your preferred chef is available if we adjust your event to "
                f"start {amount} minutes {direction}. Would this work for you?"
            ),
            NegotiationReason.NEW_BOOKING_CONFLICT: (
                f"We have a nearby event and would appreciate if you could "
                f"start {amount} minutes {direction}. This helps us serve "
                f"both parties with excellence."
            ),
            NegotiationReason.WEATHER_DELAY: (
                f"Due to weather conditions, we'd like to start {amount} minutes "
                f"{direction} to ensure safe travel for our chef and equipment."
            ),
            NegotiationReason.EQUIPMENT_ISSUE: (
                f"To ensure all equipment is ready, we'd like to adjust your "
                f"start time by {amount} minutes {direction}."
            ),
            NegotiationReason.CUSTOMER_REQUEST: (
                f"As requested, we can adjust your event to start {amount} " f"minutes {direction}."
            ),
        }

        return messages.get(
            reason, f"We'd like to adjust your event by {amount} minutes {direction}."
        )

    async def _get_booking(self, booking_id: UUID) -> Optional[Booking]:
        """Fetch a booking by ID."""
        result = await self.session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def _get_pending_negotiation(
        self,
        booking_id: UUID,
    ) -> Optional[UUID]:
        """Check if there's an active negotiation for a booking."""
        from sqlalchemy import text

        query = text(
            """
            SELECT id FROM core.booking_negotiations
            WHERE booking_id = :booking_id
              AND status = 'pending'
              AND expires_at > NOW()
            LIMIT 1
        """
        )

        try:
            result = await self.session.execute(query, {"booking_id": str(booking_id)})
            row = result.fetchone()
            return UUID(row[0]) if row else None
        except Exception:
            return None

    async def _update_negotiation_status(
        self,
        negotiation_id: UUID,
        status: NegotiationStatus,
        responded_at: Optional[datetime] = None,
        response_note: Optional[str] = None,
    ):
        """Update a negotiation's status."""
        from sqlalchemy import text

        query = text(
            """
            UPDATE core.booking_negotiations
            SET status = :status,
                responded_at = :responded_at,
                response_note = :response_note,
                updated_at = NOW()
            WHERE id = :neg_id
        """
        )

        await self.session.execute(
            query,
            {
                "neg_id": str(negotiation_id),
                "status": status.value,
                "responded_at": responded_at,
                "response_note": response_note,
            },
        )
        await self.session.commit()

    async def _apply_time_change(
        self,
        booking_id: UUID,
        new_time: time,
        discount_percent: float,
    ) -> bool:
        """Apply the negotiated time change to a booking."""
        try:
            stmt = (
                update(Booking)
                .where(Booking.id == booking_id)
                .values(
                    adjusted_slot_time=new_time,
                    adjustment_reason="customer_accepted_negotiation",
                    # TODO: Apply discount to total if incentive offered
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def get_pending_negotiations(
        self,
        limit: int = 20,
    ) -> list[NegotiationRequest]:
        """Get all pending negotiations (for admin dashboard)."""
        from sqlalchemy import text

        query = text(
            """
            SELECT 
                n.id, n.booking_id, n.original_time, n.proposed_time,
                n.shift_minutes, n.reason, n.reason_message,
                n.incentive_percent, n.status, n.created_at, n.expires_at,
                b.customer_email, b.customer_name, b.event_date
            FROM core.booking_negotiations n
            JOIN core.bookings b ON b.id = n.booking_id
            WHERE n.status = 'pending'
              AND n.expires_at > NOW()
            ORDER BY n.created_at DESC
            LIMIT :limit
        """
        )

        try:
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
        except Exception:
            return []

        negotiations = []
        for row in rows:
            negotiations.append(
                NegotiationRequest(
                    id=UUID(row[0]),
                    booking_id=UUID(row[1]),
                    customer_email=row[11],
                    customer_name=row[12],
                    original_date=row[13],
                    original_time=row[2],
                    proposed_time=row[3],
                    shift_minutes=row[4],
                    reason=NegotiationReason(row[5]),
                    reason_message=row[6],
                    incentive_percent=row[7],
                    status=NegotiationStatus(row[8]),
                    created_at=row[9],
                    expires_at=row[10],
                )
            )

        return negotiations

    async def expire_old_negotiations(self):
        """Mark expired negotiations. Run periodically via cron."""
        from sqlalchemy import text

        query = text(
            """
            UPDATE core.booking_negotiations
            SET status = 'expired', updated_at = NOW()
            WHERE status = 'pending' AND expires_at < NOW()
        """
        )

        await self.session.execute(query)
        await self.session.commit()
