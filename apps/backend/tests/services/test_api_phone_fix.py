"""
Test with properly formatted phone
"""
import requests

url = "http://localhost:8000/api/v1/public/leads"

# Phone needs to match pattern: ^\+?1?\d{10,15}$
payload = {
    "name": "John Doe",
    "email": "john@test.com",
    "phone": "+15551234567",  # With +1 prefix
    "guest_count": 25,
    "event_date": "2025-11-15",
    "budget": "$1000-2000",
    "message": "Wedding reception",
    "location": "Beverly Hills",
    "source": "website"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Lead ID: {data.get('lead_id')}")
    else:
        print(f"\n❌ Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            pass
            
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
