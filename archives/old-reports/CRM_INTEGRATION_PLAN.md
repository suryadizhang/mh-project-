# AI Sales CRM Integration Plan - MH Project

## 🎯 Executive Summary

Integration of AI Sales CRM into existing MyHibachi project using:

- **2 APIs**: Existing Backend API (enhanced) + AI API
- **1 Database**: PostgreSQL with schema separation
- **CRM Panel**: Integrated into existing Admin app
- **AI Booking**: Safe command-based booking creation

## 🏗️ Architecture Overview

```
Customer App (Next.js) ─────┐
Admin App (Next.js + CRM) ──┤ ──→ Backend API (FastAPI)
RingCentral/Chat Widget ────┤     ├── Identity (OAuth 2.1 + MFA)
                             │     ├── Commands (CQRS Write)
                             │     ├── Queries (CQRS Read)
AI API (FastAPI) ────────────┘     ├── Integrations (RC/Stripe/Plaid)
                                   └── Automation (Journeys)
                                          │
                                   PostgreSQL (1 DB)
                                   ├── core (customers, bookings, chefs)
                                   ├── events (domain_events, outbox)
                                   ├── integra (payment_events, matches)
                                   └── read (projections, materialized views)
```

## 📁 Folder Structure Changes

### Current Structure (KEEP)

```
apps/
├── api/        # FastAPI backend (ENHANCE)
├── customer/   # Next.js customer app (KEEP)
├── admin/      # Next.js admin app (ADD CRM FEATURES)
└── ai-api/     # AI orchestrator (ENHANCE)
```

### Enhanced Backend API (apps/api/app/)

```
app/
├── main.py                    # EXISTING (add CRM routes)
├── config.py                  # EXISTING (add CRM settings)
├── database.py               # EXISTING (add schema separation)
│
├── identity/                  # NEW - OAuth 2.1 + OIDC + MFA
│   ├── __init__.py
│   ├── auth.py               # OIDC providers, JWT validation
│   ├── models.py             # Users, roles, sessions
│   ├── router.py             # /auth endpoints
│   └── rbac.py               # Role-based access control
│
├── commands/                  # NEW - CQRS Write Side
│   ├── __init__.py
│   ├── base.py               # Command base class
│   ├── booking.py            # CreateBooking, UpdateBooking, etc.
│   ├── customer.py           # CreateLead, UpdateConsent
│   ├── payment.py            # LinkPaymentToBooking, MarkPaid
│   └── router.py             # POST /commands/* endpoints
│
├── queries/                   # NEW - CQRS Read Side
│   ├── __init__.py
│   ├── inbox.py              # GetInbox, GetThreads
│   ├── payments.py           # GetPaymentsFeed
│   ├── schedule.py           # GetScheduleBoard
│   ├── customer.py           # GetCustomer360
│   └── router.py             # GET /queries/* endpoints
│
├── events/                    # NEW - Event Sourcing
│   ├── __init__.py
│   ├── base.py               # DomainEvent base class
│   ├── booking.py            # BookingCreated, BookingUpdated
│   ├── customer.py           # LeadCreated, ConsentUpdated
│   ├── payment.py            # PaymentReceived, PaymentMatched
│   └── store.py              # Event persistence
│
├── projectors/                # NEW - Read Model Updates
│   ├── __init__.py
│   ├── inbox.py              # Update inbox_threads
│   ├── payments.py           # Update payments_feed
│   ├── schedule.py           # Update schedule_board
│   └── customer.py           # Update customer_360
│
├── integrations/              # NEW - External APIs
│   ├── ringcentral/
│   │   ├── webhook.py        # Inbound SMS/calls
│   │   ├── sender.py         # Outbound with rate limits
│   │   └── router.py         # /webhooks/ringcentral
│   ├── stripe/
│   │   ├── webhook.py        # Payment events
│   │   ├── checkout.py       # Hosted checkout links
│   │   └── router.py         # /webhooks/stripe
│   ├── plaid/
│   │   ├── sync.py           # Bank transaction sync
│   │   └── matching.py       # Payment matching engine
│   └── google/
│       ├── calendar.py       # Multi-chef scheduling
│       └── webhook.py        # Calendar change events
│
├── automation/                # NEW - Journey Engine
│   ├── __init__.py
│   ├── engine.py             # YAML journey executor
│   ├── jobs.py               # Background tasks
│   └── workflows/            # Journey definitions
│
└── models/                    # EXISTING (add new tables)
    ├── core/                 # Customer, booking, chef tables
    ├── events/               # domain_events, outbox, inbox
    ├── integra/              # payment_events, matches
    └── read/                 # Projection tables
```

