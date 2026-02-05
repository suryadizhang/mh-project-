"""
Booking CRUD Endpoints
======================

Handles core booking operations:
- GET / - List bookings with cursor pagination
- GET /{booking_id} - Get single booking details
- POST / - Create new booking
- PUT /{booking_id} - Update booking

File Size: ~350 lines (within 500 line limit)
"""

import asyncio
import logging
import re
from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from datetime import timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, not_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from api.ai.endpoints.services.pricing_service import get_pricing_service
from core.database import get_db
from core.security.roles import role_matches
from db.models.core import Booking, BookingStatus, Customer
from services.encryption_service import SecureDataHandler
from services.google_calendar_service import create_chef_assignment_event
from services.scheduling.slot_manager import SlotManager
from utils.auth import get_current_user
from utils.pagination import paginate_query
from utils.timezone_utils import DEFAULT_TIMEZONE

from .constants import DEFAULT_STATION_ID, DEPOSIT_FIXED_CENTS, PARTY_MINIMUM_CENTS
from .notifications import notify_booking_edit, notify_new_booking
from .schemas import BookingCreate, BookingResponse, BookingUpdate, ErrorResponse

router = APIRouter(tags=["bookings"])
logger = logging.getLogger(__name__)


async def _get_chef_capacity(
    db: AsyncSession,
    event_date: date_type,
    time_slot: time_type | None = None,
    default_capacity: int = 3,
) -> int:
    """
    Get capacity based on available chefs for a given date/time.

    Queries the ops.chef_availability and ops.chef_timeoff tables
    to determine how many chefs can work on the requested date/time.

    Args:
        db: Database session
        event_date: The date to check availability for
        time_slot: Optional specific time slot to check
        default_capacity: Fallback if chef tables don't exist or query fails

    Returns:
        Number of available chefs (capacity)
    """
    try:
        from db.models.ops import (
            Chef,
            ChefAvailability,
            ChefStatus,
            ChefTimeOff,
            DayOfWeek,
            TimeOffStatus,
        )

        # Map Python weekday (0=Monday) to our DayOfWeek enum
        day_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        day_of_week = DayOfWeek(day_names[event_date.weekday()])

        # Base query: active chefs with availability on this day of week
        availability_query = (
            select(ChefAvailability.chef_id)
            .join(Chef, Chef.id == ChefAvailability.chef_id)
            .where(
                and_(
                    Chef.status == ChefStatus.ACTIVE,
                    Chef.is_active.is_(True),
                    ChefAvailability.day_of_week == day_of_week,
                    ChefAvailability.is_available.is_(True),
                )
            )
        )

        # If time_slot specified, filter by time range
        if time_slot:
            availability_query = availability_query.where(
                and_(
                    ChefAvailability.start_time <= time_slot,
                    ChefAvailability.end_time >= time_slot,
                )
            )

        # Get chefs who have approved time off on this date
        timeoff_subquery = select(ChefTimeOff.chef_id).where(
            and_(
                ChefTimeOff.start_date <= event_date,
                ChefTimeOff.end_date >= event_date,
                ChefTimeOff.status == TimeOffStatus.APPROVED,
            )
        )

        # Exclude chefs with approved time off
        final_query = availability_query.where(
            not_(ChefAvailability.chef_id.in_(timeoff_subquery))
        ).distinct()

        result = await db.execute(final_query)
        available_chef_ids = result.scalars().all()

        capacity = len(available_chef_ids)
        logger.debug(f"Chef capacity for {event_date} {time_slot}: {capacity} chefs available")

        # Return at least 1 to allow bookings when no chef data exists
        return capacity if capacity > 0 else default_capacity

    except Exception as e:
        # Tables may not exist yet or query may fail - fallback to default
        logger.warning(f"Chef capacity check failed, using default: {e}")
        return default_capacity


