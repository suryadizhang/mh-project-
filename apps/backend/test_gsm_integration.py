"""
Test script for GSM integration
Tests async initialization, fallback behavior, and secret source tracking
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import get_settings

async def test_gsm_integration():
    """Test GSM initialization and fallback"""
    print("=" * 60)
    print("Testing GSM Integration (Phase 1A)")
    print("=" * 60)
    
    # Get settings instance
    settings = get_settings()
    
    # Test 1: Check GSM fields exist
    print("\n[Test 1] Checking GSM fields...")
    assert hasattr(settings, '_gsm_config'), "Missing _gsm_config field"
    assert hasattr(settings, '_gsm_initialized'), "Missing _gsm_initialized field"
    assert hasattr(settings, '_secrets_loaded_from_gsm'), "Missing _secrets_loaded_from_gsm field"
    assert hasattr(settings, 'GCP_PROJECT_ID'), "Missing GCP_PROJECT_ID field"
    print("✅ All GSM fields present")
    
    # Test 2: Check methods exist
    print("\n[Test 2] Checking GSM methods...")
    assert hasattr(settings, 'initialize_gsm'), "Missing initialize_gsm method"
    assert hasattr(settings, 'get_secret_source'), "Missing get_secret_source method"
    print("✅ All GSM methods present")
    
    # Test 3: Test async initialization
    print("\n[Test 3] Testing async GSM initialization...")
    print(f"GCP Project ID: {settings.GCP_PROJECT_ID}")
    print(f"Environment: {settings.GCP_ENVIRONMENT}")
    
    gsm_status = await settings.initialize_gsm()
    print(f"GSM Status: {gsm_status}")
    
    # Test 4: Verify fallback behavior
    print("\n[Test 4] Checking fallback behavior...")
    if gsm_status.get('status') == 'env_only':
        print("✅ Using environment variables (GSM not available - expected in dev)")
        assert not gsm_status.get('gsm_available'), "GSM should not be available"
    elif gsm_status.get('status') == 'success':
        print(f"✅ GSM loaded {gsm_status.get('secrets_from_gsm', 0)} secrets")
        print(f"   Environment fallback: {gsm_status.get('secrets_from_env', 0)} secrets")
    elif gsm_status.get('status') == 'fallback_to_env':
        print(f"⚠️ GSM failed, using environment: {gsm_status.get('error')}")
    
    # Test 5: Check secret source tracking
    print("\n[Test 5] Testing secret source tracking...")
    secret_source = settings.get_secret_source('STRIPE_SECRET_KEY')
    print(f"STRIPE_SECRET_KEY source: {secret_source}")
    assert secret_source in ['gsm', 'env', 'unknown'], f"Invalid source: {secret_source}"
    print("✅ Secret source tracking works")
    
    # Test 6: Verify settings still work
    print("\n[Test 6] Verifying Settings still functional...")
    assert settings.APP_NAME, "APP_NAME should be set"
    assert settings.DATABASE_URL, "DATABASE_URL should be set"
    assert settings.SECRET_KEY, "SECRET_KEY should be set"
    print(f"✅ Settings functional (APP_NAME: {settings.APP_NAME})")
    
    print("\n" + "=" * 60)
    print("🎉 All GSM integration tests passed!")
    print("=" * 60)
    
    return gsm_status

if __name__ == "__main__":
    result = asyncio.run(test_gsm_integration())
    print(f"\nFinal Status: {result}")
