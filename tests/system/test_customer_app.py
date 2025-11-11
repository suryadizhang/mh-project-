import requests
import time

def test_customer_app():
    """Simple test for customer app"""
    url = "http://localhost:3000"
    
    for attempt in range(5):
        try:
            print(f"Attempt {attempt + 1}: Testing {url}")
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            if response.status_code == 200:
                print("✅ Customer app is accessible!")
                return True
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)
    
    return False

if __name__ == "__main__":
    test_customer_app()