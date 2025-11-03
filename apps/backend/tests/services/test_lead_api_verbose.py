"""
Test lead API with detailed error reporting
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
    "source": "website",
    "email_consent": True
}

headers = {
    "Content-Type": "application/json"
}

try:
    print("Testing lead creation...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(response.text)
    
    if response.status_code == 201:
        print("\n✅ Lead created successfully!")
        result = response.json()
        print(f"Lead ID: {result.get('lead_id')}")
    else:
        print(f"\n❌ Error creating lead")
        try:
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Raw error: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend server. Is it running on port 8000?")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
