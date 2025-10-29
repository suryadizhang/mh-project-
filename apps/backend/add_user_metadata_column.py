"""Add user_metadata column to identity.users table"""
import asyncio
import asyncpg
from src.core.config import get_settings

settings = get_settings()

async def add_column():
    # Remove +asyncpg suffix for direct asyncpg connection
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute('''
            ALTER TABLE identity.users 
            ADD COLUMN IF NOT EXISTS user_metadata JSONB;
        ''')
        print("✅ user_metadata column added successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_column())
