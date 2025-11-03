"""Drop and recreate scheduled_followups table with new schema"""
import sys
sys.path.insert(0, 'src')

import asyncio
from core.database import get_db_context
from sqlalchemy import text
from api.ai.scheduler.follow_up_scheduler import ScheduledFollowUp
from core.database import Base, engine

async def drop_and_recreate():
    """Drop scheduled_followups and recreate with new schema"""
    async with get_db_context() as db:
        print("Dropping scheduled_followups table...")
        await db.execute(text("DROP TABLE IF EXISTS scheduled_followups CASCADE"))
        await db.commit()
        print("✅ Dropped scheduled_followups table")
    
    print("Recreating scheduled_followups table with VARCHAR(255)...")
    async with engine.begin() as conn:
        await conn.run_sync(ScheduledFollowUp.__table__.create, checkfirst=True)
    print("✅ Recreated scheduled_followups table")
    
    # Verify new schema
    async with get_db_context() as db:
        result = await db.execute(text("""
            SELECT character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'scheduled_followups' 
            AND column_name = 'id'
        """))
        row = result.first()
        print(f"✅ Verified id column length: {row[0] if row else 'Not found'}")

if __name__ == "__main__":
    asyncio.run(drop_and_recreate())
