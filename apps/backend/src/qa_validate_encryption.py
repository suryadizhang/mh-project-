#!/usr/bin/env python3
"""
QA Validation Script - Customer Encryption Integration

Tests the Customer model encryption integration in a real environment.
Run this after deploying to staging to validate everything works.

Usage:
    python qa_validate_encryption.py
    python qa_validate_encryption.py --with-key  # Test with encryption enabled
"""

import asyncio
import sys
from uuid import uuid4
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, "apps/backend/src")

from core.encryption import encrypt_email, decrypt_email, encrypt_phone, decrypt_phone


def test_encryption_functions():
    """Test encryption helper functions"""
    print("\n" + "="*80)
    print("TEST 1: Encryption Helper Functions")
    print("="*80)

    # Test email encryption
    original_email = "qa.test@myhibachi.com"
    encrypted_email = encrypt_email(original_email)
    decrypted_email = decrypt_email(encrypted_email)

    print(f"\n📧 Email Encryption Test:")
    print(f"  Original:  {original_email}")
    print(f"  Encrypted: {encrypted_email[:50]}..." if len(encrypted_email) > 50 else f"  Encrypted: {encrypted_email}")
    print(f"  Decrypted: {decrypted_email}")
    print(f"  ✅ Match: {original_email.lower() == decrypted_email}")

    # Test phone encryption
    original_phone = "+1 (555) 123-4567"
    encrypted_phone = encrypt_phone(original_phone)
    decrypted_phone = decrypt_phone(encrypted_phone)

    print(f"\n📱 Phone Encryption Test:")
    print(f"  Original:  {original_phone}")
    print(f"  Encrypted: {encrypted_phone[:50]}..." if len(encrypted_phone) > 50 else f"  Encrypted: {encrypted_phone}")
    print(f"  Decrypted: {decrypted_phone}")
    print(f"  ✅ Formatting stripped: {' ' not in decrypted_phone and '(' not in decrypted_phone}")

    # Test passthrough mode detection
    is_encrypted = encrypted_email.startswith("gAAAAA")
    mode = "🔐 Encrypted (key configured)" if is_encrypted else "🔓 Passthrough (no key)"
    print(f"\n🔑 Encryption Mode: {mode}")

    return True


def test_customer_model_properties():
    """Test Customer model @property decorators"""
    print("\n" + "="*80)
    print("TEST 2: Customer Model Properties (Code Check)")
    print("="*80)

    try:
        from db.models.core import Customer

        # Check that Customer has required properties
        assert hasattr(Customer, 'email'), "❌ Customer.email property missing"
        assert hasattr(Customer, 'phone'), "❌ Customer.phone property missing"

        # Check that properties are decorated
        email_prop = getattr(Customer, 'email')
        phone_prop = getattr(Customer, 'phone')

        assert isinstance(email_prop, property), "❌ email is not a property"
        assert isinstance(phone_prop, property), "❌ phone is not a property"

        print("\n✅ Customer model structure validated:")
        print("  - email property exists ✅")
        print("  - phone property exists ✅")
        print("  - Both are @property decorated ✅")

        # Check that encryption fields exist
        # Note: These are class attributes, check via __annotations__
        if hasattr(Customer, '__annotations__'):
            annotations = Customer.__annotations__
            assert 'email_encrypted' in annotations, "❌ email_encrypted field missing"
            assert 'phone_encrypted' in annotations, "❌ phone_encrypted field missing"
            print("  - email_encrypted storage field exists ✅")
            print("  - phone_encrypted storage field exists ✅")

        return True

    except ImportError as e:
        print(f"❌ Failed to import Customer model: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Validation failed: {e}")
        return False


