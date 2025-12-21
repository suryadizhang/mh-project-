# 📋 Batch Deployment Checklists

**Version:** 1.1.0 **Created:** December 4, 2025 **Updated:** December
4, 2025 **Purpose:** Detailed checklists for each deployment batch

> 📌 **See Also:**
>
> - [CONSOLIDATED_MASTER_ROADMAP.md](../CONSOLIDATED_MASTER_ROADMAP.md) -
>   ALL plans consolidated
> - [DEPLOYMENT_BATCH_STRATEGY.md](./DEPLOYMENT_BATCH_STRATEGY.md) -
>   Batch strategy overview

---

## 🔴 BATCH 1: Core Booking Engine + Security

### Pre-Development Checklist

```markdown
□ Create branch: feature/batch-1-core □ Review all core routes
documentation □ Verify database schema is up to date □ Check all
environment variables documented □ Review Cloudflare account access □
Verify RBAC tables created (roles, permissions, role_permissions,
user_roles)
```

### Development Tasks

```markdown
CORE API □ Verify Customer CRUD endpoints (~20 routes) □ POST
/api/customers - Create customer □ GET /api/customers - List customers
□ GET /api/customers/{id} - Get customer □ PUT /api/customers/{id} -
Update customer □ DELETE /api/customers/{id} - Delete customer

□ Verify Chef CRUD endpoints (~15 routes) □ POST /api/chefs - Create
chef □ GET /api/chefs - List chefs □ GET /api/chefs/{id} - Get chef □
PUT /api/chefs/{id} - Update chef □ GET /api/chefs/{id}/availability -
Get availability

□ Verify Booking CRUD endpoints (~30 routes) □ POST /api/bookings -
Create booking □ GET /api/bookings - List bookings □ GET
/api/bookings/{id} - Get booking □ PUT /api/bookings/{id} - Update
booking □ POST /api/bookings/{id}/assign-chef - Assign chef □ POST
/api/bookings/{id}/confirm - Confirm booking □ POST
/api/bookings/{id}/cancel - Cancel booking

□ Verify Quote/Pricing endpoints (~15 routes) □ POST
/api/quote/calculate - Calculate quote □ GET /api/quote/{id} - Get
quote □ POST /api/quote/{id}/convert - Convert to booking

□ Verify Authentication endpoints (~15 routes) □ POST
/api/auth/login - User login □ POST /api/auth/register - User
registration □ POST /api/auth/refresh - Refresh token □ POST
/api/auth/logout - User logout □ GET /api/auth/me - Current user

□ Verify Health endpoints (~5 routes) □ GET /health - Basic health □
GET /health/ready - Readiness check □ GET /health/live - Liveness
check

4-TIER RBAC SYSTEM □ SUPER_ADMIN role - full access + user management
□ ADMIN role - most operations except user management □
CUSTOMER_SUPPORT role - read + limited write □ STATION_MANAGER role -
station-specific CRUD □ CHEF role - own profile + assigned bookings
only □ Role decorators on protected endpoints □ Permission checks on
API routes □ Station-based multi-tenancy (station_id FK)

AUDIT TRAIL SYSTEM □ audit_log table created and functional □ Soft
delete working (30-day restore window) □ Delete reason tracking
(10-500 chars mandatory) □ deleted_at, deleted_by columns populated □
Audit log capturing all data changes

FAILED BOOKING LEAD CAPTURE □ Auto-capture when booking fails □ Lead
source tracking □ AI follow-up trigger ready □ Admin lead queue
functional

STATION MANAGEMENT (Admin GUI) □ Station interface updated with
geocoding fields (lat/lng, geocode_status) □ Station interface
includes service_area_radius, escalation_radius_miles □
StationEditForm component created with full edit capability □ Geocode
Address button triggers Google Maps API □ Service area configuration
UI (radius, escalation threshold) □ Station overview shows location,
geocoding status, service area □ Station list shows code and geocoding
indicator □ Backend geocode endpoint: POST
/api/admin/stations/{id}/geocode □ Station data connected to dynamic
variables management

ADDRESS SERVICE AREA VALIDATION □ Address model has lat/lng fields for
geocoding □ Station model has lat/lng for headquarters location □
Service area check uses nearest station algorithm (multi-station
ready) □ Haversine distance calculation implemented □ is_serviceable
flag set based on distance from nearest station □ requires_escalation
flag for bookings beyond escalation_radius_miles □
/api/v1/addresses/check-service-area returns station_code,
distance_miles □ Default service_area_radius = 150 miles □ Default
escalation_radius_miles = 150 miles
```

### Security Tasks (Cloudflare)

```markdown
CLOUDFLARE TUNNEL □ Install cloudflared on VPS □ Create tunnel:
cloudflared tunnel create myhibachi □ Configure tunnel routing
(config.yml) □ Set up tunnel as systemd service □ Verify VPS IP is
hidden (DNS shows Cloudflare IPs) □ Test tunnel connectivity

CLOUDFLARE ACCESS □ Create Access application for SSH □ Configure
identity provider (Google/GitHub) □ Create Access policy (team members
only) □ Test SSH via Access (no direct SSH) □ Create Access
application for Admin Panel □ Configure admin panel policy

WAF CONFIGURATION □ Enable Cloudflare Managed Ruleset □ Enable OWASP
Core Ruleset □ Create custom rule: Rate limit API (100 req/min) □
Create custom rule: Block known bad user agents □ Create custom rule:
Protect /api/admin/\* endpoints □ Test WAF blocks SQL injection □ Test
WAF blocks XSS attempts

SSL/TLS □ Enable Full (Strict) SSL mode □ Enable Always Use HTTPS □
Enable HSTS □ Set minimum TLS version to 1.2 □ Verify certificate is
valid
```

### Testing Checklist

