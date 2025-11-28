#!/usr/bin/env python3
"""
Minimal migration script using psycopg2 directly (no ORM dependencies).
Updates menu items with dietary-friendly tags.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

# Load environment
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
load_dotenv(env_file)
print("✅ Loaded environment\n")

# Get database URL and convert from SQLAlchemy format to psycopg2 format
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
# Convert postgresql+psycopg2:// to postgresql://
DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

# Menu item updates
MENU_UPDATES = {
    "Chicken": [
        "poultry",
        "high_protein",
        "grilled",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "can_be_gluten_free",
    ],
    "NY Strip Steak": [
        "beef",
        "high_protein",
        "grilled",
        "premium",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "can_be_gluten_free",
    ],
    "Salmon": [
        "seafood",
        "fish",
        "high_protein",
        "grilled",
        "premium",
        "contains_fish",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "gluten_free",
        "can_be_gluten_free",
    ],
    "Shrimp": [
        "contains_shellfish",
        "seafood",
        "shellfish",
        "high_protein",
        "grilled",
        "halal",
        "nut_free",
        "sesame_free",
        "dairy_free",
        "can_be_gluten_free",
    ],
    "Scallops": [
        "contains_shellfish",
        "seafood",
        "shellfish",
        "high_protein",
        "grilled",
        "premium",
        "halal",
        "nut_free",
        "sesame_free",
        "dairy_free",
        "can_be_gluten_free",
    ],
    "Lobster Tail": [
        "contains_shellfish",
        "seafood",
        "shellfish",
        "high_protein",
        "grilled",
        "premium",
        "halal",
        "nut_free",
        "sesame_free",
        "dairy_free",
        "can_be_gluten_free",
    ],
    "Tofu": [
        "vegetarian",
        "vegan",
        "high_protein",
        "tofu",
        "grilled",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "gluten_free",
        "can_be_gluten_free",
    ],
    "Vegetables": [
        "vegetarian",
        "vegan",
        "grilled",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "gluten_free",
        "can_be_gluten_free",
    ],
    "Grilled Vegetables": [
        "vegetarian",
        "vegan",
        "grilled",
        "halal",
        "kosher_style",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "gluten_free",
        "can_be_gluten_free",
    ],
    "Hibachi Fried Rice": [
        "vegetarian",
        "fried",
        "contains_eggs",
        "halal",
        "dairy_free",
        "nut_free",
        "sesame_free",
        "can_be_gluten_free",
    ],
    "Adult Hibachi Experience": ["customizable", "can_be_gluten_free"],
    "Child Hibachi Experience": ["customizable", "kid_friendly", "can_be_gluten_free"],
}


def main():
    print("🔄 Updating Menu Items with Dietary-Friendly Tags\n")
    print("=" * 70)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    updated_count = 0

    for name, tags in MENU_UPDATES.items():
        try:
            # Update using psycopg2 Json adapter for JSONB
            cur.execute("UPDATE menu_items SET tags = %s WHERE name = %s", (Json(tags), name))

            if cur.rowcount > 0:
                print(f"✅ Updated: {name} ({len(tags)} tags)")
                updated_count += 1
            else:
                print(f"⚠️  NOT FOUND: {name}")

        except Exception as e:
            print(f"❌ ERROR updating {name}: {e}")

    conn.commit()

    print("\n" + "=" * 70)
    print(f"\n📊 Summary: {updated_count}/{len(MENU_UPDATES)} items updated successfully\n")

    # Verify
    print("🔍 Verification:\n")
    cur.execute("SELECT name, subcategory, tags FROM menu_items ORDER BY subcategory, name")

    tag_stats = {}

    for row in cur.fetchall():
        name, subcategory, tags = row
        tags_list = tags if tags else []

        for tag in tags_list:
            tag_stats[tag] = tag_stats.get(tag, 0) + 1

        status = "⚠️ SHELLFISH" if "contains_shellfish" in tags_list else "Standard"
        print(f"{name} ({subcategory or 'N/A'}) - {status}")
        if len(tags_list) > 5:
            print(f"  Tags ({len(tags_list)}): {', '.join(tags_list[:3])}...")
        else:
            print(f"  Tags ({len(tags_list)}): {', '.join(tags_list)}")
        print()

    print("=" * 70)
    print("\n📊 TAG USAGE STATISTICS:\n")
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        print(f"  {tag:30} → {count} items")

    print("\n" + "=" * 70)
    print("\n🎉 Migration Complete!")
    print("\n✅ COMPETITIVE ADVANTAGES:")
    print(f"   - 100% nut-free facility (nut_free → {tag_stats.get('nut_free', 0)} items)")
    print(f"   - Sesame-free facility (sesame_free → {tag_stats.get('sesame_free', 0)} items)")
    print(f"   - Dairy-free butter (dairy_free → {tag_stats.get('dairy_free', 0)} items)")
    print(
        f"   - Gluten-free soy sauce (can_be_gluten_free → {tag_stats.get('can_be_gluten_free', 0)} items)"
    )
    print(f"   - Halal-certified (halal → {tag_stats.get('halal', 0)} items)")
    print(f"   - Kosher-friendly (kosher_style → {tag_stats.get('kosher_style', 0)} items)")
    print("   - Only 2 allergens: Shellfish (optional), Eggs (fried rice only)")

    print("\n⚠️ REMINDER: Shared cooking surfaces - cross-contamination possible\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
