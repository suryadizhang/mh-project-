# 🧠 AI Hospitality Training with Dynamic Data Synchronization

## 📋 Executive Summary

**Your Concern**: "All data should match with our real data on the web
page that is dynamic"

**Current Status**:

- ✅ AI already uses `PricingService` (pulls from database)
- ✅ System prompts exist but are **static** (hardcoded)
- ❌ No real-time sync between website changes → AI knowledge
- ❌ AI doesn't know about seasonal offers, availability, or menu
  changes
- ❌ No hospitality training data or upselling patterns

**Solution**: Create a **Business Knowledge Sync System** where:

1. Database = Single source of truth
2. Website pulls from database
3. AI pulls from database
4. Hospitality training data stored as structured knowledge
5. All updates happen in one place (Admin Panel)

---

## 🎯 Problem Analysis

### Current Architecture (What Exists)

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐        ┌──────────────┐                   │
│  │   Database   │◄───────│   Website    │                   │
│  │   (Prices)   │        │  (Display)   │                   │
│  └──────────────┘        └──────────────┘                   │
│         ▲                                                     │
│         │                                                     │
│         │ ✅ Already queries pricing                         │
│         │                                                     │
│  ┌──────┴───────┐                                            │
│  │ PricingService│                                            │
│  └──────────────┘                                            │
│         ▲                                                     │
│         │                                                     │
│  ┌──────┴───────┐        ❌ Static system prompts            │
│  │  AI System   │        ❌ No business knowledge sync       │
│  │  (4 Agents)  │        ❌ No hospitality training data     │
│  └──────────────┘                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### What's Missing

| Data Type                | Current State                         | What AI Needs                             |
| ------------------------ | ------------------------------------- | ----------------------------------------- |
| **Pricing**              | ✅ Database-driven via PricingService | ✅ Already works                          |
| **Menu Items**           | ✅ In database (menu_items table)     | ❌ AI doesn't query menu changes          |
| **Policies**             | ⚠️ Hardcoded in system prompts        | ❌ Not updateable without code deploy     |
| **FAQs**                 | ⚠️ Static TypeScript files            | ❌ No sync with AI knowledge              |
| **Availability**         | ❌ Not tracked                        | ❌ AI can't check real availability       |
| **Seasonal Offers**      | ❌ Not in system                      | ❌ No promo awareness                     |
| **Hospitality Training** | ❌ Doesn't exist                      | ❌ No upselling patterns                  |
| **Business Profile**     | ❌ Hardcoded in prompts               | ❌ Can't update tone/policies dynamically |

---

## 🏗️ Solution Architecture

### Target Architecture (What We'll Build)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DYNAMIC DATA SYNC SYSTEM                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         DATABASE (Single Source of Truth)                    │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │    │
│  │  │  menu_items  │  │ addon_items  │  │ business_rules │    │    │
│  │  └──────────────┘  └──────────────┘  └────────────────┘    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │    │
│  │  │   faq_items  │  │   policies   │  │ training_data  │    │    │
│  │  └──────────────┘  └──────────────┘  └────────────────┘    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │    │
│  │  │ seasonal_    │  │  availability│  │ upsell_rules   │    │    │
│  │  │  offers      │  │   calendar   │  └────────────────┘    │    │
│  │  └──────────────┘  └──────────────┘                         │    │
│  └──────────────────────┬──────────────────────────────────────┘    │
│                         │                                             │
│          ┌──────────────┼──────────────┐                             │
│          │              │              │                             │
│    ┌─────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐                      │
│    │  Website   │ │  Admin   │ │ AI Agents   │                      │
│    │ (Display)  │ │  Panel   │ │ (4 Agents)  │                      │
│    └────────────┘ └──────────┘ └─────────────┘                      │
│         │              │              │                              │
│         │              │              ├──► Knowledge Agent (RAG)     │
│         │              │              ├──► Lead Nurturing (Sales)    │
│         │              │              ├──► Customer Care (Support)   │
│         │              │              └──► Operations (Booking)      │
│         │              │                                              │
│    ✅ Pulls latest   ✅ Updates       ✅ Queries real-time data      │
│       pricing          all tables         for every response         │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema Extensions

### New Tables Needed

