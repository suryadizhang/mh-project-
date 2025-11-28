"""
Simple test for menu item tags without complex imports.

Tests database queries for allergen filtering.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)


def test_menu_tags():
    """Test menu item tags directly via database queries."""

    engine = create_engine(DATABASE_URL)

    print("=" * 80)
    print("🧪 Testing Menu Tags System")
    print("=" * 80)

    with Session(engine) as db:
        # Test 1: Check if columns exist
        print("\n📋 Test 1: Check database schema")
        print("-" * 80)

        result = db.execute(
            text(
                """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'menu_items'
            AND column_name IN ('subcategory', 'tags')
            ORDER BY column_name
        """
            )
        )

        columns = result.fetchall()

        if columns:
            print("✅ Columns found in menu_items table:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
        else:
            print("❌ ERROR: subcategory and tags columns not found!")
            print("   Run migration first: alembic upgrade head")
            return

        # Test 2: Check existing data
        print("\n📋 Test 2: Check existing menu items")
        print("-" * 80)

        result = db.execute(
            text(
                """
            SELECT
                name,
                category,
                subcategory,
                tags,
                is_available
            FROM menu_items
            WHERE is_available = true
            ORDER BY category, name
            LIMIT 10
        """
            )
        )

        items = result.fetchall()

        if items:
            print(f"✅ Found {len(items)} menu items (showing first 10):")
            for item in items:
                name, category, subcategory, tags, available = item
                tags_str = str(tags) if tags else "[]"
                subcat_str = subcategory or "(none)"
                print(
                    f"   - {name}: category={category}, subcategory={subcat_str}, tags={tags_str}"
                )
        else:
            print("⚠️  No menu items found in database")

        # Test 3: Count items with subcategories
        print("\n📋 Test 3: Items with subcategories")
        print("-" * 80)

        result = db.execute(
            text(
                """
            SELECT subcategory, COUNT(*) as count
            FROM menu_items
            WHERE subcategory IS NOT NULL
            GROUP BY subcategory
            ORDER BY count DESC
        """
            )
        )

        subcategories = result.fetchall()

        if subcategories:
            print("✅ Subcategories in use:")
            for subcat, count in subcategories:
                print(f"   - {subcat}: {count} items")
        else:
            print("⚠️  No items have subcategories yet")
            print("   Assign subcategories via Admin UI or seed script")

        # Test 4: Count items with tags
        print("\n📋 Test 4: Items with tags")
        print("-" * 80)

        result = db.execute(
            text(
                """
            SELECT
                name,
                subcategory,
                tags
            FROM menu_items
            WHERE tags IS NOT NULL AND tags != '[]'::jsonb
            ORDER BY name
            LIMIT 10
        """
            )
        )

        tagged_items = result.fetchall()

        if tagged_items:
            print(f"✅ Found {len(tagged_items)} items with tags (showing first 10):")
            for name, subcategory, tags in tagged_items:
                print(f"   - {name} ({subcategory or 'no subcategory'}): {tags}")
        else:
            print("⚠️  No items have tags yet")
            print("   Add tags via Admin UI or seed script")

        # Test 5: Test JSONB queries (allergen filtering)
        print("\n📋 Test 5: JSONB allergen queries")
        print("-" * 80)

        # Query: Items with shellfish allergen
        result = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["contains_shellfish"]'::jsonb
        """
            )
        )

        shellfish_allergen = result.fetchall()

        if shellfish_allergen:
            print(f"🦐 Items tagged with 'contains_shellfish': {len(shellfish_allergen)}")
            for name, subcategory, tags in shellfish_allergen:
                print(f"   - {name} ({subcategory}): {tags}")
        else:
            print("ℹ️  No items tagged with 'contains_shellfish' yet")

        # Query: Fish items (safe for shellfish allergies)
        result = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE subcategory = 'fish'
        """
            )
        )

        fish_items = result.fetchall()

        if fish_items:
            print(f"\n🐟 Fish items (safe for shellfish allergies): {len(fish_items)}")
            for name, subcategory, tags in fish_items:
                print(f"   - {name}: {tags}")
        else:
            print("\nℹ️  No items with subcategory 'fish' yet")

        # Query: Shellfish items
        result = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE subcategory = 'shellfish'
        """
            )
        )

        shellfish_items = result.fetchall()

        if shellfish_items:
            print(f"\n🦐 Shellfish items: {len(shellfish_items)}")
            for name, subcategory, tags in shellfish_items:
                print(f"   - {name}: {tags}")
        else:
            print("\nℹ️  No items with subcategory 'shellfish' yet")

        # Test 6: Test index performance
        print("\n📋 Test 6: Check indexes")
        print("-" * 80)

        result = db.execute(
            text(
                """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'menu_items'
            AND (indexname LIKE '%subcategory%' OR indexname LIKE '%tags%')
        """
            )
        )

        indexes = result.fetchall()

        if indexes:
            print("✅ Indexes found:")
            for idx_name, idx_def in indexes:
                print(f"   - {idx_name}")
                print(f"     {idx_def}")
        else:
            print("⚠️  No indexes found for subcategory or tags")
            print("   Migration may not have created indexes correctly")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Summary")
        print("=" * 80)

        total = db.execute(text("SELECT COUNT(*) FROM menu_items")).scalar()
        with_subcat = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE subcategory IS NOT NULL")
        ).scalar()
        with_tags = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE tags IS NOT NULL AND tags != '[]'::jsonb")
        ).scalar()

        print(f"Total menu items: {total}")
        print(
            f"Items with subcategory: {with_subcat} ({with_subcat/total*100 if total > 0 else 0:.1f}%)"
        )
        print(f"Items with tags: {with_tags} ({with_tags/total*100 if total > 0 else 0:.1f}%)")

        if with_subcat == 0 or with_tags == 0:
            print("\n⚠️  ACTION REQUIRED:")
            print("   1. Columns exist ✅")
            print("   2. Need to populate data via:")
            print("      - Admin UI (Pricing page)")
            print("      - Seed script (apps/backend/seed_data/menu_items_with_subcategories.py)")
        else:
            print("\n✅ System ready for allergen-aware AI filtering!")


if __name__ == "__main__":
    try:
        test_menu_tags()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nCheck:")
        print("  - Database is running: postgresql://localhost:5432/my_hibachi_dev")
        print("  - Migration was run: alembic upgrade head")
