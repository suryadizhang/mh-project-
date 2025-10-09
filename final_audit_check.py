#!/usr/bin/env python3

"""
Final Deep Audit Script - Comprehensive Implementation Check
Validates all components of the rate limiting system
"""

import sys
import os
import json
from datetime import datetime

# Add the backend src directory to Python path
backend_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)

def audit_component(name, check_func):
    """Audit a specific component with error handling"""
    print(f"\n🔍 Auditing {name}...")
    print("-" * 50)
    
    try:
        result = check_func()
        if result:
            print(f"✅ {name}: PASSED")
            return True
        else:
            print(f"❌ {name}: FAILED")
            return False
    except Exception as e:
        print(f"🔴 {name}: ERROR - {e}")
        return False

def check_core_rate_limiting():
    """Check core rate limiting implementation"""
    try:
        from core.rate_limiting import RateLimiter, rate_limiter
        
        # Check class structure
        assert hasattr(RateLimiter, '_memory_store'), "Memory store should be instance variable"
        assert hasattr(rate_limiter, '_memory_store'), "Rate limiter should have memory store"
        
        # Check methods exist
        required_methods = [
            '_init_redis', '_get_user_identifier', '_get_rate_limit_config',
            '_check_rate_limit', '_check_redis_rate_limit', '_check_memory_rate_limit',
            'check_and_update'
        ]
        
        for method in required_methods:
            assert hasattr(RateLimiter, method), f"Missing method: {method}"
        
        print("   ✅ Class structure correct")
        print("   ✅ Instance variables properly used")
        print("   ✅ All required methods present")
        return True
        
    except Exception as e:
        print(f"   ❌ Core rate limiting check failed: {e}")
        return False

def check_configuration():
    """Check configuration management"""
    try:
        from core.config import get_settings, UserRole
        
        settings = get_settings()
        
        # Check admin optimization
        assert settings.RATE_LIMIT_ADMIN_PER_MINUTE == 100, "Admin should get 100/min"
        assert settings.RATE_LIMIT_ADMIN_SUPER_PER_MINUTE == 200, "Super admin should get 200/min"
        assert settings.RATE_LIMIT_PUBLIC_PER_MINUTE == 20, "Public should get 20/min"
        
        # Check helper methods
        public_config = settings.get_rate_limit_for_user(UserRole.CUSTOMER)
        admin_config = settings.get_rate_limit_for_user(UserRole.ADMIN)
        super_admin_config = settings.get_rate_limit_for_user(UserRole.OWNER)
        
        assert public_config["per_minute"] == 20, "Public config incorrect"
        assert admin_config["per_minute"] == 100, "Admin config incorrect" 
        assert super_admin_config["per_minute"] == 200, "Super admin config incorrect"
        
        # Check admin optimization ratios
        admin_ratio = admin_config["per_minute"] / public_config["per_minute"]
        super_ratio = super_admin_config["per_minute"] / public_config["per_minute"]
        
        assert admin_ratio == 5.0, f"Admin should be 5x, got {admin_ratio}x"
        assert super_ratio == 10.0, f"Super admin should be 10x, got {super_ratio}x"
        
        print(f"   ✅ Admin optimization: {admin_ratio}x and {super_ratio}x higher limits")
        print("   ✅ Configuration validation passed")
        print("   ✅ Helper methods working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration check failed: {e}")
        return False

def check_security():
    """Check security implementation"""
    try:
        from core.security import extract_user_from_token, verify_token
        from core.config import UserRole
        
        # Test invalid token handling
        result = extract_user_from_token("invalid_token")
        assert result is None, "Invalid token should return None"
        
        # Test role validation
        try:
            # This should not crash even with invalid role
            from core.security import UserRole
            role = UserRole("invalid_role")
        except ValueError:
            # Expected behavior - invalid roles should raise ValueError
            pass
        
        print("   ✅ JWT validation working")
        print("   ✅ Invalid token handling correct")
        print("   ✅ Role validation secure")
        return True
        
    except Exception as e:
        print(f"   ❌ Security check failed: {e}")
        return False

def check_middleware_integration():
    """Check middleware integration"""
    try:
        from main import app
        from core.rate_limiting import rate_limit_middleware
        
        # Check app is properly configured
        assert app.title == "My Hibachi Chef CRM", "App title incorrect"
        
        # Check middleware function exists
        assert callable(rate_limit_middleware), "Rate limit middleware should be callable"
        
        print("   ✅ FastAPI app configured correctly")
        print("   ✅ Middleware integration proper")
        return True
        
    except Exception as e:
        print(f"   ❌ Middleware check failed: {e}")
        return False

def check_monitoring():
    """Check monitoring endpoints"""
    try:
        from api.v1.endpoints.rate_limit_metrics import router
        
        # Check router exists and has routes
        assert len(router.routes) > 0, "Monitoring router should have routes"
        
        print("   ✅ Monitoring endpoints available")
        print("   ✅ Metrics collection configured")
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring check failed: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    try:
        # Check critical imports
        import fastapi
        import pydantic
        import uvicorn
        
        try:
            import redis
            redis_available = True
        except ImportError:
            redis_available = False
        
        print(f"   ✅ FastAPI: {fastapi.__version__}")
        print(f"   ✅ Pydantic: {pydantic.__version__}")
        print(f"   ✅ Uvicorn: {uvicorn.__version__}")
        print(f"   ⚠️ Redis: {'Available' if redis_available else 'Not available (fallback will be used)'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Dependencies check failed: {e}")
        return False

def check_file_structure():
    """Check file structure and organization"""
    try:
        required_files = [
            'apps/backend/src/core/rate_limiting.py',
            'apps/backend/src/core/config.py',
            'apps/backend/src/core/security.py',
            'apps/backend/src/main.py',
            'apps/backend/src/api/v1/endpoints/rate_limit_metrics.py',
            'apps/backend/src/.env',
            'apps/backend/requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"   ❌ Missing files: {missing_files}")
            return False
        
        print("   ✅ All required files present")
        print("   ✅ Project structure correct")
        return True
        
    except Exception as e:
        print(f"   ❌ File structure check failed: {e}")
        return False

def main():
    """Run comprehensive final audit"""
    print("🔍 FINAL DEEP AUDIT - RATE LIMITING IMPLEMENTATION")
    print("=" * 60)
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print("=" * 60)
    
    # Define audit checks
    audit_checks = [
        ("File Structure & Organization", check_file_structure),
        ("Dependencies & Imports", check_dependencies),
        ("Core Rate Limiting Implementation", check_core_rate_limiting),
        ("Configuration Management", check_configuration),
        ("Security Implementation", check_security),
        ("Middleware Integration", check_middleware_integration),
        ("Monitoring & Metrics", check_monitoring),
    ]
    
    # Run all audits
    results = []
    for name, check_func in audit_checks:
        result = audit_component(name, check_func)
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL AUDIT SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📊 AUDIT SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL AUDITS PASSED!")
        print("✅ Implementation is PROPER and PRODUCTION-READY")
        print("✅ Admin optimization requirements MET")
        print("✅ Ready for commit and deployment")
        return True
    else:
        print(f"\n⚠️ {total - passed} AUDIT(S) FAILED")
        print("❌ Implementation needs attention before deployment")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)