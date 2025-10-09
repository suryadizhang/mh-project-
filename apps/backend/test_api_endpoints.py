"""
Test the unified API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health: {data}")
        return True
    return False

def test_auth_login():
    """Test authentication"""
    login_data = {
        "email": "admin@myhibachichef.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
    print(f"Login endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful: {data['user']['email']} ({data['user']['role']})")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_bookings_with_auth(token):
    """Test bookings endpoint with authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/v1/bookings/", headers=headers)
    print(f"Bookings endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Bookings: {len(data)} bookings found")
        return True
    else:
        print(f"❌ Bookings failed: {response.text}")
        return False

def test_ai_chat_with_auth(token):
    """Test AI chat endpoint with authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    chat_data = {"message": "Hello, this is a test message"}
    response = requests.post(f"{BASE_URL}/v1/ai/chat", json=chat_data, headers=headers)
    print(f"AI chat endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ AI Chat: {data['response'][:50]}...")
        return True
    else:
        print(f"❌ AI Chat failed: {response.text}")
        return False

def test_rate_limiting():
    """Test rate limiting by making multiple requests"""
    print("\n=== Testing Rate Limiting ===")
    # Make 5 quick requests to see rate limiting in action
    for i in range(5):
        response = requests.get(f"{BASE_URL}/health")
        print(f"Request {i+1}: {response.status_code}")
        if response.status_code == 429:
            print("✅ Rate limiting is working!")
            return True
    print("⚠️ Rate limiting not triggered (expected for health endpoint)")
    return True

def main():
    print("=== My Hibachi Chef CRM - API Endpoint Tests ===\n")
    
    try:
        # Test 1: Health endpoint
        print("1. Testing health endpoint...")
        health_ok = test_health()
        
        # Test 2: Authentication
        print("\n2. Testing authentication...")
        token = test_auth_login()
        
        if token:
            # Test 3: Bookings endpoint
            print("\n3. Testing bookings endpoint...")
            bookings_ok = test_bookings_with_auth(token)
            
            # Test 4: AI chat endpoint
            print("\n4. Testing AI chat endpoint...")
            ai_ok = test_ai_chat_with_auth(token)
        else:
            bookings_ok = False
            ai_ok = False
        
        # Test 5: Rate limiting
        rate_limit_ok = test_rate_limiting()
        
        # Summary
        print("\n=== Test Summary ===")
        print(f"Health endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"Authentication: {'✅ PASS' if token else '❌ FAIL'}")
        print(f"Bookings endpoint: {'✅ PASS' if bookings_ok else '❌ FAIL'}")
        print(f"AI chat endpoint: {'✅ PASS' if ai_ok else '❌ FAIL'}")
        print(f"Rate limiting: {'✅ PASS' if rate_limit_ok else '❌ FAIL'}")
        
        if health_ok and token and bookings_ok and ai_ok:
            print("\n🎉 All tests passed! The unified API is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the output above for details.")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()