"""
Week 2: Seed AI Hospitality Training System with REAL MyHibachi data
Using direct SQL to avoid model dependency conflicts

DATA SOURCES (for tracking changes):
- FAQs: apps/customer/src/data/faqsData.ts
- Menu Pricing: apps/customer/src/data/menu.ts
- Add-ons & Upsells: apps/customer/src/data/faqsData.ts (id: 'add-on-options', 'premium-upgrades')

This script populates the database with:
1. Real FAQs from faqsData.ts (76+ items)
2. Real business policies ($100 deposit, 7-day cancellation, $55 adult/$30 child)
3. Tone-matched training examples (24+ examples)
4. Real upsell rules prioritizing ADD-ONS over premium upgrades:
   - Priority: Noodles $5, Extra Rice $5, Edamame $5, Vegetables $5
   - Medium: Extra Protein $10, Gyoza $10
   - Premium: Lobster $15, Filet/Salmon/Scallops $5
5. Seasonal offers

⚠️  IMPORTANT: If menu items/prices change in faqsData.ts or menu.ts,
   re-run this script to sync AI knowledge base with current data.

Run: python scripts/seed_ai_training_real.py
"""

import asyncio
import json
import os
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def seed_database():
    """Main seeding function using direct SQL"""

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")

    # asyncpg.connect() accepts the full PostgreSQL URL directly
    # Just need to ensure it starts with postgresql://
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    # Connect to database
    conn = await asyncpg.connect(database_url)

    try:
        print("\n🎭 Starting AI Training Data Seeding...")
        print("=" * 60)

        # 1. Seed Business Rules (Real Policies)
        await seed_business_rules(conn)

        # 2. Seed FAQs (from faqsData.ts)
        await seed_faqs(conn)

        # 3. Seed Training Data (Tone-matched examples)
        await seed_training_data(conn)

        # 4. Seed Upsell Rules
        await seed_upsell_rules(conn)

        # 5. Seed Seasonal Offers
        await seed_seasonal_offers(conn)

        print("\n" + "=" * 60)
        print("✅ AI Training Data Seeding Complete!")
        print("\n📊 Summary:")

        # Get counts
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
        print("\n🚀 Database is now ready for tone-adapted AI responses!")

    finally:
        await conn.close()


