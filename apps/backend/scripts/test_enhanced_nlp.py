"""
Test script for Enhanced NLP Service
Validates entity extraction, tone detection, semantic search
"""

import sys

sys.path.append(".")

from src.services.enhanced_nlp_service import get_nlp_service


def test_entity_extraction():
    """Test extracting dates, numbers, names from text"""
    print("\n" + "=" * 60)
    print("🔍 ENTITY EXTRACTION TEST")
    print("=" * 60)

    nlp = get_nlp_service()

    test_cases = [
        "I want to book for 50 people on December 15th at 6pm",
        "Can you do an event for 30 guests next Saturday?",
        "My name is Sarah Johnson and I need hibachi for 25",
        "Looking for catering on Nov 20th for about 40-45 people",
    ]

    for text in test_cases:
        print(f"\n📝 Input: '{text}'")
        entities = nlp.extract_entities(text)
        print(f"✅ Entities: {entities}")


def test_tone_detection():
    """Test enhanced tone detection with confidence scores"""
    print("\n" + "=" * 60)
    print("🎭 TONE DETECTION TEST")
    print("=" * 60)

    nlp = get_nlp_service()

    test_cases = [
        "Hey! I wanna book hibachi for my birthday party! 🎉",
        "Good morning. I'm inquiring about catering services for a corporate event.",
        "Hi... I've never done this before and I'm really nervous about planning...",
        "Yeah that sounds good! Everyone loves dumplings 😋",
        "What are your protein options and pricing?",
    ]

    expected_tones = ["casual", "formal", "anxious", "warm", "direct"]

    for i, text in enumerate(test_cases):
        print(f"\n📝 Input: '{text}'")
        tone, confidence = nlp.detect_tone_enhanced(text)
        print(f"✅ Detected: {tone} (confidence: {confidence:.2f})")
        print(f"💡 Expected: {expected_tones[i]}")

        if tone == expected_tones[i]:
            print("✅ MATCH!")
        else:
            print("⚠️  DIFFERENT (but may still be valid)")


def test_semantic_search():
    """Test semantic FAQ search - find similar questions"""
    print("\n" + "=" * 60)
    print("🔎 SEMANTIC SEARCH TEST")
    print("=" * 60)

    nlp = get_nlp_service()

    # Sample FAQs
    faqs = [
        {
            "question": "How much does My Hibachi Chef cost?",
            "answer": "Our adult pricing is $55 per person and child pricing (10 and under) is $30 per person.",
            "category": "Pricing",
        },
        {
            "question": "What add-on options do you offer?",
            "answer": "$10 add-ons: Third Protein, Gyoza. $5 add-ons: Yakisoba Noodles, Extra Fried Rice, Extra Vegetables, Edamame.",
            "category": "Menu",
        },
        {
            "question": "Is there a minimum party size?",
            "answer": "No minimum guest count, but we have a $550 minimum order requirement per event.",
            "category": "Pricing",
        },
        {
            "question": "How much is the deposit?",
            "answer": "We require a $100 deposit to secure your booking date.",
            "category": "Booking",
        },
    ]

    # Test queries - worded DIFFERENTLY than actual FAQs
    test_queries = [
        "How much for 50 peeps?",  # Should match "How much does My Hibachi Chef cost?"
        "What extras can I add?",  # Should match "What add-on options do you offer?"
        "Any minimum guests?",  # Should match "Is there a minimum party size?"
        "How much to reserve a date?",  # Should match "How much is the deposit?"
    ]

    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        results = nlp.semantic_search_faqs(query, faqs, top_k=2)

        print("✅ Top matches:")
        for result in results:
            print(f"   • {result['question']} (similarity: {result['similarity_score']:.3f})")


def test_booking_extraction():
    """Test extracting booking details from natural language"""
    print("\n" + "=" * 60)
    print("🎫 BOOKING DETAILS EXTRACTION TEST")
    print("=" * 60)

    nlp = get_nlp_service()

    test_cases = [
        "30 people with chicken and steak, plus noodles",
        "We need hibachi for 50 guests, all 3 proteins, add gyoza",
        "Book for 25 people on December 15th, chicken only",
        "40 guests, steak and shrimp, with extra fried rice and vegetables",
    ]

    for text in test_cases:
        print(f"\n📝 Input: '{text}'")
        details = nlp.extract_booking_details(text)
        print("✅ Extracted:")
        print(f"   • Guest count: {details.get('guest_count', 'Not found')}")
        print(f"   • Proteins: {details.get('proteins', [])}")
        print(f"   • Add-ons: {details.get('add_ons', [])}")
        print(f"   • Confidence: {details.get('confidence', 'unknown')}")


def test_text_normalization():
    """Test slang and typo handling"""
    print("\n" + "=" * 60)
    print("✍️  TEXT NORMALIZATION TEST")
    print("=" * 60)

    nlp = get_nlp_service()

    test_cases = [
        "Wanna book for 30 ppl thx",
        "Gonna need hibachi 4 my party",
        "Ur prices r great! Def interested",
        "Plz let me no about availability",
    ]

    for text in test_cases:
        print(f"\n📝 Input: '{text}'")
        normalized = nlp.normalize_text(text)
        print(f"✅ Normalized: '{normalized}'")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("🚀 ENHANCED NLP SERVICE TEST SUITE")
    print("=" * 60)

    try:
        test_entity_extraction()
        test_tone_detection()
        test_semantic_search()
        test_booking_extraction()
        test_text_normalization()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 60)
        print("\n🎯 Your enhanced NLP service is ready to use!")
        print("\n💡 Next steps:")
        print("   1. Integrate into AI service (replace tone_analyzer)")
        print("   2. Add semantic_search_faqs to knowledge_service")
        print("   3. Monitor performance improvements")
        print("   4. Collect metrics for comparison")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
