"""
AI Response Validator - Production Safety Layer v3.0
=====================================================

This module validates EVERY AI response before it reaches customers.
Catches pricing errors, policy mistakes, and logical inconsistencies.

⚠️  CRITICAL: This runs on EVERY customer-facing AI response

v3.0 ENHANCEMENTS:
- Price sanity checks (rejects <$300 or >$10,000)
- Confidence threshold validation
- Tool enforcement verification
- Enhanced error detection
"""

import re
from typing import Any
from config.ai_booking_config_v2 import PRICING, PRICING_CALCULATOR


# Price sanity check bounds
PRICE_SANITY_MIN = 300  # Reject quotes below $300 (likely error)
PRICE_SANITY_MAX = 10000  # Reject quotes above $10,000 (likely error)

# Normal price ranges for validation
PRICE_RANGES = {
    "small_party": (550, 900),  # 10-15 people
    "medium_party": (1100, 1800),  # 20-30 people
    "large_party": (2200, 3500),  # 40-60 people
}


class AIResponseValidator:
    """
    Validates AI responses for accuracy and safety.

    Checks:
    - Pricing accuracy
    - Mathematical correctness
    - Policy consistency
    - No contradictions
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_response(self, ai_response: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Validate AI response before sending to customer.

        v3.0 VALIDATIONS:
        - Price sanity checks (min/max bounds)
        - Mathematical accuracy
        - Dangerous phrase detection
        - Logical contradiction checks
        - Confidence threshold verification

        Args:
            ai_response: The AI's response text
            context: Request context (party size, upgrades, etc.)

        Returns:
            {
                "approved": bool,
                "errors": list[str],
                "warnings": list[str],
                "safe_to_send": bool,
                "sanity_checks": dict
            }
        """
        self.errors = []
        self.warnings = []

        # Extract numbers from response
        prices_mentioned = self._extract_prices(ai_response)

        # v3.0: Price sanity checks FIRST (catches catastrophic errors)
        sanity_result = self._sanity_check_prices(prices_mentioned, context)

        # Validate pricing accuracy
        if "adults" in context:
            self._validate_party_pricing(ai_response, context, prices_mentioned)

        # Check for dangerous phrases
        self._check_dangerous_phrases(ai_response)

        # Check for contradictions
        self._check_contradictions(ai_response)

        # v3.0: Verify tool usage (if context indicates pricing query)
        if context.get("is_pricing_query"):
            self._verify_tool_usage(context)

        return {
            "approved": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "safe_to_send": len(self.errors) == 0,
            "sanity_checks": sanity_result,
        }

    def _sanity_check_prices(self, prices: list[float], context: dict[str, Any]) -> dict[str, Any]:
        """
        v3.0: Sanity check all prices mentioned in response.

        Rejects quotes that are clearly wrong:
        - Below $300 (below party minimum, likely error)
        - Above $10,000 (would need 180+ people, likely error)
        - Negative prices
        - Prices that don't match party size

        Args:
            prices: List of dollar amounts extracted from response
            context: Request context with party size

        Returns:
            {"passed": bool, "issues": list[str]}
        """
        issues = []

        # Separate per-person prices from total quotes
        per_person_prices = [p for p in prices if p <= 100]  # Likely per-person
        total_quotes = [p for p in prices if p > 100]  # Likely total quotes

        # Check for unrealistic prices
        for price in prices:
            if price < 0:
                self.errors.append(f"SANITY CHECK FAILED: Negative price ${price:.2f} detected")
                issues.append(f"Negative price: ${price:.2f}")

        # Sanity check TOTAL quotes only (not per-person prices)
        for price in total_quotes:
            if price < PRICE_SANITY_MIN:
                self.errors.append(
                    f"SANITY CHECK FAILED: Total quote ${price:.2f} below minimum threshold "
                    f"(${PRICE_SANITY_MIN}). This is likely an error - party minimum is $550."
                )
                issues.append(f"Quote too low: ${price:.2f} < ${PRICE_SANITY_MIN}")

            if price > PRICE_SANITY_MAX:
                self.errors.append(
                    f"SANITY CHECK FAILED: Total quote ${price:.2f} exceeds maximum threshold "
                    f"(${PRICE_SANITY_MAX}). This would require 180+ people - likely an error."
                )
                issues.append(f"Quote too high: ${price:.2f} > ${PRICE_SANITY_MAX}")

        # Check price makes sense for party size
        if "adults" in context and total_quotes:
            adults = context.get("adults", 0)
            children = context.get("children", 0)
            total_guests = adults + children

            if total_guests > 0:
                # Expected range (rough estimate)
                min_expected = max(PRICING["party_minimum"], total_guests * 50)  # $50/person min
                max_expected = total_guests * 100  # $100/person max (with upgrades)

                for quote in total_quotes:
                    if quote < min_expected * 0.7:  # 30% tolerance
                        self.warnings.append(
                            f"Quote ${quote:.2f} seems low for {total_guests} guests "
                            f"(expected ${min_expected:.2f}+)"
                        )
                        issues.append("Quote low for party size")

                    if quote > max_expected * 1.5:  # 50% tolerance
                        self.warnings.append(
                            f"Quote ${quote:.2f} seems high for {total_guests} guests "
                            f"(expected <${max_expected:.2f})"
                        )
                        issues.append("Quote high for party size")

        return {
            "passed": len([e for e in self.errors if "SANITY CHECK FAILED" in e]) == 0,
            "issues": issues,
        }

    def _verify_tool_usage(self, context: dict[str, Any]) -> None:
        """
        v3.0: Verify that pricing_tool was used for pricing queries.

        If context indicates this was a pricing query, check that
        the tool was actually called (not manual calculation).

        Args:
            context: Request context with tool usage info
        """
        used_tools = context.get("tools_used", [])

        if context.get("is_pricing_query") and "calculate_party_quote" not in used_tools:
            self.errors.append(
                "TOOL ENFORCEMENT VIOLATION: Pricing query detected but "
                "calculate_party_quote tool was not used. AI must call pricing_tool "
                "for all pricing calculations to prevent hallucination errors."
            )

    def _extract_prices(self, text: str) -> list[float]:
        """Extract all dollar amounts from text"""
        # Match $X, $X.XX, $X,XXX, etc.
        pattern = r"\$([0-9,]+(?:\.[0-9]{2})?)"
        matches = re.findall(pattern, text)
        return [float(m.replace(",", "")) for m in matches]

    def _validate_party_pricing(
        self, response: str, context: dict[str, Any], prices_mentioned: list[float]
    ):
        """Validate party pricing calculations"""
        adults = context.get("adults", 0)
        children = context.get("children", 0)
        children_under_5 = context.get("children_under_5", 0)

        if adults == 0:
            return  # No validation needed

        # Calculate expected price
        calc_result = PRICING_CALCULATOR.calculate_base_cost(adults, children, children_under_5)

        expected_base = calc_result["base_cost"]
        expected_final = calc_result["final_cost_after_minimum"]

        # Check if expected price is in response
        expected_prices = [expected_base]
        if expected_final != expected_base:
            expected_prices.append(expected_final)

        # Add upgrade costs if mentioned
        if "filet" in response.lower() or "lobster" in response.lower():
            # Can't validate without knowing exact upgrade counts
            self.warnings.append("Response mentions upgrades but validation needs exact counts")

        # Check if ANY expected price appears
        found_correct_price = any(
            any(abs(mentioned - expected) < 0.01 for mentioned in prices_mentioned)
            for expected in expected_prices
        )

        if not found_correct_price and prices_mentioned:
            # AI mentioned a price but it's wrong!
            self.errors.append(
                f"PRICING ERROR: Expected ${expected_final:.2f} for "
                f"{adults} adults + {children} children, but AI mentioned: "
                f"{', '.join(f'${p:.2f}' for p in prices_mentioned)}"
            )

    def _check_dangerous_phrases(self, response: str):
        """Check for phrases that could cause customer confusion"""
        dangerous_phrases = [
            # Confusing minimum with people count
            (r"minimum (?:of )?10 people", "Confuses $550 minimum with '10 people'"),
            (r"need at least 10 adults", "Confuses $550 minimum with '10 people'"),
            (r"10 person minimum", "Confuses $550 minimum with '10 people'"),
            # Wrong pricing
            (r"\$45", "Wrong adult price (should be $55)"),
            (r"\$35", "Wrong child price (should be $30)"),
            (r"\$65", "Wrong pricing tier (we don't have tiers)"),
            # Contradictions
            (
                r"(?:maybe|possibly|approximately|around|roughly) \$",
                "Using estimates instead of exact prices",
            ),
        ]

        for pattern, reason in dangerous_phrases:
            if re.search(pattern, response, re.IGNORECASE):
                self.errors.append(f"DANGEROUS PHRASE: {reason} | Pattern: {pattern}")

    def _check_contradictions(self, response: str):
        """Check for logical contradictions"""
        # Check if AI says something meets minimum but quotes below $550
        if "meets minimum" in response.lower() or "exceeds minimum" in response.lower():
            prices = self._extract_prices(response)
            below_minimum = [p for p in prices if p < 550 and p > 10]  # Ignore unit prices

            if below_minimum:
                self.warnings.append(
                    f"Says 'meets minimum' but mentions price below $550: {below_minimum}"
                )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    validator = AIResponseValidator()

    # Test Case 1: Correct response
    print("=" * 80)
    print("TEST 1: Correct Response")
    print("=" * 80)
    test_response_1 = """
    Great! For 20 adults, the total cost is $1,100 ($55 per adult × 20).
    This exceeds our $550 minimum. Your party is all set!
    """
    result_1 = validator.validate_response(test_response_1, {"adults": 20, "children": 0})
    print(f"Approved: {result_1['approved']}")
    print(f"Errors: {result_1['errors']}")
    print(f"Warnings: {result_1['warnings']}")

    # Test Case 2: Wrong pricing
    print("\n" + "=" * 80)
    print("TEST 2: Wrong Pricing (Should Catch Error)")
    print("=" * 80)
    test_response_2 = """
    For 20 adults, the total is $900 ($45 per adult × 20).
    """
    result_2 = validator.validate_response(test_response_2, {"adults": 20, "children": 0})
    print(f"Approved: {result_2['approved']}")
    print(f"Errors: {result_2['errors']}")
    print(f"Warnings: {result_2['warnings']}")

    # Test Case 3: Dangerous phrase
    print("\n" + "=" * 80)
    print("TEST 3: Dangerous Phrase (Should Catch)")
    print("=" * 80)
    test_response_3 = """
    We have a minimum of 10 people for bookings.
    """
    result_3 = validator.validate_response(test_response_3, {"adults": 5, "children": 0})
    print(f"Approved: {result_3['approved']}")
    print(f"Errors: {result_3['errors']}")
    print(f"Warnings: {result_3['warnings']}")

    # Test Case 4: Estimate instead of exact
    print("\n" + "=" * 80)
    print("TEST 4: Using Estimates (Should Warn)")
    print("=" * 80)
    test_response_4 = """
    For 20 adults, the cost is approximately $1,100.
    """
    result_4 = validator.validate_response(test_response_4, {"adults": 20, "children": 0})
    print(f"Approved: {result_4['approved']}")
    print(f"Errors: {result_4['errors']}")
    print(f"Warnings: {result_4['warnings']}")
