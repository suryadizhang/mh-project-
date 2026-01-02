"""
Chef Portal API Endpoints

Provides self-service endpoints for chefs to manage their own:
- Profile viewing
- Availability (weekly schedule)
- Time-off requests

Authorization Rules:
- Chefs can ONLY manage their OWN availability and time-off
- Station Managers can manage chefs in their station and approve time-off
- Super Admins have full access

User-Chef Linkage:
- Uses email matching: Chef.email == current_user["email"]
- Future: Add user_id to Chef model for direct FK relationship

See: 21-BUSINESS_MODEL.instructions.md for chef requirements
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.ops import (
    Chef,
    ChefAvailability,
    ChefTimeOff,
    ChefStatus,
    DayOfWeek,
    TimeOffStatus,
)
from schemas.chef_portal import (
    # Chef Profile
    ChefProfileResponse,
    # Availability
    ChefAvailabilityCreate,
    ChefAvailabilityUpdate,
    ChefAvailabilityResponse,
    ChefWeeklyAvailabilityResponse,
    BulkAvailabilityUpdate,
    # Time Off
    TimeOffRequestCreate,
    TimeOffRequestResponse,
    TimeOffApprovalRequest,
    # Station Manager views
    StationChefSummary,
    StationChefListResponse,
)
from utils.auth import require_role, UserRole


router = APIRouter(prefix="/chef-portal", tags=["Chef Portal"])


# ============================================================================
# Helper Functions - User-Chef Linkage
# ============================================================================


async def get_chef_by_user_email(
    db: AsyncSession,
    user_email: str,
) -> Chef:
    """
    Get Chef record by matching email with current user's email.

    This is the linkage strategy since Chef model has no user_id field.
    Chef.email must match the authenticated user's email.

    Args:
        db: Database session
        user_email: Email from current authenticated user

    Returns:
        Chef record

    Raises:
        HTTPException 404 if no chef profile found for this user
    """
    result = await db.execute(
        select(Chef).where(
            and_(
                Chef.email == user_email,
                Chef.is_active == True,
            )
        )
    )
    chef = result.scalar_one_or_none()

    if not chef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chef profile found for this user. Contact your station manager.",
        )

    return chef


async def require_chef_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHEF])),
) -> Chef:
    """
    Dependency that validates CHEF role and retrieves their Chef profile.

    Returns the Chef record for the authenticated user.
    """
    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User email not found in token",
        )

    return await get_chef_by_user_email(db, user_email)


async def require_station_manager_or_super_admin(
    current_user: dict = Depends(require_role([UserRole.STATION_MANAGER, UserRole.SUPER_ADMIN])),
) -> dict:
    """
    Dependency that requires Station Manager or Super Admin role.

    Station Managers can manage chefs and approve time-off.
    Super Admins have full access.
    """
    return current_user


# ============================================================================
# Chef Profile Endpoints
# ============================================================================


@router.get(
    "/me",
    response_model=ChefProfileResponse,
    summary="Get My Chef Profile",
    description="Get the authenticated chef's profile information",
)
async def get_my_chef_profile(
    chef: Chef = Depends(require_chef_profile),
):
    """
    Get the current chef's profile.

    Chefs can only view their own profile.

    Returns:
        Chef profile with basic information
    """
    return ChefProfileResponse(
        id=chef.id,
        first_name=chef.first_name,
        last_name=chef.last_name,
        email=chef.email,
        phone=chef.phone,
        specialty=chef.specialty,
        status=chef.status.value if chef.status else "active",
        rating=float(chef.rating) if chef.rating else None,
        is_active=chef.is_active,
    )


# ============================================================================
# Availability Management Endpoints
# ============================================================================


@router.get(
    "/me/availability",
    response_model=ChefWeeklyAvailabilityResponse,
    summary="Get My Weekly Availability",
    description="Get the chef's complete weekly availability schedule",
)
async def get_my_availability(
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Get all availability slots for the current chef.

    Returns weekly schedule organized by day of week.
    """
    result = await db.execute(
        select(ChefAvailability)
        .where(ChefAvailability.chef_id == chef.id)
        .order_by(ChefAvailability.day_of_week, ChefAvailability.start_time)
    )
    slots = result.scalars().all()

    # Group by day of week
    availability_by_day: dict[str, list[ChefAvailabilityResponse]] = {
        day.value: [] for day in DayOfWeek
    }

    for slot in slots:
        slot_response = ChefAvailabilityResponse(
            id=slot.id,
            chef_id=slot.chef_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            created_at=slot.created_at,
        )
        availability_by_day[slot.day_of_week.value].append(slot_response)

    return ChefWeeklyAvailabilityResponse(
        chef_id=chef.id,
        availability=availability_by_day,
        total_slots=len(slots),
    )