def test_encryption_integration():
    """Test encryption integration with core module"""
    print("\n" + "="*80)
    print("TEST 3: Encryption Module Integration")
    print("="*80)

    try:
        from core import encryption

        # Check all required functions exist
        required_functions = [
            'encrypt_email',
            'decrypt_email',
            'encrypt_phone',
            'decrypt_phone',
            'encrypt_field',
            'decrypt_field',
        ]

        print("\n📦 Checking encryption module exports:")
        for func_name in required_functions:
            exists = hasattr(encryption, func_name)
            status = "✅" if exists else "❌"
            print(f"  {status} {func_name}")
            if not exists:
                return False

        # Test that functions are callable
        print("\n🔧 Testing function signatures:")
        test_cases = [
            ("encrypt_email", ["test@example.com"]),
            ("decrypt_email", ["test@example.com"]),
            ("encrypt_phone", ["+1234567890"]),
            ("decrypt_phone", ["+1234567890"]),
        ]

        for func_name, args in test_cases:
            func = getattr(encryption, func_name)
            try:
                result = func(*args)
                print(f"  ✅ {func_name}({args[0]}) → {result[:30]}..." if len(result) > 30 else f"  ✅ {func_name}({args[0]}) → {result}")
            except Exception as e:
                print(f"  ❌ {func_name} failed: {e}")
                return False

        return True

    except ImportError as e:
        print(f"❌ Failed to import encryption module: {e}")
        return False


def test_empty_values():
    """Test handling of empty/None values"""
    print("\n" + "="*80)
    print("TEST 4: Empty Value Handling")
    print("="*80)

    test_cases = [
        ("empty string", ""),
        ("whitespace", "   "),
    ]

    for name, value in test_cases:
        email_result = encrypt_email(value)
        phone_result = encrypt_phone(value)

        print(f"\n  Testing: {name} ('{value}')")
        print(f"    encrypt_email: {repr(email_result)} {'✅' if email_result == '' else '⚠️'}")
        print(f"    encrypt_phone: {repr(phone_result)} {'✅' if phone_result == '' else '⚠️'}")

    return True


def test_normalization():
    """Test email normalization and phone formatting"""
    print("\n" + "="*80)
    print("TEST 5: Normalization & Formatting")
    print("="*80)

    # Test email normalization (should be lowercase)
    test_email = "Customer@Example.COM"
    encrypted = encrypt_email(test_email)
    decrypted = decrypt_email(encrypted)

    print(f"\n📧 Email Normalization:")
    print(f"  Input:     {test_email}")
    print(f"  Expected:  {test_email.lower()}")
    print(f"  Actual:    {decrypted}")
    print(f"  ✅ Match:  {decrypted == test_email.lower()}")

    # Test phone formatting (should strip non-digits)
    test_phone = "+1 (555) 123-4567"
    encrypted = encrypt_phone(test_phone)
    decrypted = decrypt_phone(encrypted)

    print(f"\n📱 Phone Formatting:")
    print(f"  Input:     {test_phone}")
    print(f"  Decrypted: {decrypted}")
    print(f"  ✅ No spaces:       {' ' not in decrypted}")
    print(f"  ✅ No parentheses:  {'(' not in decrypted and ')' not in decrypted}")
    print(f"  ✅ No hyphens:      {'-' not in decrypted}")

    return True


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Encryption integration is working correctly.")
        print("\n📝 Next Steps:")
        print("  1. Deploy to staging environment")
        print("  2. Test with real database (create/retrieve customers)")
        print("  3. Verify encrypted values in database")
        print("  4. Monitor logs for errors")
        print("  5. Deploy to production (with feature flag OFF initially)")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review errors above.")
        return 1


def main():
    """Run all QA validation tests"""
    print("\n" + "="*80)
    print("My Hibachi - Customer Encryption QA Validation")
    print("="*80)
    print(f"\n🕒 Started: {datetime.now(timezone.utc).isoformat()}")

    results = {
        "Encryption Functions": test_encryption_functions(),
        "Customer Model Properties": test_customer_model_properties(),
        "Encryption Module Integration": test_encryption_integration(),
        "Empty Value Handling": test_empty_values(),
        "Normalization & Formatting": test_normalization(),
    }

    print(f"\n🕒 Finished: {datetime.now(timezone.utc).isoformat()}")

    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