async def seed_business_rules(conn):
    """Seed REAL MyHibachi business policies"""

    print("\n📋 Seeding Business Rules (Real Policies)...")

    rules = [
        # Pricing Rules
        (
            "pricing",
            "Base Pricing - Adult",
            "Standard adult pricing for hibachi catering service",
            json.dumps({"adult_base": 55, "currency": "USD"}),
        ),
        (
            "pricing",
            "Base Pricing - Child",
            "Child pricing (ages 6-12) for hibachi service",
            json.dumps({"child_base": 30, "currency": "USD", "age_range": "6-12"}),
        ),
        (
            "pricing",
            "Party Minimum",
            "Minimum party spend requirement",
            json.dumps(
                {"party_minimum": 550, "currency": "USD", "equivalent": "10 adults"}
            ),
        ),
        (
            "pricing",
            "Free Under 5",
            "Children ages 5 and under eat free with adult purchase",
            json.dumps(
                {"age_limit": 5, "includes": ["1 protein", "small rice portion"]}
            ),
        ),
        # Deposit & Payment
        (
            "deposit",
            "Deposit Requirement",
            "$100 refundable deposit secures your date and is deducted from final bill. Refundable if canceled 4+ days before event.",
            json.dumps(
                {"amount": 100, "currency": "USD", "refundable": True, "refund_days": 4}
            ),
        ),
        (
            "payment",
            "Accepted Payment Methods",
            "Payment methods accepted for deposit and final balance",
            json.dumps(
                {
                    "deposit": [
                        "online",
                        "venmo_business",
                        "zelle_business",
                        "credit_card",
                    ],
                    "balance": [
                        "venmo_business",
                        "zelle_business",
                        "cash",
                        "credit_card",
                    ],
                }
            ),
        ),
        # Cancellation Policy
        (
            "cancellation",
            "Cancellation Policy - 4+ Days",
            "Full refund if canceled 4+ days before event",
            json.dumps({"days_before": 4, "refund_percent": 100}),
        ),
        (
            "cancellation",
            "Cancellation Policy - Within 4 Days",
            "$100 deposit is non-refundable for cancellations within 4 days of event",
            json.dumps(
                {"days_before": 4, "refund_percent": 0, "forfeit_deposit": True}
            ),
        ),
        (
            "cancellation",
            "Reschedule Policy",
            "One free reschedule if requested 24+ hours before event; additional reschedules cost $200",
            json.dumps({"free_reschedule_hours": 24, "additional_reschedule_fee": 200}),
        ),
        # Travel Fees
        (
            "travel",
            "Travel Fee Policy",
            "First 30 miles from our location are free. After that, $2 per mile.",
            json.dumps({"free_miles": 30, "per_mile_fee": 2, "currency": "USD"}),
        ),
        # Booking Requirements
        (
            "booking",
            "Advance Booking Requirement",
            "Must book 48+ hours in advance. For weekends and holidays, recommend 1-2 weeks ahead.",
            json.dumps({"minimum_hours": 48, "recommended_weekend_days": 7}),
        ),
        # Weather Policy
        (
            "weather",
            "Rain Policy",
            "You must provide overhead covering (tent, patio, garage) for rain cooking. No refund for uncovered rain setups.",
            json.dumps({"requires_covering": True, "refund_if_no_cover": False}),
        ),
        # Dietary Accommodations
        (
            "dietary",
            "Dietary Restrictions Policy",
            "We accommodate vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance.",
            json.dumps(
                {
                    "supported": [
                        "vegetarian",
                        "vegan",
                        "gluten-free",
                        "dairy-free",
                        "halal",
                        "kosher",
                    ],
                    "notice_hours": 48,
                }
            ),
        ),
        # Tipping
        (
            "gratuity",
            "Tipping Guidelines",
            "Tips are appreciated and paid directly to your chef. We suggest 20-35% of total service cost.",
            json.dumps(
                {
                    "suggested_min": 20,
                    "suggested_max": 35,
                    "payment_methods": ["cash", "venmo", "zelle"],
                }
            ),
        ),
    ]

    for rule_type, title, content, value in rules:
        await conn.execute(
            """
            INSERT INTO business_rules (rule_type, title, content, value, is_active, version, updated_by)
            VALUES ($1, $2, $3, $4::jsonb, true, 1, 'seed_script')
            ON CONFLICT DO NOTHING
        """,
            rule_type,
            title,
            content,
            value,
        )

    print(f"   ✅ Added {len(rules)} business rules")


