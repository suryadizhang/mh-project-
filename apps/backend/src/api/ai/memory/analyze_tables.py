"""
Analyze database tables to update query planner statistics
"""
import asyncio
from core.database import get_db_context
from sqlalchemy import text


async def analyze_tables():
    """Run ANALYZE on AI tables"""
    async with get_db_context() as db:
        print("Analyzing ai_messages table...")
        await db.execute(text('ANALYZE ai_messages'))
        
        print("Analyzing scheduled_followups table...")
        await db.execute(text('ANALYZE scheduled_followups'))
        
        print("Analyzing ai_conversations table...")
        await db.execute(text('ANALYZE ai_conversations'))
        
        print("✅ Database statistics updated successfully")


if __name__ == "__main__":
    asyncio.run(analyze_tables())
