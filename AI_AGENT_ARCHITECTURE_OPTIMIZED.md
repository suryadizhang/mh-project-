# 🎯 AI Agent Architecture - Optimized for My Hibachi

**Date:** November 23, 2025  
**Philosophy:** Hybrid Multi-Agent System (Industry Best Practice)  
**Total Agents:** 9 (7 specialized + 1 general + 1 orchestrator)

---

## 🎯 DESIGN PHILOSOPHY

### Core Principle

**Specialized agents for HIGH-STAKES tasks, general agent for LOW-STAKES tasks**

- **HIGH-STAKES**: Money, bookings, customer data, dietary restrictions
  - → Specialized agent with business rules
  - → 95%+ accuracy required
  
- **LOW-STAKES**: Chitchat, general questions, ambiguous queries
  - → General conversational agent
  - → 80%+ accuracy acceptable

---

## 📊 TIER-BASED ARCHITECTURE

### Tier 1: Critical Business Agents (7 Specialized Agents)

These handle **money, bookings, and customer data** → Cannot fail

#### 1. Distance & Travel Fee Agent

**Purpose:** Calculate exact travel distance and fees

**Why specialized?**
- Uses Google Maps API (not LLM guessing)
- Business rule: First 30 miles FREE
- After 30 miles: Precise fee formula
- Wrong calculation = lost money or unhappy customer

**Tools:**
- Google Distance Matrix API
- Geocoding API
- Business rule engine

**Example:**
```
User: "How much to come to San Jose?"
Agent: "San Jose is 15 miles from Fremont. That's within our FREE 30-mile zone! 
        No travel fee. 🎉"
```

**Accuracy Required:** 100% (uses API, not LLM)

---

#### 2. Pricing Calculator Agent

**Purpose:** Calculate accurate quotes for bookings

**Why specialized?**
- Handles $550-$2,000+ quotes
- Multiple variables:
  - Guest count (adults vs kids)
  - Protein selection
  - Protein upgrades (+$5 to +$10 each)
  - Travel fees
  - Special requests
- Wrong quote = revenue loss or customer dispute

**Business Rules:**
```python
base_minimum = 550  # 10 guests minimum
adult_price = 55
kid_price = 30

upgrades = {
    'filet_mignon': 5,
    'lobster': 10,
    'scallops': 5,
    'premium_salmon': 5
}

# Quote = (adults * adult_price) + (kids * kid_price) + upgrades + travel_fee
# Must be >= base_minimum
```

**Example:**
```
User: "Price for 12 adults with lobster in San Jose?"
Agent: "12 adults @ $55 = $660
        Lobster upgrade: +$120 (12 × $10)
        Travel fee: $0 (within 30 miles)
        
        Total: $780 (includes food, chef, equipment, setup, cleanup)"
```

**Accuracy Required:** 100% (math-based, validated)

---

#### 3. Menu Advisor Agent

**Purpose:** Answer menu questions with 100% accuracy

**Why specialized?**
- **Dietary restrictions** = potential health risk (allergies, religious restrictions)
- **Ingredient questions** = cannot invent answers
- Must use ONLY information from menu database
- Wrong answer about allergens = lawsuit risk

**Knowledge Base:**
- Exact menu items
- Ingredients per dish
- Allergen information
- Dietary tags (halal-friendly, gluten-free, vegan, vegetarian)
- Preparation methods

**Example:**
```
User: "Do you have gluten-free options?"
Agent: "Yes! All our hibachi proteins are naturally gluten-free:
        ✅ Chicken, Steak, Shrimp, Salmon, Filet Mignon, Lobster, Scallops
        
        Note: We can prepare with gluten-free soy sauce upon request.
        Fried rice contains gluten, but we can substitute with vegetables."
```

**Accuracy Required:** 100% (uses RAG, never invents)

---

#### 4. Booking Coordinator Agent

**Purpose:** Guide customer through booking flow

**Why specialized?**
- Highest-value interaction (converts lead → booking)
- Must collect ALL required information:
  - Event date & time
  - Guest count (adults vs kids)
  - Location (full address)
  - Protein selection
  - Contact info (name, phone, email)
  - Special requests
- Missing 1 field = booking fails

