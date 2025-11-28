"""
Update existing menu items with subcategories and allergen tags.

This script adds:
- Subcategories (fish, shellfish, poultry, beef, etc.)
- Allergen tags (contains_shellfish, contains_gluten, etc.)
- Dietary tags (vegan, vegetarian, gluten_free, etc.)
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)


def update_menu_items():
    """Update menu items with subcategories and allergen tags."""

    engine = create_engine(DATABASE_URL)

    print("=" * 80)
    print("🔄 Updating Menu Items with Subcategories and Allergen Tags")
    print("=" * 80)

    with Session(engine) as db:
        # Update Chicken
        print("\n📝 Updating Chicken...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'poultry',
                tags = '["gluten_free", "high_protein"]'::jsonb
            WHERE name = 'Chicken'
        """
            )
        )

        # Update NY Strip Steak
        print("📝 Updating NY Strip Steak...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'beef',
                tags = '["gluten_free", "high_protein"]'::jsonb
            WHERE name = 'NY Strip Steak'
        """
            )
        )

        # Update Shrimp (SHELLFISH - contains allergen)
        print("📝 Updating Shrimp (shellfish allergen)...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'shellfish',
                tags = '["contains_shellfish", "seafood", "high_protein", "grilled"]'::jsonb
            WHERE name = 'Shrimp'
        """
            )
        )

        # Update Tofu
        print("📝 Updating Tofu...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'vegetarian',
                tags = '["vegetarian", "vegan", "gluten_free", "high_protein", "tofu"]'::jsonb
            WHERE name = 'Tofu'
        """
            )
        )

        # Update Vegetables
        print("📝 Updating Vegetables...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'vegetarian',
                tags = '["vegetarian", "vegan", "gluten_free"]'::jsonb
            WHERE name = 'Vegetables'
        """
            )
        )

        # Update Grilled Vegetables
        print("📝 Updating Grilled Vegetables...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = 'vegetarian',
                tags = '["vegetarian", "vegan", "gluten_free", "grilled"]'::jsonb
            WHERE name = 'Grilled Vegetables'
        """
            )
        )

        # Update Hibachi Fried Rice (contains gluten from soy sauce)
        print("📝 Updating Hibachi Fried Rice...")
        db.execute(
            text(
                """
            UPDATE menu_items
            SET
                subcategory = NULL,
                tags = '["vegetarian", "fried", "contains_gluten"]'::jsonb
            WHERE name = 'Hibachi Fried Rice'
        """
            )
        )

        # Commit changes
        db.commit()

        print("\n✅ All updates complete!")

        # Verify updates
        print("\n" + "=" * 80)
        print("📊 Verification")
        print("=" * 80)

        result = db.execute(
            text(
                """
            SELECT
                name,
                subcategory,
                tags
            FROM menu_items
            WHERE is_available = true
            ORDER BY
                CASE
                    WHEN subcategory = 'poultry' THEN 1
                    WHEN subcategory = 'beef' THEN 2
                    WHEN subcategory = 'fish' THEN 3
                    WHEN subcategory = 'shellfish' THEN 4
                    WHEN subcategory = 'vegetarian' THEN 5
                    ELSE 6
                END,
                name
        """
            )
        )

        items = result.fetchall()

        print("\n📋 Updated Menu Items:")
        for name, subcategory, tags in items:
            subcat_str = subcategory or "(none)"

            # Check for allergens
            allergen_warning = ""
            if tags and "contains_shellfish" in tags:
                allergen_warning = " ⚠️ SHELLFISH ALLERGEN"
            elif tags and "contains_gluten" in tags:
                allergen_warning = " ⚠️ GLUTEN"

            print(f"   - {name}: {subcat_str}{allergen_warning}")
            print(f"     Tags: {tags}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Summary")
        print("=" * 80)

        total = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE is_available = true")
        ).scalar()
        with_subcat = db.execute(
            text(
                "SELECT COUNT(*) FROM menu_items WHERE subcategory IS NOT NULL AND is_available = true"
            )
        ).scalar()
        shellfish = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE tags @> '[\"contains_shellfish\"]'::jsonb")
        ).scalar()

        print(f"Total active menu items: {total}")
        print(
            f"Items with subcategory: {with_subcat} ({with_subcat/total*100 if total > 0 else 0:.1f}%)"
        )
        print(f"Items with shellfish allergen: {shellfish}")

        print("\n✅ Database ready for allergen-aware AI filtering!")
        print("\nNext steps:")
        print("  1. Test AI agent with: 'I have a shellfish allergy'")
        print("  2. Test Admin UI: Update menu items via Pricing page")
        print("  3. Add more proteins: Salmon (fish), Scallops (shellfish), etc.")


if __name__ == "__main__":
    try:
        update_menu_items()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
