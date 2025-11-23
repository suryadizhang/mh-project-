"""
Reset Supabase Database - Nuclear Option
Drops ALL tables, resets Alembic, runs migrations from scratch
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Supabase connection
DB_CONFIG = {
    "host": "db.yuchqvpctookhjovvdwi.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": "DkYokZB945vm3itM",
    "port": 5432
}

def reset_database():
    """Drop all tables and reset migration state"""
    print("=" * 80)
    print("🔥 NUCLEAR DATABASE RESET - SUPABASE")
    print("=" * 80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # 1. Drop all schemas (CASCADE will drop all tables)
    print("\n📋 Step 1: Dropping all application schemas...")
    schemas_to_drop = [
        'lead', 'events', 'identity', 'newsletter', 'communications', 'support', 'bookings',
        'core', 'feedback', 'integra', 'marketing'  # Old schemas from previous versions
    ]
    
    for schema in schemas_to_drop:
        try:
            cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            print(f"  ✓ Dropped schema: {schema}")
        except Exception as e:
            print(f"  ⚠️  Could not drop {schema}: {e}")
    
    # 2. Drop all tables in public schema (except Supabase internal tables)
    print("\n📋 Step 2: Dropping all tables in public schema...")
    cur.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT LIKE 'pg_%' 
        AND tablename NOT LIKE 'sql_%'
        AND tablename NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
    """)
    tables = cur.fetchall()
    
    for (table_name,) in tables:
        try:
            cur.execute(f'DROP TABLE IF EXISTS public."{table_name}" CASCADE')
            print(f"  ✓ Dropped table: public.{table_name}")
        except Exception as e:
            print(f"  ⚠️  Could not drop {table_name}: {e}")
    
    # 3. Drop Alembic version table
    print("\n📋 Step 3: Resetting Alembic migration history...")
    try:
        cur.execute("DROP TABLE IF EXISTS alembic_version CASCADE")
        print("  ✓ Dropped alembic_version table")
    except Exception as e:
        print(f"  ⚠️  Could not drop alembic_version: {e}")
    
    # 4. Drop all custom ENUM types (they persist after dropping tables)
    print("\n📋 Step 4: Dropping all custom ENUM types...")
    cur.execute("""
        SELECT t.typname
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typtype = 'e'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    """)
    types = cur.fetchall()
    
    for (type_name,) in types:
        try:
            cur.execute(f'DROP TYPE IF EXISTS {type_name} CASCADE')
            print(f"  ✓ Dropped type: {type_name}")
        except Exception as e:
            print(f"  ⚠️  Could not drop {type_name}: {e}")
    
    if types:
        print(f"  ✓ Dropped {len(types)} custom types")
    else:
        print("  ✓ No custom types to drop")
    
    # 5. Show what's left
    print("\n📋 Step 5: Checking remaining tables...")
    cur.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'storage', 'auth', 'extensions', 'graphql', 'graphql_public', 'vault', 'pgsodium', 'supabase_functions', 'realtime')
        ORDER BY schemaname, tablename
    """)
    remaining = cur.fetchall()
    
    if remaining:
        print(f"\n  ⚠️  {len(remaining)} tables remaining (Supabase internal):")
        for schema, table in remaining:
            print(f"    - {schema}.{table}")
    else:
        print("  ✓ All application tables removed!")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ DATABASE RESET COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: cd apps/backend")
    print("2. Run: alembic upgrade head")
    print("3. Run: python scripts/seed_mock_data.py")
    print("=" * 80)

if __name__ == "__main__":
    response = input("\n⚠️  WARNING: This will DELETE ALL DATA in Supabase database!\nType 'YES' to continue: ")
    if response == "YES":
        reset_database()
    else:
        print("❌ Cancelled")
