"""Quick script to check actual bookings table schema."""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/myhibachi_crm')

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'core' AND table_name = 'bookings' 
        ORDER BY ordinal_position
    """))
    
    print("=== core.bookings actual columns ===")
    for row in result:
        print(f"{row[0]:<30} {row[1]}")
