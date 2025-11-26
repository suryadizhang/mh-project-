"""
Apply Phase 1 Performance Optimizations
========================================

This script creates the composite index for duplicate check optimization.

Expected Impact:
- Duplicate check: 637ms → ~100ms (84% faster)
- Schedule follow-up: 1931ms → ~1300ms (32% faster)
"""

import asyncio
from pathlib import Path
import sys

from sqlalchemy import text

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

import contextlib

from core.database import get_db_context


async def apply_optimizations():
    """Apply Phase 1 performance optimizations"""

    async with get_db_context() as db:
        # 1. Create composite index for duplicate check

        with contextlib.suppress(Exception):
            await db.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_scheduled_followups_duplicate_check
                ON scheduled_followups(user_id, trigger_type, status, scheduled_at)
            """
                )
            )

        # 2. Run ANALYZE to update query planner statistics
        await db.execute(text("ANALYZE scheduled_followups"))
        await db.execute(text("ANALYZE ai_messages"))

        await db.commit()


if __name__ == "__main__":
    asyncio.run(apply_optimizations())

