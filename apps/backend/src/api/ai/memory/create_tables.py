"""
Database Migration: Create AI Memory Tables
==========================================

Creates tables for conversation memory:
- ai_conversations: Conversation metadata
- ai_messages: Individual messages with emotion tracking

Run manually:
    cd apps/backend
    export PYTHONPATH=$PWD/src
    python -m api.ai.memory.create_tables

Or use Alembic for production migrations.
"""

import asyncio
import logging
from sqlalchemy import text

from core.database import engine, Base, get_db_context
from api.ai.memory.postgresql_memory import AIConversation, AIMessage
from api.ai.scheduler.follow_up_scheduler import ScheduledFollowUp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create AI memory tables"""
    
    logger.info("Creating AI memory tables...")
    
    try:
        # Create tables using SQLAlchemy
        async with engine.begin() as conn:
            # Import models to register them
            logger.info("Importing models...")
            
            # Create tables
            logger.info("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ AI memory tables created successfully")
            
            # Verify tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND (table_name LIKE 'ai_%' OR table_name = 'scheduled_followups')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.all()]
            logger.info(f"Created tables: {tables}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False


async def drop_tables():
    """Drop AI memory tables (DANGER: for testing only)"""
    
    logger.warning("⚠️  DROPPING AI memory tables...")
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS scheduled_followups CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS ai_messages CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS ai_conversations CASCADE"))
            
            logger.info("✅ AI memory tables dropped")
            return True
            
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False


async def check_tables():
    """Check if AI memory tables exist"""
    
    try:
        async with get_db_context() as db:
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('ai_conversations', 'ai_messages', 'scheduled_followups')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.all()]
            
            if len(tables) == 3:
                logger.info(f"✅ AI memory and scheduler tables exist: {tables}")
                return True
            else:
                logger.warning(f"⚠️  Missing tables. Found: {tables}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to check tables: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        # Drop tables (testing only)
        result = asyncio.run(drop_tables())
        sys.exit(0 if result else 1)
    
    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        # Check tables
        result = asyncio.run(check_tables())
        sys.exit(0 if result else 1)
    
    else:
        # Create tables
        result = asyncio.run(create_tables())
        sys.exit(0 if result else 1)
