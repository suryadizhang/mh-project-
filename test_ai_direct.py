"""
Direct test of AI with our pricing config - NO DOCKER, NO FASTAPI
"""

import asyncio
import os
import sys

# Add backend src to path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "apps", "backend", "src")
)

from config.ai_booking_config_v2 import (
    AI_REASONING_RULES,
    AI_UNDERSTANDING_PRINCIPLES,
    BRAND_PERSONALITY,
    PRICING,
)
from openai import AsyncOpenAI


async def test_ai():
    print("=" * 80)
    print("🧪 DIRECT AI TEST - Bypassing all FastAPI/Docker middleware")
    print("=" * 80)

    # Load OpenAI key from .env
    env_file = os.path.join(
        os.path.dirname(__file__), "apps", "backend", ".env"
    )
    api_key = None

    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if "OPENAI_API_KEY" in line and not line.strip().startswith(
                    "#"
                ):
                    api_key = (
                        line.split("=", 1)[1].strip().strip('"').strip("'")
                    )
                    break

    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in apps/backend/.env")
        return

    print(f"✅ OpenAI API Key loaded: {api_key[:10]}...{api_key[-4:]}")

    # Print our config
    print("\n📋 AI BOOKING CONFIG:")
    print(f"   Adult Price: ${PRICING['adult_base']}")
    print(f"   Child Price: ${PRICING['child_base']}")
    print(f"   Minimum: ${PRICING['party_minimum']}")
    print(f"   Deposit: ${PRICING.get('deposit_amount', 100)}")

    print("\n🎨 BRAND VOICE:")
    print(BRAND_PERSONALITY[:200] + "...")

    # Build system prompt with COMPREHENSIVE KNOWLEDGE + SEMANTIC UNDERSTANDING
    system_prompt = f"""You are the My Hibachi booking assistant - a knowledgeable hospitality professional.

{AI_UNDERSTANDING_PRINCIPLES}

{AI_REASONING_RULES}

PRICING (USE THESE EXACT NUMBERS):
- Adults (13+): ${PRICING['adult_base']} per person
- Children (6-12): ${PRICING['child_base']} per person  
- Children under 5: FREE
- Minimum Order: ${PRICING['party_minimum']} TOTAL (this is a DOLLAR AMOUNT, not people count!)
- Deposit Required: ${PRICING['deposit']}
- Travel: First 30 miles FREE, then $2/mile

MENU HIGHLIGHTS:
- Each guest chooses 2 proteins (Chicken, Steak, Shrimp, Calamari, Tofu)
- Premium upgrades: Salmon/Scallops/Filet +$5, Lobster +$15
- Includes: fried rice, vegetables, salad, sauces, sake (21+)
- Add-ons available: 3rd protein +$10, Yakisoba/Rice/Veggies/Edamame +$5, Gyoza +$10

{BRAND_PERSONALITY}

COMPREHENSIVE BUSINESS KNOWLEDGE:
You have deep understanding of:
- All menu options and customizations
- Dietary accommodations (vegan, gluten-free, halal, kosher, etc.)
- Setup requirements and space needs
- Weather policies and backup planning
- Safety protocols and insurance
- Service areas throughout Northern California
- Booking process and payment options
- Cancellation and rescheduling policies
- Special events (birthdays, corporate, etc.)

REMEMBER: Use your knowledge naturally. Be helpful, warm, and proactive. Show calculations when discussing pricing.
"""

    # Test queries - mix of pricing AND business logic questions
    test_queries = [
        "How much for 20 people?",
        "What's the price for 10 adults and 5 kids?",
        "Can you do a birthday party for my daughter? She has friends with peanut allergies",
        "Do you serve vegan options? My party has 15 people and 3 are vegan",
        "What if it rains on the day of the party?",
    ]

    client = AsyncOpenAI(api_key=api_key, timeout=30.0)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"📝 TEST {i}: {query}")
        print(f"{'='*80}")

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",  # GPT-4o: Latest model with deep reasoning & natural conversation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
            )

            ai_response = response.choices[0].message.content

            print("\n🤖 AI RESPONSE:")
            print(f"{ai_response}")

            # Check for correct pricing
            if query == test_queries[0]:  # 20 people
                expected_total = 20 * PRICING["adult_base"]  # $1,100
                if (
                    str(expected_total) in ai_response
                    or f"${expected_total}" in ai_response
                    or f"${expected_total:,}" in ai_response
                ):
                    print(
                        f"\n✅ CORRECT PRICING: Found ${expected_total} for 20 adults"
                    )
                else:
                    print(
                        f"\n⚠️  WARNING: Expected ${expected_total} not clearly found in response"
                    )

            elif query == test_queries[1]:  # 10 adults + 5 kids
                expected_total = (10 * PRICING["adult_base"]) + (
                    5 * PRICING["child_base"]
                )  # $700
                if (
                    str(expected_total) in ai_response
                    or f"${expected_total}" in ai_response
                ):
                    print(
                        f"\n✅ CORRECT PRICING: Found ${expected_total} (10 adults × ${PRICING['adult_base']} + 5 kids × ${PRICING['child_base']})"
                    )
                else:
                    print(
                        f"\n⚠️  WARNING: Expected ${expected_total} not found"
                    )

            # Check tone
            warm_words = [
                "excited",
                "love",
                "great",
                "wonderful",
                "happy",
                "pleased",
                "delighted",
                "!",
            ]
            has_warm_tone = any(
                word in ai_response.lower() for word in warm_words
            )
            if has_warm_tone:
                print("✅ WARM TONE: Detected friendly/enthusiastic language")
            else:
                print(
                    "⚠️  TONE: Response seems neutral/professional but not particularly warm"
                )

            print("\n📊 METADATA:")
            print(f"   Model: {response.model}")
            print(
                f"   Tokens: {response.usage.total_tokens} (in: {response.usage.prompt_tokens}, out: {response.usage.completion_tokens})"
            )

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'='*80}")
    print("✅ DIRECT AI TEST COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_ai())
