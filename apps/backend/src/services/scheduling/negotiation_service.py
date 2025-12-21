"""
Negotiation Service - Request Existing Customers to Shift Times

Handles booking time shift negotiations:
1. Identify bookings that could shift to accommodate new request
2. Send negotiation requests via SMS/email
3. Track responses and auto-apply if accepted
4. Provide incentives for flexibility
"""

from datetime import datetime, date, time, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from enum import IntEnum
import logging

from pydantic import BaseModel

from .slot_manager import SlotManager, TimeSlot
from .availability_engine import AvailabilityEngine

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================


class NegotiationStatus(IntEnum):
    """Status of a negotiation request."""

    PENDING = 1
    SENT = 2
    VIEWED = 3
    ACCEPTED = 4
    DECLINED = 5
    EXPIRED = 6
    CANCELLED = 7


class NegotiationType(IntEnum):
    """Type of shift being requested."""

    TIME_SHIFT = 1  # Shift to different time same day
    CHEF_CHANGE = 2  # Accept different chef
    DATE_SHIFT = 3  # Move to different day (rare)


class IncentiveType(IntEnum):
    """Incentives for accepting shift."""

    NONE = 0
    DISCOUNT = 1  # Percentage off
    FREE_ADDON = 2  # Free extra protein or similar
    LOYALTY_POINTS = 3  # Bonus loyalty points


# ============================================================
# Data Models
# ============================================================


class ShiftRequest(BaseModel):
    """A request to shift a booking."""

    booking_id: UUID
    customer_id: UUID
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    current_date: date
    current_time: time
    current_slot: int
    proposed_time: time
    proposed_slot: int
    shift_minutes: int
    shift_direction: str  # 'earlier' or 'later'
    reason: str
    incentive_type: IncentiveType = IncentiveType.DISCOUNT
    incentive_value: float = 0.0  # e.g., 10 for 10% discount


class NegotiationRequest(BaseModel):
    """Full negotiation request with tracking."""

    id: UUID
    shift_request: ShiftRequest
    status: NegotiationStatus = NegotiationStatus.PENDING
    created_at: datetime
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_notes: Optional[str] = None
    expires_at: datetime
    message_id: Optional[str] = None  # SMS/Email ID for tracking


class NegotiationCandidate(BaseModel):
    """A booking that could potentially shift."""

    booking_id: UUID
    customer_id: UUID
    customer_name: str
    current_slot: int
    current_time: time
    can_shift_earlier: bool
    can_shift_later: bool
    max_earlier_minutes: int
    max_later_minutes: int
    shift_difficulty: int  # 1-10, lower = easier to shift
    customer_flexibility_score: int  # Based on past behavior


class NegotiationResult(BaseModel):
    """Result of negotiation attempt."""

    request_id: UUID
    success: bool
    status: NegotiationStatus
    message: str
    freed_slot: Optional[int] = None
    freed_time: Optional[time] = None


# ============================================================
# Negotiation Service
# ============================================================


