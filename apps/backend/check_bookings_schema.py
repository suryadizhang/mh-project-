"""Check actual bookings table schema in database"""
from sqlalchemy import create_engine, text
from core.config import settings

# Create sync engine
sync_engine = create_engine(str(settings.database_url).replace('+asyncpg', ''))

with sync_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema='core' AND table_name='bookings'
        ORDER BY ordinal_position
    """))

    print("Actual bookings table schema (core.bookings):")
    print("=" * 60)
    for row in result:
        nullable = "NULL" if row[2] == "YES" else "NOT NULL"
        print(f"{row[0]:<30} {row[1]:<20} {nullable}")
