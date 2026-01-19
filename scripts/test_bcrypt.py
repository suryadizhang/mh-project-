#!/usr/bin/env python3
"""
Direct bcrypt password test - no database needed.
Run with: python3 test_bcrypt.py <password> <hash>
"""
import os
import sys

import bcrypt

# Get password from command line or environment
test_password = os.getenv("TEST_PASSWORD") or (
    sys.argv[1] if len(sys.argv) > 1 else None
)

# Hash from command line argument or environment
stored_hash = os.getenv("TEST_HASH") or (
    sys.argv[2] if len(sys.argv) > 2 else None
)

if not test_password or not stored_hash:
    print("ERROR: Missing password or hash!")
    print("Usage: python3 test_bcrypt.py <password> <hash>")
    print("   OR: TEST_PASSWORD=xxx TEST_HASH=yyy python3 test_bcrypt.py")
    sys.exit(1)
    exit(1)

print(f"Testing password: {test_password}")
print(f"Hash length: {len(stored_hash)}")
print(f"Hash prefix: {stored_hash[:10]}...")

try:
    result = bcrypt.checkpw(
        test_password.encode("utf-8"), stored_hash.encode("utf-8")
    )
    print(f"\n{'='*50}")
    print(
        f"RESULT: {'✅ PASSWORD MATCHES!' if result else '❌ PASSWORD DOES NOT MATCH'}"
    )
    print(f"{'='*50}")
except Exception as e:
    print(f"ERROR: {e}")
