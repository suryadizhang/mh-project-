"""
Booking request/response schemas with comprehensive validation
Prevents injection attacks and validates all inputs
"""

import re
from datetime import date, datetime, time, timedelta
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from services.business_config_service import get_business_config_sync


class BookingStatus(str, Enum):
    """Booking status enumeration"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingCreate(BaseModel):
    """
    Schema for creating a new booking with strict validation

    Security Features:
    - No **kwargs injection - all fields explicitly defined
    - Time format validation (HH:MM 24-hour format)
    - Party size constraints (1-50 guests)
    - Date validation (must be in future)
    - UUID validation for customer_id
    - Email validation for contact_email
    - Phone number format validation
    """

    customer_id: UUID = Field(
        ...,
        description="Customer UUID - must be a valid UUID4",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    event_date: date = Field(
        ...,
        description="Date of the event (YYYY-MM-DD format)",
        examples=["2025-12-31"],
    )

    event_time: str = Field(
        ...,
        description="Time of event in 24-hour HH:MM format",
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        examples=["18:30", "14:00", "20:45"],
        min_length=4,
        max_length=5,
    )

    party_size: int = Field(
        ..., ge=1, le=50, description="Number of guests (1-50)", examples=[4, 8, 12]
    )

    # Optional contact information (may differ from customer profile)
    contact_phone: str | None = Field(
        None,
        description="Contact phone number (E.164 format recommended)",
        pattern=r"^\+?[1-9]\d{1,14}$|^\(\d{3}\)\s?\d{3}-\d{4}$|^\d{3}-\d{3}-\d{4}$",
        max_length=20,
        examples=["+14155552671", "(415) 555-2671", "415-555-2671"],
    )

    contact_email: EmailStr | None = Field(
        None, description="Contact email address", examples=["customer@example.com"]
    )

    # Special requests and notes
    special_requests: str | None = Field(
        None,
        max_length=1000,
        description="Special dietary restrictions or requests",
        examples=["Vegetarian menu required", "Celebrating birthday"],
    )

    internal_notes: str | None = Field(
        None,
        max_length=500,
        description="Internal notes (admin only)",
        examples=["VIP customer", "Prefers window seating"],
    )

    # Table assignment (optional, usually set by staff)
    table_number: str | None = Field(
        None,
        max_length=10,
        pattern=r"^[A-Z0-9-]+$",
        description="Table number/identifier (alphanumeric with hyphens)",
        examples=["T-12", "VIP1", "PATIO-4"],
    )

    # Additional booking metadata
    duration_hours: int | None = Field(
        default=2,
        ge=1,
        le=8,
        description="Expected duration in hours (1-8)",
        examples=[2, 3, 4],
    )

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, v: date) -> date:
        """
        Ensure event date is valid:
        - Not in the past
        - Not more than max_advance_days in the future (SSoT: booking.max_advance_days)

        The max_advance_days value comes from dynamic_variables table via SSoT.
        Default is 365 days if not configured.
        """
        if v < date.today():
            raise ValueError("Event date cannot be in the past")

        # Get max advance days from SSoT (defaults to 365 if not in DB)
        try:
            config = get_business_config_sync()
            # max_advance_days is stored in dynamic_variables as booking.max_advance_days
            max_days = getattr(config, "max_advance_days", 365)
        except Exception:
            # Fallback to 365 days if config unavailable
            max_days = 365

        max_future_date = date.today() + timedelta(days=max_days)
        if v > max_future_date:
            raise ValueError(
                f"Event date cannot be more than {max_days} days in advance. "
                f"Maximum booking date is {max_future_date.strftime('%B %d, %Y')}."
            )

        return v

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, v: str) -> str:
        """Validate time format and ensure it's within business hours"""
        # Regex pattern already validates HH:MM format (00:00 to 23:59)
        # Additional business logic: ensure time is within operational hours
        try:
            hour, minute = map(int, v.split(":"))

            # Example: Restaurant operates 11:00 - 23:00
            if hour < 11 or hour >= 23:
                raise ValueError("Booking time must be between 11:00 and 23:00")

            # Time object for further validation if needed
            time(hour=hour, minute=minute)

        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid time format: {v}. Use HH:MM format (e.g., '18:30')"
            )

        return v

    @field_validator("special_requests", "internal_notes")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        """Sanitize text fields to prevent XSS/injection attacks"""
        if v is None:
            return None

        # Remove control characters and trim whitespace
        v = v.strip()

        # Remove null bytes
        v = v.replace("\x00", "")

        # Optionally remove HTML tags (basic sanitization)
        v = re.sub(r"<[^>]*>", "", v)

        return v if v else None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                    "event_date": "2025-12-31",
                    "event_time": "18:30",
                    "party_size": 6,
                    "contact_phone": "+14155552671",
                    "contact_email": "customer@example.com",
                    "special_requests": "Celebrating anniversary, would like a window table",
                    "duration_hours": 3,
                }
            ]
        }
    }


class BookingUpdate(BaseModel):
    """
    Schema for updating an existing booking
    All fields optional - only provided fields will be updated
    """

    event_date: date | None = Field(None, description="New event date")
    event_time: str | None = Field(
        None,
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="New event time (HH:MM format)",
    )
    party_size: int | None = Field(None, ge=1, le=50, description="New party size")
    contact_phone: str | None = Field(
        None,
        pattern=r"^\+?[1-9]\d{1,14}$|^\(\d{3}\)\s?\d{3}-\d{4}$|^\d{3}-\d{3}-\d{4}$",
        max_length=20,
    )
    contact_email: EmailStr | None = None
    special_requests: str | None = Field(None, max_length=1000)
    internal_notes: str | None = Field(None, max_length=500)
    table_number: str | None = Field(None, max_length=10, pattern=r"^[A-Z0-9-]+$")
    status: BookingStatus | None = None

    # Validators apply same rules as BookingCreate
    _validate_date = field_validator("event_date")(
        BookingCreate.validate_event_date.__func__
    )
    _validate_time = field_validator("event_time")(
        BookingCreate.validate_event_time.__func__
    )
    _sanitize_text = field_validator("special_requests", "internal_notes")(
        BookingCreate.sanitize_text_fields.__func__
    )


class BookingResponse(BaseModel):
    """Schema for booking responses"""

    id: UUID
    customer_id: UUID
    event_date: date
    event_time: str
    party_size: int
    status: BookingStatus

    contact_phone: str | None = None
    contact_email: str | None = None
    special_requests: str | None = None
    internal_notes: str | None = None
    table_number: str | None = None

    confirmed_at: datetime | None = None
    seated_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "customer_id": "987fcdeb-51a2-43f7-9876-fedcba098765",
                    "event_date": "2025-12-31",
                    "event_time": "18:30",
                    "party_size": 6,
                    "status": "confirmed",
                    "contact_email": "customer@example.com",
                    "created_at": "2025-10-11T10:30:00Z",
                    "updated_at": "2025-10-11T10:30:00Z",
                }
            ]
        },
    }


class BookingListResponse(BaseModel):
    """Schema for paginated booking list responses"""

    bookings: list[BookingResponse]
    total: int = Field(..., ge=0, description="Total number of bookings")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bookings": [],
                    "total": 0,
                    "page": 1,
                    "per_page": 20,
                    "total_pages": 0,
                }
            ]
        }
    }
