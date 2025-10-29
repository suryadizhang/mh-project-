"""Check database tables"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from core.database import engine
from sqlalchemy import text

async def check_tables():
    async with engine.begin() as conn:
        # Check schemas
        result = await conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema') ORDER BY schema_name"))
        schemas = [row[0] for row in result]
        print("\nExisting schemas:")
        print("="*50)
        for schema in schemas:
            print(f"  {schema}")
        print("="*50)
        
        # Check all tables by schema
        result = await conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """))
        
        tables_by_schema = {}
        for row in result:
            schema = row[0]
            table = row[1]
            if schema not in tables_by_schema:
                tables_by_schema[schema] = []
            tables_by_schema[schema].append(table)
        
        print("\nExisting tables by schema:")
        print("="*50)
        for schema in sorted(tables_by_schema.keys()):
            print(f"\n{schema}: ({len(tables_by_schema[schema])} tables)")
            for table in sorted(tables_by_schema[schema]):
                print(f"  - {table}")
        print("="*50)

asyncio.run(check_tables())
