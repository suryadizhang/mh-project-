"""
Smart Scheduling System Schemas

Pydantic models for:
- Availability checking
- Travel time calculation
- Chef assignment
- Address geocoding
- Booking negotiations
"""

from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class NegotiationStatusEnum(str, Enum):
    """Status of a booking negotiation request."""

    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class NegotiationReasonEnum(str, Enum):
    """Reason for requesting a time shift."""

    TRAVEL_CONFLICT = "travel_conflict"
    CHEF_AVAILABILITY = "chef_availability"
    DOUBLE_BOOKING = "double_booking"
    CUSTOMER_PREFERENCE = "customer_preference"


# ============================================================================
# Address Schemas
# ============================================================================


class AddressInput(BaseModel):
    """Input for geocoding an address."""

    full_address: str = Field(..., min_length=10, max_length=500)

    @field_validator("full_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")
        return v.strip()


class AddressCreateRequest(BaseModel):
    """Request to create/cache an address with geocoding."""

    raw_address: str = Field(..., min_length=10, max_length=500, description="Full street address")
    customer_id: Optional[UUID] = Field(None, description="Link to customer for saved addresses")
    label: Optional[str] = Field(None, max_length=50, description="Label like 'Home', 'Work'")
    is_default: bool = Field(False, description="Set as customer's default address")


class AddressResponse(BaseModel):
    """Response after creating/finding an address."""

    id: UUID
    raw_address: str
    formatted_address: Optional[str]
    lat: Optional[Decimal]
    lng: Optional[Decimal]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    geocode_status: str  # pending, success, failed, partial
    is_cached: bool = Field(False, description="True if address was already in cache")
    is_serviceable: bool = Field(True, description="True if within service area")

    class Config:
        from_attributes = True


class GeocodedAddressResponse(BaseModel):
    """Response from geocoding endpoint."""

    original_address: str
    normalized_address: Optional[str]
    lat: Optional[Decimal]
    lng: Optional[Decimal]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    is_valid: bool
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CustomerAddressListResponse(BaseModel):
    """List of customer's saved addresses."""

    addresses: list[AddressResponse]
    count: int


# ============================================================================
# Availability Schemas
# ============================================================================


class AvailabilityCheckRequest(BaseModel):
    """Request to check slot availability."""

    event_date: date
    event_time: time
    guest_count: int = Field(..., ge=1, le=100)
    venue_lat: Optional[Decimal] = None
    venue_lng: Optional[Decimal] = None
    preferred_chef_id: Optional[UUID] = None


class SlotAvailabilityResponse(BaseModel):
    """Single time slot availability info."""

    slot_time: time
    slot_label: str = ""  # "12PM", "3PM", "6PM", "9PM"
    is_available: bool
    available_chefs: int = 0
    conflict_reason: Optional[str] = None
    can_adjust: bool = False  # If slot can be shifted ±30/60 min
    adjustment_options: list[int] = []  # [-60, -30, 30, 60] minutes


class SuggestionResponse(BaseModel):
    """Response with availability and suggestions."""

    requested_date: date
    requested_time: time
    is_requested_available: bool
    conflict_reason: Optional[str] = None
    suggestions: list[SlotAvailabilityResponse] = []


class CalendarDayAvailability(BaseModel):
    """Availability for a single day."""

    date: date
    has_availability: bool
    available_slots: list[str] = []  # ["12PM", "3PM"]
    fully_booked: bool = False


class CalendarAvailabilityRequest(BaseModel):
    """Request for calendar view availability."""

    start_date: date
    end_date: date
    venue_lat: Optional[Decimal] = None
    venue_lng: Optional[Decimal] = None


class CalendarAvailabilityResponse(BaseModel):
    """Calendar view of availability."""

    days: list[CalendarDayAvailability]
    start_date: date
    end_date: date


# ============================================================================
# Travel Time Schemas
# ============================================================================


class TravelTimeRequest(BaseModel):
    """Request for travel time calculation."""

    origin_lat: Decimal
    origin_lng: Decimal
    dest_lat: Decimal
    dest_lng: Decimal
    departure_time: Optional[time] = None  # For rush hour calculation