```markdown
UNIT TESTS □ Customer service tests pass □ Chef service tests pass □
Booking service tests pass □ Quote service tests pass □ Auth service
tests pass □ RBAC decorator tests pass □ Audit trail tests pass

INTEGRATION TESTS □ Create booking flow (end-to-end) □ Edit booking
flow □ Cancel booking flow □ Assign chef flow □ Authentication flow □
RBAC permissions enforced correctly □ Failed booking captures lead

SECURITY TESTS □ SQL injection blocked by WAF □ XSS blocked by WAF □
Rate limiting working □ Unauthorized access blocked □ JWT validation
working □ RBAC prevents unauthorized operations

LOAD TESTS □ 50 concurrent users - API <200ms □ 100 concurrent users -
API <500ms □ No memory leaks after 1000 requests
```

### Pre-Merge Checklist (feature → dev)

```markdown
□ All unit tests pass (100%) □ All integration tests pass (95%+) □
Code review approved by 2+ reviewers □ No security vulnerabilities
(npm audit, safety) □ No console.log/print statements □ Documentation
updated □ Feature flags configured: □ FEATURE_CORE_API=true □
FEATURE_AUTH=true □ FEATURE_CLOUDFLARE_TUNNEL=true □ FEATURE_RBAC=true
□ FEATURE_AUDIT_TRAIL=true □ FEATURE_SOFT_DELETE=true □
FEATURE_FAILED_BOOKING_LEAD_CAPTURE=true □ Error handling complete
```

### Pre-Production Checklist (dev → main)

```markdown
□ Full regression test suite passes □ Performance benchmarks met □
Load testing passed □ Security scan passed □ Manager sign-off obtained
□ Rollback plan tested □ Monitoring alerts configured □ Environment
variables set in production □ Database migrations applied □ Backup
verified
```

### Post-Deployment Checklist

```markdown
□ Health checks passing (/health, /health/ready, /health/live) □ No
error spikes in logs (monitor 4 hours) □ Create booking - manually
verified □ Edit booking - manually verified □ Cancel booking -
manually verified □ Assign chef - manually verified □ Login/logout -
manually verified □ RBAC permissions enforced - verified □ Audit trail
recording - verified □ Failed booking lead capture - verified □
Cloudflare Tunnel active □ WAF blocking attacks □ SSL/TLS working
(check via SSL Labs) □ 48-hour stability period - no issues □
Post-deployment review completed
```

### Additional Batch 1 Features (NEW)

```markdown
BOOKING ENHANCEMENTS □ Booking Confirmation SMS - Send immediately on
booking creation □ Duplicate Booking Prevention - Check same
date/time/venue conflicts □ Venue Access Instructions Field - Gate
codes, parking, elevator info □ Emergency Contact Field - Backup phone
for event day □ Booking Notes/Tags System - Internal staff notes per
booking

CHEF MANAGEMENT UI □ Chef Availability Calendar UI - Visual calendar
in admin panel □ Chef schedule grid view - Day/Week/Month views □
Drag-and-drop assignment - Quick chef assignment

RESPONSE SLA MONITORING □ SLA timer starts on customer message receipt
□ Warning alert: 60 min (SMS), 2 hr (Email) - Yellow flag □ Critical
alert: 90 min (SMS), 4 hr (Email) - Supervisor notified □ Escalation:
2 hr (SMS), 8 hr (Email) - Manager + auto-assign □ SLA dashboard
showing pending responses □ Auto-acknowledge: "Thanks! We'll respond
within 30 minutes"
```

### Success Criteria

```markdown
□ All 150 routes responding correctly □ Average API response time
<200ms □ Error rate <0.1% □ Zero security incidents □ Cloudflare
Tunnel hiding VPS IP □ WAF blocking malicious requests □ All health
checks passing □ RBAC permissions enforced correctly □ Audit trail
capturing all changes □ No critical bugs for 48 hours
```

---

## 🗓️ SMART SCHEDULING SYSTEM

> **Spec File:**
> `.github/instructions/17-SMART_SCHEDULING_SYSTEM.instructions.md`
> **Last Updated:** 2025-12-21

### Overview

The Smart Scheduling System is an intelligent booking management
solution that spans multiple batches. It includes 8 phases for
optimizing slot availability, chef assignments, and customer
negotiations.

### Phase Status Summary

| Phase | Feature                | Status      | Implementation           |
| ----- | ---------------------- | ----------- | ------------------------ |
| **1** | Foundation (Geocoding) | ✅ COMPLETE | `geocoding_service.py`   |
| **2** | Auth & RBAC            | ✅ COMPLETE | `core/security.py`       |
| **3** | Chef Management        | ✅ COMPLETE | `chef_optimizer.py`      |
| **4** | Travel Time            | ✅ COMPLETE | `travel_time_service.py` |
| **5** | Smart Suggestions      | ✅ COMPLETE | `suggestion_engine.py`   |
| **6** | Slot Adjustment        | ✅ COMPLETE | `slot_manager.py`        |
| **7** | Chef Optimizer         | ✅ COMPLETE | `chef_optimizer.py`      |
| **8** | Negotiation            | ✅ COMPLETE | `negotiation_service.py` |

### Development Tasks

