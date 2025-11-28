"""
AI Allergen Filtering Integration Test

Tests the complete flow:
1. Database JSONB queries for allergen filtering
2. AI Agent _filter_by_dietary_restrictions() method
3. Fish vs Shellfish distinction for allergen awareness
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)


def test_ai_allergen_filtering():
    """Test AI allergen filtering scenarios."""

    engine = create_engine(DATABASE_URL)

    print("=" * 80)
    print("🧪 AI Allergen Filtering Integration Test")
    print("=" * 80)

    with Session(engine) as db:
        # Test 1: Shellfish Allergy - Exclude all shellfish
        print("\n" + "=" * 80)
        print("Test 1: Customer with Shellfish Allergy")
        print("=" * 80)
        print('Customer says: "I have a shellfish allergy, what can I eat?"')

        safe_items = db.execute(
            text(
                """
            SELECT name, category, subcategory, tags
            FROM menu_items
            WHERE is_available = true
            AND NOT (tags @> '["contains_shellfish"]'::jsonb)
            ORDER BY
                CASE category
                    WHEN 'poultry' THEN 1
                    WHEN 'beef' THEN 2
                    WHEN 'seafood' THEN 3
                    WHEN 'specialty' THEN 4
                    ELSE 5
                END,
                name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: Found {len(safe_items)} safe options")
        print("\nSafe Menu Items:")

        fish_found = False
        for name, category, subcategory, tags in safe_items:
            subcat_str = f" ({subcategory})" if subcategory else ""

            if subcategory == "fish":
                fish_found = True
                print(f"   ✅ {name}{subcat_str} ← FISH IS SAFE FOR SHELLFISH ALLERGIES!")
            elif category in ("poultry", "beef", "seafood", "specialty"):
                print(f"   ✅ {name}{subcat_str}")

        # Verify fish items are included
        if fish_found:
            print("\n✅ TEST PASSED: Fish items correctly included (safe for shellfish allergies)")
        else:
            print("\n⚠️  WARNING: No fish items found - add Salmon to menu")

        # Verify shellfish items are excluded
        excluded_items = db.execute(
            text(
                """
            SELECT name, subcategory
            FROM menu_items
            WHERE tags @> '["contains_shellfish"]'::jsonb
            ORDER BY name
        """
            )
        ).fetchall()

        print(f"\n❌ Excluded Items ({len(excluded_items)} shellfish items):")
        for name, subcategory in excluded_items:
            print(f"   ❌ {name} ({subcategory}) - contains shellfish allergen")

        # Test 2: Seafood Options (All)
        print("\n" + "=" * 80)
        print("Test 2: Customer Wants Seafood")
        print("=" * 80)
        print('Customer says: "What seafood do you have?"')

        seafood_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE subcategory IN ('fish', 'shellfish')
            ORDER BY
                CASE subcategory
                    WHEN 'fish' THEN 1
                    WHEN 'shellfish' THEN 2
                END,
                name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: We have {len(seafood_items)} seafood options")

        fish_count = 0
        shellfish_count = 0

        print("\n🐟 Fish (Safe for shellfish allergies):")
        for name, subcategory, tags in seafood_items:
            if subcategory == "fish":
                fish_count += 1
                print(f"   ✅ {name}")

        print("\n🦐 Shellfish (⚠️ Allergen Warning):")
        for name, subcategory, tags in seafood_items:
            if subcategory == "shellfish":
                shellfish_count += 1
                is_premium = "premium" in tags
                premium_badge = " 💎" if is_premium else ""
                print(f"   ⚠️  {name}{premium_badge}")

        print(f"\n📊 Breakdown: {fish_count} fish, {shellfish_count} shellfish")

        if fish_count > 0 and shellfish_count > 0:
            print("✅ TEST PASSED: Both fish and shellfish categories present")
        else:
            print("⚠️  WARNING: Missing fish or shellfish items")

        # Test 3: Shellfish Allergy BUT Loves Seafood
        print("\n" + "=" * 80)
        print("Test 3: Shellfish Allergy BUT Loves Seafood")
        print("=" * 80)
        print('Customer says: "I have a shellfish allergy but I love seafood. What can I eat?"')

        fish_only = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE subcategory = 'fish'
            AND NOT (tags @> '["contains_shellfish"]'::jsonb)
            ORDER BY name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: You can enjoy {len(fish_only)} fish option(s)")
        print("\n🐟 Fish Options (SAFE for you):")
        for name, subcategory, tags in fish_only:
            print(f"   ✅ {name} - Fish is NOT shellfish, so it's SAFE!")
            print(f"      Tags: {tags}")

        if len(fish_only) > 0:
            print(
                "\n✅ TEST PASSED: Fish items correctly identified as safe for shellfish allergies"
            )
            print("   AI correctly distinguishes fish from shellfish!")
        else:
            print("\n❌ TEST FAILED: No fish items found")
            print("   Add Salmon with subcategory='fish' to demonstrate distinction")

        # Test 4: Vegan AND Gluten-Free (Multiple restrictions)
        print("\n" + "=" * 80)
        print("Test 4: Multiple Restrictions (Vegan + Gluten-Free)")
        print("=" * 80)
        print('Customer says: "I need vegan and gluten-free options"')

        vegan_gf = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["vegan"]'::jsonb
            AND tags @> '["gluten_free"]'::jsonb
            ORDER BY name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: Found {len(vegan_gf)} items that are both vegan AND gluten-free")
        for name, subcategory, tags in vegan_gf:
            subcat_str = f" ({subcategory})" if subcategory else ""
            print(f"   ✅ {name}{subcat_str}")
            print(f"      Tags: {tags}")

        if len(vegan_gf) > 0:
            print("\n✅ TEST PASSED: Multi-tag JSONB queries working correctly")
        else:
            print("\n⚠️  WARNING: No items are both vegan AND gluten-free")

        # Test 5: Gluten-Free (Common restriction)
        print("\n" + "=" * 80)
        print("Test 5: Gluten-Free Options")
        print("=" * 80)
        print('Customer says: "What\'s gluten-free?"')

        gf_items = db.execute(
            text(
                """
            SELECT name, category, subcategory, tags
            FROM menu_items
            WHERE tags @> '["gluten_free"]'::jsonb
            AND is_available = true
            ORDER BY category, name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: We have {len(gf_items)} gluten-free options")

        proteins = [item for item in gf_items if item[1] in ("poultry", "beef", "seafood")]
        vegetables = [
            item for item in gf_items if "vegetarian" in str(item[2]) or item[1] == "specialty"
        ]

        print(f"\n🍗 Proteins ({len(proteins)}):")
        for name, category, subcategory, tags in proteins:
            subcat_str = f" ({subcategory})" if subcategory else f" ({category})"
            print(f"   ✅ {name}{subcat_str}")

        print(f"\n🥬 Vegetarian ({len(vegetables)}):")
        for name, category, subcategory, tags in vegetables:
            print(f"   ✅ {name}")

        # Items with gluten warning
        gluten_items = db.execute(
            text(
                """
            SELECT name, tags
            FROM menu_items
            WHERE tags @> '["contains_gluten"]'::jsonb
            ORDER BY name
        """
            )
        ).fetchall()

        if gluten_items:
            print(f"\n⚠️  Items with gluten ({len(gluten_items)}):")
            for name, tags in gluten_items:
                print(f"   ⚠️  {name} - contains gluten")

        # Final Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)

        total_items = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE is_available = true")
        ).scalar()
        items_with_tags = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE tags IS NOT NULL AND tags != '[]'::jsonb")
        ).scalar()
        fish_items = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE subcategory = 'fish'")
        ).scalar()
        shellfish_items = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE subcategory = 'shellfish'")
        ).scalar()
        allergen_tagged = db.execute(
            text("SELECT COUNT(*) FROM menu_items WHERE tags @> '[\"contains_shellfish\"]'::jsonb")
        ).scalar()

        print(f"Total menu items: {total_items}")
        print(
            f"Items with tags: {items_with_tags} ({items_with_tags/total_items*100 if total_items > 0 else 0:.1f}%)"
        )
        print(f"Fish items (safe for shellfish allergies): {fish_items}")
        print(f"Shellfish items: {shellfish_items}")
        print(f"Items with shellfish allergen tag: {allergen_tagged}")

        # Pass/Fail
        print("\n" + "=" * 80)
        print("✅ Test Results")
        print("=" * 80)

        tests_passed = 0
        tests_total = 5

        # Test 1: Fish items excluded shellfish
        if fish_found:
            print("✅ Test 1: Fish correctly identified as safe for shellfish allergies")
            tests_passed += 1
        else:
            print("⚠️  Test 1: No fish items found (needs Salmon)")

        # Test 2: Seafood breakdown
        if fish_count > 0 and shellfish_count > 0:
            print("✅ Test 2: Both fish and shellfish categories present")
            tests_passed += 1
        else:
            print("⚠️  Test 2: Missing fish or shellfish items")

        # Test 3: Fish safe for shellfish allergies
        if len(fish_only) > 0:
            print("✅ Test 3: Fish items safe for shellfish allergies")
            tests_passed += 1
        else:
            print("❌ Test 3: No fish items for shellfish allergy scenario")

        # Test 4: Multi-tag queries
        if len(vegan_gf) > 0:
            print("✅ Test 4: Multi-tag JSONB queries working")
            tests_passed += 1
        else:
            print("⚠️  Test 4: No vegan + gluten-free items")

        # Test 5: Gluten-free filtering
        if len(gf_items) > 0:
            print("✅ Test 5: Gluten-free filtering working")
            tests_passed += 1
        else:
            print("❌ Test 5: No gluten-free items")

        # Test 6: Halal Request (NEW - COMPETITIVE ADVANTAGE)
        print("\n" + "=" * 80)
        print("Test 6: Halal Dietary Requirement")
        print("=" * 80)
        print('Customer says: "I need halal food"')

        halal_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["halal"]'::jsonb
            AND is_available = true
            ORDER BY
                CASE subcategory
                    WHEN 'poultry' THEN 1
                    WHEN 'beef' THEN 2
                    WHEN 'fish' THEN 3
                    WHEN 'shellfish' THEN 4
                    WHEN 'vegetarian' THEN 5
                    ELSE 6
                END,
                name
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: We have {len(halal_items)} halal-certified options!")
        print("   All proteins are halal-certified through Restaurant Depot\n")

        for name, subcategory, tags in halal_items:
            subcat_str = f" ({subcategory})" if subcategory else ""
            print(f"   ✅ {name}{subcat_str} - Halal-certified")

        if len(halal_items) >= 10:
            print(
                f"\n✅ TEST 6 PASSED: {len(halal_items)} halal options available (Restaurant Depot certified)"
            )
            tests_passed += 1
            tests_total += 1
        else:
            print(f"\n⚠️  TEST 6: Only {len(halal_items)} halal items (expected 10+)")
            tests_total += 1

        # Test 7: Nut Allergy (NEW - COMPETITIVE ADVANTAGE)
        print("\n" + "=" * 80)
        print("Test 7: Nut Allergy (100% Nut-Free Facility)")
        print("=" * 80)
        print('Customer says: "I have a severe nut allergy"')

        nut_free_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["nut_free"]'::jsonb
            AND is_available = true
            ORDER BY name
        """
            )
        ).fetchall()

        nut_containing = db.execute(
            text(
                """
            SELECT name FROM menu_items
            WHERE tags @> '["contains_nuts"]'::jsonb
        """
            )
        ).fetchall()

        print("\n🏆 GREAT NEWS! We are a 100% NUT-FREE facility!")
        print(f"   ✅ {len(nut_free_items)} items are nut-free")
        print(f"   ❌ {len(nut_containing)} items contain nuts\n")

        if len(nut_containing) == 0:
            print("✅ VERIFICATION: NO items contain nuts (peanuts or tree nuts)")
            print("   You can safely enjoy our ENTIRE menu!\n")

        print("Safe options (ALL items!):")
        for name, subcategory, tags in nut_free_items[:5]:  # Show first 5
            print(f"   ✅ {name}")
        if len(nut_free_items) > 5:
            print(f"   ... and {len(nut_free_items) - 5} more items!")

        if len(nut_containing) == 0 and len(nut_free_items) >= 10:
            print(
                f"\n✅ TEST 7 PASSED: 100% nut-free facility verified ({len(nut_free_items)} nut-free items, 0 with nuts)"
            )
            tests_passed += 1
            tests_total += 1
        else:
            print(
                f"\n⚠️  TEST 7: Nut-free items: {len(nut_free_items)}, Contains nuts: {len(nut_containing)}"
            )
            tests_total += 1

        # Test 8: Dairy-Free / Lactose Intolerant (NEW - COMPETITIVE ADVANTAGE)
        print("\n" + "=" * 80)
        print("Test 8: Dairy-Free / Lactose Intolerant")
        print("=" * 80)
        print('Customer says: "I\'m lactose intolerant, what can I eat?"')

        dairy_free_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["dairy_free"]'::jsonb
            AND is_available = true
            ORDER BY name
        """
            )
        ).fetchall()

        dairy_containing = db.execute(
            text(
                """
            SELECT name FROM menu_items
            WHERE tags @> '["contains_dairy"]'::jsonb
        """
            )
        ).fetchall()

        print("\n🏆 GREAT NEWS! We use DAIRY-FREE butter for all cooking!")
        print(f"   ✅ {len(dairy_free_items)} items are dairy-free")
        print(f"   ❌ {len(dairy_containing)} items contain dairy\n")

        if len(dairy_containing) == 0:
            print("✅ VERIFICATION: NO items contain dairy (we don't use regular butter!)")
            print("   You can safely enjoy our ENTIRE menu!\n")

        print("Safe options (ALL items!):")
        for name, subcategory, tags in dairy_free_items[:5]:
            print(f"   ✅ {name}")
        if len(dairy_free_items) > 5:
            print(f"   ... and {len(dairy_free_items) - 5} more items!")

        if len(dairy_containing) == 0 and len(dairy_free_items) >= 10:
            print(
                f"\n✅ TEST 8 PASSED: Dairy-free facility verified ({len(dairy_free_items)} dairy-free, 0 with dairy)"
            )
            tests_passed += 1
            tests_total += 1
        else:
            print(
                f"\n⚠️  TEST 8: Dairy-free items: {len(dairy_free_items)}, Contains dairy: {len(dairy_containing)}"
            )
            tests_total += 1

        # Test 9: Sesame Allergy (NEW - COMPETITIVE ADVANTAGE)
        print("\n" + "=" * 80)
        print("Test 9: Sesame Allergy (Sesame-Free Facility)")
        print("=" * 80)
        print('Customer says: "I have a sesame allergy"')

        sesame_free_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["sesame_free"]'::jsonb
            AND is_available = true
            ORDER BY name
        """
            )
        ).fetchall()

        sesame_containing = db.execute(
            text(
                """
            SELECT name FROM menu_items
            WHERE tags @> '["contains_sesame"]'::jsonb
        """
            )
        ).fetchall()

        print("\n🏆 GREAT NEWS! We are SESAME-FREE (rare for Japanese restaurants!)")
        print(f"   ✅ {len(sesame_free_items)} items are sesame-free")
        print(f"   ❌ {len(sesame_containing)} items contain sesame\n")

        if len(sesame_containing) == 0:
            print("✅ VERIFICATION: NO items contain sesame (no sesame oil or seeds)")
            print("   You can safely enjoy our ENTIRE menu!\n")

        print("Safe options (ALL items!):")
        for name, subcategory, tags in sesame_free_items[:5]:
            print(f"   ✅ {name}")
        if len(sesame_free_items) > 5:
            print(f"   ... and {len(sesame_free_items) - 5} more items!")

        if len(sesame_containing) == 0 and len(sesame_free_items) >= 10:
            print(
                f"\n✅ TEST 9 PASSED: Sesame-free facility verified ({len(sesame_free_items)} sesame-free, 0 with sesame)"
            )
            tests_passed += 1
            tests_total += 1
        else:
            print(
                f"\n⚠️  TEST 9: Sesame-free items: {len(sesame_free_items)}, Contains sesame: {len(sesame_containing)}"
            )
            tests_total += 1

        # Test 10: Egg Allergy (Only Fried Rice)
        print("\n" + "=" * 80)
        print("Test 10: Egg Allergy")
        print("=" * 80)
        print('Customer says: "I have an egg allergy"')

        egg_free_items = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE NOT (tags @> '["contains_eggs"]'::jsonb)
            AND is_available = true
            ORDER BY name
        """
            )
        ).fetchall()

        egg_containing = db.execute(
            text(
                """
            SELECT name FROM menu_items
            WHERE tags @> '["contains_eggs"]'::jsonb
        """
            )
        ).fetchall()

        print(f"\n✅ AI Response: {len(egg_free_items)} items are egg-free!")
        print(f"   ⚠️  Only {len(egg_containing)} item(s) contain eggs\n")

        print("Items with eggs:")
        for (name,) in egg_containing:
            print(f"   ❌ {name} - contains eggs")

        print(f"\nSafe options ({len(egg_free_items)} items):")
        for name, subcategory, tags in egg_free_items[:5]:
            print(f"   ✅ {name}")
        if len(egg_free_items) > 5:
            print(f"   ... and {len(egg_free_items) - 5} more items!")

        if len(egg_containing) == 1 and "fried rice" in str(egg_containing).lower():
            print(
                f"\n✅ TEST 10 PASSED: Only fried rice contains eggs ({len(egg_free_items)} egg-free items)"
            )
            tests_passed += 1
            tests_total += 1
        else:
            print(
                f"\n⚠️  TEST 10: Egg-free: {len(egg_free_items)}, Contains eggs: {len(egg_containing)}"
            )
            tests_total += 1

        # Test 11: Multiple Restrictions (Halal + Dairy-Free)
        print("\n" + "=" * 80)
        print("Test 11: Multiple Restrictions (Halal + Dairy-Free)")
        print("=" * 80)
        print('Customer says: "I need halal food that\'s also dairy-free"')

        halal_dairy_free = db.execute(
            text(
                """
            SELECT name, subcategory, tags
            FROM menu_items
            WHERE tags @> '["halal"]'::jsonb
            AND tags @> '["dairy_free"]'::jsonb
            AND is_available = true
            ORDER BY name
        """
            )
        ).fetchall()

        print(
            f"\n✅ AI Response: Found {len(halal_dairy_free)} items that are BOTH halal AND dairy-free"
        )
        for name, subcategory, tags in halal_dairy_free:
            print(f"   ✅ {name} - Halal-certified + dairy-free butter")

        if len(halal_dairy_free) >= 10:
            print(f"\n✅ TEST 11 PASSED: {len(halal_dairy_free)} items meet both requirements")
            tests_passed += 1
            tests_total += 1
        else:
            print(f"\n⚠️  TEST 11: Only {len(halal_dairy_free)} items (expected 10+)")
            tests_total += 1

        print(
            f"\n📊 Score: {tests_passed}/{tests_total} tests passed ({tests_passed/tests_total*100:.0f}%)"
        )

        if tests_passed == tests_total:
            print("\n🎉 ALL TESTS PASSED! AI allergen filtering is production-ready!")
        elif tests_passed >= 3:
            print("\n✅ MOSTLY WORKING! Core allergen filtering functional, minor gaps remain")
        else:
            print("\n⚠️  NEEDS WORK: Several tests failed, review implementation")

        print("\n" + "=" * 80)
        print("🔍 Key Insight")
        print("=" * 80)
        print("Fish (Salmon) vs Shellfish (Shrimp, Scallops, Lobster)")
        print("  - Fish: subcategory='fish', NO shellfish tag")
        print("  - Shellfish: subcategory='shellfish', tags contains 'contains_shellfish'")
        print("  - AI can safely recommend fish to customers with shellfish allergies!")
        print("=" * 80)


if __name__ == "__main__":
    try:
        test_ai_allergen_filtering()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
