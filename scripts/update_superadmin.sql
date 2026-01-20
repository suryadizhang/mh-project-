-- Update super admin password for suryadizhang.swe@gmail.com
-- Password: 13Agustus!
-- Generated hash: $2b$12$L3jqASGPDOjgqkgVjarBhOlj2X.auE7MWDpc/Ua7KKcMsgkh7hymu

UPDATE identity.users
SET password_hash = '$2b$12$L3jqASGPDOjgqkgVjarBhOlj2X.auE7MWDpc/Ua7KKcMsgkh7hymu',
    updated_at = NOW()
WHERE email = 'suryadizhang.swe@gmail.com';

-- Verify the update
SELECT id, email, status, is_super_admin, created_at, updated_at
FROM identity.users
WHERE email = 'suryadizhang.swe@gmail.com';
