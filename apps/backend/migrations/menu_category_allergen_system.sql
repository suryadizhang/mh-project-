-- ============================================
-- My Hibachi Menu Category & Allergen System
-- Migration Script
-- Date: 2025-11-27
-- ============================================

-- Step 1: Add new columns to menu_items table
-- ============================================

ALTER TABLE ops.menu_items
ADD COLUMN IF NOT EXISTS main_category VARCHAR(50);

-- Rename dietary_tags to tags (or add if doesn't exist)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'ops'
        AND table_name = 'menu_items'
        AND column_name = 'dietary_tags'
    ) THEN
        ALTER TABLE ops.menu_items RENAME COLUMN dietary_tags TO tags;
    ELSE
        ALTER TABLE ops.menu_items ADD COLUMN tags JSONB NOT NULL DEFAULT '[]';
    END IF;
END $$;

-- Add display_order if doesn't exist
ALTER TABLE ops.menu_items
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Add is_included if doesn't exist
ALTER TABLE ops.menu_items
ADD COLUMN IF NOT EXISTS is_included BOOLEAN DEFAULT false;


-- Step 2: Create indexes for performance
-- ============================================

-- GIN index for tag queries (critical for AI search)
CREATE INDEX IF NOT EXISTS idx_menu_items_tags
ON ops.menu_items USING GIN (tags);

-- Index for main category filtering
CREATE INDEX IF NOT EXISTS idx_menu_items_main_category
ON ops.menu_items (main_category);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_menu_items_category_active
ON ops.menu_items (main_category, is_available);


-- Step 3: Migrate existing data
-- ============================================

-- Map old category values to new main_category
UPDATE ops.menu_items
SET main_category = CASE
    WHEN category IN ('chicken', 'shrimp', 'steak', 'tofu') THEN 'protein'
    WHEN category IN ('salmon', 'scallops', 'lobster', 'filet_mignon') THEN 'premium_protein'
    WHEN category IN ('gyoza', 'edamame', 'salad') THEN 'appetizer'
    WHEN category IN ('rice', 'noodles', 'vegetables', 'extra_protein') THEN 'addon'
    WHEN category IN ('teriyaki', 'soy_sauce', 'yum_yum') THEN 'sauce'
    ELSE 'protein'  -- Default fallback
END
WHERE main_category IS NULL;


-- Step 4: Populate tags based on business rules
-- ============================================

-- Base Proteins
UPDATE ops.menu_items
SET tags = '["poultry", "grilled", "gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%chicken%' AND main_category = 'protein';

UPDATE ops.menu_items
SET tags = '["seafood", "shellfish", "crustaceans", "grilled", "gluten_free", "dairy_free", "contains_shellfish", "contains_crustaceans"]'::jsonb
WHERE name ILIKE '%shrimp%' AND main_category = 'protein';

UPDATE ops.menu_items
SET tags = '["beef", "grilled", "gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%steak%' AND main_category = 'protein';

UPDATE ops.menu_items
SET tags = '["vegetarian", "grilled", "gluten_free", "dairy_free", "contains_soy"]'::jsonb
WHERE name ILIKE '%tofu%' AND main_category = 'protein';

-- Premium Proteins
UPDATE ops.menu_items
SET tags = '["seafood", "fish", "grilled", "gluten_free", "dairy_free", "contains_fish"]'::jsonb
WHERE name ILIKE '%salmon%' AND main_category = 'premium_protein';

UPDATE ops.menu_items
SET tags = '["seafood", "shellfish", "mollusks", "grilled", "gluten_free", "dairy_free", "contains_shellfish", "contains_mollusks"]'::jsonb
WHERE name ILIKE '%scallop%' AND main_category = 'premium_protein';

UPDATE ops.menu_items
SET tags = '["seafood", "shellfish", "crustaceans", "grilled", "gluten_free", "dairy_free", "contains_shellfish", "contains_crustaceans"]'::jsonb
WHERE name ILIKE '%lobster%' AND main_category = 'premium_protein';

UPDATE ops.menu_items
SET tags = '["beef", "grilled", "gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%filet%' AND main_category = 'premium_protein';

-- Appetizers
UPDATE ops.menu_items
SET tags = '["poultry", "pan_fried", "dairy_free", "contains_gluten", "contains_soy"]'::jsonb
WHERE name ILIKE '%gyoza%' AND main_category = 'appetizer';

UPDATE ops.menu_items
SET tags = '["vegetarian", "steamed", "gluten_free", "dairy_free", "contains_soy"]'::jsonb
WHERE name ILIKE '%edamame%' AND main_category = 'appetizer';

UPDATE ops.menu_items
SET tags = '["vegetarian", "raw", "gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%salad%' AND main_category = 'appetizer';