```sql
-- 1. Business Rules (Policies, Terms, Guidelines)
CREATE TABLE business_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL, -- 'policy', 'guideline', 'restriction', 'offer'
    category VARCHAR(100) NOT NULL, -- 'cancellation', 'refund', 'travel', 'menu'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL, -- The actual policy text
    effective_date DATE,
    expiry_date DATE,
    priority INTEGER DEFAULT 0, -- For sorting (higher = more important)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. FAQ Management (Dynamic FAQs)
CREATE TABLE faq_items (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    tags TEXT[], -- PostgreSQL array of tags
    confidence_level VARCHAR(20) DEFAULT 'high', -- 'high', 'medium', 'low'
    source_urls TEXT[], -- Links to relevant pages
    review_needed BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Training Data (Hospitality Examples)
CREATE TABLE training_data (
    id SERIAL PRIMARY KEY,
    interaction_type VARCHAR(50) NOT NULL, -- 'greeting', 'pricing', 'upsell', 'objection_handling'
    customer_input TEXT NOT NULL,
    ideal_response TEXT NOT NULL,
    personality_type VARCHAR(50), -- 'warm', 'professional', 'enthusiastic'
    tone_tags TEXT[], -- ['friendly', 'empathetic', 'solution-focused']
    booking_outcome VARCHAR(20), -- 'booked', 'follow_up', 'declined'
    effectiveness_score DECIMAL(3, 2), -- 0.00 to 1.00
    agent_type VARCHAR(50), -- 'lead_nurturing', 'customer_care', 'operations', 'knowledge'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Upsell Rules (Dynamic Upselling Logic)
CREATE TABLE upsell_rules (
    id SERIAL PRIMARY KEY,
    trigger_condition VARCHAR(100) NOT NULL, -- 'guest_count >= 10', 'event_type = "wedding"'
    suggested_upgrade VARCHAR(100) NOT NULL, -- 'Filet Mignon', 'Premium Sake Service'
    message_template TEXT NOT NULL, -- "For events with {guest_count} guests..."
    min_guest_count INTEGER,
    max_guest_count INTEGER,
    priority INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 2), -- Percentage converted
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Seasonal Offers (Time-Limited Promotions)
CREATE TABLE seasonal_offers (
    id SERIAL PRIMARY KEY,
    offer_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    discount_amount DECIMAL(10, 2), -- Dollar amount off
    discount_percent DECIMAL(5, 2), -- Percentage off
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    min_guests INTEGER,
    applicable_to TEXT[], -- ['adult_menu', 'premium_upgrades']
    promo_code VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Availability Calendar (Real-Time Availability)
CREATE TABLE availability_calendar (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL, -- '12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM'
    station_id VARCHAR(50), -- For multi-location support
    max_capacity INTEGER DEFAULT 1, -- How many events can be booked per slot
    booked_count INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT true,
    blocked_reason VARCHAR(255), -- 'holiday', 'staff_shortage', 'weather'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_date, time_slot, station_id)
);

-- 7. Knowledge Base Articles (For RAG)
CREATE TABLE knowledge_base_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    article_type VARCHAR(50), -- 'how_to', 'policy', 'menu_detail', 'troubleshooting'
    tags TEXT[],
    embedding VECTOR(1536), -- For OpenAI text-embedding-3-small (requires pgvector extension)
    last_updated TIMESTAMP DEFAULT NOW(),
    is_published BOOLEAN DEFAULT true
);

-- Indexes for performance
CREATE INDEX idx_business_rules_active ON business_rules(is_active, rule_type);
CREATE INDEX idx_faq_category ON faq_items(category, is_active);
CREATE INDEX idx_training_agent ON training_data(agent_type, effectiveness_score);
CREATE INDEX idx_upsell_active ON upsell_rules(is_active, priority);
CREATE INDEX idx_seasonal_dates ON seasonal_offers(start_date, end_date, is_active);
CREATE INDEX idx_availability_date ON availability_calendar(event_date, time_slot);
```

---

## 🔄 Real-Time Data Sync Flow

### How Data Updates Propagate

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA UPDATE FLOW                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1️⃣ Admin Updates Price (via Admin Panel)                        │
│     ↓                                                              │
│  ┌──────────────────────────────────────────┐                    │
│  │  UPDATE menu_items SET                   │                    │
│  │    base_price = 60.00                    │                    │
│  │  WHERE name = 'Adult Base Price';        │                    │
│  └──────────────┬───────────────────────────┘                    │
│                 │                                                  │
│  2️⃣ Database Triggers Price Change History                       │
│                 ↓                                                  │
│  ┌──────────────────────────────────────────┐                    │
│  │  INSERT INTO price_change_history        │                    │
│  │    (old_price, new_price, changed_by...) │                    │
│  └──────────────┬───────────────────────────┘                    │
│                 │                                                  │
│  3️⃣ Notification Service Alerts Team                             │
│                 ↓                                                  │
│  ┌──────────────────────────────────────────┐                    │
│  │  • Email to Super Admin                  │                    │
│  │  • WhatsApp to Operations Team           │                    │
│  │  • Slack #pricing-updates channel        │                    │
│  └──────────────┬───────────────────────────┘                    │
│                 │                                                  │
│  4️⃣ Website & AI Auto-Sync (No Code Deploy Needed!)              │
│                 ├────────────────┬──────────────┐                │
│                 ↓                ↓              ↓                │
│  ┌──────────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Website        │  │ AI Agents   │  │  Analytics  │        │
│  │ (Next.js)        │  │ (FastAPI)   │  │  Dashboard  │        │
│  ├──────────────────┤  ├─────────────┤  ├─────────────┤        │
│  │ Fetches pricing  │  │ Queries DB  │  │ Shows price │        │
│  │ on page load     │  │ for every   │  │ history     │        │
│  │ (15min cache)    │  │ response    │  │ chart       │        │
│  └──────────────────┘  └─────────────┘  └─────────────┘        │
│                                                                    │
│  ⏱️ Total Propagation Time: < 5 seconds                           │
│  💰 Cost: $0 (no external API calls, just DB queries)             │
│  🚀 Deploy: NONE (database-driven, not code-driven)               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 AI Hospitality Training System

