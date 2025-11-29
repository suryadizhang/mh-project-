"""Quick test for Stripe API"""
import stripe
from dotenv import load_dotenv
import os

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

print("Testing Stripe API...")
print(f"API Key (first 20 chars): {stripe.api_key[:20]}...")

try:
    # Test by retrieving account info
    account = stripe.Account.retrieve()
    print(f"✅ Success! Account ID: {account.id}")
    print(f"Email: {account.email}")
    print(f"Country: {account.country}")
except stripe.error.AuthenticationError as e:
    print(f"❌ Authentication Error: {e}")
    print("\nPossible fixes:")
    print("1. Go to: https://dashboard.stripe.com/test/apikeys")
    print("2. Click 'Reveal test key' for Secret key")
    print("3. Copy the ENTIRE key (should start with sk_test_)")
    print("4. Update STRIPE_SECRET_KEY in .env file")
except Exception as e:
    print(f"❌ Error: {e}")
