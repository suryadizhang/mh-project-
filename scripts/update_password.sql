-- Update password for super admin user
UPDATE identity.users
SET password_hash = '$2b$12$EgTDOVNZBK0cAjklxcD1Ie3ODEBqOkLn9GqLVCHQKpZL1WJaQ/HnS',
    updated_at = NOW()
WHERE email = 'suryadizhang.swe@gmail.com';

-- Verify the update
SELECT email, LEFT(password_hash, 30) as hash_prefix, updated_at
FROM identity.users
WHERE email = 'suryadizhang.swe@gmail.com';
