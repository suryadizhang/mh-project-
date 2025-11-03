# 🧪 Complete API Integration Test Suite
# Tests all 7 API integrations with webhook support

import os
import sys
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

# =============================================================================
# 1. Environment Variables Check
# =============================================================================

def test_environment_variables():
    """Check if all required environment variables are set"""
    print_header("1. ENVIRONMENT VARIABLES CHECK")
    
    required_vars = {
        "Stripe": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET"],
        "RingCentral": ["RC_CLIENT_ID", "RC_CLIENT_SECRET", "RC_USERNAME", "RC_PASSWORD", "RC_EXTENSION", "RC_SMS_FROM"],
        "OpenAI": ["OPENAI_API_KEY", "OPENAI_MODEL"],
        "Plaid": ["PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ENV"],
        "Meta": ["META_APP_ID", "META_APP_SECRET", "META_PAGE_ACCESS_TOKEN", "META_VERIFY_TOKEN"],
        "Google": ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_MAPS_API_KEY"],
        "Cloudinary": ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"],
        "Business": ["BUSINESS_ADDRESS", "BUSINESS_LATITUDE", "BUSINESS_LONGITUDE", "TRAVEL_FREE_DISTANCE_MILES", "TRAVEL_FEE_PER_MILE_CENTS"]
    }
    
    all_ok = True
    for service, vars_list in required_vars.items():
        print(f"\n{Colors.BOLD}{service}:{Colors.RESET}")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if any(x in var.lower() for x in ['secret', 'password', 'key', 'token']):
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                print_success(f"{var}: {display_value}")
            else:
                print_error(f"{var}: NOT SET")
                all_ok = False
    
    return all_ok

# =============================================================================
# 2. Google Maps Distance Matrix API Test
# =============================================================================

def test_google_maps_api():
    """Test Google Maps Distance Matrix API and travel fee calculator"""
    print_header("2. GOOGLE MAPS API & TRAVEL FEE CALCULATOR")
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    origin = f"{os.getenv('BUSINESS_LATITUDE')},{os.getenv('BUSINESS_LONGITUDE')}"
    
    test_destinations = [
        ("Google HQ, Mountain View", "1600 Amphitheatre Parkway, Mountain View, CA"),
        ("San Francisco", "San Francisco, CA"),
        ("Sacramento", "Sacramento, CA"),
    ]
    
    for name, address in test_destinations:
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': origin,
                'destinations': address,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'OK':
                element = data['rows'][0]['elements'][0]
                if element.get('status') == 'OK':
                    distance_miles = element['distance']['value'] / 1609.34
                    duration = element['duration']['text']
                    
                    # Calculate travel fee
                    free_miles = int(os.getenv('TRAVEL_FREE_DISTANCE_MILES', 30))
                    fee_per_mile = int(os.getenv('TRAVEL_FEE_PER_MILE_CENTS', 200)) / 100
                    
                    if distance_miles <= free_miles:
                        fee = 0
                        fee_text = f"$0 (FREE - within {free_miles} miles)"
                    else:
                        billable_miles = distance_miles - free_miles
                        fee = billable_miles * fee_per_mile
                        fee_text = f"${fee:.2f} ({billable_miles:.1f} miles × ${fee_per_mile}/mile)"
                    
                    print_success(f"{name}: {distance_miles:.1f} miles, {duration}, Travel fee: {fee_text}")
                else:
                    print_error(f"{name}: Routing error - {element.get('status')}")
            else:
                print_error(f"{name}: API error - {data.get('status')}")
        except Exception as e:
            print_error(f"{name}: {str(e)}")
    
    return True

# =============================================================================
# 3. RingCentral SMS Test
# =============================================================================

def test_ringcentral_api():
    """Test RingCentral authentication and SMS capability"""
    print_header("3. RINGCENTRAL SMS & VOICE API")
    
    try:
        from ringcentral import SDK
        
        sdk = SDK(
            os.getenv('RC_CLIENT_ID'),
            os.getenv('RC_CLIENT_SECRET'),
            os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
        )
        
        platform = sdk.platform()
        
        # Try JWT authentication first
        jwt_token = os.getenv('RC_JWT_TOKEN')
        if jwt_token:
            print_info("Using JWT authentication...")
            platform.login(jwt=jwt_token)
        else:
            print_warning("No JWT token found, trying password authentication...")
            platform.login(
                jwt=None,
                username=os.getenv('RC_USERNAME'),
                password=os.getenv('RC_PASSWORD'),
                extension=os.getenv('RC_EXTENSION')
            )
        
        print_success(f"Authentication successful")
        
        # Get account info
        response = platform.get('/restapi/v1.0/account/~')
        account_data = response.json_dict()
        print_info(f"Account ID: {account_data.get('id')}")
        
        # Get extension info
        ext_response = platform.get('/restapi/v1.0/account/~/extension/~')
        ext_data = ext_response.json_dict()
        print_info(f"Extension: {ext_data.get('extensionNumber')} - {ext_data.get('name')}")
        print_info(f"Main number: {os.getenv('RC_SMS_FROM')}")
        print_warning("SMS sending test skipped (would send real SMS)")
        
        return True
    except ImportError:
        print_error("ringcentral SDK not installed. Run: pip install ringcentral")
        return False
    except Exception as e:
        print_error(f"Authentication failed: {str(e)}")
        return False