```markdown
PHASE 1: FOUNDATION ✅ COMPLETE □ Database schema for booking
locations (lat/lng) ✅ □ Google Maps geocoding service ✅ □ Slot
configuration table ✅ □ Address validation API ✅

PHASE 2: AUTH & RBAC ✅ COMPLETE □ JWT authentication verified ✅ □
API key authentication ✅ □ 4-tier RBAC (Super Admin → Admin → Staff →
Customer) ✅ □ Permission decorators ✅

PHASE 3: CHEF MANAGEMENT ✅ COMPLETE □ Chef locations table ✅ □ Chef
availability API ✅ □ Chef assignment API ✅ □ Preferred chef handling
✅ □ Travel scoring (40% weight) ✅ □ Skill matching (20% weight) ✅ □
Workload balance (15% weight) ✅ □ Rating scoring (15% weight) ✅ □
Customer preference (+50 bonus) ✅

PHASE 4: TRAVEL TIME ✅ COMPLETE □ Google Maps Distance Matrix API ✅
□ Travel time caching (7-day cache) ✅ □ Rush hour multiplier (Mon-Fri
3-7PM = 1.5x) ✅ □ Travel-aware slot checker ✅

PHASE 5: SMART SUGGESTIONS ✅ COMPLETE □ Suggestion engine service ✅
□ Alternative time finder (same day) ✅ □ Next day/week suggestions ✅
□ Priority scoring for suggestions ✅

PHASE 6: DYNAMIC SLOT ADJUSTMENT ✅ COMPLETE □ 4 time slots: 12PM,
3PM, 6PM, 9PM ✅ □ ±30 min preferred / ±60 min max adjustment ✅ □
Event duration calculation (60 + guests × 3, max 120 min) ✅ □
Conflict resolution logic ✅

PHASE 7: CHEF OPTIMIZER ✅ COMPLETE □ Optimizer service ✅ □ Guest
count skill matching ✅ □ Travel efficiency scoring ✅ □ Workload
balance scoring ✅ □ Customer preference bonus ✅ □ Station manager
suggestions UI ⏳ PENDING

PHASE 8: NEGOTIATION SYSTEM ✅ COMPLETE □ Negotiation request tracking
✅ □ SMS/Email notification templates ✅ □ Response tracking with
incentives ✅ □ Auto-adjustment on acceptance ✅
```

### API Endpoints (Implemented)

```markdown
AVAILABILITY □ POST /api/v1/scheduling/availability/check ✅ □ POST
/api/v1/scheduling/availability/calendar ✅

TRAVEL TIME □ POST /api/v1/scheduling/travel-time/calculate ✅

GEOCODING □ POST /api/v1/scheduling/geocode ✅ □ GET
/api/v1/scheduling/geocode/validate ✅

CHEF ASSIGNMENT (STUB - Returns placeholder data) □ POST
/api/v1/scheduling/chef/recommend ⚠️ □ GET
/api/v1/scheduling/chef/top-recommendations ⚠️

NEGOTIATION □ POST /api/v1/scheduling/negotiations ✅ □ POST
/api/v1/scheduling/negotiations/respond ✅ □ GET
/api/v1/scheduling/negotiations/pending ✅

CONFIGURATION □ GET /api/v1/scheduling/slots/config ✅ □ POST
/api/v1/scheduling/duration/calculate ✅
```

### Implementation Files

| Service        | File                                                          | Status      |
| -------------- | ------------------------------------------------------------- | ----------- |
| Geocoding      | `apps/backend/src/services/scheduling/geocoding_service.py`   | ✅ COMPLETE |
| Travel Time    | `apps/backend/src/services/scheduling/travel_time_service.py` | ✅ COMPLETE |
| Slot Manager   | `apps/backend/src/services/scheduling/slot_manager.py`        | ✅ COMPLETE |
| Suggestions    | `apps/backend/src/services/scheduling/suggestion_engine.py`   | ✅ COMPLETE |
| Negotiation    | `apps/backend/src/services/scheduling/negotiation_service.py` | ✅ COMPLETE |
| Availability   | `apps/backend/src/services/scheduling/availability_engine.py` | ✅ COMPLETE |
| Chef Optimizer | `apps/backend/src/services/scheduling/chef_optimizer.py`      | ⚠️ STUB     |
| Router         | `apps/backend/src/routers/v1/scheduling.py`                   | ✅ COMPLETE |

### ✅ Smart Scheduling System COMPLETE

All 8 phases of the Smart Scheduling System are now implemented:

**Scoring Algorithm (chef_optimizer.py):**

1. **Travel Score** (40% weight) - Minutes from previous location
2. **Skill Score** (20% weight) - Match guest count to chef specialty
3. **Workload Score** (15% weight) - Balance bookings across chefs
4. **Rating Score** (15% weight) - Chef's average rating
5. **Preference Score** (10% weight) - Customer requested chef (+50
   bonus)

**Remaining UI Work:**

- Station Manager chef suggestions UI (Phase 7D)

---

## �🔴 BATCH 2: Payment Processing

### Pre-Development Checklist

```markdown
□ Batch 1 stable for 48+ hours □ Create branch:
feature/batch-2-payments □ Stripe account verified (production ready)
□ Stripe webhook endpoint planned □ StripeCustomer model already
created ✅
```

### Development Tasks

