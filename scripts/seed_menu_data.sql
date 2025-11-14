-- Seed Menu Items and Pricing Tiers
-- SOURCE OF TRUTH: Menu page apps/customer/src/app/menu/page.tsx (2025-11-12)
-- REAL PRICING: $55/adult, $30/child (6-12), FREE (5 & under), $550 EVENT MINIMUM
-- BASE PROTEINS (Included): Chicken, NY Strip Steak, Shrimp, Calamari, Tofu
-- PREMIUM UPGRADES: Salmon +$5, Scallops +$5, Filet Mignon +$5, Lobster Tail +$15
-- Run with: psql -f seed_menu_data.sql

-- Generate UUIDs for records (using gen_random_uuid())
-- Note: IDs are generated inline for each INSERT

BEGIN;

-- ============================================
-- CLEAR EXISTING DATA (for re-seeding)
-- ============================================

DELETE FROM public.menu_items;
DELETE FROM public.pricing_tiers;

-- ============================================
-- PRICING TIERS (USER-VERIFIED ACTUAL PRICING)
-- ============================================

INSERT INTO public.pricing_tiers (
    id, tier_level, name, description, price_per_person, min_guests,
    max_proteins, includes_appetizers, includes_noodles, includes_extended_show,
    features, is_popular, is_active, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'basic',
        'Standard Hibachi Experience',
        'Premium hibachi experience for adults - $550 event minimum',
        55.00,  -- VERIFIED: $55 per adult
        10,     -- VERIFIED: $550 minimum / $55 = 10 guests minimum
        2,      -- VERIFIED: Choice of 2 proteins
        true,   -- VERIFIED: Includes side salad
        false,  -- VERIFIED: Noodles NOT included
        false,
        ARRAY[
            '⚠️ $550 EVENT MINIMUM (approximately 10 adults)',
            'Professional hibachi chef with live entertainment',
            'All cooking equipment and setup provided',
            'Choice of 2 proteins: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu',
            'Hibachi fried rice with fresh vegetables',
            'Side salad with signature sauces',
            'Unlimited sake for guests 21+',
            'Premium protein upgrades available: Filet Mignon +$5, Lobster Tail +$15'
        ],
        true,   -- This is the standard (most popular) package
        true,
        1
    ),
    (
        gen_random_uuid()::text,
        'premium',
        'Kids Portion (Ages 6-12)',
        'Same great experience sized for children',
        30.00,  -- VERIFIED: $30 per child (ages 6-12)
        1,
        2,      -- VERIFIED: Same 2-protein selection as adults
        true,
        false,
        false,
        ARRAY[
            'Same 2-protein selection as adults',
            'Kid-sized portions of fried rice',
            'Fresh vegetables',
            'Side salad',
            'Full entertainment experience'
        ],
        false,
        true,
        2
    ),
    (
        gen_random_uuid()::text,
        'luxury',
        'Kids Free (Ages 5 & Under)',
        'Complimentary with adult purchase',
        0.00,   -- VERIFIED: FREE for ages 5 & under
        1,
        1,      -- VERIFIED: 1 protein, small portion
        false,
        false,
        false,
        ARRAY[
            '1 protein option',
            'Small rice portion',
            'Vegetables',
            'Must have adult purchase',
            'Ages 5 and under only'
        ],
        false,
        true,
        3
    );

-- ============================================
-- MENU ITEMS - POULTRY (VERIFIED)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'Chicken',
        'Tender, juicy chicken breast',
        'poultry',
        NULL,  -- VERIFIED: Included in base price
        false,
        true,
        1
    );

-- ============================================
-- MENU ITEMS - BEEF (VERIFIED)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'NY Strip Steak',
        'Premium cut NY strip steak',
        'beef',
        NULL,  -- VERIFIED: Included in base price
        false,
        true,
        1
    ),
    (
        gen_random_uuid()::text,
        'Filet Mignon',
        'Premium tenderloin',
        'beef',
        5.00,  -- VERIFIED: +$5 per person upgrade
        true,
        true,
        2
    );

-- ============================================
-- MENU ITEMS - SEAFOOD (FROM MENU PAGE)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'Shrimp',
        'Fresh jumbo shrimp with garlic butter',
        'seafood',
        NULL,  -- VERIFIED: Included in base proteins (menu page)
        false,
        true,
        1
    ),
    (
        gen_random_uuid()::text,
        'Calamari',
        'Fresh tender calamari grilled with garlic',
        'seafood',
        NULL,  -- VERIFIED: Included in base proteins (menu page)
        false,
        true,
        2
    ),
    (
        gen_random_uuid()::text,
        'Salmon',
        'Wild-caught Atlantic salmon with teriyaki glaze',
        'seafood',
        5.00,  -- VERIFIED: +$5 premium upgrade (menu page)
        true,
        true,
        3
    ),
    (
        gen_random_uuid()::text,
        'Scallops',
        'Fresh sea scallops grilled to perfection',
        'seafood',
        5.00,  -- VERIFIED: +$5 premium upgrade (menu page)
        true,
        true,
        4
    ),
    (
        gen_random_uuid()::text,
        'Lobster Tail',
        'Fresh lobster tail with garlic butter',
        'seafood',
        15.00,  -- VERIFIED: +$15 premium upgrade (menu page)
        true,
        true,
        5
    );

