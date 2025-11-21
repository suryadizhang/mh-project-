# Legacy Models Consolidation Plan

## Current State Analysis

### Legacy Files to DELETE (13 files):

1. `legacy_base.py` - Old BaseModel
2. `legacy_declarative_base.py` - Duplicate Base
3. `legacy_booking_models.py` - Old booking structures
4. `legacy_core.py` - Customer, Booking, Payment, MessageThread,
   Message, Event
5. `legacy_encryption.py` - Crypto utilities (move to utils/)
6. `legacy_events.py` - DomainEvent, OutboxEntry, Snapshot, etc.
7. `legacy_feedback.py` - CustomerReview, DiscountCoupon,
   ReviewEscalation
8. `legacy_lead_newsletter.py` - Lead, Subscriber, Campaign models
9. `legacy_notification_groups.py` - NotificationGroup models
10. `legacy_qr_tracking.py` - QRCode, QRScan
11. `legacy_social.py` - Social media models
12. `legacy_stripe_models.py` - Stripe integration
13. `legacy_models_init.py` - Old **init**

### Canonical Models to KEEP/ENHANCE:

1. ✅ `base.py` - Single BaseModel (inherits from
   legacy_declarative_base.Base)
2. ✅ `booking.py` - Canonical Booking + Payment
3. ✅ `customer.py` - Canonical Customer
4. ✅ `user.py` - OAuth User (identity.users)
5. ✅ `role.py` - RBAC models
6. ✅ `station.py` - Station models
7. ✅ `review.py` - CustomerReview models
8. ✅ `escalation.py` - Escalation models
9. ✅ `call_recording.py` - CallRecording
10. ✅ `knowledge_base.py` - AI knowledge base
11. ✅ `lead.py` - Lead models (needs consolidation)
12. ✅ `business.py` - Business settings
13. ✅ `payment_notification.py` - Payment notifications
14. ✅ `system_event.py` - System events
15. ✅ `terms_acknowledgment.py` - Terms acceptance

### New Canonical Models to CREATE:

1. `newsletter.py` - Subscriber, Campaign models (from
   legacy_lead_newsletter.py)
2. `social.py` - Social media models (from legacy_social.py)
3. `notification.py` - Notification groups (from
   legacy_notification_groups.py)
4. `qr_code.py` - QR tracking (from legacy_qr_tracking.py)
5. `stripe_integration.py` - Stripe models (from
   legacy_stripe_models.py)
6. `event_sourcing.py` - DomainEvent, OutboxEntry (from
   legacy_events.py)
7. `message.py` - MessageThread, Message (from legacy_core.py)

## Consolidation Actions

### Phase 1: Create New Canonical Models

- Extract and modernize models from legacy files
- Use unified Base from models/base.py
- Add extend_existing=True to all tables
- Use PostgresUUID for all IDs
- Standardize naming conventions

### Phase 2: Update All Imports (50+ files)

- Replace `from models.legacy_*` with `from models.*`
- Update test files
- Update service files
- Update router files
- Update worker files

### Phase 3: Delete Legacy Files

- Remove all 13 legacy\_\*.py files
- Clean up models/**init**.py
- Remove references from alembic env.py

### Phase 4: Verify & Test

- Run all tests
- Check import errors
- Verify database queries work
- Ensure no circular imports