class NegotiationService:
    """
    Manages negotiations with existing customers to shift booking times.

    Use Case:
    - New customer wants 6PM slot but it's full
    - 6PM customer could shift to 6:30PM (still within slot range)
    - Send friendly request with incentive
    - If accepted, auto-update booking and confirm new customer
    """

    # Incentive rates by shift amount
    INCENTIVE_SCHEDULE = {
        15: {"type": IncentiveType.NONE, "value": 0},  # 15 min = no incentive needed
        30: {"type": IncentiveType.DISCOUNT, "value": 5},  # 30 min = 5% off
        45: {"type": IncentiveType.DISCOUNT, "value": 8},  # 45 min = 8% off
        60: {"type": IncentiveType.DISCOUNT, "value": 10},  # 60 min = 10% off
    }

    # Response time limits
    EXPIRATION_HOURS = 24  # Request expires in 24 hours

    def __init__(
        self,
        slot_manager: Optional[SlotManager] = None,
        availability_engine: Optional[AvailabilityEngine] = None,
    ):
        """Initialize negotiation service."""
        self.slot_manager = slot_manager or SlotManager()
        self.availability_engine = availability_engine or AvailabilityEngine()

    def find_shiftable_bookings(
        self,
        target_date: date,
        target_slot: int,
        existing_bookings: List[Dict[str, Any]],
        shift_amount_needed: int = 30,
    ) -> List[NegotiationCandidate]:
        """
        Find existing bookings that could potentially shift.

        Args:
            target_date: Date we need the slot
            target_slot: Slot number (1-4) we need
            existing_bookings: Current bookings with customer info
            shift_amount_needed: Minutes we need freed up

        Returns:
            List of candidates sorted by shift difficulty
        """
        candidates = []

        slot_config = self.slot_manager.get_slot_configuration(TimeSlot(target_slot))

        for booking in existing_bookings:
            if booking.get("event_date") != target_date:
                continue
            if booking.get("slot_number") != target_slot:
                continue

            # Check if this booking can shift
            current_time = booking.get("event_time")
            if not current_time:
                continue

            # Calculate shift possibilities within slot range
            adjustment = self.slot_manager.calculate_adjustment(current_time, target_slot)

            # Can they shift earlier?
            earlier_room = adjustment + slot_config["preferred_adjustment_minutes"]
            can_earlier = earlier_room >= shift_amount_needed

            # Can they shift later?
            later_room = slot_config["max_adjustment_minutes"] - adjustment
            can_later = later_room >= shift_amount_needed

            if not can_earlier and not can_later:
                continue

            # Calculate difficulty score
            difficulty = self._calculate_shift_difficulty(booking, shift_amount_needed)

            candidates.append(
                NegotiationCandidate(
                    booking_id=UUID(booking["id"]),
                    customer_id=UUID(booking["customer_id"]),
                    customer_name=booking.get("customer_name", "Customer"),
                    current_slot=target_slot,
                    current_time=current_time,
                    can_shift_earlier=can_earlier,
                    can_shift_later=can_later,
                    max_earlier_minutes=earlier_room if can_earlier else 0,
                    max_later_minutes=later_room if can_later else 0,
                    shift_difficulty=difficulty,
                    customer_flexibility_score=booking.get("flexibility_score", 5),
                )
            )

        # Sort by difficulty (easier shifts first)
        candidates.sort(key=lambda c: c.shift_difficulty)

        return candidates

    def _calculate_shift_difficulty(self, booking: Dict[str, Any], shift_amount: int) -> int:
        """Calculate how difficult this shift request is (1-10)."""
        difficulty = 5  # Base difficulty

        # Large parties harder to shift
        guest_count = booking.get("guest_count", 10)
        if guest_count > 20:
            difficulty += 2
        elif guest_count > 30:
            difficulty += 4

        # Repeat customers more flexible
        if booking.get("is_repeat_customer"):
            difficulty -= 2

        # Chef-requested bookings harder
        if booking.get("chef_requested"):
            difficulty += 1

        # Longer shifts harder
        if shift_amount > 45:
            difficulty += 1
        if shift_amount > 60:
            difficulty += 2

        # Clamp to 1-10
        return max(1, min(10, difficulty))

    def create_shift_request(
        self,
        candidate: NegotiationCandidate,
        shift_direction: str,
        shift_minutes: int,
        reason: str = "Another customer needs your exact time slot",
    ) -> ShiftRequest:
        """
        Create a shift request for a candidate.

        Args:
            candidate: The booking candidate
            shift_direction: 'earlier' or 'later'
            shift_minutes: How many minutes to shift
            reason: Reason for the request
        """
        # Calculate new time
        current_dt = datetime.combine(date.today(), candidate.current_time)
        if shift_direction == "earlier":
            new_dt = current_dt - timedelta(minutes=shift_minutes)
        else:
            new_dt = current_dt + timedelta(minutes=shift_minutes)
        proposed_time = new_dt.time()

        # Determine incentive
        incentive = self._determine_incentive(shift_minutes)

        # Determine new slot (usually same, but check)
        new_slot = self.slot_manager.get_slot_for_time(proposed_time)

        return ShiftRequest(
            booking_id=candidate.booking_id,
            customer_id=candidate.customer_id,
            customer_name=candidate.customer_name,
            customer_phone="",  # Filled from database
            customer_email=None,  # Filled from database
            current_date=date.today(),  # Updated when used
            current_time=candidate.current_time,
            current_slot=candidate.current_slot,
            proposed_time=proposed_time,
            proposed_slot=new_slot or candidate.current_slot,
            shift_minutes=shift_minutes,
            shift_direction=shift_direction,
            reason=reason,
            incentive_type=incentive["type"],
            incentive_value=incentive["value"],
        )

    def _determine_incentive(self, shift_minutes: int) -> Dict[str, Any]:
        """Determine appropriate incentive for shift amount."""
        for threshold, incentive in sorted(self.INCENTIVE_SCHEDULE.items(), reverse=True):
            if shift_minutes >= threshold:
                return incentive
        return {"type": IncentiveType.NONE, "value": 0}

    def create_negotiation(
        self, shift_request: ShiftRequest, expiration_hours: int = 24
    ) -> NegotiationRequest:
        """Create a full negotiation request with tracking."""
        now = datetime.now()

        return NegotiationRequest(
            id=uuid4(),
            shift_request=shift_request,
            status=NegotiationStatus.PENDING,
            created_at=now,
            expires_at=now + timedelta(hours=expiration_hours),
        )

    def generate_sms_message(self, request: NegotiationRequest) -> str:
        """Generate SMS message for shift request."""
        sr = request.shift_request

        # Format times
        current = sr.current_time.strftime("%-I:%M %p")
        proposed = sr.proposed_time.strftime("%-I:%M %p")

        # Build message
        lines = [
            f"Hi {sr.customer_name.split()[0]}! 👋",
            "",
            f"Quick favor: Could you shift your My Hibachi party from {current} to {proposed}?",
        ]

        # Add incentive
        if sr.incentive_type == IncentiveType.DISCOUNT and sr.incentive_value > 0:
            lines.append("")
            lines.append(f"🎁 We'll give you {int(sr.incentive_value)}% off as a thank you!")

        lines.extend(
            ["", "Reply YES to confirm or NO to keep your current time.", "", "– My Hibachi Team"]
        )

        return "\n".join(lines)

    def generate_email_message(self, request: NegotiationRequest) -> Dict[str, str]:
        """Generate email for shift request."""
        sr = request.shift_request

        # Format times
        current = sr.current_time.strftime("%-I:%M %p")
        proposed = sr.proposed_time.strftime("%-I:%M %p")
        date_str = sr.current_date.strftime("%A, %B %d")

        subject = "Quick Request: Can You Shift Your Party Time? 🍱"

        # Build HTML body
        body_lines = [
            f"<p>Hi {sr.customer_name.split()[0]}!</p>",
            f"<p>We have another customer who really needs your exact time slot on {date_str}.</p>",
            f"<p>Would you be willing to shift your party from <strong>{current}</strong> to <strong>{proposed}</strong>?</p>",
        ]

        if sr.incentive_type == IncentiveType.DISCOUNT and sr.incentive_value > 0:
            body_lines.append(
                f"<p>🎁 <strong>As a thank you, we'll take {int(sr.incentive_value)}% off your booking!</strong></p>"
            )

        body_lines.extend(
            [
                "<p>",
                "<a href='ACCEPT_LINK' style='background:#22c55e;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin-right:10px;'>Yes, I Can Shift</a>",
                "<a href='DECLINE_LINK' style='background:#ef4444;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;'>No, Keep My Time</a>",
                "</p>",
                "<p>Thanks for understanding!</p>",
                "<p>– The My Hibachi Team</p>",
            ]
        )

        return {"subject": subject, "body": "\n".join(body_lines)}

    async def process_response(
        self, negotiation_id: UUID, accepted: bool, response_notes: Optional[str] = None
    ) -> NegotiationResult:
        """
        Process customer response to negotiation request.

        Args:
            negotiation_id: The negotiation request ID
            accepted: Whether customer accepted the shift
            response_notes: Any notes from customer

        Returns:
            NegotiationResult with outcome
        """
        # In real implementation, fetch from database
        # For now, return mock result

        if accepted:
            return NegotiationResult(
                request_id=negotiation_id,
                success=True,
                status=NegotiationStatus.ACCEPTED,
                message="Customer accepted the time shift. Booking updated.",
                freed_slot=1,  # Would be actual slot
                freed_time=time(18, 0),  # Would be actual time
            )
        else:
            return NegotiationResult(
                request_id=negotiation_id,
                success=False,
                status=NegotiationStatus.DECLINED,
                message="Customer declined. Looking for other options.",
                freed_slot=None,
                freed_time=None,
            )

    def get_negotiation_stats(self, negotiations: List[NegotiationRequest]) -> Dict[str, Any]:
        """Get statistics on negotiation success rates."""
        if not negotiations:
            return {"total": 0, "acceptance_rate": 0.0, "average_response_hours": 0.0}

        total = len(negotiations)
        accepted = len([n for n in negotiations if n.status == NegotiationStatus.ACCEPTED])
        declined = len([n for n in negotiations if n.status == NegotiationStatus.DECLINED])
        pending = len(
            [
                n
                for n in negotiations
                if n.status
                in (NegotiationStatus.PENDING, NegotiationStatus.SENT, NegotiationStatus.VIEWED)
            ]
        )
        expired = len([n for n in negotiations if n.status == NegotiationStatus.EXPIRED])

        # Calculate response times for responded ones
        response_times = []
        for n in negotiations:
            if n.sent_at and n.responded_at:
                delta = n.responded_at - n.sent_at
                response_times.append(delta.total_seconds() / 3600)  # Hours

        avg_response = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total": total,
            "accepted": accepted,
            "declined": declined,
            "pending": pending,
            "expired": expired,
            "acceptance_rate": (
                (accepted / (accepted + declined)) * 100 if (accepted + declined) > 0 else 0
            ),
            "average_response_hours": round(avg_response, 1),
        }


# Alias for scheduling router compatibility
NegotiationReason = NegotiationType