## 🗄️ Database Schema Design

### Schema Separation (One PostgreSQL DB)

```sql
-- Core business entities
CREATE SCHEMA core;
CREATE TABLE core.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email_encrypted TEXT NOT NULL, -- AES-GCM encrypted
    phone_encrypted TEXT NOT NULL, -- AES-GCM encrypted
    consent_sms BOOLEAN NOT NULL DEFAULT FALSE,
    consent_email BOOLEAN NOT NULL DEFAULT FALSE,
    timezone TEXT DEFAULT 'America/Los_Angeles',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE(email_encrypted) WHERE deleted_at IS NULL
);

CREATE TABLE core.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES core.customers(id),
    date DATE NOT NULL,
    slot TIME NOT NULL,
    address_encrypted TEXT NOT NULL, -- AES-GCM encrypted
    zone TEXT NOT NULL,
    chef_id UUID REFERENCES core.chefs(id),
    status booking_status NOT NULL DEFAULT 'new',
    party_adults INTEGER NOT NULL CHECK (party_adults > 0),
    party_kids INTEGER NOT NULL DEFAULT 0,
    deposit_due_cents INTEGER NOT NULL CHECK (deposit_due_cents >= 0),
    total_due_cents INTEGER NOT NULL CHECK (total_due_cents >= deposit_due_cents),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT unique_chef_slot UNIQUE (chef_id, date, slot) WHERE chef_id IS NOT NULL AND deleted_at IS NULL
);

-- Event sourcing
CREATE SCHEMA events;
CREATE TABLE events.domain_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id UUID NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    version INTEGER NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE events.outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events.domain_events(id),
    target TEXT NOT NULL, -- 'ringcentral', 'stripe', 'email'
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status outbox_status NOT NULL DEFAULT 'pending',
    error TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Integration data
CREATE SCHEMA integra;
CREATE TABLE integra.payment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider payment_provider NOT NULL,
    provider_id TEXT NOT NULL,
    method payment_method NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    occurred_at TIMESTAMPTZ NOT NULL,
    memo TEXT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(provider, provider_id)
);

-- Read projections
CREATE SCHEMA read;
CREATE MATERIALIZED VIEW read.inbox_threads AS
SELECT
    t.id as thread_id,
    t.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    t.channel,
    t.status,
    t.assigned_agent_id,
    t.last_message_at,
    t.ai_mode,
    COUNT(m.id) as message_count
FROM core.message_threads t
JOIN core.customers c ON c.id = t.customer_id
LEFT JOIN core.messages m ON m.thread_id = t.id
WHERE t.deleted_at IS NULL
GROUP BY t.id, t.customer_id, c.first_name, c.last_name, t.channel, t.status, t.assigned_agent_id, t.last_message_at, t.ai_mode;
```

## 🤖 AI Booking Integration

### AI Tools Implementation (apps/ai-api/)

```python
# ai-api/app/tools/booking.py
from typing import Dict, Any
import httpx
from uuid import uuid4

@tool("create_booking")
async def create_booking(
    customer_first_name: str,
    customer_last_name: str,
    customer_email: str,
    customer_phone: str,
    booking_date: str,  # YYYY-MM-DD
    booking_slot: str,  # HH:MM (18:00)
    address: str,
    party_adults: int,
    party_kids: int = 0,
    menu_items: List[Dict] = None,
    notes: str = None,
    consent_sms: bool = True,
    consent_email: bool = True
) -> Dict[str, Any]:
    """Create a new booking with customer information."""

    payload = {
        "source": "ai_chat",
        "customer": {
            "first_name": customer_first_name,
            "last_name": customer_last_name,
            "email": customer_email,
            "phone": customer_phone,
            "consent_sms": consent_sms,
            "consent_email": consent_email
        },
        "booking": {
            "date": booking_date,
            "slot": booking_slot,
            "address": address,
            "party": {
                "adults": party_adults,
                "kids": party_kids
            },
            "menu": menu_items or [],
            "notes": notes
        },
        "payment_preference": "stripe_checkout"
    }

    headers = {
        "Idempotency-Key": str(uuid4()),
        "Authorization": f"Bearer {await get_service_token()}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_API_URL}/commands/create-booking",
            json=payload,
            headers=headers,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()

@tool("check_availability")
async def check_availability(
    date: str,
    zone: str = None
) -> Dict[str, Any]:
    """Check available time slots for a date."""
    params = {"date": date}
    if zone:
        params["zone"] = zone

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_API_URL}/queries/availability",
            params=params,
            headers={"Authorization": f"Bearer {await get_service_token()}"}
        )
        response.raise_for_status()
        return response.json()
```

