"""
Test script for allergen filtering with new tags system.

Tests:
1. Shellfish allergy filtering
2. Fish vs shellfish distinction
3. Gluten-free filtering
4. Vegan/vegetarian filtering
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

from models.knowledge_base import MenuItem
from api.ai.agents.menu_agent import MenuAgent
from core.config import settings


def test_allergen_filtering():
    """Test allergen filtering with database tags."""

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)

    with Session(engine) as db:
        print("=" * 80)
        print("🧪 Testing Allergen Filtering with Tags System")
        print("=" * 80)

        # Initialize Menu Agent
        agent = MenuAgent(db=db)

        # Test 1: Shellfish allergy
        print("\n📋 Test 1: Customer has shellfish allergy")
        print("-" * 80)
        result = agent._filter_by_dietary_restrictions(
            {"restrictions": ["shellfish-free"], "guest_count": 4}
        )

        print(f"✅ Found {result['count']} safe items")
        print(f"⚠️  Warnings: {result.get('warnings', [])}")

        # Check if any shellfish items made it through
        shellfish_items = [
            item
            for item in result["safe_items"]
            if "contains_shellfish" in item.get("tags", [])
            or item.get("subcategory") == "shellfish"
        ]

        if shellfish_items:
            print(f"❌ FAILED: Found {len(shellfish_items)} shellfish items in 'safe' list:")
            for item in shellfish_items:
                print(
                    f"   - {item['name']} (subcategory: {item.get('subcategory')}, tags: {item.get('tags')})"
                )
        else:
            print("✅ PASSED: No shellfish items in safe list")

        # Check if fish items are included (safe for shellfish allergies)
        fish_items = [item for item in result["safe_items"] if item.get("subcategory") == "fish"]

        if fish_items:
            print(f"✅ PASSED: Found {len(fish_items)} fish items (safe for shellfish allergies):")
            for item in fish_items[:3]:  # Show first 3
                print(f"   - {item['name']} (subcategory: {item.get('subcategory')})")
        else:
            print("⚠️  WARNING: No fish items found (may not be seeded yet)")

        # Test 2: Gluten-free
        print("\n📋 Test 2: Customer needs gluten-free options")
        print("-" * 80)
        result = agent._filter_by_dietary_restrictions(
            {"restrictions": ["gluten-free"], "guest_count": 4}
        )

        print(f"✅ Found {result['count']} gluten-free items")
        print(f"⚠️  Warnings: {result.get('warnings', [])}")

        # Test 3: Vegan
        print("\n📋 Test 3: Customer is vegan")
        print("-" * 80)
        result = agent._filter_by_dietary_restrictions(
            {"restrictions": ["vegan"], "guest_count": 4}
        )

        print(f"✅ Found {result['count']} vegan items")

        vegan_items = [item for item in result["safe_items"] if "vegan" in item.get("tags", [])]
        print(f"✅ {len(vegan_items)} items explicitly tagged as vegan")

        # Test 4: Multiple restrictions
        print("\n📋 Test 4: Customer has shellfish allergy AND is vegetarian")
        print("-" * 80)
        result = agent._filter_by_dietary_restrictions(
            {"restrictions": ["shellfish-free", "vegetarian"], "guest_count": 4}
        )

        print(f"✅ Found {result['count']} safe items")
        print(f"⚠️  Warnings: {result.get('warnings', [])}")

        # Test 5: Database query examples
        print("\n📋 Test 5: Raw database queries")
        print("-" * 80)

        # Query 1: All shellfish items
        shellfish_stmt = select(MenuItem).where(MenuItem.subcategory == "shellfish")
        shellfish = db.execute(shellfish_stmt).scalars().all()
        print(f"🦐 Shellfish items in database: {len(shellfish)}")
        for item in shellfish:
            print(f"   - {item.name} (tags: {item.tags})")

        # Query 2: All fish items (safe for shellfish allergies)
        fish_stmt = select(MenuItem).where(MenuItem.subcategory == "fish")
        fish = db.execute(fish_stmt).scalars().all()
        print(f"\n🐟 Fish items in database (safe for shellfish allergies): {len(fish)}")
        for item in fish:
            print(f"   - {item.name} (tags: {item.tags})")

        # Query 3: Items with allergen tags
        allergen_stmt = select(MenuItem).where(MenuItem.tags.op("@>")('["contains_shellfish"]'))
        allergen_items = db.execute(allergen_stmt).scalars().all()
        print(f"\n⚠️  Items tagged with 'contains_shellfish': {len(allergen_items)}")
        for item in allergen_items:
            print(f"   - {item.name} (subcategory: {item.subcategory}, tags: {item.tags})")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)

        total_items = db.execute(select(MenuItem)).scalars().all()
        items_with_subcategory = [i for i in total_items if i.subcategory]
        items_with_tags = [i for i in total_items if i.tags]

        print(f"Total menu items: {len(total_items)}")
        print(f"Items with subcategory: {len(items_with_subcategory)}")
        print(f"Items with tags: {len(items_with_tags)}")

        if len(items_with_subcategory) == 0 or len(items_with_tags) == 0:
            print("\n⚠️  WARNING: Database not seeded with subcategories/tags yet!")
            print("   Run seed script to populate example menu items.")
        else:
            print("\n✅ Database has subcategories and tags - system ready!")


if __name__ == "__main__":
    test_allergen_filtering()