### Phase 1: Business Knowledge Sync (Week 1)

#### Step 1.1: Extend PricingService to KnowledgeService

**File**:
`apps/backend/src/api/ai/endpoints/services/knowledge_service.py`

```python
"""
Knowledge Service - Dynamic Business Knowledge Retrieval
Pulls real-time data from database instead of static prompts
"""

from datetime import date, datetime
from typing import Any
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from decimal import Decimal

from models.business_rules import BusinessRule, FaqItem, TrainingData, UpsellRule
from .pricing_service import PricingService

class KnowledgeService:
    """
    Centralized knowledge service that pulls real-time business data
    REPLACES static system prompts with database-driven knowledge
    """

    def __init__(self, db: Session):
        self.db = db
        self.pricing_service = PricingService(db)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def get_business_charter(self) -> dict[str, Any]:
        """
        Get current business model, pricing, and policies
        DYNAMIC VERSION of system prompt
        """
        # Get active policies
        policies = self.db.execute(
            select(BusinessRule)
            .where(and_(
                BusinessRule.is_active == True,
                BusinessRule.rule_type == 'policy'
            ))
            .order_by(BusinessRule.priority.desc())
        ).scalars().all()

        # Get current pricing (real-time from database)
        current_pricing = {
            "adult_base": float(self.pricing_service.get_adult_price()),
            "child_base": float(self.pricing_service.get_child_price()),
            "party_minimum": float(self.pricing_service.BASE_PRICING["party_minimum"]),
            "travel_free_miles": self.pricing_service.TRAVEL_PRICING["free_radius_miles"],
            "travel_per_mile": self.pricing_service.TRAVEL_PRICING["per_mile_after"]
        }

        # Get premium upgrades
        upgrades = {
            name: float(price)
            for name, price in self.pricing_service.PREMIUM_UPGRADES.items()
        }

        return {
            "business_model": {
                "service_type": "Private hibachi catering at customer locations",
                "locations": ["homes", "venues", "corporate events"],
                "included_services": [
                    "Professional hibachi chef with entertaining cooking show",
                    "Portable hibachi grill and all cooking equipment",
                    "Utensils and serving equipment",
                    "Hibachi vegetables (zucchini, onions, mushrooms)",
                    "Signature fried rice",
                    "Premium protein options"
                ],
                "not_included": [
                    "Cleanup service",
                    "Tables and chairs",
                    "Dinnerware or plates",
                    "Setup/breakdown assistance"
                ]
            },
            "pricing": current_pricing,
            "upgrades": upgrades,
            "policies": [
                {
                    "category": p.category,
                    "title": p.title,
                    "content": p.content,
                    "effective_date": p.effective_date.isoformat() if p.effective_date else None
                }
                for p in policies
            ],
            "service_areas": self._get_service_areas(),
            "last_updated": datetime.now().isoformat()
        }

    def get_faq_answer(self, question: str, category: str = None) -> dict[str, Any] | None:
        """
        Find relevant FAQ answer (semantic search or keyword match)
        """
        query = select(FaqItem).where(FaqItem.is_active == True)

        if category:
            query = query.where(FaqItem.category == category)

        # Simple keyword matching (upgrade to semantic search with embeddings later)
        faqs = self.db.execute(query).scalars().all()

        question_lower = question.lower()
        matches = [
            faq for faq in faqs
            if any(tag.lower() in question_lower for tag in faq.tags)
        ]

        if not matches:
            return None

        # Return highest confidence match
        best_match = max(matches, key=lambda f: (
            1 if f.confidence_level == 'high' else
            0.5 if f.confidence_level == 'medium' else 0.1
        ))

        # Track analytics
        best_match.view_count += 1
        self.db.commit()

        return {
            "question": best_match.question,
            "answer": best_match.answer,
            "category": best_match.category,
            "source_urls": best_match.source_urls,
            "confidence": best_match.confidence_level
        }

    def get_upsell_suggestion(self, guest_count: int, event_type: str = None) -> dict[str, Any] | None:
        """
        Get relevant upsell suggestion based on context
        DYNAMIC upselling rules from database
        """
        query = select(UpsellRule).where(
            and_(
                UpsellRule.is_active == True,
                UpsellRule.min_guest_count <= guest_count,
                (UpsellRule.max_guest_count >= guest_count) | (UpsellRule.max_guest_count == None)
            )
        ).order_by(UpsellRule.priority.desc())

        rules = self.db.execute(query).scalars().all()

        if not rules:
            return None

        best_rule = rules[0]  # Highest priority

        # Format message with actual guest count
        message = best_rule.message_template.format(guest_count=guest_count)

        return {
            "upgrade": best_rule.suggested_upgrade,
            "message": message,
            "success_rate": float(best_rule.success_rate) if best_rule.success_rate else None
        }

    def get_training_example(self, interaction_type: str, agent_type: str = None) -> dict[str, Any] | None:
        """
        Get hospitality training example for AI to learn from
        """
        query = select(TrainingData).where(
            TrainingData.interaction_type == interaction_type
        )

        if agent_type:
            query = query.where(TrainingData.agent_type == agent_type)

        # Get highest effectiveness examples
        query = query.order_by(TrainingData.effectiveness_score.desc())

        example = self.db.execute(query).scalars().first()

        if not example:
            return None

        return {
            "customer_input": example.customer_input,
            "ideal_response": example.ideal_response,
            "tone_tags": example.tone_tags,
            "personality_type": example.personality_type,
            "booking_outcome": example.booking_outcome
        }

    def check_availability(self, event_date: date, time_slot: str, station_id: str = None) -> bool:
        """
        Check real-time availability
        """
        from models.availability import AvailabilityCalendar

        slot = self.db.execute(
            select(AvailabilityCalendar)
            .where(and_(
                AvailabilityCalendar.event_date == event_date,
                AvailabilityCalendar.time_slot == time_slot,
                AvailabilityCalendar.station_id == station_id if station_id else True
            ))
        ).scalar_one_or_none()

        if not slot:
            return True  # No entry = available (default open)

        return slot.is_available and slot.booked_count < slot.max_capacity

    def get_seasonal_offer(self, event_date: date = None) -> dict[str, Any] | None:
        """
        Get active seasonal promotion for given date
        """
        from models.seasonal import SeasonalOffer

        today = event_date or date.today()

        offer = self.db.execute(
            select(SeasonalOffer)
            .where(and_(
                SeasonalOffer.is_active == True,
                SeasonalOffer.start_date <= today,
                SeasonalOffer.end_date >= today
            ))
            .order_by(SeasonalOffer.discount_percent.desc())  # Best discount first
        ).scalar_one_or_none()

        if not offer:
            return None

        return {
            "name": offer.offer_name,
            "description": offer.description,
            "discount_amount": float(offer.discount_amount) if offer.discount_amount else None,
            "discount_percent": float(offer.discount_percent) if offer.discount_percent else None,
            "promo_code": offer.promo_code,
            "min_guests": offer.min_guests,
            "expires": offer.end_date.isoformat()
        }

    def _get_service_areas(self) -> list[str]:
        """
        Get list of service areas (could be database-driven later)
        """
        return [
            "Bay Area: San Francisco, San Jose, Oakland, Palo Alto, Mountain View",
            "Sacramento Area: Sacramento, Roseville, Folsom, Davis",
            "Wine Country: Sonoma, Napa Valley",
            "Central Valley: Stockton, Modesto, Fresno"
        ]
```

