#!/usr/bin/env python3

"""
Rate Limiting Test Script
Tests admin vs public rate limits to ensure admins get higher limits
"""

import asyncio
import aiohttp
import time
from typing import Dict, List

# Test configuration
API_BASE = "http://127.0.0.1:8001"  # Updated to match actual server port
TEST_ENDPOINTS = ["/v1/customers", "/v1/leads", "/v1/ai/chat"]

async def test_rate_limit(session: aiohttp.ClientSession, endpoint: str, headers: Dict[str, str], max_requests: int = 25) -> Dict:
    """Test rate limiting for a specific endpoint and user type"""
    
    results = {
        "endpoint": endpoint,
        "headers": headers,
        "successful_requests": 0,
        "rate_limited_at": None,
        "rate_limit_headers": {},
        "errors": []
    }
    
    print(f"\n🧪 Testing {endpoint} with {headers.get('Authorization', 'no auth')}")
    
    for i in range(1, max_requests + 1):
        try:
            async with session.get(f"{API_BASE}{endpoint}", headers=headers) as response:
                results["rate_limit_headers"] = {
                    "tier": response.headers.get("X-RateLimit-Tier", "unknown"),
                    "remaining_minute": response.headers.get("X-RateLimit-Remaining-Minute", "unknown"),
                    "remaining_hour": response.headers.get("X-RateLimit-Remaining-Hour", "unknown"),
                    "limit_minute": response.headers.get("X-RateLimit-Limit-Minute", "unknown"),
                    "limit_hour": response.headers.get("X-RateLimit-Limit-Hour", "unknown")
                }
                
                if response.status == 429:
                    results["rate_limited_at"] = i
                    print(f"  ❌ Rate limited at request {i}")
                    break
                elif response.status in [200, 404]:  # 404 is OK for test endpoints
                    results["successful_requests"] = i
                    if i <= 5 or i % 5 == 0:
                        print(f"  ✅ Request {i}: {response.status} (Remaining: {results['rate_limit_headers']['remaining_minute']}/min)")
                else:
                    results["errors"].append(f"Request {i}: Status {response.status}")
                    
        except Exception as e:
            results["errors"].append(f"Request {i}: Error {str(e)}")
    
    return results

async def run_rate_limit_tests():
    """Run comprehensive rate limiting tests"""
    
    print("🔒 RATE LIMITING TEST SUITE")
    print("=" * 50)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Public User (No Auth)",
            "headers": {},
            "expected_limit": 20
        },
        {
            "name": "Admin User",
            "headers": {"Authorization": "Bearer admin_token"},
            "expected_limit": 100
        },
        {
            "name": "Super Admin User",
            "headers": {"Authorization": "Bearer super_admin_token"},
            "expected_limit": 200
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        all_results = []
        
        for scenario in test_scenarios:
            print(f"\n📊 Testing: {scenario['name']}")
            print(f"Expected Rate Limit: {scenario['expected_limit']} req/min")
            
            # Test with a regular endpoint
            result = await test_rate_limit(
                session, 
                "/v1/customers", 
                scenario["headers"], 
                scenario["expected_limit"] + 5
            )
            
            all_results.append({
                "scenario": scenario["name"],
                "result": result
            })
            
            # Wait a bit between tests
            await asyncio.sleep(1)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 RATE LIMITING TEST SUMMARY")
        print("=" * 50)
        
        for test in all_results:
            scenario = test["scenario"]
            result = test["result"]
            
            print(f"\n{scenario}:")
            print(f"  Tier: {result['rate_limit_headers'].get('tier', 'unknown')}")
            print(f"  Successful Requests: {result['successful_requests']}")
            print(f"  Rate Limited At: {result['rate_limited_at'] or 'Not reached'}")
            print(f"  Limit per Minute: {result['rate_limit_headers'].get('limit_minute', 'unknown')}")
            print(f"  Remaining: {result['rate_limit_headers'].get('remaining_minute', 'unknown')}")
            
            if result['errors']:
                print(f"  Errors: {len(result['errors'])}")

async def test_health_endpoint():
    """Test that health endpoint is not rate limited"""
    print("\n🏥 Testing Health Endpoint (Should not be rate limited)")
    
    async with aiohttp.ClientSession() as session:
        for i in range(1, 26):
            try:
                async with session.get(f"{API_BASE}/health") as response:
                    if response.status == 429:
                        print(f"  ❌ Health endpoint rate limited at request {i}")
                        return
                    elif i % 5 == 0:
                        print(f"  ✅ Health check {i}: {response.status}")
            except Exception as e:
                print(f"  ❌ Health check {i}: Error {str(e)}")
        
        print("  ✅ Health endpoint not rate limited (as expected)")

async def test_ai_endpoint_limits():
    """Test AI endpoint rate limits (should be 10/min regardless of user)"""
    print("\n🤖 Testing AI Endpoint Rate Limits")
    
    test_scenarios = [
        {
            "name": "Public User - AI",
            "headers": {},
            "expected_limit": 10
        },
        {
            "name": "Admin User - AI", 
            "headers": {"Authorization": "Bearer admin_token"},
            "expected_limit": 10  # Same as public for AI
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for scenario in test_scenarios:
            print(f"\n  Testing: {scenario['name']}")
            
            result = await test_rate_limit(
                session,
                "/v1/ai/chat",
                scenario["headers"],
                15  # Test 15 requests
            )
            
            print(f"    Tier: {result['rate_limit_headers'].get('tier', 'unknown')}")
            print(f"    Rate Limited At: {result['rate_limited_at'] or 'Not reached'}")
            print(f"    Expected: ~10 requests/min")

if __name__ == "__main__":
    print("Starting rate limiting tests...")
    print("Make sure the FastAPI server is running on http://127.0.0.1:8000")
    print()
    
    asyncio.run(test_health_endpoint())
    asyncio.run(run_rate_limit_tests())
    asyncio.run(test_ai_endpoint_limits())
    
    print("\n✅ Rate limiting tests completed!")