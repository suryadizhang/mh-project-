"""
Week 2: Seed AI Hospitality Training System with REAL MyHibachi data

This script populates the database with:
1. Real FAQs from faqsData.ts (50+ items)
2. Real business policies ($100 deposit, 7-day cancellation, etc.)
3. Tone-matched training examples
4. Real upsell rules (Lobster +$15, Filet +$5, etc.)
5. Seasonal offers

Run: python scripts/seed_ai_training_data.py
"""

import asyncio
import os

# Import knowledge base models
import sys
from datetime import datetime

import asyncpg
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models.knowledge_base import (
    BusinessRule,
    FAQItem,
    KnowledgeCache,
    SeasonalOffer,
    TrainingData,
    UpsellRule,
)

load_dotenv()


async def seed_database():
    """Main seeding function using direct SQL"""

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")

    # Convert to asyncpg format
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "", 1)
    elif database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "", 1)

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

        # 6. Pre-cache common knowledge
        await seed_knowledge_cache(conn)

        print("\n" + "=" * 60)
        print("✅ AI Training Data Seeding Complete!")
        print("\nDatabase is now ready for tone-adapted AI responses! 🚀")

    finally:
        await conn.close()


async def seed_business_rules(session: AsyncSession):
    """Seed REAL MyHibachi business policies"""

    print("\n📋 Seeding Business Rules (Real Policies)...")

    rules = [
        # Pricing Rules
        BusinessRule(
            rule_type="pricing",
            title="Base Pricing - Adult",
            content="Standard adult pricing for hibachi catering service",
            value={"adult_base": 55, "currency": "USD"},
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="pricing",
            title="Base Pricing - Child",
            content="Child pricing (ages 6-12) for hibachi service",
            value={"child_base": 30, "currency": "USD", "age_range": "6-12"},
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="pricing",
            title="Party Minimum",
            content="Minimum party spend requirement",
            value={"party_minimum": 550, "currency": "USD", "equivalent": "10 adults"},
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="pricing",
            title="Free Under 5",
            content="Children ages 5 and under eat free with adult purchase",
            value={"age_limit": 5, "includes": ["1 protein", "small rice portion"]},
            is_active=True,
            updated_by="seed_script",
        ),
        # Deposit & Payment
        BusinessRule(
            rule_type="deposit",
            title="Deposit Requirement",
            content="$100 refundable deposit secures your date and is deducted from final bill. Refundable if canceled 4+ days before event.",
            value={
                "amount": 100,
                "currency": "USD",
                "refundable": True,
                "refund_days": 4,
            },
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="payment",
            title="Accepted Payment Methods",
            content="Payment methods accepted for deposit and final balance",
            value={
                "deposit": [
                    "online",
                    "venmo_business",
                    "zelle_business",
                    "credit_card",
                ],
                "balance": ["venmo_business", "zelle_business", "cash", "credit_card"],
            },
            is_active=True,
            updated_by="seed_script",
        ),
        # Cancellation Policy
        BusinessRule(
            rule_type="cancellation",
            title="Cancellation Policy - 4+ Days",
            content="Full refund if canceled 4+ days before event",
            value={"days_before": 4, "refund_percent": 100},
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="cancellation",
            title="Cancellation Policy - Within 4 Days",
            content="$100 deposit is non-refundable for cancellations within 4 days of event",
            value={"days_before": 4, "refund_percent": 0, "forfeit_deposit": True},
            is_active=True,
            updated_by="seed_script",
        ),
        BusinessRule(
            rule_type="cancellation",
            title="Reschedule Policy",
            content="One free reschedule within 48 hours of booking; additional reschedules cost $100",
            value={"free_reschedule_hours": 48, "additional_reschedule_fee": 100},
            is_active=True,
            updated_by="seed_script",
        ),
        # Travel Fees
        BusinessRule(
            rule_type="travel",
            title="Travel Fee Policy",
            content="First 30 miles from our location are free. After that, $2 per mile with flexible options for your area.",
            value={"free_miles": 30, "per_mile_fee": 2, "currency": "USD"},
            is_active=True,
            updated_by="seed_script",
        ),
        # Booking Requirements
        BusinessRule(
            rule_type="booking",
            title="Advance Booking Requirement",
            content="Must book 48+ hours in advance. For weekends and holidays, recommend 1-2 weeks ahead.",
            value={"minimum_hours": 48, "recommended_weekend_days": 7},
            is_active=True,
            updated_by="seed_script",
        ),
        # Weather Policy
        BusinessRule(
            rule_type="weather",
            title="Rain Policy",
            content="You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups.",
            value={"requires_covering": True, "refund_if_no_cover": False},
            is_active=True,
            updated_by="seed_script",
        ),
        # Dietary Accommodations
        BusinessRule(
            rule_type="dietary",
            title="Dietary Restrictions Policy",
            content="We accommodate vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance.",
            value={
                "supported": [
                    "vegetarian",
                    "vegan",
                    "gluten-free",
                    "dairy-free",
                    "halal",
                    "kosher",
                ],
                "notice_hours": 48,
            },
            is_active=True,
            updated_by="seed_script",
        ),
        # Tipping
        BusinessRule(
            rule_type="gratuity",
            title="Tipping Guidelines",
            content="Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost.",
            value={
                "suggested_min": 20,
                "suggested_max": 35,
                "payment_methods": ["cash", "venmo", "zelle"],
            },
            is_active=True,
            updated_by="seed_script",
        ),
    ]

    for rule in rules:
        session.add(rule)

    print(
        f"   ✅ Added {len(rules)} business rules (pricing, deposit, cancellation, travel, etc.)"
    )


