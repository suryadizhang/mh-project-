"""
AI Booking Assistant - Comprehensive Dynamic Configuration System

This is the SINGLE SOURCE OF TRUTH for all AI booking assistant knowledge.
All data is synced with customer-facing pages and dynamically loaded.

CRITICAL: This configuration must ALWAYS match these business data sources:
├── apps/customer/src/data/faqsData.ts ........... FAQs, policies, detailed business rules
├── apps/customer/src/components/quote/QuoteCalculator.tsx ... Pricing calculator logic
├── apps/customer/src/app/menu/page.tsx ........... Menu display, pricing cards
├── apps/customer/src/app/terms/page.tsx .......... Terms & conditions, liability
├── apps/customer/src/app/privacy/page.tsx ........ Privacy policy, data handling
├── apps/customer/src/app/BookUs/page.tsx ......... Booking flow, requirements
└── apps/backend/src/api/ai/orchestrator/tools/pricing_tool.py ... Calculation engine

**DYNAMIC DATA PHILOSOPHY:**
This configuration is NOT static. It references the actual calculation logic and business
rules used by the website. When prices change, FAQs update, or policies modify, this
configuration MUST be updated simultaneously to prevent customer confusion.

**AI REASONING MODEL:**
The AI uses this configuration to:
1. Calculate prices using EXACT formulas (not estimates)
2. Explain policies using EXACT wording from Terms & Conditions
3. Answer questions using EXACT data from FAQs
4. Never contradict the website or give wrong information

Last Updated: 2025-11-16
Synced Version: v2.0
"""

# ============================================================================
# BRAND VOICE & PERSONALITY
# ============================================================================

BRAND_PERSONALITY = """You are the AI booking assistant for My Hibachi Chef, a premium hibachi catering service.

**Brand Voice Characteristics:**
- 🌟 Warm & Friendly: Like talking to a trusted friend who's genuinely excited to help
- 💎 Professional: Knowledgeable, reliable, and detail-oriented
- 🎉 Enthusiastic: Show genuine excitement about creating memorable experiences
- 🤝 Helpful: Proactive in answering questions before they're asked
- 💯 Honest: Transparent about pricing, policies, and what to expect

**Communication Style:**
- Use natural, conversational language (avoid corporate jargon)
- Be clear and concise (no walls of text)
- Use emojis tastefully to add warmth (1-3 per message)
- Address customers by name when known
- Show empathy and understanding
- End messages with clear next steps or questions

**Tone Adaptation:**
- Match customer's energy level (formal ↔ casual)
- More reassurance for anxious customers
- More efficiency for direct/busy customers
- Extra warmth for celebrations (birthdays, anniversaries)
- Professional polish for corporate events"""

# ============================================================================
# ACCURATE PRICING DATA (Synced with menu.ts)
# ============================================================================

PRICING = {
    # Base Pricing
    "adult_base": 55,  # Per adult (13+)
    "child_base": 30,  # Per child (6-12 years)
    "children_free_age": 5,  # Ages 5 and under eat free
    "party_minimum": 550,  # Total minimum spend (~10 adults)
    "currency": "USD",
    # Premium Protein Upgrades (PER PERSON)
    "upgrades": {"salmon": 5, "scallops": 5, "filet_mignon": 5, "lobster_tail": 15},
    # Add-On Options (PER PERSON)
    "addons": {
        "yakisoba_noodles": 5,
        "extra_fried_rice": 5,
        "edamame": 5,
        "vegetables": 5,
        "third_protein": 10,
        "gyoza": 10,
    },
    # Deposit & Fees
    "deposit": 100,  # Refundable if canceled 7+ days before event
    "deposit_refundable": True,
    "deposit_refund_days": 7,
    # Travel Fees
    "travel_free_miles": 30,
    "travel_per_mile": 2,
    # Tipping Guidelines
    "tip_suggested_min": 20,  # Percentage
    "tip_suggested_max": 35,  # Percentage
}

# ============================================================================
# MENU & PACKAGES (Synced with faqsData.ts)
# ============================================================================

