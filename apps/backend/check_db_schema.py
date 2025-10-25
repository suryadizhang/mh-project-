"""
Quick script to check if Lead tables exist in the database
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)
print(f"Added {src_path} to Python path")

from sqlalchemy import text
from api.app.database import engine as async_engine

async def check_lead_tables():
    """Check if lead schema and tables exist"""
    print("🔍 Checking database schema for Lead tables...\n")
    
    async with async_engine.begin() as conn:
        # Check if lead schema exists
        result = await conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'lead'
        """))
        schema_exists = result.fetchone() is not None
        
        if schema_exists:
            print("✅ Schema 'lead' exists")
        else:
            print("❌ Schema 'lead' does NOT exist")
            return False
        
        # Check for lead tables
        tables_to_check = ['leads', 'lead_contacts', 'lead_context', 'lead_events']
        
        for table in tables_to_check:
            result = await conn.execute(text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'lead' AND table_name = '{table}'
            """))
            exists = result.fetchone() is not None
            
            if exists:
                # Count rows
                count_result = await conn.execute(text(f"SELECT COUNT(*) FROM lead.{table}"))
                count = count_result.fetchone()[0]
                print(f"✅ Table 'lead.{table}' exists ({count} rows)")
            else:
                print(f"❌ Table 'lead.{table}' does NOT exist")
        
        # Check for enums
        print("\n🔍 Checking enums...")
        result = await conn.execute(text("""
            SELECT typname 
            FROM pg_type 
            WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'lead')
            AND typtype = 'e'
        """))
        enums = result.fetchall()
        
        if enums:
            print(f"✅ Found {len(enums)} enum types:")
            for enum in enums:
                print(f"   - {enum[0]}")
        else:
            print("⚠️  No enum types found in lead schema")
        
        print("\n✅ Database schema check complete!")
        return True

if __name__ == "__main__":
    try:
        asyncio.run(check_lead_tables())
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
