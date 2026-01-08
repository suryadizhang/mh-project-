"""
Reset password for super admin user.
Creates a bcrypt hash for the new password and outputs SQL to update it.
"""

import bcrypt

# New password - change this to your desired password
NEW_PASSWORD = "REDACTED_PASSWORD"

# Hash the password using bcrypt (same as the app does)
password_bytes = NEW_PASSWORD.encode("utf-8")
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt)
hashed_str = hashed.decode("utf-8")

print(f"New Password: {NEW_PASSWORD}")
print(f"New Hash: {hashed_str}")
print()
print("SQL to update password:")
print(
    f"UPDATE identity.users SET password_hash = '{hashed_str}', updated_at = NOW() WHERE email = 'suryadizhang.swe@gmail.com';"
)
