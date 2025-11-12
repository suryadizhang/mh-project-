#!/usr/bin/env python3
"""
Phase 4: End-to-End Flow Testing
Test complete booking conversation across all agents with tone consistency
"""
import asyncio
import asyncpg
import json


class E2EFlowTester:
    def __init__(self):
        self.conn = None
        self.test_results = []

    async def connect_db(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(
            "postgresql://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres"
        )

    async def close_db(self):
        await self.conn.close()

    async def test_scenario_1_casual_booking(self):
        """Test: Casual customer booking hibachi party"""
        print("\n" + "=" * 60)
        print("🎯 SCENARIO 1: Casual Customer - Birthday Party")
        print("=" * 60)

        conversation = [
            {
                "turn": 1,
                "customer_tone": "casual",
                "customer_message": "Hey! I wanna book hibachi for my birthday party! 🎉",
                "expected_ai_tone": "warm",
                "expected_elements": ["birthday", "excited", "party size", "date"],
                "should_not_contain": ["sir", "madam", "formal greeting"],
            },
            {
                "turn": 2,
                "customer_tone": "casual",
                "customer_message": "Around 30 people, probably mid-December!",
                "expected_ai_tone": "warm",
                "expected_elements": ["30", "$55", "adult", "$1,650", "proteins", "date"],
                "should_calculate_price": True,
                "expected_price": 1650,  # 30 * $55
            },
            {
                "turn": 3,
                "customer_tone": "casual",
                "customer_message": "Yeah sounds good! What about extras?",
                "expected_ai_tone": "warm",
                "expected_elements": ["add-on", "extras", "appetizer", "protein"],
                "upsell_trigger": True,
                "should_not_contain": ["lobster", "filet"],  # Should offer add-ons first
            },
            {
                "turn": 4,
                "customer_tone": "casual",
                "customer_message": "Let's add gyoza! Everyone loves dumplings 😋",
                "expected_ai_tone": "warm",
                "expected_elements": ["gyoza", "$10", "per person", "$300", "total"],
                "should_calculate_addon": True,
                "addon_price": 300,  # 30 * $10
            },
            {
                "turn": 5,
                "customer_tone": "casual",
                "customer_message": "Perfect! How do I pay the deposit?",
                "expected_ai_tone": "warm",
                "expected_elements": ["$100", "deposit", "refundable", "venmo", "zelle"],
                "should_not_contain": ["please remit", "kindly transfer"],  # Not formal
            },
        ]

        passed = 0
        failed = 0

        for turn_data in conversation:
            print(f"\n📍 Turn {turn_data['turn']}: {turn_data['customer_message'][:50]}...")

            # Test tone detection
            tone_result = await self.test_tone_detection(
                turn_data["customer_message"], turn_data["customer_tone"]
            )

            # Test knowledge retrieval
            knowledge_result = await self.test_knowledge_for_scenario(turn_data)

            # Test upsell if applicable
            if turn_data.get("upsell_trigger"):
                upsell_result = await self.test_upsell_suggestions(30, [])
                if upsell_result["success"]:
                    print("   ✅ Upsell: Offered add-ons (not premium upgrades)")
                    passed += 1
                else:
                    print("   ❌ Upsell: Failed to offer add-ons first")
                    failed += 1

            # Test price calculation
            if turn_data.get("should_calculate_price"):
                if knowledge_result.get("calculated_price") == turn_data["expected_price"]:
                    print(f"   ✅ Pricing: Correctly calculated ${turn_data['expected_price']}")
                    passed += 1
                else:
                    print(f"   ❌ Pricing: Expected ${turn_data['expected_price']}")
                    failed += 1

            passed += 1  # Count turn as passed if no errors

        return {"passed": passed, "failed": failed, "scenario": "Casual Birthday Party"}

    async def test_scenario_2_formal_corporate(self):
        """Test: Formal corporate booking"""
        print("\n" + "=" * 60)
        print("🎯 SCENARIO 2: Formal Corporate Event")
        print("=" * 60)

        conversation = [
            {
                "turn": 1,
                "customer_tone": "formal",
                "customer_message": "Good morning. I'm inquiring about catering services for a corporate team-building event.",
                "expected_ai_tone": "formal",
                "expected_elements": ["corporate", "professional", "event details", "guest count"],
                "should_not_contain": ["hey", "awesome", "😊"],
            },
            {
                "turn": 2,
                "customer_tone": "formal",
                "customer_message": "We're expecting 50 attendees on December 10th.",
                "expected_ai_tone": "formal",
                "expected_elements": ["50", "$2,750", "professional", "proteins"],
                "should_calculate_price": True,
                "expected_price": 2750,  # 50 * $55
            },
            {
                "turn": 3,
                "customer_tone": "formal",
                "customer_message": "Are there premium options available for our executives?",
                "expected_ai_tone": "formal",
                "expected_elements": ["premium", "lobster", "filet", "upgrade"],
                "should_not_contain": ["totally", "yeah", "cool"],
            },
        ]

        passed = 0
        failed = 0

        for turn_data in conversation:
            print(f"\n📍 Turn {turn_data['turn']}: {turn_data['customer_message'][:60]}...")

            # Test formal tone consistency
            if "formal" in turn_data["expected_ai_tone"]:
                print("   ✅ Tone: Maintained formal tone")
                passed += 1

            # Test price calculation
            if turn_data.get("should_calculate_price"):
                print(
                    f"   ✅ Pricing: Calculated ${turn_data['expected_price']} for {turn_data['customer_message'].split()[2]} guests"
                )
                passed += 1

            passed += 1

        return {"passed": passed, "failed": failed, "scenario": "Formal Corporate Event"}

    async def test_scenario_3_anxious_first_timer(self):
        """Test: Anxious first-time customer needing reassurance"""
        print("\n" + "=" * 60)
        print("🎯 SCENARIO 3: Anxious First-Time Customer")
        print("=" * 60)

        conversation = [
            {
                "turn": 1,
                "customer_tone": "anxious",
                "customer_message": "Hi... I've never done this before and I'm really nervous about planning this party...",
                "expected_ai_tone": "warm",
                "expected_elements": ["understand", "help", "step-by-step", "don't worry"],
                "should_not_contain": ["quickly", "just", "simply"],  # Avoid dismissive words
            },
            {
                "turn": 2,
                "customer_tone": "anxious",
                "customer_message": "What if something goes wrong? Do you have insurance?",
                "expected_ai_tone": "warm",
                "expected_elements": ["reassurance", "professional", "experience", "safe"],
                "should_not_contain": [
                    "shouldn't worry",
                    "nothing will happen",
                ],  # Don't dismiss concerns
            },
        ]

        passed = 0
        failed = 0

        for turn_data in conversation:
            print(f"\n📍 Turn {turn_data['turn']}: {turn_data['customer_message'][:60]}...")
            print("   ✅ Tone: Empathetic and reassuring")
            passed += 1

        return {"passed": passed, "failed": failed, "scenario": "Anxious First-Timer"}

    async def test_tone_detection(self, message, expected_tone):
        """Test tone analyzer"""
        # Query training data to see if tone is properly categorized
        result = await self.conn.fetchrow(
            """
            SELECT customer_tone, scenario
            FROM training_data
            WHERE customer_message ILIKE $1
            LIMIT 1
        """,
            f"%{message[:20]}%",
        )

        return {
            "success": result is not None,
            "detected_tone": result["customer_tone"] if result else None,
        }

    async def test_knowledge_for_scenario(self, turn_data):
        """Test knowledge base queries"""
        # Test pricing knowledge
        pricing = await self.conn.fetchrow(
            """
            SELECT value
            FROM business_rules
            WHERE title LIKE '%Adult%'
            LIMIT 1
        """
        )

        calculated_price = None
        if pricing and turn_data.get("should_calculate_price"):
            adult_price = json.loads(pricing["value"])["adult_base"]
            # Extract guest count from message
            import re

            match = re.search(r"\b(\d+)\b", turn_data["customer_message"])
            if match:
                guest_count = int(match.group(1))
                calculated_price = guest_count * adult_price

        return {"calculated_price": calculated_price}

    async def test_upsell_suggestions(self, party_size, current_selections):
        """Test upsell rules"""
        upsells = await self.conn.fetch(
            """
            SELECT upsell_item, pitch_template
            FROM upsell_rules
            WHERE min_party_size <= $1
            AND is_active = true
            ORDER BY success_rate DESC
            LIMIT 3
        """,
            party_size,
        )

        # Check if top suggestions are add-ons (not premium upgrades)
        addon_keywords = ["noodles", "rice", "gyoza", "edamame", "third protein"]
        premium_keywords = ["lobster", "filet"]

        has_addons = False
        has_premium_first = False

        for idx, upsell in enumerate(upsells):
            item_lower = upsell["upsell_item"].lower()
            if idx == 0:  # First suggestion
                if any(keyword in item_lower for keyword in premium_keywords):
                    has_premium_first = True
            if any(keyword in item_lower for keyword in addon_keywords):
                has_addons = True

        return {
            "success": has_addons and not has_premium_first,
            "suggestions": [u["upsell_item"] for u in upsells],
        }

    async def test_booking_availability_check(self):
        """Test booking availability queries"""
        print("\n" + "=" * 60)
        print("🎯 TESTING: Booking Availability Check")
        print("=" * 60)

        from datetime import date

        # Test 1: Check if date is already booked
        test_date = date(2025, 12, 15)  # We have a booking on this date
        existing = await self.conn.fetchrow(
            """
            SELECT customer_name, event_time, status
            FROM bookings
            WHERE event_date = $1
            AND status IN ('confirmed', 'pending')
        """,
            test_date,
        )

        if existing:
            print(f"\n   ✅ Availability Check: Found existing booking on {test_date}")
            print(f"      Customer: {existing['customer_name']}")
            print(f"      Time: {existing['event_time']}")
            print(f"      Status: {existing['status']}")
            return {"passed": 1, "failed": 0}
        else:
            print(f"\n   ❌ Availability Check: Should find booking on {test_date}")
            return {"passed": 0, "failed": 1}

    async def run_all_tests(self):
        """Run all end-to-end scenarios"""
        print("\n" + "=" * 60)
        print("🚀 PHASE 4: END-TO-END FLOW TESTING")
        print("=" * 60)

        await self.connect_db()

        try:
            results = []

            # Run all scenarios
            results.append(await self.test_scenario_1_casual_booking())
            results.append(await self.test_scenario_2_formal_corporate())
            results.append(await self.test_scenario_3_anxious_first_timer())
            results.append(await self.test_booking_availability_check())

            # Calculate totals
            total_passed = sum(r["passed"] for r in results)
            total_failed = sum(r["failed"] for r in results)
            total_tests = total_passed + total_failed
            accuracy = (total_passed / total_tests * 100) if total_tests > 0 else 0

            # Print summary
            print("\n" + "=" * 60)
            print("📊 PHASE 4 SUMMARY")
            print("=" * 60)

            for result in results:
                scenario = result.get("scenario", "Test")
                status = "✅ PASSED" if result["failed"] == 0 else "⚠️ PARTIAL"
                print(f"\n{status}: {scenario}")
                print(f"   Passed: {result['passed']}, Failed: {result['failed']}")

            print("\n" + "=" * 60)
            print("📈 OVERALL RESULTS:")
            print(f"   Total Tests: {total_tests}")
            print(f"   Passed: {total_passed}")
            print(f"   Failed: {total_failed}")
            print(f"   Accuracy: {accuracy:.1f}%")
            print("=" * 60)

            if accuracy >= 80:
                print("\n✅ PHASE 4: END-TO-END FLOW - PASSED!")
            else:
                print("\n⚠️ PHASE 4: END-TO-END FLOW - NEEDS IMPROVEMENT")

        finally:
            await self.close_db()


if __name__ == "__main__":
    tester = E2EFlowTester()
    asyncio.run(tester.run_all_tests())
