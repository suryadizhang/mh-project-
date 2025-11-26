#!/usr/bin/env python3
"""
Debug test for Resend email - checks configuration and sends test email
"""
import sys
from pathlib import Path
import os
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)
print(f"📁 Loaded .env from: {env_path}")
print()

print("=" * 70)
print("🔍 RESEND EMAIL DEBUG TEST")
print("=" * 70)
print()

# Check environment variables
print("📋 ENVIRONMENT VARIABLES:")
print(f"   EMAIL_ENABLED: {os.getenv('EMAIL_ENABLED')}")
print(f"   RESEND_API_KEY: {os.getenv('RESEND_API_KEY', 'NOT SET')[:20]}..." if os.getenv('RESEND_API_KEY') else "   RESEND_API_KEY: NOT SET")
print(f"   RESEND_FROM_EMAIL: {os.getenv('RESEND_FROM_EMAIL')}")
print(f"   RESEND_FROM_NAME: {os.getenv('RESEND_FROM_NAME')}")
print()

# Try importing resend
print("📦 CHECKING RESEND PACKAGE:")
try:
    import resend
    print(f"   ✅ Resend package imported successfully")
    print(f"   Version: {resend.__version__ if hasattr(resend, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"   ❌ Resend package not found: {e}")
    sys.exit(1)
print()

# Load email service
print("🔧 LOADING EMAIL SERVICE:")
from src.services.email_service import email_service

print(f"   Enabled: {email_service.enabled}")
print(f"   API Key: {'SET' if email_service.api_key else 'NOT SET'}")
print(f"   From Email: {email_service.from_email}")
print(f"   From Name: {email_service.from_name}")
print()

# Try sending a simple test email directly via Resend API
print("📧 SENDING TEST EMAIL DIRECTLY VIA RESEND API:")
test_email = "suryadizhang.swe@gmail.com"

try:
    resend.api_key = os.getenv('RESEND_API_KEY')

    params = {
        "from": "My Hibachi Chef <cs@myhibachichef.com>",
        "to": [test_email],
        "subject": "🧪 Resend Test Email - Direct API Call",
        "html": "<h1>Test Email</h1><p>This is a direct API test from My Hibachi backend.</p>",
        "text": "Test Email - This is a direct API test from My Hibachi backend.",
    }

    print(f"   Sending to: {test_email}")
    print(f"   From: {params['from']}")
    print(f"   Subject: {params['subject']}")
    print()

    response = resend.Emails.send(params)

    print(f"   ✅ SUCCESS!")
    print(f"   Response: {response}")
    print(f"   Message ID: {response.get('id', 'N/A')}")

except Exception as e:
    print(f"   ❌ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("🔍 Check https://resend.com/logs for delivery status")
print("=" * 70)