@router.get(
    "/",
    summary="List bookings with cursor pagination",
    description="""
    Retrieve a paginated list of bookings.

    ## Pagination
    Uses cursor-based pagination for O(1) performance.
    - First page: No cursor required
    - Next page: Use `next_cursor` from response
    - Previous page: Use `prev_cursor` from response

    ## Filtering
    - `user_id`: Filter by customer ID
    - `status`: Filter by booking status

    ## Multi-Tenant
    Results are filtered by station based on user role.
    """,
)
async def list_bookings(
    user_id: str | None = Query(None, description="Filter by customer ID"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    List bookings with cursor pagination.

    Uses eager loading to reduce from 51 queries to 1 query.
    """
    # Build base query with eager loading
    query = (
        select(Booking)
        .options(joinedload(Booking.customer))
        .where(Booking.deleted_at.is_(None))
        .order_by(Booking.created_at.desc())
    )

    # Apply role-based filtering
    user_role = current_user.get("role", "")

    # STATION_MANAGER: Can only see bookings for their assigned stations
    if role_matches(user_role, "STATION_MANAGER", "station_manager"):
        station_ids = current_user.get("station_ids", [])
        if station_ids:
            query = query.where(Booking.station_id.in_([UUID(sid) for sid in station_ids]))

    # CHEF: Can only see bookings assigned to themselves
    elif role_matches(user_role, "CHEF", "chef"):
        chef_id = current_user.get("chef_id")
        if chef_id:
            query = query.where(Booking.chef_id == UUID(chef_id))
        else:
            # If no chef_id in token, chef sees nothing (security measure)
            query = query.where(Booking.id.is_(None))

    # Apply user filter
    if user_id:
        query = query.where(Booking.customer_id == UUID(user_id))

    # Apply status filter
    if status_filter:
        try:
            status_enum = BookingStatus(status_filter)
            query = query.where(Booking.status == status_enum)
        except ValueError:
            pass  # Invalid status, skip filter

    # Apply cursor pagination
    result = await paginate_query(
        db=db,
        query=query,
        order_by=Booking.created_at,
        cursor=cursor,
        limit=limit,
        order_direction="desc",
        secondary_order=Booking.id,
    )

    return result


@router.get(
    "/unassigned",
    summary="Get unassigned bookings",
    description="Retrieve all bookings that don't have a chef assigned. For station managers, "
    "only returns unassigned bookings from their stations.",
)
async def list_unassigned_bookings(
    cursor: str | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get all unassigned bookings (chef_id is NULL).

    RBAC:
    - SUPER_ADMIN, ADMIN: See all unassigned bookings
    - STATION_MANAGER: See only unassigned bookings from their stations
    - CUSTOMER_SUPPORT: See all unassigned bookings
    - CHEF: Not allowed (returns empty)
    """
    user_role = current_user.get("role", "")

    # Build query for unassigned bookings (chef_id is NULL)
    query = select(Booking).where(Booking.chef_id.is_(None))

    # RBAC filtering
    if role_matches(user_role, "SUPER_ADMIN", "super_admin"):
        pass  # See all
    elif role_matches(user_role, "ADMIN", "admin"):
        pass  # See all
    elif role_matches(user_role, "CUSTOMER_SUPPORT", "customer_support"):
        pass  # See all
    elif role_matches(user_role, "STATION_MANAGER", "station_manager"):
        station_ids = current_user.get("station_ids", [])
        if station_ids:
            query = query.where(Booking.station_id.in_([UUID(sid) for sid in station_ids]))
        else:
            # No stations assigned, see nothing
            query = query.where(Booking.id.is_(None))
    else:
        # CHEF or other roles - not authorized for this endpoint
        return {"items": [], "next_cursor": None, "has_more": False}

    # Only show confirmed bookings that need assignment
    query = query.where(Booking.status == BookingStatus.CONFIRMED)

    # Order by event date (soonest first - most urgent)
    query = query.order_by(Booking.event_datetime.asc())

    # Apply cursor pagination
    result = await paginate_query(
        db=db,
        query=query,
        order_by=Booking.event_datetime,
        cursor=cursor,
        limit=limit,
        order_direction="asc",
        secondary_order=Booking.id,
    )

    return result


@router.get(
    "/{booking_id}",
    summary="Get booking details",
    description="Retrieve detailed information about a specific booking.",
    responses={
        200: {"description": "Booking details", "model": BookingResponse},
        403: {
            "description": "Not authorized to view this booking",
            "model": ErrorResponse,
        },
        404: {"description": "Booking not found", "model": ErrorResponse},
    },
)
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get single booking details.

    Uses eager loading for customer and payments (1 query instead of 34).
    """
    query = (
        select(Booking)
        .options(
            joinedload(Booking.customer),
            selectinload(Booking.payments),
        )
        .where(
            Booking.id == UUID(booking_id),
            Booking.deleted_at.is_(None),
        )
    )

    result = await db.execute(query)
    booking = result.unique().scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Authorization check
    customer_id_str = str(booking.customer_id)
    current_user_id = current_user.get("id")
    user_role = current_user.get("role", "")

    # Allow admin roles to view any booking
    if user_role not in ("SUPER_ADMIN", "ADMIN", "CUSTOMER_SUPPORT", "STATION_MANAGER"):
        if customer_id_str != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this booking",
            )

    # Calculate payment totals
    total_paid = sum(p.amount_cents for p in booking.payments if p.status == "completed")
    deposit_paid = total_paid >= booking.deposit_due_cents if booking.deposit_due_cents else False

    return {
        "id": str(booking.id),
        "user_id": str(booking.customer_id),
        "date": booking.date.strftime("%Y-%m-%d") if booking.date else None,
        "time": booking.slot.strftime("%H:%M") if booking.slot else None,
        "customer_requested_time": (
            booking.customer_requested_time.strftime("%H:%M")
            if booking.customer_requested_time
            else None
        ),
        "guests": (booking.party_adults or 0) + (booking.party_kids or 0),
        "status": (
            booking.status.value if hasattr(booking.status, "value") else str(booking.status)
        ),
        "total_amount": (booking.total_due_cents / 100.0 if booking.total_due_cents else 0.0),
        "deposit_paid": deposit_paid,
        "balance_due": (
            (booking.total_due_cents - booking.deposit_due_cents) / 100.0
            if booking.total_due_cents and booking.deposit_due_cents
            else 0.0
        ),
        "payment_status": (
            booking.status.value if hasattr(booking.status, "value") else str(booking.status)
        ),
        "menu_items": [],
        "addons": [],
        "location": {
            "address": "TBD",
            "travel_distance": 0.0,
            "travel_fee": 0.0,
        },
        "created_at": (booking.created_at.isoformat() if booking.created_at else None),
    }


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="""
    Create a new hibachi catering booking.

    ## Requirements:
    - Valid authentication token
    - Date must be at least 48 hours in the future
    - Guest count between 1-50
    - Valid US phone number and email

    ## Pricing:
    - Base price: Dynamic from pricing service
    - Deposit required: $100 fixed (due within 2 hours)
    - Party minimum: $550
    """,
)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new booking with validation and notifications."""
    try:
        # Initialize encryption
        try:
            encryption_handler = SecureDataHandler()
        except ValueError as e:
            logger.error(f"Encryption key not configured: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: encryption not available",
            )

        # Parse date and time
        from datetime import date as date_type

        booking_date = date_type.fromisoformat(booking_data.date)
        hour, minute = map(int, booking_data.time.split(":"))
        customer_requested_time = time_type(hour=hour, minute=minute)

        # Option C+E Hybrid: Snap customer's requested time to nearest slot
        # Store both for: slot = chef scheduling, customer_requested_time = display
        slot_manager = SlotManager()
        _, booking_slot = slot_manager.snap_to_nearest_slot(customer_requested_time)

        # Validate 48-hour advance booking (use customer's requested time for UX)
        now = datetime.now(timezone.utc)
        booking_datetime = datetime.combine(
            booking_date, customer_requested_time, tzinfo=timezone.utc
        )
        if booking_datetime < now + timedelta(hours=48):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking date must be at least 48 hours in the future",
            )

        # Validate business hours (use customer's requested time)
        if customer_requested_time.hour < 11 or customer_requested_time.hour >= 22:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking time must be between 11:00 and 22:00",
            )

        # Check slot availability with multi-chef capacity
        # Count existing bookings for this slot
        existing_count_result = await db.execute(
            select(func.count(Booking.id)).where(
                and_(
                    Booking.date == booking_date,
                    Booking.slot == booking_slot,
                    Booking.status.notin_([BookingStatus.CANCELLED]),
                    Booking.deleted_at.is_(None),
                )
            )
        )
        existing_booking_count = existing_count_result.scalar() or 0

        # Get chef capacity for this date/slot
        chef_capacity = await _get_chef_capacity(db, booking_date, booking_slot)
        logger.debug(
            f"Slot availability: {existing_booking_count}/{chef_capacity} bookings for {booking_date} {booking_slot}"
        )

        if existing_booking_count >= chef_capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Time slot {booking_data.time} on {booking_data.date} is fully booked (capacity: {chef_capacity})",
            )

        # Parse customer name
        name_parts = booking_data.customer_name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else "Guest"
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Encrypt PII
        email_encrypted = encryption_handler.encrypt_email(booking_data.customer_email)
        phone_encrypted = encryption_handler.encrypt_phone(booking_data.customer_phone)
        address_encrypted = encryption_handler.encrypt_email(booking_data.location_address)

        # Find or create customer
        customer = await _find_or_create_customer(
            db,
            encryption_handler,
            email_encrypted,
            phone_encrypted,
            first_name,
            last_name,
            now,
        )

        # Calculate pricing
        zone = _extract_zone(booking_data.location_address)
        pricing_service = get_pricing_service()
        adult_price_cents = int(pricing_service.get_adult_price() * 100)

        total_cents = max(
            booking_data.guests * adult_price_cents,
            PARTY_MINIMUM_CENTS,
        )

        # Create booking
        booking_id = uuid4()
        customer_deposit_deadline = now + timedelta(hours=2)

        booking = Booking(
            id=booking_id,
            customer_id=customer.id,
            station_id=UUID(DEFAULT_STATION_ID),
            date=booking_date,
            slot=booking_slot,
            customer_requested_time=customer_requested_time,  # Option C+E: Store original time for display
            address_encrypted=address_encrypted,
            zone=zone,
            party_adults=booking_data.guests,
            party_kids=0,
            deposit_due_cents=DEPOSIT_FIXED_CENTS,
            total_due_cents=total_cents,
            status=BookingStatus.PENDING,
            source="web",
            sms_consent=True,
            sms_consent_timestamp=now,
            customer_deposit_deadline=customer_deposit_deadline,
            internal_deadline=now + timedelta(hours=24),
            deposit_deadline=customer_deposit_deadline,
            special_requests=booking_data.special_requests,
        )

        db.add(booking)

        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Race condition or duplicate booking: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot was just booked. Please select a different time.",
            )

        # Send notification asynchronously
        asyncio.create_task(
            notify_new_booking(
                customer_name=booking_data.customer_name,
                customer_phone=booking_data.customer_phone,
                event_date=booking_data.date,
                event_time=booking_data.time,
                guest_count=booking_data.guests,
                location=booking_data.location_address,
                booking_id=str(booking_id),
                special_requests=booking_data.special_requests,
            )
        )

        logger.info(f"✅ Booking created: {booking_id} for {booking_data.customer_name}")

        return {
            "id": str(booking_id),
            "user_id": current_user.get("id", str(customer.id)),
            "date": booking_data.date,
            "time": booking_data.time,
            "guests": booking_data.guests,
            "status": "pending",
            "total_amount": total_cents / 100,
            "deposit_amount": DEPOSIT_FIXED_CENTS / 100,
            "deposit_paid": False,
            "balance_due": total_cents / 100,
            "payment_status": "awaiting_deposit",
            "customer_name": booking_data.customer_name,
            "customer_email": booking_data.customer_email,
            "location_address": booking_data.location_address,
            "deposit_deadline": customer_deposit_deadline.isoformat(),
            "created_at": now.isoformat(),
            "customer_requested_time": customer_requested_time.strftime("%H:%M"),
            "message": "Booking created successfully. Please pay deposit within 2 hours to confirm.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Failed to create booking: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}",
        )


