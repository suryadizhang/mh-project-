"""
Public Booking Endpoints (No Authentication Required)

This module handles PUBLIC booking operations that customers can use
WITHOUT logging in:
- Submit new bookings (leads/pending bookings)
- Get booked dates for calendar display
- Get available time slots for a specific date

These endpoints are designed for the customer-facing website.
Uses BusinessConfig for dynamic pricing values (Single Source of Truth).
"""

import asyncio
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
from services.business_config_service import get_business_config
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["public-bookings"])
logger = logging.getLogger(__name__)

# Station ID for Fremont, CA (main business location - California Bay Area)
DEFAULT_STATION_ID = "22222222-2222-2222-2222-222222222222"


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

        # Check if date is too far in the future (90 days)
        max_date = today + timedelta(days=90)
        if parsed_date > max_date:
            return {
                "success": True,
                "date": date,
                "timeSlots": [],
                "message": "Date is too far in the future (max 90 days)",
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
    """
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

        # Validate date is not too far in the future (90 days)
        max_date = now + timedelta(days=90)
        if booking_datetime > max_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking date cannot be more than 90 days in the future",
            )

        # Validate time is within business hours (11:00 - 22:00)
        if hour < 11 or hour >= 22:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking time must be between 11:00 AM and 10:00 PM",
            )

        # Check availability - ensure time slot is not already booked
        # ⚠️ RACE CONDITION FIX: Use SELECT FOR UPDATE to lock potential conflicting rows
        # This prevents TOCTOU (Time Of Check, Time Of Use) race conditions where
        # two concurrent requests could both pass the check before either commits
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
            .with_for_update(nowait=False)  # Lock row, wait if already locked
        )
        result = await db.execute(existing_booking_stmt)
        existing_booking = result.scalar_one_or_none()

        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot is already booked. Please select a different time.",
            )

        # Parse customer name into first/last
        name_parts = booking_data.customer_name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else "Guest"
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Encrypt PII
        email_encrypted = encryption_handler.encrypt_email(booking_data.customer_email)
        phone_encrypted = encryption_handler.encrypt_phone(booking_data.customer_phone)
        address_encrypted = encryption_handler.encrypt_email(booking_data.location_address)

        # Look up or create customer
        customer_stmt = select(Customer).where(
            Customer.email_encrypted == email_encrypted,
            Customer.deleted_at.is_(None),
        )
        result = await db.execute(customer_stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            # Create new customer (Fremont, CA station - California Bay Area)
            customer = Customer(
                id=uuid4(),
                station_id=UUID(DEFAULT_STATION_ID),  # Fremont, CA
                first_name=first_name,
                last_name=last_name,
                email_encrypted=email_encrypted,
                phone_encrypted=phone_encrypted,
                consent_sms=True,
                consent_email=True,
                consent_updated_at=now,
                timezone="America/Los_Angeles",  # California timezone
            )
            db.add(customer)
            await db.flush()
            logger.info(f"✅ Created new customer: {customer.id}")

        # Extract zone from address (ZIP code based)
        zip_match = re.search(r"\b(\d{5})\b", booking_data.location_address)
        zone = zip_match.group(1) if zip_match else "DEFAULT"

        # Get dynamic pricing from BusinessConfig (Single Source of Truth)
        config = await get_business_config(db)

        adult_price_cents = config.adult_price_cents
        child_price_cents = config.child_price_cents
        party_minimum_cents = config.party_minimum_cents
        deposit_cents = config.deposit_amount_cents

        logger.info(
            f"📊 Booking using {config.source} config: adult=${adult_price_cents/100}, deposit=${deposit_cents/100}"
        )

        # Calculate pricing (assuming all adults for now)
        party_adults = booking_data.guests
        party_kids = 0

        # Calculate total with party minimum
        total_cents = max(
            party_adults * adult_price_cents + party_kids * child_price_cents,
            party_minimum_cents,
        )

        # Set deadlines
        customer_deposit_deadline = now + timedelta(hours=2)
        internal_deadline = now + timedelta(hours=24)

        # Create booking
        booking_id = uuid4()
        booking = Booking(
            id=booking_id,
            customer_id=customer.id,
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
            sms_consent_timestamp=now,
            customer_deposit_deadline=customer_deposit_deadline,
            internal_deadline=internal_deadline,
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

        # Create response
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

        # Log booking creation
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
            # Email to customer
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
                logger.info(
                    f"📧 Email confirmation sent to customer: {booking_data.customer_email}"
                )

            # Email to admin (myhibachichef@gmail.com)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Failed to create public booking: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking. Please try again or contact us directly.",
        )
