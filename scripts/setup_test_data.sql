-- Phase 2.5: Setup Test Data for End-to-End Testing
-- Run this before making test calls

-- 1. Create test customer with phone +12103884155
INSERT INTO public.customers (
    id,
    user_id,
    phone, 
    email,
    name,
    stripe_customer_id,
    created_at,
    updated_at
) VALUES (
    'test-customer-surya-' || EXTRACT(EPOCH FROM NOW())::TEXT,
    'test-user-surya-' || EXTRACT(EPOCH FROM NOW())::TEXT,
    '+12103884155',
    'surya@myhibachi.com',
    'Surya Test',
    'cus_test_' || EXTRACT(EPOCH FROM NOW())::TEXT,
    NOW(),
    NOW()
) ON CONFLICT (phone) DO UPDATE 
SET email = EXCLUDED.email,
    name = EXCLUDED.name,
    updated_at = NOW()
RETURNING id, phone, email, name;

-- 2. Create test booking for tomorrow at 7 PM
INSERT INTO public.bookings (
    customer_name,
    customer_email,
    customer_phone,
    event_date,
    event_time,
    event_address,
    guest_count,
    adult_count,
    child_count,
    total_amount,
    status,
    created_at,
    updated_at
) VALUES (
    'Surya Test',
    'surya@myhibachi.com',
    '+12103884155',
    (NOW() + INTERVAL '1 day')::DATE,
    '19:00:00'::TIME,
    '123 Test St, Sacramento, CA 95814',
    4,
    3,
    1,
    600.00,
    'confirmed',
    NOW(),
    NOW()
)
RETURNING id, event_date, event_time, guest_count, status;

-- 3. Verify test data
SELECT 
    'Customer Created' as type,
    c.id,
    c.phone,
    c.email,
    c.name
FROM public.customers c
WHERE c.phone = '+12103884155';

SELECT 
    'Booking Created' as type,
    b.id,
    b.event_date,
    b.event_time,
    b.guest_count,
    b.status
FROM public.bookings b
WHERE b.customer_phone = '+12103884155'
ORDER BY b.event_date DESC
LIMIT 1;
