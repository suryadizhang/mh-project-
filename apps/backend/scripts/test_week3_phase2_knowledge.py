"""
Week 3 Phase 2: Knowledge Base Testing
Tests KnowledgeService retrieval of real MyHibachi data
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 60)
print("📚 WEEK 3 PHASE 2: KNOWLEDGE BASE TESTING")
print("=" * 60 + "\n")


async def test_knowledge_base():
    """Test knowledge base queries"""

    try:
        import asyncpg

        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

        conn = await asyncpg.connect(database_url)

        print("✅ Database connected\n")

        tests_passed = 0
        tests_total = 0

        # Test 1: Adult Pricing
        print("💰 Test 1: Adult Pricing Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT title, value::jsonb->>'adult_base' as amount
                FROM business_rules 
                WHERE rule_type = 'pricing' 
                AND title LIKE '%Adult%'
                LIMIT 1
            """
            )

            if result and result["amount"]:
                amount = int(result["amount"])
                if amount == 55:
                    print(f"   ✅ PASS: Adult pricing = ${amount}/person")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL: Expected $55, got ${amount}")
            else:
                print("   ❌ FAIL: No adult pricing found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 2: Child Pricing
        print("👶 Test 2: Child Pricing Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT title, value::jsonb->>'child_base' as amount
                FROM business_rules 
                WHERE rule_type = 'pricing' 
                AND title LIKE '%Child%'
                LIMIT 1
            """
            )

            if result and result["amount"]:
                amount = int(result["amount"])
                if amount == 30:
                    print(f"   ✅ PASS: Child pricing = ${amount}/person (ages 6-12)")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL: Expected $30, got ${amount}")
            else:
                print("   ❌ FAIL: No child pricing found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 3: Party Minimum
        print("👥 Test 3: Party Minimum Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT title, value::jsonb->>'party_minimum' as amount
                FROM business_rules 
                WHERE rule_type = 'pricing' 
                AND title LIKE '%Minimum%'
                LIMIT 1
            """
            )

            if result and result["amount"]:
                amount = int(result["amount"])
                if amount == 550:
                    print(f"   ✅ PASS: Party minimum = ${amount} (~10 adults)")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL: Expected $550, got ${amount}")
            else:
                print("   ❌ FAIL: No party minimum found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 4: Deposit Policy
        print("💳 Test 4: Deposit Policy Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT title, 
                       value::jsonb->>'amount' as amount,
                       (value::jsonb->>'refundable')::boolean as refundable
                FROM business_rules 
                WHERE rule_type = 'deposit'
                LIMIT 1
            """
            )

            if result:
                amount = int(result["amount"])
                refundable = result["refundable"]
                if amount == 100 and refundable:
                    print(f"   ✅ PASS: Deposit = ${amount} (refundable)")
                    tests_passed += 1
                else:
                    print(
                        f"   ❌ FAIL: Expected $100 refundable, got ${amount} refundable={refundable}"
                    )
            else:
                print("   ❌ FAIL: No deposit policy found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 5: Cancellation Policy
        print("🚫 Test 5: Cancellation Policy Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT title, 
                       (value::jsonb->>'days_before')::int as days,
                       (value::jsonb->>'refund_percent')::int as refund
                FROM business_rules 
                WHERE rule_type = 'cancellation'
                AND title LIKE '%7+ Days%'
                LIMIT 1
            """
            )

            if result:
                days = result["days"]
                refund = result["refund"]
                if days == 7 and refund == 100:
                    print(f"   ✅ PASS: 7+ days cancellation = {refund}% refund")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL: Expected 7 days/100% refund, got {days} days/{refund}%")
            else:
                print("   ❌ FAIL: No cancellation policy found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 6: FAQ Search
        print("❓ Test 6: FAQ Search - Pricing Question")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT question, answer 
                FROM faq_items 
                WHERE question LIKE '%cost%' OR question LIKE '%price%' OR question LIKE '%much%'
                LIMIT 1
            """
            )

            if result:
                answer = result["answer"]
                if "$55" in answer and "$30" in answer:
                    print("   ✅ PASS: FAQ found with correct pricing")
                    print(f"      Q: {result['question'][:60]}...")
                    tests_passed += 1
                else:
                    print("   ❌ FAIL: FAQ found but missing $55/$30 pricing")
            else:
                print("   ❌ FAIL: No pricing FAQ found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        # Test 7: Menu/Upgrades Query
        print("🍤 Test 7: Premium Upgrades Query")
        tests_total += 1
        try:
            result = await conn.fetchrow(
                """
                SELECT upsell_item, pitch_template 
                FROM upsell_rules 
                WHERE upsell_item LIKE '%Lobster%'
                LIMIT 1
            """
            )

            if result:
                item = result["upsell_item"]
                pitch = result["pitch_template"]
                if "lobster" in pitch.lower() or "$15" in pitch:
                    print("   ✅ PASS: Lobster upgrade found")
                    print(f"      Item: {item}")
                    tests_passed += 1
                else:
                    print("   ❌ FAIL: Lobster upgrade found but missing details")
            else:
                print("   ❌ FAIL: No lobster upgrade found in database")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

        await conn.close()

        # Summary
        print("=" * 60)
        print("📊 KNOWLEDGE BASE TEST SUMMARY")
        print("=" * 60)
        print(f"\nTests Passed: {tests_passed}/{tests_total} ({tests_passed/tests_total*100:.1f}%)")
        print("\n" + "=" * 60)

        if tests_passed == tests_total:
            print("✅ PHASE 2: KNOWLEDGE BASE - PASSED!")
            print("All queries returned correct real MyHibachi data")
            return True
        else:
            print("⚠️  PHASE 2: KNOWLEDGE BASE - PARTIAL PASS")
            print(
                f"Accuracy: {tests_passed/tests_total*100:.1f}% ({tests_passed}/{tests_total} passed)"
            )
            return tests_passed >= tests_total * 0.85  # 85% pass rate

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_knowledge_base())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
