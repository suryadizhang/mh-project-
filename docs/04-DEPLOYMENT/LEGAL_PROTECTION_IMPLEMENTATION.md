# Legal Protection & Food Safety Implementation Plan

**Created:** December 27, 2025 **Version:** 1.0.0 **Purpose:**
Comprehensive legal protection for My Hibachi catering operations
**Record Retention:** 7 YEARS (all signed agreements, documentation,
incident records)

---

## User Decisions (December 27, 2025)

| Item                       | User Decision                                                 | Implementation |
| -------------------------- | ------------------------------------------------------------- | -------------- |
| **Digital Signature**      | D1) Hybrid SignaturePad + timestamp + email PDF               | Batch 1.x      |
| **Allergen System**        | D1) Required + SMS confirmation (all channels)                | Batch 1.x      |
| **Chef Dashboard**         | C1) GCal sync + Web dashboard                                 | Batch 2-3      |
| **Chef Workflow**          | B+C Hybrid (4 taps, 4 photos, weekly health, system does 90%) | Batch 2-3      |
| **Claim Policy**           | E1) Enhanced policy + pre-event health notice                 | Batch 1.x      |
| **Photo Documentation**    | Manual uploads + thermometer photos                           | Batch 2-3      |
| **Third-Party Disclaimer** | Include in Terms of Service                                   | Batch 1.x      |
| **Chef Certification**     | Database tracking + expiration alerts                         | Batch 2        |

---

## Implementation Phases

### BATCH 1.X: Legal Foundation (CRITICAL)

**Target:** Before any public launch **Effort:** 15-20 hours total

#### 1.1 Digital Agreement System (8-10 hours)

**Database Schema:**

```sql
CREATE TABLE core.signed_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES core.customers(id),
    agreement_type VARCHAR(50) NOT NULL, -- 'liability_waiver', 'allergen_disclosure'
    agreement_version VARCHAR(20) NOT NULL, -- '2025.1'
    agreement_text TEXT NOT NULL, -- Full text at time of signing

    -- Signature data
    signature_image BYTEA, -- PNG of canvas signature
    signature_typed_name VARCHAR(200), -- If typed instead of drawn
    signed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Verification data
    signer_ip_address INET,
    signer_user_agent TEXT,
    signer_device_fingerprint VARCHAR(500),

    -- Confirmation
    confirmation_email_sent_at TIMESTAMPTZ,
    confirmation_pdf_url TEXT, -- S3/R2 URL to PDF copy

    -- Multi-channel tracking
    signing_method VARCHAR(20) NOT NULL, -- 'online', 'sms_link', 'phone', 'in_person', 'ai_chat'

    -- Immutability
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- No updated_at - agreements are NEVER modified

    CONSTRAINT signed_agreements_immutable CHECK (
        -- Prevent any updates via application-level check
        TRUE
    )
);

-- Index for quick lookups
CREATE INDEX idx_signed_agreements_booking ON core.signed_agreements(booking_id);
CREATE INDEX idx_signed_agreements_customer ON core.signed_agreements(customer_id);
CREATE INDEX idx_signed_agreements_date ON core.signed_agreements(signed_at);

-- 7-year retention policy (handled by archival job)
COMMENT ON TABLE core.signed_agreements IS 'Immutable record of signed agreements. Retain for 7 years minimum.';
```

**Agreement Versions Table:**

```sql
CREATE TABLE core.agreement_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content_markdown TEXT NOT NULL, -- Template with {{variables}}
    effective_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id),

    UNIQUE(agreement_type, version)
);

-- Seed initial templates
INSERT INTO core.agreement_templates (agreement_type, version, title, content_markdown, effective_date) VALUES
('liability_waiver', '2025.1', 'Service Agreement & Liability Waiver', '...', '2025-01-01'),
('allergen_disclosure', '2025.1', 'Allergen Disclosure & Acknowledgment', '...', '2025-01-01');
```

**Backend Services:**

```
apps/backend/src/services/agreements/
├── agreement_service.py      # Create, retrieve agreements
├── signature_service.py      # Handle signature capture
├── pdf_generator.py          # Generate confirmation PDFs
└── sms_signing_service.py    # Send signing links via SMS
```

**API Endpoints:**

```
POST /api/v1/agreements/sign              # Sign agreement (online)
POST /api/v1/agreements/send-link         # Send SMS/email signing link
GET  /api/v1/agreements/status/{booking}  # Check if signed
GET  /api/v1/agreements/{id}/pdf          # Download PDF copy
POST /api/v1/agreements/verify            # Verify agreement exists
```

**Frontend Components:**

```
apps/customer/src/components/agreements/
├── AgreementViewer.tsx       # Display agreement text
├── SignaturePad.tsx          # Canvas for drawing signature
├── SignatureCapture.tsx      # Combined UI for signing
└── AgreementConfirmation.tsx # Success + PDF download

apps/customer/src/app/sign/[token]/page.tsx  # SMS link landing page
```

**Email/SMS Templates:**

```
SMS (for non-online bookings):
"Hi {{name}}! Your My Hibachi event is booked for {{date}}.
Please review and sign the service agreement to confirm: {{link}}
This must be completed before your event."

Email Confirmation:
Subject: "Your My Hibachi Service Agreement - Signed ✓"
- Thank you message
- PDF attachment of signed agreement
- Event details summary
- Allergen reminder
```

