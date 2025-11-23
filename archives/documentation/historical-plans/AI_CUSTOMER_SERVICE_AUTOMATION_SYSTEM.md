# 🤖 AI Customer Service Automation System

## Automated Customer Journey with Smart Escalation

---

## 🎯 System Overview

**Goal**: Automate routine customer service tasks while maintaining
the personal touch and escalating complex issues to humans.

**Integration**: Works with MyHibachi Quick-Reply Pack guidelines + AI
Adaptive Tone System

---

## 📅 Automated Customer Journey Timeline

### **Stage 1: Booking Confirmation** (Day 0)

**AI Actions**:

```
1. Send confirmation message (personalized tone)
2. Recap booking details (date, time, location, initial guest count)
3. Explain what's included + what customer provides
4. Set internal reminders for future touchpoints
```

**Example Message** (Casual Tone - Based on Official Guidelines):

```
✨ Booking Confirmed — My Hibachi! ✨

Hey [Name]! 🎉 We're SO excited to cook for you!

📅 **Your Event**:
• Date/Time: [Date] at [Time]
• Address: [Full Address]
• Guests: [# Guests] (can adjust up to 3 days before)
• Deposit: $100 ✅ Received!
• Event Duration: 90 minutes (automatically extended for 30+ guests)

**What's Included**:
✨ 2 proteins per person (your choice)
🍚 Hibachi fried rice
🥦 Fresh vegetables
🥗 Salad
🔥 Chef's entertaining cooking show
🍜 Yum-yum sauce & hot sauce

**What You Provide**:
• Seating, tables, and utensils for guests
• Flat outdoor cooking space (no indoor cooking unless pre-approved)
• Good lighting if evening event

**Important Notes**:
• Our chef will arrive 15-20 minutes early for setup
• Final guest count and menu choices due 3 days before event
• Remaining balance due at event (cash, Zelle, Venmo, or card)
• Please review our full agreement: [Agreement Link]

I'll check in with you about a week before to finalize your protein choices!

Can't wait! 🔥

– My Hibachi Team
```

---

### **Stage 2: 7-Day Reminder** (7 days before event)

**AI Actions**:

```
1. Send friendly reminder
2. Request menu selection (proteins + any upgrades)
3. Confirm guest count is still accurate
4. Ask about parking/access details
```

**Example Message** (Warm Tone):

```
Hi [Name]! 🙌

Your My Hibachi event is coming up in 1 week on [Date] at [Time]!

Quick check-in to finalize a few details:

**1️⃣ Menu Selection** (please choose 2 proteins):
Included Options:
• Chicken 🍗
• Steak 🥩
• Shrimp 🍤
• Calamari 🦑
• Tofu 🌱

Premium Upgrades (optional):
• Salmon (+$5/person)
• Scallops (+$5/person)
• Filet Mignon (+$5/person)
• Lobster (+$15/person)

Want to add extras?
• Yakisoba noodles (+$5)
• Extra fried rice (+$5)
• Extra veggies (+$5)
• Add 3rd protein (+$10)

**2️⃣ Guest Count Check**:
Still expecting [# Adults / # Kids / # Toddlers]? Let me know if that changed!

**3️⃣ Parking & Access**:
Any gate codes, parking notes, or special instructions for our chef?

Just reply with your protein choices and I'll get everything confirmed! 😊

– My Hibachi Team
```

**AI Logic**:

```python
async def send_7_day_reminder(booking_id):
    booking = await get_booking(booking_id)

    # Check if menu already selected
    if booking.menu_selected:
        message = generate_confirmation_reminder(booking)
    else:
        message = generate_menu_request_reminder(booking)

    # Send via customer's preferred channel (SMS/Email/WhatsApp)
    await send_message(
        customer_id=booking.customer_id,
        message=message,
        channel=booking.preferred_communication
    )

    # Set follow-up reminder for 4-day deadline
    await schedule_followup(
        booking_id=booking_id,
        days_before=4,
        action="check_menu_selection"
    )
```

---

### **Stage 3: 4-Day Deadline Check** (4 days before event)

**AI Actions**:

```
1. Check if menu selection received
2. If YES → Send confirmation
3. If NO → Send urgent reminder (with friendly tone)
4. If still NO after 2nd reminder → Escalate to human for personal call
```

**Example Message** (If no menu received):

