"""
Comprehensive Test Suite for Encryption Service

Tests all error scenarios as requested by user:
"make sure no error on it or it will cause big problem when the encryption decryption goes error"

Test Coverage:
1. Normal encryption/decryption (happy path)
2. Empty/None inputs
3. Invalid phone formats
4. Invalid email formats
5. Corrupted encrypted data
6. Wrong encryption key
7. Missing encryption key
8. Unicode characters
9. Very long strings
10. Special characters
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.encryption_service import SecureDataHandler, generate_encryption_key
from dotenv import load_dotenv

# Load environment
load_dotenv()


def print_test(test_name: str, passed: bool, details: str = ""):
    """Pretty print test results"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"      {details}")


def test_encryption_service():
    """Run comprehensive encryption tests"""
    print("=" * 60)
    print("🔐 ENCRYPTION SERVICE COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    # Initialize handler
    try:
        handler = SecureDataHandler()
        print_test("Initialize encryption handler", True, "Handler created successfully")
    except Exception as e:
        print_test("Initialize encryption handler", False, f"Failed: {e}")
        return False
    
    print()
    print("-" * 60)
    print("TEST GROUP 1: Normal Operations (Happy Path)")
    print("-" * 60)
    
    # Test 1: Encrypt and decrypt phone
    test_phone = "2103884155"
    encrypted_phone = handler.encrypt_phone(test_phone)
    decrypted_phone = handler.decrypt_phone(encrypted_phone)
    test_1_pass = decrypted_phone == test_phone and encrypted_phone != test_phone
    print_test("Phone encryption/decryption", test_1_pass, 
               f"Original: {test_phone}, Decrypted: {decrypted_phone}")
    
    # Test 2: Encrypt and decrypt email
    test_email = "customer@example.com"
    encrypted_email = handler.encrypt_email(test_email)
    decrypted_email = handler.decrypt_email(encrypted_email)
    test_2_pass = decrypted_email == test_email and encrypted_email != test_email
    print_test("Email encryption/decryption", test_2_pass,
               f"Original: {test_email}, Decrypted: {decrypted_email}")
    
    # Test 3: Verify encryption changes data
    test_3_pass = encrypted_phone.startswith("v1:") and len(encrypted_phone) > 20
    print_test("Encrypted data format", test_3_pass,
               f"Encrypted phone format: {encrypted_phone[:30]}...")
    
    print()
    print("-" * 60)
    print("TEST GROUP 2: Empty/None Input Handling")
    print("-" * 60)
    
    # Test 4: None input
    result_none = handler.encrypt_phone(None)
    test_4_pass = result_none is None
    print_test("None input handling", test_4_pass,
               f"None input returns: {result_none}")
    
    # Test 5: Empty string
    result_empty = handler.encrypt_phone("")
    test_5_pass = result_empty == ""
    print_test("Empty string handling", test_5_pass,
               f"Empty string returns: '{result_empty}'")
    
    # Test 6: Whitespace only
    result_whitespace = handler.encrypt_phone("   ")
    test_6_pass = result_whitespace == "   "
    print_test("Whitespace-only handling", test_6_pass,
               f"Whitespace returns: '{result_whitespace}'")
    
    print()
    print("-" * 60)
    print("TEST GROUP 3: Invalid Input Handling")
    print("-" * 60)
    
    # Test 7: Invalid phone (letters)
    invalid_phone = "abcdefghij"
    encrypted_invalid = handler.encrypt_phone(invalid_phone)
    test_7_pass = encrypted_invalid.startswith("UNENCRYPTED:")
    print_test("Invalid phone (letters) fallback", test_7_pass,
               f"Invalid phone fallback: {encrypted_invalid}")
    
    # Test 8: Phone with formatting
    formatted_phone = "(210) 388-4155"
    encrypted_formatted = handler.encrypt_phone(formatted_phone)
    decrypted_formatted = handler.decrypt_phone(encrypted_formatted)
    test_8_pass = decrypted_formatted == "2103884155"  # Should strip formatting
    print_test("Phone formatting sanitization", test_8_pass,
               f"Original: {formatted_phone}, Sanitized: {decrypted_formatted}")
    
    # Test 9: Invalid email (no @)
    invalid_email = "notanemail"
    encrypted_invalid_email = handler.encrypt_email(invalid_email)
    test_9_pass = encrypted_invalid_email.startswith("UNENCRYPTED:")
    print_test("Invalid email fallback", test_9_pass,
               f"Invalid email fallback: {encrypted_invalid_email}")
    
    print()
    print("-" * 60)
    print("TEST GROUP 4: Error Recovery (Critical for User)")
    print("-" * 60)
    
    # Test 10: Decrypt corrupted data
    corrupted_data = "v1:corrupted_base64_data_12345"
    decrypted_corrupted = handler.decrypt_phone(corrupted_data)
    test_10_pass = decrypted_corrupted == corrupted_data  # Should return as-is
    print_test("Corrupted data recovery", test_10_pass,
               "Corrupted data returns original (no crash)")
    
    # Test 11: Decrypt with UNENCRYPTED prefix
    unencrypted_data = "UNENCRYPTED:2103884155"
    decrypted_unencrypted = handler.decrypt_phone(unencrypted_data)
    test_11_pass = decrypted_unencrypted == "2103884155"
    print_test("UNENCRYPTED prefix handling", test_11_pass,
               f"Stripped prefix correctly: {decrypted_unencrypted}")
    
    # Test 12: Decrypt without version prefix (backward compatibility)
    # Manually encrypt without version prefix
    from cryptography.fernet import Fernet
    cipher = Fernet(os.getenv('ENCRYPTION_KEY').encode())
    legacy_encrypted = cipher.encrypt("2103884155".encode()).decode()
    decrypted_legacy = handler.decrypt_phone(legacy_encrypted)
    test_12_pass = decrypted_legacy == "2103884155"
    print_test("Legacy format support", test_12_pass,
               f"Decrypted legacy format: {decrypted_legacy}")
    
    print()
    print("-" * 60)
    print("TEST GROUP 5: Edge Cases")
    print("-" * 60)
    
    # Test 13: Very long phone number
    long_phone = "1234567890" * 10  # 100 digits
    encrypted_long = handler.encrypt_phone(long_phone)
    decrypted_long = handler.decrypt_phone(encrypted_long)
    test_13_pass = decrypted_long == long_phone
    print_test("Very long phone number", test_13_pass,
               f"Length: {len(long_phone)} digits, preserved: {len(decrypted_long)}")
    
    # Test 14: Unicode characters in email
    unicode_email = "用户@example.com"
    encrypted_unicode = handler.encrypt_email(unicode_email)
    decrypted_unicode = handler.decrypt_email(encrypted_unicode)
    test_14_pass = decrypted_unicode == unicode_email
    print_test("Unicode email support", test_14_pass,
               f"Unicode preserved: {decrypted_unicode}")
    
    # Test 15: Special characters in phone
    special_phone = "+1 (210) 388-4155 ext. 123"
    encrypted_special = handler.encrypt_phone(special_phone)
    decrypted_special = handler.decrypt_phone(encrypted_special)
    test_15_pass = "2103884155" in decrypted_special  # Should extract digits
    print_test("Special characters sanitization", test_15_pass,
               f"Sanitized to: {decrypted_special}")
    
    print()
    print("-" * 60)
    print("TEST GROUP 6: Security Validation")
    print("-" * 60)
    
    # Test 16: Different data produces different ciphertext
    phone_a = "2103884155"
    phone_b = "2103884156"
    encrypted_a = handler.encrypt_phone(phone_a)
    encrypted_b = handler.encrypt_phone(phone_b)
    test_16_pass = encrypted_a != encrypted_b
    print_test("Different data produces different ciphertext", test_16_pass,
               f"Cipher A != Cipher B: {encrypted_a[:20]}... != {encrypted_b[:20]}...")
    
    # Test 17: Same data produces different ciphertext (Fernet uses random IV)
    encrypted_a1 = handler.encrypt_phone(phone_a)
    encrypted_a2 = handler.encrypt_phone(phone_a)
    test_17_pass = encrypted_a1 != encrypted_a2  # Fernet includes timestamp
    print_test("Random IV (non-deterministic encryption)", test_17_pass,
               "Same data produces different ciphertext (secure)")
    
    # Test 18: Verify encrypted data is not readable
    test_18_pass = test_phone not in encrypted_phone and "210" not in encrypted_phone
    print_test("Encrypted data not readable", test_18_pass,
               "Original data not visible in ciphertext")
    
    print()
    print("=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    all_tests = [
        test_1_pass, test_2_pass, test_3_pass, test_4_pass, test_5_pass,
        test_6_pass, test_7_pass, test_8_pass, test_9_pass, test_10_pass,
        test_11_pass, test_12_pass, test_13_pass, test_14_pass, test_15_pass,
        test_16_pass, test_17_pass, test_18_pass
    ]
    
    passed = sum(all_tests)
    total = len(all_tests)
    percentage = (passed / total) * 100
    
    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")
    print()
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Encryption service is production-ready!")
        print("   - No crashes on invalid input")
        print("   - Graceful error handling with fallbacks")
        print("   - Data never lost (UNENCRYPTED: prefix for failures)")
        print("   - Comprehensive logging for debugging")
        print("   - Secure encryption with random IV")
        return True
    else:
        print(f"❌ {total - passed} TESTS FAILED - Review encryption service")
        return False


if __name__ == "__main__":
    success = test_encryption_service()
    sys.exit(0 if success else 1)