**Tasks:**

```markdown
□ Create signed_agreements table migration □ Create
agreement_templates table migration □ Seed liability waiver template
(v2025.1) □ Seed allergen disclosure template (v2025.1) □ Install
signature_pad npm package □ Create SignaturePad.tsx component □ Create
SignatureCapture.tsx (full signing UI) □ Create agreement_service.py □
Create pdf_generator.py (use reportlab or weasyprint) □ Create POST
/api/v1/agreements/sign endpoint □ Create signing link system for
phone/text bookings □ Create /sign/[token] page for SMS links □ Add
agreement step to online booking flow □ Create email confirmation
template □ Create SMS signing request template □ Test: Online signing
flow □ Test: SMS link signing flow □ Test: PDF generation and storage
□ Test: 7-year retention verified
```

#### 1.2 Allergen Disclosure System (4-6 hours)

**Database Schema:**

```sql
-- Add to core.bookings table
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    allergen_disclosure TEXT;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    common_allergens JSONB DEFAULT '[]'::jsonb;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    allergen_confirmed BOOLEAN DEFAULT false;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    allergen_confirmed_at TIMESTAMPTZ;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    allergen_confirmed_method VARCHAR(20); -- 'online', 'sms', 'phone', 'in_person'

-- Common allergens reference
CREATE TABLE IF NOT EXISTS core.common_allergens (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

INSERT INTO core.common_allergens (name, display_name, icon, display_order) VALUES
('shellfish', 'Shellfish (shrimp, crab, lobster)', '🦐', 1),
('fish', 'Fish', '🐟', 2),
('soy', 'Soy', '🫘', 3),
('sesame', 'Sesame', '🌱', 4),
('eggs', 'Eggs', '🥚', 5),
('wheat', 'Wheat/Gluten', '🌾', 6),
('peanuts', 'Peanuts', '🥜', 7),
('tree_nuts', 'Tree Nuts', '🌰', 8),
('dairy', 'Dairy/Milk', '🥛', 9),
('msg', 'MSG Sensitivity', '⚠️', 10);
```

**Booking Form Updates:**

```typescript
// Required allergen section in booking form
interface AllergenDisclosure {
  commonAllergens: string[]; // ['shellfish', 'soy']
  otherAllergens: string; // Free text
  confirmed: boolean; // "I have asked all guests"
}

// Validation: Cannot submit without confirmation
const allergenSchema = z.object({
  commonAllergens: z.array(z.string()),
  otherAllergens: z.string().max(500),
  confirmed: z.literal(true, {
    errorMap: () => ({
      message:
        'You must confirm you have asked all guests about allergies',
    }),
  }),
});
```

**24-Hour Reminder:**

```
SMS/Email sent 24 hours before event:

"Your My Hibachi event is tomorrow! 🎉

ALLERGEN REMINDER:
You indicated: {{allergens_or_none}}

If this has changed, please update now: {{link}}

⚠️ HEALTH NOTICE:
To protect all guests, please ensure no one attends who has
experienced vomiting, diarrhea, or fever in the past 48 hours.

See you tomorrow!
- My Hibachi Team"
```

**Tasks:**

```markdown
□ Add allergen columns to bookings table □ Create common_allergens
reference table □ Create AllergenSelector component □ Add allergen
step to booking form (required) □ Validation: Block submission without
confirmation □ Create allergen confirmation SMS for phone bookings □
Add allergen section to signed agreement □ Create 24-hour allergen
reminder job □ Include health notice in reminder □ Test: Online
allergen disclosure □ Test: SMS confirmation flow □ Test: Reminder
sends correctly
```

#### 1.3 Terms of Service Updates (2-3 hours)

**Sections to Add:**

```markdown
## LIABILITY LIMITATIONS

### Food Safety Acknowledgment

Customer acknowledges and agrees that:

1. **Cooking Environment**: Hibachi cooking involves raw proteins
   being prepared and cooked at Customer's chosen venue. Customer is
   responsible for providing adequate ventilation, a level cooking
   surface, and access to running water.

2. **Temperature Control**: Our chefs transport ingredients in
   temperature- controlled coolers and cook all proteins to
   FDA-recommended internal temperatures. Customer acknowledges that
   once our chef departs, Customer assumes responsibility for proper
   storage of any leftover food.

3. **Allergen Disclosure**: Customer MUST disclose all known food
   allergies at time of booking. Customer acknowledges that our
   equipment is used across multiple events and a completely
   allergen-free environment cannot be guaranteed. Failure to disclose
   known allergies releases My Hibachi from liability for
   allergen-related reactions.

4. **Third-Party Food**: My Hibachi is not responsible for any food,
   beverages, ice, or other consumables not prepared by our chefs,
   including items provided by Customer, guests, or other vendors at
   the same event.

5. **Post-Service Storage**: Any food not consumed within 2 hours of
   service should be refrigerated to 40°F or below. My Hibachi is not
   responsible for illness resulting from improperly stored leftovers.

### Foodborne Illness Claims

Customer acknowledges the following claim requirements:

1. **Reporting Window**: Any suspected foodborne illness must be
   reported within 72 hours of the event via email to
   claims@myhibachichef.com.

2. **Documentation Required**: Claims must include:
   - Description of symptoms and onset time
   - Names and contact information of all affected guests
   - Medical documentation (doctor visit, diagnosis, lab results if
     applicable)
   - Written statement confirming no other restaurant meals consumed
     within 48 hours prior to symptom onset

3. **Multiple Affected Guests**: Due to the statistical nature of
   foodborne illness, claims involving only 1-2 affected individuals
   cannot be attributed to event food and will not be processed for
   refund.

4. **Timeline Consistency**: Symptom onset must be consistent with
   known incubation periods for foodborne pathogens. Claims with
   inconsistent timelines may be denied.

5. **Norovirus Clarification**: Norovirus (commonly called "stomach
   flu") spreads person-to-person through direct contact, NOT through
   properly cooked food. If multiple guests develop symptoms 12-48
   hours after an event, it is statistically more likely that an
   infected guest attended the event and transmitted the virus to
   others.

### Limitation of Liability

IN NO EVENT SHALL MY HIBACHI'S TOTAL LIABILITY EXCEED THE AMOUNT PAID
FOR THE EVENT IN QUESTION. MY HIBACHI SHALL NOT BE LIABLE FOR:

- Consequential, incidental, or punitive damages
- Lost wages, business interruption, or economic losses
- Medical expenses beyond the direct refund amount
- Claims submitted outside the 72-hour reporting window
- Claims without required medical documentation
- Claims involving only 1-2 affected individuals
- Illness caused by food not prepared by My Hibachi
- Illness caused by improper storage of leftovers after chef departure
- Allergen reactions when allergens were not disclosed at booking
```

