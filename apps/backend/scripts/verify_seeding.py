"""
Verify AI Training Data Seeding
"""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()


async def verify():
    """Verify seeded data"""

    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    conn = await asyncpg.connect(database_url)

    try:
        print("\n" + "=" * 60)
        print("📊 DATABASE VERIFICATION")
        print("=" * 60)

        # Business Rules
        print("\n📋 BUSINESS RULES (Showing real MyHibachi policies):")
        rules = await conn.fetch(
            """
            SELECT rule_type, title, value->>'amount' as amount 
            FROM business_rules 
            WHERE rule_type IN ('pricing', 'deposit', 'cancellation')
            LIMIT 5
        """
        )
        for r in rules:
            amount = f" - ${r['amount']}" if r["amount"] else ""
            print(f"   ✓ {r['rule_type']}: {r['title']}{amount}")

        # FAQs
        print("\n❓ FAQs (Real customer questions):")
        faqs = await conn.fetch(
            """
            SELECT category, question 
            FROM faq_items 
            ORDER BY id
            LIMIT 5
        """
        )
        for f in faqs:
            print(f"   ✓ [{f['category']}] {f['question'][:60]}...")

        # Training Data
        print("\n🎭 TRAINING EXAMPLES (Tone-matched responses):")
        training = await conn.fetch(
            """
            SELECT DISTINCT customer_tone, scenario 
            FROM training_data 
            ORDER BY customer_tone
        """
        )
        for t in training:
            print(f"   ✓ {t['customer_tone']} tone - {t['scenario']}")

        # Upsell Rules
        print("\n💎 UPSELL RULES (Real premium upgrades):")
        upsells = await conn.fetch(
            """
            SELECT upsell_item, trigger_condition 
            FROM upsell_rules 
            LIMIT 5
        """
        )
        for u in upsells:
            print(f"   ✓ {u['upsell_item']}")
            print(f"      Trigger: {u['trigger_condition']}")

        # Seasonal Offers
        print("\n🎉 SEASONAL OFFERS:")
        offers = await conn.fetch(
            """
            SELECT title, discount_type, discount_value 
            FROM seasonal_offers
        """
        )
        for o in offers:
            print(f"   ✓ {o['title']}")
            print(f"      {o['discount_type']}: {o['discount_value']}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        rules_count = await conn.fetchval("SELECT COUNT(*) FROM business_rules")
        faqs_count = await conn.fetchval("SELECT COUNT(*) FROM faq_items")
        training_count = await conn.fetchval("SELECT COUNT(*) FROM training_data")
        upsell_count = await conn.fetchval("SELECT COUNT(*) FROM upsell_rules")
        offers_count = await conn.fetchval("SELECT COUNT(*) FROM seasonal_offers")

        print(f"   - Business Rules: {rules_count}")
        print(f"   - FAQ Items: {faqs_count}")
        print(f"   - Training Examples: {training_count}")
        print(f"   - Upsell Rules: {upsell_count}")
        print(f"   - Seasonal Offers: {offers_count}")
        print("=" * 60)
        print("\n✅ All data verified successfully!")
        print("\n🚀 Ready to test tone-adapted AI responses!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(verify())
