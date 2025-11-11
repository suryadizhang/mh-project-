#!/usr/bin/env python3
"""
RingCentral Quick Setup Script
Automates the setup process for RingCentral integration.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from apps.api.app.utils.ringcentral_utils import (
        validate_configuration,
        test_connection,
        get_setup_checklist,
        create_environment_template
    )
    from apps.api.app.utils.ringcentral_seed_data import (
        create_test_environment,
        validate_test_data
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("🎌 MY HIBACHI CHEF - RingCentral Setup")
    print("=" * 60)
    print()


def print_section(title: str):
    """Print section header."""
    print(f"\n📋 {title}")
    print("-" * 50)


def check_environment():
    """Check if required environment variables are set."""
    print_section("Environment Check")
    
    config = validate_configuration()
    
    if config["valid"]:
        print("✅ All required environment variables are set")
        return True
    else:
        print("❌ Missing required environment variables:")
        for missing in config["missing"]:
            print(f"   - {missing}")
        
        print("\n💡 Solution:")
        print("1. Copy the environment template below to your .env file")
        print("2. Fill in your RingCentral credentials")
        print()
        print(create_environment_template())
        return False


async def test_api_connection():
    """Test RingCentral API connection."""
    print_section("API Connection Test")
    
    try:
        result = await test_connection()
        
        if result["connected"]:
            print("✅ Successfully connected to RingCentral API")
            print(f"   Account: {result['account_info']['name']}")
            print(f"   Status: {result['account_info']['status']}")
            
            if result["capabilities"]["sms_ready"]:
                print(f"   SMS Ready: ✅ ({result['capabilities']['phone_number']})")
            else:
                print("   SMS Ready: ❌ (No phone number configured)")
            
            return True
        else:
            print(f"❌ Failed to connect: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def setup_test_data():
    """Set up test data for development."""
    print_section("Test Data Setup")
    
    try:
        # Validate test data generation
        validation = validate_test_data()
        
        if validation["all_valid"]:
            print("✅ Test data generation working correctly")
            
            # Create test environment
            test_env = create_test_environment()
            
            # Save test data to file
            output_file = project_root / "ringcentral_test_data.json"
            with open(output_file, "w") as f:
                json.dump(test_env, f, indent=2, default=str)
            
            print(f"✅ Test data saved to: {output_file}")
            print(f"   - {len(test_env['leads'])} test leads")
            print(f"   - {len(test_env['phone_numbers'])} test phone numbers") 
            print(f"   - {len(test_env['conversation_scenarios'])} conversation scenarios")
            print(f"   - {len(test_env['webhook_payloads'])} webhook test payloads")
            return True
        else:
            print("❌ Test data validation failed")
            if "error" in validation:
                print(f"   Error: {validation['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Test data setup failed: {e}")
        return False


def show_setup_checklist():
    """Show setup progress checklist."""
    print_section("Setup Checklist")
    
    try:
        checklist = get_setup_checklist()
        
        for step in checklist["steps"]:
            status = "✅" if step["completed"] else "❌"
            required = " (Required)" if step["required"] else " (Optional)"
            
            print(f"{status} Step {step['step']}: {step['title']}{required}")
            print(f"      {step['description']}")
            
            if not step["completed"] and "missing" in step:
                for missing in step["missing"]:
                    print(f"      Missing: {missing}")
        
        print(f"\nSetup Complete: {'✅' if checklist['setup_complete'] else '❌'}")
        
        if checklist["next_actions"]:
            print("\n🎯 Next Actions:")
            for action in checklist["next_actions"]:
                print(f"   - {action}")
        
        return checklist["setup_complete"]
        
    except Exception as e:
        print(f"❌ Failed to get setup checklist: {e}")
        return False


def show_next_steps():
    """Show next steps after setup."""
    print_section("Next Steps")
    
    print("🚀 Your RingCentral integration is set up! Here's what to do next:")
    print()
    print("1. 📱 Register Webhooks:")
    print("   python scripts/register_ringcentral_webhooks.py")
    print()
    print("2. 🧪 Test SMS Sending:")
    print("   python scripts/test_ringcentral_sms.py +1234567890")
    print()
    print("3. 🔗 Start Development Server:")
    print("   uvicorn apps.api.app.main:app --reload")
    print()
    print("4. 📊 Monitor Webhook Health:")
    print("   curl http://localhost:8000/api/webhooks/ringcentral/health")
    print()
    print("5. 📚 Read the Complete Guide:")
    print("   COMPLETE_RINGCENTRAL_IMPLEMENTATION_GUIDE.md")


async def main():
    """Main setup function."""
    print_banner()
    
    success_count = 0
    total_checks = 4
    
    # Check 1: Environment
    if check_environment():
        success_count += 1
    
    # Check 2: API Connection (only if environment is good)
    if success_count > 0:
        if await test_api_connection():
            success_count += 1
    
    # Check 3: Test Data
    if setup_test_data():
        success_count += 1
    
    # Check 4: Setup Checklist
    if show_setup_checklist():
        success_count += 1
    
    # Summary
    print_section("Setup Summary")
    print(f"Completed: {success_count}/{total_checks} checks")
    
    if success_count == total_checks:
        print("🎉 Setup completed successfully!")
        show_next_steps()
    else:
        print("⚠️  Setup incomplete. Please address the issues above.")
        print("\n💡 For help, check the implementation guide:")
        print("   COMPLETE_RINGCENTRAL_IMPLEMENTATION_GUIDE.md")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        sys.exit(1)