---

#### Step 1.2: Update AI Agents to Use KnowledgeService

**File**: `apps/backend/src/api/ai/agents/knowledge_agent.py`

**BEFORE** (Static System Prompt):

```python
def get_system_prompt(self) -> str:
    return """You are the knowledge expert for MyHibachi.

    Pricing:
    - Adults: $55
    - Children: $30
    - Party minimum: $550
    ...
    """  # ❌ Hardcoded, outdated if prices change
```

**AFTER** (Dynamic Knowledge):

```python
def get_system_prompt(self) -> str:
    # Get real-time business data from database
    charter = self.knowledge_service.get_business_charter()

    return f"""You are the knowledge expert for MyHibachi.

    **Current Pricing** (as of {charter['last_updated']}):
    - Adults (13+): ${charter['pricing']['adult_base']:.2f}
    - Children (6-12): ${charter['pricing']['child_base']:.2f}
    - Party minimum: ${charter['pricing']['party_minimum']:.2f}
    - Free travel radius: {charter['pricing']['travel_free_miles']} miles
    - Travel fee after: ${charter['pricing']['travel_per_mile']:.2f}/mile

    **Premium Upgrades**:
    {self._format_upgrades(charter['upgrades'])}

    **Active Policies**:
    {self._format_policies(charter['policies'])}

    **Service Areas**:
    {chr(10).join('• ' + area for area in charter['service_areas'])}

    **What's Included**:
    {chr(10).join('• ' + item for item in charter['business_model']['included_services'])}

    **What's NOT Included** (customers must provide):
    {chr(10).join('• ' + item for item in charter['business_model']['not_included'])}

    Use the `search_knowledge_base` tool for complex questions.
    Check `check_availability` tool for event date availability.
    Always cite source when providing policy information.
    """
```

