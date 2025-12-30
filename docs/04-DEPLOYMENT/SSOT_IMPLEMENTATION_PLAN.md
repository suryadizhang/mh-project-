# Single Source of Truth (SSoT) Implementation Plan

**Created:** December 27, 2025
**Version:** 1.0.0
**Status:** APPROVED - Ready for Implementation
**Spec File:** `.github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md`

---

## User Decisions (December 27, 2025)

| Decision | User Choice | Rationale |
|----------|-------------|-----------|
| **AI Fallback Behavior** | B) Collect info first, THEN escalate | Better UX - gather context before handoff |
| **Akaunting Structure** | Separate company per station | Multi-station tax compliance, clean P&L |
| **Newsletter Template Editor** | A) Simple markdown editor | Faster development, easier maintenance |
| **Chef Payroll** | A) Akaunting vendors | Leverage existing accounting system |
| **FAQ Edit Permissions** | C) Customer Support can suggest (approval required) | Quality control with contribution |

---

## Implementation Phases Overview

| Phase | Focus | Target Batch | Effort | Priority | Dependencies |
|-------|-------|--------------|--------|----------|--------------|
| **1** | AI Critical Fixes | 1.x | 4-6 hrs | CRITICAL | None |
| **2** | Legal Documents | 1.x | 3-4 hrs | CRITICAL | Phase 1 |
| **3** | FAQ System | 1.x | 4-6 hrs | HIGH | Phase 1 |
| **4** | UI Text Centralization | 1.x | 2-3 hrs | HIGH | Phase 1 |
| **5** | Akaunting Integration | 2 | 8-10 hrs | MEDIUM | Batch 2 start |
| **6** | Newsletter System | 3-4 | 6-8 hrs | LOWER | Batch 3 start |

---

## Phase 1: AI Critical Fixes (Batch 1.x)

**Priority:** CRITICAL
**Effort:** 4-6 hours
**Dependencies:** None

### 1.1 Remove Hardcoded Pricing from AI

**Problem:** `apps/backend/src/config/ai_booking_config.py` has hardcoded `PRICING` dict at lines 63-86 that can cause AI to quote wrong prices.

**Files to Modify:**
- `apps/backend/src/config/ai_booking_config.py` - Remove PRICING dict
- `apps/backend/src/config/ai_booking_config_v2.py` - Remove TypedDict with hardcoded values
- `apps/backend/src/api/ai/orchestrator/tools/pricing_tool.py` - Use get_business_config() only

**Tasks:**
```markdown
[ ] 1.1.1 Audit ai_booking_config.py for all hardcoded values
[ ] 1.1.2 Remove PRICING dict (lines 63-86)
[ ] 1.1.3 Update all references to use get_business_config()
[ ] 1.1.4 Audit ai_booking_config_v2.py for hardcoded TypedDicts
[ ] 1.1.5 Verify pricing_tool.py uses live database values
[ ] 1.1.6 Test AI quote calculation with live config
```

### 1.2 Graceful Degradation Protocol (Collect First, Then Escalate)

**Pattern:** When pricing API unavailable, AI should:
1. Collect customer info (name, phone, email, event details)
2. Politely explain technical difficulty
3. Escalate with full context to human agent
4. NEVER quote fallback/cached prices

**Files to Create/Modify:**
- `apps/backend/src/api/ai/orchestrator/tools/pricing_tool.py`
- `apps/backend/src/api/ai/orchestrator/tools/policy_tool.py`
- `apps/backend/src/api/ai/orchestrator/tools/faq_tool.py`
- `apps/backend/src/api/ai/graceful_degradation.py` (NEW)

**Tasks:**
```markdown
[ ] 1.2.1 Create graceful_degradation.py with escalation templates
[ ] 1.2.2 Implement collect-first pattern in pricing_tool error handler:
      - Try to get pricing
      - On failure: Ask for name, phone, event details
      - Format: "I'd love to give you an exact quote! I'm having a small technical hiccup..."
      - Escalate with collected context
[ ] 1.2.3 Add policy_tool graceful degradation
[ ] 1.2.4 Add faq_tool graceful degradation
[ ] 1.2.5 Create escalation message templates for each failure mode
[ ] 1.2.6 Log all degradation events for monitoring
```

