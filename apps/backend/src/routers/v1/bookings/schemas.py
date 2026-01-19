"""
Booking Pydantic Schemas.

This module contains all Pydantic models for the bookings API endpoints.
Schemas are used for request validation and response serialization.

Related Endpoints:
- CRUD: create, read, update, delete bookings
- Calendar: admin weekly/monthly views, reschedule
- Availability: check dates, available time slots
- Cancellation: 2-step cancellation workflow
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# CRUD Schemas
# =============================================================================


class BookingCreate(BaseModel):
    """Schema for creating a new booking."""

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


class BookingResponse(BaseModel):
    """Schema for booking response."""

    id: str = Field(..., description="Unique booking identifier")
    user_id: str = Field(..., description="User ID who created the booking")
    date: str = Field(..., description="Booking date")
    time: str = Field(..., description="Booking time")
    guests: int = Field(..., description="Number of guests")
    status: str = Field(
        ...,
        description="Booking status (pending, confirmed, completed, cancelled)",
    )
    total_amount: float = Field(..., description="Total cost in USD")
    deposit_paid: bool = Field(..., description="Whether deposit has been paid")
    balance_due: float = Field(..., description="Remaining balance due in USD")
    payment_status: str = Field(..., description="Payment status")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "booking-abc123",
                    "user_id": "user-xyz789",
                    "date": "2024-12-25",
                    "time": "18:00",
                    "guests": 8,
                    "status": "confirmed",
                    "total_amount": 450.00,
                    "deposit_paid": True,
                    "balance_due": 350.00,
                    "payment_status": "deposit_paid",
                    "created_at": "2024-10-19T10:30:00Z",
                }
            ]
        }
    }


class BookingUpdate(BaseModel):
    """Schema for updating an existing booking."""

    date: str | None = Field(None, description="Updated booking date")
    time: str | None = Field(None, description="Updated booking time")
    guests: int | None = Field(None, ge=1, le=50, description="Updated guest count")
    location_address: str | None = Field(None, description="Updated location")
    special_requests: str | None = Field(
        None, max_length=500, description="Updated special requests"
    )
    status: str | None = Field(None, description="Updated status")
    chef_id: UUID | None = Field(
        None,
        description="Assign chef to booking (UUID). Set to null to unassign chef.",
    )


# =============================================================================
# Delete Schemas
# =============================================================================


class DeleteBookingRequest(BaseModel):
    """Schema for deleting a booking with mandatory reason."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Mandatory deletion reason (10-500 characters)",
        json_schema_extra={
            "examples": [
                "Customer requested cancellation due to weather concerns",
                "Duplicate booking created by mistake",
                "Customer no longer needs the service",
            ]
        },
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"reason": "Customer requested cancellation due to weather concerns"}]
        }
    }


class DeleteBookingResponse(BaseModel):
    """Schema for delete booking response."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Success message")
    booking_id: str = Field(..., description="Deleted booking ID")
    deleted_at: str = Field(..., description="Deletion timestamp (ISO 8601)")
    deleted_by: str = Field(..., description="User ID who performed deletion")
    restore_until: str = Field(
        ..., description="Date until which booking can be restored (ISO 8601)"
    )
    reason: str = Field(..., description="Reason for deletion")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Booking deleted successfully",
                    "booking_id": "booking-abc123",
                    "deleted_at": "2025-10-28T15:30:00Z",
                    "deleted_by": "user-xyz789",
                    "restore_until": "2025-11-27T15:30:00Z",
                    "reason": "Customer requested cancellation",
                }
            ]
        }
    }


# =============================================================================
# Cancellation Workflow Schemas (2-Step Process)
# =============================================================================


class CancellationRequestInput(BaseModel):
    """Schema for requesting booking cancellation (Step 1)."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for cancellation request (10-500 characters)",
        json_schema_extra={
            "examples": [
                "Customer called to cancel due to weather concerns",
                "Event venue no longer available",
                "Customer wants to reschedule to a different date",
            ]
        },
    )


class CancellationApprovalInput(BaseModel):
    """Schema for approving cancellation request (Step 2 - Approve)."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for approving cancellation (10-500 characters)",
        json_schema_extra={
            "examples": [
                "Approved per customer request - full refund issued",
                "Approved - event falls outside service window",
                "Approved - customer provided valid documentation",
            ]
        },
    )


class CancellationRejectionInput(BaseModel):
    """Schema for rejecting cancellation request (Step 2 - Reject)."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for rejecting cancellation (10-500 characters)",
        json_schema_extra={
            "examples": [
                "Rejected - event is within 24-hour no-cancellation window",
                "Rejected - deposit is non-refundable per policy",
                "Rejected - customer agreed to proceed with event",
            ]
        },
    )


class CancellationResponse(BaseModel):
    """Response schema for cancellation workflow actions."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable result message")
    booking_id: str = Field(..., description="Booking ID")
    previous_status: str = Field(..., description="Status before this action")
    new_status: str = Field(..., description="Status after this action")
    action_by: str = Field(..., description="User ID who performed the action")
    action_at: str = Field(..., description="Timestamp of action (ISO 8601)")


# =============================================================================
# Error Response Schema
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Error message")

    model_config = {"json_schema_extra": {"examples": [{"detail": "Booking not found"}]}}
