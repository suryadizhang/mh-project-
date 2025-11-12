import asyncio
import asyncpg


async def check():
    conn = await asyncpg.connect(
        "postgresql://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres"
    )
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
