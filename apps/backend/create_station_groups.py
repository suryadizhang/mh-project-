"""
Create Station-Specific Notification Groups

This script creates notification groups for each station, so station managers
can receive notifications only for events at their specific station.

Run this after stations are created in the database.
"""
import asyncio
import os
from dotenv import load_dotenv
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/myhibachi")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class Station(Base):
    __tablename__ = "stations"
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    name = Column(String(100), nullable=False)
    city = Column(String(100))
    state = Column(String(2))
    is_active = Column(Boolean, default=True)


class NotificationGroup(Base):
    __tablename__ = "notification_groups"
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    station_id = Column(SQLUUID(as_uuid=True), nullable=True)
    whatsapp_group_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(SQLUUID(as_uuid=True), nullable=True)


class NotificationGroupEvent(Base):
    __tablename__ = "notification_group_events"
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    group_id = Column(SQLUUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(SQLUUID(as_uuid=True), nullable=True)


async def create_station_groups():
    """Create notification groups for each active station"""
    
    system_admin_id = UUID("00000000-0000-0000-0000-000000000000")
    
    # Event types station managers should receive
    station_events = [
        "new_booking",
        "booking_edit",
        "booking_cancellation",
        "payment_received",
        "review_received",
        "complaint_received"
    ]
    
    async with async_session_maker() as session:
        try:
            print("=" * 80)
            print("CREATING STATION-SPECIFIC NOTIFICATION GROUPS")
            print("=" * 80)
            print()
            
            # Get all active stations
            result = await session.execute(
                select(Station).where(Station.is_active == True)
            )
            stations = result.scalars().all()
            
            if not stations:
                print("⚠️  No active stations found in database.")
                print("   Please create stations first before running this script.")
                print()
                return
            
            print(f"📍 Found {len(stations)} active station(s)")
            print()
            
            created_count = 0
            skipped_count = 0
            
            for station in stations:
                station_location = f"{station.city}, {station.state}" if station.city and station.state else "Unknown Location"
                group_name = f"Station Managers - {station.name}"
                
                # Check if group already exists
                existing = await session.execute(
                    select(NotificationGroup).where(
                        NotificationGroup.name == group_name,
                        NotificationGroup.station_id == station.id
                    )
                )
                if existing.scalar_one_or_none():
                    print(f"⏭️  Group '{group_name}' already exists - skipping")
                    skipped_count += 1
                    continue
                
                # Create notification group for this station
                group = NotificationGroup(
                    id=uuid4(),
                    name=group_name,
                    description=f"Station managers and staff for {station.name} ({station_location}) - receive all station-specific notifications",
                    station_id=station.id,
                    is_active=True,
                    created_by=system_admin_id
                )
                
                session.add(group)
                await session.flush()
                
                # Subscribe to relevant event types
                for event_type in station_events:
                    event = NotificationGroupEvent(
                        id=uuid4(),
                        group_id=group.id,
                        event_type=event_type,
                        is_active=True,
                        created_by=system_admin_id
                    )
                    session.add(event)
                
                await session.commit()
                
                print(f"✅ Created group: {group_name}")
                print(f"   ID: {group.id}")
                print(f"   Station: {station.name} ({station_location})")
                print(f"   Station ID: {station.id}")
                print(f"   📌 Subscribed to: {', '.join(station_events)}")
                print()
                
                created_count += 1
            
            print("=" * 80)
            print("✅ STATION GROUPS CREATION COMPLETE")
            print("=" * 80)
            print()
            print(f"📊 Summary:")
            print(f"   Created: {created_count} new station group(s)")
            print(f"   Skipped: {skipped_count} existing group(s)")
            print(f"   Total Stations: {len(stations)}")
            print()
            print("🎯 Next Steps:")
            print("1. Add station managers/staff to their respective groups via API")
            print("2. Set WhatsApp group IDs for each station group (optional)")
            print("3. Test notifications - events will be filtered by station_id")
            print()
            print("📚 API Endpoints:")
            print("   POST   /api/admin/notification-groups/{id}/members")
            print("   GET    /api/admin/notification-groups?station_id={station-id}")
            print("   PATCH  /api/admin/notification-groups/{id}")
            print()
            
        except Exception as e:
            print(f"❌ Error creating station groups: {e}")
            import traceback
            traceback.print_exc()


async def list_station_groups():
    """List all station-specific notification groups"""
    
    async with async_session_maker() as session:
        try:
            print("=" * 80)
            print("STATION-SPECIFIC NOTIFICATION GROUPS")
            print("=" * 80)
            print()
            
            result = await session.execute(
                select(NotificationGroup, Station)
                .outerjoin(Station, NotificationGroup.station_id == Station.id)
                .where(NotificationGroup.station_id.isnot(None))
                .order_by(Station.name)
            )
            
            groups_with_stations = result.all()
            
            if not groups_with_stations:
                print("📋 No station-specific groups found yet.")
                print("   Run create_station_groups.py to create them.")
                print()
                return
            
            print(f"📋 Found {len(groups_with_stations)} station group(s):\n")
            
            for group, station in groups_with_stations:
                station_name = station.name if station else "Unknown Station"
                station_location = f"{station.city}, {station.state}" if station and station.city else "N/A"
                
                print(f"✅ {group.name}")
                print(f"   Group ID: {group.id}")
                print(f"   Station: {station_name} ({station_location})")
                print(f"   Station ID: {group.station_id}")
                print(f"   Status: {'Active' if group.is_active else 'Inactive'}")
                
                # Get event subscriptions
                events_result = await session.execute(
                    select(NotificationGroupEvent).where(
                        NotificationGroupEvent.group_id == group.id,
                        NotificationGroupEvent.is_active == True
                    )
                )
                events = events_result.scalars().all()
                if events:
                    event_types = [e.event_type for e in events]
                    print(f"   📌 Events: {', '.join(event_types)}")
                print()
            
        except Exception as e:
            print(f"❌ Error listing station groups: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    print("\n🚀 Station Notification Groups Manager\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_station_groups())
    else:
        asyncio.run(create_station_groups())
        print("\n💡 Tip: Run 'python create_station_groups.py list' to view all station groups\n")
