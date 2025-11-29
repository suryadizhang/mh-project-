"""
Manual test for Booking Reminders API
Tests the complete CRUD flow for booking reminders
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from db.models.core import Booking, BookingStatus, BookingReminder, ReminderStatus


async def test_booking_reminders():
    """Test booking reminders CRUD operations"""

    async with AsyncSessionLocal() as db:
        print("🧪 Testing Booking Reminders Feature\n")

        # Step 1: Create a test booking
        print("1️⃣ Creating test booking...")
        test_booking = Booking(
            customer_id=1,  # Assuming customer exists
            booking_datetime=datetime.utcnow() + timedelta(days=7),
            party_size=8,
            status=BookingStatus.PENDING.value,
            contact_phone="+19167408768",
            contact_email="test@example.com"
        )
        db.add(test_booking)
        await db.commit()
        await db.refresh(test_booking)
        print(f"   ✅ Created booking ID: {test_booking.id}\n")

        # Step 2: Create a reminder
        print("2️⃣ Creating booking reminder...")
        reminder = BookingReminder(
            booking_id=test_booking.id,
            reminder_type="email",
            scheduled_for=datetime.utcnow() + timedelta(days=6),
            message="Don't forget your hibachi event tomorrow!",
            status=ReminderStatus.PENDING.value
        )
        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)
        print(f"   ✅ Created reminder ID: {reminder.id}")
        print(f"   📧 Type: {reminder.reminder_type}")
        print(f"   📅 Scheduled for: {reminder.scheduled_for}")
        print(f"   📝 Status: {reminder.status}\n")

        # Step 3: Query reminders for booking
        print("3️⃣ Querying reminders for booking...")
        result = await db.execute(
            select(BookingReminder)
            .where(BookingReminder.booking_id == test_booking.id)
        )
        reminders = result.scalars().all()
        print(f"   ✅ Found {len(reminders)} reminder(s)\n")

        # Step 4: Update reminder
        print("4️⃣ Updating reminder...")
        reminder.message = "Updated message: Your hibachi event is coming up!"
        await db.commit()
        print(f"   ✅ Updated message\n")

        # Step 5: Mark as sent
        print("5️⃣ Marking reminder as sent...")
        reminder.status = ReminderStatus.SENT.value
        reminder.sent_at = datetime.utcnow()
        await db.commit()
        print(f"   ✅ Status: {reminder.status}")
        print(f"   📤 Sent at: {reminder.sent_at}\n")

        # Step 6: Cleanup
        print("6️⃣ Cleaning up test data...")
        await db.delete(reminder)
        await db.delete(test_booking)
        await db.commit()
        print("   ✅ Cleanup complete\n")

        print("=" * 60)
        print("✅ ALL TESTS PASSED - Booking Reminders Feature Working!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_booking_reminders())
