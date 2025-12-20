-- Create addon_items table (if doesn't exist)
-- Run this with: psql -h db.yuchqvpctookhjovvdwi.supabase.co -U postgres -d postgres -f create_addon_items_table.sql

-- Create AddonCategory enum if doesn't exist
DO $$ BEGIN
    CREATE TYPE addon_category AS ENUM (
        'protein_upgrades',
        'enhancements',
        'equipment',
        'entertainment',
        'beverages'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create addon_items table
CREATE TABLE IF NOT EXISTS public.addon_items (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category addon_category NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    image_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    station_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_addon_items_category ON public.addon_items(category);
CREATE INDEX IF NOT EXISTS idx_addon_items_active ON public.addon_items(is_active);
CREATE INDEX IF NOT EXISTS idx_addon_items_station ON public.addon_items(station_id);
CREATE INDEX IF NOT EXISTS idx_addon_items_lookup ON public.addon_items(category, is_active, display_order);

-- Insert addon items
INSERT INTO public.addon_items (id, name, description, category, price, is_active, display_order) VALUES
('addon_001', 'Filet Mignon', 'Premium upgrade - tender filet mignon (+$5 per person)', 'protein_upgrades', 5.00, TRUE, 1),
('addon_002', 'Salmon', 'Premium upgrade - fresh Atlantic salmon (+$5 per person)', 'protein_upgrades', 5.00, TRUE, 2),
('addon_003', 'Scallops', 'Premium upgrade - seared scallops (+$5 per person)', 'protein_upgrades', 5.00, TRUE, 3),
('addon_004', 'Lobster Tail', 'Premium upgrade - succulent lobster tail (+$15 per person)', 'protein_upgrades', 15.00, TRUE, 4),
('addon_005', 'Extra Protein', 'Add an extra protein to your meal (+$10 each, premium adds upgrade price)', 'protein_upgrades', 10.00, TRUE, 5),
('addon_006', 'Yakisoba Noodles', 'Substitute fried rice with yakisoba noodles (+$5 per person)', 'enhancements', 5.00, TRUE, 6),
('addon_007', 'Extra Fried Rice', 'Additional portion of hibachi fried rice (+$5 per person)', 'enhancements', 5.00, TRUE, 7),
('addon_008', 'Extra Vegetables', 'Additional grilled vegetables (+$5 per person)', 'enhancements', 5.00, TRUE, 8),
('addon_009', 'Edamame', 'Steamed edamame appetizer (+$5)', 'enhancements', 5.00, TRUE, 9),
('addon_010', 'Gyoza (6 pieces)', 'Pan-fried pork dumplings (+$10)', 'enhancements', 10.00, TRUE, 10)
ON CONFLICT (id) DO NOTHING;