**Tasks:**

```markdown
□ Draft liability waiver content (legal review recommended) □ Draft
allergen acknowledgment content □ Draft foodborne illness claim policy
□ Draft third-party food disclaimer □ Create terms version 2025.1 □
Add to agreement_templates table □ Update Terms of Service page □
Legal review of all language (if available)
```

---

### BATCH 2: Chef Operations (HIGH PRIORITY)

**Target:** After Stripe integration complete **Effort:** 20-25 hours
total

#### 2.1 Chef Certification Tracking (4-6 hours)

**Database Schema:**

```sql
CREATE TABLE IF NOT EXISTS ops.chef_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    certification_type VARCHAR(50) NOT NULL,
    -- 'food_handler', 'servsafe_manager', 'first_aid', 'cpr', 'drivers_license'
    certification_name VARCHAR(200) NOT NULL,
    issuing_authority VARCHAR(200),
    certificate_number VARCHAR(100),
    issued_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    document_url TEXT, -- S3/R2 URL to certificate scan
    verified_by UUID REFERENCES identity.users(id),
    verified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chef_certs_chef ON ops.chef_certifications(chef_id);
CREATE INDEX idx_chef_certs_expiration ON ops.chef_certifications(expiration_date);

-- Expiration alert view
CREATE OR REPLACE VIEW ops.expiring_certifications AS
SELECT
    c.id as chef_id,
    c.name as chef_name,
    c.email as chef_email,
    cert.certification_type,
    cert.certification_name,
    cert.expiration_date,
    cert.expiration_date - CURRENT_DATE as days_until_expiry
FROM ops.chefs c
JOIN ops.chef_certifications cert ON c.id = cert.chef_id
WHERE cert.is_active = true
AND cert.expiration_date <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY cert.expiration_date;
```

**Certification Requirements:**

```python
REQUIRED_CERTIFICATIONS = {
    'food_handler': {
        'name': 'Food Handler Certificate',
        'required': True,
        'blocks_assignment': True,  # Cannot be assigned if expired
    },
    'drivers_license': {
        'name': "Driver's License",
        'required': True,
        'blocks_assignment': True,
    },
}

RECOMMENDED_CERTIFICATIONS = {
    'servsafe_manager': {
        'name': 'ServSafe Manager Certification',
        'required': False,
        'blocks_assignment': False,
    },
    'first_aid': {
        'name': 'First Aid Certification',
        'required': False,
        'blocks_assignment': False,
    },
}
```

**Expiration Alert System:**

```
ALERT SCHEDULE:
- 30 days before: Email to chef + admin notification
- 14 days before: SMS to chef + admin urgent notification
- 7 days before: SMS to chef + admin + block new assignments
- 0 days (expired): Block all assignments, notify admin

ADMIN DASHBOARD:
- List of expiring certifications (next 30 days)
- List of expired certifications (blocking assignments)
- Upload/verify new certificates
```

**Tasks:**

```markdown
□ Create chef_certifications table migration □ Create certification
requirements config □ Create expiration alert cron job □ Admin UI:
Certification management □ Admin UI: Expiring certs dashboard □ Block
chef assignment if required cert expired □ Email/SMS templates for
expiration alerts □ Test: Expiration alerts send correctly □ Test:
Assignment blocking works
```

#### 2.2 Chef Prep Checklist & Event Dashboard (8-10 hours)

**Design Principle:** System does 90% of the work. Chef sees ORDER
COUNTS (not calculated quantities - chef knows how much per order).

