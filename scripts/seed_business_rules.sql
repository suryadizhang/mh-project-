-- ============================================================================
-- BUSINESS RULES SEED SCRIPT
-- ============================================================================
-- Purpose: Seed business_rules table with Terms & Conditions from website
-- Source of Truth: apps/customer/src/app/terms/page.tsx
-- Last Verified: 2025-11-12
-- Total Rules: 15 key business policies
-- 
-- IMPORTANT: This data is DYNAMIC and subject to change!
-- - Terms & Conditions may be updated due to legal/policy changes
-- - Cancellation policies can change based on business needs
-- - Payment terms may be adjusted
-- - Use auto-sync service to detect changes from TypeScript source
-- - Manual updates via admin UI will override auto-sync
-- ============================================================================

-- Clean slate: delete all existing rules
TRUNCATE TABLE business_rules RESTART IDENTITY CASCADE;

-- ========================================================================
-- CATEGORY: CANCELLATION POLICY
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('CANCELLATION',
 'Full Refund Period',
 'Full refund including $100 deposit if canceled 7 or more days before event',
 '{"days_before": 7, "refund_percentage": 100, "includes_deposit": true}'::jsonb,
 true, 1),

('CANCELLATION',
 'No Refund Period',
 '$100 deposit is non-refundable if canceled less than 7 days before event',
 '{"days_before": 7, "deposit_refundable": false, "balance_refundable": false}'::jsonb,
 true, 1),

('CANCELLATION',
 'Emergency Cancellations',
 'Cancellations due to severe weather, natural disasters, or other circumstances beyond our control will be handled on a case-by-case basis',
 '{"applies_to": ["severe weather", "natural disasters", "force majeure"], "review_required": true}'::jsonb,
 true, 1);

-- ========================================================================
-- CATEGORY: RESCHEDULING POLICY
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('RESCHEDULING',
 'First Reschedule Free',
 'One free reschedule allowed within 48 hours of booking',
 '{"first_reschedule_free": true, "time_window_hours": 48, "subsequent_fee": 100}'::jsonb,
 true, 1),

('RESCHEDULING',
 'Additional Reschedule Fee',
 '$100 fee applies to any reschedules after the first one',
 '{"fee_amount": 100, "applies_after_first": true}'::jsonb,
 true, 1),

('RESCHEDULING',
 'Advance Notice Required',
 'Minimum 7 days advance notice recommended for rescheduling',
 '{"recommended_notice_days": 7, "subject_to_availability": true}'::jsonb,
 true, 1),

('RESCHEDULING',
 'Weather Rescheduling',
 'No fee for weather-related rescheduling if proper notice is given',
 '{"weather_exception": true, "fee_waived": true, "notice_required": true}'::jsonb,
 true, 1);

-- ========================================================================
-- CATEGORY: PAYMENT POLICY
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('PAYMENT',
 'Deposit Requirement',
 '$100 refundable deposit required to secure booking',
 '{"deposit_amount": 100, "refundable": true, "conditions": "if canceled 7+ days before event"}'::jsonb,
 true, 1),

('PAYMENT',
 'Deposit Applied to Final Bill',
 'Deposit is deducted from final bill on event day',
 '{"deducted_from_balance": true, "applied_on_event_day": true}'::jsonb,
 true, 1),

('PAYMENT',
 'Final Payment Due',
 'Remaining balance due on event date',
 '{"due_date": "event_day", "payment_methods": ["credit_card", "venmo_business", "zelle_business", "cash"]}'::jsonb,
 true, 1),

('PAYMENT',
 'Accepted Payment Methods',
 'We accept Credit Cards (Visa, MasterCard, American Express), Venmo Business, Zelle Business, and Cash',
 '{"methods": ["credit_card", "venmo_business", "zelle_business", "cash"], "processor": "Stripe"}'::jsonb,
 true, 1);

-- ========================================================================
-- CATEGORY: BOOKING REQUIREMENTS
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('BOOKING',
 'Advance Booking Required',
 'All bookings must be made at least 48 hours in advance',
 '{"minimum_hours": 48, "recommended_days": 7, "peak_season_days": 14}'::jsonb,
 true, 1),

('BOOKING',
 'Final Guest Count',
 'Final guest count must be provided 48 hours before the event',
 '{"deadline_hours": 48, "required": true}'::jsonb,
 true, 1);

-- ========================================================================
-- CATEGORY: SERVICE MINIMUMS
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('PRICING',
 'Party Minimum',
 '$550 total minimum per event (approximately 10 adults)',
 '{"minimum_amount": 550, "approximate_guests": 10, "currency": "USD"}'::jsonb,
 true, 1),

('PRICING',
 'Travel Fee Structure',
 'First 30 miles from our location are free. After that, $2 per mile',
 '{"free_miles": 30, "per_mile_rate": 2, "flexible": true}'::jsonb,
 true, 1);

-- ========================================================================
-- CATEGORY: LIABILITY
-- ========================================================================

INSERT INTO business_rules (rule_type, title, content, value, is_active, version) VALUES
('LIABILITY',
 'Liability Limitation',
 'Our liability is limited to the total amount paid for services',
 '{"limited_to": "total_service_cost", "exclusions": ["client_negligence", "undisclosed_allergies", "weather_disruptions", "venue_issues"]}'::jsonb,
 true, 1);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 
    rule_type,
    COUNT(*) as rule_count,
    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
FROM business_rules
GROUP BY rule_type
ORDER BY rule_type;

-- Total should be 15 rules
SELECT COUNT(*) as total_rules FROM business_rules WHERE is_active = true;

-- Show all rules with their JSON values
SELECT 
    rule_type,
    title,
    value->>'fee_amount' as fee,
    value->>'days_before' as days,
    value->>'minimum_amount' as minimum
FROM business_rules
WHERE is_active = true
ORDER BY rule_type, title;
