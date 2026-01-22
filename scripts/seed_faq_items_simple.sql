-- ============================================================================
-- FAQ ITEMS SEED SCRIPT (Simple Version)
-- ============================================================================
-- Purpose: Seed faq_items table with verified FAQs from customer website
-- Source of Truth: apps/customer/src/data/faqsData.ts
-- Last Verified: 2025-11-12
-- Total FAQs: 35 items across 8 categories
--
-- IMPORTANT: This data is DYNAMIC and subject to change!
-- - FAQs can be added, modified, or removed at any time
-- - Answers may be updated based on policy changes
-- - Pricing information must stay synchronized with menu page
-- - Use auto-sync service to detect changes from TypeScript source
-- - Manual updates via admin UI will override auto-sync
-- ============================================================================

-- Clean slate: delete all existing FAQs
TRUNCATE TABLE faq_items RESTART IDENTITY CASCADE;

-- ========================================================================
-- CATEGORY: Pricing & Minimums (4 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('How much does My Hibachi Chef cost?',
 '$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.',
 'Pricing & Minimums', 0, 0, true),

('Is there a minimum party size?',
 'Yes — $550 total minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.',
 'Pricing & Minimums', 0, 0, true),

('Is tipping expected?',
 'Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost. You can tip cash or via Venmo/Zelle Business.',
 'Pricing & Minimums', 0, 0, true),

('Do you charge travel fees?',
 'First 30 miles from our location are free. After that, $2 per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.',
 'Pricing & Minimums', 0, 0, true);

-- ========================================================================
-- CATEGORY: Menu & Upgrades (7 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('What''s included in the hibachi menu?',
 'Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.',
 'Menu & Upgrades', 0, 0, true),

('What are the premium protein upgrades?',
 'For premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5 per person, while Lobster Tail is +$15 per person. These upgrade your existing protein choices to premium options.',
 'Menu & Upgrades', 0, 0, true),

('What are the kids'' portions and pricing?',
 '$30 per child (6-12 years) — same 2-protein selection as adults. Ages 5 & under eat free with adult purchase (1 protein, small rice portion).',
 'Menu & Upgrades', 0, 0, true),

('Do you serve sake and alcohol?',
 'Yes! We provide sake for guests 21+ as part of the standard experience. We don''t provide other alcohol — you''re welcome to supply your own beer, wine, or cocktails.',
 'Menu & Upgrades', 0, 0, true),

('Can I add an extra protein or more?',
 'Yes! Each guest normally gets 2 proteins, but you can add an extra protein for +$10 each. This is an additional option that gives you more food, not an upgrade. If you want the extra protein to be a premium option (Salmon, Scallops, Filet Mignon, or Lobster Tail), that would be the +$10 for the additional protein plus the premium upgrade cost (+$5 for Salmon/Scallops/Filet Mignon, +$15 for Lobster Tail).',
 'Menu & Upgrades', 0, 0, true),

('What additional enhancements can I add to my menu?',
 'We offer several delicious add-on options: Yakisoba Noodles, Extra Fried Rice, Extra Vegetables, and Edamame are all +$5 each. Gyoza and Extra Protein are +$10 each. These can be ordered per person or shared family-style.',
 'Menu & Upgrades', 0, 0, true),

('Can guests choose different proteins?',
 'Absolutely! Each guest can choose their own 2 proteins from: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu. Everyone can have different selections. Premium upgrades (Salmon +$5, Scallops +$5, Filet Mignon +$5, Lobster Tail +$15) are also individual choices.',
 'Menu & Upgrades', 0, 0, true);

-- ========================================================================
-- CATEGORY: Booking & Payments (5 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('How do I book My Hibachi Chef?',
 'Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit (refundable if canceled 7+ days before event).',
 'Booking & Payments', 0, 0, true),

('What''s the deposit policy?',
 '$100 refundable deposit secures your date and is deducted from final bill (refundable if canceled 7+ days before event). Remaining balance due on event date. Accept Venmo Business, Zelle Business, Cash, Credit Card.',
 'Booking & Payments', 0, 0, true),

('What payment methods do you accept?',
 'Venmo Business, Zelle Business, Cash, and Credit Card. Deposit paid online when booking. Balance due on event date or in advance.',
 'Booking & Payments', 0, 0, true),

('How far in advance should I book?',
 '48 hours minimum required. For weekends and holidays, recommend 1-2 weeks ahead. Text (916) 740-8768 to check availability.',
 'Booking & Payments', 0, 0, true),

('Why is a deposit required?',
 'The $100 deposit confirms your reservation and helps us prepare fresh ingredients specifically for your party. It also ensures commitment from both sides and covers our preparation costs. The deposit is deducted from your final bill on party day.',
 'Booking & Payments', 0, 0, true);

-- ========================================================================
-- CATEGORY: Travel & Service Area (2 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('Where do you serve?',
 'We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first 30 miles, then $2/mile.',
 'Travel & Service Area', 0, 0, true),

('Do you travel to my city?',
 'We serve the Bay Area, Sacramento, Central Valley, and coastal/mountain communities throughout Northern California. Text (916) 740-8768 with your zip code for confirmation.',
 'Travel & Service Area', 0, 0, true);

-- ========================================================================
-- CATEGORY: On-Site Setup & Requirements (5 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('What space do you need for the hibachi setup?',
 'Clear area 68.3"L × 27.5"W × 41.3"H for our grill. Need level ground, outdoor space or well-ventilated indoor area, and table access so guests can watch the show.',
 'On-Site Setup & Requirements', 0, 0, true),

('How should I arrange tables and seating?',
 'U-shape with chef''s grill at the open end so everyone watches the show. Two 8-foot tables seat ~10 people, three 6-foot tables handle 12-15 guests.',
 'On-Site Setup & Requirements', 0, 0, true),

('Can you cook indoors?',
 'Outdoor preferred for safety, but indoor possible with high ceilings and excellent ventilation. Must handle smoke and propane safely. Email cs@myhibachichef.com to discuss indoor requirements.',
 'On-Site Setup & Requirements', 0, 0, true),

('What do I need to provide?',
 'You provide: tables, chairs, plates, utensils, glasses, beverages (except sake), napkins. We bring: hibachi grill, food, cooking tools, propane, safety equipment, sake.',
 'On-Site Setup & Requirements', 0, 0, true),

('What time will the chef arrive?',
 'Our chef will arrive approximately 15-30 minutes before your scheduled party time for setup. Setup is quick and usually takes just a few minutes. We''ll confirm arrival time when we call to finalize details.',
 'On-Site Setup & Requirements', 0, 0, true);

-- ========================================================================
-- CATEGORY: Dietary & Allergens (1 FAQ)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('Can you accommodate dietary restrictions?',
 'Yes! Vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance so our chef can prepare. Email cs@myhibachichef.com with specific needs.',
 'Dietary & Allergens', 0, 0, true);

-- ========================================================================
-- CATEGORY: Policies (2 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('What''s your cancellation policy?',
 'Full refund if canceled 4+ days before event. $100 deposit is refundable for cancellations 4+ days before event, non-refundable within 4 days. One free reschedule if requested 24+ hours before event; additional reschedules cost $200.',
 'Policies', 0, 0, true),

('What happens if it rains?',
 'You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups — plan a backup covered area!',
 'Policies', 0, 0, true);

-- ========================================================================
-- CATEGORY: Special Occasions (1 FAQ)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('Do you do birthday parties and special events?',
 'Absolutely! Birthday parties are our specialty. Chefs make the show extra fun and family-friendly, accommodate dietary needs, and make the birthday person feel special. Book 48+ hours ahead!',
 'Special Occasions', 0, 0, true);

-- ========================================================================
-- CATEGORY: Contact (2 FAQs)
-- ========================================================================

INSERT INTO faq_items (question, answer, category, view_count, helpful_count, is_active) VALUES
('What''s the fastest way to reach you?',
 'Text (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Follow @my_hibachi_chef on Instagram and Facebook. Usually respond within 1-2 hours during business hours.',
 'Contact', 0, 0, true),

('Is it safe to use propane for cooking in residential areas?',
 'Yes, absolutely safe! Our chefs are experienced professionals who follow strict safety protocols. We bring portable fire extinguishers to every event, perform propane leak checks, maintain safe distances from flammable objects, and ensure proper ventilation.',
 'On-Site Setup & Requirements', 0, 0, true),

('Can I get a receipt or invoice?',
 'Yes! We can provide receipts or invoices for deposit, remaining balance, and gratuity. Perfect for expense reimbursement or business events. Contact cs@myhibachichef.com to request documentation.',
 'Booking & Payments', 0, 0, true);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT
    category,
    COUNT(*) as faq_count
FROM faq_items
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- Total should be 35 FAQs
SELECT COUNT(*) as total_faqs FROM faq_items WHERE is_active = true;
