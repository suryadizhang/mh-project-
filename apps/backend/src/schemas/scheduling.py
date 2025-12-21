"""
Pydantic Schemas for Smart Scheduling System

Request/Response models for:
- Availability checking
- Alternative suggestions
- Chef assignment
- Booking negotiations
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Enums
# ============================================================================


class NegotiationStatusEnum(str, Enum):
    """Status of a negotiation request"""

    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"
    cancelled = "cancelled"


class NegotiationReasonEnum(str, Enum):
    """Reason for requesting time shift"""

    travel_optimization = "travel_optimization"
    chef_availability = "chef_availability"
    new_booking_conflict = "new_booking_conflict"
    weather_delay = "weather_delay"
    equipment_issue = "equipment_issue"
    customer_request = "customer_request"


# ============================================================================
# Address & Geocoding
# ============================================================================


class AddressInput(BaseModel):
    """Address input for geocoding"""

    street_address: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")

    @property
    def full_address(self) -> str:
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"


class GeocodedAddressResponse(BaseModel):
    """Response from geocoding an address"""

    model_config = ConfigDict(from_attributes=True)

    original_address: str
    normalized_address: str
    lat: Decimal
    lng: Decimal
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_valid: bool
    confidence: float


# ============================================================================
# Availability & Suggestions
# ============================================================================


class AvailabilityCheckRequest(BaseModel):
    """Request to check slot availability"""

    event_date: date
    event_time: time
    guest_count: int = Field(..., ge=1, le=200)
    venue_address: Optional[str] = None
    venue_lat: Optional[Decimal] = None
    venue_lng: Optional[Decimal] = None
    preferred_chef_id: Optional[UUID] = None


class SlotAvailabilityResponse(BaseModel):
    """Availability status for a single slot"""

    model_config = ConfigDict(from_attributes=True)

    slot_time: time
    slot_date: date
    is_available: bool
    conflict_reason: Optional[str] = None
    adjusted_time: Optional[time] = None
    travel_time_from_prev: Optional[int] = None
    travel_time_to_next: Optional[int] = None
    score: float = 0.0


class SuggestionResponse(BaseModel):
    """Response with availability and alternative suggestions"""

    requested_date: date
    requested_time: time
    is_requested_available: bool
    conflict_reason: Optional[str] = None
    suggestions: list[SlotAvailabilityResponse] = []
    message: str


class CalendarAvailabilityRequest(BaseModel):
    """Request for calendar view of availability"""

    start_date: date
    end_date: date
    guest_count: int = Field(..., ge=1, le=200)
    venue_lat: Optional[Decimal] = None
    venue_lng: Optional[Decimal] = None
    preferred_chef_id: Optional[UUID] = None


class CalendarDayAvailability(BaseModel):
    """Availability for a single day"""

    date: date
    slots: list[SlotAvailabilityResponse]


class CalendarAvailabilityResponse(BaseModel):
    """Calendar view of availability across date range"""

    start_date: date
    end_date: date
    days: list[CalendarDayAvailability]


# ============================================================================
# Travel Time
# ============================================================================


class TravelTimeRequest(BaseModel):
    """Request to calculate travel time between two points"""

    origin_lat: Decimal = Field(..., ge=-90, le=90)
    origin_lng: Decimal = Field(..., ge=-180, le=180)
    destination_lat: Decimal = Field(..., ge=-90, le=90)
    destination_lng: Decimal = Field(..., ge=-180, le=180)
    departure_time: Optional[datetime] = None


class TravelTimeResponse(BaseModel):
    """Response with travel time calculation"""

    origin_lat: Decimal
    origin_lng: Decimal
    destination_lat: Decimal
    destination_lng: Decimal
    travel_time_minutes: int
    is_rush_hour: bool
    base_time_minutes: int
    multiplier_applied: float
    distance_km: Optional[float] = None
    from_cache: bool = False


# ============================================================================
# Chef Assignment
# ============================================================================


class ChefScoreResponse(BaseModel):
    """Scoring result for a chef-booking match"""

    model_config = ConfigDict(from_attributes=True)

    chef_id: UUID
    chef_name: str
    total_score: float
    travel_score: float
    skill_score: float
    workload_score: float
    history_score: float
    travel_time_minutes: Optional[int] = None
    is_preferred: bool = False
    notes: list[str] = []


class ChefAssignmentRequest(BaseModel):
    """Request for chef assignment recommendation"""

    booking_id: UUID
    event_date: date
    event_time: time
    venue_lat: Decimal
    venue_lng: Decimal
    guest_count: int = Field(..., ge=1, le=200)
    customer_id: Optional[UUID] = None
    preferred_chef_id: Optional[UUID] = None
    is_preference_required: bool = False


class ChefAssignmentResponse(BaseModel):
    """Response with chef assignment recommendation"""

    booking_id: UUID
    recommended_chef_id: UUID
    recommended_chef_name: str
    confidence_score: float
    reason: str
    is_optimal: bool
    all_scores: list[ChefScoreResponse] = []


# ============================================================================
# Negotiations
# ============================================================================


class CreateNegotiationRequest(BaseModel):
    """Request to create a negotiation for time shift"""

    booking_id: UUID
    proposed_time: time
    reason: NegotiationReasonEnum
    reason_message: Optional[str] = None
    incentive_percent: float = Field(default=0.0, ge=0, le=10)


class NegotiationResponse(BaseModel):
    """Response after creating or updating negotiation"""

    negotiation_id: UUID
    status: NegotiationStatusEnum
    message: str
    booking_updated: bool = False
    new_time: Optional[time] = None


class RespondToNegotiationRequest(BaseModel):
    """Customer response to a negotiation request"""

    negotiation_id: UUID
    accepted: bool
    customer_note: Optional[str] = Field(None, max_length=500)


class NegotiationDetailResponse(BaseModel):
    """Full details of a negotiation request"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    customer_email: str
    customer_name: str
    original_date: date
    original_time: time
    proposed_time: time
    shift_minutes: int
    reason: NegotiationReasonEnum
    reason_message: str
    incentive_percent: float
    status: NegotiationStatusEnum
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime] = None
    response_note: Optional[str] = None


class PendingNegotiationsResponse(BaseModel):
    """List of pending negotiations"""

    count: int
    negotiations: list[NegotiationDetailResponse]


# ============================================================================
# Slot Configuration
# ============================================================================


class SlotConfigResponse(BaseModel):
    """Configuration for a time slot"""

    slot_time: time
    slot_name: str
    adjust_earlier_minutes: int
    adjust_later_minutes: int
    is_active: bool = True


class AllSlotsConfigResponse(BaseModel):
    """All available slot configurations"""

    slots: list[SlotConfigResponse]


# ============================================================================
# Event Duration
# ============================================================================


class EventDurationRequest(BaseModel):
    """Request to calculate event duration"""

    guest_count: int = Field(..., ge=1, le=200)


class EventDurationResponse(BaseModel):
    """Calculated event duration"""

    guest_count: int
    duration_minutes: int
    formula: str = "min(60 + (guests × 3), 120)"
