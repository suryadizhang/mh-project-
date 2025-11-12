#!/usr/bin/env python3
"""Quick debug script to check business_rules table structure"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()


async def check_structure():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)

    print("=== BUSINESS_RULES TABLE STRUCTURE ===\n")

    # Get column types
    print("📋 Column Types:")
    columns = await conn.fetch(
        """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'business_rules'
    """
    )
    for col in columns:
        print(f"   {col['column_name']}: {col['data_type']}")

    print("\n📝 Sample Rows:")
    rows = await conn.fetch("SELECT * FROM business_rules LIMIT 3")
    for row in rows:
        print(f"\n   ID: {row['id']}")
        print(f"   Type: {row['rule_type']}")
        print(f"   Title: {row['title']}")
        print(f"   Value type: {type(row['value'])}")
        print(f"   Value: {row['value']}")

    print("\n\n💳 Deposit/Cancellation Policies:")
    policies = await conn.fetch(
        """
        SELECT rule_type, title, value 
        FROM business_rules 
        WHERE rule_type IN ('deposit', 'cancellation')
    """
    )
    for policy in policies:
        print(f"\n   {policy['rule_type'].upper()}: {policy['title']}")
        print(f"   Value: {policy['value']}")

    print("\n\n🎯 Upsell Rules:")
    upsell_count = await conn.fetchval("SELECT COUNT(*) FROM upsell_rules")
    print(f"   Total rules: {upsell_count}")

    if upsell_count > 0:
        print("\n   All Upsell Items:")
        upsells = await conn.fetch(
            "SELECT upsell_item, pitch_template, min_party_size, success_rate FROM upsell_rules ORDER BY success_rate DESC"
        )
        for u in upsells:
            print(f"   • {u['upsell_item']}")
            print(f"     Min Party: {u['min_party_size']} | Priority: {u['success_rate']}")
            print(f"     Pitch: {u['pitch_template'][:80]}...")
            print()

    await conn.close()


if __name__ == "__main__":
    asyncio.run(check_structure())