**Chef Prep Checklist UI (Mobile-First):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📦 PREP SUMMARY                          Event: Smith Family    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 📅 Tonight 6:00 PM | 15 guests (30 protein selections)         │
│                                                                  │
│ ⚠️ ALLERGIES ⚠️                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🦐 SHELLFISH (2 guests) → Cook shrimp/calamari LAST,       │ │
│ │                           separate section of grill        │ │
│ │ 🌾 SOY (1 guest) → Use tamari or coconut aminos            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ PROTEIN SELECTIONS (2 per guest = 30 total)                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ BASE PROTEINS (included):                                   │ │
│ │ ├── 🐔 Chicken ......................... 12 selections      │ │
│ │ ├── 🥩 NY Strip Steak .................. 8 selections       │ │
│ │ ├── 🦐 Shrimp .......................... 4 selections       │ │
│ │ ├── 🦑 Calamari ........................ 3 selections       │ │
│ │ └── 🥬 Tofu ............................ 1 selection        │ │
│ │                                                              │ │
│ │ PREMIUM UPGRADES (+$):                                      │ │
│ │ ├── 🍣 Salmon (+$5) .................... 1 selection        │ │
│ │ └── 🦞 Lobster Tail (+$15) ............. 1 selection        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ SIDES (Included with all meals - 15 guests)                     │
│ ├── 🍚 Hibachi Fried Rice ................ 15 portions         │
│ ├── 🥗 House Salad ....................... 15 portions         │
│ ├── 🥒 Hibachi Veggies ................... 15 portions         │
│ └── 🍶 Sake (21+ guests) ................. per adult           │
│                                                                  │
│ ADD-ONS (if ordered)                                            │
│ ├── 🥟 Gyoza ............................. 2 orders            │
│ └── 🍚 Extra Fried Rice .................. 1 add-on            │
│                                                                  │
│ SPECIAL REQUESTS                                                │
│ "No onions for the kids, extra fried rice for grandma"         │
│                                                                  │
│ ─────────────────────────────────────────────────────────────── │
│ 📍 Location: 123 Oak Street, Fremont CA                         │
│ 📞 Customer: (555) 123-4567                                     │
│                                                                  │
│ [📅 Add to Calendar] [📱 Start Checklist]                       │
└─────────────────────────────────────────────────────────────────┘
```

**Allergen Cooking Notes (Auto-Generated):**

```python
ALLERGEN_COOKING_RULES = {
    'shellfish': {
        'icon': '🦐',
        'action': 'Cook shrimp LAST on separate section of grill',
        'contamination_note': 'Use separate utensils for shellfish allergic guests',
    },
    'soy': {
        'icon': '🌾',
        'action': 'Use TAMARI instead of regular soy sauce for this guest',
        'substitution': 'tamari',
    },
    'sesame': {
        'icon': '🫘',
        'action': 'Skip sesame seeds and sesame oil for this guest',
        'omit': ['sesame_seeds', 'sesame_oil'],
    },
    'dairy': {
        'icon': '🥛',
        'action': 'No butter, use oil only for this guest',
        'substitution': 'vegetable_oil',
    },
    'eggs': {
        'icon': '🥚',
        'action': 'No fried rice for egg-allergic guests (or make without egg)',
        'note': 'Standard fried rice contains egg',
    },
    'gluten': {
        'icon': '🌾',
        'action': 'Use tamari (gluten-free soy sauce) for this guest',
        'substitution': 'tamari',
    },
}
```

**Frontend: Chef Mobile App (Progressive Web App)**

```
apps/chef/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Today's events
│   │   ├── event/[id]/page.tsx   # Event details + checklist
│   │   └── history/page.tsx      # Past events
│   ├── components/
│   │   ├── EventCard.tsx
│   │   ├── PrepSummary.tsx       # ORDER COUNTS display
│   │   ├── AllergenAlert.tsx     # Prominent allergy warnings
│   │   ├── EventChecklist.tsx    # 4 tap actions
│   │   ├── PhotoUpload.tsx       # 4 required photos
│   │   └── WeeklyHealthAttestation.tsx
│   └── hooks/
│       ├── useEvents.ts
│       ├── useChecklist.ts
│       └── useGoogleCalendar.ts
```

**Order Count Aggregation Service:**

```python
# services/chef/prep_summary_service.py

async def get_prep_summary(booking_id: UUID) -> PrepSummary:
    """
    Generate prep summary showing ORDER COUNTS by item.
    Chef knows how much per order - we just show counts.
    """
    booking = await get_booking_with_orders(booking_id)

    summary = {
        'event_info': {
            'customer_name': booking.customer_name,
            'event_time': booking.event_datetime,
            'total_guests': booking.total_guests,
            'venue_address': booking.venue_address,
            'customer_phone': booking.customer_phone,
        },
        'allergens': [
            {
                'allergen': a.allergen_type,
                'icon': ALLERGEN_ICONS[a.allergen_type],
                'guest_count': a.guest_count,
                'cooking_action': ALLERGEN_COOKING_RULES[a.allergen_type]['action'],
            }
            for a in booking.allergens
        ],
        'proteins': aggregate_orders_by_category(booking.orders, 'protein'),
        'sides': {
            'fried_rice': booking.total_guests,  # 1 per guest
            'salad': booking.total_guests,       # 1 per guest
            'veggies': booking.total_guests,     # 1 per guest
        },
        'addons': aggregate_orders_by_category(booking.orders, 'addon'),
        'special_requests': booking.special_requests,
    }

    return PrepSummary(**summary)