MENU_ITEMS = {
    "standard_proteins": ["Chicken", "NY Strip Steak", "Shrimp", "Calamari", "Tofu"],
    "premium_proteins": [
        "Salmon (+$5)",
        "Scallops (+$5)",
        "Filet Mignon (+$5)",
        "Lobster Tail (+$15)",
    ],
    "proteins_per_guest": 2,
    "included_items": [
        "Hibachi fried rice",
        "Fresh vegetables",
        "Side salad",
        "Signature sauces (Yum Yum, Ginger, Teriyaki)",
        "Sake for adults 21+",
    ],
    "kids_menu": {
        "age_range": "6-12 years",
        "price": 30,
        "proteins": 2,
        "free_age": "5 and under",
        "free_includes": "1 protein, small rice portion",
    },
}

# ============================================================================
# AI INSTRUCTIONS & REASONING RULES
# ============================================================================

AI_REASONING_RULES = """
**CRITICAL PRICING LOGIC:**

1. MINIMUM ORDER CALCULATION:
   - The minimum is $550 TOTAL DOLLAR AMOUNT (not number of people)
   - This equals approximately 10 adults × $55 = $550
   - ANY party that totals $550+ meets the minimum (could be 10 adults, 9 adults + 7 kids, etc.)
   - Example: 30 people = 30 × $55 = $1,650 → EXCEEDS minimum by $1,100 ✓
   
2. PARTY SIZE CALCULATION:
   - Calculate TOTAL cost first: (# adults × $55) + (# kids × $30)
   - Compare total to $550 minimum
   - If total ≥ $550 → They meet the minimum!
   - DO NOT confuse the $550 minimum with "10 people minimum"
   
3. UPGRADE PRICING:
   - Premium proteins are +$5 per person (Salmon, Scallops, Filet Mignon)
   - Lobster Tail is +$15 per person
   - Example: 30 people with Filet Mignon = (30 × $55) + (30 × $5) = $1,800
   
4. NEVER SAY:
   - ❌ "You need at least 10 adults" (when they already exceed $550 minimum)
   - ❌ "You need 20 adults to meet the minimum" (when 30 people = $1,650)
   - ❌ Confuse dollar amounts with people counts
   
5. ALWAYS CALCULATE:
   - Total party cost = (adults × $55) + (children × $30) + (upgrades if mentioned)
   - Check if total ≥ $550
   - If yes → "Great! Your party total of $[amount] exceeds our $550 minimum"
"""

# ============================================================================
# BUSINESS POLICIES (Synced with faqsData.ts)
# ============================================================================

POLICIES = {
    "booking": {
        "minimum_advance_hours": 48,
        "recommended_weekend_days": 7,  # 1-2 weeks for weekends
        "booking_methods": ["online", "text (916) 740-8768"],
    },
    "payment": {
        "deposit_methods": ["online", "venmo_business", "zelle_business", "credit_card"],
        "balance_methods": ["venmo_business", "zelle_business", "cash", "credit_card"],
        "balance_due": "on event date or in advance",
    },
    "cancellation": {
        "full_refund_days": 7,  # Cancel 7+ days before = full refund
        "non_refundable_days": 7,  # Cancel within 7 days = no refund
    },
    "reschedule": {
        "free_within_hours": 48,  # Free reschedule within 48hrs of booking
        "additional_fee": 100,  # $100 for additional reschedules
    },
    "weather": {
        "requires_covering": True,
        "policy": "Must provide overhead covering (tent, patio, garage) for rain cooking",
    },
    "dietary": {
        "accommodations": ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Halal", "Kosher"],
        "notice_hours": 48,
    },
}

# ============================================================================
# SERVICE AREAS (Synced with faqsData.ts)
# ============================================================================

SERVICE_AREAS = {
    "primary": ["Sacramento", "Bay Area (San Francisco, Oakland, San Jose)", "Central Valley"],
    "extended": ["Coastal communities", "Mountain communities", "Northern California"],
    "verification": "Text (916) 740-8768 with your zip code for confirmation",
}

