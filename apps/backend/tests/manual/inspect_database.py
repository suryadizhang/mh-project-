"""
Emergency Database Inspector
Checks actual database structure to understand which schema is being used.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import create_engine, inspect, text

from core.config import get_settings


def inspect_database():
    """Inspect actual database structure"""
    
    settings = get_settings()
    
    # Use psycopg2 for synchronous inspection
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(db_url)
    
    print("\n" + "=" * 80)
    print("🔍 DATABASE STRUCTURE INSPECTION")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # 1. Check schemas
    print("\n📁 Available Schemas:")
    schemas = inspector.get_schema_names()
    for schema in schemas:
        print(f"  - {schema}")
    
    # 2. Check tables in each relevant schema
    for schema in ['public', 'core', 'identity']:
        if schema in schemas:
            print(f"\n📊 Tables in '{schema}' schema:")
            tables = inspector.get_table_names(schema=schema)
            if tables:
                for table in sorted(tables):
                    print(f"  - {table}")
            else:
                print("  (no tables)")
    
    # 3. Detailed check of customers table (most critical)
    print("\n" + "=" * 80)
    print("👥 CUSTOMER TABLE ANALYSIS")
    print("=" * 80)
    
    for schema in ['public', 'core']:
        if schema in schemas:
            try:
                tables = inspector.get_table_names(schema=schema)
                if 'customers' in tables:
                    print(f"\n✅ Found: {schema}.customers")
                    print(f"\n📋 Column Structure:")
                    cols = inspector.get_columns('customers', schema=schema)
                    for col in cols:
                        nullable = "NULL" if col['nullable'] else "NOT NULL"
                        default = f" DEFAULT {col.get('default', '')}" if col.get('default') else ""
                        print(f"  - {col['name']:30} {str(col['type']):20} {nullable}{default}")
                    
                    print(f"\n🔑 Foreign Keys:")
                    fks = inspector.get_foreign_keys('customers', schema=schema)
                    if fks:
                        for fk in fks:
                            print(f"  - {fk['constrained_columns']} -> {fk['referred_schema']}.{fk['referred_table']}({fk['referred_columns']})")
                    else:
                        print("  (none)")
                    
                    print(f"\n📇 Indexes:")
                    indexes = inspector.get_indexes('customers', schema=schema)
                    if indexes:
                        for idx in indexes:
                            unique = "UNIQUE" if idx['unique'] else "INDEX"
                            print(f"  - {unique}: {idx['name']} on {idx['column_names']}")
                    else:
                        print("  (none)")
                    
                    # Count rows
                    with engine.connect() as conn:
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}".customers'))
                        count = result.scalar()
                        print(f"\n📊 Row count: {count}")
            except Exception as e:
                print(f"\n❌ Error checking {schema}.customers: {e}")
    
    # 4. Check bookings table
    print("\n" + "=" * 80)
    print("📅 BOOKINGS TABLE ANALYSIS")
    print("=" * 80)
    
    for schema in ['public', 'core']:
        if schema in schemas:
            try:
                tables = inspector.get_table_names(schema=schema)
                if 'bookings' in tables:
                    print(f"\n✅ Found: {schema}.bookings")
                    cols = inspector.get_columns('bookings', schema=schema)
                    print(f"\n📋 Key Columns:")
                    key_cols = ['id', 'customer_id', 'event_date', 'date', 'status']
                    for col in cols:
                        if col['name'] in key_cols or 'id' in col['name']:
                            nullable = "NULL" if col['nullable'] else "NOT NULL"
                            print(f"  - {col['name']:30} {str(col['type']):20} {nullable}")
                    
                    # Count rows
                    with engine.connect() as conn:
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}".bookings'))
                        count = result.scalar()
                        print(f"\n📊 Row count: {count}")
            except Exception as e:
                print(f"\n❌ Error checking {schema}.bookings: {e}")
    
    # 5. Check booking_reminders (our new table!)
    print("\n" + "=" * 80)
    print("🔔 BOOKING_REMINDERS TABLE (Feature 1)")
    print("=" * 80)
    
    try:
        tables = inspector.get_table_names(schema='public')
        if 'booking_reminders' in tables:
            print(f"\n✅ Found: public.booking_reminders")
            cols = inspector.get_columns('booking_reminders', schema='public')
            print(f"\n📋 Columns:")
            for col in cols:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  - {col['name']:30} {str(col['type']):20} {nullable}")
            
            with engine.connect() as conn:
                result = conn.execute(text('SELECT COUNT(*) FROM public.booking_reminders'))
                count = result.scalar()
                print(f"\n📊 Row count: {count}")
        else:
            print("\n❌ Table 'booking_reminders' NOT FOUND in public schema")
    except Exception as e:
        print(f"\n❌ Error checking booking_reminders: {e}")
    
    # 6. Summary & Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    has_public_customers = 'customers' in inspector.get_table_names(schema='public')
    has_core_customers = 'core' in schemas and 'customers' in inspector.get_table_names(schema='core')
    
    if has_public_customers and has_core_customers:
        print("\n🔴 PROBLEM: Both public.customers AND core.customers exist!")
        print("   Action: Need to consolidate to ONE schema")
    elif has_core_customers:
        print("\n⚠️  Using core.customers (legacy multi-tenant)")
        print("   Action: Migrate models to match core schema OR migrate data to public")
    elif has_public_customers:
        print("\n✅ Using public.customers (modern schema)")
        print("   Action: Current models should work - check column names")
    else:
        print("\n❌ NO customers table found in any schema!")
        print("   Action: Run migrations to create tables")
    
    print("\n" + "=" * 80 + "\n")
    
    engine.dispose()


if __name__ == "__main__":
    inspect_database()
