-- =====================================================
-- Migration: 008_legal_agreements_system.sql
-- Created: 2025-01-30
-- Purpose: Legal agreements system for liability waiver,
--          allergen disclosure, and booking confirmation.
-- Retention: 7 YEARS (legal compliance requirement)
-- =====================================================

BEGIN;

-- =====================================================
-- 1. AGREEMENT TEMPLATES TABLE
-- Stores versioned templates for different agreement types
-- =====================================================
CREATE TABLE IF NOT EXISTS core.agreement_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template identification
    agreement_type VARCHAR(50) NOT NULL,  -- 'liability_waiver', 'allergen_disclosure', 'booking_terms'
    version VARCHAR(20) NOT NULL,          -- '2025.1.0'
    title VARCHAR(200) NOT NULL,

    -- Content (Markdown with {{variable}} placeholders)
    content_markdown TEXT NOT NULL,

    -- Validity
    effective_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,

    -- Variables this template uses (for validation)
    variable_refs TEXT[] DEFAULT '{}',

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id),

    -- Ensure unique version per type
    UNIQUE(agreement_type, version)
);

COMMENT ON TABLE core.agreement_templates IS 'Versioned templates for legal agreements. Templates use {{variable}} placeholders for dynamic values.';
COMMENT ON COLUMN core.agreement_templates.agreement_type IS 'Type: liability_waiver, allergen_disclosure, booking_terms';
COMMENT ON COLUMN core.agreement_templates.content_markdown IS 'Markdown content with {{ADULT_PRICE}}, {{DEPOSIT_AMOUNT}} etc placeholders';
COMMENT ON COLUMN core.agreement_templates.variable_refs IS 'Array of variable names used in this template for validation';

-- =====================================================
-- 2. SIGNED AGREEMENTS TABLE
-- Immutable record of signed agreements (7-year retention)
-- =====================================================
CREATE TABLE IF NOT EXISTS core.signed_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES core.customers(id),

    -- Agreement content (frozen at time of signing)
    agreement_type VARCHAR(50) NOT NULL,
    agreement_version VARCHAR(20) NOT NULL,
    agreement_text TEXT NOT NULL,  -- Full rendered text at signing (no placeholders)

    -- Signature data
    signature_image BYTEA,           -- PNG of canvas signature
    signature_typed_name VARCHAR(200), -- If typed instead of drawn
    signed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Signer verification
    signer_name VARCHAR(200) NOT NULL,
    signer_email VARCHAR(255) NOT NULL,
    signer_ip_address INET,
    signer_user_agent TEXT,
    signer_device_fingerprint VARCHAR(500),

    -- Signing method tracking
    signing_method VARCHAR(20) NOT NULL,  -- 'online', 'sms_link', 'phone', 'in_person', 'ai_chat'

    -- PDF delivery
    confirmation_email_sent_at TIMESTAMPTZ,
    confirmation_pdf_url TEXT,  -- R2/S3 URL to PDF copy

    -- Immutability (no updated_at - agreements are NEVER modified)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Retention tracking
    retention_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 years')
);

-- Add constraint to prevent updates (immutable)
-- This is enforced at application level, but we can add a trigger for extra safety
CREATE OR REPLACE FUNCTION core.prevent_signed_agreement_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Signed agreements are immutable and cannot be modified';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS signed_agreements_no_update ON core.signed_agreements;
CREATE TRIGGER signed_agreements_no_update
    BEFORE UPDATE ON core.signed_agreements
    FOR EACH ROW
    EXECUTE FUNCTION core.prevent_signed_agreement_update();

COMMENT ON TABLE core.signed_agreements IS 'Immutable record of signed agreements. Retain for 7 years minimum. NEVER modify after creation.';
COMMENT ON COLUMN core.signed_agreements.agreement_text IS 'Full rendered text at signing time - all placeholders replaced with actual values';
COMMENT ON COLUMN core.signed_agreements.signing_method IS 'How agreement was signed: online, sms_link, phone, in_person, ai_chat';
COMMENT ON COLUMN core.signed_agreements.retention_expires_at IS 'Auto-delete after 7 years for compliance';