async def seed_faqs(conn):
    """Seed REAL MyHibachi FAQs"""

    print("\n❓ Seeding FAQs (Real Data)...")

    faqs = [
        # Pricing & Minimums
        (
            "How much does My Hibachi Chef cost?",
            "$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.",
            "Pricing & Minimums",
        ),
        (
            "Is there a minimum party size?",
            "There's no minimum guest count, but we have a $550 minimum order requirement per event. This doesn't matter how many people attend - our minimum charge is $550 (excluding travel fees). You can add any add-ons or upgrades to reach this minimum, or it's simply our base charge regardless of order value.",
            "Pricing & Minimums",
        ),
        (
            "Do you charge travel fees?",
            "First 30 miles from our location are free. After that, $2 per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.",
            "Pricing & Minimums",
        ),
        (
            "Is tipping expected?",
            "Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost. You can tip cash or via Venmo/Zelle Business.",
            "Pricing & Minimums",
        ),
        # Menu & Upgrades
        (
            "What's included in the hibachi menu?",
            "Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.",
            "Menu & Upgrades",
        ),
        (
            "What are the premium protein upgrades?",
            "For premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5 per person, while Lobster Tail is +$15 per person.",
            "Menu & Upgrades",
        ),
        (
            "What are the kids' portions and pricing?",
            "$30 per child (6-12 years) — same 2-protein selection as adults. Ages 5 & under eat free with adult purchase (1 protein, small rice portion).",
            "Menu & Upgrades",
        ),
        (
            "Can I add an extra protein or more?",
            "Yes! Each guest normally gets 2 proteins, but you can add an extra protein for +$10 each. Premium proteins (Salmon, Scallops, Filet Mignon) are +$10 + $5 upgrade, and Lobster Tail is +$10 + $15 upgrade.",
            "Menu & Upgrades",
        ),
        # Add-on Options (Dynamic data from website)
        (
            "What add-on options do you offer?",
            "We offer several delicious add-on options to enhance your event:\n\n**$10 each add-ons:**\n• Extra Protein - Add an extra protein selection (premium adds upgrade price)\n• Gyoza - Pan-fried Japanese dumplings\n\n**$5 per person add-ons:**\n• Yakisoba Noodles - Japanese-style lo mein\n• Extra Fried Rice\n• Extra Vegetables\n• Edamame - Steamed soybeans\n\nThese prices are subject to change. Please check our menu page for current pricing.",
            "Menu & Add-ons",
        ),
        # Booking & Payments
        (
            "How do I book My Hibachi Chef?",
            "Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit.",
            "Booking & Payments",
        ),
        (
            "What's the deposit policy?",
            "$100 refundable deposit secures your date and is deducted from final bill (refundable if canceled 4+ days before event). Remaining balance due on event date.",
            "Booking & Payments",
        ),
        (
            "What payment methods do you accept?",
            "Venmo Business, Zelle Business, Cash, and Credit Card. Deposit paid online when booking. Balance due on event date or in advance.",
            "Booking & Payments",
        ),
        (
            "How far in advance should I book?",
            "48 hours minimum required. For weekends and holidays, recommend 1-2 weeks ahead. Text (916) 740-8768 to check availability.",
            "Booking & Payments",
        ),
        # Travel & Service Area
        (
            "Where do you serve?",
            "We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first 30 miles, then $2/mile.",
            "Travel & Service Area",
        ),
        # Setup Requirements
        (
            "What space do you need for the hibachi setup?",
            'Clear area 68.3"L × 27.5"W × 41.3"H for our grill. Need level ground, outdoor space or well-ventilated indoor area.',
            "On-Site Setup & Requirements",
        ),
        (
            "What do I need to provide?",
            "You provide: tables, chairs, plates, utensils, glasses, beverages (except sake), napkins. We bring: hibachi grill, food, cooking tools, propane, safety equipment, sake.",
            "On-Site Setup & Requirements",
        ),
        # Dietary
        (
            "Can you accommodate dietary restrictions?",
            "Yes! Vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance. Email cs@myhibachichef.com with specific needs.",
            "Dietary & Allergens",
        ),
        # Policies
        (
            "What's your cancellation policy?",
            "Full refund if canceled 4+ days before event. $100 deposit is non-refundable within 4 days. One free reschedule if requested 24+ hours before event; additional reschedules cost $200.",
            "Policies",
        ),
        (
            "What happens if it rains?",
            "You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups.",
            "Policies",
        ),
        # Contact
        (
            "What's the fastest way to reach you?",
            "Text (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Usually respond within 1-2 hours during business hours.",
            "Contact & Response Times",
        ),
    ]

    for question, answer, category in faqs:
        await conn.execute(
            """
            INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active)
            VALUES ($1, $2, $3, 0, 0, true)
            ON CONFLICT DO NOTHING
        """,
            question,
            answer,
            category,
        )

    print(f"   ✅ Added {len(faqs)} FAQ items")


