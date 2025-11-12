#!/usr/bin/env python3
"""
WEEK 3 PHASE 3: UPSELL TRIGGERS TESTING
Tests contextual upsell rules based on customer context
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def get_upsell_suggestions(conn, party_size: int, current_selections: list):
    """Query upsell rules directly from database"""
    query = """
        SELECT 
            upsell_item,
            pitch_template,
            tone_adaptation,
            success_rate
        FROM upsell_rules
        WHERE is_active = true
        AND min_party_size <= $1
        AND (max_party_size >= $1 OR max_party_size IS NULL)
        ORDER BY success_rate DESC NULLS LAST
        LIMIT 3
    """

    rows = await conn.fetch(query, party_size)

    suggestions = []
    for row in rows:
        if row["upsell_item"] not in current_selections:
            suggestions.append(
                {
                    "item": row["upsell_item"],
                    "pitch": row["pitch_template"],
                    "tone_adaptation": row["tone_adaptation"],
                    "success_rate": float(row["success_rate"]) if row["success_rate"] else None,
                }
            )

    return suggestions


async def test_upsell_triggers():
    """Test upsell triggers with various customer contexts"""

    print("=" * 60)
    print("🎯 WEEK 3 PHASE 3: UPSELL TRIGGERS TESTING")
    print("=" * 60)
    print()

    # Connect to database
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    print("✅ Database connected")
    print()

    tests_passed = 0
    tests_total = 0

    test_cases = [
        {
            "name": "Initial Offer → General prompt",
            "party_size": 25,
            "current_selections": [],
            "expected_keywords": ["extras", "add-on", "appetizer"],
            "should_suggest": True,
            "min_suggestions": 1,
            "description": "First, offer general: 'Would you like any extras?'",
        },
        {
            "name": "Customer interested → Show add-on options from website data",
            "party_size": 30,
            "current_selections": ["Add-on Offer - General"],
            "expected_keywords": ["add-on", "add", "extra"],
            "should_suggest": True,
            "min_suggestions": 2,
            "description": "AI offers add-ons based on actual website data (dynamic, subject to change)",
        },
        {
            "name": "Small party → Same conversational flow",
            "party_size": 10,
            "current_selections": [],
            "expected_keywords": ["extras", "add-on"],
            "should_suggest": True,
            "min_suggestions": 1,
            "description": "All parties get conversational offer",
        },
        {
            "name": "Already selected protein → Offer other options",
            "party_size": 20,
            "current_selections": ["Third Protein Add-on"],
            "expected_keywords": ["gyoza", "noodles", "edamame"],
            "should_suggest": True,
            "should_not_include": ["third protein add-on"],
            "description": "Show other items if one selected",
        },
        {
            "name": "Large party → Can mention premium if they ask",
            "party_size": 60,
            "current_selections": ["Add-on Offer - General", "Third Protein Add-on", "Gyoza"],
            "expected_keywords": ["noodles", "edamame"],
            "should_suggest": True,
            "description": "Natural flow continues",
        },
    ]

    for test in test_cases:
        print(f"🎯 Test: {test['name']}")
        tests_total += 1

        try:
            # Get upsell suggestions
            suggestions = await get_upsell_suggestions(
                conn, party_size=test["party_size"], current_selections=test["current_selections"]
            )

            # Check if upsell was suggested
            has_suggestions = len(suggestions) > 0

            # Validate expectation
            if test["should_suggest"]:
                if has_suggestions:
                    # Check for minimum suggestions if specified
                    min_required = test.get("min_suggestions", 1)
                    if len(suggestions) < min_required:
                        print(
                            f"   ❌ FAIL: Expected at least {min_required} suggestions, got {len(suggestions)}"
                        )
                        print(f"   Suggestions: {suggestions}")
                        print()
                        continue

                    # Check for expected keywords in suggestions
                    suggestions_text = str(suggestions).lower()
                    found_keywords = [
                        kw for kw in test["expected_keywords"] if kw in suggestions_text
                    ]

                    # Check should_not_include
                    excluded = test.get("should_not_include", [])
                    found_excluded = [kw for kw in excluded if kw in suggestions_text]

                    if found_excluded:
                        print(f"   ❌ FAIL: Found excluded keywords: {', '.join(found_excluded)}")
                        print(f"   Suggestions: {suggestions_text[:150]}...")
                    elif found_keywords or not test["expected_keywords"]:
                        print(f"   ✅ PASS: {len(suggestions)} upsell(s) suggested")
                        if found_keywords:
                            print(f"   Keywords: {', '.join(found_keywords)}")
                        print(f"   Items: {[s['item'] for s in suggestions]}")
                        tests_passed += 1
                    else:
                        print("   ❌ FAIL: Upsell suggested but missing expected keywords")
                        print(f"   Expected: {test['expected_keywords']}")
                        print(f"   Got: {suggestions_text[:150]}...")
                else:
                    print("   ❌ FAIL: Should suggest upsell but none found")
            else:
                if not has_suggestions:
                    print("   ✅ PASS: Correctly skipped upsell")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL: Should NOT suggest upsell but got: {suggestions}")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

        print()

    await conn.close()

    # Summary
    print("=" * 60)
    print("📊 UPSELL TRIGGERS TEST SUMMARY")
    print("=" * 60)
    print()
    print(f"Tests Passed: {tests_passed}/{tests_total} ({tests_passed/tests_total*100:.1f}%)")
    print()
    print("=" * 60)

    if tests_passed >= tests_total * 0.7:  # 70% threshold
        print("✅ PHASE 3: UPSELL TRIGGERS - PASSED!")
        print(f"Accuracy: {tests_passed/tests_total*100:.1f}% (threshold: 70%)")
        return 0
    else:
        print("⚠️  PHASE 3: UPSELL TRIGGERS - NEEDS IMPROVEMENT")
        print(f"Accuracy: {tests_passed/tests_total*100:.1f}% (threshold: 70%)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_upsell_triggers())
    sys.exit(exit_code)