**Escalation Template Example:**
```python
GRACEFUL_DEGRADATION = {
    "pricing_unavailable": {
        "collect_first_message": (
            "I'd love to give you an exact quote! I'm having a small "
            "technical hiccup accessing our current pricing. While I "
            "get our team to help, could you share your name and the "
            "best phone number to reach you? 📞"
        ),
        "handoff_message": (
            "Thank you, {name}! I've connected you with our booking "
            "team who will call you at {phone} within the next 30 "
            "minutes with accurate pricing. They have all the details "
            "about your event! 🎉"
        ),
        "action": "escalate_to_human",
        "priority": "high",
        "include_context": ["name", "phone", "event_date", "guest_count", "venue"]
    }
}
```

### 1.3 AI Health Monitoring

**Tasks:**
```markdown
[ ] 1.3.1 Add AI config validation on FastAPI startup
[ ] 1.3.2 Log warnings if dynamic_variables table missing values
[ ] 1.3.3 Create admin dashboard indicator: AI health status
[ ] 1.3.4 Alert if AI escalation rate exceeds 10% of conversations
[ ] 1.3.5 Add Prometheus metrics for AI degradation events
```

### 1.4 Phase 1 Testing

```markdown
[ ] 1.4.1 Unit test: pricing_tool without DB returns graceful escalation
[ ] 1.4.2 Unit test: escalation includes all collected customer info
[ ] 1.4.3 Integration test: Full graceful degradation flow
[ ] 1.4.4 Integration test: AI uses live pricing from get_business_config()
[ ] 1.4.5 Manual test: Simulate DB outage, verify graceful behavior
```

### 1.5 Phase 1 Acceptance Criteria

- [ ] AI NEVER quotes hardcoded prices
- [ ] When pricing unavailable, AI collects customer info first
- [ ] Escalation includes full context (name, phone, event details)
- [ ] AI health status visible in admin dashboard
- [ ] All Phase 1 tests passing

---

## Phase 2: Legal Documents Template System (Batch 1.x)

**Priority:** CRITICAL
**Effort:** 3-4 hours
**Dependencies:** Phase 1 complete

### 2.1 Database Schema

**Migration File:** `database/migrations/YYYYMMDDHHMMSS_legal_documents.sql`

```sql
-- Legal documents with template variables
CREATE TABLE IF NOT EXISTS public.legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL UNIQUE,  -- 'terms', 'privacy', 'liability'
    title VARCHAR(200) NOT NULL,
    content_template TEXT NOT NULL,  -- Markdown with {{variable}} placeholders
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    variable_refs TEXT[],  -- List of variables used in template
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id)
);

-- Version history for compliance
CREATE TABLE IF NOT EXISTS public.legal_document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.legal_documents(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    content_template TEXT NOT NULL,
    changed_by UUID REFERENCES identity.users(id),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_legal_documents_type ON public.legal_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_legal_versions_document ON public.legal_document_versions(document_id);
```

**Tasks:**
```markdown
[ ] 2.1.1 Create migration file
[ ] 2.1.2 Run migration on staging
[ ] 2.1.3 Seed initial legal documents with templates
[ ] 2.1.4 Verify migration on staging for 24 hours
```

### 2.2 Backend Service

**File:** `apps/backend/src/services/legal_service.py`

**Tasks:**
```markdown
[ ] 2.2.1 Create LegalService class
[ ] 2.2.2 Implement get_rendered_document(document_type) method:
      - Fetch document from database
      - Fetch current business config
      - Replace {{variable}} placeholders with values
      - Return rendered content with metadata
[ ] 2.2.3 Implement version tracking for compliance
[ ] 2.2.4 Add caching (1 hour TTL, invalidate on config change)
```

**API Endpoint:** `GET /api/v1/legal/{document_type}`

**Response:**
```json
{
  "title": "Terms of Service",
  "content": "... rendered markdown with values ...",
  "version": "1.2",
  "effective_date": "2025-01-01",
  "rendered_at": "2025-12-27T10:30:00Z",
  "values_used": {
    "deposit_amount": "$100",
    "refund_days": "7"
  }
}
```

### 2.3 Frontend Integration

**Files to Modify:**
- `apps/customer/src/app/terms/page.tsx`
- `apps/customer/src/app/privacy/page.tsx` (if exists)
- `apps/customer/src/hooks/useLegal.ts` (NEW)

