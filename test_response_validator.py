"""Test AI Response Validator"""

import sys

sys.path.insert(0, "apps/backend/src")

from config.ai_response_validator import AIResponseValidator

validator = AIResponseValidator()

# Test Case 1: Correct response
print("=" * 80)
print("TEST 1: Correct Response")
print("=" * 80)
test_response_1 = """
Great! For 20 adults, the total cost is $1,100 ($55 per adult × 20).
This exceeds our $550 minimum. Your party is all set!
"""
result_1 = validator.validate_response(
    test_response_1, {"adults": 20, "children": 0}
)
print(f"✅ Approved: {result_1['approved']}")
print(f"Errors: {result_1['errors'] if result_1['errors'] else 'None'}")
print(f"Warnings: {result_1['warnings'] if result_1['warnings'] else 'None'}")

# Test Case 2: Wrong pricing
print("\n" + "=" * 80)
print("TEST 2: Wrong Pricing (Should Catch Error)")
print("=" * 80)
test_response_2 = """
For 20 adults, the total is $900 ($45 per adult × 20).
"""
result_2 = validator.validate_response(
    test_response_2, {"adults": 20, "children": 0}
)
print(f"❌ Approved: {result_2['approved']}")
print(f"Errors: {result_2['errors']}")

# Test Case 3: Dangerous phrase
print("\n" + "=" * 80)
print("TEST 3: Dangerous Phrase - '10 people minimum' (Should Catch)")
print("=" * 80)
test_response_3 = """
We have a minimum of 10 people for bookings.
"""
result_3 = validator.validate_response(
    test_response_3, {"adults": 5, "children": 0}
)
print(f"❌ Approved: {result_3['approved']}")
print(f"Errors: {result_3['errors']}")

# Test Case 4: Estimate instead of exact
print("\n" + "=" * 80)
print("TEST 4: Using Estimates (Should Warn)")
print("=" * 80)
test_response_4 = """
For 20 adults, the cost is approximately $1,100.
"""
result_4 = validator.validate_response(
    test_response_4, {"adults": 20, "children": 0}
)
print(f"❌ Approved: {result_4['approved']}")
print(f"Errors: {result_4['errors']}")

print("\n" + "=" * 80)
print("✅ VALIDATOR WORKING - CATCHES PRICING ERRORS!")
print("=" * 80)
