"""
Booking Reminder Service
Business logic for managing booking reminders.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.core import Booking

# MIGRATED: from models.booking_reminder → db.models.booking_reminder
from db.models.booking_reminder import BookingReminder, ReminderStatus
from schemas.booking_reminder import BookingReminderCreate, BookingReminderUpdate


class BookingReminderService:
    """Service for managing booking reminders"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reminder(self, data: BookingReminderCreate) -> BookingReminder:
        """
        Create a new booking reminder.

        Args:
            data: Reminder creation data

        Returns:
            Created reminder

        Raises:
            ValueError: If booking doesn't exist
        """
        # Verify booking exists
        booking_result = await self.db.execute(select(Booking).where(Booking.id == data.booking_id))
        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise ValueError(f"Booking {data.booking_id} not found")

        # Create reminder
        reminder = BookingReminder(
            booking_id=data.booking_id,
            reminder_type=data.reminder_type.value,
            scheduled_for=data.scheduled_for,
            message=data.message,
            status=ReminderStatus.PENDING.value,
        )

        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)

        # TODO: Schedule Celery task to send reminder at scheduled_for time
        # from tasks.send_reminder import send_reminder_task
        # send_reminder_task.apply_async(
        #     args=[str(reminder.id)],
        #     eta=data.scheduled_for
        # )

        return reminder

    async def get_reminder(self, reminder_id: UUID) -> Optional[BookingReminder]:
        """
        Get reminder by ID.

        Args:
            reminder_id: Reminder ID

        Returns:
            Reminder or None
        """
        result = await self.db.execute(
            select(BookingReminder)
            .options(selectinload(BookingReminder.booking))
            .where(BookingReminder.id == reminder_id)
        )
        return result.scalar_one_or_none()

    async def list_reminders(
        self,
        booking_id: Optional[int] = None,
        status: Optional[ReminderStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[BookingReminder], int]:
        """
        List reminders with optional filtering.

        Args:
            booking_id: Filter by booking ID
            status: Filter by status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (reminders, total_count)
        """
        # Build query
        query = select(BookingReminder).options(selectinload(BookingReminder.booking))

        if booking_id:
            query = query.where(BookingReminder.booking_id == booking_id)

        if status:
            query = query.where(BookingReminder.status == status.value)

        # Get total count
        count_query = select(BookingReminder)
        if booking_id:
            count_query = count_query.where(BookingReminder.booking_id == booking_id)
        if status:
            count_query = count_query.where(BookingReminder.status == status.value)

        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(BookingReminder.scheduled_for.asc())

        # Execute
        result = await self.db.execute(query)
        reminders = result.scalars().all()

        return list(reminders), total

    async def update_reminder(
        self, reminder_id: UUID, data: BookingReminderUpdate
    ) -> Optional[BookingReminder]:
        """
        Update a reminder.

        Args:
            reminder_id: Reminder ID
            data: Update data

        Returns:
            Updated reminder or None
        """
        reminder = await self.get_reminder(reminder_id)
        if not reminder:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(reminder, field):
                if isinstance(value, (ReminderStatus, str)) and field in [
                    "status",
                    "reminder_type",
                ]:
                    setattr(reminder, field, value.value if hasattr(value, "value") else value)
                else:
                    setattr(reminder, field, value)

        reminder.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(reminder)

        return reminder

    async def cancel_reminder(self, reminder_id: UUID) -> Optional[BookingReminder]:
        """
        Cancel a reminder.

        Args:
            reminder_id: Reminder ID

        Returns:
            Cancelled reminder or None
        """
        reminder = await self.get_reminder(reminder_id)
        if not reminder:
            return None

        if reminder.status == ReminderStatus.SENT.value:
            raise ValueError("Cannot cancel a reminder that has already been sent")

        reminder.status = ReminderStatus.CANCELLED.value
        reminder.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(reminder)

        # TODO: Cancel Celery task if not yet sent
        # from celery import current_app
        # current_app.control.revoke(task_id, terminate=True)

        return reminder

    async def mark_as_sent(
        self, reminder_id: UUID, error_message: Optional[str] = None
    ) -> Optional[BookingReminder]:
        """
        Mark reminder as sent (or failed).

        Args:
            reminder_id: Reminder ID
            error_message: Error message if failed

        Returns:
            Updated reminder or None
        """
        reminder = await self.get_reminder(reminder_id)
        if not reminder:
            return None

        if error_message:
            reminder.status = ReminderStatus.FAILED.value
            reminder.error_message = error_message
        else:
            reminder.status = ReminderStatus.SENT.value
            reminder.sent_at = datetime.utcnow()

        reminder.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(reminder)

        return reminder

    async def delete_reminder(self, reminder_id: UUID) -> bool:
        """
        Delete a reminder.

        Args:
            reminder_id: Reminder ID

        Returns:
            True if deleted, False if not found
        """
        reminder = await self.get_reminder(reminder_id)
        if not reminder:
            return False

        await self.db.delete(reminder)
        await self.db.commit()

        return True
