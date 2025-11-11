import requests

def test_customer_app_port_3007():
    """Test customer app on port 3007"""
    url = "http://localhost:3007"
    
    try:
        print(f"Testing {url}")
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Customer app is accessible on port 3007!")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_customer_app_port_3007()