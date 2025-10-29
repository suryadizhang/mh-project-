"""
Seed First Station: California Bay Area (STATION-CA-BAY-001)
Run this script to create the initial station in the database.

Usage:
    python seed_first_station.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend src to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

# Load environment variables from the correct .env file (parent directory, not src/.env)
from dotenv import load_dotenv
env_path = backend_dir / ".env"
load_dotenv(env_path)

print(f"📋 Loading environment from: {env_path}")
print(f"📋 Database URL: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal, get_db_context
from api.app.auth.station_models import Station
from api.app.utils.station_code_generator import generate_station_code
from datetime import datetime


async def seed_first_station():
    """Create the first station: California Bay Area."""
    
    print("🚀 Seeding First Station: California Bay Area")
    print("=" * 60)
    
    # Create async session
    async with AsyncSessionLocal() as session:
        try:
            # Generate station code
            station_code = await generate_station_code(
                db=session,
                city="Bay Area",
                state="CA",
                country="US"
            )
            
            print(f"✓ Generated station code: {station_code}")
            
            # Station data
            station_data = {
                "code": station_code,
                "name": "California Bay Area",
                "display_name": "MyHibachi - California Bay Area",
                "city": "Fremont",
                "state": "CA",
                "country": "US",
                "timezone": "America/Los_Angeles",
                "email": "bay-area@myhibachi.com",
                "phone": "+1-510-555-0100",
                "address": "123 Mission Blvd",
                "postal_code": "94539",
                "status": "active",
                "settings": {
                    "currency": "USD",
                    "language": "en",
                    "auto_confirmation": True,
                    "notification_enabled": True
                },
                "business_hours": {
                    "monday": {"open": "10:00", "close": "22:00", "is_open": True},
                    "tuesday": {"open": "10:00", "close": "22:00", "is_open": True},
                    "wednesday": {"open": "10:00", "close": "22:00", "is_open": True},
                    "thursday": {"open": "10:00", "close": "22:00", "is_open": True},
                    "friday": {"open": "10:00", "close": "23:00", "is_open": True},
                    "saturday": {"open": "09:00", "close": "23:00", "is_open": True},
                    "sunday": {"open": "09:00", "close": "22:00", "is_open": True}
                },
                "service_area_radius": 50,  # 50 miles
                "max_concurrent_bookings": 15,
                "booking_lead_time_hours": 24,
                "branding_config": {
                    "primary_color": "#FF6B35",
                    "secondary_color": "#004E89",
                    "logo_url": None,
                    "tagline": "Authentic Hibachi Experience in the Bay Area"
                }
            }
            
            # Create station
            station = Station(**station_data)
            session.add(station)
            await session.commit()
            await session.refresh(station)
            
            print(f"✓ Station created successfully!")
            print(f"\n📋 Station Details:")
            print(f"   ID:           {station.id}")
            print(f"   Code:         {station.code}")
            print(f"   Name:         {station.name}")
            print(f"   Display Name: {station.display_name}")
            print(f"   Location:     {station.city}, {station.state} {station.postal_code}")
            print(f"   Timezone:     {station.timezone}")
            print(f"   Status:       {station.status}")
            print(f"   Email:        {station.email}")
            print(f"   Phone:        {station.phone}")
            print(f"   Max Bookings: {station.max_concurrent_bookings} concurrent")
            print(f"   Lead Time:    {station.booking_lead_time_hours} hours")
            print(f"   Created:      {station.created_at}")
            print(f"\n✅ First station seeded successfully!")
            print(f"\n💡 Next Steps:")
            print(f"   1. Assign a station manager via admin panel")
            print(f"   2. Configure staff users with appropriate roles")
            print(f"   3. Test booking creation for this station")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding station: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SEED FIRST STATION: CALIFORNIA BAY AREA")
    print("=" * 60 + "\n")
    
    asyncio.run(seed_first_station())
    
    print("\n" + "=" * 60)
    print("  SEEDING COMPLETE!")
    print("=" * 60 + "\n")