@router.post(
    "/me/availability",
    response_model=ChefAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Availability Slot",
    description="Add a single availability slot to the chef's schedule",
)
async def add_availability_slot(
    slot_data: ChefAvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Add a new availability slot.

    Chef can only add slots to their own schedule.
    Validates that start_time < end_time.
    """
    # Check for duplicate/overlapping slot
    existing = await db.execute(
        select(ChefAvailability).where(
            and_(
                ChefAvailability.chef_id == chef.id,
                ChefAvailability.day_of_week == slot_data.day_of_week,
                ChefAvailability.start_time == slot_data.start_time,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Availability slot already exists for {slot_data.day_of_week.value} at {slot_data.start_time}",
        )

    # Create new slot
    new_slot = ChefAvailability(
        chef_id=chef.id,
        day_of_week=slot_data.day_of_week,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        is_available=slot_data.is_available,
    )

    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)

    return ChefAvailabilityResponse(
        id=new_slot.id,
        chef_id=new_slot.chef_id,
        day_of_week=new_slot.day_of_week,
        start_time=new_slot.start_time,
        end_time=new_slot.end_time,
        is_available=new_slot.is_available,
        created_at=new_slot.created_at,
    )


@router.put(
    "/me/availability/{slot_id}",
    response_model=ChefAvailabilityResponse,
    summary="Update Availability Slot",
    description="Update an existing availability slot",
)
async def update_availability_slot(
    slot_id: UUID,
    slot_data: ChefAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Update an existing availability slot.

    Chef can only update their own slots.
    """
    result = await db.execute(
        select(ChefAvailability).where(
            and_(
                ChefAvailability.id == slot_id,
                ChefAvailability.chef_id == chef.id,  # Ensure chef owns this slot
            )
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found or you don't have permission to modify it",
        )

    # Update fields if provided
    if slot_data.start_time is not None:
        slot.start_time = slot_data.start_time
    if slot_data.end_time is not None:
        slot.end_time = slot_data.end_time
    if slot_data.is_available is not None:
        slot.is_available = slot_data.is_available

    await db.commit()
    await db.refresh(slot)

    return ChefAvailabilityResponse(
        id=slot.id,
        chef_id=slot.chef_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        is_available=slot.is_available,
        created_at=slot.created_at,
    )


@router.delete(
    "/me/availability/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Availability Slot",
    description="Remove an availability slot from the chef's schedule",
)
async def delete_availability_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Delete an availability slot.

    Chef can only delete their own slots.
    """
    result = await db.execute(
        select(ChefAvailability).where(
            and_(
                ChefAvailability.id == slot_id,
                ChefAvailability.chef_id == chef.id,  # Ensure chef owns this slot
            )
        )
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found or you don't have permission to delete it",
        )

    await db.delete(slot)
    await db.commit()


@router.put(
    "/me/availability/bulk",
    response_model=ChefWeeklyAvailabilityResponse,
    summary="Bulk Update Weekly Availability",
    description="Replace all availability slots with new schedule (max 21 slots)",
)
async def bulk_update_availability(
    bulk_data: BulkAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Bulk update all availability slots.

    This replaces ALL existing slots with the provided list.
    Useful for setting up a complete weekly schedule at once.
    Maximum 21 slots (3 per day for 7 days).
    """
    # Delete all existing slots for this chef
    await db.execute(delete(ChefAvailability).where(ChefAvailability.chef_id == chef.id))

    # Create new slots
    new_slots = []
    for slot_data in bulk_data.slots:
        new_slot = ChefAvailability(
            chef_id=chef.id,
            day_of_week=slot_data.day_of_week,
            start_time=slot_data.start_time,
            end_time=slot_data.end_time,
            is_available=slot_data.is_available,
        )
        db.add(new_slot)
        new_slots.append(new_slot)

    await db.commit()

    # Refresh and build response
    availability_by_day: dict[str, list[ChefAvailabilityResponse]] = {
        day.value: [] for day in DayOfWeek
    }

    for slot in new_slots:
        await db.refresh(slot)
        slot_response = ChefAvailabilityResponse(
            id=slot.id,
            chef_id=slot.chef_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            created_at=slot.created_at,
        )
        availability_by_day[slot.day_of_week.value].append(slot_response)

    return ChefWeeklyAvailabilityResponse(
        chef_id=chef.id,
        availability=availability_by_day,
        total_slots=len(new_slots),
    )


# ============================================================================
# Time Off Request Endpoints
# ============================================================================


@router.get(
    "/me/timeoff",
    response_model=list[TimeOffRequestResponse],
    summary="Get My Time Off Requests",
    description="Get all time-off requests for the authenticated chef",
)
async def get_my_timeoff_requests(
    status_filter: Optional[TimeOffStatus] = Query(
        None,
        description="Filter by status (pending, approved, denied, cancelled)",
    ),
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Get all time-off requests for the current chef.

    Optional filter by status.
    Ordered by request date (most recent first).
    """
    query = select(ChefTimeOff).where(ChefTimeOff.chef_id == chef.id)

    if status_filter:
        query = query.where(ChefTimeOff.status == status_filter)

    query = query.order_by(ChefTimeOff.requested_at.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    return [
        TimeOffRequestResponse(
            id=req.id,
            chef_id=req.chef_id,
            start_date=req.start_date,
            end_date=req.end_date,
            type=req.type,
            status=req.status,
            reason=req.reason,
            requested_at=req.requested_at,
            processed_at=req.processed_at,
            approved_by=req.approved_by,
            manager_notes=req.manager_notes if hasattr(req, "manager_notes") else None,
        )
        for req in requests
    ]


@router.post(
    "/me/timeoff",
    response_model=TimeOffRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Time Off Request",
    description="Submit a new time-off request for approval",
)
async def submit_timeoff_request(
    request_data: TimeOffRequestCreate,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Submit a new time-off request.

    Requests start in PENDING status and require station manager approval.
    Validates that end_date >= start_date.
    """
    # Check for overlapping approved/pending time-off
    existing = await db.execute(
        select(ChefTimeOff).where(
            and_(
                ChefTimeOff.chef_id == chef.id,
                ChefTimeOff.status.in_([TimeOffStatus.PENDING, TimeOffStatus.APPROVED]),
                or_(
                    # New request overlaps with existing
                    and_(
                        ChefTimeOff.start_date <= request_data.end_date,
                        ChefTimeOff.end_date >= request_data.start_date,
                    )
                ),
            )
        )
    )
    overlapping = existing.scalar_one_or_none()

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a {overlapping.status.value} time-off request that overlaps with these dates",
        )

    # Create new request
    new_request = ChefTimeOff(
        chef_id=chef.id,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        type=request_data.type,
        status=TimeOffStatus.PENDING,
        reason=request_data.reason,
        requested_at=datetime.utcnow(),
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return TimeOffRequestResponse(
        id=new_request.id,
        chef_id=new_request.chef_id,
        start_date=new_request.start_date,
        end_date=new_request.end_date,
        type=new_request.type,
        status=new_request.status,
        reason=new_request.reason,
        requested_at=new_request.requested_at,
        processed_at=new_request.processed_at,
        approved_by=new_request.approved_by,
        manager_notes=None,
    )


@router.delete(
    "/me/timeoff/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel Time Off Request",
    description="Cancel a pending time-off request",
)
async def cancel_timeoff_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    chef: Chef = Depends(require_chef_profile),
):
    """
    Cancel a pending time-off request.

    Only PENDING requests can be cancelled by the chef.
    Approved/denied requests cannot be cancelled.
    """
    result = await db.execute(
        select(ChefTimeOff).where(
            and_(
                ChefTimeOff.id == request_id,
                ChefTimeOff.chef_id == chef.id,  # Ensure chef owns this request
            )
        )
    )
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time-off request not found",
        )

    if request.status != TimeOffStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a {request.status.value} request. Only pending requests can be cancelled.",
        )

    # Update to cancelled instead of deleting (for audit trail)
    request.status = TimeOffStatus.CANCELLED
    request.processed_at = datetime.utcnow()

    await db.commit()


