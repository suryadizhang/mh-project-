"""
Test script for lead generation API
Tests the public lead capture endpoint
"""
import requests
import json
from datetime import date

# Test data
lead_data = {
    "name": "John Test",
    "email": "john.test@example.com",
    "phone": "5551234567",
    "event_date": "2025-12-15",
    "guest_count": 50,
    "budget": "$2000-3000",
    "location": "Los Angeles, CA",
    "message": "Looking for hibachi catering for company holiday party",
    "source": "website",
    "email_consent": True,
    "sms_consent": True
}

print("🧪 Testing Lead Generation API...")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get("http://localhost:8000/api/v1/public/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed")
except Exception as e:
    print(f"   ❌ Health check failed: {e}")

# Test 2: Create lead
print("\n2. Testing lead creation...")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/public/leads",
        json=lead_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 201:
        print("   ✅ Lead created successfully!")
        lead_id = result.get("lead_id")
        print(f"   📋 Lead ID: {lead_id}")
    else:
        print(f"   ❌ Lead creation failed")
except Exception as e:
    print(f"   ❌ Lead creation error: {e}")

# Test 3: Invalid data (missing required fields)
print("\n3. Testing validation (missing email and phone)...")
try:
    invalid_data = {
        "name": "Invalid Test",
        "source": "website"
    }
    response = requests.post(
        "http://localhost:8000/api/v1/public/leads",
        json=invalid_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print("   ✅ Validation working correctly")
    else:
        print(f"   ⚠️ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Validation test error: {e}")

print("\n" + "=" * 60)
print("✅ Testing complete!")
