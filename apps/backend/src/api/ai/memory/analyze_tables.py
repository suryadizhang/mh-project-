"""
Analyze database tables to update query planner statistics
"""

import asyncio

from core.database import get_db_context
from sqlalchemy import text


async def analyze_tables():
    """Run ANALYZE on AI tables"""
    async with get_db_context() as db:
        await db.execute(text("ANALYZE ai_messages"))

        await db.execute(text("ANALYZE scheduled_followups"))

        await db.execute(text("ANALYZE ai_conversations"))


if __name__ == "__main__":
    asyncio.run(analyze_tables())
