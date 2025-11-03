import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.notification_group_service import NotificationGroupService
from db.session import async_session_maker

async def list_groups():
    async with async_session_maker() as session:
        service = NotificationGroupService(session)
        groups = await service.list_groups()
        
        print("\n📋 Notification Groups:\n")
        for group in groups:
            print(f"✅ {group.name}")
            print(f"   ID: {group.id}")
            print(f"   Description: {group.description}")
            print()

if __name__ == "__main__":
    asyncio.run(list_groups())
