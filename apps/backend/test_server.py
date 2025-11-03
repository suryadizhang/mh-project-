"""
Quick Server Test Script
Tests if the backend server is running and responds to requests
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", expected_status=200):
    """Test a single endpoint"""
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"Method: {method}")
        print(f"{'='*60}")
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response Data:\n{json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text[:200]}")
        
        if response.status_code == expected_status:
            print(f"✅ {name} - PASSED")
            return True
        else:
            print(f"❌ {name} - FAILED (Expected {expected_status}, got {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} - CONNECTION FAILED (Is server running?)")
        return False
    except Exception as e:
        print(f"❌ {name} - ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 BACKEND SERVER TEST SUITE")
    print("="*60)
    
    # Wait a moment for server to be ready
    print("\n⏳ Waiting for server to start...")
    time.sleep(2)
    
    tests = [
        ("Basic Health Check", f"{BASE_URL}/health", "GET", 200),
        ("Liveness Probe", f"{BASE_URL}/api/health/live", "GET", 200),
        ("Readiness Probe", f"{BASE_URL}/api/health/ready", "GET", 200),
        ("Startup Probe", f"{BASE_URL}/api/health/startup", "GET", 200),
        ("API Documentation", f"{BASE_URL}/docs", "GET", 200),
    ]
    
    results = []
    for test in tests:
        results.append(test_endpoint(*test))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Server is fully functional!")
    elif passed > 0:
        print(f"\n⚠️  PARTIAL SUCCESS - {passed} out of {total} tests passed")
    else:
        print("\n❌ ALL TESTS FAILED - Check if server is running")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
