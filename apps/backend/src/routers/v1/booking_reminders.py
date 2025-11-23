"""
Booking Reminder Endpoints
REST API for managing booking reminders.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.feature_flags import FeatureFlag, require_feature
from models.booking_reminder import ReminderStatus
from schemas.booking_reminder import (
    BookingReminderCreate,
    BookingReminderListResponse,
    BookingReminderResponse,
    BookingReminderUpdate,
)
from services.booking_reminder_service import BookingReminderService

router = APIRouter(prefix="/bookings", tags=["booking-reminders"])


@router.post(
    "/{booking_id}/reminders",
    response_model=BookingReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create booking reminder",
    description="Create a new reminder for a booking (email/SMS notification)"
)
@require_feature(FeatureFlag.BOOKING_REMINDERS)
async def create_booking_reminder(
    booking_id: int,
    reminder_data: BookingReminderCreate,
    db: AsyncSession = Depends(get_db)
) -> BookingReminderResponse:
    """
    Create a new booking reminder.
    
    The reminder will be sent at the scheduled time via email, SMS, or both.
    
    **Feature Flag**: `FEATURE_FLAG_BOOKING_REMINDERS`
    
    **Request Body**:
    ```json
    {
        "booking_id": "uuid",
        "reminder_type": "email",  // "email", "sms", or "both"
        "scheduled_for": "2025-12-24T10:00:00Z",
        "message": "Optional custom message"
    }
    ```
    
    **Returns**: Created reminder with status "pending"
    """
    # Override booking_id from path
    reminder_data.booking_id = booking_id
    
    service = BookingReminderService(db)
    
    try:
        reminder = await service.create_reminder(reminder_data)
        return BookingReminderResponse.model_validate(reminder)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{booking_id}/reminders",
    response_model=BookingReminderListResponse,
    summary="List booking reminders",
    description="Get all reminders for a specific booking"
)
@require_feature(FeatureFlag.BOOKING_REMINDERS)
async def list_booking_reminders(
    booking_id: int,
    status_filter: Optional[ReminderStatus] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> BookingReminderListResponse:
    """
    List all reminders for a booking.
    
    **Feature Flag**: `FEATURE_FLAG_BOOKING_REMINDERS`
    
    **Query Parameters**:
    - status: Filter by status (pending, sent, failed, cancelled)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    
    **Returns**: Paginated list of reminders
    """
    service = BookingReminderService(db)
    
    reminders, total = await service.list_reminders(
        booking_id=booking_id,
        status=status_filter,
        page=page,
        page_size=page_size
    )
    
    return BookingReminderListResponse(
        reminders=[BookingReminderResponse.model_validate(r) for r in reminders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{booking_id}/reminders/{reminder_id}",
    response_model=BookingReminderResponse,
    summary="Get booking reminder",
    description="Get a specific reminder by ID"
)
@require_feature(FeatureFlag.BOOKING_REMINDERS)
async def get_booking_reminder(
    booking_id: int,
    reminder_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> BookingReminderResponse:
    """
    Get a specific booking reminder.
    
    **Feature Flag**: `FEATURE_FLAG_BOOKING_REMINDERS`
    
    **Returns**: Reminder details
    """
    service = BookingReminderService(db)
    
    reminder = await service.get_reminder(reminder_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found"
        )
    
    if reminder.booking_id != booking_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} does not belong to booking {booking_id}"
        )
    
    return BookingReminderResponse.model_validate(reminder)


@router.put(
    "/{booking_id}/reminders/{reminder_id}",
    response_model=BookingReminderResponse,
    summary="Update booking reminder",
    description="Update a reminder (reschedule, change message, etc.)"
)
@require_feature(FeatureFlag.BOOKING_REMINDERS)
async def update_booking_reminder(
    booking_id: int,
    reminder_id: UUID,
    update_data: BookingReminderUpdate,
    db: AsyncSession = Depends(get_db)
) -> BookingReminderResponse:
    """
    Update a booking reminder.
    
    **Feature Flag**: `FEATURE_FLAG_BOOKING_REMINDERS`
    
    **Request Body** (all fields optional):
    ```json
    {
        "reminder_type": "sms",
        "scheduled_for": "2025-12-25T10:00:00Z",
        "message": "Updated message",
        "status": "cancelled"
    }
    ```
    
    **Returns**: Updated reminder
    """
    service = BookingReminderService(db)
    
    # Verify reminder exists and belongs to booking
    existing = await service.get_reminder(reminder_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found"
        )
    
    if existing.booking_id != booking_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} does not belong to booking {booking_id}"
        )
    
    try:
        reminder = await service.update_reminder(reminder_id, update_data)
        return BookingReminderResponse.model_validate(reminder)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{booking_id}/reminders/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel booking reminder",
    description="Cancel a pending reminder"
)
@require_feature(FeatureFlag.BOOKING_REMINDERS)
async def cancel_booking_reminder(
    booking_id: int,
    reminder_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Cancel a booking reminder.
    
    **Feature Flag**: `FEATURE_FLAG_BOOKING_REMINDERS`
    
    **Note**: Can only cancel reminders with status "pending".
    Already sent reminders cannot be cancelled.
    
    **Returns**: 204 No Content on success
    """
    service = BookingReminderService(db)
    
    # Verify reminder exists and belongs to booking
    existing = await service.get_reminder(reminder_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found"
        )
    
    if existing.booking_id != booking_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} does not belong to booking {booking_id}"
        )
    
    try:
        await service.cancel_reminder(reminder_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
