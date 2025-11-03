"""Quick script to check actual bookings table schema."""
import os
import sys
from sqlalchemy import create_engine, inspect, text

# Get database URL from environment variable (required)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is required")
    print("   Set it in your apps/backend/.env file")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

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
