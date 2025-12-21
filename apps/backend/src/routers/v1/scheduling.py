"""
Smart Scheduling API Endpoints

Provides:
- Availability checking with smart suggestions
- Travel time calculation
- Chef assignment optimization
- Booking negotiation management
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.scheduling import (
    # Availability
    AvailabilityCheckRequest,
    SuggestionResponse,
    SlotAvailabilityResponse,
    CalendarAvailabilityRequest,
    CalendarAvailabilityResponse,
    CalendarDayAvailability,
    # Travel
    TravelTimeRequest,
    TravelTimeResponse,
    # Chef Assignment
    ChefAssignmentRequest,
    ChefAssignmentResponse,
    ChefScoreResponse,
    # Negotiation
    CreateNegotiationRequest,
    NegotiationResponse,
    RespondToNegotiationRequest,
    NegotiationDetailResponse,
    PendingNegotiationsResponse,
    NegotiationStatusEnum,
    # Config
    SlotConfigResponse,
    AllSlotsConfigResponse,
    EventDurationRequest,
    EventDurationResponse,
    # Address
    AddressInput,
    GeocodedAddressResponse,
)
from services.scheduling import (
    SlotManagerService,
    SuggestionEngine,
    TravelTimeService,
    GeocodingService,
    ChefOptimizerService,
    NegotiationService,
    NegotiationReason,
)
from services.scheduling.travel_time_service import Coordinates

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


# ============================================================================
# Availability Endpoints
# ============================================================================


@router.post("/availability/check", response_model=SuggestionResponse)
async def check_availability(
    request: AvailabilityCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Check if a requested time slot is available.

    If unavailable, returns smart suggestions for alternative times.
    Suggestions are ranked by proximity to requested time.
    """
    slot_manager = SlotManagerService()
    suggestion_engine = SuggestionEngine(db, slot_manager=slot_manager)

    result = await suggestion_engine.check_and_suggest(
        requested_date=request.event_date,
        requested_time=request.event_time,
        guest_count=request.guest_count,
        venue_lat=request.venue_lat,
        venue_lng=request.venue_lng,
        preferred_chef_id=request.preferred_chef_id,
    )

    return SuggestionResponse(
        requested_date=result.requested_date,
        requested_time=result.requested_time,
        is_requested_available=result.is_requested_available,
        conflict_reason=result.conflict_reason,
        suggestions=[
            SlotAvailabilityResponse(
                slot_time=s.slot_time,
                slot_date=s.slot_date,
                is_available=s.is_available,
                conflict_reason=s.conflict_reason,
                adjusted_time=s.adjusted_time,
                travel_time_from_prev=s.travel_time_from_prev,
                travel_time_to_next=s.travel_time_to_next,
                score=s.score,
            )
            for s in result.suggestions
        ],
        message=result.message,
    )


@router.post("/availability/calendar", response_model=CalendarAvailabilityResponse)
async def get_calendar_availability(
    request: CalendarAvailabilityRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get availability for all slots across a date range.

    Useful for displaying a calendar view with available slots.
    Limited to 30 days max.
    """
    # Validate date range
    delta = (request.end_date - request.start_date).days
    if delta < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )
    if delta > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days",
        )

    slot_manager = SlotManagerService()
    suggestion_engine = SuggestionEngine(db, slot_manager=slot_manager)

    calendar = await suggestion_engine.get_availability_calendar(
        start_date=request.start_date,
        end_date=request.end_date,
        guest_count=request.guest_count,
        venue_lat=request.venue_lat,
        venue_lng=request.venue_lng,
        preferred_chef_id=request.preferred_chef_id,
    )

    days = []
    for cal_date, slots in sorted(calendar.items()):
        days.append(
            CalendarDayAvailability(
                date=cal_date,
                slots=[
                    SlotAvailabilityResponse(
                        slot_time=s.slot_time,
                        slot_date=s.slot_date,
                        is_available=s.is_available,
                        conflict_reason=s.conflict_reason,
                        score=s.score,
                    )
                    for s in slots
                ],
            )
        )

    return CalendarAvailabilityResponse(
        start_date=request.start_date,
        end_date=request.end_date,
        days=days,
    )


# ============================================================================
# Travel Time Endpoints
# ============================================================================


@router.post("/travel-time/calculate", response_model=TravelTimeResponse)
async def calculate_travel_time(
    request: TravelTimeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate travel time between two locations.

    Accounts for:
    - Rush hour traffic (Mon-Fri 3-7 PM = +50%)
    - Caches results for efficiency
    """
    travel_service = TravelTimeService(db)

    departure = request.departure_time or datetime.now()

    # Create Coordinates objects for the service
    origin = Coordinates(
        lat=request.origin_lat,
        lng=request.origin_lng,
    )
    destination = Coordinates(
        lat=request.destination_lat,
        lng=request.destination_lng,
    )

    travel_result = await travel_service.get_travel_time(
        origin=origin,
        destination=destination,
        departure_time=departure,
    )

    if travel_result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to calculate travel time. Please try again.",
        )

    return TravelTimeResponse(
        origin_lat=request.origin_lat,
        origin_lng=request.origin_lng,
        destination_lat=request.destination_lat,
        destination_lng=request.destination_lng,
        travel_time_minutes=travel_result.traffic_duration_minutes,
        is_rush_hour=travel_result.is_rush_hour,
        base_time_minutes=travel_result.base_duration_minutes,
        multiplier_applied=1.5 if travel_result.is_rush_hour else 1.0,
        from_cache=travel_result.from_cache,
    )


