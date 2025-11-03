"""
Test script to add a member to notification group
Uses direct database access to bypass JWT authentication for testing
"""
import asyncio
import os
from dotenv import load_dotenv
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Load environment first
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required for tests")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def add_member_to_group():
    """Add a member to the All Admins group"""
    
    # Import models directly to avoid triggering server startup
    from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
    from sqlalchemy.dialects.postgresql import UUID as SQLUUID
    from sqlalchemy.ext.declarative import declarative_base
    from datetime import datetime
    
    Base = declarative_base()
    
    class NotificationGroupMember(Base):
        __tablename__ = "notification_group_members"
        id = Column(SQLUUID(as_uuid=True), primary_key=True)
        group_id = Column(SQLUUID(as_uuid=True), nullable=False)
        phone_number = Column(String(20), nullable=False)
        name = Column(String(100), nullable=False)
        email = Column(String(255), nullable=True)
        receive_whatsapp = Column(Boolean, default=True)
        receive_sms = Column(Boolean, default=False)
        receive_email = Column(Boolean, default=False)
        priority = Column(String(20), default='medium')
        is_active = Column(Boolean, default=True)
        added_at = Column(DateTime, default=datetime.utcnow)
        added_by = Column(SQLUUID(as_uuid=True), nullable=True)
    
    # Group IDs from initialization
    ALL_ADMINS_ID = "289fc142-6d17-47bd-affb-a72ece84b2df"
    
    # Member details
    member_data = {
        "phone_number": "+19167408768",
        "name": "Admin User",
        "email": None,
        "receive_whatsapp": True,
        "receive_sms": False,
        "receive_email": False
    }
    
    # System admin ID (used for created_by)
    system_admin_id = "00000000-0000-0000-0000-000000000000"
    
    async with async_session_maker() as session:
        
        try:
            print("=" * 80)
            print("ADDING MEMBER TO NOTIFICATION GROUP")
            print("=" * 80)
            print()
            print(f"📋 Group ID: {ALL_ADMINS_ID}")
            print(f"👤 Member: {member_data['name']} ({member_data['phone_number']})")
            print()
            
            # Create member directly
            member = NotificationGroupMember(
                id=uuid4(),
                group_id=UUID(ALL_ADMINS_ID),
                phone_number=member_data["phone_number"],
                name=member_data["name"],
                email=member_data.get("email"),
                receive_whatsapp=member_data.get("receive_whatsapp", True),
                receive_sms=member_data.get("receive_sms", False),
                receive_email=member_data.get("receive_email", False),
                priority='medium',
                is_active=True,
                added_by=UUID(system_admin_id)
            )
            
            session.add(member)
            await session.commit()
            await session.refresh(member)
            
            print("✅ Member added successfully!")
            print(f"   ID: {member.id}")
            print(f"   Name: {member.name}")
            print(f"   Phone: {member.phone_number}")
            print(f"   WhatsApp: {'✓' if member.receive_whatsapp else '✗'}")
            print(f"   SMS: {'✓' if member.receive_sms else '✗'}")
            print(f"   Email: {'✓' if member.receive_email else '✗'}")
            print()
            
            # List all members in the group
            result = await session.execute(
                select(NotificationGroupMember).where(
                    NotificationGroupMember.group_id == UUID(ALL_ADMINS_ID),
                    NotificationGroupMember.is_active == True
                )
            )
            members = result.scalars().all()
            print(f"📊 Total members in 'All Admins' group: {len(members)}")
            for m in members:
                print(f"   • {m.name} ({m.phone_number})")
            
            print()
            print("=" * 80)
            print("✅ MEMBER ADDITION COMPLETE")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error adding member: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting member addition test...\n")
    asyncio.run(add_member_to_group())
