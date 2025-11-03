"""
Initialize Default Notification Groups

This script creates the default notification groups for the admin panel.
Run this after the database migration to set up the initial groups.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is required")
    print("   Set it in your apps/backend/.env file")
    sys.exit(1)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initialize_groups():
    """Initialize default notification groups"""
    print("=" * 80)
    print("INITIALIZING DEFAULT NOTIFICATION GROUPS")
    print("=" * 80)
    print()
    
    from services.notification_group_service import NotificationGroupService
    from api.app.models.notification_groups import DEFAULT_GROUPS
    
    async with async_session_maker() as session:
        service = NotificationGroupService(session)
        
        try:
            print(f"📋 Creating {len(DEFAULT_GROUPS)} default groups...")
            print()
            
            # Create a system admin user ID (you can replace this with an actual admin ID)
            system_admin_id = "00000000-0000-0000-0000-000000000000"
            
            created_groups = []
            
            for group_config in DEFAULT_GROUPS:
                try:
                    # Check if group already exists by listing and filtering
                    existing_groups = await service.list_groups()
                    if any(g.name == group_config['name'] for g in existing_groups):
                        print(f"⏭️  Group '{group_config['name']}' already exists - skipping")
                        continue
                    
                    # Create group with event subscriptions
                    group = await service.create_group(
                        name=group_config['name'],
                        description=group_config['description'],
                        station_id=group_config.get('station_id'),
                        created_by=system_admin_id,
                        event_types=group_config.get('events', ['all'])
                    )
                    
                    print(f"✅ Created group: {group_config['name']}")
                    print(f"   ID: {group.id}")
                    print(f"   Description: {group_config['description']}")
                    print(f"   📌 Subscribed to: {', '.join(group_config.get('events', ['all']))}")
                    
                    created_groups.append(group)
                    print()
                
                except Exception as e:
                    print(f"❌ Error creating group '{group_config['name']}': {e}")
                    continue
            
            await session.commit()
            
            print()
            print("=" * 80)
            print("✅ INITIALIZATION COMPLETE")
            print("=" * 80)
            print()
            print(f"📊 Summary:")
            print(f"   Total groups created: {len(created_groups)}")
            print()
            print("🎯 Next Steps:")
            print("1. Add team members to groups via API or admin panel")
            print("2. Configure station-specific groups for station managers")
            print("3. Adjust event subscriptions as needed")
            print()
            print("📚 API Endpoints:")
            print("   POST   /api/admin/notification-groups/{id}/members")
            print("   GET    /api/admin/notification-groups")
            print("   PATCH  /api/admin/notification-groups/{id}")
            print()
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()


if __name__ == "__main__":
    print()
    print("🚀 Starting notification groups initialization...")
    print()
    asyncio.run(initialize_groups())
