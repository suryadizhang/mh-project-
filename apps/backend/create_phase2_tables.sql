-- Create Phase 2A models in ops schema
-- TravelZone, MenuItem, PricingRule
-- Generated from migration 6fed0b9d2bdd

-- 1. TravelZone (ops.travel_zones)
CREATE TABLE IF NOT EXISTS ops.travel_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    zip_codes JSONB NOT NULL,
    base_fee NUMERIC(10, 2) NOT NULL,
    per_mile_fee NUMERIC(10, 2) NOT NULL,
    max_distance_miles INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ops_travel_zones_active
ON ops.travel_zones(is_active);

COMMENT ON TABLE ops.travel_zones IS 'Phase 2A - Distance Agent: Dynamic travel fee calculation by zone';
COMMENT ON COLUMN ops.travel_zones.zip_codes IS 'JSONB array of ZIP codes in this zone';
COMMENT ON COLUMN ops.travel_zones.base_fee IS 'Base travel fee for this zone';
COMMENT ON COLUMN ops.travel_zones.per_mile_fee IS 'Per-mile fee after base distance';

-- 2. MenuItem (ops.menu_items)
CREATE TABLE IF NOT EXISTS ops.menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    base_price_per_person NUMERIC(10, 2) NOT NULL,
    dietary_tags JSONB NOT NULL,
    ingredients JSONB NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT true,
    seasonal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ops_menu_items_available
ON ops.menu_items(is_available);

CREATE INDEX IF NOT EXISTS idx_ops_menu_items_category
ON ops.menu_items(category);

COMMENT ON TABLE ops.menu_items IS 'Phase 2A - Menu Advisor Agent: Dynamic menu recommendations';
COMMENT ON COLUMN ops.menu_items.dietary_tags IS 'JSONB array: vegan, gluten-free, etc.';
COMMENT ON COLUMN ops.menu_items.ingredients IS 'JSONB array of ingredients for allergen checking';

-- 3. PricingRule (ops.pricing_rules)
CREATE TABLE IF NOT EXISTS ops.pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    pricing_formula JSONB NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE,
    priority INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ops_pricing_rules_active
ON ops.pricing_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_ops_pricing_rules_priority
ON ops.pricing_rules(priority);

CREATE INDEX IF NOT EXISTS idx_ops_pricing_rules_type
ON ops.pricing_rules(rule_type);

COMMENT ON TABLE ops.pricing_rules IS 'Phase 2A - Pricing Calculator Agent: NO hardcoded prices, dynamic rules only';
COMMENT ON COLUMN ops.pricing_rules.conditions IS 'JSONB: guest_count, date_range, day_of_week, etc.';
COMMENT ON COLUMN ops.pricing_rules.pricing_formula IS 'JSONB: base_price, multipliers, add-ons';
COMMENT ON COLUMN ops.pricing_rules.priority IS 'Higher priority rules override lower ones';

-- Verify creation
SELECT 'ops.travel_zones' AS table_name, COUNT(*) AS row_count FROM ops.travel_zones
UNION ALL
SELECT 'ops.menu_items', COUNT(*) FROM ops.menu_items
UNION ALL
SELECT 'ops.pricing_rules', COUNT(*) FROM ops.pricing_rules;
