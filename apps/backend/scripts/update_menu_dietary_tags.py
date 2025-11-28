"""
Update Menu Items with Dietary-Friendly Tags

This script updates all existing menu items with accurate allergen and dietary tags
based on My Hibachi's ACTUAL ingredients:

✅ ADVANTAGES:
- 100% nut-free facility
- Sesame-free (no sesame oil/seeds)
- Dairy-free butter used
- Gluten-free soy sauce available
- Halal-certified (Restaurant Depot)
- No pork products
- No cooking alcohol (sake is drink only)

⚠️ ALLERGENS:
- Shellfish (shrimp, scallops, lobster only - optional)
- Eggs (fried rice only)

Run: python -m apps.backend.scripts.update_menu_dietary_tags
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv

backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from: {env_file}\n")
else:
    print(f"⚠️  No .env file found at: {env_file}\n")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL_SYNC not found in environment variables")

print(
    f"📡 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}\n"
)
engine = create_engine(DATABASE_URL)


def update_menu_items():
    """Update all menu items with accurate dietary tags"""

    with Session(engine) as db:
        print("🔄 Updating Menu Items with Dietary-Friendly Tags\n")
        print("=" * 70)

        # Menu item updates based on actual ingredients
        updates = [
            {
                "name": "Chicken",
                "tags": [
                    "high_protein",
                    "grilled",
                    "halal",  # Restaurant Depot certified
                    "kosher_style",  # No pork, dairy-free, accommodating
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                ],
                "notes": "Halal-certified poultry with dairy-free butter",
            },
            {
                "name": "NY Strip Steak",
                "tags": [
                    "high_protein",
                    "grilled",
                    "halal",  # Restaurant Depot certified
                    "kosher_style",  # No pork, dairy-free, accommodating
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                ],
                "notes": "Halal-certified beef with dairy-free butter",
            },
            {
                "name": "Salmon",
                "tags": [
                    "seafood",
                    "fish",
                    "high_protein",
                    "grilled",
                    "premium",
                    "halal",  # Seafood is halal
                    "kosher_style",  # Fish with fins/scales = kosher!
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "gluten_free",  # No gluten ingredients
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                    "contains_fish",  # FDA allergen (obviously!)
                ],
                "notes": "Perfect for halal, kosher-style, multiple allergies",
            },
            {
                "name": "Shrimp",
                "tags": [
                    "contains_shellfish",  # ⚠️ ALLERGEN
                    "seafood",
                    "shellfish",
                    "high_protein",
                    "grilled",
                    "halal",  # Seafood is halal
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "dairy_free",  # Dairy-free butter
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                ],
                "notes": "Shellfish allergen - customer can opt out",
            },
            {
                "name": "Scallops",
                "tags": [
                    "contains_shellfish",  # ⚠️ ALLERGEN
                    "seafood",
                    "shellfish",
                    "high_protein",
                    "grilled",
                    "premium",
                    "halal",  # Seafood is halal
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "dairy_free",  # Dairy-free butter
                    "gluten_free",  # No gluten ingredients
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                ],
                "notes": "Premium shellfish allergen - customer can opt out",
            },
            {
                "name": "Lobster Tail",
                "tags": [
                    "contains_shellfish",  # ⚠️ ALLERGEN
                    "seafood",
                    "shellfish",
                    "high_protein",
                    "grilled",
                    "premium",
                    "customer_favorite",
                    "halal",  # Seafood is halal
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "dairy_free",  # Dairy-free butter
                    "gluten_free",  # No gluten ingredients
                    "can_be_gluten_free",  # Gluten-free soy sauce option
                ],
                "notes": "Premium shellfish allergen - customer can opt out",
            },
            {
                "name": "Tofu",
                "tags": [
                    "vegetarian",
                    "vegan",
                    "high_protein",
                    "tofu",
                    "halal",  # Plant-based is halal
                    "kosher_style",  # Pareve (neutral)
                    "dairy_free",  # No dairy
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                    "gluten_free",  # Tofu itself is GF
                    "can_be_gluten_free",  # Can use GF soy sauce
                ],
                "notes": "Perfect vegan/vegetarian protein option",
            },
            {
                "name": "Vegetables",
                "tags": [
                    "vegetarian",
                    "vegan",
                    "gluten_free",
                    "halal",  # Vegetables are halal
                    "kosher_style",  # Pareve (neutral)
                    "dairy_free",  # No dairy
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                ],
                "notes": "Naturally allergen-friendly",
            },
            {
                "name": "Grilled Vegetables",
                "tags": [
                    "vegetarian",
                    "vegan",
                    "gluten_free",
                    "grilled",
                    "halal",  # Vegetables are halal
                    "kosher_style",  # Pareve (neutral)
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                ],
                "notes": "Grilled with dairy-free butter",
            },
            {
                "name": "Hibachi Fried Rice",
                "tags": [
                    "vegetarian",
                    "fried",
                    "contains_eggs",  # ⚠️ ONLY major allergen!
                    "halal",  # Halal ingredients
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame oil
                    "can_be_gluten_free",  # Can use GF soy sauce
                ],
                "notes": "Only contains eggs - WAY better than typical hibachi!",
            },
            {
                "name": "Adult Hibachi Experience",
                "tags": [
                    "customizable",
                    "can_be_gluten_free",
                    "halal",  # All proteins halal-certified
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                ],
                "notes": "Customizable to dietary needs",
            },
            {
                "name": "Child Hibachi Experience",
                "tags": [
                    "customizable",
                    "kid_friendly",
                    "can_be_gluten_free",
                    "halal",  # All proteins halal-certified
                    "dairy_free",  # Dairy-free butter
                    "nut_free",  # 100% nut-free facility
                    "sesame_free",  # No sesame products
                ],
                "notes": "Kid-friendly and customizable",
            },
        ]

        # Execute updates
        updated_count = 0
        for item in updates:
            try:
                tags_json = json.dumps(item["tags"])

                # Update using parameterized query (PostgreSQL style)
                result = db.execute(
                    text(
                        """
                        UPDATE menu_items
                        SET tags = :tags::jsonb
                        WHERE name = :name
                    """
                    ).bindparams(tags=tags_json, name=item["name"])
                )

                if result.rowcount > 0:
                    print(f"✅ Updated: {item['name']}")
                    print(f"   Tags: {', '.join(item['tags'][:3])}... ({len(item['tags'])} total)")
                    print(f"   Notes: {item['notes']}")
                    print()
                    updated_count += 1
                else:
                    print(f"⚠️  NOT FOUND: {item['name']}")
                    print()

            except Exception as e:
                print(f"❌ ERROR updating {item['name']}: {e}")
                print()

        # Commit transaction
        db.commit()

        print("=" * 70)
        print(f"\n📊 Summary: {updated_count}/{len(updates)} items updated successfully")

        # Query updated items to verify
        print("\n🔍 Verification: Querying updated items...\n")

        result = db.execute(
            text(
                """
            SELECT name, subcategory, tags, base_price
            FROM menu_items
            ORDER BY
                CASE
                    WHEN subcategory = 'poultry' THEN 1
                    WHEN subcategory = 'beef' THEN 2
                    WHEN subcategory = 'fish' THEN 3
                    WHEN subcategory = 'shellfish' THEN 4
                    WHEN subcategory = 'vegetarian' THEN 5
                    WHEN subcategory IS NULL THEN 6
                    ELSE 7
                END,
                name
        """
            )
        )

        print("🏆 ALLERGEN-FRIENDLY MENU ITEMS:\n")

        for row in result:
            name, subcategory, tags, price = row
            tags_list = tags if isinstance(tags, list) else []

            # Categorize items
            is_halal = "halal" in tags_list
            is_kosher_style = "kosher_style" in tags_list
            is_allergen_free = (
                "nut_free" in tags_list and "sesame_free" in tags_list and "dairy_free" in tags_list
            )
            has_shellfish = "contains_shellfish" in tags_list
            has_eggs = "contains_eggs" in tags_list

            # Build status line
            status = []
            if is_halal:
                status.append("✅ HALAL")
            if is_kosher_style:
                status.append("✅ KOSHER-STYLE")
            if is_allergen_free:
                status.append("🏆 ALLERGEN-FRIENDLY")
            if has_shellfish:
                status.append("⚠️ SHELLFISH")
            if has_eggs:
                status.append("⚠️ EGGS")

            print(f"{name} ({subcategory or 'experience'})")
            print(f"  Price: ${price:.2f}")
            print(f"  Status: {' | '.join(status) if status else 'Standard'}")
            print(
                f"  Tags ({len(tags_list)}): {', '.join(tags_list[:4])}{'...' if len(tags_list) > 4 else ''}"
            )
            print()

        # Summary statistics
        print("=" * 70)
        print("\n📊 TAG USAGE STATISTICS:\n")

        tag_counts = db.execute(
            text(
                """
            SELECT
                jsonb_array_elements_text(tags) as tag,
                COUNT(*) as count
            FROM menu_items
            WHERE tags IS NOT NULL
            GROUP BY tag
            ORDER BY count DESC, tag
        """
            )
        )

        for tag, count in tag_counts:
            print(f"  {tag:<25} → {count} items")

        print("\n" + "=" * 70)
        print("\n🎉 All menu items updated with dietary-friendly tags!")
        print("\n✅ COMPETITIVE ADVANTAGES:")
        print("   - 100% nut-free facility (safety for severe allergies)")
        print("   - Sesame-free (rare for Japanese restaurants)")
        print("   - Dairy-free butter (lactose intolerant friendly)")
        print("   - Gluten-free soy sauce available (celiac friendly)")
        print("   - Halal-certified (Restaurant Depot)")
        print("   - Kosher-friendly (no pork, dairy-free, salmon OK)")
        print("   - Only 2 allergens: Shellfish (optional), Eggs (fried rice only)")
        print("\n⚠️ REMINDER: Shared cooking surfaces - cross-contamination possible")
        print("   Include disclaimer in AI responses and FAQ")


if __name__ == "__main__":
    try:
        update_menu_items()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
