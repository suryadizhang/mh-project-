"""Check database tables"""
import asyncio
from api.app.database import engine
from sqlalchemy import text

async def check_tables():
    async with engine.begin() as conn:
        # Check schemas
        result = await conn.execute(text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"))
        schemas = [row[0] for row in result]
        print("\nExisting schemas:")
        print("="*50)
        for schema in schemas:
            print(f"  {schema}")
        print("="*50)
        
        # Check tables
        result = await conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('bookings', 'payments', 'users')
            ORDER BY table_schema, table_name
        """))
        print("\nExisting tables:")
        print("="*50)
        for row in result:
            print(f"  {row[0]}.{row[1]}")
        print("="*50)

asyncio.run(check_tables())