### Backend Command Implementation (apps/api/app/commands/)

```python
# api/app/commands/booking.py
from pydantic import BaseModel, validator
from typing import Optional, List, Dict
from uuid import UUID
import uuid

class CustomerData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    consent_sms: bool = True
    consent_email: bool = True

    @validator('email')
    def validate_email(cls, v):
        # Email validation logic
        return v.lower().strip()

    @validator('phone')
    def validate_phone(cls, v):
        # Normalize to E.164 format
        return normalize_phone(v)

class BookingData(BaseModel):
    date: str  # YYYY-MM-DD
    slot: str  # HH:MM
    address: str
    zone: Optional[str] = None
    party: Dict[str, int]  # {"adults": 11, "kids": 2}
    menu: List[Dict] = []
    notes: Optional[str] = None

class CreateBookingCommand(BaseModel):
    source: str
    customer: CustomerData
    booking: BookingData
    payment_preference: str = "stripe_checkout"
    channel_thread_id: Optional[str] = None
    metadata: Dict = {}

# Command handler
async def handle_create_booking(
    command: CreateBookingCommand,
    idempotency_key: str,
    user_id: UUID
) -> Dict[str, Any]:
    """Handle booking creation with full validation and event emission."""

    async with get_db_session() as session:
        # Start transaction
        async with session.begin():
            # 1. Find or create customer (encrypted fields)
            customer = await find_or_create_customer(
                session, command.customer
            )

            # 2. Validate availability
            availability = await check_slot_availability(
                session,
                command.booking.date,
                command.booking.slot,
                command.booking.zone
            )

            if not availability.available:
                raise BookingConflictError(
                    "Slot not available",
                    alternatives=availability.alternatives
                )

            # 3. Calculate pricing
            pricing = await calculate_booking_price(
                command.booking.party,
                command.booking.menu,
                command.booking.zone
            )

            # 4. Create booking
            booking = Booking(
                id=uuid.uuid4(),
                customer_id=customer.id,
                date=command.booking.date,
                slot=command.booking.slot,
                address_encrypted=encrypt_field(command.booking.address),
                zone=command.booking.zone or derive_zone(command.booking.address),
                party_adults=command.booking.party["adults"],
                party_kids=command.booking.party.get("kids", 0),
                deposit_due_cents=pricing.deposit_cents,
                total_due_cents=pricing.total_cents,
                notes=command.booking.notes,
                status=BookingStatus.DEPOSIT_PENDING
            )

            session.add(booking)
            await session.flush()  # Get booking.id

            # 5. Emit domain events
            events = [
                BookingCreatedEvent(
                    aggregate_id=booking.id,
                    booking_id=booking.id,
                    customer_id=customer.id,
                    date=booking.date,
                    slot=booking.slot,
                    total_cents=booking.total_due_cents,
                    source=command.source
                )
            ]

            if customer.is_new:
                events.append(
                    LeadCreatedEvent(
                        aggregate_id=customer.id,
                        customer_id=customer.id,
                        source=command.source,
                        channel=command.channel_thread_id
                    )
                )

            # 6. Persist events + outbox entries
            for event in events:
                await persist_domain_event(session, event)
                await create_outbox_entries(session, event, [
                    "stripe_checkout",  # Generate payment link
                    "email_confirmation"  # Send booking confirmation
                ])

            # 7. Return booking summary
            return {
                "booking_id": str(booking.id),
                "customer_id": str(customer.id),
                "status": booking.status.value,
                "summary": f"{booking.date} at {booking.slot} • {booking.party_adults + booking.party_kids} guests",
                "deposit_due": f"${booking.deposit_due_cents / 100:.2f}",
                "total_due": f"${booking.total_due_cents / 100:.2f}",
                "stripe_checkout_url": None  # Will be populated by outbox processor
            }
```

## 🎨 Admin Panel Integration

### Enhanced Admin App (apps/admin/src/pages/)

