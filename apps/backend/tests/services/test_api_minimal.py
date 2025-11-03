"""
Minimal API test
"""
import requests
import json

url = "http://localhost:8000/api/v1/public/leads"

payload = {
    "name": "John Doe",
    "email": "john@test.com",
    "phone": "5551234567",
    "guest_count": 25,
    "event_date": "2025-11-15",
    "budget": "$1000-2000",
    "message": "Wedding reception",
    "location": "Beverly Hills",
    "source": "website"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Lead ID: {data.get('lead_id')}")
        print(f"Message: {data.get('message')}")
    else:
        print(f"\n❌ FAILED!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
