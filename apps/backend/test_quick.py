"""Quick test to verify backend startup and database connection"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("=" * 80)
print("QUICK BACKEND VERIFICATION TEST")
print("=" * 80)
print()

# Test 1: Import models
print("Test 1: Import models...")
try:
    from db.models.core import Booking
    from models.booking_reminder import BookingReminder

    print("✅ Models imported successfully")
    print(f"  - Booking.reminders exists: {hasattr(Booking, 'reminders')}")
    print(f"  - BookingReminder.booking exists: {hasattr(BookingReminder, 'booking')}")
except Exception as e:
    print(f"❌ Failed to import models: {e}")
    sys.exit(1)

# Test 2: Database connection
print("\nTest 2: Database connection...")
try:
    from core.database import engine
    from sqlalchemy import text

    async def test_db():
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            value = result.scalar()
            return value

    result = asyncio.run(test_db())
    print(f"✅ Database connected successfully (test query returned: {result})")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Test 3: Try to import main app
print("\nTest 3: Import FastAPI app...")
try:
    from main import app

    print("✅ FastAPI app imported successfully")
    print(f"  - App title: {app.title}")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - Backend ready to start!")
print("=" * 80)
print("\nNext steps:")
print("1. Start backend: uvicorn main:app --reload")
print("2. Run tests: pytest tests/test_race_condition_fix.py -v")
