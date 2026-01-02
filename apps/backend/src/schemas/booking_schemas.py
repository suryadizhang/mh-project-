"""
Booking Schemas - Legacy Compatibility Module

This module contains legacy booking schemas for backward compatibility.
For enterprise booking schemas with UUID references, use schemas.booking

NOTE: The following schema files were cleaned up as unused:
- schemas.waitlist - DELETED (waitlist feature never implemented)
- schemas.admin - DELETED (endpoints use Form(...) directly)
- schemas.newsletter - DELETED (duplicate of newsletters.py endpoint)

Remaining modular schemas:
- schemas.analytics (CustomerAnalytics) - Business analytics for admin dashboard
- schemas.booking - Enterprise booking schemas with UUID references
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr

# Re-export analytics for backward compatibility
from schemas.analytics import CustomerAnalytics

# Import UserRole from auth.py (Single Source of Truth)
# This replaces the legacy 3-role enum (CUSTOMER, ADMIN, SUPERADMIN)
from utils.auth import UserRole


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingCreate(BaseModel):
    """
    Request body for creating a new booking (legacy format).

    Note: For enterprise booking with UUID customer references,
    use schemas.booking.BookingCreate instead.
    """

    name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    zipcode: str
    date: str
    time_slot: str
    contact_preference: str


class CancelBookingRequest(BaseModel):
    """Request body for cancelling a booking (admin only)."""

    reason: str


class BookingResponse(BaseModel):
    """Response model for booking operations (legacy format)."""

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


# Explicit exports for documentation
__all__ = [
    # Legacy booking schemas
    "UserRole",
    "BookingStatus",
    "BookingCreate",
    "CancelBookingRequest",
    "BookingResponse",
    # Re-exported from modular files
    "CustomerAnalytics",
]
