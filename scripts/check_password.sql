-- Check password hash for the super admin user
SELECT
    email,
    password_hash IS NOT NULL as has_password,
    length(password_hash) as hash_length,
    CASE
        WHEN password_hash LIKE '$2a$%' THEN 'bcrypt'
        WHEN password_hash LIKE '$2b$%' THEN 'bcrypt'
        WHEN password_hash LIKE '$argon2%' THEN 'argon2'
        WHEN password_hash LIKE 'pbkdf2%' THEN 'pbkdf2'
        ELSE 'unknown'
    END as hash_type,
    is_super_admin,
    status
FROM identity.users
WHERE email = 'suryadizhang.swe@gmail.com';