```typescript
// pages/crm/inbox/index.tsx - Unified Inbox
export default function InboxPage() {
  const { threads, loading } = useInboxThreads();
  const { sendMessage } = useSendMessage();

  return (
    <div className="grid grid-cols-4 h-screen">
      {/* Thread List */}
      <div className="col-span-1 border-r">
        <ThreadList
          threads={threads}
          loading={loading}
          onSelectThread={setActiveThread}
        />
      </div>

      {/* Conversation View */}
      <div className="col-span-2">
        <ConversationView
          thread={activeThread}
          onSendMessage={sendMessage}
          aiSuggestionsEnabled={true}
        />
      </div>

      {/* Customer Panel */}
      <div className="col-span-1 border-l">
        <CustomerPanel
          customerId={activeThread?.customer_id}
          showBookingActions={true}
        />
      </div>
    </div>
  );
}

// components/ConversationComposer.tsx
export function ConversationComposer({ onSend, aiSuggestion }) {
  const [message, setMessage] = useState("");
  const [sendAs, setSendAs] = useState<"ai" | "human">("ai");

  const handleSend = async () => {
    // Send command to Backend API (never direct DB)
    await fetch('/api/commands/send-message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': crypto.randomUUID()
      },
      body: JSON.stringify({
        thread_id: activeThread.id,
        content: message,
        sender_type: sendAs,
        sender_id: sendAs === "human" ? currentUser.id : "ai_system"
      })
    });

    setMessage("");
  };

  return (
    <div className="p-4 border-t">
      {aiSuggestion && (
        <div className="mb-2 p-2 bg-blue-50 rounded">
          <span className="text-sm text-blue-600">AI suggests:</span>
          <p className="text-blue-800">{aiSuggestion}</p>
          <button
            onClick={() => setMessage(aiSuggestion)}
            className="text-blue-600 text-sm underline"
          >
            Use this
          </button>
        </div>
      )}

      <div className="flex space-x-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 border rounded p-2"
          placeholder="Type your message..."
        />
        <div className="flex flex-col space-y-1">
          <button
            onClick={() => setSendAs("ai")}
            className={`px-3 py-1 rounded text-sm ${
              sendAs === "ai" ? "bg-blue-600 text-white" : "bg-gray-200"
            }`}
          >
            Send as AI
          </button>
          <button
            onClick={() => setSendAs("human")}
            className={`px-3 py-1 rounded text-sm ${
              sendAs === "human" ? "bg-green-600 text-white" : "bg-gray-200"
            }`}
          >
            Send as Me
          </button>
        </div>
        <button
          onClick={handleSend}
          disabled={!message.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

## 🚀 Implementation Steps

### Phase 1: Foundation (Week 1-2)

1. ✅ Add database schemas (core/events/integra/read)
2. ✅ Implement CQRS Command/Query structure
3. ✅ Add Identity module (OAuth 2.1 + MFA)
4. ✅ Create basic event sourcing pipeline

### Phase 2: AI Integration (Week 3-4)

5. ✅ Implement CreateBooking command with validation
6. ✅ Add AI tools that call Backend Commands
7. ✅ Test booking creation flow end-to-end
8. ✅ Add Stripe hosted checkout integration

### Phase 3: Admin Integration (Week 5-6)

9. ✅ Create CRM pages in Admin app
10. ✅ Implement unified inbox functionality
11. ✅ Add customer 360 and booking detail views
12. ✅ Connect real-time updates via projections

### Phase 4: External Integrations (Week 7-8)

13. ✅ RingCentral webhook integration
14. ✅ Plaid payment matching
15. ✅ Google Calendar multi-chef scheduling
16. ✅ Journey automation engine

## ✅ Success Criteria

- [ ] AI can create bookings via conversation
- [ ] All booking data appears in Admin CRM panel
- [ ] Payment links generated automatically
- [ ] TCPA consent tracking working
- [ ] Event sourcing audit trail complete
- [ ] P95 response times met (<150ms commands)

## 🔐 Security Checklist

- [ ] OAuth 2.1 + PKCE implemented
- [ ] MFA enforced for admin users
- [ ] Field-level encryption for PII
- [ ] Idempotency keys prevent duplicates
- [ ] PCI SAQ-A compliance verified
- [ ] GDPR DSAR endpoints functional
- [ ] Hash-chained audit log tamper-evident

---

**Next Action:** Begin Phase 1 implementation starting with database
schema creation and CQRS foundation.
