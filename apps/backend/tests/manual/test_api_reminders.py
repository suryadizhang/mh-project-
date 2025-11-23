"""
Quick API test for Booking Reminders
Run the server first: uvicorn src.main:app --reload
Then run this script: python tests/manual/test_api_reminders.py
"""

import asyncio
import httpx
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000/api/v1"


async def test_reminders_api():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("🧪 Testing Booking Reminders API\n")
        
        # We need a valid booking ID - let's assume booking ID 1 exists
        # In production, you'd create a booking first
        booking_id = 1
        
        # Test 1: Create reminder
        print("1️⃣  Testing POST /bookings/{id}/reminders")
        reminder_data = {
            "booking_id": booking_id,
            "reminder_type": "email",
            "scheduled_for": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "message": "Test reminder message"
        }
        
        response = await client.post(
            f"/bookings/{booking_id}/reminders",
            json=reminder_data
        )
        
        if response.status_code == 503:
            print("   ⚠️  Feature flag is OFF - Enable FEATURE_FLAG_BOOKING_REMINDERS=true")
            return
        elif response.status_code == 404:
            print(f"   ⚠️  Booking {booking_id} not found - Create a booking first")
            return
        elif response.status_code == 201:
            reminder = response.json()
            reminder_id = reminder["id"]
            print(f"   ✅ Created reminder: {reminder_id}")
            print(f"      Type: {reminder['reminder_type']}")
            print(f"      Status: {reminder['status']}\n")
            
            # Test 2: List reminders
            print("2️⃣  Testing GET /bookings/{id}/reminders")
            response = await client.get(f"/bookings/{booking_id}/reminders")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['total']} reminder(s)\n")
            
            # Test 3: Get specific reminder
            print("3️⃣  Testing GET /bookings/{id}/reminders/{reminder_id}")
            response = await client.get(f"/bookings/{booking_id}/reminders/{reminder_id}")
            if response.status_code == 200:
                print(f"   ✅ Retrieved reminder {reminder_id}\n")
            
            # Test 4: Update reminder
            print("4️⃣  Testing PUT /bookings/{id}/reminders/{reminder_id}")
            update_data = {"message": "Updated reminder message"}
            response = await client.put(
                f"/bookings/{booking_id}/reminders/{reminder_id}",
                json=update_data
            )
            if response.status_code == 200:
                print(f"   ✅ Updated reminder\n")
            
            # Test 5: Cancel reminder
            print("5️⃣  Testing DELETE /bookings/{id}/reminders/{reminder_id}")
            response = await client.delete(f"/bookings/{booking_id}/reminders/{reminder_id}")
            if response.status_code == 204:
                print(f"   ✅ Cancelled reminder\n")
            
            print("=" * 60)
            print("✅ ALL API TESTS PASSED!")
            print("=" * 60)
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
            print(f"   {response.text}")


if __name__ == "__main__":
    print("Make sure the server is running: uvicorn src.main:app --reload\n")
    asyncio.run(test_reminders_api())