-- =====================================================
-- 3. ALLERGEN DISCLOSURES TABLE
-- Per-booking allergen information with confirmation
-- =====================================================
CREATE TABLE IF NOT EXISTS core.allergen_disclosures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,

    -- Common allergens present at event (from FDA Big 9)
    -- Our menu only contains: shellfish, fish, soy, eggs, wheat/gluten, sesame
    -- We are: NUT-FREE, DAIRY-FREE (use dairy-free butter)
    common_allergens JSONB DEFAULT '[]'::jsonb,  -- ['shellfish', 'eggs', 'soy']

    -- Free-text for additional details
    other_allergens TEXT,
    special_requests TEXT,

    -- Confirmation tracking
    confirmed BOOLEAN DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    confirmed_method VARCHAR(20),  -- 'online', 'sms', 'phone', 'verbal'

    -- Reminder sent
    reminder_sent_at TIMESTAMPTZ,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.allergen_disclosures IS 'Per-booking allergen disclosure. Tracks what allergens guests have and confirmation status.';
COMMENT ON COLUMN core.allergen_disclosures.common_allergens IS 'JSON array of allergen keys: shellfish, fish, soy, eggs, wheat, sesame';

-- =====================================================
-- 4. SLOT HOLDS TABLE
-- Temporary holds during agreement signing (2-hour timeout)
-- =====================================================
CREATE TABLE IF NOT EXISTS core.slot_holds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Slot being held
    event_date DATE NOT NULL,
    slot_time TIME NOT NULL,
    station_id UUID REFERENCES identity.stations(id),

    -- Hold details
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(200),
    guest_count INT DEFAULT 10,

    -- Signing link
    signing_token UUID DEFAULT gen_random_uuid(),
    signing_link_sent_at TIMESTAMPTZ,

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 hours'),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'converted', 'expired', 'cancelled'
    converted_to_booking_id UUID REFERENCES core.bookings(id),

    -- Prevent duplicate holds on same slot
    UNIQUE(event_date, slot_time, station_id, status)
);

COMMENT ON TABLE core.slot_holds IS 'Temporary slot holds during agreement signing. 2-hour timeout before slot is released.';
COMMENT ON COLUMN core.slot_holds.signing_token IS 'UUID token for SMS/email signing link';
COMMENT ON COLUMN core.slot_holds.expires_at IS 'Auto-expire 2 hours after creation';

-- =====================================================
-- 5. INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_signed_agreements_booking
    ON core.signed_agreements(booking_id);
CREATE INDEX IF NOT EXISTS idx_signed_agreements_customer
    ON core.signed_agreements(customer_id);
CREATE INDEX IF NOT EXISTS idx_signed_agreements_date
    ON core.signed_agreements(signed_at);
CREATE INDEX IF NOT EXISTS idx_signed_agreements_retention
    ON core.signed_agreements(retention_expires_at);

CREATE INDEX IF NOT EXISTS idx_allergen_disclosures_booking
    ON core.allergen_disclosures(booking_id);

CREATE INDEX IF NOT EXISTS idx_slot_holds_date_slot
    ON core.slot_holds(event_date, slot_time, station_id);
CREATE INDEX IF NOT EXISTS idx_slot_holds_token
    ON core.slot_holds(signing_token);
CREATE INDEX IF NOT EXISTS idx_slot_holds_expires
    ON core.slot_holds(expires_at) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_agreement_templates_type
    ON core.agreement_templates(agreement_type, is_active);

-- =====================================================
-- 6. SEED INITIAL AGREEMENT TEMPLATES
-- =====================================================

