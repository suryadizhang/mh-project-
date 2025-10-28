"""
RingCentral JWT Authentication Setup Guide
"""

# JWT is more secure and recommended for server-side apps
# Here's how to set it up:

# Step 1: In RingCentral Developer Console
# 1. Go to your app "My Hibachi CRM"
# 2. Check "JWT auth flow" in authentication methods
# 3. Save

# Step 2: Generate JWT Credentials
# 1. Go to "Credentials" tab
# 2. Click "Create JWT Credentials" 
# 3. Download the credentials file (it's a JSON file)
# 4. The file will contain your private key

# Step 3: Add to .env file
# Add this line to your .env:
# RC_JWT_TOKEN=<paste the entire JWT token from the file>

# Step 4: Update the authentication code to use JWT:

from ringcentral import SDK
import os
from dotenv import load_dotenv

load_dotenv()

def authenticate_with_jwt():
    """Authenticate using JWT (recommended for server apps)"""
    sdk = SDK(
        os.getenv('RC_CLIENT_ID'),
        os.getenv('RC_CLIENT_SECRET'),
        os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
    )
    
    platform = sdk.platform()
    
    # Use JWT token authentication
    platform.login(jwt=os.getenv('RC_JWT_TOKEN'))
    
    return platform

def authenticate_with_password():
    """Authenticate using password (simpler but less secure)"""
    sdk = SDK(
        os.getenv('RC_CLIENT_ID'),
        os.getenv('RC_CLIENT_SECRET'),
        os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
    )
    
    platform = sdk.platform()
    
    # Use password authentication
    platform.login(
        username=os.getenv('RC_USERNAME'),
        extension=os.getenv('RC_EXTENSION'),
        password=os.getenv('RC_PASSWORD')
    )
    
    return platform

# Try JWT first, fall back to password if not available
try:
    if os.getenv('RC_JWT_TOKEN'):
        platform = authenticate_with_jwt()
        print("✅ Authenticated with JWT")
    else:
        platform = authenticate_with_password()
        print("✅ Authenticated with password")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
