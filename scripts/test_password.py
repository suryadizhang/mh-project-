#!/usr/bin/env python3
"""
Test password verification for the super admin user
"""
import sys

sys.path.insert(
    0, "/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/src"
)

import os

import bcrypt
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC", "postgresql://localhost/myhibachi_production"
)
# Remove async driver if present
DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2").replace(
    "+asyncpg", ""
)

print(f"Using database: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(
        text(
            """
        SELECT email, password_hash, is_super_admin, status
        FROM identity.users
        WHERE email = 'suryadizhang.swe@gmail.com'
    """
        )
    )
    row = result.fetchone()

    if not row:
        print("ERROR: User not found!")
        sys.exit(1)

    email, password_hash, is_super_admin, status = row
    print(f"User: {email}")
    print(f"Has password hash: {password_hash is not None}")
    print(f"Hash length: {len(password_hash) if password_hash else 0}")
    print(f"Hash prefix: {password_hash[:10] if password_hash else 'N/A'}...")
    print(f"Is super admin: {is_super_admin}")
    print(f"Status: {status}")

    # Test password verification
    test_password = "REDACTED_PASSWORD"

    if password_hash:
        try:
            result = bcrypt.checkpw(
                test_password.encode("utf-8"), password_hash.encode("utf-8")
            )
            print(
                f"\nPassword '{test_password}' verification result: {result}"
            )
        except Exception as e:
            print(f"\nPassword verification error: {e}")
    else:
        print("\nNo password hash stored!")

print("\nDone.")