-- Liability Waiver Template v2025.1.0
INSERT INTO core.agreement_templates (
    agreement_type, version, title, content_markdown, effective_date, variable_refs
) VALUES (
    'liability_waiver',
    '2025.1.0',
    'Service Agreement & Liability Waiver',
    $TEMPLATE$
# My Hibachi Chef Service Agreement & Liability Waiver

**Effective Date:** {{EFFECTIVE_DATE}}

## 1. SERVICE AGREEMENT

By signing below, I ("Customer") agree to engage My Hibachi Chef ("Company") to provide hibachi catering services for my event.

### Event Details
- **Deposit Required:** ${{DEPOSIT_AMOUNT}} (non-refundable within 4 days of event)
- **Minimum Order:** ${{PARTY_MINIMUM}}
- **Pricing:** ${{ADULT_PRICE}}/adult (13+), ${{CHILD_PRICE}}/child (6-12), free under {{CHILD_FREE_AGE}}

## 2. LIABILITY LIMITATIONS

### 2.1 Food Safety Acknowledgment
Customer acknowledges and agrees that:

1. **Cooking Environment**: Hibachi cooking involves raw proteins being prepared and cooked at Customer's chosen venue. Customer is responsible for providing adequate ventilation, a level cooking surface, and access to running water.

2. **Temperature Control**: Our chefs transport ingredients in temperature-controlled coolers and cook all proteins to FDA-recommended internal temperatures. Customer acknowledges that once our chef departs, Customer assumes responsibility for proper storage of any leftover food.

3. **Allergen Disclosure**: Customer MUST disclose all known food allergies at time of booking. Our equipment is used across multiple events and a completely allergen-free environment CANNOT be guaranteed. Failure to disclose known allergies releases My Hibachi Chef from liability for allergen-related reactions.

4. **Third-Party Food**: My Hibachi Chef is NOT responsible for any food, beverages, ice, or other consumables not prepared by our chefs, including items provided by Customer, guests, or other vendors at the same event.

5. **Post-Service Storage**: Any food not consumed within 2 hours of service should be refrigerated to 40°F or below. My Hibachi Chef is not responsible for illness resulting from improperly stored leftovers.

### 2.2 Facility & Allergen Information

**ALLERGENS PRESENT IN OUR MENU:**
- Shellfish (shrimp, scallops, lobster, calamari)
- Fish (salmon)
- Soy (soy sauce, tamari available as alternative)
- Eggs (in fried rice only)
- Wheat/Gluten (soy sauce, noodles - gluten-free options available)
- Sesame (sesame oil, seeds - can be omitted upon request)

**ALLERGEN-FRIENDLY ADVANTAGES:**
- ✅ 100% NUT-FREE facility (no peanuts or tree nuts)
- ✅ DAIRY-FREE cooking (we use dairy-free butter)
- ✅ Halal-certified proteins available
- ✅ Gluten-free soy sauce available upon request

### 2.3 Foodborne Illness Claims

Customer acknowledges the following claim requirements:

1. **Reporting Window**: Any suspected foodborne illness must be reported within 72 hours of the event via email to claims@myhibachichef.com.

2. **Documentation Required**: Claims must include:
   - Description of symptoms and onset time
   - Names and contact information of all affected guests
   - Medical documentation (doctor visit, diagnosis)
   - Written statement confirming no other restaurant meals consumed within 48 hours prior

3. **Multiple Affected Guests**: Due to the statistical nature of foodborne illness, claims involving only 1-2 affected individuals cannot be attributed to event food and will not be processed for refund.

### 2.4 Limitation of Liability

**IN NO EVENT SHALL MY HIBACHI CHEF'S TOTAL LIABILITY EXCEED THE AMOUNT PAID FOR THE EVENT IN QUESTION.**

My Hibachi Chef SHALL NOT be liable for:
- Consequential, incidental, or punitive damages
- Lost wages, business interruption, or economic losses
- Medical expenses beyond the direct refund amount
- Claims submitted outside the 72-hour reporting window
- Claims without required medical documentation
- Claims involving only 1-2 affected individuals
- Illness caused by food not prepared by My Hibachi Chef
- Illness caused by improper storage of leftovers after chef departure
- Allergen reactions when allergens were not disclosed at booking

## 3. CANCELLATION POLICY

- **Deposit Refundable:** If canceled 4+ days before event
- **Deposit Non-Refundable:** Within 4 days of event
- **One Free Reschedule:** If requested 24+ hours before event
- **Additional Reschedules:** $100 fee

## 4. ACKNOWLEDGMENT

By signing below, I confirm that:
- I have read and understand this agreement
- I have disclosed all known food allergies for my guests
- I accept the liability limitations stated herein
- I am authorized to agree on behalf of all guests

**Customer Signature:** ___________________________

**Date:** {{SIGNATURE_DATE}}
$TEMPLATE$,
    '2025-01-01',
    ARRAY['EFFECTIVE_DATE', 'DEPOSIT_AMOUNT', 'PARTY_MINIMUM', 'ADULT_PRICE', 'CHILD_PRICE', 'CHILD_FREE_AGE', 'SIGNATURE_DATE']
) ON CONFLICT (agreement_type, version) DO NOTHING;