-- Addons
UPDATE ops.menu_items
SET tags = '["gluten_free", "dairy_free", "contains_eggs", "contains_soy"]'::jsonb
WHERE name ILIKE '%fried rice%' AND main_category = 'addon';

UPDATE ops.menu_items
SET tags = '["gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%white rice%' AND main_category = 'addon';

UPDATE ops.menu_items
SET tags = '["vegetarian", "grilled", "gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%vegetable%' AND main_category = 'addon';

UPDATE ops.menu_items
SET tags = '["dairy_free", "contains_gluten", "contains_eggs"]'::jsonb
WHERE name ILIKE '%noodle%' AND main_category = 'addon';

-- Sauces
UPDATE ops.menu_items
SET tags = '["dairy_free", "contains_gluten", "contains_soy"]'::jsonb
WHERE name ILIKE '%teriyaki%' AND main_category = 'sauce';

UPDATE ops.menu_items
SET tags = '["gluten_free", "dairy_free", "contains_soy"]'::jsonb
WHERE name ILIKE '%gluten%free%soy%' AND main_category = 'sauce';

UPDATE ops.menu_items
SET tags = '["gluten_free", "dairy_free"]'::jsonb
WHERE name ILIKE '%yum%yum%' AND main_category = 'sauce';


-- Step 5: Insert missing menu items (if not exist)
-- ============================================

-- Insert Lobster if doesn't exist
INSERT INTO ops.menu_items (
    id,
    name,
    description,
    main_category,
    tags,
    base_price_per_person,
    is_included,
    is_available,
    seasonal,
    display_order
)
SELECT
    gen_random_uuid(),
    'Lobster Tail',
    'Grilled lobster tail with butter',
    'premium_protein',
    '["seafood", "shellfish", "crustaceans", "grilled", "gluten_free", "dairy_free", "contains_shellfish", "contains_crustaceans"]'::jsonb,
    15.00,
    false,
    true,
    false,
    3
WHERE NOT EXISTS (
    SELECT 1 FROM ops.menu_items WHERE name ILIKE '%lobster%'
);

-- Insert Gluten-Free Soy Sauce if doesn't exist
INSERT INTO ops.menu_items (
    id,
    name,
    description,
    main_category,
    tags,
    base_price_per_person,
    is_included,
    is_available,
    seasonal,
    display_order
)
SELECT
    gen_random_uuid(),
    'Gluten-Free Soy Sauce',
    'Tamari-style gluten-free soy sauce',
    'sauce',
    '["gluten_free", "dairy_free", "contains_soy"]'::jsonb,
    0.00,
    true,
    true,
    false,
    2
WHERE NOT EXISTS (
    SELECT 1 FROM ops.menu_items WHERE name ILIKE '%gluten%free%soy%'
);


-- Step 6: Add constraints and validation
-- ============================================

-- Ensure main_category has valid values
ALTER TABLE ops.menu_items
ADD CONSTRAINT chk_menu_items_main_category
CHECK (main_category IN ('protein', 'premium_protein', 'appetizer', 'addon', 'sauce'));

-- Ensure tags is always valid JSON array
ALTER TABLE ops.menu_items
ADD CONSTRAINT chk_menu_items_tags_is_array
CHECK (jsonb_typeof(tags) = 'array');


-- Step 7: Create helper functions for allergen queries
-- ============================================

