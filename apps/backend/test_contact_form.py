"""
Test Contact Form API
Quick test script to verify contact form endpoint works
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_contact_form_submission():
    """Test successful contact form submission"""
    print("🧪 Testing contact form submission...")
    
    response = client.post(
        "/api/v1/contact/submit",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "(916) 555-1234",
            "subject": "booking",
            "message": "I would like to book a hibachi event for 20 people.",
            "honeypot": ""  # Empty (human)
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "submission_id" in data
    
    print("✅ Contact form submission test passed!")

def test_honeypot_bot_detection():
    """Test that honeypot field catches bots"""
    print("\n🧪 Testing honeypot bot detection...")
    
    response = client.post(
        "/api/v1/contact/submit",
        json={
            "name": "Bot",
            "email": "bot@spam.com",
            "phone": "1234567890",
            "subject": "other",
            "message": "Spam message",
            "honeypot": "I am a bot"  # Bot filled this
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should still return 200 OK (fake success for bots)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    
    print("✅ Honeypot bot detection test passed!")

def test_validation_errors():
    """Test validation catches bad input"""
    print("\n🧪 Testing validation errors...")
    
    # Test short message
    response = client.post(
        "/api/v1/contact/submit",
        json={
            "name": "John",
            "email": "john@example.com",
            "phone": "9165551234",
            "subject": "booking",
            "message": "Short",  # Too short (< 10 chars)
            "honeypot": ""
        }
    )
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422  # Validation error
    
    print("✅ Validation error test passed!")

def test_health_endpoint():
    """Test health check endpoint"""
    print("\n🧪 Testing health endpoint...")
    
    response = client.get("/api/v1/contact/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "contact_form"
    assert data["status"] == "operational"
    
    print("✅ Health endpoint test passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 Contact Form API Tests")
    print("=" * 60)
    
    try:
        test_health_endpoint()
        test_contact_form_submission()
        test_honeypot_bot_detection()
        test_validation_errors()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
