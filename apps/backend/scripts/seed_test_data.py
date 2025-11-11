#!/usr/bin/env python3
"""
MyHibachi Test Data Seeding Script

This script populates the database with realistic test data for development
and testing purposes.

Usage:
    python scripts/seed_test_data.py

Requirements:
    - Database must exist and migrations must be run
    - .env file must be configured with DATABASE_URL
    - Dependencies: faker, sqlalchemy, asyncio

Data Generated:
    - 10 stations (different locations)
    - 1,000 customers (realistic profiles)
    - 5,000 bookings (last 2 years, various statuses)
    - 3,000 payments (associated with bookings)
    - Stripe customer and payment intent records
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from random import choice, randint, random, sample
from typing import List

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Initialize Faker
fake = Faker()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in environment variables")
    print("Please create a .env file with DATABASE_URL=postgresql://...")
    sys.exit(1)

# Convert postgres:// to postgresql:// if needed
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create async engine
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Booking statuses
BOOKING_STATUSES = ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']
PAYMENT_STATUSES = ['pending', 'succeeded', 'failed', 'refunded']


class DataSeeder:
    """Handles seeding of test data into the database."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.station_ids = []
        self.customer_ids = []
        self.booking_ids = []
    
    async def clear_existing_data(self):
        """Clear existing test data (optional - use with caution!)."""
        print("⚠️  Clearing existing data...")
        
        # Delete in reverse order of foreign key dependencies
        await self.session.execute(text("DELETE FROM stripe_payment_intents"))
        await self.session.execute(text("DELETE FROM payments"))
        await self.session.execute(text("DELETE FROM stripe_customers"))
        await self.session.execute(text("DELETE FROM bookings"))
        await self.session.execute(text("DELETE FROM customers"))
        await self.session.execute(text("DELETE FROM stations"))
        
        await self.session.commit()
        print("✅ Existing data cleared")
    
    async def seed_stations(self, count: int = 10):
        """Create test station records."""
        print(f"🏢 Creating {count} stations...")
        
        station_names = [
            "Downtown Hibachi Grill",
            "Westside Japanese BBQ",
            "Eastside Teppanyaki",
            "Northgate Hibachi House",
            "Southpark Grill Station",
            "Midtown Teppan Corner",
            "Harbor View Hibachi",
            "Riverside Japanese Grill",
            "Mountain View Teppanyaki",
            "Lakeside Hibachi Express"
        ]
        
        for i in range(count):
            result = await self.session.execute(
                text("""
                    INSERT INTO stations (
                        name, address, city, state, zip_code,
                        phone, email, capacity, is_active,
                        created_at, updated_at
                    )
                    VALUES (
                        :name, :address, :city, :state, :zip_code,
                        :phone, :email, :capacity, :is_active,
                        :created_at, :updated_at
                    )
                    RETURNING id
                """),
                {
                    'name': station_names[i] if i < len(station_names) else f"Station {i+1}",
                    'address': fake.street_address(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'zip_code': fake.zipcode(),
                    'phone': fake.phone_number()[:20],
                    'email': fake.email(),
                    'capacity': randint(20, 100),
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            )
            station_id = result.scalar()
            self.station_ids.append(station_id)
        
        await self.session.commit()
        print(f"✅ Created {count} stations")
    
    async def seed_customers(self, count: int = 1000):
        """Create test customer records."""
        print(f"👥 Creating {count} customers...")
        
        for i in range(count):
            # Create customer
            result = await self.session.execute(
                text("""
                    INSERT INTO customers (
                        first_name, last_name, email, phone,
                        address, city, state, zip_code,
                        created_at, updated_at
                    )
                    VALUES (
                        :first_name, :last_name, :email, :phone,
                        :address, :city, :state, :zip_code,
                        :created_at, :updated_at
                    )
                    RETURNING id
                """),
                {
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'email': fake.email(),
                    'phone': fake.phone_number()[:20],
                    'address': fake.street_address() if random() > 0.3 else None,
                    'city': fake.city() if random() > 0.3 else None,
                    'state': fake.state_abbr() if random() > 0.3 else None,
                    'zip_code': fake.zipcode() if random() > 0.3 else None,
                    'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
                    'updated_at': datetime.utcnow()
                }
            )
            customer_id = result.scalar()
            self.customer_ids.append(customer_id)
            
            # Create Stripe customer record
            await self.session.execute(
                text("""
                    INSERT INTO stripe_customers (
                        customer_id, stripe_customer_id,
                        created_at, updated_at
                    )
                    VALUES (
                        :customer_id, :stripe_customer_id,
                        :created_at, :updated_at
                    )
                """),
                {
                    'customer_id': customer_id,
                    'stripe_customer_id': f"cus_test_{fake.uuid4()[:24]}",
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            )
            
            # Commit every 100 customers to avoid memory issues
            if (i + 1) % 100 == 0:
                await self.session.commit()
                print(f"   Progress: {i + 1}/{count} customers created...")
        
        await self.session.commit()
        print(f"✅ Created {count} customers")
    
    async def seed_bookings(self, count: int = 5000):
        """Create test booking records."""
        print(f"📅 Creating {count} bookings...")
        
        if not self.station_ids or not self.customer_ids:
            print("❌ ERROR: Must seed stations and customers first")
            return
        
        # Generate bookings over last 2 years
        start_date = datetime.utcnow() - timedelta(days=730)
        end_date = datetime.utcnow() + timedelta(days=30)  # Some future bookings
        
        for i in range(count):
            booking_date = fake.date_time_between(start_date=start_date, end_date=end_date)
            status = choice(BOOKING_STATUSES)
            
            # Past bookings more likely to be completed/cancelled
            if booking_date < datetime.utcnow() - timedelta(days=7):
                status = choice(['completed', 'completed', 'completed', 'cancelled', 'no_show'])
            # Future bookings more likely to be pending/confirmed
            elif booking_date > datetime.utcnow():
                status = choice(['pending', 'confirmed', 'confirmed'])
            
            result = await self.session.execute(
                text("""
                    INSERT INTO bookings (
                        customer_id, station_id, booking_date, party_size,
                        status, special_requests, total_amount,
                        created_at, updated_at
                    )
                    VALUES (
                        :customer_id, :station_id, :booking_date, :party_size,
                        :status, :special_requests, :total_amount,
                        :created_at, :updated_at
                    )
                    RETURNING id
                """),
                {
                    'customer_id': choice(self.customer_ids),
                    'station_id': choice(self.station_ids),
                    'booking_date': booking_date,
                    'party_size': randint(1, 12),
                    'status': status,
                    'special_requests': fake.sentence() if random() > 0.7 else None,
                    'total_amount': round(Decimal(randint(50, 500)), 2),
                    'created_at': booking_date - timedelta(days=randint(1, 30)),
                    'updated_at': datetime.utcnow()
                }
            )
            booking_id = result.scalar()
            self.booking_ids.append(booking_id)
            
            # Commit every 500 bookings
            if (i + 1) % 500 == 0:
                await self.session.commit()
                print(f"   Progress: {i + 1}/{count} bookings created...")
        
        await self.session.commit()
        print(f"✅ Created {count} bookings")
    
    async def seed_payments(self, count: int = 3000):
        """Create test payment records."""
        print(f"💳 Creating {count} payments...")
        
        if not self.booking_ids:
            print("❌ ERROR: Must seed bookings first")
            return
        
        # Select random bookings for payments (not all bookings have payments)
        bookings_with_payments = sample(self.booking_ids, min(count, len(self.booking_ids)))
        
        for i, booking_id in enumerate(bookings_with_payments[:count]):
            # Get booking details
            booking_result = await self.session.execute(
                text("SELECT customer_id, total_amount, created_at FROM bookings WHERE id = :id"),
                {'id': booking_id}
            )
            booking = booking_result.fetchone()
            
            if not booking:
                continue
            
            customer_id, amount, booking_created = booking
            payment_date = booking_created + timedelta(hours=randint(1, 48))
            status = choice(['succeeded', 'succeeded', 'succeeded', 'failed', 'refunded'])
            
            # Create payment
            result = await self.session.execute(
                text("""
                    INSERT INTO payments (
                        booking_id, customer_id, amount, currency,
                        status, payment_method, transaction_id,
                        created_at, updated_at
                    )
                    VALUES (
                        :booking_id, :customer_id, :amount, :currency,
                        :status, :payment_method, :transaction_id,
                        :created_at, :updated_at
                    )
                    RETURNING id
                """),
                {
                    'booking_id': booking_id,
                    'customer_id': customer_id,
                    'amount': amount,
                    'currency': 'usd',
                    'status': status,
                    'payment_method': choice(['card', 'card', 'card', 'cash']),
                    'transaction_id': f"txn_test_{fake.uuid4()[:24]}",
                    'created_at': payment_date,
                    'updated_at': datetime.utcnow()
                }
            )
            payment_id = result.scalar()
            
            # Create Stripe payment intent record
            await self.session.execute(
                text("""
                    INSERT INTO stripe_payment_intents (
                        payment_id, stripe_payment_intent_id,
                        amount, currency, status,
                        created_at, updated_at
                    )
                    VALUES (
                        :payment_id, :stripe_payment_intent_id,
                        :amount, :currency, :status,
                        :created_at, :updated_at
                    )
                """),
                {
                    'payment_id': payment_id,
                    'stripe_payment_intent_id': f"pi_test_{fake.uuid4()[:24]}",
                    'amount': int(amount * 100),  # Stripe uses cents
                    'currency': 'usd',
                    'status': status,
                    'created_at': payment_date,
                    'updated_at': datetime.utcnow()
                }
            )
            
            # Commit every 300 payments
            if (i + 1) % 300 == 0:
                await self.session.commit()
                print(f"   Progress: {i + 1}/{count} payments created...")
        
        await self.session.commit()
        print(f"✅ Created {count} payments")
    
    async def print_summary(self):
        """Print summary of seeded data."""
        print("\n" + "="*60)
        print("📊 DATABASE SEEDING SUMMARY")
        print("="*60)
        
        # Count records in each table
        tables = ['stations', 'customers', 'bookings', 'payments', 
                  'stripe_customers', 'stripe_payment_intents']
        
        for table in tables:
            result = await self.session.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            )
            count = result.scalar()
            print(f"  {table.ljust(25)}: {count:,} records")
        
        print("="*60)
        print("")


async def main():
    """Main seeding function."""
    print("\n" + "🌱 " + "="*58)
    print("🌱  MyHibachi Test Data Seeding")
    print("🌱 " + "="*58 + "\n")
    
    # Prompt for confirmation
    print("⚠️  WARNING: This will add test data to your database.")
    print("   Database: " + DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL)
    print("")
    
    # Comment out this confirmation for automated seeding
    # response = input("Continue? (yes/no): ")
    # if response.lower() not in ['yes', 'y']:
    #     print("❌ Seeding cancelled")
    #     return
    
    async with async_session() as session:
        seeder = DataSeeder(session)
        
        try:
            # Optionally clear existing data
            # await seeder.clear_existing_data()
            
            # Seed data in order (respecting foreign key constraints)
            await seeder.seed_stations(count=10)
            await seeder.seed_customers(count=1000)
            await seeder.seed_bookings(count=5000)
            await seeder.seed_payments(count=3000)
            
            # Print summary
            await seeder.print_summary()
            
            print("🎉 " + "="*58)
            print("🎉  SEEDING COMPLETE!")
            print("🎉 " + "="*58)
            print("\n✅ Your database is now populated with realistic test data.")
            print("✅ You can now run the backend server and test all endpoints.\n")
            
        except Exception as e:
            print(f"\n❌ ERROR during seeding: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    # Run async main
    asyncio.run(main())
