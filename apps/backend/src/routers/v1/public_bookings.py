"""
Public Booking Endpoints (No Authentication Required)

This module handles PUBLIC booking operations that customers can use
WITHOUT logging in:
- Submit new bookings (leads/pending bookings)
- Get booked dates for calendar display
- Get available time slots for a specific date

These endpoints are designed for the customer-facing website.
Uses BusinessConfig for dynamic pricing values (Single Source of Truth).

## Enterprise-Grade Transaction Handling
This module implements industry-standard patterns:
1. Explicit transaction management with context managers
2. Proper rollback on any error (not just IntegrityError)
3. Connection pool health checks
4. Retry logic for transient database errors
5. Proper exception chaining for debugging
"""

import asyncio
import os
import re
from datetime import (
    datetime,
    date as date_type,
    time as time_type,
    timedelta,
    timezone,
)
import logging
from typing import Any
from uuid import UUID, uuid4

from core.database import get_db
from db.models.core import Booking, BookingStatus, Customer
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from services.unified_notification_service import notify_new_booking
from services.email_service import email_service
from services.encryption_service import SecureDataHandler
from services.business_config_service import get_business_config_sync
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError, DBAPIError

router = APIRouter(tags=["public-bookings"])
logger = logging.getLogger(__name__)

# Station ID for Houston (main business location)
DEFAULT_STATION_ID = "11111111-1111-1111-1111-111111111111"

# Enterprise retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.5


# ============================================================================
# ENTERPRISE-GRADE HELPER FUNCTIONS
# ============================================================================


async def verify_db_connection(db: AsyncSession) -> bool:
    """
    Verify database connection is healthy.

    Enterprise pattern: Always verify connection before critical operations.
    This catches stale connections from the pool.
    """
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False


async def safe_rollback(db: AsyncSession) -> None:
    """
    Safely rollback a transaction, handling any errors.

    Enterprise pattern: Rollback can fail if connection is broken.
    Always wrap in try-except.
    """
    try:
        await db.rollback()
        logger.debug("Transaction rolled back successfully")
    except Exception as e:
        logger.error(f"Rollback failed (connection may be dead): {e}")
        # Connection is likely corrupted, it will be recycled by pool


def is_transient_error(error: Exception) -> bool:
    """
    Check if error is transient and worth retrying.

    Enterprise pattern: Distinguish transient errors (retry) from
    permanent errors (fail fast).
    """
    transient_indicators = [
        "connection refused",
        "connection reset",
        "timeout",
        "deadlock",
        "lock wait timeout",
        "too many connections",
        "server closed the connection",
    ]
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in transient_indicators)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class PublicBookingCreate(BaseModel):
    """Schema for creating a public booking (no auth required)."""

    date: str = Field(..., description="Booking date in YYYY-MM-DD format")
    time: str = Field(..., description="Booking time in HH:MM format")
    guests: int = Field(..., ge=1, le=50, description="Number of guests (1-50)")
    location_address: str = Field(..., min_length=10, description="Event location address")
    customer_name: str = Field(..., min_length=2, description="Customer full name")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_phone: str = Field(..., description="Customer phone number")
    special_requests: str | None = Field(
        None,
        max_length=500,
        description="Special requests or dietary restrictions",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2024-12-25",
                    "time": "18:00",
                    "guests": 8,
                    "location_address": "123 Main St, San Jose, CA 95123",
                    "customer_name": "John Doe",
                    "customer_email": "john@example.com",
                    "customer_phone": "+14155551234",
                    "special_requests": "Vegetarian option for 2 guests",
                }
            ]
        }
    }


class PublicBookingResponse(BaseModel):
    """Response schema for public booking creation."""

    id: str = Field(..., description="Unique booking identifier")
    date: str = Field(..., description="Booking date")
    time: str = Field(..., description="Booking time")
    guests: int = Field(..., description="Number of guests")
    status: str = Field(..., description="Booking status (pending)")
    total_amount: float = Field(..., description="Total cost in USD")
    deposit_amount: float = Field(..., description="Required deposit in USD ($100 fixed)")
    deposit_deadline: str = Field(..., description="Deadline to pay deposit")
    created_at: str = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Confirmation message")


class TimeSlot(BaseModel):
    """Schema for available time slot."""

    time: str = Field(..., description="Time slot label (e.g., '12PM')")
    label: str = Field(..., description="Human readable label (e.g., '12:00 PM - 2:00 PM')")
    available: int = Field(..., description="Number of slots available")
    isAvailable: bool = Field(..., description="Whether the slot is available")