---

### Phase 2: Hospitality Training Data Collection (Week 2)

#### Step 2.1: Seed Training Data

**File**: `apps/backend/src/db/seeds/seed_training_data.sql`

```sql
-- Hospitality Training Examples (Teacher Pairs)

-- 1. GREETING & TONE SETTING
INSERT INTO training_data (
    interaction_type,
    customer_input,
    ideal_response,
    personality_type,
    tone_tags,
    booking_outcome,
    effectiveness_score,
    agent_type
) VALUES
(
    'greeting',
    'Hi, I want to book hibachi for my party',
    'Hi there! 🔥 How exciting — we''d love to bring the hibachi experience to your celebration! To get you a personalized quote, could you share: (1) How many guests? (2) Event date? (3) Your city/ZIP code? We serve all of Northern California!',
    'enthusiastic',
    ARRAY['warm', 'professional', 'question-guided'],
    'follow_up',
    0.92,
    'lead_nurturing'
),

-- 2. PRICING INQUIRY (Simple)
(
    'pricing',
    'How much for 12 people in San Jose?',
    'For 12 guests in San Jose, here''s your total: • Base: $55/person × 12 = $660 • Travel fee: $10 (round-trip distance) • **Total: $670** This includes your choice of 2 proteins (Chicken, Steak, Shrimp, Scallops, Salmon, or Tofu), fried rice, veggies, chef entertainment, and sake for 21+. We have 12 PM, 3 PM, 6 PM, or 9 PM time slots — which works best for you? 🗓️',
    'professional',
    ARRAY['detailed', 'transparent', 'call-to-action'],
    'booked',
    0.88,
    'lead_nurturing'
),

-- 3. UPSELLING (Contextual, Not Pushy)
(
    'upsell',
    'We want steak and shrimp for 14 people',
    'Excellent choice — steak & shrimp is our most popular combo! 🥩🍤 Just to enhance your experience: would you like to upgrade to **Filet Mignon** for +$5/person? It''s our guests'' favorite for its buttery texture and tenderness. Completely optional, but many families celebrating special occasions love it!',
    'warm',
    ARRAY['benefit-focused', 'optional', 'enthusiastic'],
    'upsold',
    0.85,
    'lead_nurturing'
),

-- 4. OBJECTION HANDLING (Price Concern)
(
    'objection_handling',
    '$55 per person seems expensive',
    'I totally understand — let me break down what''s included so you can see the full value: ✓ **Private hibachi chef** (30+ min cooking show) ✓ All equipment, grill, setup ✓ Fresh proteins, fried rice, veggies ✓ Unlimited sake for adults 21+ ✓ Chef gratuity NOT included (you control tip amount) Compare this to restaurant hibachi ($40-50/person) + no entertainment at home. Plus, we come to YOU — no driving, no waiting, total privacy! Many families find it''s actually more affordable than taking everyone out. Does that help?',
    'empathetic',
    ARRAY['value-focused', 'comparison', 'reassuring'],
    'follow_up',
    0.79,
    'lead_nurturing'
),

-- 5. COMPLAINT HANDLING
(
    'complaint',
    'Chef arrived 30 minutes late last time',
    'I''m so sorry to hear that — punctuality is very important to us, and we clearly missed the mark. Thank you for letting us know. May I get your event date and booking ID? I''d like to: (1) File a report with our operations team, (2) Offer you a $50 credit toward your next booking as an apology. We take this seriously and want to make it right.',
    'empathetic',
    ARRAY['apologetic', 'solution-focused', 'accountability'],
    'resolved',
    0.91,
    'customer_care'
),

-- 6. MENU CUSTOMIZATION
(
    'menu',
    'Can we do vegetarian only?',
    'Absolutely! We''re happy to do an all-vegetarian hibachi experience 🥦🌽 We''ll prepare: • Tofu (seasoned and grilled) • Hibachi vegetables (zucchini, onions, mushrooms, broccoli) • Fried rice (can be made vegan if needed) • Side salad with ginger dressing Our chefs are experienced with dietary preferences and will make it delicious! Same pricing applies: $55/adult, $30/child.',
    'accommodating',
    ARRAY['inclusive', 'detailed', 'reassuring'],
    'booked',
    0.87,
    'operations'
),

-- 7. AVAILABILITY CHECK
(
    'availability',
    'Do you have availability on Christmas Eve?',
    'Great question! Christmas Eve is one of our busiest days. Let me check real-time availability for you... [checks availability_calendar] Good news — we currently have: ✅ **6:00 PM slot available** ❌ 12 PM, 3 PM, 9 PM fully booked I recommend securing the 6 PM slot ASAP as holiday dates fill up fast. Would you like me to hold that for you?',
    'professional',
    ARRAY['urgent', 'scarcity', 'helpful'],
    'booked',
    0.94,
    'operations'
);

-- Add 20-30 more examples covering:
-- • Complex dietary restrictions
-- • Multi-day bookings
-- • Corporate events
-- • Weather concerns
-- • Payment questions
-- • Upgrade rejections (graceful acceptance)
-- • Holiday pricing
-- • Last-minute bookings
```

