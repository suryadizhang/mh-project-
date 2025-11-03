"""Test Supabase database connection"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    print("Testing Supabase connection...")
    # Get database URL from environment variable (required)
    DATABASE_URL = os.getenv('DATABASE_URL_ASYNC')
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL_ASYNC environment variable is required")
        print("   Set it in your apps/backend/.env file")
        sys.exit(1)
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False
    )
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            value = result.scalar()
            print(f"✅ Database connected successfully! Test query returned: {value}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
