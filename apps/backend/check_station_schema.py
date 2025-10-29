"""Check Station table schema in database."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from sqlalchemy import text
from core.database import AsyncSessionLocal


async def check_schema():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema='identity' AND table_name='stations'
            ORDER BY ordinal_position
        """))
        
        print("Station Table Schema:")
        print("=" * 60)
        for row in result.fetchall():
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"  {row[0]:<30} {row[1]:<20} {nullable}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_schema())
