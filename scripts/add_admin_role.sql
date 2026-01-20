-- Add admin role to test@myhibachi.com user
INSERT INTO identity.user_roles (user_id, role_id)
VALUES ('a718947d-14d5-44c5-965f-f45bd124c8f2', '8cae9a5d-2d2a-475d-b575-92becf239f90')
ON CONFLICT DO NOTHING;

-- Verify the role was added
SELECT u.id, u.email, r.name as role_name
FROM identity.users u
LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
LEFT JOIN identity.roles r ON ur.role_id = r.id
WHERE u.email = 'test@myhibachi.com';
