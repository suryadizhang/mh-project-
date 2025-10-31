"""Test Supabase database connection"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    print("Testing Supabase connection...")
    engine = create_async_engine(
        'postgresql+asyncpg://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres',
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
