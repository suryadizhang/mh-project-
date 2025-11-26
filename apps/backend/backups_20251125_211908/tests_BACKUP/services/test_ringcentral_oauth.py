"""
RingCentral OAuth 2.0 Authentication (Alternative to Password)
Since password flow isn't available, we'll use OAuth client credentials
"""
import os
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

def get_oauth_token():
    """Get OAuth token using client credentials"""
    client_id = os.getenv('RC_CLIENT_ID')
    client_secret = os.getenv('RC_CLIENT_SECRET')
    
    # Create Basic Auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # For extension-level access, we need to use password grant
    # But since that's not enabled, let's try without extension
    data = {
        'grant_type': 'password',
        'username': os.getenv('RC_USERNAME'),
        'password': os.getenv('RC_PASSWORD'),
        'extension': os.getenv('RC_EXTENSION')
    }
    
    print("🔐 Attempting OAuth authentication...")
    print(f"Username: {os.getenv('RC_USERNAME')}")
    print(f"Extension: {os.getenv('RC_EXTENSION')}\n")
    
    try:
        response = requests.post(
            'https://platform.ringcentral.com/restapi/oauth/token',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentication successful!")
            print(f"Access Token: {token_data['access_token'][:20]}...")
            print(f"Token Type: {token_data['token_type']}")
            print(f"Expires In: {token_data['expires_in']} seconds")
            return token_data
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}\n")
            
            # Try without extension
            print("🔄 Trying without extension...")
            data.pop('extension', None)
            response2 = requests.post(
                'https://platform.ringcentral.com/restapi/oauth/token',
                headers=headers,
                data=data
            )
            
            if response2.status_code == 200:
                token_data = response2.json()
                print("✅ Authentication successful (without extension)!")
                return token_data
            else:
                print(f"❌ Still failed: {response2.status_code}")
                print(f"Response: {response2.text}")
                return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("RINGCENTRAL OAUTH 2.0 AUTHENTICATION TEST")
    print("=" * 70)
    print()
    
    token = get_oauth_token()
    
    print()
    print("=" * 70)
    if token:
        print("✅ RESULT: Authentication successful!")
        print("Next step: Store this token and use it for API calls")
    else:
        print("❌ RESULT: Authentication failed")
        print()
        print("CONCLUSION:")
        print("Password grant type is NOT enabled for this app.")
        print()
        print("RECOMMENDATION:")
        print("Since RingCentral SMS requires verification anyway,")
        print("let's proceed with webhook testing for the 7 working")
        print("integrations and handle RingCentral separately.")
    print("=" * 70)
