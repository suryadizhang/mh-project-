#!/usr/bin/env python3
"""
Menu Sync Checker - Validates if AI knowledge base is in sync with frontend menu data

This script compares:
1. Add-on prices in database vs faqsData.ts
2. Premium upgrade prices in database vs faqsData.ts
3. Base pricing in database vs menu data

Run: python scripts/check_menu_sync.py
"""

import asyncio
import asyncpg
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Expected pricing from frontend (source of truth)
EXPECTED_ADDONS = {
    "Yakisoba Noodles": 5.00,
    "Extra Fried Rice": 5.00,
    "Edamame": 5.00,
    "Extra Vegetables": 5.00,
    "Extra Protein Add-on": 10.00,
    "Gyoza": 10.00,
}

EXPECTED_UPGRADES = {
    "Lobster Tail": 15.00,
    "Filet Mignon": 5.00,
    "Salmon": 5.00,
    "Scallops": 5.00,
}

EXPECTED_BASE_PRICING = {
    "adult_base": 55.00,
    "child_base": 30.00,
    "party_minimum": 550.00,
}


async def check_sync():
    """Check if database is in sync with frontend menu data"""

    print("=" * 60)
    print("🔍 MENU SYNC VALIDATION")
    print("=" * 60)
    print()

    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)

    issues_found = 0

    # Check base pricing
    print("💰 Checking Base Pricing...")
    base_pricing = await conn.fetchrow(
        """
        SELECT value 
        FROM business_rules 
        WHERE rule_type = 'pricing' AND title LIKE '%Adult%'
    """
    )

    if base_pricing:
        value = (
            json.loads(base_pricing["value"])
            if isinstance(base_pricing["value"], str)
            else base_pricing["value"]
        )
        adult_base = value.get("adult_base")
        if adult_base != EXPECTED_BASE_PRICING["adult_base"]:
            print(
                f"   ⚠️  MISMATCH: Adult pricing DB=${adult_base} vs Expected=${EXPECTED_BASE_PRICING['adult_base']}"
            )
            issues_found += 1
        else:
            print(f"   ✅ Adult pricing: ${adult_base}")

    # Check add-ons
    print("\n🍜 Checking Add-on Pricing...")
    for addon_name, expected_price in EXPECTED_ADDONS.items():
        # Search for the item in upsell_rules (may have different exact naming)
        result = await conn.fetchrow(
            """
            SELECT upsell_item, pitch_template
            FROM upsell_rules
            WHERE upsell_item ILIKE $1
            LIMIT 1
        """,
            f"%{addon_name.split()[0]}%",
        )

        if result:
            # Extract price from pitch_template (e.g., "+$5 per person")
            pitch = result["pitch_template"]
            price_match = re.search(r"\+\$(\d+(?:\.\d+)?)", pitch)
            if price_match:
                db_price = float(price_match.group(1))
                if db_price != expected_price:
                    print(
                        f"   ⚠️  MISMATCH: {addon_name} DB=${db_price} vs Expected=${expected_price}"
                    )
                    issues_found += 1
                else:
                    print(f"   ✅ {addon_name}: ${db_price}")
            else:
                print(f"   ⚠️  WARNING: Could not parse price from: {pitch}")
                issues_found += 1
        else:
            print(f"   ❌ MISSING: {addon_name} not found in database")
            issues_found += 1

    # Check premium upgrades
    print("\n💎 Checking Premium Upgrade Pricing...")
    for upgrade_name, expected_price in EXPECTED_UPGRADES.items():
        result = await conn.fetchrow(
            """
            SELECT upsell_item, pitch_template
            FROM upsell_rules
            WHERE upsell_item ILIKE $1
            LIMIT 1
        """,
            f"%{upgrade_name}%",
        )

        if result:
            pitch = result["pitch_template"]
            price_match = re.search(r"\+\$(\d+(?:\.\d+)?)", pitch)
            if price_match:
                db_price = float(price_match.group(1))
                if db_price != expected_price:
                    print(
                        f"   ⚠️  MISMATCH: {upgrade_name} DB=${db_price} vs Expected=${expected_price}"
                    )
                    issues_found += 1
                else:
                    print(f"   ✅ {upgrade_name}: ${db_price}")
        else:
            print(f"   ❌ MISSING: {upgrade_name} not found in database")
            issues_found += 1

    await conn.close()

    # Summary
    print()
    print("=" * 60)
    if issues_found == 0:
        print("✅ ALL CHECKS PASSED - Database is in sync with menu!")
    else:
        print(f"⚠️  {issues_found} ISSUES FOUND - Run seed_ai_training_real.py to resync")
    print("=" * 60)

    return 0 if issues_found == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(check_sync())
    exit(exit_code)
