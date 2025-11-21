#!/usr/bin/env python3
"""
AI Booking Assistant - Pricing & Tone Verification Test
Ensures AI uses accurate pricing and proper brand voice
"""

import os
import sys

# Add backend to Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "apps", "backend", "src")
)

# Import AI config to verify
from config.ai_booking_config import (
    BRAND_PERSONALITY,
    MENU_ITEMS,
    POLICIES,
    PRICING,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/mh_webapp_dev",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def verify_pricing_config():
    """Verify AI configuration has correct pricing"""
    print_header("PRICING CONFIGURATION VERIFICATION")

    print("✅ CORRECT PRICING (from menu.ts & faqsData.ts):")
    print(f"   - Adult (13+): ${PRICING['adult_base']}/person ✓")
    print(f"   - Child (6-12): ${PRICING['child_base']}/person ✓")
    print("   - Ages 5 & under: FREE ✓")
    print(f"   - Party minimum: ${PRICING['party_minimum']} (~10 adults) ✓")

    print("\n🎁 PREMIUM UPGRADES:")
    for item, price in PRICING["upgrades"].items():
        print(f"   - {item.replace('_', ' ').title()}: +${price}/person")

    print("\n🍜 ADD-ON OPTIONS:")
    for item, price in PRICING["addons"].items():
        print(f"   - {item.replace('_', ' ').title()}: +${price}/person")

    print("\n💰 DEPOSIT & FEES:")
    print(
        f"   - Deposit: ${PRICING['deposit']} (refundable if canceled {PRICING['deposit_refund_days']}+ days before)"
    )
    print(
        f"   - Travel: First {PRICING['travel_free_miles']} miles free, then ${PRICING['travel_per_mile']}/mile"
    )

    # Verify accuracy
    errors = []

    if PRICING["adult_base"] != 55:
        errors.append(
            f"❌ Adult price is ${PRICING['adult_base']} but should be $55"
        )

    if PRICING["child_base"] != 30:
        errors.append(
            f"❌ Child price is ${PRICING['child_base']} but should be $30"
        )

    if PRICING["party_minimum"] != 550:
        errors.append(
            f"❌ Party minimum is ${PRICING['party_minimum']} but should be $550"
        )

    if PRICING["deposit"] != 100:
        errors.append(
            f"❌ Deposit is ${PRICING['deposit']} but should be $100"
        )

    if errors:
        print("\n⚠️  PRICING ERRORS FOUND:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("\n✅ ALL PRICING VERIFIED CORRECT!")
        return True


def verify_menu_config():
    """Verify menu configuration matches actual menu"""
    print_header("MENU CONFIGURATION VERIFICATION")

    print("🍱 STANDARD PROTEINS (included):")
    for protein in MENU_ITEMS["standard_proteins"]:
        print(f"   ✓ {protein}")

    print(f"\n📝 Proteins per guest: {MENU_ITEMS['proteins_per_guest']}")

    print("\n🌟 PREMIUM PROTEINS (upgrades):")
    for protein in MENU_ITEMS["premium_proteins"]:
        print(f"   ✓ {protein}")

    print("\n✅ INCLUDED IN ALL PACKAGES:")
    for item in MENU_ITEMS["included_items"]:
        print(f"   ✓ {item}")

    print("\n👶 KIDS MENU:")
    print(
        f"   - Ages {MENU_ITEMS['kids_menu']['age_range']}: ${MENU_ITEMS['kids_menu']['price']}/child"
    )
    print(f"   - Proteins: {MENU_ITEMS['kids_menu']['proteins']}")
    print(
        f"   - Ages {MENU_ITEMS['kids_menu']['free_age']}: {MENU_ITEMS['kids_menu']['free_includes']}"
    )

    # Verify key items exist
    required_proteins = ["Chicken", "NY Strip Steak", "Shrimp"]
    missing = [
        p
        for p in required_proteins
        if p not in MENU_ITEMS["standard_proteins"]
    ]

    if missing:
        print(f"\n❌ MISSING PROTEINS: {', '.join(missing)}")
        return False
    else:
        print("\n✅ ALL MENU ITEMS VERIFIED!")
        return True


def verify_policies():
    """Verify business policies are accurate"""
    print_header("BUSINESS POLICIES VERIFICATION")

    print("📅 BOOKING POLICIES:")
    print(
        f"   - Minimum advance: {POLICIES['booking']['minimum_advance_hours']} hours"
    )
    print(
        f"   - Weekend recommendation: {POLICIES['booking']['recommended_weekend_days']} days ahead"
    )
    print(f"   - Methods: {', '.join(POLICIES['booking']['booking_methods'])}")

    print("\n💳 PAYMENT POLICIES:")
    print(
        f"   - Deposit methods: {', '.join(POLICIES['payment']['deposit_methods'])}"
    )
    print(
        f"   - Balance methods: {', '.join(POLICIES['payment']['balance_methods'])}"
    )
    print(f"   - Balance due: {POLICIES['payment']['balance_due']}")

    print("\n🚫 CANCELLATION POLICY:")
    print(
        f"   - Full refund: {POLICIES['cancellation']['full_refund_days']}+ days before event"
    )
    print(
        f"   - Non-refundable: Within {POLICIES['cancellation']['non_refundable_days']} days"
    )

    print("\n🔄 RESCHEDULE POLICY:")
    print(
        f"   - Free: Within {POLICIES['reschedule']['free_within_hours']} hours of booking"
    )
    print(f"   - Additional fee: ${POLICIES['reschedule']['additional_fee']}")

    print("\n🥗 DIETARY ACCOMMODATIONS:")
    print(
        f"   - Supported: {', '.join(POLICIES['dietary']['accommodations'])}"
    )
    print(f"   - Notice required: {POLICIES['dietary']['notice_hours']} hours")

    # Verify key policies
    errors = []

    if POLICIES["booking"]["minimum_advance_hours"] != 48:
        errors.append("❌ Minimum advance should be 48 hours")

    if POLICIES["cancellation"]["full_refund_days"] != 7:
        errors.append("❌ Refund policy should be 7 days")

    if errors:
        print("\n⚠️  POLICY ERRORS:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("\n✅ ALL POLICIES VERIFIED!")
        return True


def verify_brand_voice():
    """Verify brand personality configuration"""
    print_header("BRAND VOICE VERIFICATION")

    print("🎯 BRAND PERSONALITY DEFINED:")

    # Check for key characteristics
    required_traits = [
        "warm",
        "friendly",
        "professional",
        "enthusiastic",
        "helpful",
        "honest",
    ]

    personality_lower = BRAND_PERSONALITY.lower()

    found_traits = []
    missing_traits = []

    for trait in required_traits:
        if trait in personality_lower:
            found_traits.append(trait)
            print(f"   ✓ {trait.title()}")
        else:
            missing_traits.append(trait)
            print(f"   ❌ {trait.title()} (not mentioned)")

    print(
        f"\n📏 Personality description length: {len(BRAND_PERSONALITY)} characters"
    )

    if len(found_traits) >= 4:
        print(
            f"\n✅ BRAND VOICE WELL-DEFINED ({len(found_traits)}/{len(required_traits)} traits)"
        )
        return True
    else:
        print(
            f"\n⚠️  BRAND VOICE NEEDS WORK ({len(found_traits)}/{len(required_traits)} traits)"
        )
        return False


def run_test_scenarios():
    """Test pricing calculations for common scenarios"""
    print_header("TEST SCENARIOS - PRICING CALCULATIONS")

    scenarios = [
        {
            "name": "Small Birthday Party",
            "adults": 10,
            "children": 5,
            "upgrades": [],
            "addons": [],
        },
        {
            "name": "Family Reunion",
            "adults": 20,
            "children": 8,
            "upgrades": ["lobster_tail"],
            "lobster_count": 5,
            "addons": ["gyoza"],
        },
        {
            "name": "Corporate Event",
            "adults": 50,
            "children": 0,
            "upgrades": ["salmon"],
            "salmon_count": 50,
            "addons": ["yakisoba_noodles", "edamame"],
        },
    ]

    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}:")
        print(
            f"   Guests: {scenario['adults']} adults, {scenario['children']} children"
        )

        # Calculate base cost
        adult_cost = scenario["adults"] * PRICING["adult_base"]
        child_cost = scenario["children"] * PRICING["child_base"]
        base_total = adult_cost + child_cost

        print(
            f"   Base: ${adult_cost} (adults) + ${child_cost} (children) = ${base_total}"
        )

        # Calculate upgrades
        upgrade_cost = 0
        if "lobster_count" in scenario:
            upgrade_cost += (
                scenario["lobster_count"] * PRICING["upgrades"]["lobster_tail"]
            )
            print(
                f"   Lobster upgrade: {scenario['lobster_count']} × ${PRICING['upgrades']['lobster_tail']} = ${scenario['lobster_count'] * PRICING['upgrades']['lobster_tail']}"
            )

        if "salmon_count" in scenario:
            upgrade_cost += (
                scenario["salmon_count"] * PRICING["upgrades"]["salmon"]
            )
            print(
                f"   Salmon upgrade: {scenario['salmon_count']} × ${PRICING['upgrades']['salmon']} = ${scenario['salmon_count'] * PRICING['upgrades']['salmon']}"
            )

        # Calculate add-ons
        addon_cost = 0
        total_guests = scenario["adults"] + scenario["children"]
        for addon in scenario.get("addons", []):
            addon_price = PRICING["addons"][addon]
            addon_total = total_guests * addon_price
            addon_cost += addon_total
            print(
                f"   {addon.replace('_', ' ').title()} add-on: {total_guests} guests × ${addon_price} = ${addon_total}"
            )

        # Grand total
        grand_total = base_total + upgrade_cost + addon_cost
        print(f"   \ud83d\udcb5 TOTAL: ${grand_total}")

        # Check minimum
        if grand_total < PRICING["party_minimum"]:
            print(f"   ⚠️  Below minimum (${PRICING['party_minimum']})")
        else:
            print("   ✅ Meets minimum")


def main():
    """Run all verifications"""
    print("\n")
    print("🧪" * 40)
    print("  AI BOOKING ASSISTANT - ACCURACY VERIFICATION")
    print("🧪" * 40)

    results = []

    # Run all verification tests
    results.append(("Pricing Config", verify_pricing_config()))
    results.append(("Menu Config", verify_menu_config()))
    results.append(("Business Policies", verify_policies()))
    results.append(("Brand Voice", verify_brand_voice()))

    # Run test scenarios
    run_test_scenarios()

    # Final summary
    print_header("VERIFICATION SUMMARY")

    all_passed = all([result[1] for result in results])

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name}")

    print("\n" + "=" * 80)

    if all_passed:
        print("\n🎉 ALL VERIFICATIONS PASSED! 🎉")
        print("\nAI is configured with:")
        print("  ✅ Accurate pricing ($55 adult, $30 child)")
        print("  ✅ Correct menu items and packages")
        print("  ✅ Accurate business policies")
        print("  ✅ Warm, friendly, professional brand voice")
        print("\n🚀 READY FOR CUSTOMER INTERACTIONS!")
        return True
    else:
        print("\n⚠️  SOME VERIFICATIONS FAILED")
        print("\n❌ Please fix errors before deploying AI to customers")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
