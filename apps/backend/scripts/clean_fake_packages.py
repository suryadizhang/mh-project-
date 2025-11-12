#!/usr/bin/env python3
"""Remove fake package data from database"""
import asyncio
import asyncpg
import os


async def clean_fake_data():
    db_url = os.getenv("SUPABASE_DB_URL", "postgresql://postgres@localhost:5432/postgres")
    conn = await asyncpg.connect(db_url)

    print("\n🔍 Checking for fake packages in database...\n")

    # Find fake packages
    fake_packages = await conn.fetch(
        """SELECT id, upsell_item, pitch_template 
           FROM upsell_rules 
           WHERE upsell_item LIKE '%Package%' 
           OR pitch_template LIKE '%package%'
           ORDER BY id"""
    )

    if fake_packages:
        print(f"❌ Found {len(fake_packages)} fake package entries:\n")
        for pkg in fake_packages:
            print(f"   ID: {pkg['id']}")
            print(f"   Item: {pkg['upsell_item']}")
            print(f"   Pitch: {pkg['pitch_template'][:80]}...")
            print()

        # Delete them
        print("🗑️  Deleting fake packages...")
        deleted = await conn.execute(
            """DELETE FROM upsell_rules 
               WHERE upsell_item LIKE '%Package%' 
               OR pitch_template LIKE '%package%'"""
        )
        print(f"✅ Deleted: {deleted}\n")
    else:
        print("✅ No fake packages found!\n")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(clean_fake_data())