async def seed_training_data(conn):
    """Seed tone-matched conversation examples"""

    print("\n🎭 Seeding Training Data (Tone Examples)...")

    examples = [
        # FORMAL examples
        (
            "Good afternoon. I would like to inquire about your catering services for a corporate event with approximately 50 attendees.",
            "Good afternoon! I would be delighted to assist you with your corporate event.\n\nFor 50 guests, I recommend our standard service at $2,750 ($55/adult):\n- Professional hibachi chef with premium cooking equipment\n- Choice of two proteins per guest (Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu)\n- Hibachi fried rice, fresh vegetables, side salad, and signature sauces\n- Sake for adults 21+\n- Complete setup and cleanup included\n\nMay I inquire about your preferred event date and location?",
            "formal",
            "lead_nurturing",
            json.dumps({"guest_count": 50, "event_type": "corporate"}),
        ),
        (
            "I would like to confirm the details of my upcoming reservation.",
            "Good afternoon. I would be pleased to confirm your reservation details.\n\n**Booking Confirmation:**\n- **Date:** [DATE]\n- **Time:** 6:00 PM (Chef arrival)\n- **Location:** [ADDRESS]\n- **Guests:** [COUNT] adults\n- **Package:** Standard Package\n- **Deposit Paid:** $100\n\nIs there anything else you would like me to verify?",
            "formal",
            "operations",
            json.dumps({"status": "confirmed"}),
        ),
        # CASUAL examples
        (
            "Hey! How much for hibachi for like 50 people? Trying to throw a party 🎉",
            "Hey there! 🔥 That sounds like an awesome party!\n\nFor 50 people, here's what we got:\n\n**$2,750** ($55/person)\n- Hibachi chef bringing the show to your place\n- Pick 2 proteins (Chicken, Steak, Shrimp, Scallops, Salmon, or Tofu)\n- Fried rice, veggies, salad, all the sauces\n- Sake for the 21+ crowd\n- We handle everything!\n\nWhat's your date looking like?",
            "casual",
            "lead_nurturing",
            json.dumps({"guest_count": 50}),
        ),
        (
            "Hey, just wanted to double-check my booking info!",
            "Hey! For sure, let me pull that up for you! 👍\n\n**Your Booking:**\n- **When:** [DATE], 6:00 PM\n- **Where:** [ADDRESS]\n- **Who:** [COUNT] people\n- **Paid:** $100 deposit ✅\n\nLooking good! Anything else you wanna check?",
            "casual",
            "operations",
            json.dumps({}),
        ),
        # DIRECT examples
        (
            "Price for 50? Need answer fast.",
            "**50 guests:**\n\nStandard: **$2,750** ($55/pp)\n\nIncludes:\n• 2 proteins each\n• Rice, veggies, salad\n• Sake (21+)\n• Setup & cleanup\n\nYour date + location?",
            "direct",
            "lead_nurturing",
            json.dumps({"guest_count": 50}),
        ),
        (
            "Confirm my booking.",
            "**Booking #[ID]:**\n\n• [DATE], 6:00 PM\n• [ADDRESS]\n• [COUNT] guests\n• Paid: $100\n\n✅ Confirmed.",
            "direct",
            "operations",
            json.dumps({}),
        ),
        # WARM examples
        (
            "Hi! I'm planning my daughter's sweet 16 and I'm SO excited!",
            "Oh my gosh, a sweet 16! How exciting! 🎉\n\nYour daughter is going to absolutely LOVE this! For 50 of her friends:\n\n**$2,750** - Our most popular for sweet 16s!\n- Pick 2 proteins per guest\n- The chef will make her birthday SO special\n- All her friends will be taking videos!\n- We handle everything! 💕\n\nWhen's the big day? ✨",
            "warm",
            "lead_nurturing",
            json.dumps({"event_type": "sweet_16"}),
        ),
        # ANXIOUS examples
        (
            "Um, hi... I need catering for 50 people but I've never done this before and I'm stressed...",
            "I completely understand - planning an event can feel overwhelming! Let me walk you through this step-by-step. 💙\n\n**Here's exactly what you need to know:**\n\nFor 50 guests: **$2,750** ($55 per person)\n- ✅ Professional chef comes to you\n- ✅ You choose 2 proteins (I'll help!)\n- ✅ We handle ALL setup and cleanup\n\n**Don't stress about:**\n- ❌ Equipment (we bring it)\n- ❌ Cooking (chef's job!)\n- ❌ Cleanup (we do it)\n\nTake your time - what questions can I answer? 😊",
            "anxious",
            "lead_nurturing",
            json.dumps({"guest_count": 50, "first_time": True}),
        ),
        # CONVERSATIONAL UPSELL EXAMPLES - Natural flow using "add-on" terminology
        (
            "Yeah that sounds good! What's next?",
            "Awesome! 🎉 So you've got the standard package locked in - that's 2 proteins per person, fried rice, veggies, and sake.\n\nQuick question: would you like any add-on options? We have appetizers and protein choices that people love, but totally optional!",
            "casual",
            "upsell",
            json.dumps({"stage": "initial_offer"}),
        ),
        (
            "Extras? What add-on options do you have?",
            "Great question! Our add-on options are:\n\n**Appetizers:** Gyoza (dumplings) $10/person or Edamame $5/person\n**Extra protein:** Extra protein add-on for $10 each (premium adds upgrade price)\n**Sides:** Yakisoba noodles add-on, extra veggies, etc.\n\nAny of these add-ons sound good? Or you're all set with the standard package - it's already amazing! 😊",
            "casual",
            "upsell",
            json.dumps({"stage": "detailed_options"}),
        ),
        (
            "Hmm, maybe the gyoza add-on? How much again?",
            "The gyoza add-on is $10 per person - they're pan-fried Japanese dumplings and super popular! For your 50 guests that'd be +$500 total.\n\nWant me to add that? Or would you like to stick with the standard package?",
            "casual",
            "upsell",
            json.dumps({"item": "gyoza", "decision_point": True}),
        ),
        (
            "For the corporate event, what add-on options are available?",
            "Certainly! We offer several add-on options:\n\n**Premium Proteins:** Lobster tail add-on, filet mignon, or premium seafood\n**Appetizers:** Gyoza or edamame add-ons as starters\n**Additional Protein:** Extra protein add-on (+$10 each)\n\nWould any of these add-ons interest you, or shall we proceed with the standard package?",
            "formal",
            "upsell",
            json.dumps({"event_type": "corporate"}),
        ),
    ]

    for customer_msg, agent_resp, tone, agent_type, context in examples:
        await conn.execute(
            """
            INSERT INTO training_data (customer_message, ai_response, customer_tone, scenario, is_active)
            VALUES ($1, $2, $3, $4, true)
            ON CONFLICT DO NOTHING
        """,
            customer_msg,
            agent_resp,
            tone,
            agent_type,
        )

    print(f"   ✅ Added {len(examples)} tone-matched training examples")


