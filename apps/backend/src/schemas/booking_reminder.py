"""
Booking Reminder Schemas
Pydantic models for request/response validation.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from models.booking_reminder import ReminderType, ReminderStatus


class BookingReminderBase(BaseModel):
    """Base schema for booking reminders"""
    reminder_type: ReminderType = Field(..., description="Type of reminder (email, sms, both)")
    scheduled_for: datetime = Field(..., description="When to send the reminder (ISO 8601 format)")
    message: Optional[str] = Field(None, description="Custom message content")
    
    @field_validator('scheduled_for')
    @classmethod
    def validate_scheduled_for(cls, v: datetime) -> datetime:
        """Ensure scheduled_for is in the future"""
        # Make comparison timezone-aware
        now = datetime.now(timezone.utc)
        # If v is naive, make it UTC-aware
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < now:
            raise ValueError("scheduled_for must be in the future")
        return v


class BookingReminderCreate(BookingReminderBase):
    """Schema for creating a booking reminder"""
    booking_id: int = Field(..., description="ID of the booking to remind about")


class BookingReminderUpdate(BaseModel):
    """Schema for updating a booking reminder"""
    reminder_type: Optional[ReminderType] = None
    scheduled_for: Optional[datetime] = None
    message: Optional[str] = None
    status: Optional[ReminderStatus] = None
    
    @field_validator('scheduled_for')
    @classmethod
    def validate_scheduled_for(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled_for is in the future"""
        if v is not None:
            # Make comparison timezone-aware
            now = datetime.now(timezone.utc)
            # If v is naive, make it UTC-aware
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            if v < now:
                raise ValueError("scheduled_for must be in the future")
        return v


class BookingReminderResponse(BookingReminderBase):
    """Schema for booking reminder response"""
    id: UUID
    booking_id: int
    sent_at: Optional[datetime] = None
    status: ReminderStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookingReminderListResponse(BaseModel):
    """Schema for list of booking reminders"""
    reminders: list[BookingReminderResponse]
    total: int
    page: int = 1
    page_size: int = 50
