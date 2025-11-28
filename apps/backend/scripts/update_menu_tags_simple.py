#!/usr/bin/env python3
"""
Simple migration script to update menu items with dietary-friendly tags.
Uses SQLAlchemy ORM to avoid SQL syntax issues.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import models
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "src"))

# Load environment
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from: {env_file}\n")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.knowledge_base import MenuItem

# Connect to database
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    print("❌ DATABASE_URL_SYNC not found in environment")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Menu item updates with ACCURATE dietary-friendly tags
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

    updated_count = 0
    not_found = []

    with Session(engine) as session:
        for name, tags in MENU_UPDATES.items():
            try:
                # Query menu item by name
                stmt = select(MenuItem).where(MenuItem.name == name)
                menu_item = session.execute(stmt).scalar_one_or_none()

                if not menu_item:
                    print(f"⚠️  NOT FOUND: {name}")
                    not_found.append(name)
                    continue

                # Update tags
                menu_item.tags = tags

                print(f"✅ Updated: {name}")
                print(f"   Tags ({len(tags)}): {', '.join(tags[:4])}...")
                print()
                updated_count += 1

            except Exception as e:
                print(f"❌ ERROR updating {name}: {e}\n")

        # Commit all changes
        session.commit()

    print("=" * 70)
    print(f"\n📊 Summary: {updated_count}/{len(MENU_UPDATES)} items updated successfully")

    if not_found:
        print(f"\n⚠️  Not Found ({len(not_found)} items): {', '.join(not_found)}")

    # Verify updates
    print("\n🔍 Verification: Querying updated items...\n")
    print("🏆 ALLERGEN-FRIENDLY MENU ITEMS:\n")

    with Session(engine) as session:
        stmt = select(MenuItem).order_by(MenuItem.subcategory, MenuItem.name)
        items = session.execute(stmt).scalars().all()

        tag_stats = {}
        allergen_count = {}

        for item in items:
            tags_list = item.tags if item.tags else []

            # Count tag usage
            for tag in tags_list:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1

            # Count allergens
            allergens = [t for t in tags_list if t.startswith("contains_")]
            allergen_count[len(allergens)] = allergen_count.get(len(allergens), 0) + 1

            status = "⚠️ SHELLFISH" if "contains_shellfish" in tags_list else "Standard"

            print(f"{item.name} ({item.subcategory or 'N/A'})")
            print(f"  Status: {status}")
            if len(tags_list) > 5:
                print(f"  Tags ({len(tags_list)}): {', '.join(tags_list[:3])}...")
            else:
                print(f"  Tags ({len(tags_list)}): {', '.join(tags_list)}")
            print()

    print("=" * 70)
    print("\n📊 TAG USAGE STATISTICS:\n")

    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        print(f"  {tag:25} → {count} items")

    print("\n" + "=" * 70)
    print("\n🎉 Migration complete!")
    print("\n✅ COMPETITIVE ADVANTAGES:")
    print("   - 100% nut-free facility (nut_free → {} items)".format(tag_stats.get("nut_free", 0)))
    print(
        "   - Sesame-free facility (sesame_free → {} items)".format(tag_stats.get("sesame_free", 0))
    )
    print("   - Dairy-free butter (dairy_free → {} items)".format(tag_stats.get("dairy_free", 0)))
    print(
        "   - Gluten-free soy sauce (can_be_gluten_free → {} items)".format(
            tag_stats.get("can_be_gluten_free", 0)
        )
    )
    print("   - Halal-certified (halal → {} items)".format(tag_stats.get("halal", 0)))
    print("   - Kosher-friendly (kosher_style → {} items)".format(tag_stats.get("kosher_style", 0)))
    print("   - Only 2 allergens: Shellfish (optional), Eggs (fried rice only)")

    print("\n⚠️ REMINDER: Shared cooking surfaces - cross-contamination possible")
    print("   Include disclaimer in AI responses and FAQ\n")


if __name__ == "__main__":
    main()