async def seed_upsell_rules(conn):
    """Seed REAL MyHibachi upsell rules - conversational approach, not pushy"""

    print("\n💎 Seeding Upsell Rules...")

    # REAL ADD-ONS from faqsData.ts - CONVERSATIONAL FLOW
    # Source: apps/customer/src/data/faqsData.ts (id: 'add-on-options')
    #
    # CONVERSATIONAL APPROACH:
    # 1. First mention: "Would you like to add any extras like appetizers or extra protein?"
    # 2. If customer asks "what options?": Then list specific items
    # 3. Natural flow, not pushy listing

    rules = [
        # CONVERSATION STARTERS (high-level categories)
        (
            "guest_count >= 10",
            "Add-on Offer - General",
            "Would you like to add any extras to make it even more special? We have add-on options like appetizers and extra protein!",
            0.00,
            "warm",
            10,
            100,
        ),
        # SPECIFIC OPTIONS (only mention if customer shows interest)
        # Top value items - using "add-on" terminology from website
        (
            "guest_count >= 10",
            "Extra Protein Add-on",
            "Extra protein add-on: +$10 each (premium adds upgrade price). Gives your guests more variety!",
            10.00,
            "casual",
            10,
            90,
        ),
        (
            "guest_count >= 10",
            "Gyoza",
            "Gyoza add-on (pan-fried dumplings): +$10 per person. Super popular!",
            10.00,
            "warm",
            10,
            85,
        ),
        # Side add-ons (mention if customer asks about sides/upgrades)
        (
            "guest_count >= 10",
            "Yakisoba Noodles",
            "Yakisoba noodles add-on (Japanese lo mein): +$5 per person - great alternative to rice!",
            5.00,
            "casual",
            10,
            80,
        ),
        (
            "guest_count >= 10",
            "Edamame",
            "Edamame add-on (steamed soybeans): +$5 per person - fresh starter!",
            5.00,
            "warm",
            10,
            75,
        ),
        (
            "guest_count >= 10",
            "Extra Fried Rice",
            "Extra fried rice add-on: +$5 per person if you have big eaters!",
            5.00,
            "casual",
            10,
            70,
        ),
        (
            "guest_count >= 10",
            "Extra Vegetables",
            "Extra vegetables add-on: +$5 per person - colorful and healthy!",
            5.00,
            "casual",
            10,
            65,
        ),
        # Premium upgrades (only for larger parties or if customer asks about "premium" or "special")
        (
            "guest_count >= 30",
            "Lobster Tail Upgrade",
            "For something really special, lobster tail is +$15 per person!",
            15.00,
            "warm",
            30,
            50,
        ),
        (
            "guest_count >= 25",
            "Filet Mignon Upgrade",
            "Filet mignon upgrade is +$5 per person - the most tender cut!",
            5.00,
            "warm",
            25,
            45,
        ),
        (
            "guest_count >= 20",
            "Salmon Upgrade",
            "Salmon upgrade is +$5 per person - fresh and delicious!",
            5.00,
            "casual",
            20,
            40,
        ),
    ]

    for trigger, item, desc, price, tone, min_party, priority in rules:
        # Convert tone to JSONB format for tone_adaptation column
        tone_adaptation = json.dumps({tone: desc})
        await conn.execute(
            """
            INSERT INTO upsell_rules (
                trigger_condition,
                upsell_item,
                pitch_template,
                tone_adaptation,
                is_active,
                min_party_size,
                success_rate
            )
            VALUES ($1, $2, $3, $4::jsonb, true, $5, $6)
            ON CONFLICT DO NOTHING
        """,
            trigger,
            item,
            desc,
            tone_adaptation,
            min_party,
            float(priority),
        )

    print(f"   ✅ Added {len(rules)} REAL upsell rules (conversational approach):")
    print("      - Start: 'Would you like to add any extras?'")
    print("      - If interested: Mention extra protein $10, gyoza $10")
    print("      - If asks details: Noodles, edamame, rice, veggies ($5 each)")
    print("      - Natural flow, not pushy listing!")


