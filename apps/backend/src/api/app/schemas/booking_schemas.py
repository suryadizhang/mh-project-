from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingCreate(BaseModel):
    """Request body for creating a new booking."""

    name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    zipcode: str
    date: str
    time_slot: str
    contact_preference: str


class WaitlistCreate(BaseModel):
    """Request body for joining the waitlist."""

    name: str
    phone: str
    email: EmailStr
    preferred_date: str
    preferred_time: str


class CancelBookingRequest(BaseModel):
    """Request body for cancelling a booking (admin only)."""

    reason: str


class WaitlistEntry(BaseModel):
    """Waitlist entry model."""

    id: int
    name: str
    phone: str
    email: str
    preferred_date: str
    preferred_time: str
    created_at: datetime | None = None


class BookingResponse(BaseModel):
    """Response model for booking operations."""

    id: int
    name: str
    phone: str
    email: str
    address: str
    city: str
    zipcode: str
    date: str
    time_slot: str
    contact_preference: str
    created_at: datetime
    deposit_received: bool = False


class AdminCreateRequest(BaseModel):
    """Request body for creating admin user."""

    username: str
    password: str
    full_name: str | None = None
    email: EmailStr | None = None


class PasswordChangeRequest(BaseModel):
    """Request body for changing password."""

    current_password: str
    new_password: str


class NewsletterSendRequest(BaseModel):
    """Request body for sending newsletter."""

    subject: str
    message: str
    city_filter: str | None = None
    send_type: str = "email"


class CustomerAnalytics(BaseModel):
    """Customer analytics response model."""

    total_customers: int
    new_customers_this_month: int
    returning_customers: int
    customer_tiers: dict
    top_customers: list
    booking_patterns: dict
    retention_rate: float
