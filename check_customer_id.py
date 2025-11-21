import os

from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set")
    exit(1)

engine = create_engine(db_url)
with engine.connect() as conn:
    # Check all columns of customers table
    result = conn.execute(
        text(
            """
        SELECT table_schema, column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'customers'
        ORDER BY table_schema, ordinal_position
    """
        )
    )
    print("=== Customers table structure ===")
    for row in result:
        print(
            f"Schema: {row[0]}, Column: {row[1]}, Type: {row[2]}, UDT: {row[3]}"
        )

    # Check bookings table too
    result2 = conn.execute(
        text(
            """
        SELECT table_schema, column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'bookings' AND column_name IN ('id', 'customer_id')
        ORDER BY table_schema, ordinal_position
    """
        )
    )
    print("\n=== Bookings table structure ===")
    for row in result2:
        print(
            f"Schema: {row[0]}, Column: {row[1]}, Type: {row[2]}, UDT: {row[3]}"
        )