# ============================================================================
# Geocoding Endpoints
# ============================================================================


@router.post("/geocode", response_model=GeocodedAddressResponse)
async def geocode_address(
    address: AddressInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Convert a street address to geographic coordinates.

    Returns normalized address and lat/lng coordinates.
    """
    geocoding_service = GeocodingService(db)

    result = await geocoding_service.geocode(address.full_address)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to geocode address. Please verify the address.",
        )

    return GeocodedAddressResponse(
        original_address=result.original_address,
        normalized_address=result.normalized_address,
        lat=result.lat,
        lng=result.lng,
        city=result.city,
        state=result.state,
        zip_code=result.zip_code,
        is_valid=result.is_valid,
        confidence=result.confidence,
    )


@router.get("/geocode/validate")
async def validate_address(
    address: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate an address string.

    Returns whether the address is valid and a normalized version.
    """
    geocoding_service = GeocodingService(db)

    is_valid, message = await geocoding_service.validate_address(address)

    return {
        "is_valid": is_valid,
        "message": message,
    }


# ============================================================================
# Chef Assignment Endpoints
# ============================================================================


@router.post("/chef/recommend", response_model=ChefAssignmentResponse)
async def recommend_chef(
    request: ChefAssignmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get optimal chef assignment recommendation for a booking.

    Scoring factors:
    - Travel time efficiency (closest chef)
    - Skill match for party size
    - Workload balance
    - Customer history
    - Customer preference

    Requires: Station Manager role or higher
    """
    # TODO: Add RBAC check for station_manager role

    chef_optimizer = ChefOptimizerService(db)

    recommendation = await chef_optimizer.get_optimal_assignment(
        booking_id=request.booking_id,
        event_date=request.event_date,
        event_time=request.event_time,
        venue_lat=request.venue_lat,
        venue_lng=request.venue_lng,
        guest_count=request.guest_count,
        customer_id=request.customer_id,
        preferred_chef_id=request.preferred_chef_id,
        is_preference_required=request.is_preference_required,
    )

    return ChefAssignmentResponse(
        booking_id=recommendation.booking_id,
        recommended_chef_id=recommendation.recommended_chef_id,
        recommended_chef_name=recommendation.recommended_chef_name,
        confidence_score=recommendation.confidence_score,
        reason=recommendation.reason,
        is_optimal=recommendation.is_optimal,
        all_scores=[
            ChefScoreResponse(
                chef_id=s.chef_id,
                chef_name=s.chef_name,
                total_score=s.total_score,
                travel_score=s.travel_score,
                skill_score=s.skill_score,
                workload_score=s.workload_score,
                history_score=s.history_score,
                travel_time_minutes=s.travel_time_minutes,
                is_preferred=s.is_preferred,
                notes=s.notes,
            )
            for s in recommendation.all_scores
        ],
    )


@router.get("/chef/top-recommendations", response_model=list[ChefScoreResponse])
async def get_top_chef_recommendations(
    booking_id: UUID,
    event_date: date,
    event_time: time,
    venue_lat: Decimal,
    venue_lng: Decimal,
    guest_count: int,
    limit: int = Query(default=3, ge=1, le=10),
    customer_id: Optional[UUID] = None,
    preferred_chef_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get top N chef recommendations for manual selection.

    Returns scored list of available chefs for station manager to choose from.
    """
    chef_optimizer = ChefOptimizerService(db)

    scores = await chef_optimizer.get_top_recommendations(
        booking_id=booking_id,
        event_date=event_date,
        event_time=event_time,
        venue_lat=venue_lat,
        venue_lng=venue_lng,
        guest_count=guest_count,
        customer_id=customer_id,
        preferred_chef_id=preferred_chef_id,
        limit=limit,
    )

    return [
        ChefScoreResponse(
            chef_id=s.chef_id,
            chef_name=s.chef_name,
            total_score=s.total_score,
            travel_score=s.travel_score,
            skill_score=s.skill_score,
            workload_score=s.workload_score,
            history_score=s.history_score,
            travel_time_minutes=s.travel_time_minutes,
            is_preferred=s.is_preferred,
            notes=s.notes,
        )
        for s in scores
    ]


# ============================================================================
# Negotiation Endpoints
# ============================================================================


@router.post("/negotiations", response_model=NegotiationResponse)
async def create_negotiation(
    request: CreateNegotiationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a request to shift an existing booking's time.

    Sends a polite notification to the customer asking if they
    can accommodate a time change. Optional incentive (discount)
    can be offered.

    Requires: Station Manager role or higher
    """
    # TODO: Add RBAC check
    # TODO: Get current user ID

    negotiation_service = NegotiationService(db)

    result = await negotiation_service.create_shift_request(
        booking_id=request.booking_id,
        proposed_time=request.proposed_time,
        reason=NegotiationReason(request.reason.value),
        reason_message=request.reason_message,
        incentive_percent=request.incentive_percent,
        requested_by_user_id=None,  # TODO: Get from auth
    )

    return NegotiationResponse(
        negotiation_id=result.negotiation_id,
        status=NegotiationStatusEnum(result.status.value),
        message=result.message,
        booking_updated=result.booking_updated,
        new_time=result.new_time,
    )


@router.post("/negotiations/respond", response_model=NegotiationResponse)
async def respond_to_negotiation(
    request: RespondToNegotiationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Customer response to a negotiation request.

    If accepted, the booking time is automatically updated.
    """
    negotiation_service = NegotiationService(db)

    result = await negotiation_service.respond_to_negotiation(
        negotiation_id=request.negotiation_id,
        accepted=request.accepted,
        customer_note=request.customer_note,
    )

    return NegotiationResponse(
        negotiation_id=result.negotiation_id,
        status=NegotiationStatusEnum(result.status.value),
        message=result.message,
        booking_updated=result.booking_updated,
        new_time=result.new_time,
    )


@router.get("/negotiations/pending", response_model=PendingNegotiationsResponse)
async def get_pending_negotiations(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all pending negotiation requests.

    For admin dashboard to track outstanding requests.

    Requires: Station Manager role or higher
    """
    negotiation_service = NegotiationService(db)

    negotiations = await negotiation_service.get_pending_negotiations(limit=limit)

    return PendingNegotiationsResponse(
        count=len(negotiations),
        negotiations=[
            NegotiationDetailResponse(
                id=n.id,
                booking_id=n.booking_id,
                customer_email=n.customer_email,
                customer_name=n.customer_name,
                original_date=n.original_date,
                original_time=n.original_time,
                proposed_time=n.proposed_time,
                shift_minutes=n.shift_minutes,
                reason=NegotiationStatusEnum(n.reason.value),
                reason_message=n.reason_message,
                incentive_percent=n.incentive_percent,
                status=NegotiationStatusEnum(n.status.value),
                created_at=n.created_at,
                expires_at=n.expires_at,
                responded_at=n.responded_at,
                response_note=n.response_note,
            )
            for n in negotiations
        ],
    )


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.get("/slots/config", response_model=AllSlotsConfigResponse)
async def get_slot_configurations():
    """
    Get all available time slot configurations.

    Returns slot times and their adjustment limits.
    """
    slot_manager = SlotManagerService()
    configs = slot_manager.get_all_slot_configs()

    return AllSlotsConfigResponse(
        slots=[
            SlotConfigResponse(
                slot_time=c.slot_time,
                slot_name=c.slot_name,
                adjust_earlier_minutes=c.adjust_earlier_minutes,
                adjust_later_minutes=c.adjust_later_minutes,
                is_active=c.is_active,
            )
            for c in configs
        ],
    )


@router.post("/duration/calculate", response_model=EventDurationResponse)
async def calculate_event_duration(
    request: EventDurationRequest,
):
    """
    Calculate event duration based on party size.

    Formula: min(60 + (guests × 3), 120) minutes

    - Minimum: 63 minutes (1 guest)
    - Maximum: 120 minutes (20+ guests)
    """
    slot_manager = SlotManagerService()
    duration = slot_manager.calculate_event_duration(request.guest_count)

    return EventDurationResponse(
        guest_count=request.guest_count,
        duration_minutes=duration,
    )
