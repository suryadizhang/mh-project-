"""
Booking Delete Endpoint
=======================

Handles soft-delete operations with:
- RBAC authorization
- Multi-tenant isolation
- Audit trail logging
- GDPR/SOC 2/PCI DSS compliance

File Size: ~200 lines (within 500 line limit)
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.audit_logger import audit_logger
from core.database import get_db
from core.security.roles import role_matches
from services.encryption_service import SecureDataHandler
from db.models.core import Booking, BookingStatus
from utils.auth import can_access_station, require_customer_support

from .constants import RESTORE_WINDOW_DAYS
from .notifications import notify_cancellation
from .schemas import DeleteBookingResponse

router = APIRouter(tags=["bookings"])
logger = logging.getLogger(__name__)


@router.delete(
    "/{booking_id}",
    response_model=DeleteBookingResponse,
    summary="Soft-delete a booking",
    description="""
    Soft-delete a booking (mark as deleted without permanent removal).

    ## Authorization
    Requires one of these roles:
    - **SUPER_ADMIN**: Can delete any booking
    - **ADMIN**: Can delete any booking
    - **CUSTOMER_SUPPORT**: Can delete any booking
    - **STATION_MANAGER**: Can only delete bookings from their assigned stations

    ## Audit Trail
    All deletions are logged with:
    - Who deleted (user ID, role)
    - When deleted (timestamp)
    - Why deleted (reason)
    - Previous state (for recovery)

    ## Recovery
    Soft-deleted bookings can be restored within 30 days.
    After 30 days, they are permanently purged.

    ## Compliance
    - GDPR: Audit trail for data deletion requests
    - SOC 2: Access control and logging
    - PCI DSS: Cardholder data handling
    """,
    responses={
        200: {"description": "Booking soft-deleted successfully"},
        403: {"description": "Not authorized to delete this booking"},
        404: {"description": "Booking not found"},
        422: {"description": "Cannot delete booking in current state"},
    },
)
async def delete_booking(
    booking_id: str,
    reason: str = "Customer request",
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_customer_support),
) -> DeleteBookingResponse:
    """
    Soft-delete a booking with full audit trail.

    Multi-tenant: STATION_MANAGER can only delete from their stations.
    """
    user_id = current_user.get("id")
    user_role = current_user.get("role", "")

    # Fetch booking with customer for notification
    result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.customer))
        .where(
            Booking.id == UUID(booking_id),
            Booking.deleted_at.is_(None),
        )
    )
    booking = result.unique().scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or already deleted",
        )

    # Multi-tenant authorization check
    if role_matches(user_role, "STATION_MANAGER", "station_manager"):
        station_ids = current_user.get("station_ids", [])
        booking_station_id = str(booking.station_id) if booking.station_id else None

        if not await can_access_station(booking_station_id, station_ids):
            logger.warning(
                f"🚫 Station manager {user_id} attempted to delete booking "
                f"from unauthorized station {booking_station_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete bookings from this station",
            )

    # Capture pre-deletion state for audit
    old_values = {
        "id": str(booking.id),
        "customer_id": str(booking.customer_id),
        "station_id": str(booking.station_id) if booking.station_id else None,
        "date": booking.date.isoformat() if booking.date else None,
        "slot": booking.slot.strftime("%H:%M") if booking.slot else None,
        "status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        "total_due_cents": booking.total_due_cents,
        "deposit_due_cents": booking.deposit_due_cents,
    }

    # Perform soft delete
    now = datetime.now(timezone.utc)
    restore_until = now + timedelta(days=RESTORE_WINDOW_DAYS)

    booking.deleted_at = now
    booking.deleted_by = UUID(user_id) if user_id else None
    booking.delete_reason = reason
    booking.status = BookingStatus.CANCELLED

    await db.commit()

    # Log to audit trail
    await audit_logger.log_delete(
        db=db,
        entity_type="booking",
        entity_id=str(booking.id),
        user_id=user_id,
        user_role=user_role,
        reason=reason,
        old_values=old_values,
        restore_until=restore_until,
    )

    logger.info(
        f"🗑️ Booking {booking_id} soft-deleted by {user_role} {user_id}. "
        f"Reason: {reason}. Restore until: {restore_until.isoformat()}"
    )

    # Send notification asynchronously (non-blocking)
    try:
        encryption_handler = SecureDataHandler()
        customer_phone = (
            encryption_handler.decrypt_phone(booking.customer.phone_encrypted)
            if booking.customer and booking.customer.phone_encrypted
            else None
        )
        customer_name = (
            f"{booking.customer.first_name} {booking.customer.last_name}".strip()
            if booking.customer
            else "Unknown"
        )

        if customer_phone:
            asyncio.create_task(
                notify_cancellation(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    booking_id=booking_id,
                    event_date=booking.date.isoformat() if booking.date else "Unknown",
                    event_time=booking.slot.strftime("%H:%M") if booking.slot else "Unknown",
                    cancelled_by=f"{user_role} ({user_id[:8]}...)",
                    reason=reason,
                )
            )
    except Exception as e:
        # Non-blocking: log but don't fail the delete
        logger.warning(f"Failed to send cancellation notification: {e}")

    return DeleteBookingResponse(
        success=True,
        message="Booking soft-deleted successfully",
        booking_id=booking_id,
        deleted_at=now.isoformat(),
        deleted_by=user_id,
        restore_until=restore_until.isoformat(),
        reason=reason,
    )