---

#### Step 2.2: Seed Upsell Rules

```sql
-- Dynamic Upselling Logic

INSERT INTO upsell_rules (
    trigger_condition,
    suggested_upgrade,
    message_template,
    min_guest_count,
    max_guest_count,
    priority,
    success_rate,
    is_active
) VALUES
-- Large parties get premium protein suggestion
(
    'guest_count >= 10',
    'Filet Mignon',
    'Since you''re hosting {guest_count} guests, many of our customers upgrade to Filet Mignon (+$5/person). It''s our most tender cut and a crowd favorite for special celebrations!',
    10,
    NULL,
    10,
    15.3, -- 15.3% conversion rate
    true
),

-- Mid-size parties get seafood combo
(
    'guest_count >= 8 AND guest_count < 15',
    'Scallops + Lobster Tail Combo',
    'For your group of {guest_count}, we have a popular seafood upgrade: Scallops (+$5) and Lobster Tail (+$15) per person. Creates an unforgettable surf-and-turf experience!',
    8,
    14,
    8,
    12.7,
    true
),

-- Holiday events get extended performance
(
    'event_date IN (holiday_list)',
    'Extended Performance (+30 min)',
    'Since this is a holiday celebration, would you like our Extended Performance package? (+$50) Your chef will do extra tricks, engage more with guests, and extend cooking time. Very popular for Christmas, New Year, and Thanksgiving!',
    NULL,
    NULL,
    9,
    22.1,
    true
),

-- Corporate events get sake service
(
    'event_type = "corporate"',
    'Premium Sake Service',
    'For corporate events, we offer a Premium Sake Service (+$25) with sake tasting, Japanese etiquette presentation, and premium bottles. Great for client entertainment or team celebrations!',
    15,
    NULL,
    7,
    18.9,
    true
);
```

---

#### Step 2.3: Seed FAQ Items (Dynamic FAQs)

```sql
-- Migrate TypeScript FAQs to Database

INSERT INTO faq_items (
    question,
    answer,
    category,
    subcategory,
    tags,
    confidence_level,
    source_urls,
    is_active
) VALUES
(
    'How much does My Hibachi Chef cost?',
    '$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.',
    'Pricing & Minimums',
    'Per-person Rates',
    ARRAY['pricing', '$55 adult', '$30 child', '$550 minimum'],
    'high',
    ARRAY['/menu', '/pricing'],
    true
),
(
    'Do you provide cleanup service?',
    'No, we do NOT provide cleanup service. Customers are responsible for post-event cleanup. We bring all cooking equipment, utensils, and serving items, but cleanup of the dining area is the host''s responsibility.',
    'Service Details',
    'What''s NOT Included',
    ARRAY['cleanup', 'not included', 'customer responsibility'],
    'high',
    ARRAY['/faq'],
    true
),
(
    'What is your cancellation policy?',
    'Cancellations made 14+ days before event: Full refund of deposit. Cancellations 7-13 days before: 50% refund. Cancellations less than 7 days: No refund (but we''ll work with you on weather/emergency situations). We turn away other bookings when we reserve your date, so we appreciate advance notice.',
    'Policies',
    'Cancellation & Refunds',
    ARRAY['cancellation', 'refund', 'deposit', '14 days'],
    'high',
    ARRAY['/terms'],
    true
);

-- Add all 50+ FAQs from TypeScript files
```

