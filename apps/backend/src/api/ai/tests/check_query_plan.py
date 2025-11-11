"""
Check Query Plan for Duplicate Check
=====================================
Verifies if PostgreSQL is using the composite index
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

from sqlalchemy import text

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from core.database import get_db_context


async def check_query_plan():
    """Check if composite index is being used"""

    async with get_db_context() as db:
        # The actual duplicate check query
        test_date = datetime.now(timezone.utc) + timedelta(days=7)
        date_start = test_date
        date_end = test_date + timedelta(days=2)

        query = text(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT * FROM scheduled_followups
            WHERE user_id = 'test_user'
              AND trigger_type = 'post_event'
              AND status = 'pending'
              AND scheduled_at >= :date_start
              AND scheduled_at <= :date_end
        """
        )

        result = await db.execute(query, {"date_start": date_start, "date_end": date_end})

        for _row in result:
            pass

        # Check available indexes

        index_query = text(
            """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'scheduled_followups'
            ORDER BY indexname
        """
        )

        result = await db.execute(index_query)
        for _row in result:
            pass

        await db.commit()


if __name__ == "__main__":
    asyncio.run(check_query_plan())
