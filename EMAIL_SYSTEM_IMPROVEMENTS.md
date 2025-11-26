# Email Management System - Improvements & Enhancements

## 🎯 Current Features (Already Implemented)

### ✅ Gmail-Style UI

- Threaded conversations (grouped by subject)
- Inbox sidebar with email previews
- Avatars with initials
- Relative timestamps ("5m ago", "Yesterday")
- Unread indicators (blue dot)
- Star/unstar threads
- Search emails
- Filter by unread/starred
- Reply box (Customer Support only)

### ✅ Dual Inbox System

1. **Customer Support** (cs@myhibachichef.com) - Full READ/WRITE
   - Read incoming emails via IONOS IMAP
   - Reply via Resend API
   - Mark read/unread, star, archive
   - Search & filter emails

2. **Payment Monitoring** (myhibachichef@gmail.com) - READ ONLY
   - View payment notifications
   - Manual verification
   - No reply capability

---

## 🚀 NEW: WhatsApp Email Notifications (Just Added)

### Architecture

```
┌──────────────────┐
│  IONOS IMAP      │ → New customer email arrives
│  cs@myhibachi... │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│ EmailNotificationService     │ → Checks every 60s
│ - fetch_new_emails()         │
│ - deduplicate_notifications()│
│ - check_notification_hours() │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ WhatsAppNotificationService  │ → Send alert to admin
│ - send_email_alert()         │
└──────────────────────────────┘
```

### Features

