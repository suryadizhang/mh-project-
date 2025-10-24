"""
Simple test data seeder for MyHibachi CRM
Creates basic test data for API performance testing
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.app.database import Base, engine
from api.app.models.booking_models import LegacyUser, UserRole, LegacyBooking, BookingStatus, TimeSlotEnum
from api.app.models.stripe_models import StripePayment, StripeCustomer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from faker import Faker

fake = Faker()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_test_data():
    """Seed the database with test data."""
    print("Starting test data seeding...")
    print(f"Using database: {engine.url}")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Create test admin user
            print("\n1. Creating admin user...")
            admin_user = LegacyUser(
                id="admin-123-456",
                email="admin@myhibachi.com",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XGvA8qBYMwBK",  # "admin123"
                first_name="Admin",
                last_name="User",
                phone="+1234567890",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            session.add(admin_user)
            
            # 2. Create test customers
            print("2. Creating 100 customers...")
            customers = []
            for i in range(100):
                customer = LegacyUser(
                    id=f"customer-{i+1}",
                    email=f"customer{i+1}@example.com",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XGvA8qBYMwBK",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone=fake.phone_number()[:20],
                    role=UserRole.CUSTOMER,
                    is_active=True,
                    is_verified=True
                )
                customers.append(customer)
                session.add(customer)
            
            await session.flush()
            
            # 3. Create Stripe customers
            print("3. Creating 100 Stripe customer records...")
            for i, user in enumerate(customers):
                stripe_customer = StripeCustomer(
                    id=f"cust-stripe-{i+1}",
                    user_id=user.id,
                    email=user.email,
                    stripe_customer_id=f"cus_test_{i+1}",
                    name=f"{user.first_name} {user.last_name}",
                    phone=user.phone,
                    preferred_payment_method=random.choice(["stripe", "zelle", "venmo"]),
                    total_spent=Decimal(random.randint(0, 5000)),
                    total_bookings=random.randint(0, 20),
                    zelle_savings=Decimal(random.randint(0, 500)),
                    loyalty_tier=random.choice(["bronze", "silver", "gold", "platinum"])
                )
                session.add(stripe_customer)
            
            await session.flush()
            
            # 4. Create bookings
            print("4. Creating 500 bookings...")
            bookings = []
            base_date = datetime.now() - timedelta(days=365)
            
            for i in range(500):
                customer = random.choice(customers)
                event_date = base_date + timedelta(days=random.randint(0, 730))  # 2 years range
                
                booking = LegacyBooking(
                    id=f"booking-{i+1}",
                    booking_reference=f"MH-{datetime.now().year}-{i+1:04d}",
                    user_id=customer.id,
                    customer_name=f"{customer.first_name} {customer.last_name}",
                    customer_email=customer.email,
                    customer_phone=customer.phone,
                    event_date=event_date.date(),
                    event_time=random.choice([TimeSlotEnum.SLOT_12PM, TimeSlotEnum.SLOT_3PM, TimeSlotEnum.SLOT_6PM, TimeSlotEnum.SLOT_9PM]),
                    guest_count=random.randint(4, 20),
                    venue_street=fake.street_address(),
                    venue_city=fake.city(),
                    venue_state="CA",
                    venue_zipcode=fake.zipcode()[:10],
                    status=random.choice([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.CANCELLED]),
                    total_amount=Decimal(random.randint(200, 2000)),
                    deposit_amount=Decimal(100),
                    deposit_paid=random.choice([True, False]),
                    remaining_balance=Decimal(random.randint(0, 1900))
                )
                bookings.append(booking)
                session.add(booking)
            
            await session.flush()
            
            # 5. Create payments
            print("5. Creating 300 payments...")
            for i in range(300):
                booking = random.choice(bookings)
                payment = StripePayment(
                    id=f"payment-{i+1}",
                    user_id=booking.user_id,
                    booking_id=booking.id,
                    stripe_payment_intent_id=f"pi_test_{i+1}",
                    stripe_customer_id=None,  # Can be null
                    amount=Decimal(random.randint(50, 500)),
                    currency="usd",
                    status=random.choice(["succeeded", "pending", "failed"]),
                    method=random.choice(["stripe", "zelle", "venmo"]),
                    payment_type=random.choice(["deposit", "balance", "full"]),
                    description=f"Payment for booking {booking.booking_reference}"
                )
                session.add(payment)
            
            # Commit all data
            await session.commit()
            print("\n[SUCCESS] Test data seeding complete!")
            print("Summary:")
            print(f"  - 1 admin user")
            print(f"  - 100 customer users")
            print(f"  - 100 Stripe customer records")
            print(f"  - 500 bookings")
            print(f"  - 300 payments")
            
        except Exception as e:
            await session.rollback()
            print(f"\n[ERROR] Failed to seed data: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_test_data())
    print("\n[COMPLETE] Database is ready for testing!")
