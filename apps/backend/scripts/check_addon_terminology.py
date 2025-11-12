#!/usr/bin/env python3
"""Quick check: Verify pitch templates use 'add-on' terminology from website"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_terminology():
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(database_url)

    print("\n🔍 Checking pitch templates for 'add-on' terminology:\n")
    print("=" * 60)

    rows = await conn.fetch(
        """
        SELECT upsell_item, pitch_template 
        FROM upsell_rules 
        WHERE upsell_item IN ('Third Protein Add-on', 'Gyoza', 'Yakisoba Noodles', 'Add-on Offer - General')
        ORDER BY success_rate DESC
    """
    )

    for row in rows:
        print(f"\n📌 Item: {row['upsell_item']}")
        print(f"   Pitch: {row['pitch_template']}")

        # Check for "add-on" terminology
        if "add-on" in row["pitch_template"].lower():
            print("   ✅ Uses 'add-on' terminology (matches website)")
        else:
            print("   ⚠️  Missing 'add-on' terminology")

    print("\n" + "=" * 60)
    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_terminology())
