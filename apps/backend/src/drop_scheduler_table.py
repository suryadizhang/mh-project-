"""Drop and recreate scheduled_followups table with new schema"""

import sys

sys.path.insert(0, "src")

import asyncio

from db.models.ai import CustomerEngagementFollowUp
from core.database import engine, get_db_context
from sqlalchemy import text


async def drop_and_recreate():
    """Drop scheduled_followups and recreate with new schema"""
    async with get_db_context() as db:
        await db.execute(text("DROP TABLE IF EXISTS scheduled_followups CASCADE"))
        await db.commit()

    async with engine.begin() as conn:
        await conn.run_sync(CustomerEngagementFollowUp.__table__.create, checkfirst=True)

    # Verify new schema
    async with get_db_context() as db:
        result = await db.execute(
            text(
                """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'scheduled_followups'
            AND column_name = 'id'
        """
            )
        )
        result.first()


if __name__ == "__main__":
    asyncio.run(drop_and_recreate())
