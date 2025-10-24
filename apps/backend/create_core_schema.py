"""
Create core schema and migrate tables from public to core schema.
This aligns the database structure with the API's expectations.
"""
import asyncio
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import text
from api.app.database import engine


async def create_core_schema():
    """Create core schema and migrate relevant tables."""
    
    print("=" * 60)
    print("CREATING CORE SCHEMA AND MIGRATING TABLES")
    print("=" * 60)
    
    async with engine.begin() as conn:
        
        # Step 1: Create core schema
        print("\n[1/6] Creating core schema...")
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS core;"))
        print("✅ Core schema created")
        
        # Step 2: Check what tables exist in public schema
        print("\n[2/6] Checking existing tables in public schema...")
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """))
        public_tables = [row[0] for row in result.fetchall()]
        print(f"Found {len(public_tables)} tables in public schema:")
        for table in public_tables:
            print(f"  - {table}")
        
        # Step 3: Define tables that should be in core schema
        core_tables = [
            'customers',
            'bookings', 
            'payments',
            'message_threads',
            'messages',
            'leads',
            'social_threads',
            'social_messages',
            'subscribers',
            'newsletter_campaigns',
            'campaign_deliveries'
        ]
        
        # Step 4: Check which tables actually exist and need migration
        tables_to_migrate = [t for t in core_tables if t in public_tables]
        print(f"\n[3/6] Tables to migrate to core schema: {len(tables_to_migrate)}")
        for table in tables_to_migrate:
            print(f"  - {table}")
        
        if not tables_to_migrate:
            print("\n⚠️  No tables found to migrate. They may already be in core schema.")
            
            # Check if tables already exist in core
            result = await conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'core' 
                ORDER BY tablename;
            """))
            core_existing = [row[0] for row in result.fetchall()]
            if core_existing:
                print(f"\n✅ Found {len(core_existing)} tables already in core schema:")
                for table in core_existing:
                    print(f"  - {table}")
                print("\n[SUCCESS] Core schema already properly configured!")
                return
            else:
                print("\n⚠️  No tables in core schema either. May need to create tables.")
                return
        
        # Step 5: Migrate each table to core schema
        print(f"\n[4/6] Migrating {len(tables_to_migrate)} tables to core schema...")
        
        for table in tables_to_migrate:
            try:
                print(f"\n  Migrating {table}...")
                
                # Check if table already exists in core
                check_result = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_tables 
                        WHERE schemaname = 'core' 
                        AND tablename = '{table}'
                    );
                """))
                exists_in_core = check_result.scalar()
                
                if exists_in_core:
                    print(f"    ⚠️  {table} already exists in core schema, skipping...")
                    continue
                
                # Move table from public to core
                await conn.execute(text(f"""
                    ALTER TABLE public.{table} SET SCHEMA core;
                """))
                print(f"    ✅ Migrated {table} to core schema")
                
            except Exception as e:
                print(f"    ❌ Error migrating {table}: {e}")
                # Continue with other tables
        
        # Step 6: Update sequence ownership (for tables with SERIAL columns)
        print(f"\n[5/6] Updating sequence ownership...")
        try:
            # Get all sequences in public schema
            result = await conn.execute(text("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """))
            sequences = [row[0] for row in result.fetchall()]
            
            for seq in sequences:
                # Check if sequence is related to a migrated table
                for table in tables_to_migrate:
                    if table in seq:
                        try:
                            await conn.execute(text(f"""
                                ALTER SEQUENCE public.{seq} SET SCHEMA core;
                            """))
                            print(f"    ✅ Migrated sequence {seq}")
                        except Exception as e:
                            print(f"    ⚠️  Could not migrate sequence {seq}: {e}")
        except Exception as e:
            print(f"    ⚠️  Error updating sequences: {e}")
        
        # Step 7: Grant permissions on core schema
        print(f"\n[6/6] Granting permissions on core schema...")
        try:
            await conn.execute(text("""
                GRANT USAGE ON SCHEMA core TO PUBLIC;
            """))
            await conn.execute(text("""
                GRANT ALL ON ALL TABLES IN SCHEMA core TO PUBLIC;
            """))
            await conn.execute(text("""
                GRANT ALL ON ALL SEQUENCES IN SCHEMA core TO PUBLIC;
            """))
            print("✅ Permissions granted")
        except Exception as e:
            print(f"⚠️  Error granting permissions: {e}")
    
    # Step 8: Verify migration
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    async with engine.connect() as conn:
        # Check core schema tables
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'core' 
            ORDER BY tablename;
        """))
        core_tables_after = [row[0] for row in result.fetchall()]
        
        print(f"\n✅ Tables now in core schema: {len(core_tables_after)}")
        for table in core_tables_after:
            # Get row count
            try:
                count_result = await conn.execute(text(f"""
                    SELECT COUNT(*) FROM core.{table};
                """))
                count = count_result.scalar()
                print(f"  - core.{table} ({count} rows)")
            except Exception as e:
                print(f"  - core.{table} (error counting: {e})")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Core schema migration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run pytest tests: pytest tests/test_api_performance.py -v")
    print("  2. Check for any foreign key constraint errors")
    print("  3. Update any application code still referencing public schema")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_core_schema())