-- Allergen Disclosure Template v2025.1.0
INSERT INTO core.agreement_templates (
    agreement_type, version, title, content_markdown, effective_date, variable_refs
) VALUES (
    'allergen_disclosure',
    '2025.1.0',
    'Allergen Disclosure & Acknowledgment',
    $TEMPLATE$
# Allergen Disclosure & Acknowledgment

## Allergens Present in Our Menu

The following allergens ARE present in our standard hibachi menu:

| Allergen | Present In | Can Be Avoided? |
|----------|-----------|-----------------|
| 🦐 **Shellfish** | Shrimp, Scallops, Lobster, Calamari | ✅ Yes - select other proteins |
| 🐟 **Fish** | Salmon | ✅ Yes - select other proteins |
| 🫘 **Soy** | Soy sauce | ✅ Yes - request tamari or coconut aminos |
| 🥚 **Eggs** | Fried rice | ✅ Yes - request eggless fried rice |
| 🌾 **Wheat/Gluten** | Soy sauce, Noodles | ✅ Yes - request gluten-free soy sauce |
| 🌱 **Sesame** | Sesame oil, sesame seeds | ✅ Yes - request sesame-free preparation |

## Our Allergen-Friendly Advantages

✅ **100% NUT-FREE** - No peanuts or tree nuts in our facility
✅ **DAIRY-FREE** - We use dairy-free butter for all cooking
✅ **Halal-Certified** - Proteins from Restaurant Depot
✅ **Gluten-Free Options** - Tamari/gluten-free soy sauce available

## Cross-Contamination Notice

⚠️ **IMPORTANT:** We use shared cooking surfaces (hibachi grill), shared utensils, and shared oil. While we take precautions, we **CANNOT GUARANTEE** a 100% allergen-free environment.

## Guest Allergies

Please list all known food allergies for your event guests:

**Common Allergens:** {{SELECTED_ALLERGENS}}

**Other Allergies/Dietary Needs:** {{OTHER_ALLERGIES}}

## Acknowledgment

By signing below, I confirm that:
- I have disclosed all known allergies for my guests
- I understand cross-contamination is possible
- I take responsibility for informing guests about allergen risks
- I release My Hibachi Chef from liability for undisclosed allergies

**Customer Signature:** ___________________________

**Date:** {{SIGNATURE_DATE}}
$TEMPLATE$,
    '2025-01-01',
    ARRAY['SELECTED_ALLERGENS', 'OTHER_ALLERGIES', 'SIGNATURE_DATE']
) ON CONFLICT (agreement_type, version) DO NOTHING;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency)
-- =====================================================
-- DROP TABLE IF EXISTS core.slot_holds CASCADE;
-- DROP TABLE IF EXISTS core.allergen_disclosures CASCADE;
-- DROP TABLE IF EXISTS core.signed_agreements CASCADE;
-- DROP TABLE IF EXISTS core.agreement_templates CASCADE;
-- DROP FUNCTION IF EXISTS core.prevent_signed_agreement_update();
