"""Check bookings table schema and unique constraint"""
from sqlalchemy import create_engine, text

engine = create_engine(
    'postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres'
)

with engine.connect() as conn:
    # Check if bookings table exists
    tables_result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'bookings'
    """)).fetchall()

    if tables_result:
        print("✅ bookings table EXISTS\n")

        # Check unique constraint/index
        indexes_result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'bookings' AND indexname = 'idx_booking_datetime_active'
        """)).fetchall()

        if indexes_result:
            print("✅ Unique constraint idx_booking_datetime_active EXISTS")
            print(f"   Definition: {indexes_result[0][1]}\n")
        else:
            print("❌ Unique constraint idx_booking_datetime_active NOT FOUND\n")

        # Check bookings table schema
        schema_result = conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'bookings'
            ORDER BY ordinal_position
        """)).fetchall()

        print("bookings table schema (first 10 columns):")
        for row in schema_result[:10]:
            col_name, data_type, max_len = row
            type_str = f"{data_type}({max_len})" if max_len else data_type
            print(f"  {col_name}: {type_str}")
    else:
        print("❌ bookings table NOT FOUND")

