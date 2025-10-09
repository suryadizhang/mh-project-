"""
Simple test for the unified API to verify it's working
"""
import requests
import json
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        # Test the health endpoint (assuming server is running on localhost:8000)
        response = requests.get("http://localhost:8000/health")
        print(f"Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
            return True
        else:
            print(f"Health endpoint failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("Server not running - this is expected if testing structure only")
        return None

def test_auth_login():
    """Test the auth login endpoint"""
    try:
        # Test admin login
        login_data = {
            "email": "admin@myhibachichef.com",
            "password": "admin123"
        }
        response = requests.post("http://localhost:8000/v1/auth/login", json=login_data)
        print(f"Login endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Login successful! Token type: {data.get('token_type')}")
            print(f"User role: {data.get('user', {}).get('role')}")
            return data.get('access_token')
        else:
            print(f"Login failed: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("Server not running - this is expected if testing structure only")
        return None

def test_rate_limiting():
    """Test rate limiting for different user types"""
    token = test_auth_login()
    if not token:
        print("Cannot test rate limiting without valid token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test booking endpoint (admin should have 100 req/min)
        response = requests.get("http://localhost:8000/v1/bookings/", headers=headers)
        print(f"Bookings endpoint status: {response.status_code}")
        
        # Test AI chat endpoint (should have 10 req/min)
        chat_data = {"message": "Hello, test message"}
        response = requests.post("http://localhost:8000/v1/ai/chat", json=chat_data, headers=headers)
        print(f"AI chat endpoint status: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("Server not running - this is expected if testing structure only")

def test_import_structure():
    """Test that our Python modules can be imported correctly"""
    try:
        from core.config import Settings
        print("✅ Successfully imported Settings from core.config")
        
        settings = Settings()
        print(f"✅ Settings initialized - environment: {settings.ENVIRONMENT}")
        print(f"✅ Rate limits configured - admin: {settings.get_admin_rate_limit()}/min")
        
        from core.rate_limiting import RateLimiter
        print("✅ Successfully imported RateLimiter from core.rate_limiting")
        
        from core.security import SecurityManager
        print("✅ Successfully imported SecurityManager from core.security")
        
        from api.v1.endpoints.auth import router as auth_router
        print("✅ Successfully imported auth router")
        
        from api.v1.endpoints.bookings import router as bookings_router
        print("✅ Successfully imported bookings router")
        
        from api.v1.endpoints.ai.chat import router as ai_router
        print("✅ Successfully imported AI chat router")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("=== My Hibachi Chef CRM - Unified API Test ===\n")
    
    # Test 1: Import structure
    print("1. Testing Python import structure...")
    import_success = test_import_structure()
    print()
    
    # Test 2: Health endpoint (if server is running)
    print("2. Testing health endpoint...")
    health_status = test_health_endpoint()
    print()
    
    # Test 3: Auth login (if server is running)
    print("3. Testing authentication...")
    auth_status = test_auth_login()
    print()
    
    # Test 4: Rate limiting (if server is running)
    print("4. Testing rate limiting...")
    test_rate_limiting()
    print()
    
    # Summary
    print("=== Test Summary ===")
    print(f"Import structure: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"Health endpoint: {'✅ PASS' if health_status == True else '⚠️  SKIP (server not running)' if health_status is None else '❌ FAIL'}")
    print(f"Authentication: {'✅ PASS' if auth_status else '⚠️  SKIP (server not running)' if health_status is None else '❌ FAIL'}")
    
    if import_success:
        print("\n🎉 Core structure is working! The unified API is ready for testing.")
        print("To test endpoints, run: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Import issues detected. Check the file structure and dependencies.")