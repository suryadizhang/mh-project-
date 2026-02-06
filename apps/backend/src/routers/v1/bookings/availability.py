"""
Booking Availability Endpoints.

This module handles public-facing availability checking:
- GET /booked-dates - List of dates with bookings
- GET /availability - Check if a specific date is available
- GET /available-times - Get time slots for a specific date

All endpoints are publicly accessible (optional authentication).

UPDATED: Now integrates with Smart Scheduling System:
- Uses AvailabilityEngine for dynamic chef-based availability
- Uses SlotManager for time slot definitions with adjustment ranges
- Returns real chef count, not hardcoded max_per_slot=1
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.core import Booking

# Smart Scheduling Integration
from services.scheduling.availability_engine import AvailabilityEngine
from services.scheduling.slot_manager import DEFAULT_SLOTS, SlotManager
from utils.auth import get_optional_user

router = APIRouter(tags=["bookings"])
logger = logging.getLogger(__name__)


@router.get(
    "/booked-dates",
    summary="Get all booked dates",
    description="""
    Retrieve a list of all dates that have bookings.
    Useful for calendar displays and availability checking.

    ## Response:
    Returns array of dates in YYYY-MM-DD format that have bookings.

    ## Authentication:
    Optional - public endpoint for availability checking.
    """,
)
async def get_booked_dates(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get all dates that have bookings."""
    try:
        # Build query to get distinct dates
        query = select(func.distinct(Booking.date)).where(
            Booking.status.in_(["pending", "confirmed", "completed"]),
            Booking.deleted_at.is_(None),
        )

        # Apply station filtering if user is authenticated
        if current_user and current_user.get("station_id"):
            query = query.where(Booking.station_id == UUID(current_user["station_id"]))

        result = await db.execute(query)
        dates = result.scalars().all()

        # Format dates as ISO strings
        booked_dates = [
            date.isoformat() if hasattr(date, "isoformat") else str(date) for date in dates
        ]

        # Return in flat format expected by frontend: { bookedDates: [...] }
        # The API client wrapper adds { success: true, data: ... } automatically
        return {
            "bookedDates": booked_dates,
        }

    except Exception as e:
        logger.error(f"Error fetching booked dates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch booked dates",
        )


