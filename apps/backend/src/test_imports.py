from core.config import Settings
from core.rate_limiting import RateLimiter  
import core.security as security
from core.database import get_db

def test_imports():
    print("=== Testing Core Module Imports ===")
    
    try:
        settings = Settings()
        print("✅ Settings import successful")
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False
        
    try:
        rate_limiter = RateLimiter()
        print("✅ RateLimiter import successful")
    except Exception as e:
        print(f"❌ RateLimiter error: {e}")
        return False
        
    try:
        # Test security functions
        token = security.create_access_token({"sub": "test"})
        print("✅ Security module import successful")
    except Exception as e:
        print(f"❌ Security module error: {e}")
        return False
        
    try:
        # Test the database dependency generator
        db_gen = get_db()
        print("✅ Database dependency import successful")
    except Exception as e:
        print(f"❌ Database dependency error: {e}")
        return False
    
    return True

def test_api_endpoints():
    print("\n=== Testing API Endpoint Imports ===")
    
    try:
        from api.v1.endpoints.auth import router as auth_router
        print("✅ Auth router import successful")
    except Exception as e:
        print(f"❌ Auth router error: {e}")
        return False
        
    try:
        from api.v1.endpoints.bookings import router as bookings_router
        print("✅ Bookings router import successful")
    except Exception as e:
        print(f"❌ Bookings router error: {e}")
        return False
        
    try:
        from api.v1.endpoints.ai.chat import router as ai_router
        print("✅ AI chat router import successful")
    except Exception as e:
        print(f"❌ AI chat router error: {e}")
        return False
    
    return True

def test_main_app():
    print("\n=== Testing Main Application ===")
    
    try:
        from main import app
        print("✅ Main FastAPI app import successful")
        
        # Check if we can access the app info
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        return True
    except Exception as e:
        print(f"❌ Main app error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== My Hibachi Chef CRM - Module Import Test ===\n")
    
    core_success = test_imports()
    api_success = test_api_endpoints()
    app_success = test_main_app()
    
    print("\n=== Summary ===")
    print(f"Core modules: {'✅ PASS' if core_success else '❌ FAIL'}")
    print(f"API endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Main application: {'✅ PASS' if app_success else '❌ FAIL'}")
    
    if core_success and api_success and app_success:
        print("\n🎉 All imports successful! The unified API is ready.")
        print("To start the server: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Some imports failed. Check the error messages above.")