# =============================================================================
# 4. OpenAI API Test
# =============================================================================

def test_openai_api():
    """Test OpenAI API connection"""
    print_header("4. OPENAI API")
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            messages=[{"role": "user", "content": "Say 'API connection successful' in exactly 3 words"}],
            max_tokens=10
        )
        
        message = response.choices[0].message.content
        print_success(f"API connection successful")
        print_info(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4')}")
        print_info(f"Test response: {message}")
        
        return True
    except ImportError:
        print_error("openai SDK not installed. Run: pip install openai")
        return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

# =============================================================================
# 5. Stripe API Test
# =============================================================================

def test_stripe_api():
    """Test Stripe API connection"""
    print_header("5. STRIPE PAYMENT API")
    
    try:
        import stripe
        
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Test by fetching account details
        account = stripe.Account.retrieve()
        
        print_success(f"API connection successful")
        print_info(f"Account ID: {account.id}")
        print_info(f"Webhook secret configured: {'Yes' if os.getenv('STRIPE_WEBHOOK_SECRET') else 'No'}")
        
        return True
    except ImportError:
        print_error("stripe SDK not installed. Run: pip install stripe")
        return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

# =============================================================================
# 6. Plaid API Test
# =============================================================================

def test_plaid_api():
    """Test Plaid API connection"""
    print_header("6. PLAID BANKING API")
    
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products
        from plaid.model.country_code import CountryCode
        
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={
                'clientId': os.getenv('PLAID_CLIENT_ID'),
                'secret': os.getenv('PLAID_SECRET'),
            }
        )
        
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)
        
        # Test by creating a link token
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="My Hibachi Chef",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id='test-user-123'
            )
        )
        
        response = client.link_token_create(request)
        
        print_success(f"API connection successful")
        print_info(f"Environment: {os.getenv('PLAID_ENV')}")
        print_info(f"Client ID: {os.getenv('PLAID_CLIENT_ID')[:8]}...")
        
        return True
    except ImportError:
        print_error("plaid SDK not installed. Run: pip install plaid-python")
        return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

# =============================================================================
# 7. Meta (Facebook/Instagram) API Test
# =============================================================================

def test_meta_api():
    """Test Meta Graph API connection"""
    print_header("7. META (FACEBOOK/INSTAGRAM) API")
    
    try:
        page_token = os.getenv('META_PAGE_ACCESS_TOKEN')
        
        # Test by fetching page info
        url = f"https://graph.facebook.com/v18.0/me"
        params = {'access_token': page_token}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'id' in data:
            print_success(f"API connection successful")
            print_info(f"Page ID: {data.get('id')}")
            print_info(f"Page Name: {data.get('name', 'N/A')}")
            
            # Check Instagram connection
            ig_url = f"https://graph.facebook.com/v18.0/{data['id']}"
            ig_params = {
                'fields': 'instagram_business_account',
                'access_token': page_token
            }
            ig_response = requests.get(ig_url, params=ig_params, timeout=10)
            ig_data = ig_response.json()
            
            if 'instagram_business_account' in ig_data:
                print_success(f"Instagram connected: {ig_data['instagram_business_account']['id']}")
            else:
                print_warning("Instagram not connected")
            
            return True
        else:
            print_error(f"API test failed: {data.get('error', {}).get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

# =============================================================================
# 8. Cloudinary API Test
# =============================================================================

def test_cloudinary_api():
    """Test Cloudinary image upload API"""
    print_header("8. CLOUDINARY IMAGE UPLOAD API")
    
    try:
        import cloudinary
        import cloudinary.api
        
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET')
        )
        
        # Test by pinging the API
        response = cloudinary.api.ping()
        
        if response.get('status') == 'ok':
            print_success(f"API connection successful")
            print_info(f"Cloud name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
            return True
        else:
            print_error(f"API test failed")
            return False
    except ImportError:
        print_error("cloudinary SDK not installed. Run: pip install cloudinary")
        return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

# =============================================================================
# Main Test Runner
# =============================================================================

def main():
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║           MY HIBACHI CRM - API INTEGRATION TEST SUITE             ║")
    print("║                                                                    ║")
    print("║  Testing all 7 API integrations before webhook configuration      ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    start_time = datetime.now()
    
    results = {}
    
    # Run all tests
    results['Environment Variables'] = test_environment_variables()
    results['Google Maps API'] = test_google_maps_api()
    results['RingCentral API'] = test_ringcentral_api()
    results['OpenAI API'] = test_openai_api()
    results['Stripe API'] = test_stripe_api()
    results['Plaid API'] = test_plaid_api()
    results['Meta API'] = test_meta_api()
    results['Cloudinary API'] = test_cloudinary_api()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    print(f"{Colors.BOLD}Duration: {duration:.2f} seconds{Colors.RESET}\n")
    
    if passed == total:
        print_success("All integration tests passed! ✨")
        print_info("\nNext steps:")
        print("  1. Start your backend server")
        print("  2. Start Cloudflare Tunnel to get public URL")
        print("  3. Configure webhooks with the tunnel URL")
        print("  4. Test webhook integrations\n")
    else:
        print_error("Some tests failed. Please fix the issues before proceeding.")
        print_warning("\nCheck:")
        print("  - All environment variables are set in .env")
        print("  - All required packages are installed")
        print("  - API credentials are valid\n")

if __name__ == "__main__":
    main()