**Tasks:**
```markdown
[ ] 2.3.1 Create useLegal() hook for fetching legal documents
[ ] 2.3.2 Update terms/page.tsx:
      - Remove hardcoded "$100 deposit" (lines 111, 131, 135, 147)
      - Fetch from /api/v1/legal/terms
      - Render markdown content
      - Show loading state
[ ] 2.3.3 Update privacy page similarly
[ ] 2.3.4 Add error handling for API failure
```

### 2.4 Admin UI

**File:** `apps/admin/src/app/legal/page.tsx` (NEW)

**Tasks:**
```markdown
[ ] 2.4.1 Create legal document management page
[ ] 2.4.2 Markdown editor with preview
[ ] 2.4.3 Variable picker dropdown (insert {{variable}})
[ ] 2.4.4 Version history viewer
[ ] 2.4.5 Publish/unpublish toggle
[ ] 2.4.6 Super Admin only access
```

### 2.5 Phase 2 Testing

```markdown
[ ] 2.5.1 Unit test: Template rendering with all variables
[ ] 2.5.2 Unit test: Version history creation on update
[ ] 2.5.3 Integration test: API returns rendered document
[ ] 2.5.4 E2E test: Terms page displays dynamic content
[ ] 2.5.5 Manual test: Admin can edit and publish
```

### 2.6 Phase 2 Acceptance Criteria

- [ ] No hardcoded prices in legal documents
- [ ] Legal documents fetch from API with current values
- [ ] Version history tracks all changes
- [ ] Admin can edit documents via UI
- [ ] All Phase 2 tests passing

---

## Phase 3: FAQ System with Approval Workflow (Batch 1.x)

**Priority:** HIGH
**Effort:** 4-6 hours
**Dependencies:** Phase 1 complete

### 3.1 Database Schema

**Migration File:** `database/migrations/YYYYMMDDHHMMSS_faq_system.sql`

```sql
-- FAQ items with template answers
CREATE TABLE IF NOT EXISTS public.faq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer_template TEXT NOT NULL,  -- Contains {{variable}} placeholders
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    variable_refs TEXT[],  -- List of variables used in answer
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id)
);

-- FAQ edit suggestions (Customer Support workflow)
CREATE TABLE IF NOT EXISTS public.faq_edit_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_id UUID REFERENCES public.faq_items(id) ON DELETE SET NULL,  -- null for new FAQ
    suggested_question TEXT NOT NULL,
    suggested_answer TEXT NOT NULL,
    suggestion_type VARCHAR(20) NOT NULL CHECK (suggestion_type IN ('new', 'edit', 'delete')),
    suggested_by UUID NOT NULL REFERENCES identity.users(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES identity.users(id),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_faq_items_category ON public.faq_items(category);
CREATE INDEX IF NOT EXISTS idx_faq_items_active ON public.faq_items(is_active);
CREATE INDEX IF NOT EXISTS idx_faq_suggestions_status ON public.faq_edit_suggestions(status);
```

**Tasks:**
```markdown
[ ] 3.1.1 Create migration file
[ ] 3.1.2 Run migration on staging
[ ] 3.1.3 Migrate existing FAQ data from faqsData.ts to database
[ ] 3.1.4 Convert hardcoded values to {{variable}} templates
```

### 3.2 Permission Model (Per User Decision)

| Role | Permissions |
|------|-------------|
| **Super Admin** | Full CRUD, approve/reject suggestions |
| **Admin** | Full CRUD, approve/reject suggestions |
| **Customer Support** | View FAQs, suggest edits (requires approval) |
| **Public** | Read-only active FAQs |

### 3.3 Backend Service

**File:** `apps/backend/src/services/faq_service.py`

**Tasks:**
```markdown
[ ] 3.3.1 Create FAQService class
[ ] 3.3.2 Implement get_rendered_faqs(category=None):
      - Fetch active FAQs from database
      - Inject current values from get_business_config()
      - Return rendered answers
[ ] 3.3.3 Implement CRUD operations (Admin/Super Admin)
[ ] 3.3.4 Implement suggest_edit(faq_id, suggestion, user) - Customer Support
[ ] 3.3.5 Implement approve_suggestion(suggestion_id, admin) - Admin
[ ] 3.3.6 Implement reject_suggestion(suggestion_id, admin, notes) - Admin
[ ] 3.3.7 Add caching (15 min TTL)
```

