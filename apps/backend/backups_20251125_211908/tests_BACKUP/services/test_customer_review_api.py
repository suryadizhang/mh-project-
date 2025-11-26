"""
Test Customer Review API - Verify endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_stats_endpoint():
    """Test the stats endpoint (no auth required)"""
    print("\n🧪 Testing GET /api/customer-reviews/stats")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/customer-reviews/stats")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats endpoint working!")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_approved_reviews_endpoint():
    """Test the approved reviews feed (no auth required)"""
    print("\n🧪 Testing GET /api/customer-reviews/approved-reviews")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/customer-reviews/approved-reviews?page=1&limit=10")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Approved reviews endpoint working!")
            print(f"Success: {data.get('success')}")
            print(f"Total: {data.get('total', 0)}")
            print(f"Reviews: {len(data.get('data', []))}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_swagger_docs():
    """Test if API docs are accessible"""
    print("\n🧪 Testing GET /docs (Swagger UI)")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API documentation accessible!")
            print(f"📚 Open in browser: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Customer Review API - Integration Test")
    print("=" * 70)
    
    results = []
    
    # Test all endpoints
    results.append(("Stats Endpoint", test_stats_endpoint()))
    results.append(("Approved Reviews Endpoint", test_approved_reviews_endpoint()))
    results.append(("API Documentation", test_swagger_docs()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n🎯 Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✨ All tests passed! Customer Review API is operational.")
        print(f"\n📚 Next steps:")
        print(f"   1. Open http://localhost:8000/docs to see all endpoints")
        print(f"   2. Test submit-review endpoint with images + videos")
        print(f"   3. Build admin moderation API")
        print(f"   4. Build frontend components")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