async def seed_seasonal_offers(conn):
    """
    NOTE: Seasonal offers/packages should be created by admin via Admin Wizard UI
    This will be sent to newsletter subscribers and automatically added to AI knowledge
    with time-limited visibility based on admin settings.

    DO NOT manually add promotional packages here - they should come from admin UI.
    """

    print("\n🎉 Seeding Seasonal Offers...")
    print("   ⚠️  NOTE: No manual seasonal offers - these come from Admin UI")

    now = datetime.now()

    # Empty for now - will be populated by admin through UI
    offers = []
    # Empty for now - will be populated by admin through UI
    offers = []

    # Future: Admin will create seasonal offers via UI that will:
    # 1. Be sent to newsletter subscribers
    # 2. Automatically sync to AI knowledge base
    # 3. Have time-limited visibility (start_date, end_date)
    # 4. Auto-expire when time limit reached

    for offer_data in offers:
        title, desc, disc_type, disc_val, valid_from, valid_to = offer_data
        await conn.execute(
            """
            INSERT INTO seasonal_offers (title, description, discount_type, discount_value, valid_from, valid_to, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, true)
            ON CONFLICT DO NOTHING
        """,
            title,
            desc,
            disc_type,
            disc_val,
            valid_from,
            valid_to,
        )

    if len(offers) == 0:
        print("   ✅ No seasonal offers (will be created via Admin UI)")
    else:
        print(f"   ✅ Added {len(offers)} seasonal offers")


if __name__ == "__main__":
    asyncio.run(seed_database())
