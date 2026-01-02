"""
Chef Portal Schemas

Pydantic models for chef self-service operations:
- Weekly availability management
- Time-off requests
- Chef profile viewing

Authorization:
- Chefs can only modify their OWN availability
- Station managers can view/manage chefs in their station
- Super admins have full access

See: 21-BUSINESS_MODEL.instructions.md for business rules
See: utils/auth.py for RBAC permissions
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums (matching database enums from ops.py)
# ============================================================================


class DayOfWeek(str, Enum):
    """Days of the week for scheduling."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeOffType(str, Enum):
    """Types of time-off requests."""

    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    UNPAID = "unpaid"


class TimeOffStatus(str, Enum):
    """Time-off request status."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


class ChefStatus(str, Enum):
    """Chef account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"


# ============================================================================
# Chef Profile Schemas
# ============================================================================


class ChefProfileResponse(BaseModel):
    """Chef's own profile information."""

    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    specialty: str
    status: ChefStatus
    rating: Optional[Decimal] = None
    total_bookings: int = 0
    completed_bookings: int = 0
    hired_date: Optional[date] = None

    class Config:
        from_attributes = True


# ============================================================================
# Availability Schemas
# ============================================================================


class ChefAvailabilityBase(BaseModel):
    """Base schema for availability with validation."""

    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    is_available: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: time, info) -> time:
        """Ensure end_time is after start_time."""
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class ChefAvailabilityCreate(ChefAvailabilityBase):
    """Create a new availability slot."""

    pass


class ChefAvailabilityUpdate(BaseModel):
    """Update an existing availability slot."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None


class ChefAvailabilityResponse(ChefAvailabilityBase):
    """Response for a single availability slot."""

    id: UUID
    chef_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ChefWeeklyAvailabilityResponse(BaseModel):
    """Full weekly availability schedule."""

    chef_id: UUID
    chef_name: str
    slots: List[ChefAvailabilityResponse]


class BulkAvailabilityUpdate(BaseModel):
    """Bulk update for weekly availability."""

    slots: List[ChefAvailabilityCreate] = Field(
        ...,
        min_length=1,
        max_length=21,  # Max 3 slots per day × 7 days
        description="List of availability slots to set",
    )
    replace_existing: bool = Field(
        True,
        description="If true, deletes existing slots before adding new ones",
    )


# ============================================================================
# Time-Off Schemas
# ============================================================================


class TimeOffRequestBase(BaseModel):
    """Base schema for time-off requests."""

    start_date: date
    end_date: date
    type: TimeOffType
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Ensure end_date is on or after start_date."""
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date cannot be before start_date")
        return v

    @field_validator("start_date")
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        """Ensure start_date is not in the past."""
        if v < date.today():
            raise ValueError("start_date cannot be in the past")
        return v


class TimeOffRequestCreate(TimeOffRequestBase):
    """Create a new time-off request."""

    pass


class TimeOffRequestResponse(TimeOffRequestBase):
    """Response for a single time-off request."""

    id: UUID
    chef_id: UUID
    status: TimeOffStatus
    approved_by: Optional[str] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimeOffRequestListResponse(BaseModel):
    """List of time-off requests."""

    requests: List[TimeOffRequestResponse]
    total: int


class TimeOffApprovalRequest(BaseModel):
    """Station manager approval/denial of time-off."""

    status: TimeOffStatus = Field(
        ...,
        description="Must be 'approved' or 'denied'",
    )
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: TimeOffStatus) -> TimeOffStatus:
        """Only allow approved or denied status."""
        if v not in [TimeOffStatus.APPROVED, TimeOffStatus.DENIED]:
            raise ValueError("Status must be 'approved' or 'denied'")
        return v


# ============================================================================
# Station Manager View Schemas
# ============================================================================


class StationChefSummary(BaseModel):
    """Summary of a chef for station manager view."""

    id: UUID
    name: str
    email: str
    specialty: str
    status: ChefStatus
    rating: Optional[Decimal] = None
    pending_timeoff_count: int = 0


class StationChefListResponse(BaseModel):
    """List of chefs in a station."""

    station_id: UUID
    station_name: str
    chefs: List[StationChefSummary]
    total: int
