"""Check message_threads table structure and station_id column"""

from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SYNC = os.getenv('DATABASE_URL_SYNC')
engine = create_engine(DATABASE_URL_SYNC)
inspector = inspect(engine)

print("="*80)
print("MESSAGE_THREADS TABLE STRUCTURE CHECK")
print("="*80)

# Check if message_threads table exists
tables = inspector.get_table_names(schema='core')

if 'message_threads' in tables:
    print("\n✓ message_threads table EXISTS in core schema\n")
    
    # Get columns
    columns = inspector.get_columns('message_threads', schema='core')
    
    print("COLUMNS:")
    print("-" * 80)
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"   {col['name']:30} {str(col['type']):20} {nullable}")
    
    # Check for station_id column
    has_station_id = any(col['name'] == 'station_id' for col in columns)
    
    if has_station_id:
        print("\n✓ station_id column EXISTS")
    else:
        print("\n✗ station_id column MISSING")
    
    # Check foreign keys
    print("\nFOREIGN KEYS:")
    print("-" * 80)
    fks = inspector.get_foreign_keys('message_threads', schema='core')
    for fk in fks:
        print(f"   {fk['constrained_columns']} → {fk['referred_schema']}.{fk['referred_table']}.{fk['referred_columns']}")
    
    # Check indexes
    print("\nINDEXES:")
    print("-" * 80)
    indexes = inspector.get_indexes('message_threads', schema='core')
    for idx in indexes:
        unique = "UNIQUE" if idx.get('unique') else ""
        print(f"   {idx['name']:40} {idx['column_names']} {unique}")
    
    # Check row count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM core.message_threads"))
        count = result.scalar()
        print(f"\nROW COUNT: {count} records")
        
        if has_station_id:
            result = conn.execute(text("SELECT COUNT(*) FROM core.message_threads WHERE station_id IS NULL"))
            null_count = result.scalar()
            print(f"Records with NULL station_id: {null_count}")
else:
    print("\n✗ message_threads table DOES NOT EXIST in core schema")
    print("\nThis is a potential issue - the table is referenced in migrations but not created.")

print("\n" + "="*80)