✅ **Real-time email monitoring** (checks every 60 seconds) ✅
**WhatsApp notifications** for new customer support emails ✅
**Deduplication** (don't spam same email notification) ✅
**Configurable notification hours** (9am-9pm by default) ✅
**Priority-based alerts** (urgent keywords trigger high-priority
alerts) ✅ **Admin settings** to enable/disable ✅ **Multi-admin
support** (notify multiple phone numbers)

### Urgent Keywords Detection

Emails containing these keywords trigger **HIGH-PRIORITY** alerts:

- urgent
- emergency
- asap
- complaint
- refund
- cancel
- problem
- issue
- help
- immediately

### Notification Format

**Normal Email Alert:**

```
📧 NEW EMAIL - Customer Support

From: John Doe
Email: john@example.com
Subject: Question about booking

Preview:
Hi, I have a question about my upcoming hibachi booking...

🔗 View in Admin:
https://admin.myhibachichef.com/emails?tab=customer_support&id=msg-123
```

**Urgent Email Alert:**

```
🚨 URGENT EMAIL - Customer Support

From: Jane Smith
Email: jane@example.com
Subject: URGENT - Need to cancel booking

Preview:
I need to cancel my booking ASAP due to an emergency...

🔗 View in Admin:
https://admin.myhibachichef.com/emails?tab=customer_support&id=msg-456
```

### Files Created

1. **`apps/backend/src/services/email_notification_service.py`** (320
   lines)
   - EmailNotificationService class
   - WhatsApp integration
   - Deduplication logic
   - Notification hours checking
   - Urgent keyword detection
   - Background scheduler

2. **`apps/backend/src/tasks/email_notification_task.py`** (50 lines)
   - Background task wrapper
   - Auto-restart on crash
   - Logging

### Configuration

Add to `apps/backend/.env`:

```bash
# Email Notification Settings
EMAIL_NOTIFICATION_ENABLED=true
EMAIL_NOTIFICATION_START_HOUR=9   # 9am
EMAIL_NOTIFICATION_END_HOUR=21    # 9pm
EMAIL_NOTIFICATION_INTERVAL=60    # Check every 60 seconds

# Admin phone numbers (comma-separated for multiple admins)
BUSINESS_PHONE=+19167408768,+12103884155
ON_CALL_ADMIN_PHONE=+19167408768
```

### Integration with main.py

Add to `apps/backend/src/main.py`:

```python
from tasks.email_notification_task import start_email_notification_task

@app.on_event("startup")
async def startup():
    # ... existing startup code ...

    # Start email notification scheduler
    logger.info("🚀 Starting email notification background task...")
    asyncio.create_task(start_email_notification_task())
    logger.info("✅ Email notification scheduler started")
```

---

## 📋 Recommended Improvements (Next Steps)

### 1. UI/UX Enhancements

#### A. Attachment Support (1-2 hours)

**Current State:** Attachments detected but not downloadable
**Improvement:**

- Add download button for each attachment
- Show file type icon (PDF, DOC, IMG, etc.)
- Preview images inline
- Virus scanning for uploaded files

**Files to Modify:**

- `apps/admin/src/app/emails/page.tsx` - Add download buttons
- `apps/backend/src/routers/v1/admin_emails.py` - Add attachment
  download endpoint
- `apps/backend/src/services/customer_email_monitor.py` - Extract
  attachment data

#### B. Draft Saving (30 mins)

**Current State:** Replies lost if user navigates away
**Improvement:**

- Auto-save drafts to localStorage every 5 seconds
- Restore drafts when returning to email
- Show "Draft saved at 2:34 PM" indicator

**Implementation:**

```typescript
// apps/admin/src/app/emails/page.tsx
useEffect(() => {
  const draftKey = `email-draft-${selectedThread?.thread_id}`;
  const savedDraft = localStorage.getItem(draftKey);
  if (savedDraft) {
    setReplyText(savedDraft);
    toast.info('Draft restored');
  }
}, [selectedThread]);

useEffect(() => {
  if (replyText && selectedThread) {
    const draftKey = `email-draft-${selectedThread.thread_id}`;
    localStorage.setItem(draftKey, replyText);
  }
}, [replyText, selectedThread]);
```

#### C. Quick Reply Templates (1 hour)

**Current State:** Must type every reply manually **Improvement:**

- Predefined templates for common responses
- Template variables: {customer_name}, {booking_id}, {event_date}
- One-click template insertion

**Templates:**

- "Thank you for your inquiry..."
- "Your booking is confirmed..."
- "We apologize for the inconvenience..."
- "Your refund has been processed..."

#### D. Rich Text Editor (2-3 hours)

**Current State:** Plain text replies only **Improvement:**

- WYSIWYG editor (TinyMCE or Tiptap)
- Bold, italic, underline, lists
- Insert links, images
- HTML signature support

#### E. Email Signatures (30 mins)

**Current State:** No signature appended to replies **Improvement:**

- Configurable signature per user
- Default signature for cs@myhibachichef.com
- Include logo, contact info, social links

**Example Signature:**

```html
--- Best regards, My Hibachi Chef Team 📧 cs@myhibachichef.com 📞
(916) 740-8768 🌐 www.myhibachichef.com
```

#### F. Auto-Refresh (30 mins)

**Current State:** Must manually click refresh **Improvement:**

- Auto-fetch new emails every 30 seconds
- Show "New email arrived" toast notification
- Visual indicator when new emails detected
- Pause auto-refresh when composing reply

#### G. Keyboard Shortcuts (1 hour)

**Current State:** Mouse-only navigation **Improvement:**

- `j/k` - Navigate up/down in email list
- `c` - Compose new email
- `r` - Reply to selected email
- `e` - Archive email
- `s` - Star email
- `u` - Mark as unread
- `/` - Focus search box
- `Esc` - Close compose modal

#### H. Bulk Actions (2 hours)

**Current State:** One email at a time **Improvement:**

- Multi-select checkboxes
- Bulk star/unstar
- Bulk archive
- Bulk mark as read/unread
- Bulk delete
- "Select all" button

#### I. Labels/Tags System (2-3 hours)

**Current State:** No email categorization **Improvement:**

- Custom labels (e.g., "Booking Question", "Payment Issue",
  "Complaint")
- Color-coded labels
- Filter by label
- Auto-label based on keywords

#### J. Mobile Responsive (1-2 hours)

**Current State:** Desktop-optimized **Improvement:**

- Collapsible sidebar on mobile
- Swipe gestures (swipe right to archive)
- Touch-friendly buttons (larger tap targets)
- Bottom navigation for actions

---

### 2. Backend Enhancements

#### A. Email Storage in Database (3-4 hours)

**Current State:** Emails only in IMAP (ephemeral) **Improvement:**

- Store emails in PostgreSQL for fast access
- Index by sender, subject, date for search
- Sync with IMAP every 60 seconds
- Archive old emails (> 90 days) to cold storage

**Database Schema:**

```sql
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    inbox VARCHAR(50) NOT NULL, -- 'customer_support' or 'payments'
    from_address VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_address VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    text_body TEXT,
    html_body TEXT,
    received_at TIMESTAMP NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    labels TEXT[], -- Array of label names
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_emails_inbox ON emails(inbox);
CREATE INDEX idx_emails_thread_id ON emails(thread_id);
CREATE INDEX idx_emails_received_at ON emails(received_at DESC);
CREATE INDEX idx_emails_is_read ON emails(is_read) WHERE is_read = FALSE;
```

#### B. Email Analytics (1 hour)

**Current State:** No tracking **Improvement:**

- Track reply time (first response)
- Count emails per day/week/month
- Busiest hours/days
- Most common subjects
- Response rate (% of emails replied to)

#### C. Email Search Improvements (1-2 hours)

**Current State:** Basic text search **Improvement:**

- Full-text search (PostgreSQL `tsvector`)
- Search operators: `from:`, `subject:`, `has:attachment`
- Date range filters
- Advanced search UI

---

### 3. Resend API Enhancements

#### A. Webhook Integration (1 hour) - **HIGH PRIORITY**

**Current State:** No delivery tracking **Improvement:**

- Track email delivery status
- Track bounce/spam reports
- Track opens (if customer enables)
- Track clicks on links
- Store webhook events in database

**Webhook Events:**

- `email.sent` - Email sent successfully
- `email.delivered` - Email delivered to recipient
- `email.delivery_delayed` - Temporary delivery failure
- `email.bounced` - Permanent delivery failure
- `email.complained` - Marked as spam
- `email.opened` - Email opened (if tracking enabled)
- `email.clicked` - Link clicked

#### B. Email Templates (1-2 hours)

**Current State:** Plain text/HTML in code **Improvement:**

- Resend email templates
- Template versioning
- Preview before sending
- A/B testing

#### C. Scheduled Sending (1 hour)

**Current State:** Send immediately **Improvement:**

- Schedule email for later
- Recurring emails (weekly newsletter)
- Timezone-aware scheduling

---

## 🎯 Priority Ranking

### Critical (Do First)

1. **Resend Webhooks** (1 hour) - Track delivery status
2. **Auto-Refresh** (30 mins) - Better UX
3. **Draft Saving** (30 mins) - Prevent data loss
4. **Email Notification Task Integration** (15 mins) - Enable WhatsApp
   alerts

### High Priority (Do Soon)

5. **Quick Reply Templates** (1 hour) - Faster responses
6. **Email Signatures** (30 mins) - Professional replies
7. **Attachment Download** (1-2 hours) - View customer files
8. **Keyboard Shortcuts** (1 hour) - Power user efficiency

### Medium Priority (Nice to Have)

9. **Rich Text Editor** (2-3 hours) - Better formatting
10. **Bulk Actions** (2 hours) - Mass operations
11. **Email Storage in DB** (3-4 hours) - Performance + search
12. **Labels/Tags** (2-3 hours) - Organization

### Low Priority (Future)

13. **Email Analytics** (1 hour) - Insights
14. **Mobile Responsive** (1-2 hours) - Mobile access
15. **Scheduled Sending** (1 hour) - Advanced feature

---

## 📊 Estimated Time Investment

**Total Time for All Improvements:** ~30-40 hours

**Quick Wins (< 2 hours total):**

- Auto-Refresh (30 mins)
- Draft Saving (30 mins)
- Email Signatures (30 mins)
- Enable WhatsApp Notifications (15 mins)

**High Impact (< 5 hours total):**

- Resend Webhooks (1 hour)
- Quick Reply Templates (1 hour)
- Attachment Download (1-2 hours)
- Keyboard Shortcuts (1 hour)

**Major Features (20+ hours):**

- Rich Text Editor (2-3 hours)
- Email Storage in DB (3-4 hours)
- Bulk Actions (2 hours)
- Labels/Tags (2-3 hours)
- Email Analytics (1 hour)
- Mobile Responsive (1-2 hours)
- Search Improvements (1-2 hours)
- Email Templates (1-2 hours)

---

## 🚀 Next Steps

1. **Enable WhatsApp Email Notifications** (15 mins)
   - Add `start_email_notification_task()` to `main.py` startup
   - Configure admin phone numbers in `.env`
   - Test notification delivery

2. **Test Email UI End-to-End** (1 hour)
   - Start backend server
   - Test customer support inbox (read, reply, star, archive)
   - Test payment monitoring inbox (read-only)
   - Verify WhatsApp notifications for new emails

3. **Implement Quick Wins** (2 hours)
   - Auto-refresh
   - Draft saving
   - Email signatures

4. **Add Resend Webhooks** (1 hour)
   - Critical for tracking email delivery

5. **Continue with other improvements** based on priority

---

## 📝 Summary

**Current Email System:**

- ✅ Gmail-style UI with 2 inboxes
- ✅ Full CRUD operations (read, reply, star, archive, delete)
- ✅ Search and filtering
- ✅ Threaded conversations
- ✅ WhatsApp notifications for new emails (NEW!)

**Recommended Next Actions:**

1. Enable WhatsApp notifications (15 mins)
2. Test end-to-end (1 hour)
3. Add Resend webhooks (1 hour)
4. Implement quick wins (2 hours)
5. Continue with high-priority improvements

This gives you a **production-ready email management system** with
real-time WhatsApp alerts for incoming customer emails!