**API Endpoints:**
```markdown
GET  /api/v1/faqs                              - Public, rendered with values
GET  /api/v1/faqs?category=Pricing             - Filter by category
POST /api/v1/admin/faqs                        - Create FAQ (Admin only)
PUT  /api/v1/admin/faqs/{id}                   - Update FAQ (Admin only)
DELETE /api/v1/admin/faqs/{id}                 - Delete FAQ (Admin only)
POST /api/v1/admin/faqs/suggest                - Suggest edit (Customer Support)
GET  /api/v1/admin/faqs/suggestions            - List pending (Admin)
POST /api/v1/admin/faqs/suggestions/{id}/approve - Approve (Admin)
POST /api/v1/admin/faqs/suggestions/{id}/reject  - Reject (Admin)
```

### 3.4 Frontend - Customer Site

**Files to Modify:**
- `apps/customer/src/lib/data/faqsData.ts` - Mark as deprecated
- `apps/customer/src/hooks/useFaqs.ts` (NEW)
- `apps/customer/src/components/FAQ/*.tsx`

**Tasks:**
```markdown
[ ] 3.4.1 Create useFaqs() hook:
      - Fetch from /api/v1/faqs
      - Cache with React Query
      - Support category filtering
[ ] 3.4.2 Update FAQ components to use hook instead of faqsData.ts
[ ] 3.4.3 Add loading skeletons
[ ] 3.4.4 Deprecate faqsData.ts with warning comment
```

### 3.5 Frontend - Admin Panel

**File:** `apps/admin/src/app/faqs/page.tsx` (NEW)

**Tasks:**
```markdown
[ ] 3.5.1 Create FAQ management page with table
[ ] 3.5.2 FAQ Editor with markdown preview
[ ] 3.5.3 Variable picker dropdown
[ ] 3.5.4 Category management
[ ] 3.5.5 Suggestions queue tab:
      - List pending suggestions
      - Preview suggested changes
      - Approve/Reject buttons with notes
[ ] 3.5.6 Customer Support sees "Suggest Edit" instead of "Edit"
[ ] 3.5.7 Admin sees direct "Edit" button
```

### 3.6 Phase 3 Testing

```markdown
[ ] 3.6.1 Unit test: Template rendering with variables
[ ] 3.6.2 Unit test: Suggestion workflow (create, approve, reject)
[ ] 3.6.3 Integration test: Public API returns rendered FAQs
[ ] 3.6.4 Integration test: Permission checks enforced
[ ] 3.6.5 E2E test: Customer sees dynamic FAQ content
[ ] 3.6.6 E2E test: Customer Support can suggest, Admin approves
```

### 3.7 Phase 3 Acceptance Criteria

- [ ] FAQs stored in database with templates
- [ ] FAQ answers render with current pricing values
- [ ] Customer Support can suggest edits
- [ ] Admin can approve/reject suggestions
- [ ] Customer site displays dynamic FAQs
- [ ] All Phase 3 tests passing

---

## Phase 4: UI Text Centralization (Batch 1.x)

**Priority:** HIGH
**Effort:** 2-3 hrs
**Dependencies:** Phase 1 complete

### 4.1 Create Config Hooks

**File:** `apps/customer/src/hooks/useConfig.ts`

```typescript
interface ConfigBundle {
  pricing: {
    adultPrice: number;
    childPrice: number;
    partyMinimum: number;
    depositAmount: number;
  };
  travel: {
    freeMiles: number;
    perMileRate: number;
  };
  policies: {
    advanceBookingHours: number;
    refundDays: number;
    rescheduleAllowed: boolean;
  };
  guestLimits: {
    minimum: number;
    maximum: number;
    minimumForHibachi: number;
  };
  isLoading: boolean;
  error: Error | null;
}
```

**Tasks:**
```markdown
[ ] 4.1.1 Create useConfig() hook (complete config bundle)
[ ] 4.1.2 Create usePolicies() hook (formatted policy text)
[ ] 4.1.3 Verify usePricing() returns all pricing values
[ ] 4.1.4 Add proper TypeScript types
```

### 4.2 Backend Endpoint

**API:** `GET /api/v1/config/all`