```markdown
STRIPE INTEGRATION □ Enable Stripe router in main.py (uncomment lines
838-871) □ Configure Stripe API keys □ Set up Stripe webhook endpoint
□ Configure webhook secret

PAYMENT ENDPOINTS □ POST /api/v1/stripe/checkout-session - Create
checkout □ POST /api/v1/stripe/payment-intent - Create payment intent
□ GET /api/v1/stripe/payment/{id} - Get payment status □ POST
/api/v1/stripe/refund - Process refund □ POST /api/v1/stripe/webhook -
Handle Stripe events

WEBHOOK HANDLING □ Handle checkout.session.completed □ Handle
payment_intent.succeeded □ Handle payment_intent.failed □ Handle
charge.refunded □ Handle customer.created □ Log all webhook events □
Implement idempotency (prevent duplicate processing)

INVOICE GENERATION □ Generate PDF invoice on payment success □ Send
invoice via email □ Store invoice in database □ Admin can
view/download invoices

DYNAMIC PRICING MANAGEMENT (From DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md)
□ Create price_change_history table □ id, price_type, old_value,
new_value, changed_by, changed_at, reason □ Admin Pricing API □ GET
/api/v1/admin/pricing - List all prices □ PUT
/api/v1/admin/pricing/{id} - Update price □ GET
/api/v1/admin/pricing/history - Price change history □ Pricing Admin
UI □ View current prices □ Edit prices with reason □ View price change
history □ Price validation rules □ No negative prices □ Min/max bounds
□ Mandatory change reason □ Database as source of truth (remove
hardcoded prices) □ Price change notifications to admin

DEPOSIT REMINDER & AUTO-CANCEL SYSTEM (NEW) □ Deposit window: 2 hours
from booking creation □ First reminder: Immediately after booking
(SMS + Email) □ Second reminder: At 1-hour mark (SMS + Email) □ Staff
alert: At 2-hour mark (manual review option) □ Auto-cancel: At 6-hour
mark if no deposit (system auto-cancels) □ Cancel notification: SMS +
Email to customer □ Lead capture: Failed deposits captured as leads
for follow-up □ Database: booking.deposit_due_at,
booking.deposit_reminded_at

TIP COLLECTION SYSTEM (NEW) □ Tip UI integrated into checkout flow
(optional) □ Suggested tip amounts: 20%, 25%, 30%, Custom □ Tip
displayed on payment confirmation □ 100% of tip goes to assigned chef
□ Tip tracking in chef payment reports □ Database:
payments.tip_amount, payments.tip_chef_id

SPLIT PAYMENT SUPPORT (NEW) □ Allow multiple payment methods per
booking □ Primary card pays deposit, second card pays balance □
Maximum 3 payment splits per booking □ Each split tracked separately
in Stripe □ UI for adding/removing payment methods

PAYMENT PLANS (NEW) □ Deposit now, balance due X days before event □
Automatic balance reminder (7 days, 3 days, 1 day before) □
Auto-charge saved card on due date (with customer consent) □ Fallback
to manual payment if auto-charge fails

PROMOTION SYSTEM (NEW - Admin/Super Admin Only) □ Create promotion:
name, discount_type, discount_value, valid_from, valid_to □ Promotion
codes: unique codes for tracking □ Admin creates promotions (Super
Admin approves) □ Apply promotion at checkout □ Track promotion usage
and revenue impact □ No automatic seasonal/holiday pricing - all year
same price □ Promotions are the ONLY way to adjust pricing

AUTOMATED REFUND RULES (NEW) □ Cancellation >72 hours: Full refund
(auto) □ Cancellation 24-72 hours: 50% refund (manual approval) □
Cancellation <24 hours: No refund (manual exception possible) □ Refund
audit trail with reason codes
```

### Testing Checklist

```markdown
STRIPE TEST MODE □ Create test checkout session □ Complete test
payment □ Verify webhook received □ Verify database updated □ Test
refund flow □ Test failed payment handling

DYNAMIC PRICING TESTS □ Admin can view all prices □ Admin can update
prices □ Price changes logged to history □ Validation rules enforced □
Old prices don't affect existing bookings

INTEGRATION TESTS □ Full payment flow (end-to-end) □ Deposit
collection flow □ Refund processing flow □ Webhook signature
validation □ Error handling for failed payments □ Dynamic pricing
updates reflected in quotes

EDGE CASES □ Double payment prevention □ Partial refund □ Full refund
□ Payment timeout handling □ Webhook retry handling □ Price update
during checkout
```

### Pre-Production Checklist

```markdown
□ Switch to Stripe production API keys □ Configure production webhook
URL □ Test with real card (small amount) □ Verify production webhook
receiving □ Finance team sign-off □ Refund policy documented □ Dynamic
pricing validation complete
```

### Post-Deployment Checklist

```markdown
□ Create payment - manually verified □ Complete checkout - manually
verified □ Webhook received - verified in Stripe dashboard □ Invoice
generated - verified □ Refund processed - manually verified □ Dynamic
pricing admin UI functional □ Price changes logged correctly □ 72-hour
stability period (money involved!) □ No payment errors □ Financial
reconciliation check
```

---

## 🟠 BATCH 3: Core AI

### Pre-Development Checklist

```markdown
□ Batch 2 stable for 48+ hours □ Create branch:
feature/batch-3-core-ai □ OpenAI API key ready □ All 7 agents already
built ✅ □ Intent router already built ✅
```

### Development Tasks

```markdown
AI ENDPOINTS □ POST /api/v1/ai/chat - Main chat endpoint □ GET
/api/v1/ai/conversations/{id} - Get conversation □ POST
/api/v1/ai/escalate - Manual escalation □ GET /api/v1/ai/agents - List
available agents

AGENT VERIFICATION □ LeadNurturingAgent - Test sales scenarios □
CustomerCareAgent - Test support scenarios □ OperationsAgent - Test
booking scenarios □ KnowledgeAgent - Test FAQ scenarios □
DistanceAgent - Test travel fee scenarios □ MenuAgent - Test menu
scenarios □ AllergenAgent - Test dietary scenarios

INTENT ROUTING □ Verify intent classification accuracy □ Test agent
selection logic □ Test fallback handling □ Test escalation triggers

CONVERSATION MANAGEMENT □ Verify context preservation □ Verify
conversation history storage □ Verify conversation retrieval □ Test
multi-turn conversations

SMART ESCALATION SYSTEM (From SMART_AI_ESCALATION_SYSTEM.md) □
Keyword-based auto-resume functional □ 30+ AI-handleable keywords
detected: price, cost, book, schedule, menu, date, time, chef,
location, area, serve, available, guests, dietary, allergy, vegan,
vegetarian, halal, kosher, setup, equipment, cancel, reschedule,
travel, fee, distance □ Human-only detection working □ 15+ escalation
keywords: manager, supervisor, complaint, lawsuit, attorney, lawyer,
human, person, agent, representative, frustrated, angry, unacceptable,
refund dispute □ Manual resume button visible in admin □ GTM Analytics
tracking all escalation events □ Target: 80%+ conversations handled by
AI without human

MISTRAL AI INTEGRATION (TIER 3 PROVIDER) □ Add MistralProvider class
(apps/backend/src/services/ai/providers/mistral.py) □ Use Mistral
Large 2 (123B) for medium complexity □ Use Mistral Small for
FAQ/simple queries □ 128K context window support □ Excellent function
calling for tool use □ Configure API key in GSM: MISTRAL_API_KEY □
Cost: ~$1-8/M tokens (5-10x cheaper than GPT-4o)

3-MODEL LLM STRATEGY (APPROVED) □ Tier 1: GPT-4o (OpenAI) - Complex
bookings, negotiations, tool calling □ Tier 2: Claude 3.5
(Anthropic) - Complaints, empathy, brand voice □ Tier 3: Mistral
(Large/Small) - FAQ, menu, simple queries □ NO GROK - Not needed for
hibachi catering use case □ API keys in GSM: OPENAI_API_KEY,
ANTHROPIC_API_KEY, MISTRAL_API_KEY □ Shadow learning collects data
from all 3 for future training

SMART AI ROUTER FOR COST OPTIMIZATION □ Query complexity classifier
(simple/medium/complex) □ Simple queries (FAQ, hours, basic info) →
Mistral Small ($1/M) □ Medium queries (booking details, menu) →
Mixtral 8x22B ($2/M) □ Complex queries (complaints, booking changes) →
Full ensemble ($15+/M) □ Complexity scoring based on:

- Query length
- Detected intent
- Customer sentiment
- Conversation history depth □ Cost tracking per conversation □
  Monthly AI cost dashboard □ Target: 60-70% cost reduction vs
  all-GPT-4

AI BOOKING MODIFICATION (NEW) □ AI can reschedule bookings (date/time
changes) □ AI can update guest count □ AI can change venue address □
All modifications require customer confirmation □ Audit trail for
AI-initiated changes

PROACTIVE FOLLOW-UP (NEW) □ AI initiates outreach for abandoned quotes
□ AI sends reminders for incomplete bookings □ Follow-up timing: 1
hour, 24 hours, 3 days □ Channel preference: SMS primary, Email
fallback

CONTEXT HANDOFF TO HUMAN (NEW) □ Full conversation summary when
escalating □ Customer info, booking details, previous interactions □
Sentiment analysis of conversation □ Agent sees all context instantly
(no re-asking)

AI QUALITY SCORING (NEW) □ Rate each AI response: helpful/not helpful
□ Track resolution rate per agent type □ Flag responses for human
review □ Training feedback loop
```