# ============================================================================
# SETUP REQUIREMENTS (Synced with faqsData.ts)
# ============================================================================

SETUP_REQUIREMENTS = {
    "grill_dimensions": {"length": "68.3 inches", "width": "27.5 inches", "height": "41.3 inches"},
    "space": {
        "requires": "Level ground, clear area for grill",
        "location": "Outdoor space or well-ventilated indoor area",
        "table_access": "Guests need to sit around grill for show",
    },
    "table_setup": {
        "layout": "U-shape with grill at open end",
        "example_10_people": "Two 8-foot tables",
        "example_15_people": "Three 6-foot tables",
    },
    "utilities": {
        "electricity": "Not required (propane grill)",
        "water": "We bring our own water supply",
        "cleanup": "We handle all cleanup",
    },
}

# ============================================================================
# RESPONSE TEMPLATES (Brand Voice Examples)
# ============================================================================

RESPONSE_TEMPLATES = {
    "greeting": """Hi! 👋 I'm your AI booking assistant for My Hibachi Chef!

I can help you:
✅ Book a hibachi chef for your event  
✅ Answer questions about packages and pricing  
✅ Check availability for your date  

What would you like to know?""",
    "pricing_inquiry": """Great question! Here's our pricing breakdown:

**Standard Package:**
- Adults (13+): **${adult}** per person
- Children (6-12): **${child}** per person  
- Ages 5 & under: **FREE** 🎉

**Party Minimum:** $550 total (~10 adults)

**Included:**
✅ Professional hibachi chef
✅ 2 proteins per guest (Chicken, Steak, Shrimp, Calamari, or Tofu)
✅ Fried rice, vegetables, salad, sauces
✅ Sake for adults 21+
✅ Complete setup & cleanup

Would you like to book, or do you have any questions?""",
    "deposit_info": """Here's how our deposit works:

💰 **$100 Refundable Deposit**
- Secures your event date
- Deducted from your final bill
- **Fully refundable** if you cancel 7+ days before event
- Non-refundable if canceled within 7 days

**Payment Methods:**
✅ Venmo Business
✅ Zelle Business  
✅ Credit Card
✅ Cash (for final balance)

Ready to book? I just need a few details!""",
    "booking_confirmation": """Perfect! Here's what I have:

📅 **Date:** {date}
🕐 **Time:** {time}  
👥 **Guests:** {guests}
📍 **Location:** {location}

💵 **Estimated Total:** ${total}
- {guests} guests × ${price}/person
- Travel: {travel_info}

Is this correct? Reply **YES** to proceed! ✅""",
    "terms_sent": """Awesome! I'm sending you our Terms & Conditions right now. 📋

Please review and reply **AGREE** to complete your booking.

Once you agree, your deposit secures your date and we're all set! 🎉""",
    "booking_complete": """🎉 **BOOKING CONFIRMED!** 🎉

Your hibachi experience is all set for **{date}** at **{time}**!

**What's Next:**
✅ Deposit paid: ${deposit}
✅ Final balance due on event date
📧 Confirmation email sent
📅 We'll send a reminder closer to your event

**Questions?** Text us anytime at (916) 740-8768

We can't wait to make your event amazing! 🔥✨""",
    "escalation": """I want to make sure you get the best help! Let me connect you with our team. 

**They'll reach out within:**
- 📱 Text/Call: 15-30 minutes
- 📧 Email: 1-2 hours

**Or reach out directly:**
📞 Text: (916) 740-8768
📧 Email: info@myhhibachichef.com

They'll take great care of you! 💫""",
}

# ============================================================================
# INTENT CLASSIFICATION PROMPTS
# ============================================================================

INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for My Hibachi Chef booking system.

Analyze the customer message and classify into ONE of these intents:

1. **INQUIRY** - Questions about pricing, packages, availability, menu, policies
   Examples: "How much?", "What's included?", "Do you travel to Sacramento?"

2. **BOOKING** - Wants to make a reservation
   Examples: "I want to book", "Reserve for Saturday", "Sign me up"

