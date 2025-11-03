"""
Apply Phase 1 Performance Optimizations
========================================

This script creates the composite index for duplicate check optimization.

Expected Impact:
- Duplicate check: 637ms → ~100ms (84% faster)
- Schedule follow-up: 1931ms → ~1300ms (32% faster)
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from core.database import get_db_context


async def apply_optimizations():
    """Apply Phase 1 performance optimizations"""
    
    print("=" * 80)
    print("PHASE 1 PERFORMANCE OPTIMIZATIONS")
    print("=" * 80)
    print()
    
    async with get_db_context() as db:
        # 1. Create composite index for duplicate check
        print("Creating composite index for duplicate check...")
        print("  Index: idx_scheduled_followups_duplicate_check")
        print("  Columns: (user_id, trigger_type, status, scheduled_at)")
        print()
        
        try:
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_followups_duplicate_check
                ON scheduled_followups(user_id, trigger_type, status, scheduled_at)
            """))
            print("[+] Composite index created successfully")
        except Exception as e:
            print(f"[!] Warning: {e}")
            print("    (Index may already exist)")
        
        print()
        
        # 2. Run ANALYZE to update query planner statistics
        print("Updating query planner statistics...")
        await db.execute(text("ANALYZE scheduled_followups"))
        await db.execute(text("ANALYZE ai_messages"))
        print("[+] Statistics updated")
        
        print()
        await db.commit()
    
    print("=" * 80)
    print("OPTIMIZATION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run performance test: python src/api/ai/tests/test_performance_optimizations.py")
    print("2. Verify improvements with profiling: python src/api/ai/tests/profile_schedule_performance.py")
    print("3. Check query plans:")
    print()
    print("   EXPLAIN ANALYZE")
    print("   SELECT * FROM scheduled_followups")
    print("   WHERE user_id = 'test' AND trigger_type = 'post_event'")
    print("     AND status = 'pending' AND scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '2 days';")
    print()


if __name__ == "__main__":
    asyncio.run(apply_optimizations())