```
Hi [Name]!

Quick heads up — we need your protein choices by tomorrow to guarantee
your preferred menu for [Date] 🎉

**Please choose 2 proteins**:
• Chicken 🍗
• Steak 🥩
• Shrimp 🍤
• Calamari 🦑
• Tofu 🌱

**Or upgrade to**:
• Salmon (+$5/person)
• Scallops (+$5/person)
• Filet Mignon (+$5/person)
• Lobster (+$15/person)

If I don't hear back by tomorrow, we'll go with our default:
**Chicken + Steak** (our most popular combo!) 👍

Just reply with your choice and we're all set! 😊

– My Hibachi Team
```

**AI Logic**:

```python
async def check_4_day_deadline(booking_id):
    booking = await get_booking(booking_id)

    if not booking.menu_selected:
        # Send urgent reminder
        await send_urgent_menu_reminder(booking)

        # Schedule final check in 24 hours
        await schedule_followup(
            booking_id=booking_id,
            hours_from_now=24,
            action="escalate_if_no_menu"
        )
    else:
        # Menu received, send confirmation
        await send_menu_confirmation(booking)
```

**Escalation Trigger**:

```python
async def escalate_if_no_menu(booking_id):
    booking = await get_booking(booking_id)

    if not booking.menu_selected:
        # ESCALATE TO HUMAN
        await create_escalation(
            booking_id=booking_id,
            priority="HIGH",
            reason="No menu selection by 4-day deadline",
            action_required="Personal call to confirm menu",
            deadline="3 days before event"
        )

        # Notify human agent
        await notify_team(
            message=f"🚨 Booking #{booking_id} needs menu confirmation call",
            assignee="operations_team"
        )
```

---

### **Stage 4: 24-Hour Window** (1 day before event)

**AI Actions**:

```
1. Send final confirmation
2. Handle minor adjustments (headcount +/- 2, protein swaps)
3. Escalate major changes to human (headcount >10% change, date change, cancellation)
4. Confirm parking/access details
```

**Example Message**:

```
See you tomorrow at [Time]! 🙌

**Final Confirmation**:
• Date/Time: [Date] at [Time]
• Address: [Full Address]
• Guests: [# Adults / # Kids / # Toddlers]
• Proteins: [List]
• Upgrades: [List or "None"]
• Balance Due: $[Amount] (cash, Venmo, Zelle, or card on event day)

Our chef will arrive 15-30 minutes early to set up.

**Need to make a last-minute change?**
Minor adjustments (±2 guests, swap proteins) → Just reply here!
Major changes (guest count >10%, date change) → Call us: (916) 740-8768

We'll text you when we're on the way tomorrow! 🔥

– My Hibachi Team
```

**AI Logic for 24-Hour Adjustments**:

```python
async def handle_24hr_adjustment(booking_id, request):
    booking = await get_booking(booking_id)
    change_type = classify_change(request)

    # MINOR CHANGES (AI handles automatically)
    if change_type == "minor_headcount":  # ±2 guests
        new_count = extract_guest_count(request)
        if abs(new_count - booking.guest_count) <= 2:
            await update_booking(booking_id, guest_count=new_count)
            await send_adjustment_confirmation(booking)
            return "handled"

    elif change_type == "protein_swap":  # Same number of proteins
        new_proteins = extract_proteins(request)
        await update_booking(booking_id, proteins=new_proteins)
        await send_adjustment_confirmation(booking)
        return "handled"

    # MAJOR CHANGES (Escalate to human)
    elif change_type in ["major_headcount", "date_change", "cancellation"]:
        await create_escalation(
            booking_id=booking_id,
            priority="URGENT",
            reason=f"24-hour {change_type} request",
            customer_request=request,
            deadline="Immediate (event tomorrow)"
        )

        # Immediate notification
        await send_sms_to_team(
            message=f"🚨 URGENT: Booking #{booking_id} - {change_type}",
            phone="(916) 740-8768"
        )

        # Auto-response to customer
        await send_message(
            customer_id=booking.customer_id,
            message="""Thanks for reaching out! Since your event is tomorrow,
            I've notified our manager to call you right away at [phone].
            They'll help with your request!"""
        )

        return "escalated"

async def handle_cancellation_request(booking_id):
    """
    Handle cancellation based on timing
    Refund policy: ≥7 days = full refund, <7 days = no refund
    Reschedule policy: Within 48 hours of booking = free once, after = $100 fee
    """
    booking = await get_booking(booking_id)
    days_until_event = (booking.event_date - datetime.now()).days
    hours_since_booking = (datetime.now() - booking.created_at).total_seconds() / 3600

    # FULL REFUND (≥7 days before event)
    if days_until_event >= 7:
        await send_message(
            customer_id=booking.customer_id,
            message="""I understand you need to cancel. Since we're more than 7 days
            out, you're eligible for a full refund of your $100 deposit.

            Would you like to:
            1️⃣ Cancel and receive full refund
            2️⃣ Reschedule to a different date

            Just reply with 1 or 2 and I'll take care of it! 😊"""
        )
        return "ai_handled"

    # NO REFUND but offer reschedule
    elif 3 <= days_until_event < 7:
        # Check if within 48-hour free reschedule window
        if hours_since_booking <= 48:
            message = """I see you need to cancel. Unfortunately, we're less than 7 days
            from your event, so the deposit is non-refundable per our policy.

            However, since you booked within the last 48 hours, you qualify for
            ONE FREE RESCHEDULE to a different date! Would you like to pick a new date? 📅"""
        else:
            message = """I understand you need to cancel. Unfortunately, we're less than
            7 days from your event, so the deposit is non-refundable per our policy.

            However, you can reschedule to a different date for a $100 rescheduling fee
            (your $100 deposit will be applied to the new booking). Would you like to
            explore available dates? 📅"""

        await send_message(booking.customer_id, message)

        # Escalate for calendar coordination
        await create_escalation(
            booking_id=booking_id,
            priority="MEDIUM",
            reason="Cancellation/reschedule request (3-6 days before)",
            action_required="Check availability, coordinate new date"
        )
        return "escalated_for_coordination"

    # NO REFUND (<3 days)
    else:
        await send_message(
            customer_id=booking.customer_id,
            message="""I'm sorry to hear you need to cancel. Unfortunately, with less
            than 3 days until your event, the deposit is non-refundable per our policy.

            I've notified our management team, and they'll reach out to you shortly
            to discuss your options. Our phone number is (916) 740-8768 if you'd like
            to call directly."""
        )

        # Escalate to management for compassionate handling
        await create_escalation(
            booking_id=booking_id,
            priority="HIGH",
            reason="Late cancellation request (<3 days)",
            action_required="Personal call - discuss options, confirm no-refund policy",
            notes="Handle with empathy, explain policy clearly"
        )
        return "escalated_to_management"
```

---

### **Stage 5: Event Day** (Day of event)

**AI Actions**:

```
1. Send "on the way" notification (when chef departs)
2. Send "arriving in 10 minutes" alert
3. Log event as completed
4. Schedule post-event follow-up
```

**Example Messages**:

```
# When chef departs
Hey [Name]! Our chef is on the way to [Address]!
ETA: [Time]. See you soon! 🔥

# 10 minutes before arrival
We're 10 minutes away! Please make sure the setup area is ready.
Can't wait to cook for you! 🎉
```

---

### **Stage 6: Post-Event Follow-Up** (1 day after event)

**AI Actions**:

```
1. Send thank you message
2. Request rating (1-5 stars)
3. Smart routing based on rating:
   - 4-5 stars → Request Google/Yelp review
   - 1-3 stars → Route to internal feedback form + escalate to human
```

**Example Message** (Initial):

```
Hi [Name]! 👋

Thank you for choosing My Hibachi Chef! We hope you and your guests
had an amazing time! 🎉

**How was your experience?**
Please rate us from 1-5 stars:
⭐ (Poor) ⭐⭐ (Fair) ⭐⭐⭐ (Good) ⭐⭐⭐⭐ (Great) ⭐⭐⭐⭐⭐ (Excellent)

Just reply with a number (1-5) and I'll take care of the rest! 😊

– My Hibachi Team
```

**AI Logic for Smart Review Routing**:

```python
async def handle_review_response(booking_id, rating):
    booking = await get_booking(booking_id)

    # GOOD REVIEW (4-5 stars)
    if rating >= 4:
        message = f"""
        Thank you so much for the {rating}-star rating! 🌟🎉

        We'd be honored if you could share your experience on:

        ⭐ **Google**: {GOOGLE_REVIEW_LINK}
        ⭐ **Yelp**: {YELP_REVIEW_LINK}

        Your review helps other families discover our hibachi experience!

        Thanks again, and we hope to cook for you again soon! 🔥
        """

        await send_message(booking.customer_id, message)

        # Log successful customer
        await mark_as_promoter(booking.customer_id)

    # NEUTRAL/BAD REVIEW (1-3 stars)
    else:
        message = f"""
        Thank you for your {rating}-star feedback. We truly appreciate
        your honesty and want to make things right.

        Could you share what we could improve?
        👉 {INTERNAL_FEEDBACK_FORM_LINK}

        Your feedback goes directly to our management team, and we take
        every comment seriously.

        – My Hibachi Management
        """

        await send_message(booking.customer_id, message)

        # ESCALATE TO HUMAN for personal follow-up
        await create_escalation(
            booking_id=booking_id,
            priority="HIGH",
            reason=f"Customer gave {rating}-star review",
            action_required="Personal follow-up call to address concerns",
            customer_feedback=await get_customer_feedback(booking_id)
        )

        # Notify management immediately
        await send_email_to_management(
            subject=f"⚠️ Low Rating Alert - Booking #{booking_id}",
            body=f"""
            Customer: {booking.customer_name}
            Event Date: {booking.event_date}
            Rating: {rating}/5 stars

            Action required: Personal follow-up call
            """
        )
```

---

## 🚨 Human Escalation System

### **Escalation Triggers** (When AI Stops, Human Steps In)

| Trigger                             | Priority | Auto-Response to Customer                                           | Human Action Required                                                                         |
| ----------------------------------- | -------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **No menu by 4-day deadline**       | HIGH     | "We've notified our team to call you today!"                        | Personal call to confirm menu                                                                 |
| **Change within 24 hours**          | URGENT   | "Manager will call you right away!"                                 | Approve/deny change, adjust pricing                                                           |
| **Date change/reschedule request**  | MEDIUM   | "Let me check our availability for you!"                            | Check calendar, verify if within 48-hour free reschedule window, calculate $100 fee if beyond |
| **Cancellation request (≥7 days)**  | MEDIUM   | "I understand. Let me process your full refund right away."         | Process full deposit refund ($100)                                                            |
| **Cancellation request (3-6 days)** | HIGH     | "I've notified management about your cancellation request."         | No refund per policy, confirm with customer, process cancellation                             |
| **Cancellation request (<3 days)**  | HIGH     | "I've notified management about your cancellation request."         | No refund per policy, confirm with customer, process cancellation                             |
| **Bad review (1-3 stars)**          | HIGH     | "Thank you for feedback. Management will reach out personally."     | Personal call to resolve issue                                                                |
| **Complex dietary restrictions**    | MEDIUM   | "Let me connect you with our chef to discuss custom options!"       | Chef consultation call                                                                        |
| **Unsafe weather setup**            | URGENT   | "Safety is our priority. Manager will call you to discuss options." | Weather assessment, rescheduling                                                              |

### **Escalation Workflow**

```
Customer Request → AI Analyzes Complexity → Classify as Minor/Major

MINOR (AI handles):
├─ Menu selection reminders
├─ Parking/access info collection
├─ Minor headcount adjustments (>24 hrs)
├─ Protein substitutions (>24 hrs)
├─ Good review routing
└─ Booking confirmations

MAJOR (Human escalation):
├─ Date changes
├─ Changes within 24 hours
├─ No menu by deadline
├─ Cancellations
├─ Bad reviews (≤3 stars)
└─ Complex special requests
```

### **Escalation Dashboard** (For Human Agents)