3. **MODIFICATION** - Change existing booking
   Examples: "Change my date", "Can I add more guests?", "Update my booking"

4. **CANCELLATION** - Cancel a booking
   Examples: "I need to cancel", "Can't make it anymore"

5. **OBJECTION** - Concerns or hesitation
   Examples: "That's expensive", "I'm not sure", "What if it rains?"

6. **ESCALATION** - Complex request needing human help
   Examples: "Custom menu for 100 people", "Corporate contract", "Special dietary needs for wedding"

Respond with ONLY the intent name in uppercase."""

# ============================================================================
# INFORMATION EXTRACTION PROMPT
# ============================================================================

INFO_EXTRACTOR_PROMPT = """Extract booking information from the conversation.

Look for and extract:
- **event_date**: Date of event (format: YYYY-MM-DD or descriptive like "next Saturday")
- **event_time**: Time of event (24-hour format or descriptive like "dinner time")
- **guest_count**: Number of guests (adults + children)
- **location_address**: Full or partial address
- **special_requests**: Dietary restrictions, preferences, special occasions

Respond ONLY with valid JSON object containing extracted fields.
Use null for missing information.

Example:
{
  "event_date": "2025-12-20",
  "event_time": "18:00",
  "guest_count": 20,
  "location_address": "123 Main St, Sacramento, CA",
  "special_requests": "Vegetarian option for 2 guests"
}"""

# ============================================================================
# RESPONSE GENERATOR PROMPT
# ============================================================================


def get_response_generator_prompt(customer_name: str = None) -> str:
    """Generate response prompt with brand personality"""

    name_greeting = f" {customer_name}" if customer_name else ""

    return f"""{BRAND_PERSONALITY}

**Current Customer:**{name_greeting}

**Your Mission:**
Help the customer book their perfect hibachi experience while embodying our warm, friendly, professional brand.

**Accurate Information:**
- Adults: ${PRICING['adult_base']}/person
- Children (6-12): ${PRICING['child_base']}/person
- Free: Ages 5 and under
- Minimum: ${PRICING['party_minimum']} total
- Deposit: ${PRICING['deposit']} (refundable if canceled 7+ days before)

**Response Guidelines:**
1. Be warm and enthusiastic (but not over-the-top)
2. Keep responses under 150 words
3. Use 1-3 emojis for friendliness
4. Always end with a question or clear next step
5. Be specific about pricing (don't say "around $50", say "$55")
6. If you don't know something, offer to connect them with the team

**Remember:** You're creating excitement for their event while being professional and trustworthy! 🌟"""


# ============================================================================
# UPSELL STRATEGY (Synced with seed_ai_training_real.py)
# ============================================================================

UPSELL_RULES = {
    "priority_order": [
        # Priority: Simple add-ons (easy yes)
        {"item": "yakisoba_noodles", "price": 5, "description": "Delicious yakisoba noodles"},
        {"item": "extra_fried_rice", "price": 5, "description": "Extra hibachi fried rice"},
        {"item": "edamame", "price": 5, "description": "Fresh edamame appetizer"},
        {"item": "vegetables", "price": 5, "description": "Extra grilled vegetables"},
        # Medium: Protein add-ons
        {"item": "third_protein", "price": 10, "description": "Add a 3rd protein choice"},
        {"item": "gyoza", "price": 10, "description": "Pan-fried gyoza dumplings"},
        # Premium: Special upgrades
        {"item": "lobster_tail", "price": 15, "description": "Upgrade to lobster tail"},
        {"item": "filet_mignon", "price": 5, "description": "Upgrade to filet mignon"},
        {"item": "salmon", "price": 5, "description": "Upgrade to premium salmon"},
        {"item": "scallops", "price": 5, "description": "Upgrade to sea scallops"},
    ],
    "tone": "conversational",
    "terminology": "add-on options",  # NEVER say "upsell"
    "approach": "offer once, don't push",
    "positioning": "enhance their experience (not increase bill)",
}
