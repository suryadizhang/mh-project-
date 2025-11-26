"""
Seed Test Data for Development and Testing
Creates realistic test data for all features including booking reminders.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models import (
    Booking,
    BookingStatus,
    Customer,
    CustomerStatus,
    Payment,
    PaymentStatus,
)


async def seed_test_data():
    """Seed comprehensive test data"""
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n" + "=" * 60)
        print("🌱 SEEDING TEST DATA")
        print("=" * 60)
        
        # 1. Create test customers
        print("\n📋 Creating test customers...")
        
        customers_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-0101",
                "status": CustomerStatus.ACTIVE,
                "email_notifications": True,
                "sms_notifications": True,
                "loyalty_points": 100,
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "phone": "+1-555-0102",
                "status": CustomerStatus.VIP,
                "email_notifications": True,
                "sms_notifications": False,
                "loyalty_points": 500,
            },
            {
                "first_name": "Bob",
                "last_name": "Johnson",
                "email": "bob.johnson@example.com",
                "phone": "+1-555-0103",
                "status": CustomerStatus.ACTIVE,
                "email_notifications": False,
                "sms_notifications": True,
                "loyalty_points": 50,
            },
        ]
        
        customers = []
        for cust_data in customers_data:
            # Check if customer exists
            result = await session.execute(
                select(Customer).where(Customer.email == cust_data["email"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  ✓ Customer {cust_data['email']} already exists (ID: {existing.id})")
                customers.append(existing)
            else:
                customer = Customer(**cust_data)
                session.add(customer)
                await session.flush()  # Get ID
                customers.append(customer)
                print(f"  + Created customer {cust_data['email']} (ID: {customer.id})")
        
        await session.commit()
        
        # 2. Create test bookings
        print("\n📅 Creating test bookings...")
        
        now = datetime.now(timezone.utc)
        
        bookings_data = [
            {
                "customer_id": customers[0].id,
                "event_date": now + timedelta(days=7),
                "event_time": "18:00:00",
                "guest_count": 10,
                "location_address": "123 Main St, Anytown, USA",
                "status": BookingStatus.PENDING,
                "total_amount": 50000,  # $500.00
                "deposit_amount": 10000,  # $100.00
                "special_requests": "Vegetarian options needed",
            },
            {
                "customer_id": customers[1].id,
                "event_date": now + timedelta(days=14),
                "event_time": "19:00:00",
                "guest_count": 20,
                "location_address": "456 Oak Ave, Another City, USA",
                "status": BookingStatus.CONFIRMED,
                "total_amount": 100000,  # $1000.00
                "deposit_amount": 20000,  # $200.00
                "special_requests": "Birthday celebration - need cake",
            },
            {
                "customer_id": customers[2].id,
                "event_date": now + timedelta(days=3),
                "event_time": "17:30:00",
                "guest_count": 8,
                "location_address": "789 Pine Rd, Somewhere, USA",
                "status": BookingStatus.PENDING,
                "total_amount": 40000,  # $400.00
                "deposit_amount": 8000,  # $80.00
                "special_requests": None,
            },
            {
                "customer_id": customers[0].id,
                "event_date": now + timedelta(days=21),
                "event_time": "18:30:00",
                "guest_count": 15,
                "location_address": "123 Main St, Anytown, USA",
                "status": BookingStatus.PENDING,
                "total_amount": 75000,  # $750.00
                "deposit_amount": 15000,  # $150.00
                "special_requests": "Anniversary dinner",
            },
        ]
        
        bookings = []
        for i, booking_data in enumerate(bookings_data, 1):
            # Check if booking exists by checking for bookings with same customer and date
            result = await session.execute(
                select(Booking).where(
                    Booking.customer_id == booking_data["customer_id"],
                    Booking.event_date == booking_data["event_date"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  ✓ Booking #{existing.id} already exists")
                bookings.append(existing)
            else:
                booking = Booking(**booking_data)
                session.add(booking)
                await session.flush()
                bookings.append(booking)
                print(f"  + Created booking #{booking.id} for {booking.event_date.date()} @ {booking.event_time}")
        
        await session.commit()
        
        # 3. Create test payments
        print("\n💳 Creating test payments...")
        
        for booking in bookings:
            # Check if payment exists
            result = await session.execute(
                select(Payment).where(Payment.booking_id == booking.id)
            )
            existing_payment = result.scalar_one_or_none()
            
            if existing_payment:
                print(f"  ✓ Payment for booking #{booking.id} already exists")
            else:
                payment = Payment(
                    booking_id=booking.id,
                    amount=booking.deposit_amount,
                    status=PaymentStatus.COMPLETED if booking.status == BookingStatus.CONFIRMED else PaymentStatus.PENDING,
                    payment_method="stripe",
                    transaction_id=f"test_txn_{booking.id}_{int(now.timestamp())}",
                    paid_at=now if booking.status == BookingStatus.CONFIRMED else None,
                )
                session.add(payment)
                print(f"  + Created payment for booking #{booking.id} (${payment.amount/100:.2f})")
        
        await session.commit()
        
        # 4. Summary
        print("\n" + "=" * 60)
        print("✅ TEST DATA SEEDING COMPLETE")
        print("=" * 60)
        
        # Get counts
        customer_count = await session.execute(select(Customer))
        booking_count = await session.execute(select(Booking))
        payment_count = await session.execute(select(Payment))
        
        print(f"\n📊 Database Summary:")
        print(f"  • Customers: {len(customer_count.all())}")
        print(f"  • Bookings: {len(booking_count.all())}")
        print(f"  • Payments: {len(payment_count.all())}")
        
        print(f"\n🎯 Test Booking IDs for API Testing:")
        for booking in bookings:
            status_icon = "✅" if booking.status == BookingStatus.CONFIRMED else "⏳"
            print(f"  {status_icon} Booking #{booking.id} - {booking.event_date.date()} @ {booking.event_time} ({booking.guest_count} guests)")
        
        print(f"\n📝 Example API Test Commands:")
        if bookings:
            first_booking_id = bookings[0].id
            print(f"""
  # Create reminder for booking #{first_booking_id}:
  curl -X POST http://localhost:8000/api/v1/bookings/{first_booking_id}/reminders \\
    -H "Content-Type: application/json" \\
    -d '{{
      "booking_id": {first_booking_id},
      "reminder_type": "email",
      "scheduled_for": "{(now + timedelta(days=1)).isoformat()}",
      "message": "Don't forget your hibachi event tomorrow!"
    }}'
  
  # Or use the test script:
  python tests/manual/test_api_reminders.py
  
  # Or use Swagger UI:
  http://localhost:8000/docs
            """)
        
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_test_data())