class AvailableTimeSlotsResponse(BaseModel):
    """Response schema for available time slots."""

    success: bool
    date: str
    timeSlots: list[TimeSlot]


class BookedDatesResponse(BaseModel):
    """Response schema for booked dates."""

    success: bool
    data: list[str] = Field(default_factory=list)
    count: int


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================


@router.get(
    "/booked-dates",
    response_model=BookedDatesResponse,
    summary="Get all booked dates (PUBLIC)",
    description="""
    Retrieve dates that are fully booked.
    No authentication required - used for calendar display on customer website.

    ## Response:
    Returns array of dates in YYYY-MM-DD format that are fully booked.
    """,
)
async def get_booked_dates_public(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all dates that have reached maximum bookings (public endpoint)."""
    try:
        # Get dates with 2+ bookings (fully booked)
        # Using subquery to count bookings per date
        max_bookings_per_day = 2

        query = (
            select(Booking.date, func.count(Booking.id).label("booking_count"))
            .where(
                Booking.status.in_(["pending", "confirmed", "completed"]),
                Booking.deleted_at.is_(None),
            )
            .group_by(Booking.date)
            .having(func.count(Booking.id) >= max_bookings_per_day)
        )

        result = await db.execute(query)
        rows = result.all()

        # Format dates as ISO strings
        booked_dates = [
            (row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date))
            for row in rows
        ]

        # Return format matching BookedDatesResponse schema
        return {
            "success": True,
            "data": booked_dates,
            "count": len(booked_dates),
        }

    except Exception as e:
        logger.error(f"Error fetching booked dates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch booked dates",
        )


@router.get(
    "/available-times",
    response_model=AvailableTimeSlotsResponse,
    summary="Get available time slots for a date (PUBLIC)",
    description="""
    Retrieve available time slots for a specific date.
    No authentication required - used for booking form on customer website.

    ## Query Parameters:
    - **date**: Date to check in YYYY-MM-DD format

    ## Response:
    Returns array of time slots with availability status.
    Time slots are: 12PM, 3PM, 6PM, 9PM
    """,
)
async def get_available_times(
    date: str = Query(..., description="Date to check (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
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

        # Define time slots (matching frontend expectations)
        time_slot_definitions = [
            {
                "time": "12PM",
                "label": "12:00 PM - 2:00 PM",
                "slot_time": time_type(12, 0),
            },
            {
                "time": "3PM",
                "label": "3:00 PM - 5:00 PM",
                "slot_time": time_type(15, 0),
            },
            {
                "time": "6PM",
                "label": "6:00 PM - 8:00 PM",
                "slot_time": time_type(18, 0),
            },
            {
                "time": "9PM",
                "label": "9:00 PM - 11:00 PM",
                "slot_time": time_type(21, 0),
            },
        ]

        # Query existing bookings for this date
        query = select(Booking.slot).where(
            Booking.date == parsed_date,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.deleted_at.is_(None),
        )
        result = await db.execute(query)
        booked_slots = [row.slot for row in result.all() if row.slot]

        # Max bookings per slot (usually 1 for hibachi - chef can only be at one place)
        max_per_slot = 1

        # Build response with availability
        time_slots = []
        for slot_def in time_slot_definitions:
            slot_time = slot_def["slot_time"]

            # Count how many bookings at this time
            booked_count = sum(1 for b in booked_slots if b == slot_time)
            available = max(0, max_per_slot - booked_count)
            is_available = available > 0

            # If it's today, check if the time has already passed
            if parsed_date == today:
                now = datetime.now(timezone.utc).time()
                # Need at least 4 hours advance notice
                cutoff = (datetime.combine(today, slot_time) - timedelta(hours=4)).time()
                if now > cutoff:
                    is_available = False
                    available = 0

            time_slots.append(
                {
                    "time": slot_def["time"],
                    "label": slot_def["label"],
                    "available": available,
                    "isAvailable": is_available,
                }
            )

        # Return format matching AvailableTimeSlotsResponse schema
        return {
            "success": True,
            "date": date,
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


@router.post(
    "/",
    response_model=PublicBookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking (PUBLIC)",
    description="""
    Create a new hibachi catering booking request.
    No authentication required - for customer website use.

    ## Requirements:
    - Date must be at least 48 hours in the future
    - Guest count between 1-50
    - Valid US phone number and email
    - Complete location address

    ## Process:
    1. Validates booking data
    2. Checks availability for requested date/time
    3. Calculates pricing based on guests
    4. Creates booking with 'pending' status
    5. Sends WhatsApp notification to business

    ## Pricing (from BusinessConfig):
    - Adult price: $55/person (ages 13+)
    - Child price: $30/person (ages 6-12)
    - Minimum party: $550
    - Fixed deposit: $100 (due within 2 hours)
    """,
    responses={
        201: {"description": "Booking created successfully"},
        400: {"description": "Invalid booking data"},
        409: {"description": "Time slot not available"},
    },
)
async def create_public_booking(
    booking_data: PublicBookingCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new booking from the customer website (no authentication).

    This endpoint is used by the customer-facing booking form.
    All new bookings start as 'pending' until deposit is paid.

    ## Enterprise-Grade Error Handling:
    1. Verifies DB connection before starting
    2. Uses explicit transaction with proper rollback
    3. Handles transient errors with retry logic
    4. Preserves error context for debugging
    """
    # =========================================================================
    # STEP 0: VERIFY DB CONNECTION (Enterprise Pattern)
    # =========================================================================
    if not await verify_db_connection(db):
        logger.error("Database connection unhealthy, cannot create booking")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable. Please try again in a moment.",
        )

    # =========================================================================
    # STEP 1: INPUT VALIDATION (Before starting transaction)
    # =========================================================================
    try:
        # Initialize encryption handler for PII
        try:
            encryption_handler = SecureDataHandler()
        except ValueError as e:
            logger.error(f"Encryption key not configured: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error",
            )

        # Parse date and time
        try:
            booking_date = date_type.fromisoformat(booking_data.date)
            hour, minute = map(int, booking_data.time.split(":"))
            booking_slot = time_type(hour=hour, minute=minute)
        except (ValueError, AttributeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date or time format: {e}",
            )

        # Validate date is in the future (at least 48 hours)
        now = datetime.now(timezone.utc)
        booking_datetime = datetime.combine(booking_date, booking_slot, tzinfo=timezone.utc)
        if booking_datetime < now + timedelta(hours=48):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking date must be at least 48 hours in the future",
            )

        # Validate date is not too far in the future (365 days = 1 year)
        max_date = now + timedelta(days=365)
        if booking_datetime > max_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking date cannot be more than 1 year in the future",
            )

        # Validate time is within business hours (11:00 - 22:00)
        if hour < 11 or hour >= 22:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking time must be between 11:00 AM and 10:00 PM",
            )

        # Pre-compute encrypted values (before transaction)
        name_parts = booking_data.customer_name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else "Guest"
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        email_encrypted = encryption_handler.encrypt_email(booking_data.customer_email)
        phone_encrypted = encryption_handler.encrypt_phone(booking_data.customer_phone)
        address_encrypted = encryption_handler.encrypt_email(booking_data.location_address)

        zip_match = re.search(r"\b(\d{5})\b", booking_data.location_address)
        zone = zip_match.group(1) if zip_match else "DEFAULT"

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Input validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking data provided",
        )

    # =========================================================================
    # STEP 2: DATABASE TRANSACTION (Enterprise Pattern - Explicit Management)
    # =========================================================================
    booking_id = uuid4()
    customer_id = None

    for attempt in range(MAX_RETRIES):
        try:
            # Check availability with row locking
            existing_booking_stmt = (
                select(Booking)
                .where(
                    and_(
                        Booking.date == booking_date,
                        Booking.slot == booking_slot,
                        Booking.status.notin_([BookingStatus.CANCELLED]),
                        Booking.deleted_at.is_(None),
                    )
                )
                .with_for_update(nowait=False)
            )
            result = await db.execute(existing_booking_stmt)
            existing_booking = result.scalar_one_or_none()

            if existing_booking:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This time slot is already booked. Please select a different time.",
                )

            # Look up or create customer
            customer_stmt = select(Customer).where(
                Customer.email_encrypted == email_encrypted,
                Customer.deleted_at.is_(None),
            )
            result = await db.execute(customer_stmt)
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
                    timezone="America/Chicago",  # Houston timezone
                )
                db.add(customer)
                await db.flush()  # Get customer ID without committing
                logger.info(f"✅ Created new customer: {customer.id}")

            customer_id = customer.id

            # Get dynamic pricing (use sync version to avoid DB query that could abort transaction)
            # This uses environment variables only - safe from DB transaction issues
            config = get_business_config_sync()
            adult_price_cents = config.adult_price_cents
            child_price_cents = config.child_price_cents
            party_minimum_cents = config.party_minimum_cents
            deposit_cents = config.deposit_amount_cents

            logger.info(
                f"📊 Booking using {config.source} config: adult=${adult_price_cents/100}, deposit=${deposit_cents/100}"
            )

            # Calculate pricing
            party_adults = booking_data.guests
            party_kids = 0
            total_cents = max(
                party_adults * adult_price_cents + party_kids * child_price_cents,
                party_minimum_cents,
            )

            # Set deadlines (strip timezone for TIMESTAMP WITHOUT TIME ZONE columns)
            now_naive = now.replace(tzinfo=None)
            customer_deposit_deadline = now_naive + timedelta(hours=2)
            internal_deadline = now_naive + timedelta(hours=24)

            # Create booking
            booking = Booking(
                id=booking_id,
                customer_id=customer_id,
                station_id=UUID(DEFAULT_STATION_ID),
                date=booking_date,
                slot=booking_slot,
                address_encrypted=address_encrypted,
                zone=zone,
                party_adults=party_adults,
                party_kids=party_kids,
                deposit_due_cents=deposit_cents,
                total_due_cents=total_cents,
                status=BookingStatus.PENDING,
                source="web",
                sms_consent=True,
                sms_consent_timestamp=now,  # This column is TIMESTAMP WITH TIME ZONE
                customer_deposit_deadline=customer_deposit_deadline,  # Naive datetime
                internal_deadline=internal_deadline,  # Naive datetime
                deposit_deadline=customer_deposit_deadline,  # Naive datetime
                special_requests=booking_data.special_requests,
            )

            db.add(booking)

            # Commit the transaction
            await db.commit()
            logger.info(f"✅ Booking committed successfully: {booking_id}")
            break  # Success! Exit retry loop

        except HTTPException:
            # Business logic errors - don't retry, rollback and raise
            await safe_rollback(db)
            raise

        except IntegrityError as e:
            # Duplicate key or constraint violation - race condition
            await safe_rollback(db)
            logger.warning(f"IntegrityError (race condition): {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot was just booked. Please select a different time.",
            )

        except (OperationalError, DBAPIError) as e:
            # Database connectivity issues
            await safe_rollback(db)

            if is_transient_error(e) and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY_SECONDS * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"Transient DB error (attempt {attempt + 1}/{MAX_RETRIES}), retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Database error after {attempt + 1} attempts: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database temporarily unavailable. Please try again.",
                )

        except Exception as e:
            # Unexpected errors - log full context, rollback, fail
            await safe_rollback(db)
            logger.exception(f"Unexpected error creating booking: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking. Please try again or contact us directly.",
            )

    # =========================================================================
    # STEP 3: POST-COMMIT ACTIONS (Notifications - Non-blocking)
    # =========================================================================
    response = {
        "id": str(booking_id),
        "date": booking_data.date,
        "time": booking_data.time,
        "guests": booking_data.guests,
        "status": "pending",
        "total_amount": total_cents / 100,
        "deposit_amount": deposit_cents / 100,
        "deposit_deadline": customer_deposit_deadline.isoformat(),
        "created_at": now.isoformat(),
        "message": "Booking request received! Please pay the $100 deposit within 2 hours to confirm your booking.",
    }

    logger.info(
        f"✅ Public booking created: {booking_id} for {booking_data.customer_name} on {booking_data.date} at {booking_data.time}"
    )

    # Send WhatsApp/SMS notification asynchronously (non-blocking)
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
    logger.info(f"📱 WhatsApp/SMS notification queued for booking {booking_id}")

    # Send email notifications (customer + admin)
    try:
        if booking_data.customer_email:
            email_service.send_new_booking_email_to_customer(
                customer_email=booking_data.customer_email,
                customer_name=booking_data.customer_name,
                booking_id=str(booking_id),
                event_date=booking_data.date,
                event_time=booking_data.time,
                guest_count=booking_data.guests,
                location=booking_data.location_address,
            )
            logger.info(f"📧 Email confirmation sent to customer: {booking_data.customer_email}")

        admin_email = os.getenv("ADMIN_NOTIFICATION_EMAIL", "myhibachichef@gmail.com")
        email_service.send_new_booking_email_to_admin(
            admin_email=admin_email,
            customer_name=booking_data.customer_name,
            customer_phone=booking_data.customer_phone,
            customer_email=booking_data.customer_email or "Not provided",
            booking_id=str(booking_id),
            event_date=booking_data.date,
            event_time=booking_data.time,
            guest_count=booking_data.guests,
            location=booking_data.location_address,
            special_requests=booking_data.special_requests,
        )
        logger.info(f"📧 Email alert sent to admin: {admin_email}")
    except Exception as e:
        # Don't fail the booking if email fails - just log
        logger.error(f"❌ Failed to send email notifications: {e}")

    return response