@router.get(
    "/availability",
    summary="Check availability for a specific date",
    description="""
    Check if a specific date is available for bookings.

    ## Query Parameters:
    - **date**: Date to check in YYYY-MM-DD format

    ## Response:
    Returns availability status and booking count for the date.

    ## Authentication:
    Public endpoint - no authentication required.
    """,
)
async def check_availability(
    date: str = Query(..., description="Date to check (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check availability for a specific date."""
    try:
        # Parse and validate date
        try:
            parsed_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

        # Check if date is in the past
        if parsed_date < datetime.now(timezone.utc).date():
            return {
                "success": True,
                "date": date,
                "available": False,
                "reason": "Date is in the past",
                "bookings_count": 0,
            }

        # Use AvailabilityEngine for dual-mode availability checking
        # - Short-term (≤ 14 days): Uses actual chef availability
        # - Long-term (> 14 days): Uses SSoT long_advance_slot_capacity
        availability_engine = AvailabilityEngine(db)
        slots = await availability_engine.get_available_slots_for_date(
            event_date=parsed_date,
            guest_count=10,  # Default guest count for availability check
        )

        # Count total available slots and bookings
        available_slots = [s for s in slots if s.is_available]
        total_bookings = sum(s.booking_count for s in slots)

        # Date is available if at least one slot is available
        available = len(available_slots) > 0

        return {
            "success": True,
            "date": date,
            "available": available,
            "bookings_count": total_bookings,
            "available_slots_count": len(available_slots),
            "total_slots": len(slots),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability for {date}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check availability",
        )


@router.get(
    "/available-times",
    summary="Get available time slots for a date",
    description="""
    Retrieve available time slots for a specific date.

    ## Query Parameters:
    - **date**: Date to check in YYYY-MM-DD format

    ## Response:
    Returns array of time slots with availability status.
    Time slots are: 12PM, 3PM, 6PM, 9PM

    ## Authentication:
    Optional - works for both authenticated and public access.
    """,
)
async def get_available_times(
    date: str = Query(..., description="Date to check (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Get available time slots for a specific date."""
    try:
        # Parse and validate date
        try:
            parsed_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

        # Check if date is in the past
        today = datetime.now(timezone.utc).date()
        if parsed_date < today:
            return {
                "success": True,
                "date": date,
                "timeSlots": [],
                "message": "Date is in the past",
            }

        # Check if date is too far in the future (365 days = 1 year)
        max_date = today + timedelta(days=365)
        if parsed_date > max_date:
            return {
                "success": True,
                "date": date,
                "timeSlots": [],
                "message": "Date is too far in the future (max 1 year)",
            }

        # Use SlotManager for time slot definitions
        # This replaces hardcoded time_slot_definitions with the smart scheduling system
        slot_manager = SlotManager()

        # Initialize AvailabilityEngine for dynamic chef availability
        # This replaces hardcoded max_per_slot = 1
        availability_engine = AvailabilityEngine(db=db)

        # Query existing bookings for this date (still needed for booking count)
        query = select(Booking.slot).where(
            Booking.date == parsed_date,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.deleted_at.is_(None),
        )

        # Apply station filtering if user is authenticated
        if current_user and current_user.get("station_id"):
            query = query.where(Booking.station_id == UUID(current_user["station_id"]))

        result = await db.execute(query)
        booked_slots = [row.slot for row in result.all() if row.slot]

        # Build response with dynamic chef-based availability
        time_slots = []
        for slot_num, slot_config in DEFAULT_SLOTS.items():
            slot_time = slot_config.standard_time

            # Use AvailabilityEngine to check real chef availability
            # This replaces hardcoded max_per_slot = 1 with actual chef count
            availability = await availability_engine.check_slot_availability(
                event_date=parsed_date,
                slot_time=slot_time,
                guest_count=10,  # Default guest count for availability check
            )

            available_chefs = availability.get("available_chefs", 0)
            is_available = availability.get("is_available", False)

            # If it's today, check if the time has already passed
            if parsed_date == today:
                now = datetime.now(timezone.utc).time()
                # Need at least 4 hours advance notice
                cutoff = (datetime.combine(today, slot_time) - timedelta(hours=4)).time()
                if now > cutoff:
                    is_available = False
                    available_chefs = 0

            # Format time label (e.g., "12:00 PM - 2:00 PM")
            hour = slot_time.hour
            period = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            display_hour = 12 if display_hour == 0 else display_hour
            end_hour = hour + 2
            end_period = "AM" if end_hour < 12 else "PM"
            end_display = end_hour if end_hour <= 12 else end_hour - 12
            end_display = 12 if end_display == 0 else end_display
            label = f"{display_hour}:00 {period} - {end_display}:00 {end_period}"

            # Format time key (e.g., "12PM")
            time_key = f"{display_hour}{period}"

            time_slots.append(
                {
                    "time": time_key,
                    "label": label,
                    "available": available_chefs,
                    "isAvailable": is_available,
                    # Include adjustment range info from SlotManager
                    "adjustmentRange": {
                        "preferred": f"±30 min ({slot_config.min_time_30.strftime('%I:%M %p')} - {slot_config.max_time_30.strftime('%I:%M %p')})",
                        "maximum": f"±60 min ({slot_config.min_time_60.strftime('%I:%M %p')} - {slot_config.max_time_60.strftime('%I:%M %p')})",
                    },
                }
            )

        # Return in flat format expected by frontend: { timeSlots: [...] }
        # The API client wrapper adds { success: true, data: ... } automatically
        return {
            "timeSlots": time_slots,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available times for {date}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch available times",
        )