async def seed_faqs(session: AsyncSession):
    """Seed REAL MyHibachi FAQs from faqsData.ts"""

    print("\n❓ Seeding FAQs (Real Data from faqsData.ts)...")

    faqs = [
        # Pricing & Minimums
        FAQItem(
            question="How much does My Hibachi Chef cost?",
            answer="$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.",
            category="Pricing & Minimums",
            subcategory="Per-person Rates",
            tags=["pricing", "$55 adult", "$30 child", "$550 minimum"],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="Is there a minimum party size?",
            answer="Yes — $550 total minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.",
            category="Pricing & Minimums",
            subcategory="Minimum Spend / Party Size",
            tags=["minimum", "$550", "party size", "upgrades"],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="Is tipping expected?",
            answer="Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost. You can tip cash or via Venmo/Zelle Business.",
            category="Pricing & Minimums",
            subcategory="Gratuity & Fees",
            tags=["tipping", "20-35%", "cash", "venmo", "zelle"],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="Do you charge travel fees?",
            answer="First 30 miles from our location are free. After that, $2 per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.",
            category="Pricing & Minimums",
            subcategory="Travel Fees",
            tags=["travel", "free 30 miles", "$2 per mile", "flexible service"],
            source_urls=["/menu", "/contact"],
            is_active=True,
        ),
        # Menu & Upgrades
        FAQItem(
            question="What's included in the hibachi menu?",
            answer="Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.",
            category="Menu & Upgrades",
            subcategory="Included Items",
            tags=[
                "2 proteins",
                "chicken",
                "steak",
                "shrimp",
                "rice",
                "vegetables",
                "sake",
            ],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="What are the premium protein upgrades?",
            answer="For premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5 per person, while Lobster Tail is +$15 per person. These upgrade your existing protein choices to premium options.",
            category="Menu & Upgrades",
            subcategory="Premium Upgrades",
            tags=[
                "upgrades",
                "salmon +$5",
                "scallops +$5",
                "filet +$5",
                "lobster +$15",
                "premium proteins",
            ],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="What are the kids' portions and pricing?",
            answer="$30 per child (6-12 years) — same 2-protein selection as adults. Ages 5 & under eat free with adult purchase (1 protein, small rice portion).",
            category="Menu & Upgrades",
            subcategory="Kids' Portions",
            tags=["kids", "$30", "6-12 years", "free under 5", "2 proteins"],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="Do you serve sake and alcohol?",
            answer="Yes! We provide sake for guests 21+ as part of the standard experience. We don't provide other alcohol — you're welcome to supply your own beer, wine, or cocktails.",
            category="Menu & Upgrades",
            subcategory="Add-ons & Sides",
            tags=["sake", "alcohol", "21+", "byob", "beer", "wine"],
            source_urls=["/menu"],
            is_active=True,
        ),
        FAQItem(
            question="Can I add an extra protein or more?",
            answer="Yes! Each guest normally gets 2 proteins, but you can add an extra protein for +$10 each. This is an additional option that gives you more food, not an upgrade. If you want the extra protein to be a premium option (Salmon, Scallops, Filet Mignon: +$10 + $5 = $15, or Lobster Tail: +$10 + $15 = $25).",
            category="Menu & Upgrades",
            subcategory="Add-ons & Sides",
            tags=["extra protein", "additional protein", "add-on", "+$10", "more food"],
            source_urls=["/menu"],
            is_active=True,
        ),
        # Booking & Payments
        FAQItem(
            question="How do I book My Hibachi Chef?",
            answer="Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit (refundable if canceled 4+ days before event).",
            category="Booking & Payments",
            subcategory="How to Book",
            tags=[
                "booking",
                "online",
                "text",
                "48 hours",
                "$100 deposit",
                "refundable",
            ],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="What's the deposit policy?",
            answer="$100 refundable deposit secures your date and is deducted from final bill (refundable if canceled 4+ days before event). Remaining balance due on event date. Accept Venmo Business, Zelle Business, Cash, Credit Card.",
            category="Booking & Payments",
            subcategory="Deposits & Balance",
            tags=["$100 deposit", "refundable", "deducted", "final bill"],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="What payment methods do you accept?",
            answer="Venmo Business, Zelle Business, Cash, and Credit Card. Deposit paid online when booking. Balance due on event date or in advance.",
            category="Booking & Payments",
            subcategory="Payment Methods",
            tags=["venmo", "zelle", "cash", "credit card", "online deposit"],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="How far in advance should I book?",
            answer="48 hours minimum required. For weekends and holidays, recommend 1-2 weeks ahead. Text (916) 740-8768 to check availability.",
            category="Booking & Payments",
            subcategory="Scheduling & Availability",
            tags=["48 hours minimum", "weekends", "holidays", "1-2 weeks"],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        # Travel & Service Area
        FAQItem(
            question="Where do you serve?",
            answer="We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first 30 miles, then $2/mile.",
            category="Travel & Service Area",
            subcategory="Coverage Radius",
            tags=["bay area", "sacramento", "san jose", "free 30 miles"],
            source_urls=["/contact", "/menu"],
            is_active=True,
        ),
        FAQItem(
            question="Do you travel to my city?",
            answer="We serve the Bay Area, Sacramento, Central Valley, and coastal/mountain communities throughout Northern California. Text (916) 740-8768 with your zip code for confirmation.",
            category="Travel & Service Area",
            subcategory="Coverage Radius",
            tags=[
                "bay area",
                "sacramento",
                "central valley",
                "zip code",
                "confirmation",
            ],
            source_urls=["/contact"],
            is_active=True,
        ),
        # On-Site Setup & Requirements
        FAQItem(
            question="What space do you need for the hibachi setup?",
            answer='Clear area 68.3"L × 27.5"W × 41.3"H for our grill. Need level ground, outdoor space or well-ventilated indoor area, and table access so guests can watch the show.',
            category="On-Site Setup & Requirements",
            subcategory="Space & Ventilation",
            tags=[
                "68x27x41 inches",
                "level ground",
                "outdoor",
                "ventilated",
                "table access",
            ],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="How should I arrange tables and seating?",
            answer="U-shape with chef's grill at the open end so everyone watches the show. Two 8-foot tables seat ~10 people, three 6-foot tables handle 12-15 guests.",
            category="On-Site Setup & Requirements",
            subcategory="Table Setup",
            tags=[
                "u-shape",
                "8-foot tables",
                "10 people",
                "6-foot tables",
                "12-15 guests",
            ],
            source_urls=[],
            is_active=True,
        ),
        FAQItem(
            question="Can you cook indoors?",
            answer="Outdoor preferred for safety, but indoor possible with high ceilings and excellent ventilation. Must handle smoke and propane safely. Email cs@myhibachichef.com to discuss indoor requirements.",
            category="On-Site Setup & Requirements",
            subcategory="Indoor vs Outdoor",
            tags=[
                "outdoor preferred",
                "indoor possible",
                "high ceilings",
                "ventilation",
                "smoke",
            ],
            source_urls=[],
            is_active=True,
        ),
        FAQItem(
            question="What do I need to provide?",
            answer="You provide: tables, chairs, plates, utensils, glasses, beverages (except sake), napkins. We bring: hibachi grill, food, cooking tools, propane, safety equipment, sake.",
            category="On-Site Setup & Requirements",
            subcategory="Tableware & Setup",
            tags=["tables", "chairs", "plates", "utensils", "glasses", "napkins"],
            source_urls=[],
            is_active=True,
        ),
        # Dietary & Allergens
        FAQItem(
            question="Can you accommodate dietary restrictions?",
            answer="Yes! Vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance so our chef can prepare. Email cs@myhibachichef.com with specific needs.",
            category="Dietary & Allergens",
            subcategory="Dietary Accommodations",
            tags=[
                "vegetarian",
                "vegan",
                "gluten-free",
                "dairy-free",
                "halal",
                "kosher",
                "48 hours",
            ],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        # Policies (Cancellation, Weather, Refunds)
        FAQItem(
            question="What's your cancellation policy?",
            answer="Full refund if canceled 4+ days before event. $100 deposit is refundable for cancellations 4+ days before event, non-refundable within 4 days. One free reschedule if requested 24+ hours before event; additional reschedules cost $200.",
            category="Policies (Cancellation, Weather, Refunds)",
            subcategory="Cancellation & Changes",
            tags=[
                "4 days",
                "full refund",
                "deposit refundable",
                "free reschedule",
                "$200 fee",
            ],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        FAQItem(
            question="What happens if it rains?",
            answer="You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups — plan a backup covered area!",
            category="Policies (Cancellation, Weather, Refunds)",
            subcategory="Weather / Backup Plan",
            tags=["rain", "overhead covering", "tent", "patio", "garage", "no refund"],
            source_urls=["/BookUs"],
            is_active=True,
        ),
        # Kids & Special Occasions
        FAQItem(
            question="Do you do birthday parties and special events?",
            answer="Absolutely! Birthday parties are our specialty. Chefs make the show extra fun and family-friendly, accommodate dietary needs, and make the birthday person feel special. Book 48+ hours ahead!",
            category="Kids & Special Occasions",
            subcategory="Birthdays/Anniversaries",
            tags=[
                "birthday",
                "special events",
                "family-friendly",
                "dietary needs",
                "48 hours",
            ],
            source_urls=[],
            is_active=True,
        ),
        # Contact & Response Times
        FAQItem(
            question="What's the fastest way to reach you?",
            answer="Text (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Follow @my_hibachi_chef on Instagram and Facebook. Usually respond within 1-2 hours during business hours.",
            category="Contact & Response Times",
            subcategory="Best Way to Reach",
            tags=[
                "text",
                "916-740-8768",
                "email",
                "instagram",
                "facebook",
                "1-2 hours",
            ],
            source_urls=["/contact"],
            is_active=True,
        ),
    ]

    for faq in faqs:
        session.add(faq)

    print(f"   ✅ Added {len(faqs)} real FAQ items from your website")


async def seed_training_data(session: AsyncSession):
    """Seed tone-matched conversation examples"""

    print("\n🎭 Seeding Training Data (Tone-Matched Examples)...")

    training_examples = [
        # FORMAL TONE EXAMPLES (10)
        TrainingData(
            customer_message="Good afternoon. I would like to inquire about your catering services for a corporate event with approximately 50 attendees.",
            agent_response="Good afternoon! I would be delighted to assist you with your corporate event.\n\nFor 50 guests, I recommend our standard service at $2,750 ($55/adult):\n- Professional hibachi chef with premium cooking equipment\n- Choice of two proteins per guest (Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu)\n- Hibachi fried rice, fresh vegetables, side salad, and signature sauces\n- Sake for adults 21+\n- Complete setup and cleanup included\n\nMay I inquire about your preferred event date and location to ensure availability?",
            customer_tone="formal",
            agent_type="lead_nurturing",
            booking_context={"guest_count": 50, "event_type": "corporate"},
            tags=["formal", "corporate", "pricing_inquiry", "50_guests"],
        ),
        TrainingData(
            customer_message="I must express my disappointment that our chef arrived 45 minutes late to our corporate event yesterday.",
            agent_response="Good morning, and I sincerely apologize for this unacceptable delay.\n\n**What I'm doing immediately:**\n1. I have escalated your case to our operations manager (Case #[ID])\n2. I am reviewing the incident to understand what caused this delay\n3. I will personally follow up with you within 2 hours with a resolution\n\n**Your Options:**\n- Full refund of the service fee ($550)\n- 50% discount on your next booking\n- Both a partial refund and future discount\n\nThis does not meet our standards, and I take full responsibility for ensuring this does not happen again. May I ask which resolution you would prefer?",
            customer_tone="formal",
            agent_type="customer_care",
            booking_context={"issue": "late_arrival", "delay_minutes": 45},
            tags=["formal", "complaint", "late_chef", "resolution_offered"],
        ),
        TrainingData(
            customer_message="I would like to confirm the details of my upcoming reservation.",
            agent_response="Good afternoon. I would be pleased to confirm your reservation details.\n\n**Booking Confirmation:**\n- **Date:** Saturday, [DATE]\n- **Time:** 6:00 PM (Chef arrival), 6:30 PM (Service start)\n- **Location:** [ADDRESS]\n- **Guests:** [COUNT] adults\n- **Package:** Standard Package ($[AMOUNT])\n- **Proteins Selected:** [SELECTIONS]\n- **Deposit Paid:** $100 (Balance: $[BALANCE] due day of event)\n\n**Additional Information:**\n- Chef will arrive 30 minutes prior for setup\n- Service duration: Approximately 90 minutes\n- Cleanup completed within 15 minutes post-service\n\nIs there anything else you would like me to verify?",
            customer_tone="formal",
            agent_type="operations",
            booking_context={"status": "confirmed"},
            tags=["formal", "confirmation", "booking_details"],
        ),
        TrainingData(
            customer_message="What is your cancellation policy?",
            agent_response="Thank you for your inquiry. Our cancellation policy is as follows:\n\n**Cancellation Policy:**\n\n**More than 4 days before event:**\n- Full refund of all payments\n- No cancellation fee\n\n**Within 4 days before event:**\n- $100 deposit is non-refundable\n- No refund of remaining balance\n\n**Rescheduling:**\n- One free reschedule if requested 24+ hours before event\n- Additional reschedules: $200 fee\n\n**Exceptions:**\n- Weather emergencies\n- Medical emergencies (documentation required)\n\n**To cancel or reschedule:**\nPlease contact us at (916) 740-8768 or cs@myhibachichef.com with your booking reference number.\n\nMay I assist you with anything else regarding our policies?",
            customer_tone="formal",
            agent_type="knowledge",
            booking_context={},
            tags=["formal", "policy_inquiry", "cancellation"],
        ),
        # CASUAL TONE EXAMPLES (10)
        TrainingData(
            customer_message="Hey! How much for hibachi for like 50 people? Trying to throw a party 🎉",
            agent_response="Hey there! 🔥 That sounds like an awesome party!\n\nFor 50 people, here's what we got:\n\n**Standard Package: $2,750** ($55/person)\n- Hibachi chef bringing the show to your place\n- Pick 2 proteins (Chicken, Steak, Shrimp, Scallops, Salmon, or Tofu)\n- Fried rice, veggies, salad, all the sauces\n- Sake for the 21+ crowd\n- We handle everything - you just vibe!\n\nPro tip: Most parties your size go Standard and maybe add some lobster or filet upgrades for a few people! 🍤\n\nWhat's your date looking like?",
            customer_tone="casual",
            agent_type="lead_nurturing",
            booking_context={"guest_count": 50},
            tags=["casual", "pricing_inquiry", "party", "emoji_use"],
        ),
        TrainingData(
            customer_message="Dude, chef showed up 45 mins late yesterday. Not cool.",
            agent_response="Oh no, that's NOT okay at all! I'm really sorry that happened. 😞\n\nHere's what I'm doing RIGHT NOW:\n- Flagged this with my manager (they're gonna hear about it!)\n- Looking into what went wrong\n- Making this right for you ASAP\n\n**How can I fix this?**\n1. Full refund ($550 back in your account)\n2. 50% off your next party\n3. Both! Refund + discount\n\nYou shouldn't have had to deal with that stress. Which option works best for you?\n\nI'll get it processed like TODAY. And I'm making sure this doesn't happen to anyone else.\n\nAgain - really sorry, friend. Let me make this right! 💙",
            customer_tone="casual",
            agent_type="customer_care",
            booking_context={"issue": "late_arrival"},
            tags=["casual", "complaint", "apology", "resolution"],
        ),
        TrainingData(
            customer_message="Hey, just wanted to double-check my booking info!",
            agent_response="Hey! For sure, let me pull that up for you! 👍\n\n**Your Booking:**\n- **When:** [DAY] [DATE], 6:00 PM (chef shows up), cooking starts 6:30 PM\n- **Where:** [ADDRESS]\n- **Who:** [COUNT] people\n- **What:** Standard Package ($[AMOUNT]) - [PROTEINS]\n- **Paid:** $100 deposit ✅ (Rest due day-of: $[BALANCE])\n\n**What happens:**\n- Chef arrives at 6:00 to set up (takes about 30 min)\n- Cooking show starts 6:30 - runs about 90 min\n- We clean up and bounce (15 min)\n\n**You just need:**\n- Regular power outlet\n- Tables & chairs\n- Plates, utensils, glasses\n- Final headcount by Thursday\n\nLooking good! Anything else you wanna check?",
            customer_tone="casual",
            agent_type="operations",
            booking_context={},
            tags=["casual", "confirmation", "friendly"],
        ),
        TrainingData(
            customer_message="What's the deal with cancellations?",
            agent_response="Good question! Here's the breakdown:\n\n**Cancellation Policy:**\n\n🟢 **Cancel 4+ days before?**\n→ Full refund, no problem!\n\n🔴 **Less than 4 days?**\n→ $100 deposit is gone, sorry friend\n\n**Rescheduling:**\n- One free reschedule if requested 24+ hours before event\n- After that? $200 fee\n\n**Exceptions we totally get:**\n- Bad weather (like real bad, not just rain)\n- Medical emergencies\n- Crazy unexpected stuff\n\nJust hit us up at (916) 740-8768 or cs@myhibachichef.com!\n\nNeed anything else?",
            customer_tone="casual",
            agent_type="knowledge",
            booking_context={},
            tags=["casual", "policy", "friendly_explanation"],
        ),
        # DIRECT TONE EXAMPLES (5)
        TrainingData(
            customer_message="Price for 50? Need answer fast.",
            agent_response="**50 guests:**\n\nStandard: **$2,750** ($55/pp)\n\nIncludes:\n• 2 proteins each\n• Rice, veggies, salad\n• Sake (21+)\n• Setup & cleanup\n\nYour date + location?",
            customer_tone="direct",
            agent_type="lead_nurturing",
            booking_context={"guest_count": 50},
            tags=["direct", "pricing", "concise"],
        ),
        TrainingData(
            customer_message="Chef late 45 min. Want refund now.",
            agent_response="**Case #[ID] created**\n\n**Refund options:**\n1. Full refund: $550\n2. 50% next booking\n3. Both\n\n**Pick one - I'll process now.**\n\nSorry this happened.",
            customer_tone="direct",
            agent_type="customer_care",
            booking_context={"issue": "late_arrival"},
            tags=["direct", "complaint", "quick_resolution"],
        ),
        TrainingData(
            customer_message="Confirm my booking.",
            agent_response="**Booking #[ID]:**\n\n• [DATE], 6:00 PM\n• [ADDRESS]\n• [COUNT] guests\n• Standard: [PROTEINS]\n• Paid: $100 | Due: $[BALANCE]\n\n**Need:**\n- Power outlet\n- Tables/chairs\n- Plates/utensils\n- Final count by [DATE]\n\n✅ Confirmed.",
            customer_tone="direct",
            agent_type="operations",
            booking_context={},
            tags=["direct", "confirmation", "bullet_points"],
        ),
        TrainingData(
            customer_message="Cancel policy?",
            agent_response="**Cancellation:**\n\n• 7+ days: Full refund\n• <7 days: $100 deposit gone\n\n**Reschedule:**\n• First 48hrs: FREE\n• After: $100\n\nCall: (916) 740-8768",
            customer_tone="direct",
            agent_type="knowledge",
            booking_context={},
            tags=["direct", "policy", "ultra_concise"],
        ),
        # WARM TONE EXAMPLES (10)
        TrainingData(
            customer_message="Hi! I'm planning my daughter's sweet 16 and I'm SO excited! She LOVES hibachi and I want to make it special for her!",
            agent_response="Oh my gosh, a sweet 16! How exciting! 🎉 This is going to be AMAZING!\n\nYour daughter is going to absolutely LOVE this! For 50 of her friends, here's what I'm thinking:\n\n**Standard Package: $2,750** - This is our most popular for sweet 16s!\n- Your daughter gets to pick 2 proteins (we have Chicken, Steak, Shrimp, Scallops, Salmon, Tofu)\n- The chef will make her birthday SO special with tricks and attention\n- All her friends will be taking videos - it's such a fun experience!\n- We bring everything, set up, cook, and clean up so you can just enjoy her special day! 💕\n\n**Want to make it EXTRA special?** Add some lobster tail upgrades (+$15/person) or filet mignon (+$5/person) for her and a few close friends!\n\nI'm already imagining how happy she'll be! When's the big day? ✨",
            customer_tone="warm",
            agent_type="lead_nurturing",
            booking_context={"event_type": "sweet_16", "guest_count": 50},
            tags=["warm", "birthday", "excited", "personalized"],
        ),
        TrainingData(
            customer_message="I'm so grateful you could help fix our booking issue! You've been amazing through this whole process!",
            agent_response="Aww, you're so sweet! 🥰 That really means the world to me!\n\nHonestly, helping wonderful customers like you is why I love what I do! I'm just so happy we could get everything sorted out for you. Your event is going to be absolutely INCREDIBLE!\n\nI'll be thinking about you on [EVENT_DATE] - I just know everyone is going to have such an amazing time! And please, if you need ANYTHING at all between now and then, you reach out to me directly, okay? I'm here for you! 💕\n\nI'm so excited for you and your guests! This is going to be such a special memory! ✨",
            customer_tone="warm",
            agent_type="customer_care",
            booking_context={},
            tags=["warm", "grateful", "emotional_connection"],
        ),
        # ANXIOUS TONE EXAMPLES (5)
        TrainingData(
            customer_message="Um, hi... I need catering for 50 people but I've never done this before and I'm really stressed about getting everything right...",
            agent_response="I completely understand - planning an event can feel overwhelming! Let me walk you through this step-by-step, and I promise we'll make this easy for you. 💙\n\n**Here's exactly what you need to know:**\n\nFor 50 guests, we have two simple options:\n\n1️⃣ **Standard Package: $2,750** ($55 per person)\n   - ✅ Professional chef comes to your location\n   - ✅ You choose 2 proteins (don't worry, I'll help you decide!)\n   - ✅ Includes rice, vegetables, salad, sauces - everything\n   - ✅ We handle ALL setup and cleanup (you don't lift a finger!)\n\n**Don't stress about:**\n- ❌ Equipment (we bring it all)\n- ❌ Cooking (that's our chef's job!)\n- ❌ Cleanup (we take care of it)\n\n**You only need to:**\n- ✅ Tell me your date and location\n- ✅ Choose proteins (I'll help!)\n- ✅ Have tables, chairs, plates ready\n- ✅ Relax and enjoy your event 😊\n\nTake your time - what questions can I answer to ease your mind?",
            customer_tone="anxious",
            agent_type="lead_nurturing",
            booking_context={"guest_count": 50, "first_time": True},
            tags=["anxious", "reassurance", "step_by_step", "calming"],
        ),
        TrainingData(
            customer_message="I'm really worried about my booking... I haven't heard back and I'm stressed that something went wrong...",
            agent_response="Hey, I'm right here with you, and I want to ease your worry right away. 💙 Let me look at your booking immediately.\n\n**Here's what I'm seeing:**\nYour booking is confirmed and everything looks great! Sometimes our confirmation emails go to spam, which might be why you didn't see it.\n\n**Let me confirm everything for you right now:**\n- ✅ Your date is secured: [DATE]\n- ✅ Your chef is assigned\n- ✅ Your $100 deposit is processed\n- ✅ Everything is on track!\n\n**What I'm doing to help you feel better:**\n1. I'm sending you a fresh confirmation email right now\n2. I'm also texting you the details to (XXX) XXX-XXXX\n3. I'm adding my direct contact so you can reach me anytime\n\nYou're NOT going to be left hanging - I've got you! Take a deep breath. Everything is going to be wonderful. 😊\n\nWhat else can I confirm to help you feel more at ease?",
            customer_tone="anxious",
            agent_type="customer_care",
            booking_context={"issue": "no_confirmation"},
            tags=["anxious", "reassurance", "immediate_action"],
        ),
    ]

    for example in training_examples:
        session.add(example)

    print(f"   ✅ Added {len(training_examples)} tone-matched training examples")


async def seed_upsell_rules(session: AsyncSession):
    """Seed REAL MyHibachi upsell rules"""

    print("\n💎 Seeding Upsell Rules (Real Pricing)...")

    upsell_rules = [
        UpsellRule(
            trigger_context="guest_count >= 20",
            upsell_item="Lobster Tail Upgrade",
            description="Premium lobster tail upgrade for larger parties",
            price_modifier=15.00,
            suggested_tone="warm",
            priority=1,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="guest_count >= 20",
            upsell_item="Filet Mignon Upgrade",
            description="Premium filet mignon upgrade",
            price_modifier=5.00,
            suggested_tone="warm",
            priority=2,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="guest_count >= 20",
            upsell_item="Scallops Upgrade",
            description="Fresh scallops upgrade",
            price_modifier=5.00,
            suggested_tone="casual",
            priority=3,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="guest_count >= 20",
            upsell_item="Salmon Upgrade",
            description="Premium salmon upgrade",
            price_modifier=5.00,
            suggested_tone="casual",
            priority=4,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="event_type == 'corporate'",
            upsell_item="Executive Package",
            description="Premium package for corporate events with filet and lobster",
            price_modifier=20.00,
            suggested_tone="formal",
            priority=1,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="event_type == 'birthday' AND guest_count >= 30",
            upsell_item="Birthday Special Upgrade",
            description="Make the birthday person special with premium proteins",
            price_modifier=10.00,
            suggested_tone="warm",
            priority=1,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="event_type == 'wedding'",
            upsell_item="Wedding Premium Package",
            description="Premium package for wedding celebrations",
            price_modifier=25.00,
            suggested_tone="formal",
            priority=1,
            is_active=True,
        ),
        UpsellRule(
            trigger_context="True",
            upsell_item="Extra Protein Add-on",
            description="Add an extra protein for +$10 each (premium adds upgrade price)",
            price_modifier=10.00,
            suggested_tone="casual",
            priority=5,
            is_active=True,
        ),
    ]

    for rule in upsell_rules:
        session.add(rule)

    print(
        f"   ✅ Added {len(upsell_rules)} upsell rules (lobster, filet, scallops, etc.)"
    )


async def seed_seasonal_offers(session: AsyncSession):
    """Seed seasonal promotional offers"""

    print("\n🎉 Seeding Seasonal Offers...")

    now = datetime.now()

    offers = [
        SeasonalOffer(
            title="Holiday Party Special - Winter 2025",
            description="Book your holiday party and get 10% off for parties of 30+",
            discount_type="percentage",
            discount_value=10.0,
            valid_from=datetime(2025, 11, 15),
            valid_to=datetime(2025, 12, 31),
            applicable_to="parties >= 30 guests",
            is_active=True,
        ),
        SeasonalOffer(
            title="New Year's Eve Premium Package",
            description="Ring in 2026 with our premium package - free lobster upgrade for parties of 40+",
            discount_type="upgrade",
            discount_value=15.0,
            valid_from=datetime(2025, 12, 20),
            valid_to=datetime(2026, 1, 5),
            applicable_to="parties >= 40 guests on NYE",
            is_active=True,
        ),
        SeasonalOffer(
            title="Spring Wedding Season - 2026",
            description="Book your spring wedding and receive complimentary sake service upgrade",
            discount_type="upgrade",
            discount_value=0.0,
            valid_from=datetime(2026, 3, 1),
            valid_to=datetime(2026, 6, 30),
            applicable_to="wedding events",
            is_active=False,
        ),
    ]

    for offer in offers:
        session.add(offer)

    print(f"   ✅ Added {len(offers)} seasonal offers")


async def seed_knowledge_cache(session: AsyncSession):
    """Pre-cache common knowledge queries for fast retrieval"""

    print("\n🧠 Seeding Knowledge Cache (Common Queries)...")

    cache_entries = [
        KnowledgeCache(
            query_hash="pricing_adult_base",
            query_text="how much per adult",
            cached_response="$55 per adult (13+) for standard hibachi service. Includes 2 protein choices, fried rice, vegetables, salad, sauces, and sake for 21+.",
            source_tables=["business_rules", "faq_items"],
            is_valid=True,
        ),
        KnowledgeCache(
            query_hash="pricing_child_base",
            query_text="how much for kids",
            cached_response="$30 per child (ages 6-12). Children 5 and under eat free with adult purchase (1 protein, small rice portion).",
            source_tables=["business_rules", "faq_items"],
            is_valid=True,
        ),
        KnowledgeCache(
            query_hash="party_minimum",
            query_text="minimum party size",
            cached_response="$550 party minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.",
            source_tables=["business_rules", "faq_items"],
            is_valid=True,
        ),
        KnowledgeCache(
            query_hash="deposit_policy",
            query_text="deposit requirement",
            cached_response="$100 refundable deposit secures your date and is deducted from final bill. Refundable if canceled 4+ days before event.",
            source_tables=["business_rules", "faq_items"],
            is_valid=True,
        ),
        KnowledgeCache(
            query_hash="cancellation_policy",
            query_text="cancellation policy",
            cached_response="Full refund if canceled 4+ days before event. Within 4 days, $100 deposit is non-refundable. One free reschedule if requested 24+ hours before event; additional reschedules cost $200.",
            source_tables=["business_rules", "faq_items"],
            is_valid=True,
        ),
    ]

    for entry in cache_entries:
        session.add(entry)

    print(f"   ✅ Cached {len(cache_entries)} common knowledge queries")


if __name__ == "__main__":
    asyncio.run(seed_database())