**Workflow:**
```python
class BookingCoordinator:
    required_fields = [
        'event_date',
        'event_time',
        'guest_count_adults',
        'guest_count_kids',
        'location_address',
        'protein_selection',
        'customer_name',
        'customer_phone',
        'customer_email'
    ]
    
    def guide_booking_flow(self, conversation_history):
        # Check what's missing
        missing = self._identify_missing_fields(conversation_history)
        
        # Ask for next required field
        if missing:
            return self._ask_for_next_field(missing[0])
        
        # All fields collected → generate summary
        return self._create_booking_summary()
```

**Example:**
```
User: "I want to book for my birthday next Saturday"
Agent: "Exciting! Let's get your birthday party booked. 🎉
        
        I have: Saturday, [date]
        
        Next, I need:
        1. What time would you like us to start? (We recommend 6 PM or 7 PM)
        2. How many guests? (adults and kids)
        3. Your location (city or full address)"
```

**Accuracy Required:** 95%+ (uses structured extraction)

---

#### 5. Lead Capture Agent

**Purpose:** Extract customer contact information accurately

**Why specialized?**
- CRM data quality = future revenue
- Wrong phone/email = cannot follow up
- Missing name = unprofessional
- Uses structured extraction (not free-form LLM)

**Structured Extraction:**
```python
class LeadCapture:
    def extract_contact_info(self, message: str) -> Dict:
        return {
            'name': self._extract_name(message),           # "John Smith"
            'phone': self._extract_phone(message),         # "(555) 123-4567"
            'email': self._extract_email(message),         # "john@example.com"
            'preferred_contact': self._detect_preference(message),  # "phone" | "email" | "sms"
            'confidence': self._calculate_confidence()     # 0.0 - 1.0
        }
```

**Example:**
```
User: "My name is Sarah Chen, you can reach me at (408) 555-1234 or sarah.chen@gmail.com"

Agent extracts:
  name: "Sarah Chen"
  phone: "+14085551234"  # Normalized format
  email: "sarah.chen@gmail.com"
  preferred_contact: "phone"  # Mentioned first
  confidence: 0.98
```

**Accuracy Required:** 95%+ (validates format)

---

#### 6. Payment Validator Agent (NEW)

**Purpose:** Verify deposit payments before booking confirmation

**Why specialized?**
- Handles MONEY
- Must verify:
  - Payment received
  - Amount correct (50% of total quote)
  - Payment method valid
  - No duplicate payments
- Wrong validation = revenue loss or double charge

**Business Rules:**
```python
class PaymentValidator:
    def validate_deposit(
        self,
        quote_total: float,
        payment_amount: float,
        payment_id: str
    ) -> Dict:
        required_deposit = quote_total * 0.5
        
        # Check amount
        if abs(payment_amount - required_deposit) > 0.01:  # Allow 1 cent rounding
            return {
                'valid': False,
                'reason': f'Expected ${required_deposit:.2f}, received ${payment_amount:.2f}'
            }
        
        # Check duplicate
        if self._is_duplicate_payment(payment_id):
            return {
                'valid': False,
                'reason': 'Payment already processed'
            }
        
        return {'valid': True}
```

**Accuracy Required:** 100% (financial transactions)

---

#### 7. Availability Checker Agent (NEW)

**Purpose:** Prevent double bookings

**Why specialized?**
- **Critical business rule**: One chef per event
- Must check:
  - Chef calendar availability
  - Travel time between events (cannot book 6 PM San Jose + 7 PM Oakland)
  - Setup/cleanup time (minimum 3-4 hours per event)
  - Buffer time (30 min before/after)
- Wrong check = double booking = disaster

**Validation Logic:**
```python
class AvailabilityChecker:
    def check_availability(
        self,
        requested_date: datetime,
        requested_time: time,
        location_address: str,
        estimated_duration_hours: int = 3
    ) -> Dict:
        # Get existing bookings for that day
        existing = self._get_bookings_for_date(requested_date)
        
        for booking in existing:
            # Check time overlap
            if self._has_time_conflict(
                requested_time,
                estimated_duration_hours,
                booking.start_time,
                booking.duration
            ):
                return {
                    'available': False,
                    'reason': 'Time slot already booked',
                    'suggested_times': self._suggest_alternatives(requested_date)
                }
            
            # Check travel time feasibility
            if self._has_travel_conflict(
                location_address,
                booking.location,
                requested_time,
                booking.end_time
            ):
                return {
                    'available': False,
                    'reason': 'Insufficient travel time between events'
                }
        
        return {'available': True}
```