class TravelTimeResponse(BaseModel):
    """Response with travel time info."""

    duration_minutes: int
    duration_with_traffic: int
    distance_km: Decimal
    is_rush_hour: bool = False
    traffic_multiplier: float = 1.0


# ============================================================================
# Chef Assignment Schemas
# ============================================================================


class ChefAssignmentRequest(BaseModel):
    """Request for chef recommendation."""

    booking_id: Optional[UUID] = None
    event_date: date
    event_time: time
    guest_count: int
    venue_lat: Decimal
    venue_lng: Decimal
    customer_id: Optional[UUID] = None
    preferred_chef_id: Optional[UUID] = None
    is_preference_required: bool = False
    skill_requirements: list[str] = []


class ChefScoreResponse(BaseModel):
    """Scored chef for assignment with detailed breakdown."""

    chef_id: UUID
    chef_name: str
    total_score: float = Field(ge=0.0, le=150.0)  # Max 100 + 50 bonus
    travel_score: float = Field(ge=0.0, le=100.0)
    skill_score: float = Field(ge=0.0, le=100.0)
    workload_score: float = Field(ge=0.0, le=100.0)
    history_score: float = Field(ge=0.0, le=100.0, default=0.0)  # For future customer history
    travel_time_minutes: int
    is_preferred: bool = False
    notes: str = ""


class ChefAssignmentResponse(BaseModel):
    """Response with recommended chef and alternatives."""

    booking_id: Optional[UUID] = None
    recommended_chef_id: Optional[UUID] = None
    recommended_chef_name: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=100.0)
    reason: str
    is_optimal: bool = True
    all_scores: list[ChefScoreResponse] = []


# ============================================================================
# Negotiation Schemas
# ============================================================================


class CreateNegotiationRequest(BaseModel):
    """Request to create a negotiation for time shift."""

    existing_booking_id: UUID
    proposed_time: time
    shift_minutes: int = Field(..., description="Positive = later, negative = earlier")
    reason: NegotiationReasonEnum
    new_booking_request_id: Optional[UUID] = None


class NegotiationResponse(BaseModel):
    """Response after creating negotiation."""

    negotiation_id: UUID
    status: NegotiationStatusEnum
    notification_sent: bool = False
    incentive_offered: Optional[str] = None  # "free_noodles", "free_appetizer"


class RespondToNegotiationRequest(BaseModel):
    """Customer response to negotiation."""

    negotiation_id: UUID
    accepted: bool
    customer_notes: Optional[str] = None
    selected_incentive: Optional[str] = None  # If choosing between options


class NegotiationDetailResponse(BaseModel):
    """Detailed negotiation info."""

    id: UUID
    existing_booking_id: UUID
    original_time: time
    proposed_time: time
    shift_minutes: int
    status: NegotiationStatusEnum
    incentive_type: Optional[str]
    incentive_description: Optional[str]
    reason: str
    expires_at: Optional[str]


class PendingNegotiationsResponse(BaseModel):
    """List of pending negotiations."""

    negotiations: list[NegotiationDetailResponse]
    count: int


# ============================================================================
# Config Schemas
# ============================================================================


class SlotConfigResponse(BaseModel):
    """Time slot configuration."""

    slot_name: str  # "12PM"
    slot_time: time
    min_adjust_minutes: int = -60
    max_adjust_minutes: int = 60
    min_event_duration: int = 90
    max_event_duration: int = 120
    is_active: bool = True


class AllSlotsConfigResponse(BaseModel):
    """All slot configurations."""

    slots: list[SlotConfigResponse]


class EventDurationRequest(BaseModel):
    """Request to calculate event duration."""

    guest_count: int = Field(..., ge=1, le=100)


class EventDurationResponse(BaseModel):
    """Response with calculated duration."""

    guest_count: int
    duration_minutes: int
    duration_formula: str = ""  # "1-10 guests = 90 min"
