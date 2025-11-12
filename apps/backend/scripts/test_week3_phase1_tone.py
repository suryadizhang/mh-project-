"""
Week 3 Phase 1: Tone Detection Testing
Tests ToneAnalyzer with 5 different customer tones
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 60)
print("🎭 WEEK 3 PHASE 1: TONE DETECTION TESTING")
print("=" * 60 + "\n")

# Test messages for each tone
test_messages = {
    "formal": {
        "message": "Good afternoon. I would like to inquire about your catering services for a corporate event with approximately 50 attendees. Could you please provide detailed pricing information and availability?",
        "expected_tone": "formal",
        "expected_keywords": ["Good afternoon", "I would be pleased", "professional", "detailed"],
    },
    "casual": {
        "message": "Hey! How much for hibachi for like 50 people? Trying to throw a party 🎉",
        "expected_tone": "casual",
        "expected_keywords": ["Hey", "awesome", "🔥", "got"],
    },
    "direct": {
        "message": "Price for 50 people?",
        "expected_tone": "direct",
        "expected_keywords": ["•", "50 guests", "$2,750", "$55"],
    },
    "warm": {
        "message": "Hi! I'm planning my daughter's sweet 16 and I'm SO excited! This will be such a special day for her!",
        "expected_tone": "warm",
        "expected_keywords": ["exciting", "love", "special", "💕", "✨"],
    },
    "anxious": {
        "message": "Um, hi... I need catering for 50 people but I've never done this before and I'm stressed... I don't know what to do.",
        "expected_tone": "anxious",
        "expected_keywords": ["understand", "step-by-step", "✅", "don't stress"],
    },
}


async def test_tone_detection():
    """Test tone detection with ToneAnalyzer"""

    try:
        from src.api.ai.services.tone_analyzer import ToneAnalyzer

        analyzer = ToneAnalyzer()
        print("✅ ToneAnalyzer initialized\n")

        results = {}
        total_tests = len(test_messages)
        passed_tests = 0

        for tone_name, test_case in test_messages.items():
            print(f"📝 Testing {tone_name.upper()} tone...")
            print(f"   Message: \"{test_case['message'][:60]}...\"")

            try:
                # Analyze tone
                result = analyzer.detect_tone(test_case["message"])

                detected_tone = result.detected_tone.value
                confidence = result.confidence

                # Check if tone matches
                tone_correct = detected_tone.lower() == test_case["expected_tone"].lower()
                confidence_ok = confidence >= 0.70

                if tone_correct and confidence_ok:
                    print(
                        f"   ✅ PASS: Detected {detected_tone} (confidence: {confidence * 100:.1f}%)"
                    )
                    passed_tests += 1
                    results[tone_name] = "PASS"
                elif tone_correct and not confidence_ok:
                    print(
                        f"   ⚠️  PARTIAL: Detected {detected_tone} but low confidence ({confidence * 100:.1f}%)"
                    )
                    results[tone_name] = "PARTIAL"
                else:
                    print(
                        f"   ❌ FAIL: Detected {detected_tone} (expected {test_case['expected_tone']}), confidence: {confidence * 100:.1f}%"
                    )
                    results[tone_name] = "FAIL"

            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                results[tone_name] = "ERROR"

            print()

        # Summary
        print("=" * 60)
        print("📊 TONE DETECTION TEST SUMMARY")
        print("=" * 60)
        print(f"\nTests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print("\nResults by tone:")
        for tone_name, result in results.items():
            emoji = "✅" if result == "PASS" else "⚠️" if result == "PARTIAL" else "❌"
            print(f"  {emoji} {tone_name.capitalize()}: {result}")

        print("\n" + "=" * 60)

        if passed_tests >= total_tests * 0.85:  # 85% pass rate
            print("✅ PHASE 1: TONE DETECTION - PASSED!")
            print(f"Accuracy: {passed_tests/total_tests*100:.1f}% (Target: 85%+)")
            return True
        else:
            print("❌ PHASE 1: TONE DETECTION - NEEDS IMPROVEMENT")
            print(f"Accuracy: {passed_tests/total_tests*100:.1f}% (Target: 85%+)")
            return False

    except ImportError as e:
        print(f"❌ Could not import ToneAnalyzer: {e}")
        print("\nMake sure you're running from the backend directory:")
        print("  cd apps/backend")
        print("  python scripts/test_week3_phase1_tone.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_tone_detection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