@router.put(
    "/{booking_id}",
    summary="Update an existing booking",
    description="""
    Update booking details such as date, time, guest count, location, or chef assignment.

    ## Update Rules:
    - Only pending or confirmed bookings can be updated
    - Date/time changes must be at least 72 hours before event
    - Pricing is recalculated if guest count changes

    ## Chef Assignment:
    - SUPER_ADMIN, ADMIN, or STATION_MANAGER can assign/unassign chefs
    - Set chef_id to a valid chef UUID to assign
    - Set chef_id to null to unassign the chef
    """,
)
async def update_booking(
    booking_id: str,
    booking_data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Update an existing booking."""
    # Validate booking_id is a valid UUID
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )

    # Fetch the booking from database
    result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.customer))
        .where(
            Booking.id == booking_uuid,
            Booking.deleted_at.is_(None),
        )
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    # Check if booking status allows updates
    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update booking with status: {booking.status.value}",
        )

    # Build change list for notification
    changes = []

    # Apply updates to booking
    update_data = booking_data.model_dump(exclude_none=True)

    if "date" in update_data:
        booking.date = datetime.strptime(update_data["date"], "%Y-%m-%d").date()
        changes.append(f"Date changed to {update_data['date']}")

    if "time" in update_data:
        time_parts = update_data["time"].split(":")
        customer_requested_time = time_type(int(time_parts[0]), int(time_parts[1]))

        # Option C+E: Store original time, snap to slot for scheduling
        booking.customer_requested_time = customer_requested_time
        slot_num, slot_time = SlotManager.snap_to_nearest_slot(customer_requested_time)
        booking.slot = slot_time

        changes.append(
            f"Time changed to {update_data['time']} (slot: {slot_time.strftime('%H:%M')})"
        )

    if "guests" in update_data:
        booking.party_adults = update_data["guests"]  # Fix: Booking uses party_adults not guests
        changes.append(f"Guest count changed to {update_data['guests']}")

    if "location_address" in update_data:
        booking.venue_address = update_data["location_address"]
        changes.append("Location changed")

    if "special_requests" in update_data:
        booking.special_requests = update_data["special_requests"]
        changes.append("Special requests updated")

    if "status" in update_data:
        try:
            new_status = BookingStatus(update_data["status"])
            booking.status = new_status
            changes.append(f"Status changed to {new_status.value}")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {update_data['status']}",
            )

    # Handle chef assignment
    if "chef_id" in update_data:
        chef_id = update_data["chef_id"]
        old_chef_id = booking.chef_id

        if chef_id is None:
            # Unassign chef
            booking.chef_id = None
            if old_chef_id:
                changes.append("Chef unassigned from booking")
                logger.info(f"🍳 Chef {old_chef_id} unassigned from booking {booking_id}")
        else:
            # Assign new chef
            booking.chef_id = chef_id
            if old_chef_id and old_chef_id != chef_id:
                changes.append(f"Chef changed from {old_chef_id} to {chef_id}")
                logger.info(
                    f"🍳 Chef changed from {old_chef_id} to {chef_id} for booking {booking_id}"
                )
            else:
                changes.append(f"Chef {chef_id} assigned to booking")
                logger.info(f"🍳 Chef {chef_id} assigned to booking {booking_id}")

            # Trigger Google Calendar sync for chef (async background task)
            asyncio.create_task(
                create_chef_assignment_event(db=db, booking=booking, chef_id=chef_id)
            )

    booking.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(booking)
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig) if e.orig else str(e)
        if "ix_core_bookings_chef_slot_unique" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chef is already assigned to another booking at this date/time slot",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking",
        )

    # Send edit notification if there were changes
    if changes:
        customer_name = "Customer"
        customer_phone = "+10000000000"

        if booking.customer:
            customer_name = f"{booking.customer.first_name} {booking.customer.last_name}"
            # Decrypt phone if needed

        asyncio.create_task(
            notify_booking_edit(
                customer_name=customer_name,
                customer_phone=customer_phone,
                booking_id=booking_id,
                changes=", ".join(changes),
                event_date=str(booking.date),
                event_time=str(booking.slot),
            )
        )
        logger.info(f"📧 Edit notification queued for booking {booking_id}")

    # Build response
    response = {
        "id": str(booking.id),
        "message": "Booking updated successfully",
        "date": str(booking.date),
        "time": str(booking.slot),
        "guests": (booking.party_adults or 0) + (booking.party_kids or 0) + (booking.party_toddlers or 0),
        "status": booking.status.value,
        "chef_id": str(booking.chef_id) if booking.chef_id else None,
        "customer_requested_time": (
            booking.customer_requested_time.strftime("%H:%M")
            if booking.customer_requested_time
            else None
        ),
        "changes": changes,
    }

    return response


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def _find_or_create_customer(
    db: AsyncSession,
    encryption_handler: SecureDataHandler,
    email_encrypted: str,
    phone_encrypted: str,
    first_name: str,
    last_name: str,
    now: datetime,
) -> Customer:
    """Find existing customer or create new one."""
    result = await db.execute(
        select(Customer).where(
            Customer.email_encrypted == email_encrypted,
            Customer.deleted_at.is_(None),
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        customer = Customer(
            id=uuid4(),
            station_id=UUID(DEFAULT_STATION_ID),
            first_name=first_name,
            last_name=last_name,
            email_encrypted=email_encrypted,
            phone_encrypted=phone_encrypted,
            consent_sms=True,
            consent_email=True,
            consent_updated_at=now,
            timezone=DEFAULT_TIMEZONE,  # Pacific Time (Fremont, CA)
        )
        db.add(customer)
        await db.flush()
        logger.info(f"✅ Created new customer: {customer.id}")

    return customer


def _extract_zone(address: str) -> str:
    """Extract zone (ZIP code) from address."""
    zip_match = re.search(r"\b(\d{5})\b", address)
    return zip_match.group(1) if zip_match else "DEFAULT"