**Tasks:**
```markdown
[ ] 4.2.1 Create config router
[ ] 4.2.2 Return complete config bundle:
      - pricing, travel, policies, guest_limits, contact_info
[ ] 4.2.3 Add 5-minute cache with ETag support
[ ] 4.2.4 Include cache-control headers
```

### 4.3 Refactor Hardcoded Values

**Files to Fix:**
```markdown
[ ] 4.3.1 baseLocationUtils.ts lines 91, 93 - Use travel config
[ ] 4.3.2 guestCountSchema.ts - Use dynamic guest limits
[ ] 4.3.3 All validation schemas - Use dynamic limits
[ ] 4.3.4 Footer contact info - Use business config
[ ] 4.3.5 Any remaining hardcoded values from audit
```

### 4.4 Phase 4 Testing

```markdown
[ ] 4.4.1 Unit test: useConfig() returns all values
[ ] 4.4.2 Integration test: /api/v1/config/all endpoint
[ ] 4.4.3 E2E test: UI displays dynamic values
```

### 4.5 Phase 4 Acceptance Criteria

- [ ] All UI text uses dynamic values from hooks
- [ ] Config endpoint returns complete bundle
- [ ] No hardcoded business values in frontend
- [ ] All Phase 4 tests passing

---

## Phase 5: Akaunting Integration (Batch 2)

**Priority:** MEDIUM
**Effort:** 8-10 hrs
**Dependencies:** Batch 2 start, Docker ready

### 5.1 Multi-Station Company Structure (Per User Decision)

**Architecture:** Separate Akaunting company per station

| Station | Akaunting Company | Tax Settings |
|---------|-------------------|--------------|
| CA-FREMONT-001 | My Hibachi - Fremont | CA state tax |
| CA-SANJOSE-001 | My Hibachi - San Jose | CA state tax |
| TX-DALLAS-001 | My Hibachi - Dallas | TX state tax |

**Rationale:**
- Clean P&L per location
- Proper tax compliance per jurisdiction
- Independent financial reporting
- Easier multi-owner expansion

### 5.2 Deployment Tasks

```markdown
[ ] 5.2.1 Configure Cloudflare tunnel for accounting.mysticdatanode.net
[ ] 5.2.2 Run docker/akaunting/install.sh
[ ] 5.2.3 Create initial company for Fremont station
[ ] 5.2.4 Configure tax settings for California
[ ] 5.2.5 Set up Chart of Accounts for catering business
[ ] 5.2.6 Create admin user for accounting access
```

### 5.3 Sync Services

**Files to Create:**
- `apps/backend/src/services/akaunting/akaunting_client.py` - HTTP client
- `apps/backend/src/services/akaunting/invoice_sync_service.py` - Booking → Invoice
- `apps/backend/src/services/akaunting/payment_sync_service.py` - Stripe → Akaunting
- `apps/backend/src/services/akaunting/vendor_sync_service.py` - Chef → Vendor

**Tasks:**
```markdown
[ ] 5.3.1 Create AkauntingClient with API authentication
[ ] 5.3.2 Implement invoice creation on booking completion
[ ] 5.3.3 Implement payment recording from Stripe webhooks
[ ] 5.3.4 Implement chef as vendor (for payroll tracking)
[ ] 5.3.5 Add station_id to company mapping
```

### 5.4 Chef Payroll via Akaunting Vendors (Per User Decision)

**Pattern:** Each chef is an Akaunting Vendor

```markdown
[ ] 5.4.1 Create vendor record when chef onboarded
[ ] 5.4.2 Create bill for each completed booking:
      - Base pay per event
      - Travel reimbursement (if applicable)
      - Tips collected
[ ] 5.4.3 Generate payroll summary report
[ ] 5.4.4 Admin UI: Chef payment history
```

### 5.5 Phase 5 Testing

```markdown
[ ] 5.5.1 Integration test: Booking creates Akaunting invoice
[ ] 5.5.2 Integration test: Stripe payment recorded in Akaunting
[ ] 5.5.3 Integration test: Chef vendor and bill creation
[ ] 5.5.4 Manual test: Verify reports match Stripe data
```

### 5.6 Phase 5 Acceptance Criteria

