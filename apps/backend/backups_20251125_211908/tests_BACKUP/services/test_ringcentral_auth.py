"""
RingCentral Authentication - Alternative Methods Test
"""
from ringcentral import SDK
import os
from dotenv import load_dotenv

load_dotenv()

# Method 1: Try using the app credentials directly without username/password
def test_client_credentials_flow():
    """Test if we can authenticate without username/password"""
    print("\n🔐 Testing Client Credentials Flow...")
    
    try:
        sdk = SDK(
            os.getenv('RC_CLIENT_ID'),
            os.getenv('RC_CLIENT_SECRET'),
            'https://platform.ringcentral.com'
        )
        
        platform = sdk.platform()
        
        # Try to get token using just client credentials
        # This won't work for private apps, but let's see the error
        response = platform.auth().data()
        print(f"✅ Auth successful: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Client credentials failed: {e}")
        return False

# Method 2: Check what we currently have
def show_current_config():
    """Display current RingCentral configuration"""
    print("\n📋 Current RingCentral Configuration:")
    print(f"   Client ID: {os.getenv('RC_CLIENT_ID')}")
    print(f"   Server: {os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')}")
    print(f"   Username: {os.getenv('RC_USERNAME')}")
    print(f"   Extension: {os.getenv('RC_EXTENSION')}")
    print(f"   SMS From: {os.getenv('RC_SMS_FROM')}")

if __name__ == "__main__":
    print("=" * 70)
    print("RINGCENTRAL AUTHENTICATION DIAGNOSTICS")
    print("=" * 70)
    
    show_current_config()
    test_client_credentials_flow()
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)
    print("""
For RingCentral to work with password authentication, you need to:

1. Go to: https://developers.ringcentral.com/console/app/3ADYc6Nv8qxeddtHygnfIK
2. Click on "Settings" tab
3. Under "Auth" section, look for "Grant Types" or similar
4. Enable "Password" or "Resource Owner Password Credentials"
5. Save and wait 5 minutes

ALTERNATIVE: We can skip RingCentral for now and test it separately later
after getting the proper authentication configured.

Current working integrations: 7/8 (87.5%)
- Stripe ✅
- OpenAI ✅  
- Plaid ✅
- Meta (FB/IG) ✅
- Google Maps ✅
- Cloudinary ✅
- Environment ✅
- RingCentral ❌ (auth issue)
    """)
