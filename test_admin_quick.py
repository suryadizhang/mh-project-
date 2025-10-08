import requests
import json

# Test admin AI response
try:
    response = requests.post(
        "http://localhost:8002/api/chat",
        headers={"Content-Type": "application/json"},
        json={
            "message": "How much is 1+1?",
            "user_role": "admin",
            "context": {"test": True}
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("Admin AI Response:")
        print(data.get("content", "No content"))
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Request failed: {e}")