-- Function: Get all items with specific allergen
CREATE OR REPLACE FUNCTION ops.get_items_with_allergen(allergen_tag TEXT)
RETURNS TABLE (
    item_name VARCHAR(200),
    category VARCHAR(50),
    all_tags JSONB,
    price DECIMAL(10, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        name,
        main_category,
        tags,
        base_price_per_person
    FROM ops.menu_items
    WHERE tags @> jsonb_build_array(allergen_tag)
    AND is_available = true
    ORDER BY main_category, display_order;
END;
$$ LANGUAGE plpgsql;

-- Function: Get safe items (excluding allergen)
CREATE OR REPLACE FUNCTION ops.get_safe_items_excluding_allergen(allergen_tag TEXT)
RETURNS TABLE (
    item_name VARCHAR(200),
    category VARCHAR(50),
    all_tags JSONB,
    price DECIMAL(10, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        name,
        main_category,
        tags,
        base_price_per_person
    FROM ops.menu_items
    WHERE NOT tags @> jsonb_build_array(allergen_tag)
    AND is_available = true
    ORDER BY main_category, display_order;
END;
$$ LANGUAGE plpgsql;

-- Function: Get items matching multiple tags (AND logic)
CREATE OR REPLACE FUNCTION ops.get_items_with_all_tags(required_tags TEXT[])
RETURNS TABLE (
    item_name VARCHAR(200),
    category VARCHAR(50),
    all_tags JSONB,
    price DECIMAL(10, 2)
) AS $$
DECLARE
    tag_filter JSONB;
BEGIN
    tag_filter := to_jsonb(required_tags);

    RETURN QUERY
    SELECT
        name,
        main_category,
        tags,
        base_price_per_person
    FROM ops.menu_items
    WHERE tags @> tag_filter
    AND is_available = true
    ORDER BY main_category, display_order;
END;
$$ LANGUAGE plpgsql;


-- Step 8: Create views for common queries
-- ============================================

-- View: All allergen-free proteins (no common allergens)
CREATE OR REPLACE VIEW ops.v_allergen_free_proteins AS
SELECT
    name,
    main_category,
    tags,
    base_price_per_person,
    CASE
        WHEN tags @> '["contains_shellfish"]' THEN false
        WHEN tags @> '["contains_fish"]' THEN false
        WHEN tags @> '["contains_gluten"]' THEN false
        WHEN tags @> '["contains_soy"]' THEN false
        WHEN tags @> '["contains_eggs"]' THEN false
        ELSE true
    END AS is_major_allergen_free
FROM ops.menu_items
WHERE main_category IN ('protein', 'premium_protein')
AND is_available = true;

-- View: Gluten-free menu
CREATE OR REPLACE VIEW ops.v_gluten_free_menu AS
SELECT
    name,
    main_category,
    tags,
    base_price_per_person,
    description
FROM ops.menu_items
WHERE tags @> '["gluten_free"]'
AND is_available = true
ORDER BY main_category, display_order;

-- View: Shellfish items (for allergy warnings)
CREATE OR REPLACE VIEW ops.v_shellfish_items AS
SELECT
    name,
    main_category,
    tags,
    base_price_per_person,
    CASE
        WHEN tags @> '["crustaceans"]' THEN 'Crustacean (shrimp, lobster)'
        WHEN tags @> '["mollusks"]' THEN 'Mollusk (scallops)'
        ELSE 'General shellfish'
    END AS shellfish_type
FROM ops.menu_items
WHERE tags @> '["contains_shellfish"]'
AND is_available = true
ORDER BY main_category, display_order;


-- Step 9: Verification queries
-- ============================================

-- Count items by category
SELECT
    main_category,
    COUNT(*) as item_count,
    COUNT(*) FILTER (WHERE tags @> '["gluten_free"]') as gluten_free_count,
    COUNT(*) FILTER (WHERE tags @> '["contains_shellfish"]') as shellfish_count
FROM ops.menu_items
WHERE is_available = true
GROUP BY main_category
ORDER BY main_category;

-- List all unique tags in use
SELECT DISTINCT jsonb_array_elements_text(tags) as tag
FROM ops.menu_items
ORDER BY tag;

-- Items with multiple allergens (complex cases)
SELECT
    name,
    main_category,
    jsonb_array_length(tags) as tag_count,
    tags
FROM ops.menu_items
WHERE jsonb_array_length(
    (SELECT jsonb_agg(tag)
     FROM jsonb_array_elements_text(tags) tag
     WHERE tag LIKE 'contains_%')
) > 1
ORDER BY tag_count DESC;


-- Step 10: Grant permissions
-- ============================================

-- Grant SELECT on views to application role
GRANT SELECT ON ops.v_allergen_free_proteins TO mh_app_user;
GRANT SELECT ON ops.v_gluten_free_menu TO mh_app_user;
GRANT SELECT ON ops.v_shellfish_items TO mh_app_user;

-- Grant EXECUTE on functions to application role
GRANT EXECUTE ON FUNCTION ops.get_items_with_allergen(TEXT) TO mh_app_user;
GRANT EXECUTE ON FUNCTION ops.get_safe_items_excluding_allergen(TEXT) TO mh_app_user;
GRANT EXECUTE ON FUNCTION ops.get_items_with_all_tags(TEXT[]) TO mh_app_user;


-- ============================================
-- Migration Complete
-- ============================================

-- Verify migration success
DO $$
DECLARE
    total_items INTEGER;
    items_with_tags INTEGER;
    items_with_category INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_items FROM ops.menu_items;
    SELECT COUNT(*) INTO items_with_tags FROM ops.menu_items WHERE jsonb_array_length(tags) > 0;
    SELECT COUNT(*) INTO items_with_category FROM ops.menu_items WHERE main_category IS NOT NULL;

    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Menu Category & Allergen Migration Complete';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Total menu items: %', total_items;
    RAISE NOTICE 'Items with tags: %', items_with_tags;
    RAISE NOTICE 'Items with main_category: %', items_with_category;
    RAISE NOTICE '';

    IF items_with_tags < total_items THEN
        RAISE WARNING 'Some items missing tags - review required';
    END IF;

    IF items_with_category < total_items THEN
        RAISE WARNING 'Some items missing main_category - review required';
    END IF;
END $$;