---

### Phase 3: Admin Panel Integration (Week 3)

#### Admin UI for Business Knowledge Management

**New Admin Routes**:

```
/admin/knowledge-base
  ├─ /pricing (already exists)
  ├─ /policies (NEW)
  ├─ /faqs (NEW)
  ├─ /training-data (NEW)
  ├─ /upsell-rules (NEW)
  └─ /availability-calendar (NEW)
```

**Key Features**:

1. **Inline editing** (click to edit, auto-save)
2. **Version history** (track all changes)
3. **Preview mode** ("Test AI Response" button)
4. **Bulk import/export** (CSV for training data)
5. **Analytics dashboard** (which FAQs most viewed, which upsells work
   best)

---

### Phase 4: Voice AI Integration (Week 4)

#### Deepgram Settings (Already Optimal)

Your Deepgram configuration is excellent for phone calls:

```json
{
  "model": "nova-2",
  "language": "en-US",
  "detect_language": true, // ✅ ADD THIS for accent tolerance
  "encoding": "linear16",
  "sample_rate": 8000,
  "punctuate": true,
  "diarize": true,
  "smart_format": true,
  "utterances": true, // ✅ ADD THIS for better intent detection
  "interim_results": false,
  "tier": "enhanced",
  "vad_turnoff": 2.0 // ✅ ADD THIS for noisy environments
}
```

**Why These Settings Work for "Broken English"**:

- `detect_language: true` → Auto-adjusts to EN-IN, EN-PH variants
- `utterances: true` → Breaks speech into chunks even with poor
  grammar
- `vad_turnoff: 2.0` → Handles background noise better
- `nova-2` → Already trained on diverse global accents

**Optional Post-Processing** (if transcripts still messy):

```python
# apps/backend/src/services/transcript_normalizer.py

def normalize_transcript(raw_text: str) -> str:
    """
    Light grammar correction for broken English
    Doesn't change meaning, just cleans up for AI comprehension
    """
    corrections = {
        # Common patterns
        "I want book": "I want to book",
        "how much for person": "how much per person",
        "we have party": "we are having a party",
        "you coming my house": "you come to my house",
        "what time you available": "what time are you available"
    }

    text = raw_text.lower()
    for pattern, replacement in corrections.items():
        text = text.replace(pattern, replacement)

    return text
```

---

## 🧪 Testing & Validation

### Automated Tests

```python
# apps/backend/src/tests/test_knowledge_sync.py

def test_pricing_sync():
    """Test that AI gets real-time pricing"""
    # Update price in database
    db.execute(
        "UPDATE menu_items SET base_price = 60.00 WHERE name = 'Adult Base Price'"
    )
    db.commit()

    # AI should immediately use new price
    knowledge = KnowledgeService(db)
    charter = knowledge.get_business_charter()

    assert charter['pricing']['adult_base'] == 60.00

def test_upsell_rules():
    """Test dynamic upselling"""
    knowledge = KnowledgeService(db)

    # 12 guests should trigger Filet Mignon upsell
    suggestion = knowledge.get_upsell_suggestion(guest_count=12)
    assert suggestion['upgrade'] == 'Filet Mignon'
    assert '{guest_count}' not in suggestion['message']  # Formatted correctly

def test_availability_check():
    """Test real-time availability"""
    knowledge = KnowledgeService(db)

    # Block Christmas Eve 6 PM slot
    db.execute(
        "UPDATE availability_calendar SET is_available = false WHERE event_date = '2025-12-24' AND time_slot = '6:00 PM'"
    )
    db.commit()

    # AI should know it's unavailable
    available = knowledge.check_availability(
        event_date=date(2025, 12, 24),
        time_slot='6:00 PM'
    )
    assert available == False
```

---

## 📊 Success Metrics

### KPIs to Track

| Metric                      | Target     | How to Measure                                |
| --------------------------- | ---------- | --------------------------------------------- |
| **AI Response Accuracy**    | >95%       | Admin reviews (👍/👎 feedback)                |
| **Pricing Sync Latency**    | <5 seconds | Log timestamp of DB update → AI query         |
| **Upsell Conversion Rate**  | >12%       | Track bookings with upgrades vs. without      |
| **FAQ Hit Rate**            | >80%       | Questions answered from database vs. fallback |
| **Booking Completion Rate** | >60%       | Leads → confirmed bookings                    |
| **Average Response Time**   | <2 seconds | Voice AI latency (transcription + AI + TTS)   |

---

## 🚀 Implementation Timeline

### Week 1: Database & Knowledge Service