def aggregate_orders_by_category(orders: list, category: str) -> dict:
    """Group orders and count by menu item."""
    result = {}
    for order in orders:
        if order.category == category:
            if order.item_name not in result:
                result[order.item_name] = {
                    'name': order.item_name,
                    'icon': order.icon,
                    'count': 0,
                }
            result[order.item_name]['count'] += 1
    return list(result.values())
```

**4-Tap Event Checklist Workflow (B+C Hybrid - MINIMAL CHEF INPUT):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 EVENT CHECKLIST                        Smith Family Hibachi  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                  │
│  TAP 1: HEALTH CHECK                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✅ Weekly Health Attestation: Valid until Jan 3, 2026      ││
│  │ [Tap if you feel unwell today]                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  TAP 2: ARRIVED                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 📸 Photo 1: Cooler Thermometer (<40°F)     [Take Photo]    ││
│  │ 📸 Photo 2: Venue Arrival                  [Take Photo]    ││
│  │ [I've Arrived at Venue]                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  TAP 3: ALLERGIES CONFIRMED                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ⚠️ Shellfish (2), Soy (1)                                  ││
│  │ [I confirmed allergies verbally with host]                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  TAP 4: COMPLETE                                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 📸 Photo 3: Cooking (optional but recommended)  [Take]     ││
│  │ 📸 Photo 4: Completed Service               [Take Photo]   ││
│  │ [Event Complete - All Guests Served]                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  📝 Incident? [Report an Issue]                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Simplified 4-Photo Requirements:** | Photo | When | Required | What
to Capture | |-------|------|----------|-----------------| | 1. Cooler
Temp | Before departure | ✅ YES | Thermometer showing <40°F | | 2.
Arrival | At venue | ✅ YES | Setup area at venue | | 3. Cooking |
During cooking | ⬜ Optional | Grill in action (recommended) | | 4.
Completion | After service | ✅ YES | Finished plates or happy guests
|

**GPS Capture Strategy (Automatic from Photos):**

```python
# Extract GPS from photo EXIF data - no manual tracking needed
async def extract_photo_location(photo_bytes: bytes) -> dict:
    """
    Extract GPS coordinates from photo EXIF metadata.
    iPhone/Android cameras embed location automatically.
    """
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS

    img = Image.open(BytesIO(photo_bytes))
    exif = img._getexif()

    gps_info = {}
    if exif:
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'GPSInfo':
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value

    if gps_info:
        lat = convert_gps_to_decimal(gps_info.get('GPSLatitude'), gps_info.get('GPSLatitudeRef'))
        lng = convert_gps_to_decimal(gps_info.get('GPSLongitude'), gps_info.get('GPSLongitudeRef'))
        return {'lat': lat, 'lng': lng, 'captured_at': exif_datetime}

    return None  # Photo location not available
```

````

**Event Checklist Database:**
```sql
CREATE TABLE IF NOT EXISTS ops.event_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),

    -- Health attestation
    health_attestation_confirmed BOOLEAN DEFAULT false,
    health_attestation_at TIMESTAMPTZ,

    -- Pre-departure
    equipment_sanitized BOOLEAN DEFAULT false,
    cooler_temp_departure DECIMAL(5,2),
    cooler_temp_photo_url TEXT,
    supplies_loaded BOOLEAN DEFAULT false,

    -- Arrival
    arrival_time TIMESTAMPTZ,
    arrival_gps_lat DECIMAL(10,8),
    arrival_gps_lng DECIMAL(11,8),
    food_temp_arrival DECIMAL(5,2),
    setup_photo_url TEXT,
    allergens_confirmed_verbally BOOLEAN DEFAULT false,
    waiver_signed_onsite BOOLEAN DEFAULT false,

    -- Cooking
    cooking_start_time TIMESTAMPTZ,
    protein_internal_temp DECIMAL(5,2),
    cooking_photo_url TEXT,

    -- Completion
    serving_complete_time TIMESTAMPTZ,
    completion_photo_url TEXT,
    station_cleaned BOOLEAN DEFAULT false,
    customer_satisfaction_confirmed BOOLEAN DEFAULT false,

    -- Departure
    departure_time TIMESTAMPTZ,
    departure_gps_lat DECIMAL(10,8),
    departure_gps_lng DECIMAL(11,8),

    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed'
    submitted_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_checklists_booking ON ops.event_checklists(booking_id);
CREATE INDEX idx_event_checklists_chef ON ops.event_checklists(chef_id);
````

**Google Calendar Integration:**

```python
# services/chef/google_calendar_service.py

async def sync_event_to_gcal(booking: Booking, chef: Chef) -> str:
    """Create/update Google Calendar event for chef."""

    event = {
        'summary': f'{booking.customer_name} Hibachi ({booking.total_guests} guests)',
        'location': booking.venue_address,
        'description': f"""
⚠️ ALLERGIES: {booking.allergen_summary or 'None disclosed'}

📦 View Supplies & Checklist:
{settings.CHEF_APP_URL}/event/{booking.id}

📞 Customer: {booking.customer_phone}

Special Requests:
{booking.special_requests or 'None'}
        """,
        'start': {
            'dateTime': booking.event_datetime.isoformat(),
            'timeZone': booking.timezone,
        },
        'end': {
            'dateTime': (booking.event_datetime + timedelta(hours=2)).isoformat(),
            'timeZone': booking.timezone,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 120},  # 2 hours before
                {'method': 'popup', 'minutes': 60},   # 1 hour before
            ],
        },
    }

    # Create or update event
    if booking.gcal_event_id:
        result = gcal_service.events().update(
            calendarId=chef.gcal_calendar_id,
            eventId=booking.gcal_event_id,
            body=event
        ).execute()
    else:
        result = gcal_service.events().insert(
            calendarId=chef.gcal_calendar_id,
            body=event
        ).execute()

    return result['id']
```

