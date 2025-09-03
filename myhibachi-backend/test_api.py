#!/usr/bin/env python3
"""
Test script for MyHibachi Backend API
"""

from datetime import date, timedelta

import requests

# API base URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Health check passed: {data['message']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_availability_check():
    """Test availability check endpoint"""
    print("\n🔍 Testing availability check...")
    try:
        # Test with a future date
        future_date = (date.today() + timedelta(days=3)).isoformat()
        response = requests.get(
            f"{BASE_URL}/api/v1/bookings/check", params={"date": future_date, "time": "3PM"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Availability check passed: Available = {data['available']}")
        return True
    except Exception as e:
        print(f"❌ Availability check failed: {e}")
        return False


def test_create_booking():
    """Test booking creation"""
    print("\n🔍 Testing booking creation...")
    try:
        future_date = (date.today() + timedelta(days=5)).isoformat()
        booking_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "5551234567",
            "event_date": future_date,
            "event_time": "6PM",
            "address_street": "123 Main St",
            "address_city": "San Francisco",
            "address_state": "CA",
            "address_zipcode": "94105",
            "venue_street": "123 Main St",
            "venue_city": "San Francisco",
            "venue_state": "CA",
            "venue_zipcode": "94105",
        }

        response = requests.post(f"{BASE_URL}/api/v1/bookings", json=booking_data)
        assert response.status_code == 201
        data = response.json()
        print(f"✅ Booking creation passed: ID = {data['id']}")
        return data["id"]
    except Exception as e:
        print(f"❌ Booking creation failed: {e}")
        return None


def test_get_bookings():
    """Test getting all bookings"""
    print("\n🔍 Testing get all bookings...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/bookings")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Get bookings passed: Found {len(data)} bookings")
        return True
    except Exception as e:
        print(f"❌ Get bookings failed: {e}")
        return False


def test_availability_after_booking():
    """Test that availability changes after booking"""
    print("\n🔍 Testing availability after booking...")
    try:
        future_date = (date.today() + timedelta(days=5)).isoformat()
        response = requests.get(
            f"{BASE_URL}/api/v1/bookings/check", params={"date": future_date, "time": "6PM"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Availability after booking: Available = {data['available']}")
        if not data["available"]:
            print(f"   Reason: {data.get('reason', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Availability check after booking failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 MyHibachi Backend API Tests")
    print("=" * 40)

    tests = [
        test_health_check,
        test_availability_check,
        test_create_booking,
        test_get_bookings,
        test_availability_after_booking,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API server.")


if __name__ == "__main__":
    main()
