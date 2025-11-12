import asyncio
import asyncpg
import os


async def check():
    db_url = os.getenv("SUPABASE_DB_URL", "postgresql://postgres@localhost:5432/postgres")
    conn = await asyncpg.connect(db_url)
    row = await conn.fetchrow(
        "SELECT upsell_item, pitch_template FROM upsell_rules WHERE upsell_item LIKE '%Third%Protein%' LIMIT 1"
    )
    if row:
        print(f"\n✅ Found: {row['upsell_item']}")
        print(f"Pitch: {row['pitch_template']}\n")
    else:
        print("\n❌ No Third Protein add-on found\n")
    await conn.close()


asyncio.run(check())
