#!/usr/bin/env python3

"""
Simple Rate Limiting Test
Tests admin vs public rate limits
"""

import requests
import time

API_BASE = "http://127.0.0.1:8001"

def test_single_request(endpoint="/v1/customers", headers=None):
    """Test a single request and show rate limit headers"""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=headers or {}, timeout=5)
        print(f"Status: {r.status_code}")
        
        # Show rate limit headers
        rate_headers = {k: v for k, v in r.headers.items() if k.startswith('X-RateLimit')}
        print(f"Rate limit headers: {rate_headers}")
        
        return r.status_code, rate_headers
    except Exception as e:
        print(f"Error: {e}")
        return None, {}

def test_multiple_requests(endpoint="/v1/customers", headers=None, count=25):
    """Test multiple requests to trigger rate limiting"""
    print(f"\n🧪 Testing {count} requests to {endpoint}")
    print(f"Headers: {headers or 'None'}")
    
    for i in range(1, count + 1):
        try:
            r = requests.get(f"{API_BASE}{endpoint}", headers=headers or {}, timeout=2)
            
            if r.status_code == 429:
                print(f"  ❌ Rate limited at request {i}")
                return i
            elif r.status_code in [200, 404]:  # 404 is OK for test endpoints
                if i <= 5 or i % 5 == 0:
                    tier = r.headers.get('X-RateLimit-Tier', 'unknown')
                    remaining = r.headers.get('X-RateLimit-Remaining-Minute', 'unknown')
                    print(f"  ✅ Request {i}: {r.status_code} (Tier: {tier}, Remaining: {remaining})")
            else:
                print(f"  ⚠️ Request {i}: Status {r.status_code}")
                
        except Exception as e:
            print(f"  ❌ Request {i}: Error {str(e)}")
            break
            
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    print(f"  ✅ All {count} requests successful - no rate limit hit")
    return None

if __name__ == "__main__":
    print("🔒 SIMPLE RATE LIMITING TEST")
    print("=" * 40)
    
    # Test health endpoint (should not be rate limited)
    print("\n1️⃣ Testing Health Endpoint")
    status, headers = test_single_request("/health")
    
    if status != 200:
        print("❌ Server not responding properly")
        exit(1)
    
    # Test public rate limits
    print("\n2️⃣ Testing Public Rate Limits (should hit limit ~20 requests)")
    public_limit = test_multiple_requests("/v1/customers", None, 25)
    
    # Test admin rate limits
    print("\n3️⃣ Testing Admin Rate Limits (should hit limit ~100 requests)")
    admin_headers = {"Authorization": "Bearer admin_token"}
    admin_limit = test_multiple_requests("/v1/customers", admin_headers, 25)  # Just test 25 for now
    
    # Test super admin rate limits
    print("\n4️⃣ Testing Super Admin Rate Limits (should hit limit ~200 requests)")
    super_admin_headers = {"Authorization": "Bearer super_admin_token"}
    super_admin_limit = test_multiple_requests("/v1/customers", super_admin_headers, 25)  # Just test 25 for now
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    print(f"Public user rate limited at: {public_limit or 'Not reached (>25)'}")
    print(f"Admin user rate limited at: {admin_limit or 'Not reached (>25)'}")
    print(f"Super admin rate limited at: {super_admin_limit or 'Not reached (>25)'}")
    print()
    print("Expected:")
    print("  - Public: ~20 requests/minute")
    print("  - Admin: ~100 requests/minute") 
    print("  - Super Admin: ~200 requests/minute")
    print("\n✅ Rate limiting test completed!")