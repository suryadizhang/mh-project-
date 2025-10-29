import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres.djmggqfemqvylggdzsdb:Mh2024@aws-0-us-west-1.pooler.supabase.com:6543/postgres')
    result = await conn.fetch("SELECT typname FROM pg_type WHERE typname IN ('roletype', 'permissiontype')")
    print("Existing enums:")
    for row in result:
        print(f"  - {row['typname']}")
    await conn.close()

asyncio.run(check())
