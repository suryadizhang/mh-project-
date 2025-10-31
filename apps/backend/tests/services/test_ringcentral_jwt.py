"""
Test RingCentral JWT Authentication
This script tests the JWT token authentication method for RingCentral API
"""
import os
from dotenv import load_dotenv
from ringcentral import SDK

# Load environment variables
load_dotenv()

def test_jwt_auth():
    """Test RingCentral authentication using JWT token"""
    print("=" * 80)
    print("🔐 Testing RingCentral JWT Authentication")
    print("=" * 80)
    
    # Get credentials
    client_id = os.getenv('RC_CLIENT_ID')
    client_secret = os.getenv('RC_CLIENT_SECRET')
    jwt_token = os.getenv('RC_JWT_TOKEN')
    server = os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
    
    print(f"\n📋 Configuration:")
    print(f"   Client ID: {client_id}")
    print(f"   Server: {server}")
    print(f"   JWT Token: {jwt_token[:50]}..." if jwt_token else "   JWT Token: NOT FOUND")
    
    if not all([client_id, client_secret, jwt_token]):
        print("\n❌ ERROR: Missing required credentials")
        print("   Required: RC_CLIENT_ID, RC_CLIENT_SECRET, RC_JWT_TOKEN")
        return False
    
    try:
        # Initialize SDK
        print("\n🔧 Initializing RingCentral SDK...")
        rcsdk = SDK(client_id, client_secret, server)
        platform = rcsdk.platform()
        
        # Authenticate with JWT
        print("🔑 Authenticating with JWT token...")
        platform.login(jwt=jwt_token)
        
        print("✅ JWT Authentication SUCCESSFUL!\n")
        
        # Test API call - get account info
        print("📞 Testing API call - Getting account info...")
        response = platform.get('/restapi/v1.0/account/~')
        account_data = response.json_dict()  # Use json_dict() instead of json()
        
        print(f"✅ API Call Successful!")
        print(f"   Account ID: {account_data.get('id')}")
        print(f"   Status: {account_data.get('status')}")
        
        # Test getting extension info
        print("\n📱 Testing extension info...")
        ext_response = platform.get('/restapi/v1.0/account/~/extension/~')
        ext_data = ext_response.json_dict()  # Use json_dict() instead of json()
        
        print(f"✅ Extension Info Retrieved!")
        print(f"   Extension Number: {ext_data.get('extensionNumber')}")
        print(f"   Name: {ext_data.get('name')}")
        print(f"   Status: {ext_data.get('status')}")
        
        # Test SMS capability
        print("\n💬 Checking SMS capabilities...")
        if 'permissions' in ext_data:
            print(f"   Has SMS permissions configured")
        else:
            print(f"   SMS permissions: Not found in response")
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! RingCentral JWT authentication is working!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        print(f"   Error Type: {type(e).__name__}")
        
        # Check for specific errors
        if hasattr(e, 'response'):
            print(f"   Status Code: {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"   Error: {error_data.get('error')}")
                print(f"   Description: {error_data.get('error_description')}")
            except:
                print(f"   Response: {e.response.text}")
        
        print("\n" + "=" * 80)
        return False

if __name__ == "__main__":
    success = test_jwt_auth()
    exit(0 if success else 1)