### Testing Checklist

```markdown
AI ACCURACY TESTS □ 100 sample queries - 80%+ correct agent selection
□ 100 sample queries - 80%+ appropriate responses □ Escalation
triggers - 95%+ accuracy □ Edge case handling - no crashes

SMART ESCALATION TESTS □ Auto-resume triggers on AI-handleable
keywords □ Escalation triggers on human-only keywords □ Manual resume
button works □ GTM events firing correctly □ 80%+ AI handling rate
achieved

PERFORMANCE TESTS □ Average response time <3 seconds □ No timeout
errors □ Handle 50 concurrent chat sessions

INTEGRATION TESTS □ Chat → booking creation □ Chat → quote generation
□ Chat → escalation to human □ Chat → knowledge base retrieval
```

### Post-Deployment Checklist

```markdown
□ Chat endpoint responding □ Intent routing working correctly □ All
agents responding appropriately □ Smart escalation auto-resume
functional □ 80%+ AI handling rate achieved □ Escalation queue
receiving items □ Admin can review AI conversations □ 48-hour
stability period □ No AI crashes or errors
```

---

## 🟠 BATCH 4: Communications

### Pre-Development Checklist

```markdown
□ Batch 2 stable □ Create branch: feature/batch-4-communications □
RingCentral credentials ready □ Meta Business accounts configured □
Deepgram API key ready □ CallStatus/CallDirection enums already added
✅
```

### Development Tasks

```markdown
RINGCENTRAL □ SMS sending/receiving □ Voice call handling □ Call
recording □ Webhook configuration □ Verify enums working (CallStatus,
CallDirection)

RINGCENTRAL WEBHOOK PIPELINE (From
PHASE_2_2_RINGCENTRAL_WEBHOOK_ANALYSIS.md) □ Create RingCentralVoiceAI
service (1 hour) □ Initialize service with credentials □ Implement
call event handlers □ Connect to AI orchestrator □ Webhook signature
validation (30 min) □ Verify X-RC-Signature header □ HMAC-SHA256
validation □ Reject invalid requests □ AI Orchestrator integration (1
hour) □ Route voice transcripts to intent router □ Generate AI
responses □ Convert to speech (TTS) □ End-to-end testing (30 min) □
Environment configuration (10 min) □ RC_WEBHOOK_SECRET □ RC_CLIENT_ID
□ RC_CLIENT_SECRET

RINGCENTRAL NATIVE RECORDING (From
PHASE_2_3_RINGCENTRAL_NATIVE_RECORDING.md) □ Database model update (10
min) □ Add rc_recording_id column □ Add rc_transcript column □ Add
rc_transcript_status column □ RC service methods (20 min) □
fetch_recording(call_id) - Get recording URL □
get_transcript(call_id) - Get RC transcript □
stream_recording(call_id) - Stream audio □ Webhook enhancement (15
min) □ Handle recording.completed event □ Handle transcript.ready
event □ Celery task for async processing (20 min) □ Background fetch
of recordings □ Background transcript retrieval □ API endpoints (30
min) □ GET /api/v1/calls/{id}/recording - Get recording URL □ GET
/api/v1/calls/{id}/transcript - Get transcript □ GET
/api/v1/calls/{id}/playback - Stream audio □ Testing (15 min) □ Unit
tests for RC service □ Integration test for full flow

META PLATFORMS □ WhatsApp Business API integration □ Facebook page
comments monitoring □ Facebook Messenger handling □ Instagram comments
monitoring □ Instagram DM handling □ Webhook verification

GOOGLE BUSINESS □ Google Business Messages integration □ Message
handling □ Auto-response capability

DEEPGRAM (Phase 2.1 - Already Complete ✅) □ Voice transcription
integration □ Real-time transcription (optional) □ Transcription
storage

AUTOMATED BOOKING REMINDERS (NEW) □ 24-hour reminder: SMS + Email □
3-hour reminder: SMS only □ 1-hour reminder: SMS only (chef on the
way) □ Reminder includes: date, time, address, chef name □ Reply to
confirm/reschedule option □ Reduce no-shows by 30-40%

TWO-WAY SMS FOR CHANGES (NEW) □ "Reply YES to confirm" functionality □
"Reply CHANGE to reschedule" functionality □ Parse customer SMS
responses □ Auto-update booking status based on reply □ Escalate
unrecognized responses to human

MESSAGE TEMPLATES LIBRARY (NEW) □ Pre-approved message templates □
Categories: confirmations, reminders, follow-ups, promos □ Variable
substitution: {customer_name}, {date}, {chef_name} □ Admin can
create/edit templates □ Track template performance (open rates,
responses)

READ RECEIPT TRACKING (NEW) □ Track if SMS delivered □ Track if email
opened □ Flag customers who don't engage □ Adjust follow-up strategy
based on engagement

RESPONSE SLA ALERTS (Integrated with Batch 1) □ SLA configuration per
channel (SMS, Email, Voice) □ Alert dashboard for pending responses □
Supervisor notification on SLA breach
```

