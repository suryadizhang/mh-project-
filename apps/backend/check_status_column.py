import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import get_settings

async def check_status_column():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name, data_type, udt_name "
            "FROM information_schema.columns "
            "WHERE table_schema='core' AND table_name='bookings' AND column_name='status'"
        ))
        rows = result.fetchall()
        print("Status column info:", rows)

        # Check if booking_status enum exists
        enum_result = await conn.execute(text(
            "SELECT enumlabel FROM pg_enum "
            "WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'booking_status') "
            "ORDER BY enumsortorder"
        ))
        enum_values = enum_result.fetchall()
        print("Booking_status enum values:", [row[0] for row in enum_values])

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_status_column())
