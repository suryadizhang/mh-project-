-- =====================================================
-- Migration: 017_agreement_template_v2025.2.0.sql
-- Description: Add enhanced agreement template with new policy sections
-- Author: My Hibachi Dev Agent
-- Date: 2025-02-06
--
-- New Sections Added:
--   - Weather Policy (Section 5)
--   - Guest Count Changes (Section 6)
--   - Menu Change Deadlines (Section 7)
--   - Equipment & Venue Requirements (Section 8, includes tables/chairs)
--   - Property Damage Acknowledgment (Section 9)
--   - Media Release & Photography (Section 10)
--   - Pre-Event Health Requirements (Section 11)
-- =====================================================

-- Deactivate old template version
UPDATE core.agreement_templates
SET is_active = FALSE
WHERE agreement_type = 'liability_waiver' AND version = '2025.1.0';

-- Insert new template version v2025.2.0
INSERT INTO core.agreement_templates (
    agreement_type, version, title, content_markdown, effective_date, variable_refs, is_active
) VALUES (
    'liability_waiver',
    '2025.2.0',
    'Service Agreement & Liability Waiver',
    $TEMPLATE$
# My Hibachi Chef Service Agreement & Liability Waiver

**Effective Date:** {{EFFECTIVE_DATE}}

---

## 1. SERVICE AGREEMENT

By signing below, I ("Customer") agree to engage My Hibachi Chef ("Company") to provide hibachi catering services for my event.

### Event Details
- **Deposit Required:** ${{DEPOSIT_AMOUNT}} (non-refundable within {{DEPOSIT_REFUNDABLE_DAYS}} days of event)
- **Minimum Order:** ${{PARTY_MINIMUM}}
- **Pricing:** ${{ADULT_PRICE}}/adult (13+), ${{CHILD_PRICE}}/child (6-12), free under {{CHILD_FREE_AGE}}

---

## 2. LIABILITY LIMITATIONS

### 2.1 Food Safety Acknowledgment
Customer acknowledges and agrees that:

1. **Cooking Environment**: Hibachi cooking involves raw proteins being prepared and cooked at Customer's chosen venue. Customer is responsible for providing adequate ventilation, a level cooking surface, and access to running water.

2. **Temperature Control**: Our chefs transport ingredients in temperature-controlled coolers and cook all proteins to FDA-recommended internal temperatures (165°F+ for poultry, 145°F+ for beef/seafood). Customer acknowledges that once our chef departs, Customer assumes full responsibility for proper storage of any leftover food.

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

4. **Norovirus Clarification**: Norovirus ("stomach flu") spreads person-to-person through direct contact, NOT through properly cooked food. Our hibachi grill reaches 400°F+, which kills all foodborne pathogens. If multiple guests develop vomiting/diarrhea 12-48 hours after an event, this is more likely person-to-person transmission from an already-infected attendee.

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

---

## 3. CANCELLATION & REFUND POLICY

- **Deposit Refundable:** If canceled {{DEPOSIT_REFUNDABLE_DAYS}}+ days before event
- **Deposit Non-Refundable:** Within {{DEPOSIT_REFUNDABLE_DAYS}} days of event
- **One Free Reschedule:** If requested {{FREE_RESCHEDULE_HOURS}}+ hours before event
- **Additional Reschedules:** $200 fee per reschedule
- **No-Show Policy:** Full event cost is due if Customer cancels within 24 hours or fails to be present at agreed time

---

## 4. PAYMENT TERMS

- **Deposit:** ${{DEPOSIT_AMOUNT}} due at booking (deducted from final bill)
- **Final Balance:** Due on event date or in advance
- **Accepted Methods:** Venmo Business, Zelle Business, Cash, Credit Card
- **Gratuity:** Tips are appreciated and paid directly to your chef (suggested 20-35%)

---

## 5. WEATHER POLICY ⛈️

**Customer is responsible for providing weather-appropriate accommodations for our cooking setup.**

### 5.1 Customer Obligations
- Customer MUST provide overhead covering (tent, patio cover, gazebo, garage, or indoor space) in case of rain, strong winds, or inclement weather
- Customer is responsible for monitoring weather forecasts and having a backup covered location ready
- Our chef reserves the right to cancel or stop service if conditions are unsafe for cooking (heavy rain, lightning, high winds over 25 mph)

### 5.2 No Refund for Weather Issues
- **NO REFUND** will be issued if Customer fails to provide adequate covered setup and weather prevents safe cooking
- If Customer cancels due to weather forecast, standard cancellation policy applies
- If Company cancels due to unsafe conditions (lightning, severe storm warnings), one free reschedule will be offered

### 5.3 Safe Cooking Requirements
- Propane grills cannot be operated in enclosed spaces without proper ventilation
- Chef will assess safety upon arrival and may relocate setup if needed
- Final setup location is at the chef's discretion for safety purposes

---

## 6. GUEST COUNT CHANGES & FINAL CONFIRMATION

### 6.1 Guest Count Deadline
- **Final guest count is required {{GUEST_COUNT_FINALIZE_HOURS}}+ hours before your event**
- We prepare fresh ingredients specifically for your confirmed guest count
- Accurate guest counts ensure proper portions for all attendees

### 6.2 Last-Minute Changes
- Guest count increases within {{GUEST_COUNT_FINALIZE_HOURS}} hours CANNOT be guaranteed (we may not have sufficient ingredients)
- Guest count decreases within {{GUEST_COUNT_FINALIZE_HOURS}} hours are NON-REFUNDABLE (ingredients already purchased and prepared)
- Contact us immediately at (916) 740-8768 if your count changes significantly

### 6.3 Minimum Order
- Event must meet ${{PARTY_MINIMUM}} minimum regardless of actual attendance
- If guests do not show, Customer is still responsible for minimum and confirmed guest count

---

## 7. MENU CHANGE DEADLINES

### 7.1 Menu Finalization
- **Menu selections must be finalized {{MENU_CHANGE_CUTOFF_HOURS}}+ hours before your event**
- Fresh ingredients are purchased specifically for your menu selections
- This includes protein choices, upgrades, add-ons, and dietary accommodations

### 7.2 No Changes After Deadline
- Menu changes ARE NOT allowed within {{MENU_CHANGE_CUTOFF_HOURS}} hours of event
- Dietary restriction requests MUST be submitted at least 48 hours in advance
- Premium upgrade requests after deadline are subject to availability

---

## 8. EQUIPMENT & VENUE REQUIREMENTS

### 8.1 What We Provide
Our chef will bring:
- Portable hibachi grill (dimensions: 68.3"L × 27.5"W × 41.3"H)
- All cooking equipment, utensils, and tools
- Fresh ingredients and proteins
- Propane fuel and safety equipment (fire extinguisher, leak detector)
- Sake for adults 21+ (complimentary)
- Sauces, seasonings, and condiments

### 8.2 What Customer MUST Provide
**⚠️ IMPORTANT: We do NOT provide tables, chairs, or tableware.**

Customer is responsible for:
- **Tables:** For guest seating (U-shape recommended around grill)
- **Chairs:** For all guests
- **Plates, bowls, utensils, glasses:** For each guest
- **Napkins and serving utensils**
- **Beverages:** (except sake which we provide)
- **Ice and coolers** (if needed for beverages)

💡 **Need rental recommendations?** Contact cs@myhibachichef.com and we can recommend party rental companies in your area.

### 8.3 Space Requirements
- Minimum 8×6 feet clear area for grill plus chef working space
- Level, stable ground (concrete, patio, flat grass)
- 10+ feet clearance from any flammable materials (curtains, overhanging plants, structures)
- Access to running water within reasonable distance
- Proper ventilation if indoor (high ceilings, open windows/doors, exhaust fan)

---

## 9. PROPERTY DAMAGE ACKNOWLEDGMENT

### 9.1 Cooking Risks
Customer acknowledges that hibachi cooking involves high heat, oil, and open flame which may cause:
- Smoke and cooking odors
- Grease splatter on nearby surfaces
- Heat marks on surfaces directly under or adjacent to grill
- Discoloration of pavement or grass where grill is placed

### 9.2 Customer Responsibility
- Customer is responsible for selecting an appropriate cooking location
- Customer should protect surfaces with heat-resistant mats or covers if concerned
- Customer assumes responsibility for any damage to their property or venue resulting from normal cooking operations

### 9.3 Company Not Liable
My Hibachi Chef is NOT liable for:
- Damage to patios, decks, grass, or flooring from grill heat
- Smoke damage to ceilings, walls, or furnishings
- Grease stains or splatter on surfaces within cooking area
- Any property damage at the event venue
- Damage caused by guests (children, pets, attendees)

### 9.4 Third-Party Venues
If event is held at a rented venue, HOA facility, or commercial space:
- Customer is responsible for obtaining venue approval for open-flame cooking
- Customer is responsible for any damage deposits or cleaning fees required by venue
- Customer must disclose venue restrictions to My Hibachi Chef before booking

---

## 10. MEDIA RELEASE & PHOTOGRAPHY 📸

### 10.1 Photo/Video Permission
Customer grants My Hibachi Chef permission to:
- Take photographs and videos during the event
- Use images/videos for marketing, social media, website, and promotional materials
- Share event photos on Instagram, Facebook, TikTok, and other platforms
- Feature customer testimonials and reviews (with first name only unless full name authorized)

### 10.2 Customer Content Rights
- Customer retains full rights to their own photos and videos
- Customer may share event content on personal social media
- Customer grants Company permission to repost/share customer-generated content

### 10.3 Opt-Out Option
- Customer may opt-out of all photography by notifying us in writing at cs@myhibachichef.com at least 24 hours before event
- If opted-out, our chef will not take any photos during service
- Customers who opt-out may still be featured in background of other attendees' personal photos (not our responsibility)

### 10.4 Minor Children
- Photography of minor children requires parental/guardian consent
- Guest parents are responsible for consenting to photography of their children
- We will not specifically photograph children without visible parental approval

---

## 11. PRE-EVENT HEALTH REQUIREMENTS 🏥

### 11.1 Sick Guest Policy
**To protect all guests, we require the following health protocols:**

- **Anyone who has experienced vomiting, diarrhea, or fever within the past 48 hours should NOT attend the event**
- Norovirus and other stomach bugs spread extremely easily at gatherings
- Attending while sick puts other guests at serious risk of infection

### 11.2 Host Illness
- If the host (Customer) is ill, please contact us to discuss rescheduling
- We offer flexible rescheduling for documented illness (no additional fee with 24+ hour notice)
- This protects our chef and your guests from potential illness spread

### 11.3 Chef Health Standards
- Our chefs follow strict health protocols and will not work if experiencing any illness symptoms
- If our chef becomes ill, we will provide a replacement chef or offer free rescheduling
- All chefs wash hands frequently and use sanitary food handling practices

---

## 12. ACKNOWLEDGMENT & SIGNATURE

By signing below, I confirm that:

✅ I have read and understand this complete Service Agreement & Liability Waiver

✅ I have disclosed all known food allergies for all guests attending

✅ I accept all liability limitations, including property damage acknowledgment

✅ I understand the weather policy and have a covered backup location

✅ I understand the guest count and menu change deadlines

✅ I understand that My Hibachi Chef does NOT provide tables, chairs, or tableware

✅ I grant permission for photography/video (unless I opt-out in writing)

✅ I am authorized to agree on behalf of all guests attending this event

✅ I agree to inform guests about the pre-event health requirements

---

**Date Signed:** {{SIGNATURE_DATE}}

---

*My Hibachi Chef | (916) 740-8768 | cs@myhibachichef.com | myhibachichef.com*
$TEMPLATE$,
    '2025-02-06',
    ARRAY['EFFECTIVE_DATE', 'DEPOSIT_AMOUNT', 'DEPOSIT_REFUNDABLE_DAYS', 'PARTY_MINIMUM', 'ADULT_PRICE', 'CHILD_PRICE', 'CHILD_FREE_AGE', 'GUEST_COUNT_FINALIZE_HOURS', 'MENU_CHANGE_CUTOFF_HOURS', 'FREE_RESCHEDULE_HOURS', 'SIGNATURE_DATE'],
    TRUE
) ON CONFLICT (agreement_type, version) DO UPDATE SET
    content_markdown = EXCLUDED.content_markdown,
    effective_date = EXCLUDED.effective_date,
    variable_refs = EXCLUDED.variable_refs,
    is_active = EXCLUDED.is_active;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- To rollback this migration, run:
-- UPDATE core.agreement_templates SET is_active = TRUE WHERE agreement_type = 'liability_waiver' AND version = '2025.1.0';
-- DELETE FROM core.agreement_templates WHERE agreement_type = 'liability_waiver' AND version = '2025.2.0';