### Testing Checklist

```markdown
RINGCENTRAL TESTS □ Send SMS successfully □ Receive SMS and process □
Make outbound call □ Receive inbound call □ Call recording works □
Webhook signature validation works □ RC native transcription works □
Recording playback works

RC NATIVE RECORDING TESTS □ Recording saved to database □ Transcript
retrieved from RC □ Playback URL working □ Celery task processing
correctly

META TESTS □ Send WhatsApp message □ Receive WhatsApp message □
Respond to Facebook comment □ Handle Messenger message □ Respond to
Instagram comment □ Handle Instagram DM

INTEGRATION TESTS □ SMS → AI response → SMS reply □ WhatsApp → AI
response → WhatsApp reply □ Voice call → RC recording → RC transcript
→ AI analysis
```

### Post-Deployment Checklist

```markdown
□ SMS sending/receiving works □ Voice calls connecting □ RC native
recording saving to database □ RC native transcripts retrievable □
Webhook signature validation working □ WhatsApp messages sending □
Facebook integration working □ Instagram integration working □ All
messages in unified inbox □ 48-hour stability period
```

---

## 🟡 BATCH 5: Advanced AI + Marketing Intelligence

### Pre-Development Checklist

```markdown
□ Batch 3 stable □ Create branch:
feature/batch-5-advanced-ai-marketing □ Google API credentials ready
(Ads, Analytics, Search Console) □ Psychology agent prompts prepared
```

### Development Tasks

```markdown
ADVANCED AI (From FULL_SELF_LEARNING_IMPLEMENTATION_ROADMAP.md) □
Emotion detection service (4 hours) □ Sentiment analysis model □
Emotion categories: happy, neutral, frustrated, angry, anxious □
Confidence scoring □ EmpathyAgent implementation (4 hours) □
De-escalation responses □ Hospitality psychology patterns □
ComplaintResolutionAgent implementation (4 hours) □ Professional
complaint handling □ Service recovery patterns □ AnxietyReliefAgent
implementation (4 hours) □ Reassurance for nervous customers □
First-time party host support □ WinbackAgent implementation (4 hours)
□ Retention strategies □ Re-engagement messaging □ AdminAssistantAgent
implementation (12 hours) □ Dashboard queries via natural language □
Report generation □ CRMWriterAgent implementation (8 hours) □
Auto-generate conversation summaries □ Extract key details for CRM □
KnowledgeSyncAgent implementation (4 hours) □ Keep knowledge base
updated □ Flag outdated information □ RAGRetrievalAgent implementation
(6 hours) □ Vector search setup □ Document chunking □ Relevance
scoring □ Tool calling setup (8 hours) □ AI creates bookings directly
□ AI updates customer info □ AI generates quotes □ RAG/Vector search
setup (6 hours) □ Pinecone/Qdrant integration □ Document embeddings □
Feedback collection (4 hours) □ Thumbs up/down UI □ Store feedback in
database

CUSTOMER REVIEW SYSTEM (From ENTERPRISE_FEATURES_ROADMAP.md) □ Review
Submission API (6-8 hours) □ POST /api/v1/reviews - Submit review □
GET /api/v1/reviews - List reviews (public) □ GET
/api/v1/reviews/{id} - Get review □ PUT /api/v1/reviews/{id} - Update
review (author only) □ DELETE /api/v1/reviews/{id} - Delete review □
Admin Moderation UI (4-6 hours) □ View pending reviews □
Approve/reject reviews □ Flag inappropriate content □ Edit reviews if
needed □ Customer Newsfeed (4-6 hours) □ Facebook-style feed □
Images + text □ Like/react capability (optional) □ Share capability □
Image Upload Service (2 hours) □ S3 or Cloudinary integration □ Image
resizing □ Multiple images per review □ Review Form Component (6-8
hours) □ Multi-step form □ Star rating (1-5) □ Text review □ Photo
upload □ Chef selection □ Chef Public Profile (4 hours) □ Display
reviews for chef □ Average rating □ Review count

MARKETING INTELLIGENCE (FULL Scope) □ Google Search Console API
integration □ Fetch performance data □ Get top queries □ Get top pages
□ Get indexing issues □ Display in dashboard

□ Google Ads API integration (FULL) □ Fetch campaign performance □
Fetch keyword performance □ Fetch location breakdown □ Fetch device
breakdown □ Fetch time analysis □ Fetch search terms report □ Budget
pacing tracking □ A/B test tracking □ Automated CPA alerts □ Display
all in dashboard

□ Google Analytics 4 API integration □ Fetch traffic data □ Fetch
conversion data □ Fetch user journey □ Display in dashboard

□ AI Marketing Recommendations □ OpenAI analyzes marketing data □
Generate actionable recommendations □ Priority scoring
(high/medium/low) □ Display in dashboard

REVIEW RESPONSE AI (NEW) □ Auto-draft responses to Google/Yelp reviews
□ Tone matching: professional, grateful, apologetic □ Human approval
before posting □ Response templates by rating (5-star, 4-star, 1-3
star)

SENTIMENT TREND ALERTS (NEW) □ Track sentiment across all customer
touchpoints □ Alert on negative trend (3+ negative in 24 hours) □
Weekly sentiment report □ Identify common complaint themes

CHURN PREDICTION (NEW) □ Identify at-risk customers (no booking in 6+
months) □ Score customers by churn probability □ Trigger winback
campaigns automatically □ Track winback success rate

REVIEW REQUEST AUTOMATION (NEW) □ Auto-request review after successful
event □ Timing: 2 hours post-event (while fresh) □ Only request if no
complaint detected □ Track review conversion rate □ A/B test review
request messaging
```

