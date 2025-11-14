-- ============================================================================
-- FAQ ITEMS SEED SCRIPT
-- ============================================================================
-- Purpose: Seed faq_items table with verified FAQs from customer website
-- Source of Truth: apps/customer/src/data/faqsData.ts
-- Last Verified: 2025-11-12
-- Total FAQs: 35 items across 8 categories
-- 
-- IMPORTANT: This data is DYNAMIC and subject to change!
-- - FAQs can be added, modified, or removed
-- - Answers may be updated based on policy changes
-- - Use auto-sync service to detect changes from TypeScript source
-- - Manual updates via admin UI override auto-sync
-- ============================================================================

-- Delete existing FAQ data for clean re-seed
TRUNCATE TABLE faq_items RESTART IDENTITY CASCADE;

-- ========================================================================
-- CATEGORY: Pricing & Minimums (4 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active, created_at, last_updated) VALUES
('How much does My Hibachi Chef cost?',
 '$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.',
 'Pricing & Minimums',
 0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('Is there a minimum party size?',
 'Yes — $550 total minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.',
 'Pricing & Minimums',
 0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('Is tipping expected?',
 'Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost. You can tip cash or via Venmo/Zelle Business.',
 'Pricing & Minimums',
 0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('Do you charge travel fees?',
 'First 30 miles from our location are free. After that, $2 per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.',
 'Pricing & Minimums',
 0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

    -- ========================================================================
    -- CATEGORY: Menu & Upgrades (7 FAQs)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'What''s included in the hibachi menu?',
        'Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.',
        'Menu & Upgrades',
        'Included Items',
        ARRAY['2 proteins', 'chicken', 'steak', 'shrimp', 'calamari', 'tofu', 'rice', 'vegetables', 'sake'],
        ARRAY['menu', 'included', 'proteins', 'chicken', 'steak', 'shrimp', 'calamari', 'tofu', 'rice', 'vegetables', 'salad', 'sauces', 'sake'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What are the premium protein upgrades?',
        'For premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5 per person, while Lobster Tail is +$15 per person. These upgrade your existing protein choices to premium options.',
        'Menu & Upgrades',
        'Premium Upgrades',
        ARRAY['upgrades', 'salmon +$5', 'scallops +$5', 'filet +$5', 'lobster +$15', 'premium proteins'],
        ARRAY['premium', 'upgrade', 'salmon', 'scallops', 'filet', 'mignon', 'lobster', 'tail', 'protein', '$5', '$15'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What are the kids'' portions and pricing?',
        '$30 per child (6-12 years) — same 2-protein selection as adults. Ages 5 & under eat free with adult purchase (1 protein, small rice portion).',
        'Menu & Upgrades',
        'Kids'' Portions',
        ARRAY['kids', '$30', '6-12 years', 'free under 5', '2 proteins'],
        ARRAY['kids', 'children', 'child', '$30', 'free', '5 under', '6-12', 'portions', 'proteins'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Do you serve sake and alcohol?',
        'Yes! We provide sake for guests 21+ as part of the standard experience. We don''t provide other alcohol — you''re welcome to supply your own beer, wine, or cocktails.',
        'Menu & Upgrades',
        'Add‑ons & Sides',
        ARRAY['sake', 'alcohol', '21+', 'byob', 'beer', 'wine'],
        ARRAY['sake', 'alcohol', 'drinks', 'beverages', '21+', 'byob', 'beer', 'wine', 'cocktails', 'bring'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Can I add a third protein or more?',
        'Yes! Each guest normally gets 2 proteins, but you can add a 3rd protein for +$10 per person. This is an additional option that gives you more food, not an upgrade. If you want the 3rd protein to be a premium option (Filet Mignon or Lobster Tail), that would be the +$10 for the additional protein plus the premium upgrade cost. Contact us at cs@myhibachichef.com to customize your menu.',
        'Menu & Upgrades',
        'Add‑ons & Sides',
        ARRAY['third protein', 'additional protein', 'add-on', '+$10', 'more food'],
        ARRAY['third', '3rd', 'protein', 'additional', 'more', 'extra', '$10', 'customize', 'menu'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What additional enhancements can I add to my menu?',
        'We offer several delicious add-on options: Yakisoba Noodles (Japanese-style lo mein), Extra Fried Rice, Extra Vegetables (mixed seasonal vegetables), and Edamame (steamed soybeans with sea salt) are all +$5 each. Gyoza (pan-fried Japanese dumplings) and 3rd Protein (add a third protein to your meal) are +$10 each. These can be ordered per person or shared family-style.',
        'Menu & Upgrades',
        'Add‑ons & Sides',
        ARRAY['enhancements', 'add-ons', 'yakisoba noodles +$5', 'extra rice +$5', 'extra vegetables +$5', 'edamame +$5', 'gyoza +$10', '3rd protein +$10', 'sides'],
        ARRAY['enhancements', 'add-ons', 'extras', 'yakisoba', 'noodles', 'rice', 'vegetables', 'edamame', 'gyoza', 'dumplings', 'sides', '$5', '$10'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Can guests choose different proteins?',
        'Absolutely! Each guest can choose their own 2 proteins from: Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu. Everyone can have different selections. Premium upgrades (Filet Mignon +$5, Lobster Tail +$15) are also individual choices.',
        'Menu & Upgrades',
        'Included Items',
        ARRAY['individual choices', 'different proteins', 'personalized'],
        ARRAY['individual', 'different', 'personalized', 'custom', 'choice', 'proteins', 'select', 'everyone'],
        'high',
        ARRAY['/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Booking & Payments (5 FAQs)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'How do I book My Hibachi Chef?',
        'Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit (refundable if canceled 7+ days before event).',
        'Booking & Payments',
        'How to Book',
        ARRAY['booking', 'online', 'text', '48 hours', '$100 deposit', 'refundable'],
        ARRAY['book', 'booking', 'reserve', 'online', 'website', 'text', 'phone', '48 hours', 'advance', 'deposit', '$100'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What''s the deposit policy?',
        '$100 refundable deposit secures your date and is deducted from final bill (refundable if canceled 7+ days before event). Remaining balance due on event date. Accept Venmo Business, Zelle Business, Cash, Credit Card.',
        'Booking & Payments',
        'Deposits & Balance',
        ARRAY['$100 deposit', 'refundable', 'deducted', 'final bill'],
        ARRAY['deposit', '$100', 'refundable', 'secure', 'date', 'deducted', 'balance', 'payment', '7 days'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What payment methods do you accept?',
        'Venmo Business, Zelle Business, Cash, and Credit Card. Deposit paid online when booking. Balance due on event date or in advance.',
        'Booking & Payments',
        'Payment Methods',
        ARRAY['venmo', 'zelle', 'cash', 'credit card', 'online deposit'],
        ARRAY['payment', 'methods', 'venmo', 'zelle', 'cash', 'credit', 'card', 'deposit', 'balance', 'online'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'How far in advance should I book?',
        '48 hours minimum required. For weekends and holidays, recommend 1-2 weeks ahead. Text (916) 740-8768 to check availability.',
        'Booking & Payments',
        'Scheduling & Availability',
        ARRAY['48 hours minimum', 'weekends', 'holidays', '1-2 weeks'],
        ARRAY['advance', 'booking', '48 hours', 'minimum', 'weekends', 'holidays', 'availability', 'schedule'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Why is a deposit required?',
        'The $100 deposit confirms your reservation and helps us prepare fresh ingredients specifically for your party. It also ensures commitment from both sides and covers our preparation costs. The deposit is deducted from your final bill on party day.',
        'Booking & Payments',
        'Deposits & Balance',
        ARRAY['deposit explanation', 'reservation confirmation', 'preparation costs'],
        ARRAY['deposit', 'why', 'required', 'reservation', 'confirmation', 'ingredients', 'commitment', 'preparation'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Travel & Service Area (2 FAQs)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'Where do you serve?',
        'We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first 30 miles, then $2/mile.',
        'Travel & Service Area',
        'Coverage Radius',
        ARRAY['bay area', 'sacramento', 'san jose', 'free 30 miles'],
        ARRAY['service', 'area', 'location', 'bay area', 'sacramento', 'san jose', 'travel', 'free', '30 miles'],
        'high',
        ARRAY['/contact', '/menu'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Do you travel to my city?',
        'We serve the Bay Area, Sacramento, Central Valley, and coastal/mountain communities throughout Northern California. Text (916) 740-8768 with your zip code for confirmation.',
        'Travel & Service Area',
        'Coverage Radius',
        ARRAY['bay area', 'sacramento', 'central valley', 'zip code', 'confirmation'],
        ARRAY['travel', 'city', 'location', 'bay area', 'sacramento', 'central valley', 'northern california', 'zip code'],
        'high',
        ARRAY['/contact'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: On‑Site Setup & Requirements (5 FAQs)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'What space do you need for the hibachi setup?',
        'Clear area 68.3"L × 27.5"W × 41.3"H for our grill. Need level ground, outdoor space or well-ventilated indoor area, and table access so guests can watch the show.',
        'On‑Site Setup & Requirements',
        'Space & Ventilation',
        ARRAY['68x27x41 inches', 'level ground', 'outdoor', 'ventilated', 'table access'],
        ARRAY['space', 'grill', 'dimensions', '68', '27', '41', 'inches', 'level', 'ground', 'outdoor', 'ventilated', 'table'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'How should I arrange tables and seating?',
        'U-shape with chef''s grill at the open end so everyone watches the show. Two 8-foot tables seat ~10 people, three 6-foot tables handle 12-15 guests.',
        'On‑Site Setup & Requirements',
        'Table Setup',
        ARRAY['u-shape', '8-foot tables', '10 people', '6-foot tables', '12-15 guests'],
        ARRAY['tables', 'seating', 'arrangement', 'u-shape', '8-foot', '6-foot', '10 people', '12-15 guests', 'setup'],
        'high',
        ARRAY[],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Can you cook indoors?',
        'Outdoor preferred for safety, but indoor possible with high ceilings and excellent ventilation. Must handle smoke and propane safely. Email cs@myhibachichef.com to discuss indoor requirements.',
        'On‑Site Setup & Requirements',
        'Indoor vs Outdoor',
        ARRAY['outdoor preferred', 'indoor possible', 'high ceilings', 'ventilation', 'smoke'],
        ARRAY['indoor', 'outdoor', 'cooking', 'safety', 'ceilings', 'ventilation', 'smoke', 'propane'],
        'high',
        ARRAY[],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What do I need to provide?',
        'You provide: tables, chairs, plates, utensils, glasses, beverages (except sake), napkins. We bring: hibachi grill, food, cooking tools, propane, safety equipment, sake.',
        'On‑Site Setup & Requirements',
        'Tableware & Setup',
        ARRAY['tables', 'chairs', 'plates', 'utensils', 'glasses', 'napkins'],
        ARRAY['provide', 'host', 'tables', 'chairs', 'plates', 'utensils', 'glasses', 'beverages', 'napkins', 'setup'],
        'high',
        ARRAY[],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What time will the chef arrive?',
        'Our chef will arrive approximately 15-30 minutes before your scheduled party time for setup. Setup is quick and usually takes just a few minutes. We''ll confirm arrival time when we call to finalize details.',
        'On‑Site Setup & Requirements',
        'General',
        ARRAY['arrival time', '15-30 minutes early', 'setup time'],
        ARRAY['arrival', 'time', 'chef', '15-30 minutes', 'early', 'setup', 'schedule', 'party'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Dietary & Allergens (1 FAQ)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'Can you accommodate dietary restrictions?',
        'Yes! Vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance so our chef can prepare. Email cs@myhibachichef.com with specific needs.',
        'Dietary & Allergens',
        'Dietary Accommodations',
        ARRAY['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'halal', 'kosher', '48 hours'],
        ARRAY['dietary', 'restrictions', 'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'halal', 'kosher', 'allergies', '48 hours'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Policies (Cancellation, Weather, Refunds) (2 FAQs)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'What''s your cancellation policy?',
        'Full refund if canceled 7+ days before event. $100 deposit is refundable for cancellations 7+ days before event, non-refundable within 7 days. One free reschedule within 48 hours of booking; additional reschedules cost $100.',
        'Policies (Cancellation, Weather, Refunds)',
        'Cancellation & Changes',
        ARRAY['7 days', 'full refund', 'deposit refundable', 'free reschedule', '$100 fee'],
        ARRAY['cancellation', 'cancel', 'refund', '7 days', 'deposit', '$100', 'reschedule', 'free', 'fee'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'What happens if it rains?',
        'You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups — plan a backup covered area!',
        'Policies (Cancellation, Weather, Refunds)',
        'Weather / Backup Plan',
        ARRAY['rain', 'overhead covering', 'tent', 'patio', 'garage', 'no refund'],
        ARRAY['rain', 'weather', 'covering', 'tent', 'patio', 'garage', 'backup', 'outdoor', 'uncovered'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Kids & Special Occasions (1 FAQ)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'Do you do birthday parties and special events?',
        'Absolutely! Birthday parties are our specialty. Chefs make the show extra fun and family-friendly, accommodate dietary needs, and make the birthday person feel special. Book 48+ hours ahead!',
        'Kids & Special Occasions',
        'Birthdays/Anniversaries',
        ARRAY['birthday', 'special events', 'family-friendly', 'dietary needs', '48 hours'],
        ARRAY['birthday', 'party', 'special', 'events', 'family', 'kids', 'fun', 'dietary', 'anniversary'],
        'high',
        ARRAY[],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- CATEGORY: Contact & Response Times (1 FAQ)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'What''s the fastest way to reach you?',
        'Text (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Follow @my_hibachi_chef on Instagram and Facebook. Usually respond within 1-2 hours during business hours.',
        'Contact & Response Times',
        'Best Way to Reach',
        ARRAY['text', '916-740-8768', 'email', 'instagram', 'facebook', '1-2 hours'],
        ARRAY['contact', 'reach', 'text', 'phone', 'email', 'instagram', 'facebook', 'social', 'response', 'hours'],
        'high',
        ARRAY['/contact'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

    -- ========================================================================
    -- Additional FAQs (Safety & Miscellaneous)
    -- ========================================================================

    INSERT INTO faq_items (
        id, station_id, question, answer, category, subcategory,
        tags, keywords, confidence_level, source_urls,
        view_count, helpful_count, is_active, created_at, updated_at
    ) VALUES
    (
        gen_random_uuid(),
        main_station_id,
        'Is it safe to use propane for cooking in residential areas?',
        'Yes, absolutely safe! Our chefs are experienced professionals who follow strict safety protocols. We bring portable fire extinguishers to every event, perform propane leak checks, maintain safe distances from flammable objects, and ensure proper ventilation.',
        'On‑Site Setup & Requirements',
        'General',
        ARRAY['safety', 'propane', 'fire extinguisher', 'leak checks', 'protocols'],
        ARRAY['safety', 'safe', 'propane', 'residential', 'fire', 'extinguisher', 'leak', 'protocols', 'ventilation'],
        'high',
        ARRAY[],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    ),
    (
        gen_random_uuid(),
        main_station_id,
        'Can I get a receipt or invoice?',
        'Yes! We can provide receipts or invoices for deposit, remaining balance, and gratuity. Perfect for expense reimbursement or business events. Contact cs@myhibachichef.com to request documentation.',
        'Booking & Payments',
        'Deposits & Balance',
        ARRAY['receipt', 'invoice', 'business', 'expense reimbursement'],
        ARRAY['receipt', 'invoice', 'documentation', 'business', 'expense', 'reimbursement', 'deposit', 'balance'],
        'high',
        ARRAY['/BookUs'],
        0, 0, true,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    );

END $$;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify FAQs were seeded correctly:
SELECT 
    category,
    COUNT(*) as faq_count,
    STRING_AGG(DISTINCT subcategory, ', ' ORDER BY subcategory) as subcategories
FROM faq_items
WHERE station_id IN (SELECT id FROM stations WHERE name = 'Main Location')
GROUP BY category
ORDER BY category;

-- Total count should be 35
SELECT COUNT(*) as total_faqs FROM faq_items 
WHERE station_id IN (SELECT id FROM stations WHERE name = 'Main Location');