# ============================================================================
# Station Manager Endpoints - Manage Chefs & Approve Time Off
# ============================================================================


@router.get(
    "/station/chefs",
    response_model=StationChefListResponse,
    summary="List Chefs (Station Manager)",
    description="Get all chefs visible to station manager",
)
async def list_station_chefs(
    status_filter: Optional[ChefStatus] = Query(
        None,
        description="Filter by chef status",
    ),
    is_active: Optional[bool] = Query(
        None,
        description="Filter by active status",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    List all chefs for the station manager.

    NOTE: Since Chef model currently lacks station_id, this returns ALL active chefs.
    Future: Filter by station_id when Chef-Station relationship is added.

    Station Managers and Super Admins can view this list.
    """
    query = select(Chef)

    if status_filter:
        query = query.where(Chef.status == status_filter)

    if is_active is not None:
        query = query.where(Chef.is_active == is_active)
    else:
        # Default to active chefs only
        query = query.where(Chef.is_active == True)

    query = query.order_by(Chef.last_name, Chef.first_name)

    result = await db.execute(query)
    chefs = result.scalars().all()

    chef_summaries = []
    for chef in chefs:
        # Get pending time-off count for each chef
        pending_result = await db.execute(
            select(ChefTimeOff).where(
                and_(
                    ChefTimeOff.chef_id == chef.id,
                    ChefTimeOff.status == TimeOffStatus.PENDING,
                )
            )
        )
        pending_count = len(pending_result.scalars().all())

        chef_summaries.append(
            StationChefSummary(
                id=chef.id,
                first_name=chef.first_name,
                last_name=chef.last_name,
                email=chef.email,
                phone=chef.phone,
                status=chef.status.value if chef.status else "active",
                is_active=chef.is_active,
                rating=float(chef.rating) if chef.rating else None,
                pending_timeoff_requests=pending_count,
            )
        )

    return StationChefListResponse(
        chefs=chef_summaries,
        total=len(chef_summaries),
    )


@router.get(
    "/station/chefs/{chef_id}/availability",
    response_model=ChefWeeklyAvailabilityResponse,
    summary="View Chef Availability (Station Manager)",
    description="View a chef's availability schedule",
)
async def get_chef_availability(
    chef_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    View a specific chef's availability.

    Station Managers can view (but not modify) chef availability.
    """
    # Verify chef exists
    chef_result = await db.execute(select(Chef).where(Chef.id == chef_id))
    chef = chef_result.scalar_one_or_none()

    if not chef:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chef not found",
        )

    result = await db.execute(
        select(ChefAvailability)
        .where(ChefAvailability.chef_id == chef_id)
        .order_by(ChefAvailability.day_of_week, ChefAvailability.start_time)
    )
    slots = result.scalars().all()

    # Group by day of week
    availability_by_day: dict[str, list[ChefAvailabilityResponse]] = {
        day.value: [] for day in DayOfWeek
    }

    for slot in slots:
        slot_response = ChefAvailabilityResponse(
            id=slot.id,
            chef_id=slot.chef_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            created_at=slot.created_at,
        )
        availability_by_day[slot.day_of_week.value].append(slot_response)

    return ChefWeeklyAvailabilityResponse(
        chef_id=chef_id,
        availability=availability_by_day,
        total_slots=len(slots),
    )


@router.get(
    "/station/timeoff/pending",
    response_model=list[TimeOffRequestResponse],
    summary="List Pending Time Off (Station Manager)",
    description="Get all pending time-off requests for approval",
)
async def list_pending_timeoff(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    List all pending time-off requests across all chefs.

    Station Managers use this to review and approve/deny requests.

    NOTE: Since Chef model lacks station_id, this returns ALL pending requests.
    Future: Filter by station when relationship is added.
    """
    result = await db.execute(
        select(ChefTimeOff)
        .where(ChefTimeOff.status == TimeOffStatus.PENDING)
        .order_by(ChefTimeOff.requested_at.asc())  # Oldest first
    )
    requests = result.scalars().all()

    # Fetch chef info for each request
    response_list = []
    for req in requests:
        chef_result = await db.execute(select(Chef).where(Chef.id == req.chef_id))
        chef = chef_result.scalar_one_or_none()
        chef_name = f"{chef.first_name} {chef.last_name}" if chef else "Unknown"

        response_list.append(
            TimeOffRequestResponse(
                id=req.id,
                chef_id=req.chef_id,
                chef_name=chef_name,
                start_date=req.start_date,
                end_date=req.end_date,
                type=req.type,
                status=req.status,
                reason=req.reason,
                requested_at=req.requested_at,
                processed_at=req.processed_at,
                approved_by=req.approved_by,
                manager_notes=req.manager_notes if hasattr(req, "manager_notes") else None,
            )
        )

    return response_list


@router.post(
    "/station/timeoff/{request_id}/approve",
    response_model=TimeOffRequestResponse,
    summary="Approve/Deny Time Off (Station Manager)",
    description="Approve or deny a pending time-off request",
)
async def process_timeoff_request(
    request_id: UUID,
    approval: TimeOffApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Approve or deny a time-off request.

    Only Station Managers and Super Admins can process requests.
    Only PENDING requests can be processed.
    """
    result = await db.execute(select(ChefTimeOff).where(ChefTimeOff.id == request_id))
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time-off request not found",
        )

    if request.status != TimeOffStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process a {request.status.value} request. Only pending requests can be approved/denied.",
        )

    # Validate status is only approved or denied
    if approval.status not in [TimeOffStatus.APPROVED, TimeOffStatus.DENIED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'approved' or 'denied'",
        )

    # Update request
    request.status = approval.status
    request.processed_at = datetime.utcnow()
    request.approved_by = current_user.get("id") or current_user.get("user_id")

    # Store manager notes if provided
    if approval.notes and hasattr(request, "manager_notes"):
        request.manager_notes = approval.notes

    await db.commit()
    await db.refresh(request)

    # Get chef name
    chef_result = await db.execute(select(Chef).where(Chef.id == request.chef_id))
    chef = chef_result.scalar_one_or_none()
    chef_name = f"{chef.first_name} {chef.last_name}" if chef else "Unknown"

    return TimeOffRequestResponse(
        id=request.id,
        chef_id=request.chef_id,
        chef_name=chef_name,
        start_date=request.start_date,
        end_date=request.end_date,
        type=request.type,
        status=request.status,
        reason=request.reason,
        requested_at=request.requested_at,
        processed_at=request.processed_at,
        approved_by=request.approved_by,
        manager_notes=request.manager_notes if hasattr(request, "manager_notes") else None,
    )
