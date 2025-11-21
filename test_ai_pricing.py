#!/usr/bin/env python3
"""
Quick test script to verify AI pricing and tone
"""
import json

import requests

API_BASE = "http://localhost:8000"


def test_ai_inquiry(message: str):
    """Test AI multi-channel inquiry endpoint"""
    url = f"{API_BASE}/api/v1/ai/multi-channel/inquiries/process"

    payload = {
        "message": message,
        "channel": "sms",
        "customer_metadata": {"from_number": "+19167408768"},
    }

    print(f"\n{'='*80}")
    print(f"TESTING: {message}")
    print(f"{'='*80}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ AI RESPONSE:")
            print(f"{data.get('response', 'No response field')}")
            print(
                f"\nMetadata: {json.dumps(data.get('metadata', {}), indent=2)}"
            )
        else:
            print(f"\n❌ ERROR: {response.text}")

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")


if __name__ == "__main__":
    print("🧪 Testing AI Booking Assistant")
    print("=" * 80)

    # Test 1: Basic pricing inquiry
    test_ai_inquiry("How much for 20 people?")

    # Test 2: Children pricing
    test_ai_inquiry("How much for 10 adults and 5 kids?")

    # Test 3: Complex inquiry
    test_ai_inquiry(
        "I need hibachi for 30 people with shrimp and steak. What's the price?"
    )

    print("\n" + "=" * 80)
    print("✅ Tests complete!")