### Testing Checklist

```markdown
ADVANCED AI TESTS □ Emotion detection accuracy 85%+ □ Psychology
agents respond appropriately □ Tool calling creates bookings correctly
□ RAG retrieves relevant documents □ Feedback saves correctly

CUSTOMER REVIEW TESTS □ Submit review with images □ Admin can
approve/reject □ Newsfeed displays reviews □ Chef profile shows
reviews □ Average rating calculates correctly

MARKETING TESTS □ Search Console data displays □ Google Ads data
displays (all metrics) □ Analytics data displays □ AI recommendations
generate □ Alerts trigger correctly □ Budget pacing accurate
```

### Post-Deployment Checklist

```markdown
□ All new agents responding □ Emotion detection working □ Tool calling
functional □ Customer review submission working □ Admin moderation UI
functional □ Review newsfeed displaying □ Search Console dashboard
live □ Google Ads dashboard live (full metrics) □ Analytics dashboard
live □ AI recommendations generating □ Alerts working □ 48-hour
stability period
```

---

## 🟡 BATCH 6: AI Training & Scaling

### Pre-Development Checklist

```markdown
□ Batch 5 stable □ Create branch: feature/batch-6-ai-training □
Anthropic API key ready □ Grok/xAI API key ready □ Google Calendar API
configured □ Google Business Profile API configured
```

### Development Tasks

```markdown
MULTI-LLM DISCUSSION SYSTEM (3-Model Ensemble) □ GPT-4o provider
integration (Tier 1 - complex reasoning) □ Claude 3.5 provider
integration (Tier 2 - empathy, brand voice) □ Mistral Large 2 provider
integration (Tier 3 - cost-effective) □ Discussion orchestrator (16
hours) □ 3 rounds of debate (reduced from 4 - 3 models) □ Each LLM
generates response □ Cross-review and critique □ Final consensus □
Consensus engine (8 hours) □ Voting mechanism (majority of 3) □
Similarity matching □ Best response selection □ Knowledge base storage
□ Store discussions for learning □ Tag by topic/quality

MISTRAL INTEGRATION IN ENSEMBLE (FROM BATCH 3) □ Mistral Large 2 as
Tier 3 provider □ Full function calling support □ Contributes to
consensus voting □ Fallback when GPT-4o/Claude fail □ Cost-optimized
for simple queries

SHADOW LEARNING (From FUTURE_SCALING_PLAN.md) □ Shadow mode service
(12 hours) □ Run Llama in parallel (no customer exposure) □ Compare
outputs with production □ Teacher-student pair logging □ Store GPT-4
responses as "teacher" □ Store Llama responses as "student" □
Confidence scoring □ Calculate similarity scores □ Track improvement
over time □ Readiness calculation □ When is Llama ready for
production? □ 90%+ similarity threshold

TRAINING PIPELINE □ Data export service (8 hours) □ Export
conversations □ Export feedback □ Export corrections □ Data
cleaning/PII scrubbing □ Remove customer names □ Remove phone numbers
□ Remove addresses □ LoRA training configuration (16 hours) □
Configure for Llama 3 □ Set hyperparameters □ Training scripts
(Colab/Kaggle) □ Free GPU tier usage □ Training pipeline □ Model
evaluation suite □ Test trained model □ Compare with baseline

GPU MIGRATION PREPARATION (Batch 5-6 - PREPARE ONLY) ⚠️ DO NOT
PROVISION GPU SERVER YET - Just prepare architecture □ Document
single-server architecture specs:

- Provider options: Vast.ai, RunPod (compare pricing)
- Recommended: RTX 4090 (24GB VRAM) ~$223/mo
- RAM: 64-128GB, CPU: 8-16 cores, Storage: 200GB+ NVMe □ Create
  deployment scripts for unified server (ready to run later) □ Prepare
  PostgreSQL + Redis + Ollama + FastAPI docker-compose □ Document
  migration checklist from VPS to GPU server □ Keep current VPS
  running until shadow learning reaches 50K pairs □ GPU migration
  target: When company revenue supports ~$250/mo extra □ Fallback:
  Always maintain API-based LLM access (OpenAI, Mistral)

FREE-TIER FINE-TUNING STRATEGY (Post Batch 6) ⚠️ START WITH FREE
OPTIONS before investing in GPU □ Phase A: Use FREE GPU tiers for LoRA
training:

- Kaggle Notebooks (30 hrs/week GPU - P100 or T4x2)
- Google Colab (free tier with T4 GPU, limited sessions)
- Hugging Face ZeroGPU (H200, free for Pro users @ $9/mo)
- YOUR LAPTOP (for smaller models like Phi-4 14B quantized) □ Phase B:
  Training Data Requirements:
- 50,000+ teacher-student pairs collected via shadow learning
- Use Qwen3 32B or DeepSeek R1 as base model
- LoRA adapter training (not full fine-tuning)
- Target: 90%+ similarity to GPT-4 responses □ Phase C: Free Tier
  Workflow:

1. Export cleaned training data (PII removed)
2. Upload to Kaggle dataset
3. Run LoRA training in Kaggle notebook (or laptop for small models)
4. Download adapter weights
5. Test locally with Ollama on laptop
6. If 90%+ accuracy → deploy to VPS □ Phase D: When to Upgrade to Paid
   GPU:

- API costs exceed $300/month (break-even point)
- Free tier too slow for iteration
- Training dataset exceeds 100K pairs
- Company revenue supports $200-500/mo GPU budget

$300/MONTH API COST THRESHOLD RULE: ├─ If monthly API costs < $300 →
STAY ON API (OpenAI, Mistral) ├─ If monthly API costs > $300 →
Consider renting GPU (~$223/mo) └─ Savings = API costs - GPU rental =
profit!

LOCAL LAPTOP FINE-TUNING (FREE): □ Models that fit on consumer laptop
(16GB+ RAM):

- Phi-4 14B quantized (Q4) → ~8GB RAM
- Qwen3 8B → ~6GB RAM
- DeepSeek R1 7B → ~5GB RAM □ Use Ollama + OpenWebUI for testing □ Use
  Unsloth or PEFT library for LoRA training □ Export trained adapter →
  test on Kaggle/Colab for larger models

FREE GPU TIER SPECIFICATIONS: | Provider | GPU | Hours/Week | VRAM |
Best For | |----------|-----|------------|------|----------| | Kaggle
| P100/T4x2 | 30 hrs | 16GB | LoRA training | | Colab Free | T4 |
Limited | 16GB | Quick experiments | | HF ZeroGPU | H200 | Dynamic |
70GB | Inference testing | | Colab Pro | A100 | 100 units | 40GB |
Full training ($10/mo) |

TRAINING CHECKPOINT: □ If 90%+ accuracy achieved with free tier → STAY
ON FREE □ Only provision Vast.ai/RunPod when:

- Free tier insufficient for training volume
- Ready for 24/7 local inference (saves API costs)
- Company budget allows $200-300/mo GPU investment

LOYALTY PROGRAM (From LOYALTY_PROGRAM_EXPLANATION.md) □ Phase 1:
Points Engine (1-2 weeks) □ Database schema: loyalty_points,
loyalty_transactions □ Points earning rules (1 pt/$1 spent) □ Points
redemption (100 pts = $10 discount) □ Points balance API □ Transaction
history API □ Phase 1: Tier System (1 week) □ Bronze: 0 pts - Base
earning □ Silver: 500 pts - 1.5x points, priority booking □ Gold: 1000
pts - 2x points, free setup upgrade □ Platinum: 2500 pts - 3x points,
VIP chef access □ Tier upgrade/downgrade logic □ Tier benefits API □
Phase 1: Referral Program (1 week) □ Referral codes table □ Track
referred bookings □ Award points on successful referral □ Referral
dashboard

LOYALTY GAMIFICATION (NEW) □ Challenges: Book 3 parties in 6 months =
bonus points □ Badges: First Booking, 5th Booking, Referrer, etc. □
Streaks: Book every quarter = streak bonus □ Leaderboard (optional,
privacy-conscious)

BIRTHDAY/ANNIVERSARY REWARDS (NEW) □ Collect customer birthdays at
signup □ Collect anniversary dates (first booking) □ Auto-send special
offers 2 weeks before □ Birthday: 2x points on birthday month booking
□ Anniversary: Free appetizer upgrade

REFERRAL DASHBOARD (NEW) □ See who referred whom □ Track referral
conversion rate □ Referral revenue attribution □ Top referrer
leaderboard

DEMAND FORECASTING (NEW) □ Predict busy periods based on history □
Alerts: "Next Saturday expected 150% demand" □ Staff planning
recommendations □ Dynamic chef scheduling suggestions

READINESS DASHBOARD □ Confidence metrics UI (8 hours) □ Show AI
accuracy over time □ Show shadow learning progress □ Show training
data quality □ Agent management UI □ Enable/disable agents □ Adjust
agent parameters

GOOGLE INTEGRATIONS □ Calendar API - chef availability sync □ Two-way
sync with chef calendars □ Block unavailable times □ Create booking
events □ Calendar API - booking event creation □ Auto-create calendar
events □ Include customer details □ Include booking link □ Business
Profile - review monitoring □ Fetch new Google reviews □ Alert on
negative reviews □ Aggregate review data □ Business Profile -
auto-respond to reviews □ Template responses □ AI-generated responses
(optional) □ Business Profile - sync hours □ Update business hours □
Holiday hours
```