**Tasks:**

```markdown
□ Create event_checklists table migration (simplified version) □
Design chef PWA (mobile-first) □ Create PrepSummary component (ORDER
COUNTS, not quantities) □ Create AllergenAlert with cooking action
tips □ Create 4-tap EventChecklist component □ Create PhotoUpload with
EXIF GPS extraction □ Create WeeklyHealthAttestation component □
Google Calendar deep link integration □ OAuth flow for chef GCal
connection (one-time setup) □ Test: Full 4-tap event workflow □ Test:
Photo uploads with GPS extraction □ Test: GCal creates events with
prep link
```

#### 2.3 Photo Documentation System (4-6 hours)

**Photo Upload Service:**

```python
# services/chef/photo_documentation_service.py

REQUIRED_PHOTOS = {
    'cooler_temp_departure': {
        'name': 'Cooler Temperature at Departure',
        'required': True,
        'description': 'Photo of cooler thermometer showing temperature below 40°F'
    },
    'setup_photo': {
        'name': 'Setup Before Cooking',
        'required': True,
        'description': 'Photo of cooking station at venue before cooking begins'
    },
    'protein_temp': {
        'name': 'Protein Internal Temperature',
        'required': False,  # Recommended but not blocking
        'description': 'Photo of meat thermometer showing 165°F+'
    },
    'completion_photo': {
        'name': 'Completed Service',
        'required': True,
        'description': 'Photo of finished presentation or served plates'
    },
}

async def upload_event_photo(
    booking_id: UUID,
    photo_type: str,
    file: UploadFile,
    chef_id: UUID
) -> str:
    """Upload photo with metadata."""

    # Validate photo type
    if photo_type not in REQUIRED_PHOTOS:
        raise ValueError(f"Invalid photo type: {photo_type}")

    # Generate unique filename
    filename = f"events/{booking_id}/{photo_type}_{uuid4()}.jpg"

    # Upload to S3/R2
    url = await storage.upload(filename, file)

    # Store metadata
    await db.execute(
        """
        INSERT INTO ops.event_photos (booking_id, chef_id, photo_type, url, captured_at)
        VALUES ($1, $2, $3, $4, NOW())
        """,
        booking_id, chef_id, photo_type, url
    )

    return url
```

**Tasks:**

```markdown
□ Create event_photos table □ Create photo upload API endpoint □
Create PhotoUpload component with camera access □ Validate required
photos before checklist submission □ Photo retention: 7 years
(configure storage lifecycle) □ Admin view: Photos for any event □
Test: Photo upload from mobile □ Test: EXIF data preserved (timestamp,
location)
```

---

### BATCH 3-4: Advanced Operations

#### 3.1 Incident Response System (6-8 hours)

**Database Schema:**

```sql
CREATE TABLE IF NOT EXISTS core.incident_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES core.bookings(id),
    customer_id UUID REFERENCES core.customers(id),

    -- Report details
    incident_type VARCHAR(50) NOT NULL,
    -- 'foodborne_illness', 'injury', 'property_damage', 'complaint', 'other'
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reported_by VARCHAR(200) NOT NULL, -- Name of reporter
    reported_via VARCHAR(50) NOT NULL, -- 'phone', 'email', 'form', 'social_media'

    -- Incident details
    description TEXT NOT NULL,
    affected_guests_count INT,
    affected_guests_names TEXT[], -- Array of names
    symptom_onset_time TIMESTAMPTZ,
    symptoms_description TEXT,

    -- Documentation
    medical_docs_received BOOLEAN DEFAULT false,
    medical_docs_urls TEXT[],
    other_restaurants_48hrs TEXT,
    other_food_at_event TEXT,

    -- Investigation
    investigation_status VARCHAR(50) DEFAULT 'new',
    -- 'new', 'investigating', 'pending_docs', 'resolved', 'escalated_legal'
    assigned_to UUID REFERENCES identity.users(id),
    investigation_notes TEXT,
    chef_statement TEXT,

    -- Resolution
    resolution_type VARCHAR(50),
    -- 'no_action', 'partial_refund', 'full_refund', 'insurance_claim', 'legal'
    refund_amount DECIMAL(10,2),
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES identity.users(id),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incidents_booking ON core.incident_reports(booking_id);
CREATE INDEX idx_incidents_status ON core.incident_reports(investigation_status);
```

**Incident Workflow:**

