"""Clean up test data from database"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import text
from api.app.database import engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def cleanup_test_data():
    """Remove all test-related data."""
    print("Cleaning up test data...")
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        try:
            # Delete test bookings (those with TEST- prefix in booking_reference)
            result = await session.execute(
                text("DELETE FROM bookings WHERE booking_reference LIKE 'TEST-%'")
            )
            print(f"  Deleted {result.rowcount} test bookings")
            
            # Delete test users (those with test-user- prefix)
            result = await session.execute(
                text("DELETE FROM users WHERE id LIKE 'test-user-%'")
            )
            print(f"  Deleted {result.rowcount} test users")
            
            # Delete test payments (those with test-payment- prefix)
            result = await session.execute(
                text("DELETE FROM payments WHERE id LIKE 'test-payment-%'")
            )
            print(f"  Deleted {result.rowcount} test payments")
            
            await session.commit()
            print("\n[SUCCESS] Test data cleaned up successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n[ERROR] Failed to clean up: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