### Testing Checklist

```markdown
MULTI-LLM TESTS □ Discussion generates quality responses □ Consensus
reached in 4 rounds □ Knowledge base stores discussions □ Similarity
matching works

SHADOW LEARNING TESTS □ Teacher-student pairs logged □ Confidence
scores calculated □ Readiness dashboard displays correctly □ Shadow
mode doesn't affect production

LOYALTY PROGRAM TESTS □ Points earned on booking □ Points balance
displays correctly □ Tier progression works □ Referral codes generate
and track □ Points redemption works

TRAINING TESTS □ Data exports correctly □ PII removed from data □
Training config valid

GOOGLE INTEGRATION TESTS □ Calendar sync works both ways □ Booking
events created □ Reviews fetched □ Business hours updated
```

### Post-Deployment Checklist

```markdown
□ Multi-LLM discussions working □ Training data collecting □ Shadow
mode running (parallel, no customer exposure) □ Readiness dashboard
showing metrics □ Loyalty points engine functional □ Tier system
working □ Referral tracking active □ Google Calendar syncing □
Business Profile syncing □ 48-hour stability period
```

---

## 📊 Batch Completion Sign-Off Template

```markdown
# BATCH [X] COMPLETION SIGN-OFF

**Batch Name:** [Name] **Completion Date:** [Date] **Deployed By:**
[Name]

## Pre-Production Checklist

- [ ] All tests passed
- [ ] Security scan passed
- [ ] Load testing passed
- [ ] Documentation updated
- [ ] Manager approval: **\*\***\_**\*\*** Date: **\_\_\_**

## Production Deployment

- [ ] Deployed to production at: [timestamp]
- [ ] Health checks verified
- [ ] Manual testing completed
- [ ] 48/72 hour stability verified

## Sign-Off

- [ ] Technical Lead: **\*\***\_**\*\*** Date: **\_\_\_**
- [ ] Project Manager: **\*\***\_**\*\*** Date: **\_\_\_**
- [ ] Product Owner: **\*\***\_**\*\*** Date: **\_\_\_**

## Notes

[Any issues, learnings, or notes for next batch]
```

---

**Document Status:** ✅ READY **Next Action:** Use these checklists
during batch implementation
