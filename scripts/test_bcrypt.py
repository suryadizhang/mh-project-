#!/usr/bin/env python3
"""
Direct bcrypt password test - no database needed.
Run with: python3 test_bcrypt.py
"""
import bcrypt

# Password to test
test_password = "13Agustus!!"

# Hash from database
stored_hash = "$2b$12$0a.1alaOC6JrBaeJ21lc5OtosO2ATibApKBNLhtnPT1S1lI55PWl6"

if stored_hash == "HASH_PLACEHOLDER":
    print("ERROR: Update stored_hash with the actual hash from database!")
    print(
        "Run: sudo -u postgres psql -d myhibachi_production -t -c \"SELECT password_hash FROM identity.users WHERE email='suryadizhang.swe@gmail.com';\""
    )
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
