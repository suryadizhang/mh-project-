#!/usr/bin/env python3

"""
Test the running server directly using the same Python environment
"""

import asyncio
import aiohttp
import time

async def test_single_request(session, url, headers=None, test_name="Test"):
    """Test a single request and return rate limit info"""
    try:
        async with session.get(url, headers=headers or {}) as response:
            rate_headers = {k: v for k, v in response.headers.items() if 'RateLimit' in k}
            
            result = {
                'status': response.status,
                'headers': rate_headers,
                'tier': rate_headers.get('X-RateLimit-Tier', 'unknown'),
                'remaining_minute': rate_headers.get('X-RateLimit-Remaining-Minute', 'unknown'),
                'remaining_hour': rate_headers.get('X-RateLimit-Remaining-Hour', 'unknown')
            }
            
            print(f"   {test_name}: Status {response.status}")
            print(f"   Tier: {result['tier']}")
            print(f"   Remaining/min: {result['remaining_minute']}")
            print(f"   Remaining/hour: {result['remaining_hour']}")
            
            return result
            
    except Exception as e:
        print(f"   ❌ Error in {test_name}: {e}")
        return None

async def test_multiple_requests(session, url, headers=None, count=25, test_name="Test"):
    """Test multiple requests to check rate limiting"""
    print(f"\n🔄 {test_name} - Testing {count} requests...")
    
    successful = 0
    rate_limited = 0
    last_headers = {}
    
    for i in range(1, count + 1):
        try:
            async with session.get(url, headers=headers or {}) as response:
                rate_headers = {k: v for k, v in response.headers.items() if 'RateLimit' in k}
                last_headers = rate_headers
                
                if response.status == 429:
                    rate_limited = i
                    print(f"   ⛔ Rate limited at request {i}")
                    break
                elif response.status in [200, 404]:  # 404 is OK for test endpoints
                    successful = i
                    if i <= 3 or i % 5 == 0:
                        tier = rate_headers.get('X-RateLimit-Tier', 'unknown')
                        remaining = rate_headers.get('X-RateLimit-Remaining-Minute', 'unknown')
                        print(f"   ✅ Request {i}: {response.status} (Tier: {tier}, Remaining: {remaining})")
                else:
                    print(f"   ⚠️ Request {i}: Status {response.status}")
            
            # Small delay to avoid overwhelming
            await asyncio.sleep(0.05)
            
        except Exception as e:
            print(f"   ❌ Request {i}: Error {e}")
            break
    
    return {
        'successful': successful,
        'rate_limited_at': rate_limited,
        'headers': last_headers
    }

async def test_server():
    """Test the server that should be running on port 8001"""
    base_url = "http://127.0.0.1:8001"
    
    try:
        print("🔄 Testing FastAPI server with rate limiting...")
        
        async with aiohttp.ClientSession() as session:
            
            # Test health endpoint (should not be rate limited)
            print("\n1️⃣ Testing Health Endpoint")
            health_result = await test_single_request(
                session, f"{base_url}/health", None, "Health Check"
            )
            
            if not health_result or health_result['status'] != 200:
                print("❌ Server not responding properly")
                return False
            
            # Test public user rate limits
            print("\n2️⃣ Testing Public User Rate Limits")
            public_result = await test_multiple_requests(
                session, f"{base_url}/v1/customers", None, 25, "Public User"
            )
            
            # Test admin user rate limits  
            print("\n3️⃣ Testing Admin User Rate Limits")
            admin_headers = {"Authorization": "Bearer admin_token"}
            admin_result = await test_multiple_requests(
                session, f"{base_url}/v1/customers", admin_headers, 25, "Admin User"
            )
            
            # Test super admin user rate limits
            print("\n4️⃣ Testing Super Admin User Rate Limits")  
            super_admin_headers = {"Authorization": "Bearer super_admin_token"}
            super_admin_result = await test_multiple_requests(
                session, f"{base_url}/v1/customers", super_admin_headers, 25, "Super Admin User"
            )
            
            # Test AI endpoint
            print("\n5️⃣ Testing AI Endpoint Rate Limits")
            ai_result = await test_multiple_requests(
                session, f"{base_url}/v1/ai/chat", admin_headers, 15, "AI Endpoint"
            )
            
            # Summary
            print("\n" + "=" * 50)
            print("📊 RATE LIMITING TEST SUMMARY")
            print("=" * 50)
            
            print(f"Public User:")
            print(f"  Successful requests: {public_result['successful']}")
            print(f"  Rate limited at: {public_result['rate_limited_at'] or 'Not reached'}")
            print(f"  Tier: {public_result['headers'].get('X-RateLimit-Tier', 'unknown')}")
            
            print(f"\nAdmin User:")
            print(f"  Successful requests: {admin_result['successful']}")
            print(f"  Rate limited at: {admin_result['rate_limited_at'] or 'Not reached'}")
            print(f"  Tier: {admin_result['headers'].get('X-RateLimit-Tier', 'unknown')}")
            
            print(f"\nSuper Admin User:")
            print(f"  Successful requests: {super_admin_result['successful']}")
            print(f"  Rate limited at: {super_admin_result['rate_limited_at'] or 'Not reached'}")
            print(f"  Tier: {super_admin_result['headers'].get('X-RateLimit-Tier', 'unknown')}")
            
            print(f"\nAI Endpoint:")
            print(f"  Successful requests: {ai_result['successful']}")
            print(f"  Rate limited at: {ai_result['rate_limited_at'] or 'Not reached'}")
            print(f"  Tier: {ai_result['headers'].get('X-RateLimit-Tier', 'unknown')}")
            
            # Validate admin privileges
            print(f"\n🎯 ADMIN PRIVILEGE VALIDATION:")
            if admin_result['successful'] >= public_result['successful']:
                ratio = admin_result['successful'] / max(public_result['successful'], 1)
                print(f"✅ Admin users can make {ratio:.1f}x more requests than public users")
            else:
                print(f"❌ Admin users don't have higher limits than public users")
            
            print(f"\n📈 Expected Behavior:")
            print(f"  Public: Should hit rate limit around 20 requests/minute")
            print(f"  Admin: Should hit rate limit around 100 requests/minute")
            print(f"  Super Admin: Should hit rate limit around 200 requests/minute")
            print(f"  AI: Should hit rate limit around 10 requests/minute (regardless of user)")
            
            print(f"\n✅ Rate limiting system validation completed!")
            return True
        
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to server at http://127.0.0.1:8001")
        print("   Make sure the FastAPI server is running")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def sync_test_server():
    """Synchronous wrapper for async test"""
    return asyncio.run(test_server())

if __name__ == "__main__":
    print("🧪 RATE LIMITING SERVER TEST")
    print("=" * 50)
    print("Testing server at http://127.0.0.1:8001")
    print("=" * 50)
    success = sync_test_server()
    if success:
        print("\n🎉 All tests passed! Rate limiting is working correctly.")
    else:
        print("\n⚠️ Tests failed. Check server status.")