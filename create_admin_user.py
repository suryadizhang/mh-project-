"""
Create Admin User Script for MyHibachi Production
Run this on the server to create a test admin user.

Usage:
    ADMIN_PASSWORD=YourSecurePassword python create_admin_user.py

Environment Variables:
    ADMIN_EMAIL     - Admin email (default: admin@myhibachichef.com)
    ADMIN_PASSWORD  - Admin password (REQUIRED - must be set via env var)
    ADMIN_FIRST_NAME - First name (default: Admin)
    ADMIN_LAST_NAME  - Last name (default: MyHibachi)
"""

import os
import sys
from uuid import uuid4

from passlib.context import CryptContext

# Password hashing (same as the app)
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12
)

# Admin user details from environment variables
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@myhibachichef.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_FIRST_NAME = os.getenv("ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST_NAME = os.getenv("ADMIN_LAST_NAME", "MyHibachi")

# Validate password is provided
if not ADMIN_PASSWORD:
    print("ERROR: ADMIN_PASSWORD environment variable is required!")
    print("Usage: ADMIN_PASSWORD=YourSecurePassword python create_admin_user.py")
    sys.exit(1)

# Hash the password
password_hash = pwd_context.hash(ADMIN_PASSWORD)

print(f"Creating admin user: {ADMIN_EMAIL}")
print(f"Password hash: {password_hash[:50]}...")

# Generate UUIDs
user_id = str(uuid4())
role_id = str(uuid4())
user_role_id = str(uuid4())

print(f"User ID: {user_id}")
print(f"Role ID: {role_id}")

# SQL to create user, role, and assignment
SQL_CREATE_USER = f"""
-- First, check if user already exists
DO $$
BEGIN
    -- Create admin role if not exists
    INSERT INTO identity.roles (id, name, description, role_type, is_system_role, is_active, created_at, updated_at)
    VALUES (
        '{role_id}'::uuid,
        'super_admin',
        'Super Administrator with full system access',
        'super_admin',
        TRUE,
        TRUE,
        NOW(),
        NOW()
    )
    ON CONFLICT (name) DO NOTHING;

    -- Create admin user if not exists
    INSERT INTO identity.users (id, email, password_hash, first_name, last_name, status, is_verified, user_metadata, created_at, updated_at)
    VALUES (
        '{user_id}'::uuid,
        '{ADMIN_EMAIL}',
        '{password_hash}',
        '{ADMIN_FIRST_NAME}',
        '{ADMIN_LAST_NAME}',
        'active',
        TRUE,
        '{{}}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (email) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        status = 'active',
        is_verified = TRUE,
        updated_at = NOW();

    RAISE NOTICE 'Admin user created/updated successfully';
END $$;

-- Get the actual user and role IDs for the assignment
DO $$
DECLARE
    v_user_id uuid;
    v_role_id uuid;
BEGIN
    -- Get user ID
    SELECT id INTO v_user_id FROM identity.users WHERE email = '{ADMIN_EMAIL}';

    -- Get role ID (super_admin)
    SELECT id INTO v_role_id FROM identity.roles WHERE name = 'super_admin';

    -- Create user-role assignment if not exists
    IF v_user_id IS NOT NULL AND v_role_id IS NOT NULL THEN
        INSERT INTO identity.user_roles (id, user_id, role_id, assigned_at, assigned_by)
        VALUES (
            '{user_role_id}'::uuid,
            v_user_id,
            v_role_id,
            NOW(),
            NULL
        )
        ON CONFLICT (user_id, role_id) DO NOTHING;

        RAISE NOTICE 'User-role assignment created for user % with role %', v_user_id, v_role_id;
    ELSE
        RAISE NOTICE 'Could not find user (%) or role (%)', v_user_id, v_role_id;
    END IF;
END $$;

-- Verify the setup
SELECT
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.status,
    u.is_verified,
    r.name as role_name,
    r.role_type
FROM identity.users u
LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
LEFT JOIN identity.roles r ON ur.role_id = r.id
WHERE u.email = '{ADMIN_EMAIL}';
"""

print("\n--- SQL to execute ---")
print(SQL_CREATE_USER)
print("\n--- End SQL ---")

# Save to file
with open("/tmp/create_admin_user.sql", "w") as f:
    f.write(SQL_CREATE_USER)

print("\nSQL saved to /tmp/create_admin_user.sql")
print("\nCredentials:")
print(f"  Email: {ADMIN_EMAIL}")
print(f"  Password: (set via ADMIN_PASSWORD environment variable)")
print("\nTo run the SQL:")
print("  psql -d myhibachi_production -f /tmp/create_admin_user.sql")
