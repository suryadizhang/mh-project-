"""Test the bulletproof AI configuration"""

import sys

sys.path.insert(0, "apps/backend/src")

from config.ai_booking_config_v2 import (
    PRICING,
    PRICING_CALCULATOR,
    validate_configuration,
)

print("=" * 80)
print("🔒 BULLETPROOF AI CONFIGURATION VALIDATION")
print("=" * 80)

# Run validation
result = validate_configuration()

if result["passed"]:
    print("\n✅ ALL VALIDATION TESTS PASSED!")
    print(f"   Tests run: {result['tests_run']}")
else:
    print("\n❌ VALIDATION FAILED!")
    print(f"   Errors found: {len(result['errors'])}")
    for error in result["errors"]:
        print(f"   - {error}")

# Test calculations
print("\n" + "=" * 80)
print("📊 CALCULATION TESTS")
print("=" * 80)

test_cases = [
    ("20 adults", 20, 0, 0, 1100.00),
    ("10 adults + 5 children", 10, 5, 0, 700.00),
    ("30 adults", 30, 0, 0, 1650.00),
    (
        "5 adults (below minimum)",
        5,
        0,
        0,
        275.00,
    ),  # Base cost, minimum will apply
]

all_passed = True
for name, adults, children, under_5, expected_base in test_cases:
    result = PRICING_CALCULATOR.calculate_base_cost(adults, children, under_5)
    actual_base = result["base_cost"]
    final_cost = result["final_cost_after_minimum"]

    if actual_base == expected_base:
        print(f"\n✅ {name}")
        print(f"   Base: ${actual_base:.2f}")
        if result["minimum_applied"]:
            print(
                f"   After minimum: ${final_cost:.2f} (minimum ${PRICING['party_minimum']} applied)"
            )
        print(f"   Meets minimum: {result['meets_minimum']}")
    else:
        print(f"\n❌ {name}")
        print(f"   Expected: ${expected_base:.2f}")
        print(f"   Got: ${actual_base:.2f}")
        all_passed = False

# Test upgrades
print("\n" + "=" * 80)
print("💎 UPGRADE CALCULATION TEST")
print("=" * 80)

try:
    upgrade_result = PRICING_CALCULATOR.calculate_upgrade_cost(
        total_guests=30, filet_mignon=15, lobster_tail=10
    )
    expected_upgrade = 225.00  # (15 × $5) + (10 × $15) = $75 + $150

    if upgrade_result["upgrade_total"] == expected_upgrade:
        print("✅ 30 people with 15 filet + 10 lobster")
        print(f"   Upgrade cost: ${upgrade_result['upgrade_total']:.2f}")
        print(f"   Breakdown: {upgrade_result['breakdown']}")
    else:
        print("❌ Upgrade calculation failed")
        print(f"   Expected: ${expected_upgrade:.2f}")
        print(f"   Got: ${upgrade_result['upgrade_total']:.2f}")
        all_passed = False
except Exception as e:
    print(f"❌ Upgrade test crashed: {e}")
    all_passed = False

# Test travel fee
print("\n" + "=" * 80)
print("🚗 TRAVEL FEE TEST")
print("=" * 80)

travel_tests = [
    (25.0, 0.00, "Within free zone"),
    (30.0, 0.00, "Exactly at free limit"),
    (50.0, 40.00, "Beyond free zone"),
]

for distance, expected_fee, description in travel_tests:
    travel_result = PRICING_CALCULATOR.calculate_travel_fee(distance)
    if travel_result["travel_fee"] == expected_fee:
        print(
            f"✅ {distance} miles - {description}: ${travel_result['travel_fee']:.2f}"
        )
    else:
        print(
            f"❌ {distance} miles expected ${expected_fee:.2f}, got ${travel_result['travel_fee']:.2f}"
        )
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED - CONFIGURATION IS PRODUCTION-READY")
else:
    print("❌ SOME TESTS FAILED - DO NOT DEPLOY")
print("=" * 80)