```
┌────────────────────────────────────────────────────────┐
│  🚨 Escalations Dashboard - My Hibachi                │
├────────────────────────────────────────────────────────┤
│                                                          │
│  🔴 URGENT (Today):                                     │
│  • Booking #1234 - Change within 24 hrs (Event tmrw)   │
│  • Booking #5678 - No menu received (Event in 3 days)  │
│                                                          │
│  🟠 HIGH (This Week):                                   │
│  • Booking #9012 - Bad review (2 stars) - Follow up    │
│  • Booking #3456 - Date change request                 │
│                                                          │
│  🟡 MEDIUM (Next 2 Weeks):                              │
│  • Booking #7890 - Complex dietary restriction         │
│                                                          │
│  📊 Stats (Last 30 Days):                              │
│  • AI handled: 87% (348 interactions)                   │
│  • Escalated: 13% (52 cases)                           │
│  • Avg resolution time: 2.3 hours                       │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema for Automation

```sql
-- Track automated reminders
CREATE TABLE automated_reminders (
    id SERIAL PRIMARY KEY,
    booking_id VARCHAR(50) REFERENCES bookings(id),
    reminder_type VARCHAR(50), -- '7_day', '4_day', '24_hour', 'post_event'
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(20), -- 'pending', 'sent', 'failed'
    response_received BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track escalations
CREATE TABLE escalations (
    id SERIAL PRIMARY KEY,
    booking_id VARCHAR(50) REFERENCES bookings(id),
    priority VARCHAR(20), -- 'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    reason VARCHAR(255),
    customer_request TEXT,
    action_required TEXT,
    deadline TIMESTAMP,
    assigned_to VARCHAR(100),
    status VARCHAR(20), -- 'open', 'in_progress', 'resolved', 'closed'
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Track post-event feedback
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    booking_id VARCHAR(50) REFERENCES bookings(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    review_source VARCHAR(50), -- 'google', 'yelp', 'internal'
    escalated_to_human BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track customer sentiment for personalization
CREATE TABLE customer_sentiment (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(id),
    sentiment_score DECIMAL(3, 2), -- 0.00-1.00 (promoter score)
    last_rating INTEGER,
    total_bookings INTEGER DEFAULT 1,
    is_repeat_customer BOOLEAN DEFAULT FALSE,
    is_referrer BOOLEAN DEFAULT FALSE,
    preferred_proteins JSONB, -- Track favorite proteins
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 Implementation Recommendation

### **Phase 1: Core Automation** (Week 1-2)

1. ✅ 7-day reminder system
2. ✅ 4-day menu deadline check
3. ✅ 24-hour adjustment handling
4. ✅ Human escalation triggers
5. ✅ Database schema creation

### **Phase 2: Smart Review System** (Week 2-3)

1. ✅ Post-event follow-up (1 day after)
2. ✅ Rating collection
3. ✅ Smart routing (good → external, bad → internal)
4. ✅ Escalation for bad reviews

### **Phase 3: Advanced Features** (Week 3-4)

1. ✅ Repeat customer recognition ("Welcome back!")
2. ✅ Referral tracking ("Thanks for coming through [Name]!")
3. ✅ Sentiment analysis for personalization
4. ✅ Admin dashboard for escalations

---

## 📊 Success Metrics

**Target Performance**:

- 📧 **Reminder delivery rate**: >98%
- ⏰ **Menu selection by deadline**: >85%
- 🤖 **AI resolution rate**: >80% (only 20% escalate)
- ⭐ **Review collection rate**: >60%
- 😊 **Good review routing**: >90% of 4-5 star customers
- 🚨 **Escalation response time**: <2 hours for URGENT, <24 hours for
  HIGH

**Cost Savings**:

- Automate ~350 routine interactions/month
- Reduce manual reminder workload by ~70%
- Capture 3x more reviews through automated follow-up

---

## ✅ Next Steps

1. **Approve this system design?** (Yes/No/Modify)
2. **Review links needed**:
   - Google Review URL
   - Yelp Review URL
   - Internal feedback form URL
3. **Add to TODO list as**:
   - **Week 5: Automated Customer Service System** (4 days
     implementation)

**Ready to add this to your roadmap?** 🚀

---

## 🔄 Dynamic Data Architecture (Auto-Update System)

### **Critical Requirement**: All Policies, Pricing, and FAQs Are Dynamic

**Problem**: If policies, pricing, or upgrades are hardcoded in AI
prompts, admins must deploy code every time they change something.

**Solution**: **KnowledgeService** (Week 1 TODO) - AI queries database
on every conversation.

---

### **How Dynamic Data Works**

```
┌─────────────────────────────────────────────────────────┐
│  Admin Panel (React) - Edit Interface                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Admin clicks: "Lobster is now $18 (was $15)"           │
│  Admin clicks: "Save"                                    │
│                                                           │
└──────────────────────────┬──────────────────────────────┘
                           ↓
                  POST /api/v1/menu/addons/{id}
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Database Updated (PostgreSQL)                           │
├─────────────────────────────────────────────────────────┤
│  addon_items table:                                      │
│  - name: "Lobster Tail"                                 │
│  - price: 18.00 (was 15.00)                            │
│  - last_updated: 2025-11-11 10:30:00                   │
└──────────────────────────┬──────────────────────────────┘
                           ↓
                  Customer asks AI: "How much is lobster?"
                           ↓
┌─────────────────────────────────────────────────────────┐
│  KnowledgeService.get_menu_upgrades()                   │
├─────────────────────────────────────────────────────────┤
│  1. Queries database for latest pricing                 │
│  2. Caches result for 5 seconds (performance)           │
│  3. Returns fresh data to AI                            │
└──────────────────────────┬──────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  AI Response                                             │
├─────────────────────────────────────────────────────────┤
│  "Lobster tail is +$18 per person 🦞"                   │
│  (Uses NEW price automatically)                          │
└─────────────────────────────────────────────────────────┘
```

**Update Time**: **<5 seconds** (next AI conversation uses new data)

---

### **Database Schema for Dynamic Data**

```sql
-- Business Rules (Cancellation, Deposit, Refund, Rescheduling)
CREATE TABLE business_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL,  -- 'cancellation', 'deposit', 'refund', 'rescheduling'
    title VARCHAR(255),               -- "Cancellation Policy"
    content TEXT NOT NULL,            -- Full policy text (AI reads this)
    value JSONB,                      -- Structured data: {"deposit_amount": 100, "refund_days": 7}
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,        -- Track policy versions
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)           -- Admin who made the change
);

-- Menu Upgrades (Salmon, Lobster, Filet, Scallops, Yakisoba, etc.)
CREATE TABLE addon_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),             -- 'premium_protein', 'enhancement', 'extra'
    display_order INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- FAQs (Dynamic, Editable)
CREATE TABLE faq_items (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50),             -- 'booking', 'menu', 'policies', 'setup'
    view_count INTEGER DEFAULT 0,     -- Track most-viewed FAQs
    helpful_count INTEGER DEFAULT 0,  -- Customer feedback: "Was this helpful?"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Seasonal Offers (Holiday Pricing, Promotions)
CREATE TABLE seasonal_offers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    discount_type VARCHAR(50),        -- 'percentage', 'fixed_amount', 'free_addon'
    discount_value DECIMAL(10, 2),
    valid_from DATE,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for fast queries
CREATE INDEX idx_business_rules_type ON business_rules(rule_type) WHERE is_active = TRUE;
CREATE INDEX idx_addon_items_category ON addon_items(category) WHERE is_available = TRUE;
CREATE INDEX idx_faq_items_category ON faq_items(category) WHERE is_active = TRUE;
CREATE INDEX idx_seasonal_offers_dates ON seasonal_offers(valid_from, valid_to) WHERE is_active = TRUE;
```

---

### **KnowledgeService Implementation** (Week 1 TODO)

```python
# apps/backend/src/api/ai/services/knowledge_service.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from cachetools import TTLCache

class KnowledgeService:
    """
    Centralized service for dynamic business knowledge
    Replaces static prompts with database queries
    """

    def __init__(self, db: Session, pricing_service: PricingService):
        self.db = db
        self.pricing_service = pricing_service

        # Cache results for 5 seconds (balance freshness vs performance)
        self.cache = TTLCache(maxsize=100, ttl=5)

    async def get_business_charter(self) -> Dict:
        """
        Get complete business information for AI system prompt
        Called on every customer conversation start
        """
        cache_key = "business_charter"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query fresh data from database
        charter = {
            "pricing": await self._get_pricing_info(),
            "policies": await self._get_active_policies(),
            "upgrades": await self._get_menu_upgrades(),
            "seasonal_offers": await self._get_active_offers(),
            "last_updated": datetime.now().isoformat()
        }

        self.cache[cache_key] = charter
        return charter

    async def _get_pricing_info(self) -> Dict:
        """Get current pricing (queries PricingService + database)"""
        deposit = await self.db.query(BusinessRule).filter_by(
            rule_type="deposit",
            is_active=True
        ).first()

        return {
            "adult_base": float(await self.pricing_service.get_adult_price()),
            "child_base": float(await self.pricing_service.get_child_price()),
            "deposit_amount": deposit.value.get("amount", 100) if deposit else 100,
            "party_minimum": 550,
            "travel_fee_free_miles": 30,
            "travel_fee_per_mile": 2.00
        }

    async def _get_active_policies(self) -> List[Dict]:
        """Get all active business policies"""
        policies = await self.db.query(BusinessRule).filter_by(
            is_active=True
        ).all()

        return [
            {
                "type": policy.rule_type,
                "title": policy.title,
                "content": policy.content,
                "data": policy.value
            }
            for policy in policies
        ]

    async def _get_menu_upgrades(self) -> List[Dict]:
        """Get current menu upgrades with latest pricing"""
        upgrades = await self.db.query(AddonItem).filter_by(
            is_available=True
        ).order_by(AddonItem.display_order).all()

        return [
            {
                "name": upgrade.name,
                "description": upgrade.description,
                "price": float(upgrade.price),
                "category": upgrade.category
            }
            for upgrade in upgrades
        ]

    async def _get_active_offers(self) -> List[Dict]:
        """Get current seasonal offers"""
        today = datetime.now().date()

        offers = await self.db.query(SeasonalOffer).filter(
            SeasonalOffer.is_active == True,
            SeasonalOffer.valid_from <= today,
            SeasonalOffer.valid_to >= today
        ).all()

        return [
            {
                "title": offer.title,
                "description": offer.description,
                "discount_type": offer.discount_type,
                "discount_value": float(offer.discount_value)
            }
            for offer in offers
        ]

    async def get_cancellation_policy(self) -> str:
        """Get current cancellation policy (for AI to explain)"""
        policy = await self.db.query(BusinessRule).filter_by(
            rule_type="cancellation",
            is_active=True
        ).first()

        return policy.content if policy else "Please contact us for cancellation policy details."

    async def get_faq_answer(self, question: str) -> Optional[Dict]:
        """
        Search FAQ database for relevant answer
        Uses keyword matching (can upgrade to vector search later)
        """
        # Simple keyword search (Phase 1)
        faqs = await self.db.query(FAQItem).filter(
            FAQItem.is_active == True
        ).all()

        # Find best match based on question keywords
        best_match = None
        max_score = 0

        for faq in faqs:
            score = self._calculate_relevance(question.lower(), faq.question.lower())
            if score > max_score:
                max_score = score
                best_match = faq

        if best_match and max_score > 0.3:  # 30% relevance threshold
            # Increment view count
            best_match.view_count += 1
            await self.db.commit()

            return {
                "question": best_match.question,
                "answer": best_match.answer,
                "confidence": max_score
            }

        return None

    def _calculate_relevance(self, query: str, faq_question: str) -> float:
        """Calculate relevance score between customer question and FAQ"""
        query_words = set(query.split())
        faq_words = set(faq_question.split())

        # Jaccard similarity
        intersection = query_words.intersection(faq_words)
        union = query_words.union(faq_words)

        return len(intersection) / len(union) if union else 0.0
```

---

### **AI Agent Integration** (Uses KnowledgeService)

```python
# apps/backend/src/api/ai/orchestrator/ai_orchestrator.py

class AIOrchestrator:
    def __init__(self):
        self.knowledge_service = KnowledgeService(db, pricing_service)
        self.tone_analyzer = ToneAnalyzer()

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process customer message with dynamic knowledge"""

        # 1. Get real-time business data
        business_charter = await self.knowledge_service.get_business_charter()

        # 2. Detect customer tone
        customer_tone = self.tone_analyzer.detect_tone(request.message)

        # 3. Build dynamic system prompt
        system_prompt = f"""
You are My Hibachi AI Customer Service Assistant.

**CURRENT BUSINESS INFORMATION** (Updated: {business_charter['last_updated']}):

**Pricing**:
- Adult: ${business_charter['pricing']['adult_base']}/person
- Child: ${business_charter['pricing']['child_base']}/person
- Deposit: ${business_charter['pricing']['deposit_amount']}
- Party minimum: ${business_charter['pricing']['party_minimum']}

**Active Policies**:
{self._format_policies(business_charter['policies'])}

**Menu Upgrades**:
{self._format_upgrades(business_charter['upgrades'])}

**Current Promotions**:
{self._format_offers(business_charter['seasonal_offers'])}

**Customer Tone Detected**: {customer_tone.value}
Adapt your response to match their communication style.
"""

        # 4. Route to appropriate agent with dynamic prompt
        agent = self._get_agent(request.agent_type)
        response = await agent.process(
            message=request.message,
            system_prompt=system_prompt,
            context={"customer_tone": customer_tone.value}
        )

        return response
```

---

### **Admin Panel UI** (Week 4 TODO)

```tsx
// apps/admin/src/pages/knowledge-base/policies.tsx

import { useState, useEffect } from 'react';

export default function PoliciesEditor() {
  const [policies, setPolicies] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    const response = await fetch('/api/v1/business-rules');
    const data = await response.json();
    setPolicies(data);
  };

  const handleSave = async (policyId, updates) => {
    try {
      await fetch(`/api/v1/business-rules/${policyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      // ✅ Success - AI will use new policy immediately
      toast.success(
        'Policy updated! AI will use new version in next conversation.'
      );

      // Refresh list
      fetchPolicies();
      setEditing(null);
    } catch (error) {
      toast.error('Failed to update policy');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Business Policies</h1>

      <div className="space-y-4">
        {policies.map(policy => (
          <div
            key={policy.id}
            className="bg-white p-4 rounded shadow"
          >
            <h3 className="font-semibold">{policy.title}</h3>

            {editing === policy.id ? (
              <div>
                <textarea
                  value={policy.content}
                  onChange={e =>
                    updatePolicy(policy.id, e.target.value)
                  }
                  className="w-full p-2 border rounded"
                  rows={6}
                />
                <button onClick={() => handleSave(policy.id, policy)}>
                  Save Changes
                </button>
              </div>
            ) : (
              <div>
                <p className="text-gray-600">{policy.content}</p>
                <button onClick={() => setEditing(policy.id)}>
                  Edit
                </button>
              </div>
            )}

            <p className="text-xs text-gray-400 mt-2">
              Last updated:{' '}
              {new Date(policy.last_updated).toLocaleString()}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h4 className="font-semibold">ℹ️ How It Works:</h4>
        <p className="text-sm">
          When you save changes here, the AI automatically uses the
          new policy in the next customer conversation (within 5
          seconds). No code deployment needed!
        </p>
      </div>
    </div>
  );
}
```

---

### **Benefits of Dynamic Data System**

| Benefit                  | Description                                                                          | Impact                                  |
| ------------------------ | ------------------------------------------------------------------------------------ | --------------------------------------- |
| **No Code Deploys**      | Admin edits pricing/policies in UI → Database updated → AI uses new data immediately | Save 2-4 hours per policy change        |
| **Always Current**       | AI never gives outdated information                                                  | Zero customer confusion from stale data |
| **Version History**      | Track who changed what and when                                                      | Audit trail for compliance              |
| **A/B Testing**          | Test different policy wording, measure conversion                                    | Data-driven optimization                |
| **Seasonal Flexibility** | Add holiday pricing, promotions without code changes                                 | Quick market response                   |

---

### **Performance Optimization**

**Caching Strategy**:

- Cache business charter for **5 seconds**
- Cache FAQ searches for **30 seconds**
- Invalidate cache on database updates (via webhook)

**Database Query Performance**:

- Indexed queries: `<10ms`
- Cached queries: `<1ms`
- Full system prompt build: `<50ms`

**Load Testing Results** (Expected):

- 100 concurrent customers: AI response time `<500ms`
- 1,000 requests/minute: Database handles with ease
- Cache hit rate: `>95%`

---

### **Migration Path from Static to Dynamic**

**Phase 1** (Week 1): Build infrastructure

- Create database tables
- Implement KnowledgeService
- Update AI agents to use KnowledgeService

**Phase 2** (Week 2): Migrate existing data

- Extract policies from static `.md` files
- Insert into database with proper structure
- Seed FAQs, pricing, upgrades

**Phase 3** (Week 4): Admin UI

- Build policy editor
- Build FAQ manager
- Build upgrade pricing editor

**Phase 4** (Production): Deprecate static prompts

- Monitor for 1 week (shadow mode)
- Switch all traffic to dynamic system
- Remove static prompt files

---

## 🎯 Summary: Dynamic Data Architecture

**What You Already Have**:

- ✅ PricingService (database-driven pricing)
- ✅ Architecture design (Week 1 TODO)
- ✅ Database schema planned

**What You Need to Build**:

- 🔨 KnowledgeService class (Week 1)
- 🔨 Database migrations (Week 1)
- 🔨 Seed data (Week 2)
- 🔨 Admin panel UI (Week 4)

**Result**:

- ✨ Admin edits pricing/policies in UI
- ✨ Database updated instantly
- ✨ AI uses new data in next conversation (<5 sec)
- ✨ Zero code deployments for content changes
- ✨ Always accurate, never stale information

**This is already part of your Week 1-4 roadmap!** 🚀
