SELECT email, first_name, last_name, is_super_admin, status, LEFT(password_hash, 15) as hash_prefix FROM identity.users ORDER BY created_at;
