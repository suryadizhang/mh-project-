"""
Booking Calendar Endpoints (Admin)
==================================

Admin calendar views for booking management:
- GET /admin/weekly - Weekly calendar view
- GET /admin/monthly - Monthly calendar view
- PATCH /admin/{booking_id} - Reschedule booking (drag-drop)

File Size: ~250 lines (within 500 line limit)
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.database import get_db
from core.security import decrypt_pii
from db.models.core import Booking
from utils.auth import get_current_user

from .schemas import ErrorResponse

router = APIRouter(tags=["bookings"])
logger = logging.getLogger(__name__)


@router.get(
    "/admin/weekly",
    summary="Get bookings for weekly calendar view (ADMIN)",
    description="""
    Retrieve all bookings within a specific week for calendar display.

    ## Query Parameters:
    - **date_from**: Start date (YYYY-MM-DD)
    - **date_to**: End date (YYYY-MM-DD)
    - **status**: Optional status filter

    ## Performance:
    Optimized with eager loading to prevent N+1 queries.
    """,
    responses={
        200: {"description": "Weekly bookings retrieved successfully"},
        400: {"description": "Invalid date range", "model": ErrorResponse},
    },
)
async def get_weekly_bookings(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get all bookings for a week (admin calendar view)."""

    # Parse dates
    try:
        start_date = datetime.fromisoformat(date_from)
        end_date = datetime.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Build query with eager loading
    query = (
        select(Booking)
        .options(joinedload(Booking.customer))
        .where(
            and_(
                Booking.date >= start_date,
                Booking.date <= end_date,
                Booking.deleted_at.is_(None),
            )
        )
        .order_by(Booking.date, Booking.slot)
    )

    # Apply station filtering (multi-tenant isolation)
    station_id = current_user.get("station_id")
    if station_id:
        query = query.where(Booking.station_id == UUID(station_id))

    # Apply status filter if provided
    if status_filter:
        query = query.where(Booking.status == status_filter)

    # Execute query
    result = await db.execute(query)
    bookings = result.scalars().unique().all()

    # Convert to response format
    bookings_data = []
    for booking in bookings:
        # Decrypt customer PII
        customer_email = (
            decrypt_pii(booking.customer.email_encrypted)
            if booking.customer and booking.customer.email_encrypted
            else ""
        )
        customer_name = (
            decrypt_pii(booking.customer.name_encrypted)
            if booking.customer and booking.customer.name_encrypted
            else ""
        )
        customer_phone = (
            decrypt_pii(booking.customer.phone_encrypted)
            if booking.customer and booking.customer.phone_encrypted
            else ""
        )
        special_requests = (
            decrypt_pii(booking.special_requests_encrypted)
            if booking.special_requests_encrypted
            else None
        )

        bookings_data.append(
            {
                "booking_id": str(booking.id),
                "customer": {
                    "customer_id": str(booking.customer_id),
                    "email": customer_email,
                    "name": customer_name,
                    "phone": customer_phone,
                },
                "date": booking.date.isoformat() if booking.date else None,
                "slot": booking.slot.strftime("%H:%M") if booking.slot else None,
                "total_guests": (booking.party_adults or 0) + (booking.party_kids or 0),
                "status": (
                    booking.status.value
                    if hasattr(booking.status, "value")
                    else str(booking.status)
                ),
                "total_due_cents": booking.total_due_cents,
                "balance_due_cents": (
                    (booking.total_due_cents - booking.deposit_due_cents)
                    if booking.total_due_cents and booking.deposit_due_cents
                    else 0
                ),
                "special_requests": special_requests,
                "source": booking.source,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "updated_at": booking.updated_at.isoformat() if booking.updated_at else None,
            }
        )

    return {
        "success": True,
        "data": bookings_data,
        "total_count": len(bookings_data),
    }


@router.get(
    "/admin/monthly",
    summary="Get bookings for monthly calendar view (ADMIN)",
    description="Same as weekly view but for monthly date range.",
    responses={
        200: {"description": "Monthly bookings retrieved successfully"},
        400: {"description": "Invalid date range", "model": ErrorResponse},
    },
)
async def get_monthly_bookings(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get all bookings for a month (admin calendar view)."""
    # Reuse weekly implementation (same logic, just different date range)
    return await get_weekly_bookings(date_from, date_to, status_filter, db, current_user)


@router.patch(
    "/admin/{booking_id}",
    summary="Reschedule booking date/time (ADMIN)",
    description="""
    Update a booking's date and time slot (for drag-drop calendar rescheduling).

    ## Validation:
    - Cannot reschedule to past dates
    - Cannot reschedule cancelled or completed bookings
    """,
    responses={
        200: {"description": "Booking rescheduled successfully"},
        400: {"description": "Invalid update data", "model": ErrorResponse},
        404: {"description": "Booking not found", "model": ErrorResponse},
    },
)
async def reschedule_booking(
    booking_id: str,
    update_data: dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Update booking date and time (admin calendar drag-drop)."""

    # Validate input
    new_date = update_data.get("date")
    new_slot = update_data.get("slot")

    if not new_date or not new_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'date' and 'slot' are required",
        )

    # Validate date format
    try:
        parsed_date = datetime.fromisoformat(new_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Validate slot format (HH:MM)
    if not re.match(r"^\d{2}:\d{2}$", new_slot):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time slot format. Use HH:MM (e.g., 18:00)",
        )

    # Check if date is in the past
    if parsed_date.date() < datetime.now(timezone.utc).date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reschedule to past dates",
        )

    # Fetch booking
    query = select(Booking).where(
        Booking.id == UUID(booking_id),
        Booking.deleted_at.is_(None),
    )

    # Apply station filtering (multi-tenant isolation)
    station_id = current_user.get("station_id")
    if station_id:
        query = query.where(Booking.station_id == UUID(station_id))

    result = await db.execute(query)
    booking = result.scalars().first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Validate booking status
    status_value = booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    if status_value in ("cancelled", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule {status_value} bookings",
        )

    # Update booking
    booking.date = parsed_date.date()
    booking.slot = datetime.strptime(new_slot, "%H:%M").time()
    booking.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"📅 Booking {booking_id} rescheduled to {new_date} {new_slot} "
        f"by user {current_user.get('id')}"
    )

    return {
        "success": True,
        "data": {
            "booking_id": str(booking.id),
            "date": booking.date.isoformat() if booking.date else None,
            "slot": booking.slot.strftime("%H:%M") if booking.slot else None,
            "status": status_value,
            "message": "Booking rescheduled successfully",
        },
    }
