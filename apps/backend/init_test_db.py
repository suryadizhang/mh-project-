"""
Initialize test database with realistic fake data
Run this before starting the backend for testing
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load test environment
from dotenv import load_dotenv
load_dotenv(".env.test")

from sqlalchemy import text
from api.app.database import engine, Base
from api.app.models.user import User
from api.app.models.booking import Booking
from api.app.models.customer import Customer
from api.app.auth.station_models import Station, StationUser

async def init_test_db():
    """Initialize test database with schema and fake data"""
    print("🏗️  Creating database schema...")
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database schema created")
    
    # Import models for session
    from api.app.database import AsyncSessionLocal
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async with AsyncSessionLocal() as session:
        print("📝 Creating fake data...")
        
        # Create Stations
        stations = [
            Station(
                name="Downtown Sacramento",
                description="Main location serving downtown area",
                location="1234 K St, Sacramento, CA 95814",
                phone="+1-916-555-0100",
                email="downtown@myhibachi.com",
                manager_name="John Smith",
                settings={"operating_hours": "10:00-22:00", "max_bookings": 50},
                is_active=True
            ),
            Station(
                name="East Bay Location",
                description="Serving Oakland and Berkeley",
                location="5678 Telegraph Ave, Oakland, CA 94609",
                phone="+1-510-555-0200",
                email="eastbay@myhibachi.com",
                manager_name="Sarah Johnson",
                settings={"operating_hours": "11:00-23:00", "max_bookings": 40},
                is_active=True
            ),
            Station(
                name="San Jose Branch",
                description="Silicon Valley headquarters",
                location="9012 El Camino Real, San Jose, CA 95128",
                phone="+1-408-555-0300",
                email="sanjose@myhibachi.com",
                manager_name="Michael Chen",
                settings={"operating_hours": "10:00-22:00", "max_bookings": 60},
                is_active=True
            )
        ]
        
        for station in stations:
            session.add(station)
        
        await session.flush()
        print(f"✅ Created {len(stations)} stations")
        
        # Create Users
        users = [
            User(
                email="admin@myhibachi.com",
                username="admin",
                hashed_password=pwd_context.hash("Admin123!"),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                phone="+1-916-555-9999"
            ),
            User(
                email="manager1@myhibachi.com",
                username="manager1",
                hashed_password=pwd_context.hash("Manager123!"),
                full_name="Station Manager One",
                is_active=True,
                is_superuser=False,
                phone="+1-916-555-1001"
            ),
            User(
                email="support@myhibachi.com",
                username="support",
                hashed_password=pwd_context.hash("Support123!"),
                full_name="Customer Support",
                is_active=True,
                is_superuser=False,
                phone="+1-916-555-2001"
            )
        ]
        
        for user in users:
            session.add(user)
        
        await session.flush()
        print(f"✅ Created {len(users)} users")
        
        # Create Station Users (assignments)
        station_users = [
            StationUser(
                station_id=stations[0].id,
                user_id=users[1].id,
                role="station_admin",
                permissions=["manage_bookings", "view_analytics", "manage_staff"]
            ),
            StationUser(
                station_id=stations[0].id,
                user_id=users[2].id,
                role="customer_support",
                permissions=["view_bookings", "update_bookings"]
            )
        ]
        
        for su in station_users:
            session.add(su)
        
        print(f"✅ Created {len(station_users)} station assignments")
        
        # Create Customers
        first_names = ["James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda", "David", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        customers = []
        for i in range(50):
            customer = Customer(
                email=f"customer{i+1}@example.com",
                phone=f"+1-916-555-{1000+i:04d}",
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                notes=f"Test customer {i+1}" if i % 5 == 0 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            customers.append(customer)
            session.add(customer)
        
        await session.flush()
        print(f"✅ Created {len(customers)} customers")
        
        # Create Bookings
        statuses = ["pending", "confirmed", "completed", "cancelled"]
        
        bookings = []
        for i in range(100):
            booking_date = datetime.utcnow() + timedelta(days=random.randint(-30, 60))
            
            booking = Booking(
                customer_id=random.choice(customers).id,
                station_id=random.choice(stations).id,
                booking_date=booking_date.date(),
                booking_time=booking_date.time(),
                party_size=random.randint(4, 20),
                status=random.choice(statuses),
                total_price=random.randint(200, 1500),
                deposit_paid=random.choice([True, False]),
                special_requests="Vegetarian option" if i % 10 == 0 else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            bookings.append(booking)
            session.add(booking)
        
        print(f"✅ Created {len(bookings)} bookings")
        
        await session.commit()
        print("\n🎉 Test database initialized successfully!")
        print(f"\n📊 Summary:")
        print(f"   • Stations: {len(stations)}")
        print(f"   • Users: {len(users)}")
        print(f"   • Customers: {len(customers)}")
        print(f"   • Bookings: {len(bookings)}")
        print(f"\n🔐 Test Credentials:")
        print(f"   Admin:   admin@myhibachi.com / Admin123!")
        print(f"   Manager: manager1@myhibachi.com / Manager123!")
        print(f"   Support: support@myhibachi.com / Support123!")

if __name__ == "__main__":
    asyncio.run(init_test_db())
