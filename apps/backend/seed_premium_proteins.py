"""
Add premium proteins to menu: Salmon, Scallops, Lobster

This demonstrates the fish vs shellfish distinction for allergen awareness:
- Salmon (fish) = SAFE for shellfish allergies
- Scallops, Lobster (shellfish) = ALLERGEN WARNING
"""

import os
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)


def add_premium_proteins():
    """Add Salmon, Scallops, and Lobster to menu."""

    engine = create_engine(DATABASE_URL)

    print("=" * 80)
    print("🦐 Adding Premium Proteins: Salmon, Scallops, Lobster")
    print("=" * 80)

    with Session(engine) as db:
        # Check if items already exist
        print("\n📋 Checking for existing proteins...")

        existing = db.execute(
            text(
                """
            SELECT name FROM menu_items
            WHERE name IN ('Salmon', 'Scallops', 'Lobster Tail')
        """
            )
        ).fetchall()

        existing_names = [row[0] for row in existing]

        if existing_names:
            print(f"⚠️  Found existing items: {', '.join(existing_names)}")
            print("   Skipping duplicate inserts")

        # Add Salmon (FISH - Safe for shellfish allergies)
        if "Salmon" not in existing_names:
            print("\n📝 Adding Salmon (fish - SAFE for shellfish allergies)...")
            salmon_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                INSERT INTO menu_items (
                    id,
                    name,
                    description,
                    category,
                    subcategory,
                    tags,
                    base_price,
                    is_premium,
                    is_available,
                    display_order,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    'Salmon',
                    'Fresh Atlantic salmon grilled to perfection with hibachi seasonings',
                    'seafood',
                    'fish',
                    '["seafood", "fish", "gluten_free", "high_protein", "grilled", "premium"]'::jsonb,
                    8.00,
                    true,
                    true,
                    40,
                    NOW(),
                    NOW()
                )
            """
                ),
                {"id": salmon_id},
            )
            print("   ✅ Added: Salmon (subcategory: fish)")

        # Add Scallops (SHELLFISH - Allergen)
        if "Scallops" not in existing_names:
            print("\n📝 Adding Scallops (shellfish - ⚠️ ALLERGEN)...")
            scallops_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                INSERT INTO menu_items (
                    id,
                    name,
                    description,
                    category,
                    subcategory,
                    tags,
                    base_price,
                    is_premium,
                    is_available,
                    display_order,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    'Scallops',
                    'Jumbo sea scallops seared hibachi-style',
                    'seafood',
                    'shellfish',
                    '["contains_shellfish", "seafood", "shellfish", "gluten_free", "high_protein", "grilled", "premium"]'::jsonb,
                    10.00,
                    true,
                    true,
                    41,
                    NOW(),
                    NOW()
                )
            """
                ),
                {"id": scallops_id},
            )
            print("   ✅ Added: Scallops (subcategory: shellfish, tags: contains_shellfish)")

        # Add Lobster Tail (SHELLFISH - Premium Allergen)
        if "Lobster Tail" not in existing_names:
            print("\n📝 Adding Lobster Tail (shellfish - ⚠️ ALLERGEN, Premium)...")
            lobster_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                INSERT INTO menu_items (
                    id,
                    name,
                    description,
                    category,
                    subcategory,
                    tags,
                    base_price,
                    is_premium,
                    is_available,
                    display_order,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    'Lobster Tail',
                    'Premium cold-water lobster tail grilled with garlic butter',
                    'seafood',
                    'shellfish',
                    '["contains_shellfish", "seafood", "shellfish", "gluten_free", "high_protein", "grilled", "premium", "customer_favorite"]'::jsonb,
                    15.00,
                    true,
                    true,
                    42,
                    NOW(),
                    NOW()
                )
            """
                ),
                {"id": lobster_id},
            )
            print("   ✅ Added: Lobster Tail (subcategory: shellfish, tags: contains_shellfish)")

        # Commit changes
        db.commit()

        print("\n✅ Premium proteins added!")

        # Verify with allergen breakdown
        print("\n" + "=" * 80)
        print("📊 Seafood Menu Breakdown")
        print("=" * 80)

        # Fish items (SAFE for shellfish allergies)
        fish_result = db.execute(
            text(
                """
            SELECT name, tags
            FROM menu_items
            WHERE subcategory = 'fish'
            ORDER BY name
        """
            )
        )

        fish_items = fish_result.fetchall()

        print("\n🐟 FISH (SAFE for shellfish allergies):")
        if fish_items:
            for name, tags in fish_items:
                print(f"   ✅ {name}")
                print(f"      Tags: {tags}")
        else:
            print("   (none)")

        # Shellfish items (ALLERGEN)
        shellfish_result = db.execute(
            text(
                """
            SELECT name, tags
            FROM menu_items
            WHERE subcategory = 'shellfish'
            ORDER BY display_order
        """
            )
        )

        shellfish_items = shellfish_result.fetchall()

        print("\n🦐 SHELLFISH (⚠️ ALLERGEN - contains shellfish):")
        for name, tags in shellfish_items:
            is_premium = "premium" in tags
            premium_badge = " 💎 PREMIUM" if is_premium else ""
            print(f"   ⚠️  {name}{premium_badge}")
            print(f"      Tags: {tags}")

        # Test AI query: Shellfish allergy filter
        print("\n" + "=" * 80)
        print("🧪 AI Query Test: Customer with Shellfish Allergy")
        print("=" * 80)

        safe_result = db.execute(
            text(
                """
            SELECT name, subcategory, category
            FROM menu_items
            WHERE is_available = true
            AND NOT (tags @> '["contains_shellfish"]'::jsonb)
            AND category IN ('poultry', 'beef', 'seafood', 'specialty')
            ORDER BY
                CASE category
                    WHEN 'poultry' THEN 1
                    WHEN 'beef' THEN 2
                    WHEN 'seafood' THEN 3
                    ELSE 4
                END,
                name
        """
            )
        )

        safe_items = safe_result.fetchall()

        print("\n✅ SAFE for customer with shellfish allergy:")
        for name, subcategory, category in safe_items:
            subcat_info = f" ({subcategory})" if subcategory else ""
            if subcategory == "fish":
                print(f"   ✅ {name}{subcat_info} ← Fish is SAFE!")
            else:
                print(f"   ✅ {name}{subcat_info}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Summary")
        print("=" * 80)

        total_proteins = db.execute(
            text(
                """
            SELECT COUNT(*) FROM menu_items
            WHERE category IN ('poultry', 'beef', 'seafood')
        """
            )
        ).scalar()

        fish_count = db.execute(
            text(
                """
            SELECT COUNT(*) FROM menu_items WHERE subcategory = 'fish'
        """
            )
        ).scalar()

        shellfish_count = db.execute(
            text(
                """
            SELECT COUNT(*) FROM menu_items WHERE subcategory = 'shellfish'
        """
            )
        ).scalar()

        allergen_count = db.execute(
            text(
                """
            SELECT COUNT(*) FROM menu_items
            WHERE tags @> '["contains_shellfish"]'::jsonb
        """
            )
        ).scalar()

        print(f"Total protein options: {total_proteins}")
        print(f"Fish (safe for shellfish allergies): {fish_count}")
        print(f"Shellfish (allergen): {shellfish_count}")
        print(f"Items with shellfish allergen tag: {allergen_count}")

        print("\n✅ Database ready for AI allergen filtering!")
        print("\n🧪 Test Scenarios:")
        print('   1. AI Query: "I have a shellfish allergy, what can I eat?"')
        print("      Expected: Chicken, Steak, Salmon ✅, Tofu, Vegetables")
        print("      Excluded: Shrimp ❌, Scallops ❌, Lobster ❌")
        print()
        print('   2. AI Query: "What seafood do you have?"')
        print(
            "      Expected: Salmon (fish), Shrimp (shellfish), Scallops (shellfish), Lobster (shellfish)"
        )
        print()
        print('   3. AI Query: "I love seafood but have shellfish allergy"')
        print("      Expected: Salmon ✅ (fish is safe!)")
        print("      Excluded: Shrimp, Scallops, Lobster ❌")


if __name__ == "__main__":
    try:
        add_premium_proteins()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