- ✅ Day 1-2: Create new database tables (business_rules, faq_items,
  training_data, upsell_rules)
- ✅ Day 3-4: Build `KnowledgeService` class
- ✅ Day 5: Update AI agents to use `KnowledgeService` instead of
  static prompts

### Week 2: Training Data & Seeding

- ✅ Day 6-7: Seed training_data table with 50+ hospitality examples
- ✅ Day 8-9: Seed upsell_rules and faq_items
- ✅ Day 10: Test AI responses with real data

### Week 3: Admin Panel

- ✅ Day 11-12: Build admin UI for policy management
- ✅ Day 13-14: Build FAQ editor with inline editing
- ✅ Day 15: Build training data upload interface

### Week 4: Voice AI & Testing

- ✅ Day 16-17: Integrate Deepgram with updated settings
- ✅ Day 18-19: Add transcript normalizer for broken English
- ✅ Day 20: Full system testing (website → AI → voice)

### Week 5: Monitoring & Optimization

- ✅ Day 21-22: Build analytics dashboard (upsell rates, FAQ views)
- ✅ Day 23-24: A/B test different hospitality phrasings
- ✅ Day 25: Launch to production 🎉

---

## 💡 Best Practices

### Do's ✅

- **Single Source of Truth**: Database drives website, AI, and
  analytics
- **Version Control**: Track all changes (price_change_history table)
- **Cache with TTL**: Frontend caches pricing for 15 min to reduce DB
  load
- **Test in Shadow Mode**: Log AI responses before sending to
  customers
- **Gradual Rollout**: Test with 10% of traffic first

### Don'ts ❌

- **Don't Hardcode Prices**: Never put prices in code or prompts
- **Don't Skip Notifications**: Alert team when critical data changes
- **Don't Over-Engineer**: Start simple (database → AI), add
  RAG/embeddings later if needed
- **Don't Ignore Feedback**: Track which AI responses customers rate
  poorly
- **Don't Deploy Without Backups**: Always have fallback values if DB
  query fails

---

## 🔮 Future Enhancements (Phase 2)

### Vector Search (RAG) - If Needed

**Decision Criteria**:

- Build ONLY if FAQ keyword matching accuracy <80%
- Investment: 1-2 weeks + $20-50/month (Pinecone or pgvector)

```python
# Future enhancement: Semantic search with embeddings

from openai import OpenAI

def search_knowledge_semantic(query: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search using OpenAI embeddings + pgvector
    """
    # Generate query embedding
    client = OpenAI()
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    # Vector similarity search in PostgreSQL
    results = db.execute(f"""
        SELECT title, content,
               1 - (embedding <=> '{embedding}') AS similarity
        FROM knowledge_base_articles
        WHERE is_published = true
        ORDER BY similarity DESC
        LIMIT {top_k}
    """).fetchall()

    return [
        {"title": r.title, "content": r.content, "score": r.similarity}
        for r in results
    ]
```

### RLHF-Lite (Reinforcement Learning from Human Feedback)

**How it works**:

1. Every customer interaction → Admin reviews (👍/👎)
2. Weekly batch job trains on high-rated responses
3. AI learns phrasing patterns that lead to bookings

```python
# apps/backend/src/workers/rlhf_trainer.py

from celery import Celery

app = Celery('myhibachi')

@app.task(name='train_from_feedback')
def weekly_training():
    """
    Fine-tune local model (Llama 3) using week's best interactions
    """
    # Get top-rated interactions (effectiveness_score >= 0.85)
    training_examples = db.execute("""
        SELECT customer_input, ideal_response
        FROM training_data
        WHERE effectiveness_score >= 0.85
        AND created_at >= NOW() - INTERVAL '7 days'
    """).fetchall()

    # Fine-tune Ollama model (LoRA adapter)
    # ... implementation details

    logger.info(f"Trained on {len(training_examples)} examples")
```

---

## 📞 Support & Next Steps

### What We'll Build Next

1. **Immediate (This Week)**:
   - Create database tables
   - Build `KnowledgeService`
   - Update AI agents to query database

2. **Short-term (Next 2 Weeks)**:
   - Admin panel for policy/FAQ management
   - Seed training data
   - Voice AI integration

3. **Long-term (Month 2-3)**:
   - A/B testing different hospitality phrasings
   - RAG with vector embeddings (if needed)
   - RLHF-Lite for continuous improvement

### Ready to Start?

I can generate:

1. ✅ Complete SQL migration files
2. ✅ `KnowledgeService` class (ready to paste)
3. ✅ Updated AI agent files
4. ✅ Seed data with 50+ hospitality examples
5. ✅ Admin panel React components
6. ✅ Testing suite

**Let me know which component you want me to generate first!** 🚀