```
NEW INCIDENT
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: IMMEDIATE RESPONSE (0-2 hours)                         │
│ □ Log incident with all details                                 │
│ □ Send acknowledgment to reporter                               │
│ □ Pull booking details and chef checklist                       │
│ □ DO NOT admit fault or promise refund                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: INVESTIGATION (2-72 hours)                             │
│ □ Contact chef for their account                                │
│ □ Review event checklist and photos                             │
│ □ Check other events same day (same ingredients?)               │
│ □ Request medical documentation from customer                   │
│ □ Verify timeline matches pathogen incubation                   │
│ □ Check if other food vendors at event                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: DETERMINATION                                          │
│                                                                  │
│ EVIDENCE INSUFFICIENT:          EVIDENCE SUPPORTS CLAIM:        │
│ - Only 1-2 affected             - 3+ affected                   │
│ - No medical docs               - Medical docs received         │
│ - Timeline inconsistent         - Timeline consistent           │
│ - Other food sources            - No other sources              │
│         │                               │                        │
│         ▼                               ▼                        │
│  [DENY - No Refund]              [APPROVE - Refund/Claim]       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: RESOLUTION                                             │
│ □ Communicate decision to customer                              │
│ □ Process refund if applicable                                  │
│ □ File insurance claim if applicable                            │
│ □ Document lessons learned                                      │
│ □ Close incident                                                │
└─────────────────────────────────────────────────────────────────┘
```

**Tasks:**

```markdown
□ Create incident_reports table migration □ Create incident submission
form (public) □ Create admin incident dashboard □ Create incident
workflow UI □ Create investigation checklist □ Email templates for
each stage □ Integration with booking/chef data □ Resolution tracking
□ Reporting: Incident trends □ Test: Full incident workflow
```

#### 3.1.1 Chef In-App Incident Reporting (Simpler than Google Docs)

**Design Decision:** In-app form instead of Google Docs

- Pre-filled with event data (no typing for chef)
- Works offline, syncs when connected
- Same database as customer incidents
- Faster for chef, more reliable

**Chef Incident Form UI:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 📝 REPORT AN ISSUE                         Smith Family Event   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                  │
│ Event Date: Dec 27, 2025 @ 6:00 PM (auto-filled)                │
│ Venue: 123 Oak Street, Fremont (auto-filled)                    │
│                                                                  │
│ What happened?                                                   │
│ ○ Equipment malfunction                                         │
│ ○ Ingredient issue                                              │
│ ○ Customer complaint                                            │
│ ○ Injury (guest or self)                                        │
│ ○ Property damage                                               │
│ ○ Other                                                         │
│                                                                  │
│ Describe what happened:                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                              │ │
│ │                                                              │ │
│ │                                                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 📸 Add Photos (optional)                    [Take Photo]        │
│                                                                  │
│ Was anyone hurt?  ○ No  ○ Yes → [How many? ___]                │
│                                                                  │
│ [Submit Report]                                                  │
│                                                                  │
│ ⚠️ Your station manager will be notified immediately.           │
└─────────────────────────────────────────────────────────────────┘
```

**Chef Incident Service:**

```python
# services/chef/incident_service.py

async def create_chef_incident_report(
    booking_id: UUID,
    chef_id: UUID,
    incident_type: str,
    description: str,
    photos: list[str] = None,
    injury_count: int = 0,
) -> IncidentReport:
    """
    Create incident report from chef app.
    Pre-fills event data automatically.
    """
    booking = await get_booking(booking_id)
    chef = await get_chef(chef_id)

    report = await db.execute(
        """
        INSERT INTO core.incident_reports (
            booking_id, customer_id, incident_type,
            reported_by, reported_via, description,
            affected_guests_count, investigation_status
        ) VALUES ($1, $2, $3, $4, 'chef_app', $5, $6, 'new')
        RETURNING *
        """,
        booking_id,
        booking.customer_id,
        incident_type,
        f"Chef: {chef.name}",
        description,
        injury_count
    )

    # Notify station manager immediately
    await send_incident_alert(
        station_id=chef.station_id,
        incident_id=report.id,
        urgency='high' if injury_count > 0 else 'normal'
    )

    return report
```

#### 3.2 Chef Health Attestation - WEEKLY (2-3 hours)

**Design Decision:** Weekly attestation (valid for 7 days), NOT
per-event.

- Reduces chef friction (1x/week vs every event)
- Still provides legal protection
- Alert triggers if symptoms develop mid-week

**Database Schema:**

```sql
CREATE TABLE IF NOT EXISTS ops.chef_health_attestations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    attested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),

    -- Health questions (all must be false to attest)
    symptoms_vomiting BOOLEAN NOT NULL DEFAULT false,
    symptoms_diarrhea BOOLEAN NOT NULL DEFAULT false,
    symptoms_fever BOOLEAN NOT NULL DEFAULT false,
    symptoms_jaundice BOOLEAN NOT NULL DEFAULT false,

    -- Signature
    signature_image BYTEA,
    attestation_ip INET,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_attestation_chef ON ops.chef_health_attestations(chef_id);
CREATE INDEX idx_health_attestation_valid ON ops.chef_health_attestations(valid_until);

-- View: Current valid attestations
CREATE OR REPLACE VIEW ops.chef_health_status AS
SELECT
    c.id as chef_id,
    c.name as chef_name,
    ha.attested_at,
    ha.valid_until,
    CASE
        WHEN ha.valid_until > NOW() THEN 'valid'
        WHEN ha.valid_until IS NULL THEN 'never_attested'
        ELSE 'expired'
    END as attestation_status
FROM ops.chefs c
LEFT JOIN ops.chef_health_attestations ha ON c.id = ha.chef_id
    AND ha.valid_until = (
        SELECT MAX(valid_until)
        FROM ops.chef_health_attestations
        WHERE chef_id = c.id
    );
