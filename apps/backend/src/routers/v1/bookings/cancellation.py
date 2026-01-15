"""
2-Step Booking Cancellation Workflow
====================================

Implements a 2-step cancellation process for hibachi bookings:
1. REQUEST: Status → CANCELLATION_REQUESTED (slot remains held)
2. APPROVE/REJECT: Either release slot or revert status

Endpoints:
- POST /{booking_id}/request-cancellation - Step 1
- POST /{booking_id}/approve-cancellation - Step 2 (approve)
- POST /{booking_id}/reject-cancellation - Step 2 (reject)

Why 2 Steps?
Hibachi slots are limited. Once a slot is released, another customer may
book it immediately. This workflow allows review before permanent release.

File Size: ~350 lines (within 500 line limit)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit_logger import audit_logger
from core.database import get_db
from core.security import decrypt_pii
from core.security.roles import role_matches
from db.models.core import Booking, BookingStatus
from utils.auth import can_access_station, require_customer_support

from .notifications import notify_cancellation
from .schemas import (
    CancellationApprovalInput,
    CancellationRejectionInput,
    CancellationRequestInput,
    CancellationResponse,
    ErrorResponse,
)

router = APIRouter(tags=["bookings"])
logger = logging.getLogger(__name__)


@router.post(
    "/{booking_id}/request-cancellation",
    status_code=status.HTTP_200_OK,
    summary="Request booking cancellation (Step 1 of 2)",
    description="""
    Request cancellation of a booking. This is step 1 of the 2-step cancellation workflow.

    ## Workflow:
    1. **This endpoint**: Status changes to CANCELLATION_REQUESTED (slot remains held)
    2. **Approve or Reject**: Admin must then approve (releases slot) or reject (reverts status)

    ## Why 2 Steps?
    Hibachi slots are limited. Once a slot is released, another customer may book it immediately.
    This workflow allows review before permanently releasing the slot.

    ## What Happens:
    - Booking status changes to `cancellation_requested`
    - Previous status is stored for potential rejection/revert
    - Slot remains HELD (not released) until approved
    - Action is logged to audit trail

    ## Authentication:
    Requires CUSTOMER_SUPPORT role or higher.

    ## Station Access:
    STATION_MANAGER can only request cancellation for bookings in their station.
    """,
    response_model=CancellationResponse,
    responses={
        200: {"description": "Cancellation request recorded", "model": CancellationResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        404: {"description": "Booking not found", "model": ErrorResponse},
    },
)
async def request_cancellation(
    booking_id: str,
    request_input: CancellationRequestInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_customer_support()),
) -> CancellationResponse:
    """Request cancellation of a booking (Step 1 of 2-step workflow)."""

    # Fetch booking
    query = select(Booking).where(Booking.id == UUID(booking_id))
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check if already deleted
    if booking.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has been deleted",
        )

    # Get current status value
    current_status = (
        booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    )

    # Check if already cancelled or cancellation requested
    if current_status == BookingStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled",
        )

    if current_status == BookingStatus.CANCELLATION_REQUESTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancellation has already been requested. Please approve or reject it.",
        )

    # Multi-tenant check: STATION_MANAGER can only cancel from their station
    if role_matches(current_user.get("role"), "STATION_MANAGER"):
        if not can_access_station(current_user, str(booking.station_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot request cancellation for booking from another station",
            )

    # Capture old values for audit
    old_values = {
        "status": current_status,
        "cancellation_requested_at": None,
        "cancellation_requested_by": None,
        "cancellation_reason": booking.cancellation_reason,
        "previous_status": booking.previous_status,
    }

    # Update booking
    now = datetime.now(timezone.utc)
    booking.previous_status = current_status  # Store for potential revert
    booking.status = BookingStatus.CANCELLATION_REQUESTED
    booking.cancellation_requested_at = now
    booking.cancellation_requested_by = current_user.get("name") or current_user.get("email")
    booking.cancellation_reason = request_input.reason

    await db.commit()

    # New values for audit
    new_values = {
        "status": BookingStatus.CANCELLATION_REQUESTED.value,
        "cancellation_requested_at": now.isoformat(),
        "cancellation_requested_by": booking.cancellation_requested_by,
        "cancellation_reason": request_input.reason,
        "previous_status": current_status,
    }

    # Log to audit trail
    await audit_logger.log_update(
        session=db,
        user=current_user,
        resource_type="booking",
        resource_id=booking_id,
        resource_name=f"Booking {booking_id[:8]}... - Cancellation Requested",
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request.client else None,
        station_id=str(booking.station_id) if booking.station_id else None,
        metadata={
            "action": "request_cancellation",
            "reason": request_input.reason,
            "slot_held": True,
        },
    )

    logger.info(
        f"📋 Cancellation requested for booking {booking_id} by {current_user.get('name')} - awaiting approval"
    )

    return CancellationResponse(
        success=True,
        message="Cancellation request recorded. Awaiting approval.",
        booking_id=booking_id,
        previous_status=current_status,
        new_status=BookingStatus.CANCELLATION_REQUESTED.value,
        action_by=current_user["id"],
        action_at=now.isoformat() + "Z",
    )


@router.post(
    "/{booking_id}/approve-cancellation",
    status_code=status.HTTP_200_OK,
    summary="Approve booking cancellation (Step 2 of 2 - Approve)",
    description="""
    Approve a pending cancellation request. This releases the slot.

    ## What Happens:
    - Booking status changes from CANCELLATION_REQUESTED to CANCELLED
    - **Slot is RELEASED** (another customer can now book this slot)
    - Cancellation notification sent to customer
    - Action is logged to audit trail

    ## Important:
    This action is **IRREVERSIBLE** for the slot. Once released,
    it may be immediately booked by another customer.
    """,
    response_model=CancellationResponse,
    responses={
        200: {"description": "Cancellation approved", "model": CancellationResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        404: {"description": "Booking not found", "model": ErrorResponse},
    },
)
async def approve_cancellation(
    booking_id: str,
    approval_input: CancellationApprovalInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_customer_support()),
) -> CancellationResponse:
    """Approve cancellation request (Step 2 - releases slot)."""

    # Fetch booking with customer for notification
    query = select(Booking).where(Booking.id == UUID(booking_id))
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Get current status value
    current_status = (
        booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    )

    # Validate status is CANCELLATION_REQUESTED
    if current_status != BookingStatus.CANCELLATION_REQUESTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve cancellation. Booking status is '{current_status}', expected 'cancellation_requested'.",
        )

    # Multi-tenant check
    if role_matches(current_user.get("role"), "STATION_MANAGER"):
        if not can_access_station(current_user, str(booking.station_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot approve cancellation for booking from another station",
            )

    # Capture old values for audit
    old_values = {
        "status": current_status,
        "cancelled_at": None,
        "cancelled_by": None,
        "cancellation_approved_reason": None,
    }

    # Update booking - this releases the slot!
    now = datetime.now(timezone.utc)
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now
    booking.cancelled_by = current_user.get("name") or current_user.get("email")
    booking.cancellation_approved_reason = approval_input.reason

    await db.commit()

    # New values for audit
    new_values = {
        "status": BookingStatus.CANCELLED.value,
        "cancelled_at": now.isoformat(),
        "cancelled_by": booking.cancelled_by,
        "cancellation_approved_reason": approval_input.reason,
    }

    # Log to audit trail
    await audit_logger.log_update(
        session=db,
        user=current_user,
        resource_type="booking",
        resource_id=booking_id,
        resource_name=f"Booking {booking_id[:8]}... - Cancellation Approved",
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request.client else None,
        station_id=str(booking.station_id) if booking.station_id else None,
        metadata={
            "action": "approve_cancellation",
            "approval_reason": approval_input.reason,
            "original_reason": booking.cancellation_reason,
            "slot_released": True,
        },
    )

    # Send cancellation notification asynchronously
    customer_name = (
        decrypt_pii(booking.customer.name_encrypted)
        if hasattr(booking, "customer") and booking.customer and booking.customer.name_encrypted
        else "Customer"
    )
    customer_phone = (
        decrypt_pii(booking.customer.phone_encrypted)
        if hasattr(booking, "customer") and booking.customer and booking.customer.phone_encrypted
        else None
    )

    # Determine refund eligibility
    refund_amount = None
    if booking.total_due_cents and booking.previous_status in ("deposit_paid", "confirmed"):
        refund_amount = booking.total_due_cents / 100.0

    asyncio.create_task(
        notify_cancellation(
            customer_name=customer_name,
            customer_phone=customer_phone,
            booking_id=booking_id,
            event_date=booking.date.strftime("%B %d, %Y") if booking.date else "Unknown Date",
            event_time=booking.slot if booking.slot else "Unknown Time",
            cancellation_reason=booking.cancellation_reason or "Cancellation approved",
            refund_amount=refund_amount,
        )
    )

    logger.info(
        f"✅ Cancellation approved for booking {booking_id} by {current_user.get('name')} - SLOT RELEASED"
    )

    return CancellationResponse(
        success=True,
        message="Cancellation approved. Slot has been released.",
        booking_id=booking_id,
        previous_status=current_status,
        new_status=BookingStatus.CANCELLED.value,
        action_by=current_user["id"],
        action_at=now.isoformat() + "Z",
    )


@router.post(
    "/{booking_id}/reject-cancellation",
    status_code=status.HTTP_200_OK,
    summary="Reject booking cancellation (Step 2 of 2 - Reject)",
    description="""
    Reject a pending cancellation request. This reverts the booking status.

    ## What Happens:
    - Booking status REVERTS to the status it had before cancellation was requested
    - Slot remains HELD (no change to slot availability)
    - Rejection is logged to audit trail

    ## Use Cases:
    - Customer changed their mind and wants to proceed
    - Cancellation request was within no-cancellation window
    - Deposit is non-refundable per policy
    """,
    response_model=CancellationResponse,
    responses={
        200: {"description": "Cancellation rejected", "model": CancellationResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        404: {"description": "Booking not found", "model": ErrorResponse},
    },
)
async def reject_cancellation(
    booking_id: str,
    rejection_input: CancellationRejectionInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_customer_support()),
) -> CancellationResponse:
    """Reject cancellation request (Step 2 - reverts to previous status)."""

    # Fetch booking
    query = select(Booking).where(Booking.id == UUID(booking_id))
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Get current status value
    current_status = (
        booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    )

    # Validate status is CANCELLATION_REQUESTED
    if current_status != BookingStatus.CANCELLATION_REQUESTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject cancellation. Booking status is '{current_status}', expected 'cancellation_requested'.",
        )

    # Multi-tenant check
    if role_matches(current_user.get("role"), "STATION_MANAGER"):
        if not can_access_station(current_user, str(booking.station_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot reject cancellation for booking from another station",
            )

    # Get the status to revert to
    revert_status = booking.previous_status or BookingStatus.CONFIRMED.value

    # Capture old values for audit
    old_values = {
        "status": current_status,
        "cancellation_rejected_at": None,
        "cancellation_rejected_by": None,
        "cancellation_rejection_reason": None,
        "cancellation_requested_at": (
            booking.cancellation_requested_at.isoformat()
            if booking.cancellation_requested_at
            else None
        ),
        "cancellation_reason": booking.cancellation_reason,
    }

    # Update booking - revert status, record rejection
    now = datetime.now(timezone.utc)
    booking.status = BookingStatus(revert_status)
    booking.cancellation_rejected_at = now
    booking.cancellation_rejected_by = current_user.get("name") or current_user.get("email")
    booking.cancellation_rejection_reason = rejection_input.reason
    # Clear request fields
    booking.cancellation_requested_at = None
    booking.cancellation_requested_by = None

    await db.commit()

    # New values for audit
    new_values = {
        "status": revert_status,
        "cancellation_rejected_at": now.isoformat(),
        "cancellation_rejected_by": booking.cancellation_rejected_by,
        "cancellation_rejection_reason": rejection_input.reason,
        "cancellation_requested_at": None,
    }

    # Log to audit trail
    await audit_logger.log_update(
        session=db,
        user=current_user,
        resource_type="booking",
        resource_id=booking_id,
        resource_name=f"Booking {booking_id[:8]}... - Cancellation Rejected",
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request.client else None,
        station_id=str(booking.station_id) if booking.station_id else None,
        metadata={
            "action": "reject_cancellation",
            "rejection_reason": rejection_input.reason,
            "original_reason": old_values.get("cancellation_reason"),
            "reverted_to_status": revert_status,
            "slot_held": True,
        },
    )

    logger.info(
        f"❌ Cancellation rejected for booking {booking_id} by {current_user.get('name')} - reverted to '{revert_status}'"
    )

    return CancellationResponse(
        success=True,
        message=f"Cancellation rejected. Booking status reverted to '{revert_status}'.",
        booking_id=booking_id,
        previous_status=current_status,
        new_status=revert_status,
        action_by=current_user["id"],
        action_at=now.isoformat() + "Z",
    )