-- ============================================
-- MENU ITEMS - SPECIALTY (VERIFIED)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, dietary_info, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'Tofu',
        'Firm, seasoned tofu',
        'specialty',
        NULL,  -- VERIFIED: Included in base price
        false,
        true,
        ARRAY['vegetarian', 'vegan'],
        1
    ),
    (
        gen_random_uuid()::text,
        'Vegetables',
        'Mixed seasonal vegetables',
        'specialty',
        NULL,  -- VERIFIED: Included option
        false,
        true,
        ARRAY['vegetarian', 'vegan', 'gluten-free'],
        2
    );

-- ============================================
-- MENU ITEMS - SIDES (VERIFIED - INCLUDED ONLY)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'Fried Rice',
        'Classic hibachi fried rice',
        'sides',
        NULL,  -- VERIFIED: Always included
        false,
        true,
        1
    ),
    (
        gen_random_uuid()::text,
        'Grilled Vegetables',
        'Fresh grilled vegetables',
        'sides',
        NULL,  -- VERIFIED: Always included
        false,
        true,
        2
    ),
    (
        gen_random_uuid()::text,
        'Extra Fried Rice',
        'Additional portion of hibachi fried rice',
        'sides',
        5.00,  -- VERIFIED: +$5 per person (menu page)
        true,
        true,
        3
    ),
    (
        gen_random_uuid()::text,
        'Extra Vegetables',
        'Additional portion of mixed seasonal vegetables',
        'sides',
        5.00,  -- VERIFIED: +$5 per person (menu page)
        true,
        true,
        4
    ),
    (
        gen_random_uuid()::text,
        'Yakisoba Noodles',
        'Japanese style lo mein noodles',
        'sides',
        5.00,  -- VERIFIED: +$5 per person (menu page)
        true,
        true,
        5
    );

-- ============================================
-- MENU ITEMS - APPETIZERS (VERIFIED)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        'Side Salad',
        'Fresh salad with signature sauces',
        'appetizers',
        NULL,  -- VERIFIED: Always included
        false,
        true,
        1
    ),
    (
        gen_random_uuid()::text,
        'Edamame',
        'Fresh steamed soybeans with sea salt',
        'appetizers',
        5.00,  -- VERIFIED: +$5 per person (menu page)
        true,
        true,
        2
    ),
    (
        gen_random_uuid()::text,
        'Gyoza',
        'Pan-fried Japanese dumplings',
        'appetizers',
        10.00,  -- VERIFIED: +$10 per person (menu page)
        true,
        true,
        3
    );

-- ============================================
-- MENU ITEMS - DESSERTS (Add-on option)
-- ============================================

INSERT INTO public.menu_items (
    id, name, description, category, base_price, is_premium, is_available, display_order
) VALUES
    (
        gen_random_uuid()::text,
        '3rd Protein',
        'Add a third protein to your meal',
        'desserts',
        10.00,  -- VERIFIED: +$10 per person (menu page)
        true,
        true,
        1
    );

COMMIT;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check pricing tiers
SELECT 
    tier_level,
    name,
    price_per_person,
    min_guests,
    is_popular
FROM public.pricing_tiers
ORDER BY display_order;

-- Check menu items by category
SELECT 
    category,
    COUNT(*) as item_count,
    COUNT(*) FILTER (WHERE is_premium = true) as premium_count
FROM public.menu_items
GROUP BY category
ORDER BY category;

-- Show all menu items
SELECT 
    category,
    name,
    CASE 
        WHEN is_premium THEN CONCAT('$', base_price::text, ' (premium)')
        ELSE 'Included'
    END as pricing,
    description
FROM public.menu_items
ORDER BY 
    category,
    is_premium DESC,
    display_order,
    name;

-- Show formatted pricing tiers for AI
SELECT 
    tier_level,
    name,
    CONCAT('$', price_per_person::text, '/person') as price,
    CONCAT('Min ', min_guests, ' guests') as minimum,
    CONCAT(max_proteins, ' protein choices') as proteins,
    CASE WHEN is_popular THEN '⭐ MOST POPULAR' ELSE '' END as badge
FROM public.pricing_tiers
ORDER BY display_order;