```

**Weekly Health Attestation UI (Chef App):**

```
┌─────────────────────────────────────────────────────────────────┐
│ 🏥 WEEKLY HEALTH ATTESTATION                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                  │
│ In the past 48 hours, have you experienced any of the           │
│ following symptoms?                                              │
│                                                                  │
│ ○ Vomiting                                                      │
│ ○ Diarrhea                                                      │
│ ○ Fever (100.4°F or higher)                                     │
│ ○ Jaundice (yellowing of skin/eyes)                             │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ By signing below, I attest that I have NOT experienced      │ │
│ │ any of the above symptoms and am fit to handle food.        │ │
│ │                                                              │ │
│ │ [━━━━━━━━━━━━━━━━━━ Signature Pad ━━━━━━━━━━━━━━━━━━━━]      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ⚠️ If you have symptoms, do NOT sign. Contact your station     │
│    manager immediately.                                          │
│                                                                  │
│ [Submit Attestation]                                             │
│                                                                  │
│ ✅ Valid until: January 3, 2026                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Attestation Check Before Event:**

```python
async def check_chef_can_work(chef_id: UUID) -> bool:
    """
    Check if chef has valid health attestation.
    Called before showing event details / allowing check-in.
    """
    status = await db.execute(
        """
        SELECT attestation_status, valid_until
        FROM ops.chef_health_status
        WHERE chef_id = $1
        """,
        chef_id
    )

    if status.attestation_status == 'valid':
        return True

    # Redirect to attestation form
    raise AttestationRequiredError(
        message="Weekly health attestation required",
        redirect_to=f"/health-attestation"
    )
```

**Tasks:**

```markdown
□ Create chef_health_attestations table □ Create chef_health_status
view □ Create WeeklyHealthAttestation component □ Block event access
if attestation expired (>7 days) □ Reminder notification when
attestation expires □ Admin dashboard: Chef attestation status □
Report symptoms button (triggers admin alert)
```

---

## Summary: Updated Batch Implementation

| Phase                | Batch | Component                            | Chef Effort     | Status     |
| -------------------- | ----- | ------------------------------------ | --------------- | ---------- |
| **Legal Foundation** | 1.x   | Digital Signature (SignaturePad)     | N/A             | ⏳ PLANNED |
| **Legal Foundation** | 1.x   | Allergen Disclosure (required + SMS) | N/A             | ⏳ PLANNED |
| **Legal Foundation** | 1.x   | Terms of Service Updates             | N/A             | ⏳ PLANNED |
| **Chef Ops**         | 2     | Chef Certification Tracking          | Upload once     | ⏳ PLANNED |
| **Chef Ops**         | 2-3   | Chef Prep Checklist (ORDER COUNTS)   | View only       | ⏳ PLANNED |
| **Chef Ops**         | 2-3   | 4-Tap Event Checklist                | 4 taps          | ⏳ PLANNED |
| **Chef Ops**         | 2-3   | Photo Documentation                  | 4 photos        | ⏳ PLANNED |
| **Chef Ops**         | 2-3   | Google Calendar Sync                 | 1-click setup   | ⏳ PLANNED |
| **Advanced**         | 3-4   | Weekly Health Attestation            | 1x/week         | ⏳ PLANNED |
| **Advanced**         | 3-4   | In-App Incident Reporting            | Pre-filled form | ⏳ PLANNED |
| **Advanced**         | 3-4   | Incident Investigation (Admin)       | N/A             | ⏳ PLANNED |

### Chef Workflow Summary (B+C Hybrid)

**What System Does (90%):**

- Auto-generates prep checklist from customer orders
- Pre-fills all event data
- Calculates allergen cooking actions
- Syncs to Google Calendar with deep links
- Extracts GPS/timestamp from photos (EXIF)
- Creates incident report pre-filled with event data

**What Chef Does (10%):**

- Weekly health attestation (1x per week)
- 4 taps: Health OK → Arrived → Allergies Confirmed → Complete
- 4 photos: Cooler temp, Arrival, Cooking (optional), Completion
- View prep summary (ORDER COUNTS - chef calculates amounts)

**Allergen Cooking Rules (Auto-Displayed):** | Allergen | Chef Action
| |----------|-------------| | 🦐 Shellfish | Cook shrimp/calamari
LAST on separate section of grill | | 🌾 Soy/Gluten | Use TAMARI or
coconut aminos instead of soy sauce | | 🥛 Dairy | Already dairy-free
by default (we use dairy-free butter) | | 🥚 Eggs | Make fried rice
WITHOUT egg | | 🌱 Sesame | Skip sesame seeds and sesame oil |

> ⚠️ **Customer Responsibility Disclaimer:** Chef allergen
> accommodations require accurate information provided during booking.
> If customers do not disclose all allergies, the chef may not have
> proper alternative ingredients available. My Hibachi cannot
> guarantee allergen-free preparation for undisclosed allergies.

---

## Related Documents

- [SSOT_IMPLEMENTATION_PLAN.md](./SSOT_IMPLEMENTATION_PLAN.md)
- [BATCH_CHECKLISTS.md](./BATCH_CHECKLISTS.md)
- [CURRENT_BATCH_STATUS.md](../../CURRENT_BATCH_STATUS.md)