**Accuracy Required:** 100% (prevents business disasters)

---

### Tier 2: General Conversation Agent (1 Agent)

#### 8. Conversational Agent

**Purpose:** Handle low-stakes conversations and general questions

**Why general?**
- Covers 100+ question types that don't involve money/bookings
- Flexible (can handle unexpected questions)
- Cost-effective (one agent instead of 20+ specialized ones)
- Low risk (wrong answer won't lose money)

**Example Questions:**
- "What time do you start cooking?"
- "How long does the event last?"
- "Can I bring my own drinks?"
- "Do you provide plates and utensils?"
- "What's included in the service?"
- "Do you clean up afterward?"
- "Can we take photos with the chef?"
- "What happens if it rains?" (outdoor events)

**Example:**
```
User: "What's your favorite protein to cook?"
Agent: "While I don't eat (I'm an AI! 😊), Chef Ady loves preparing the filet 
        mignon and lobster combo - guests say it's restaurant-quality right 
        at home! The sizzle on the grill always gets everyone excited. 
        
        What type of protein are you thinking about for your event?"
```

**Accuracy Required:** 80%+ (guidance, not critical)

---

### Tier 3: Orchestrator (1 Meta-Agent)

#### 9. Agent Orchestrator

**Purpose:** Route questions to the right specialized agent

**Why needed?**
- Customers don't say "I need the pricing agent"
- Single entry point for all questions
- Intelligent routing based on intent
- Can combine multiple agents for complex queries

**Routing Logic:**
```python
class AgentOrchestrator:
    def route_question(self, user_message: str) -> List[Agent]:
        intents = self._detect_intents(user_message)
        
        agents_needed = []
        
        # Check for location mention → Distance Agent
        if self._contains_location(user_message):
            agents_needed.append(DistanceAgent)
        
        # Check for pricing keywords → Pricing Agent
        if self._contains_pricing_intent(user_message):
            agents_needed.append(PricingAgent)
        
        # Check for menu questions → Menu Agent
        if self._contains_menu_intent(user_message):
            agents_needed.append(MenuAdvisorAgent)
        
        # Check for booking intent → Booking Coordinator
        if self._contains_booking_intent(user_message):
            agents_needed.append(BookingCoordinator)
        
        # No specific intent → Conversational Agent
        if not agents_needed:
            agents_needed.append(ConversationalAgent)
        
        return agents_needed
    
    async def execute(self, user_message: str) -> str:
        agents = self.route_question(user_message)
        
        # Execute agents in order
        results = []
        for agent in agents:
            result = await agent.process(user_message, context=results)
            results.append(result)
        
        # Combine results into coherent response
        return self._synthesize_response(results)
```

**Example Routing:**
```
User: "How much for 10 people with lobster in San Jose?"

Orchestrator detects:
  - Location: "San Jose" → Distance Agent needed
  - Guest count: "10 people" → Pricing Agent needed  
  - Protein: "lobster" → Pricing Agent needed
  
Execution:
  1. Distance Agent: Calculate San Jose distance → 15 miles → $0 travel fee
  2. Pricing Agent: Calculate quote
     - 10 adults @ $55 = $550
     - Lobster upgrade: 10 × $10 = $100
     - Travel fee: $0
     - Total: $650
  
  3. Synthesize response:
     "Great news! San Jose is within our free 30-mile zone.
      
      Quote for 10 guests with lobster:
      - 10 adults @ $55: $550
      - Lobster upgrade: +$100
      - Travel fee: $0
      
      Total: $650
      
      This includes everything: chef, equipment, setup, cooking, and cleanup!
      
      Would you like to check availability for a specific date?"
```

**Complex Example:**
```
User: "Can you do 15 people next Saturday in Oakland with vegetarian options?"

Orchestrator detects:
  - Date: "next Saturday" → Availability Checker needed
  - Location: "Oakland" → Distance Agent needed
  - Guest count: "15 people" → Pricing Agent needed
  - Dietary: "vegetarian" → Menu Advisor Agent needed
  - Intent: "can you do" → Booking Coordinator needed
  
Execution:
  1. Availability Checker: Check next Saturday → AVAILABLE
  2. Distance Agent: Oakland → 25 miles → $0 travel fee
  3. Menu Advisor: Vegetarian options → Tofu protein available
  4. Pricing Agent: Calculate quote → $825 (15 × $55)
  5. Booking Coordinator: Collect remaining info
  
  Response:
  "Yes, we're available next Saturday! Oakland is 25 miles away 
   (still within our free zone).
   
   For vegetarian guests, we can prepare tofu hibachi - it's delicious 
   and cooked fresh on the grill with vegetables and fried rice.
   
   Quote for 15 guests: $825
   
   To confirm your booking, I need a few more details:
   - What time works best? (6 PM or 7 PM are popular)
   - Your full address in Oakland
   - Your contact information"
```

---

## 🎯 AGENT INTERACTION MAP

```
                    ┌─────────────────────┐
                    │  Agent Orchestrator │ ← User Question
                    │   (Routes Intent)   │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │ Tier 1 Agents │  │ Tier 1 Agents │  │ Tier 2 Agent  │
    │  (Critical)   │  │  (Critical)   │  │   (General)   │
    └───────────────┘  └───────────────┘  └───────────────┘
            │                  │                  │
    ┌───────┴────────┐ ┌──────┴───────┐          │
    ▼                ▼ ▼              ▼          ▼
┌─────────┐  ┌─────────┐  ┌─────────┐   ┌──────────────┐
│Distance │  │ Pricing │  │  Menu   │   │Conversational│
│  Agent  │  │  Agent  │  │  Agent  │   │    Agent     │
└─────────┘  └─────────┘  └─────────┘   └──────────────┘
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Booking │  │  Lead   │  │ Payment │
│  Agent  │  │ Capture │  │Validator│
└─────────┘  └─────────┘  └─────────┘
┌─────────┐
│Available│
│ Checker │
└─────────┘
```

---

## 📊 COMPARISON WITH INDUSTRY

### OpenAI Approach (1 Agent)
```
✅ Pros: Simple, easy to maintain
❌ Cons: Cannot guarantee accuracy for critical tasks
❌ Risk: May give wrong prices, dietary info, availability

Example: ChatGPT might say "Sure, lobster is $8/person" (WRONG - it's $10)
```

### Our Hybrid Approach (9 Agents)
```
✅ Pros: 
  - Critical tasks use business rules (100% accuracy)
  - General tasks use LLM (flexible, conversational)
  - Best of both worlds

✅ Benefits:
  - Pricing: 100% accurate (math-based, not LLM guessing)
  - Menu: 100% accurate (RAG-based, never invents)
  - Availability: 100% accurate (database check)
  - Conversation: 80%+ accurate (LLM-based, low risk)

✅ Industry Match:
  - Uber: Distance Agent (similar to our Distance Agent)
  - OpenTable: Availability Checker (similar to ours)
  - Stripe: Payment Validator (similar to ours)
  - Intercom: Conversational Agent (similar to ours)
```

### Too Many Agents (20+ Agents)
```
❌ Cons: Over-engineered, hard to maintain
❌ Example: Separate agents for "Chicken questions" vs "Steak questions"
❌ Result: Complexity without benefit
```

---

## 🎯 DOES EVERY FEATURE NEED AN AGENT?

### ❌ NO - Here's Why

**Features that DON'T need agents:**

1. **Customer Reviews** → Simple CRUD operations, no AI needed
2. **Loyalty Points** → Math-based calculation, no AI needed
3. **Email Newsletter** → Marketing automation, not conversational AI
4. **Admin Dashboard** → Data visualization, no AI needed
5. **Payment Processing** → Stripe handles this, just need validator
6. **Photo Gallery** → Static content, no AI needed

**Features that MIGHT need agents (future):**

7. **Chef Scheduling** → Could use Scheduling Agent (Phase 4 - automation prep)
8. **Inventory Management** → Could use Inventory Agent (if you expand menu)
9. **Customer Service** → Already handled by Conversational Agent

---

## 🎯 OPTIMIZATION RULES

### When to Create a New Agent

✅ **Create specialized agent when:**
1. Task involves MONEY (pricing, payments, refunds)
2. Task involves BOOKINGS (availability, scheduling, cancellations)
3. Task involves HEALTH/SAFETY (dietary restrictions, allergens)
4. Task requires 95%+ accuracy
5. Task uses external API or database (not just LLM)
6. Wrong answer causes business loss

❌ **DON'T create agent when:**
1. Task is general conversation
2. Task is informational only (low risk if wrong)
3. Task happens rarely (< 1% of questions)
4. Task can be handled by existing general agent
5. Adding agent adds complexity without accuracy gain

### Examples

**✅ GOOD: Create Distance Agent**
- Involves money (travel fees)
- Requires Google Maps API (not LLM guessing)
- Wrong answer = revenue loss
- Happens often (every booking needs distance)

**❌ BAD: Create "Parking Instructions Agent"**
- Informational only (low risk)
- Happens rarely
- General agent can handle: "Is there parking available?"
- No business rules needed

**✅ GOOD: Create Availability Checker Agent**
- Prevents double bookings (critical!)
- Requires database check (not LLM guessing)
- Wrong answer = business disaster
- Happens often (every booking)

**❌ BAD: Create "Photo Request Agent"**
- Low risk (just send photos)
- Happens rarely
- General agent can handle: "Can I see photos of your setup?"
- No complex logic needed

---

## 🎯 FINAL RECOMMENDATION (UPDATED)

### **10 Agents Total (8 + 1 + 1)**

This is the **optimal balance** for My Hibachi:

**Tier 1: Critical Business Agents (8)** ← Added Complaint Handler
1. Distance & Travel Fee Agent
2. Pricing Calculator Agent
3. Menu Advisor Agent
4. Booking Coordinator Agent
5. Lead Capture Agent
6. Payment Validator Agent
7. Availability Checker Agent
8. **Customer Complaint Handler Agent** ← NEW (Agent #10)
9. Admin Assistant Agent (ENHANCED with panel-specific features)

**Tier 2: General Agent (1)**
10. Conversational Agent

**Tier 3: Orchestrator (1)**
11. Agent Orchestrator

### Why This Works

✅ **Accuracy where it matters**: 100% for money/bookings
✅ **Flexibility where it helps**: 80%+ for general questions
✅ **Maintainable**: 9 agents, not 50
✅ **Testable**: Each agent has clear responsibility
✅ **Scalable**: Can add agents as business grows
✅ **Industry-standard**: Used by Uber, OpenTable, Stripe, etc.

### Cost-Benefit Analysis

**Cost:**
- Development: ~80 hours (Phase 2)
- Maintenance: ~4 hours/month

**Benefit:**
- Prevent 1 double booking/month = Save $550-2,000
- Prevent 1 wrong quote/month = Save $100-500
- Improve lead capture by 20% = +$5,000-10,000/year in bookings
- Customer satisfaction = Priceless

**ROI:** 10-20x return on investment

---

## 📊 AGENT METRICS TO TRACK

### Per Agent:

1. **Usage Count** - How often called
2. **Accuracy** - % of correct responses
3. **Response Time** - How fast
4. **Cost** - LLM tokens used
5. **Business Impact** - Led to booking? Yes/No

### Overall System:

1. **Routing Accuracy** - Did orchestrator pick right agent?
2. **Multi-Agent Success** - When 2+ agents used, did it work?
3. **Fallback Rate** - How often fell back to general agent?
4. **Booking Conversion** - % of chats → bookings
5. **Customer Satisfaction** - Post-chat rating

---

## 🚀 IMPLEMENTATION ORDER (Updated)

**Phase 2A (Week 2):**
1. Distance Agent (4-6 hrs)
2. Menu Advisor Agent (6-8 hrs)
3. Pricing Agent (8-10 hrs)
4. RAG Knowledge Base (8-12 hrs)

**Phase 2B (Week 3):**
5. Conversational Agent (6-8 hrs) - NEW
6. Lead Capture Agent (6-8 hrs)
7. Booking Coordinator Agent (10-12 hrs)
8. Availability Checker Agent (8-10 hrs) - NEW
9. Payment Validator Agent (6-8 hrs) - NEW
10. Agent Orchestrator (8-12 hrs)

**Total: 76-106 hours** (was 68-92 hours, added 8-14 hours for 2 new agents + orchestrator improvements)

---

## 🎯 SUMMARY

**Question:** "How many agents do we have? Does every feature need an agent?"

**Answer:** 
- **9 agents total** (7 specialized + 1 general + 1 orchestrator)
- **NO, not every feature needs an agent**
- **Only create agents for high-stakes tasks** (money, bookings, safety)
- **Use general agent for low-stakes tasks** (questions, chitchat)
- **This is industry best practice** (Uber, OpenTable, Stripe use similar approach)

**Result:** Optimal balance of accuracy, flexibility, and maintainability. 🎯
