"""
Simple HTTP test of the Lead Generation API
Tests POST /api/v1/public/leads endpoint
"""
import json

# Test data for quote request
quote_data = {
    "name": "Test User - John Doe",
    "email": "john.doe.test@example.com",
    "phone": "+15551234567",
    "event_date": "2025-11-15",
    "guest_count": 12,
    "budget": "$1,000 - $2,000",
    "location": "Sacramento, CA",
    "message": "Looking for hibachi catering for anniversary party",
    "source": "quote",
    "email_consent": True,
    "sms_consent": False,
    "honeypot": ""
}

print("🧪 Lead Generation API Test")
print("=" * 60)
print("\n📝 Test Data:")
print(json.dumps(quote_data, indent=2))
print("\n" + "=" * 60)
print("\n📌 To test the API:")
print("\n1. Start the backend server:")
print("   cd C:\\Users\\surya\\projects\\MH webapps\\apps\\backend\\src")
print("   python -m uvicorn main:app --reload --port 8000")
print("\n2. Run this curl command in PowerShell:")
print("""
$body = @{
    name = "Test User - John Doe"
    email = "john.doe.test@example.com"
    phone = "+15551234567"
    event_date = "2025-11-15"
    guest_count = 12
    budget = "$1,000 - $2,000"
    location = "Sacramento, CA"
    message = "Looking for hibachi catering for anniversary party"
    source = "quote"
    email_consent = $true
    sms_consent = $false
    honeypot = ""
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/public/leads" -Method POST -Body $body -ContentType "application/json"
""")

print("\n3. Expected Response:")
print("""
{
  "success": true,
  "message": "Thank you! We've received your request and will contact you shortly.",
  "lead_id": "uuid-here"
}
""")

print("\n4. Verify in database:")
print("""
cd C:\\Users\\surya\\projects\\MH webapps\\apps\\backend
python check_db_schema.py
""")

print("=" * 60)
print("✅ Copy the commands above to test the API!")
print("=" * 60)