- [ ] Akaunting deployed at accounting.mysticdatanode.net
- [ ] Bookings sync to invoices automatically
- [ ] Stripe payments recorded in Akaunting
- [ ] Chefs tracked as vendors with payroll
- [ ] Multi-station company structure working
- [ ] All Phase 5 tests passing

---

## Phase 6: Newsletter System (Batch 3-4)

**Priority:** LOWER
**Effort:** 6-8 hrs
**Dependencies:** Batch 3 start

### 6.1 Newsletter Configuration Table

```sql
CREATE TABLE IF NOT EXISTS public.newsletter_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES identity.users(id)
);

-- Seed default config
INSERT INTO newsletter_config (key, value, description) VALUES
('sender_email', '"newsletter@myhibachichef.com"', 'From email address'),
('sender_name', '"My Hibachi Chef"', 'Display name for sender'),
('reply_to', '"info@myhibachichef.com"', 'Reply-to address'),
('daily_limit', '1000', 'Maximum emails per day'),
('batch_size', '50', 'Emails per batch'),
('batch_delay_seconds', '60', 'Delay between batches'),
('unsubscribe_grace_days', '30', 'Days before re-subscribe allowed');
```

### 6.2 Email Template System (Simple Markdown - Per User Decision)

**Tasks:**
```markdown
[ ] 6.2.1 Create email_templates table with markdown content
[ ] 6.2.2 Implement markdown-to-HTML renderer
[ ] 6.2.3 Variable injection ({{customer_name}}, {{booking_date}}, etc.)
[ ] 6.2.4 Preview endpoint for admin
[ ] 6.2.5 Admin UI: Simple markdown editor with preview
```

### 6.3 Admin Newsletter UI

**Tasks:**
```markdown
[ ] 6.3.1 Complete subscribers list (currently "Coming soon...")
[ ] 6.3.2 Complete segments management
[ ] 6.3.3 Complete templates editor (simple markdown)
[ ] 6.3.4 Campaign creation and scheduling
[ ] 6.3.5 Send preview to admin email
[ ] 6.3.6 Campaign analytics (sent, opened, clicked)
```

### 6.4 Phase 6 Acceptance Criteria

- [ ] All newsletter settings admin-configurable
- [ ] Simple markdown template editor working
- [ ] Campaign creation and sending functional
- [ ] All Phase 6 tests passing

---

## Risk Mitigation

### Database Migration Risks

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Full backup before each migration |
| Downtime | Run migrations during low-traffic hours |
| Rollback needed | Prepare rollback SQL scripts for each migration |

### AI Degradation Risks

| Risk | Mitigation |
|------|------------|
| DB outage affects AI | Graceful degradation with collect-first pattern |
| Wrong prices quoted | Remove ALL hardcoded values, no fallbacks |
| Customer frustrated | Polite messaging, quick escalation to human |

### Integration Risks

| Risk | Mitigation |
|------|------------|
| Akaunting API changes | Version lock Akaunting Docker image |
| Stripe webhook issues | Idempotency keys, retry logic |
| Config cache stale | Cache invalidation on admin update |

---

## Rollback Plan

### Phase 1 Rollback
- Revert ai_booking_config.py changes
- Restore hardcoded PRICING dict (not ideal but functional)

### Phase 2 Rollback
- Revert frontend to static terms page
- Keep database tables (no data loss)

### Phase 3 Rollback
- Revert frontend to faqsData.ts
- Keep database tables for future migration

### Phase 5 Rollback
- Stop Akaunting containers
- Disable sync services
- Manual invoice creation as fallback

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| AI pricing accuracy | 100% | No fallback prices quoted |
| AI escalation rate | <10% | Monitor escalation events |
| Legal document freshness | Real-time | Values match database |
| FAQ update time | <1 hour | Time from admin edit to live |
| Config propagation | <5 min | Cache TTL verification |

---

## Related Documentation

- [20-SINGLE_SOURCE_OF_TRUTH.instructions.md](../../.github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md) - Full SSoT specification
- [BATCH_CHECKLISTS.md](./BATCH_CHECKLISTS.md) - Batch deployment checklists
- [CURRENT_BATCH_STATUS.md](../../CURRENT_BATCH_STATUS.md) - Current batch progress
- [business_config_service.py](../../apps/backend/src/services/business_config_service.py) - Config service implementation

---

**Document Status:** APPROVED
**Next Action:** Start Phase 1 implementation
