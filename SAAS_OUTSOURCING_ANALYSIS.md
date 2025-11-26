# 🎯 SaaS Outsourcing Opportunities Analysis

**Date:** November 24, 2025 **Purpose:** Identify services we're
building custom that have free/low-cost SaaS alternatives **Status:**
📊 Analysis for Decision-Making

---

## 🎬 Executive Summary

Based on analysis of our codebase, we're building **13 custom
services** that could potentially be outsourced to free/low-cost SaaS
providers, saving **hundreds of development hours** and reducing
maintenance burden.

**Current SaaS Usage:**

- ✅ **Stripe** - Payment processing (already leveraging native
  features)
- ✅ **Google OAuth** - Authentication
- ✅ **Meta/Instagram** - Social media webhooks
- ✅ **RingCentral** - Phone/SMS/Voice
- ⚠️ **Email** - Currently custom SMTP (IONOS + Gmail)

**Recommended Additions:**

- ✅ **6 immediate wins** - Free tiers available, easy integration
- ⚠️ **4 consider options** - Depends on usage volume
- ❌ **3 keep custom** - Too business-specific

---

## ✅ IMMEDIATE WINS (Free Tiers Available)

### 1. **Email Service → Resend / SendGrid / Postmark**

**Current Implementation:**

- ❌ Custom SMTP handling (IONOS + Gmail)
- ❌ 2 email services (`email_service.py`,
  `api/app/services/email_service.py`)
- ❌ Manual routing logic (customer vs admin emails)
- ❌ Manual retry logic
- ❌ No analytics (open rates, click tracking)

**Free Alternative: [Resend](https://resend.com/)**

- ✅ **Free tier:** 100 emails/day, 3,000/month
- ✅ **Better deliverability:** 99%+ vs 95% SMTP
- ✅ **Email analytics:** Open rates, clicks, bounces
- ✅ **Template management:** Visual editor + API
- ✅ **Webhook events:** Delivered, opened, clicked, bounced
- ✅ **Better developer experience:** Simple API
- ✅ **Already in use:** Customer & Admin apps already have `Resend`
  imported!

**Code Impact:**

```typescript
// Frontend already has this!
// apps/customer/src/lib/email-service.ts
// apps/admin/src/lib/email-service.ts
import { Resend } from 'resend';
const resend = new Resend(process.env.RESEND_API_KEY);
```

**Backend needs:**

```python
# Replace 500+ lines of SMTP code with:
import resend

resend_client = resend.Resend(api_key=settings.resend_api_key)

await resend_client.emails.send({
    "from": "bookings@myhibachichef.com",
    "to": customer_email,
    "subject": "Booking Confirmation",
    "html": html_template,
})
```

**Migration Effort:** 2-3 hours **Annual Savings:** ~$500 (IONOS
business email cost) + 20 hours maintenance **Recommendation:** ✅
**HIGH PRIORITY** - Already partially implemented in frontend!

---

### 2. **QR Code Generation → QRCode.js (Free, Client-Side)**

**Current Implementation:**

- ❌ Custom `QRTrackingService` (307 lines)
- ❌ Backend QR generation
- ❌ Database tables for QR codes
- ❌ Custom analytics

**Free Alternative:
[QRCode.js](https://github.com/davidshimjs/qrcodejs) + Simple
Analytics**

- ✅ **Free:** Open source, client-side generation
- ✅ **No backend needed:** Generate on customer's device
- ✅ **Track clicks:** Use URL shortener with analytics (bit.ly free
  tier)
- ✅ **Simple implementation:** 10 lines of code

**Code Impact:**

```typescript
// Frontend (10 lines replaces 307 lines backend):
import QRCode from 'qrcode';

const qrCodeUrl = await QRCode.toDataURL(
  `https://myhibachichef.com/booking/${bookingId}`
);
// Display QR code to customer
```

**For Analytics:**

- Use **Bitly** (free tier: 1,000 links/month) for tracking
- Or **TinyURL** (unlimited free links, basic stats)

**Files to Remove:**

- `apps/backend/src/services/qr_tracking_service.py` (307 lines)
- `apps/backend/src/models/qr_tracking.py` (database models)
- `apps/backend/src/routers/v1/qr_tracking.py` (API endpoints)

**Migration Effort:** 1 hour **Code Reduced:** ~500 lines
**Recommendation:** ✅ **MEDIUM PRIORITY** - Easy win, significant
code reduction

---

### 3. **SMS Campaigns → ✅ KEEP RingCentral (Already Optimal)**

**Current Implementation:**

- ✅ Using **RingCentral** for unified phone + SMS + voice
- ✅ Newsletter via SMS (text-only, no email newsletters)
- ✅ Twilio for WhatsApp only (separate use case)
- ⚠️ Custom campaign management (`nurture_campaign_service.py` - 200+
  lines)

**Decision: KEEP RingCentral**

- ✅ **Already integrated and working well**
- ✅ **Unified platform:** Phone + SMS + Voice in one service
- ✅ **Business phone number:** +19167408768
- ✅ **SMS-first communication:** Matches business model
- ✅ **No migration needed:** Already optimal solution

**Potential Simplification:**

- Could simplify `nurture_campaign_service.py` campaign scheduling
  logic
- Keep RingCentral for sending, simplify management code
- Use RingCentral API directly instead of custom wrapper

**Migration Effort:** N/A (Keep as-is) **Recommendation:** ✅ **KEEP
RINGCENTRAL** - Perfect for your SMS-first business model

---

### 4. **Analytics/Reporting → Google Analytics 4 (Free)**

**Current Implementation:**

- ❌ Custom analytics queries across multiple services
- ❌ `admin_analytics.py` (custom business metrics)
- ❌ `holiday_analytics_service.py`
- ❌ `newsletter_analytics_service.py`
- ❌ No real-time dashboards

**Free Alternative:
[Google Analytics 4](https://analytics.google.com/)**

- ✅ **Free forever:** No limits for standard tracking
- ✅ **Real-time dashboards:** Pre-built visualizations
- ✅ **Event tracking:** Custom events for bookings, payments, etc.
- ✅ **Conversion tracking:** Track booking funnel
- ✅ **User journey:** See how customers find you

**Plus: [Google Data Studio](https://datastudio.google.com/) (Free)**

- ✅ **Custom dashboards:** Drag-and-drop builder
- ✅ **Multiple data sources:** Combine GA4 + Stripe + database
- ✅ **Scheduled reports:** Email PDFs daily/weekly

**Code Impact:**

```typescript
// Frontend: Add GA4 tracking (10 lines)
import { gtag } from 'analytics';

// Track booking event:
gtag('event', 'booking_created', {
  value: bookingAmount,
  currency: 'USD',
  booking_id: bookingId,
});
```

**For Backend Analytics:**

- Keep critical business logic (pricing, availability)
- Move **reporting** to GA4 + Data Studio
- Remove **custom metric calculations** (let GA4 handle it)

**Migration Effort:** 3-4 hours **Code Reduced:** ~300 lines analytics
code **Recommendation:** ✅ **MEDIUM PRIORITY** - Professional
dashboards for free

---

### 5. **Image Storage → Cloudinary / ImageKit (Free Tiers)**

**Current Implementation:**

- ❌ Custom `image_service.py` (local file storage)
- ❌ Manual image optimization
- ❌ No CDN (slow image loading)

**Free Alternative: [Cloudinary](https://cloudinary.com/)**

- ✅ **Free tier:** 25 GB storage, 25 GB bandwidth/month
- ✅ **Auto optimization:** WebP, lazy loading, responsive images
- ✅ **CDN:** Fast global delivery
- ✅ **Transformations:** Resize, crop, filters on-the-fly
- ✅ **Upload widget:** Drag-and-drop UI component

**OR [ImageKit](https://imagekit.io/):**

- ✅ **Free tier:** 20 GB storage, 20 GB bandwidth
- ✅ **Real-time transformations:** URL-based image editing
- ✅ **Better free tier:** More generous than Cloudinary

**Code Impact:**

```python
# Replace custom image handling:
import cloudinary.uploader

result = cloudinary.uploader.upload(
    file,
    folder="booking_photos",
    transformation=[
        {"width": 800, "crop": "limit"},
        {"quality": "auto"},
        {"fetch_format": "auto"}
    ]
)

image_url = result['secure_url']  # CDN URL
```

**Files to Remove:**

- `apps/backend/src/services/image_service.py`
- Local file storage logic

**Migration Effort:** 2-3 hours **Benefits:** Faster images,
auto-optimization, CDN **Recommendation:** ✅ **LOW PRIORITY** - Nice
to have, but current solution works

---

### 6. **Calendar Integration → Nylas / Google Calendar API (Free)**

**Current Implementation:**

- ❌ Manual calendar management
- ❌ No external calendar sync (Google Calendar, Outlook)
- ❌ No automated calendar invites

**Free Alternative: [Nylas](https://www.nylas.com/)**

- ✅ **Free tier:** 5 connected accounts
- ✅ **Multi-provider:** Gmail, Outlook, iCloud, Exchange
- ✅ **Calendar sync:** Two-way sync with customer calendars
- ✅ **Availability API:** Check customer availability
- ✅ **Event creation:** Auto-create calendar events

**OR Google Calendar API (Free):**

- ✅ **Free forever:** No limits
- ✅ **Event creation:** Auto-send calendar invites
- ✅ **Reminders:** Built-in notification system
- ✅ **Availability:** Check free/busy times

**Code Impact:**

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Create calendar event:
service = build('calendar', 'v3', credentials=creds)
event = {
    'summary': 'Hibachi Catering Event',
    'start': {'dateTime': booking.start_time},
    'end': {'dateTime': booking.end_time},
    'attendees': [{'email': customer.email}],
    'reminders': {'useDefault': False, 'overrides': [
        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
        {'method': 'popup', 'minutes': 60},  # 1 hour before
    ]}
}

service.events().insert(calendarId='primary', body=event).execute()
```

**Benefits:**

- ✅ Auto-send calendar invites to customers
- ✅ Reduce no-shows (calendar reminders)
- ✅ Check customer availability before booking

**Migration Effort:** 3-4 hours **Recommendation:** ⚠️ **CONSIDER** -
Depends on customer demand for calendar integration

---

## ⚠️ CONSIDER (Depends on Usage Volume)

### 7. **Newsletter Management → Brevo / Mailchimp**

**Current Implementation:**

- ❌ Custom subscriber management
- ❌ Custom campaign tracking
- ❌ Custom email templates
- ❌ Manual segmentation

**Free Alternative: [Brevo](https://www.brevo.com/)**

- ✅ **Free tier:** Unlimited contacts, 300 emails/day
- ✅ **Visual editor:** Drag-and-drop email builder
- ✅ **Automation:** Welcome series, drip campaigns
- ✅ **Segmentation:** Tag-based targeting
- ✅ **Analytics:** Open rates, clicks, conversions

**OR [Mailchimp](https://mailchimp.com/):**

- ✅ **Free tier:** 500 contacts, 1,000 emails/month
- ⚠️ **More restrictive:** Lower limits than Brevo

**Migration Effort:** 4-6 hours (need to migrate subscriber list)
**Code Reduced:** ~400 lines newsletter code **Recommendation:** ⚠️
**EVALUATE** - If sending <300 emails/day, use Brevo. If more, keep
custom.

---

### 8. **Customer Support Chat → Tawk.to / Crisp (Free)**

**Current Implementation:**

- ❌ No built-in live chat
- ⚠️ Using social media DMs (Instagram, Facebook)
- ⚠️ Phone/SMS via RingCentral

**Free Alternative: [Tawk.to](https://www.tawk.to/)**

- ✅ **100% free forever:** No limits, no credit card
- ✅ **Live chat widget:** Add to website in 5 minutes
- ✅ **Mobile apps:** iOS + Android
- ✅ **Canned responses:** Pre-written replies
- ✅ **File sharing:** Send images, PDFs
- ✅ **Visitor monitoring:** See who's on your site

**OR [Crisp](https://crisp.chat/):**

- ✅ **Free tier:** Unlimited conversations, 2 seats
- ✅ **Chatbot:** Automated responses
- ✅ **Email integration:** Manage emails in same inbox
- ✅ **Better UI:** More modern interface

**Code Impact:**

```html
<!-- Add to website header: -->
<script type="text/javascript">
  var Tawk_API = Tawk_API || {};
  var Tawk_LoadStart = new Date();
  (function () {
    var s1 = document.createElement('script');
    s1.src = 'https://embed.tawk.to/YOUR_PROPERTY_ID/default';
    document.head.appendChild(s1);
  })();
</script>
```

**Benefits:**

- ✅ Instant customer support
- ✅ Reduce phone calls
- ✅ Capture leads from website visitors

**Migration Effort:** 30 minutes **Recommendation:** ✅ **LOW
PRIORITY** - Quick win if you want live chat

---

### 9. **Form Builder → Typeform / Google Forms (Free)**

**Current Implementation:**

- ❌ Custom booking forms
- ❌ Custom quote request forms
- ⚠️ Forms embedded in Next.js apps

**Free Alternative: [Typeform](https://www.typeform.com/)**

- ✅ **Free tier:** 10 responses/month (limited)
- ⚠️ **Paid needed:** $25/month for unlimited

**OR [Google Forms](https://forms.google.com/) (Better for free):**

- ✅ **Free forever:** Unlimited forms, unlimited responses
- ✅ **Auto-save to Sheets:** Easy data export
- ✅ **Customization:** Themes, logic branching
- ✅ **Embed anywhere:** iFrame integration

**OR [Tally](https://tally.so/):**

- ✅ **Free tier:** Unlimited forms, unlimited responses!
- ✅ **Better UX:** More modern than Google Forms
- ✅ **Calculations:** Auto-calculate totals
- ✅ **Conditional logic:** Show/hide fields based on answers

**Migration Effort:** 1-2 hours per form **Recommendation:** ❌ **NOT
RECOMMENDED** - Current Next.js forms are better integrated and more
professional

---

### 10. **Appointment Scheduling → Calendly / Cal.com (Free)**

**Current Implementation:**

- ✅ Custom booking system (core business logic - keep this!)
- ❌ No self-service scheduling for consultations/quotes

**Free Alternative: [Cal.com](https://cal.com/)**

- ✅ **Free tier:** Unlimited events, unlimited bookings
- ✅ **Open source:** Self-hosted option available
- ✅ **Integrations:** Google Calendar, Zoom, Stripe
- ✅ **Embed widget:** Add to website
- ✅ **Custom branding:** Use your domain

**OR [Calendly](https://calendly.com/):**

- ✅ **Free tier:** 1 event type, unlimited bookings
- ⚠️ **Limited free:** Need paid for multiple event types

**Use Case:**

- ❌ **Don't replace main booking system** (too complex, core
  business)
- ✅ **Add for consultation calls:** Let customers book 15-min quote
  calls
- ✅ **Add for site visits:** Chef availability checks

**Code Impact:**

```html
<!-- Embed Cal.com widget: -->
<iframe src="https://cal.com/myhibachi/consultation" />
```

**Migration Effort:** 1 hour setup **Recommendation:** ⚠️
**OPTIONAL** - Only if you want consultation scheduling separate from
main bookings

---

## ❌ KEEP CUSTOM (Business-Specific)

### 11. **Booking System** - ❌ KEEP CUSTOM

- Too business-specific (travel fees, multi-chef, menu customization)
- Core business logic (don't outsource)
- Stripe Checkout can't handle complex pricing

### 12. **AI Booking Assistant** - ❌ KEEP CUSTOM

- Unique to your business model
- Requires deep integration with menu, pricing, availability
- No SaaS can replicate this

### 13. **Payment Matching** - ❌ KEEP CUSTOM

- Unique Zelle/Venmo email parsing logic
- Business-specific matching algorithm
- Already automated and working well

---

## 📊 SUMMARY & RECOMMENDATIONS

### ✅ **HIGH PRIORITY (Implement ASAP)**

| Service      | Replace With      | Effort    | Savings        | Annual Cost         |
| ------------ | ----------------- | --------- | -------------- | ------------------- |
| **Email**    | Resend            | 2-3 hours | $500 + 20 hrs  | **FREE** (3K/month) |
| **QR Codes** | QRCode.js + Bitly | 1 hour    | 500 lines code | **FREE**            |

**Total Immediate Savings:** $500/year + 500 lines code + 20
hours/year maintenance

---

### ⚠️ **MEDIUM PRIORITY (Consider)**

| Service        | Replace With        | Effort    | Benefit                   | Cost               |
| -------------- | ------------------- | --------- | ------------------------- | ------------------ |
| **Analytics**  | Google Analytics 4  | 3-4 hours | Professional dashboards   | **FREE**           |
| **Images**     | Cloudinary          | 2-3 hours | CDN, auto-optimization    | **FREE** (25GB)    |
| **Calendar**   | Google Calendar API | 3-4 hours | Auto-invites, reminders   | **FREE**           |
| **Newsletter** | Brevo               | 4-6 hours | Visual editor, automation | **FREE** (300/day) |

---

### 🔍 **LOW PRIORITY (Nice to Have)**

| Service                     | Replace With | Benefit              | Cost     |
| --------------------------- | ------------ | -------------------- | -------- |
| **Live Chat**               | Tawk.to      | Instant support      | **FREE** |
| **Consultation Scheduling** | Cal.com      | Self-service booking | **FREE** |

---

## 💰 COST-BENEFIT ANALYSIS

### **Current Costs (Annual):**

- IONOS Business Email: ~$500/year
- Custom code maintenance: ~40 hours/year (~$2,000 value)
- **Total:** ~$2,500/year

### **After Outsourcing (High Priority Only):**

- Resend: **$0** (free tier sufficient)
- QR Codes: **$0** (client-side generation)
- Maintenance reduction: -20 hours/year (~$1,000 value)
- **Total:** **$0/year** + 500 lines less code

### **ROI:**

- **Year 1:** Save $2,500 + 6 hours implementation
- **Year 2+:** Save $2,500 + 20 hours/year
- **Code reduction:** 500 lines immediately

---

## 🚀 IMPLEMENTATION PLAN

### **Phase 1: Email Migration (Week 1)**

1. ✅ Frontend already has Resend configured
2. Migrate backend email service to Resend API
3. Test all email types (confirmations, receipts, admin)
4. Switch DNS/SPF records to Resend
5. Deprecate IONOS SMTP

**Estimated Time:** 3 hours **Risk:** LOW (Resend has better
deliverability)

---

### **Phase 2: QR Code Migration (Week 1)**

1. Replace backend QR generation with client-side QRCode.js
2. Setup Bitly account for tracking links
3. Update booking confirmation emails with QR codes
4. Test QR scanning on mobile devices
5. Remove QR tracking database tables (optional - can keep analytics)

**Estimated Time:** 1-2 hours **Risk:** LOW (simple library
replacement)

---

### **Phase 3: Analytics Enhancement (Week 2)**

1. Setup Google Analytics 4 account
2. Add GA4 tracking to customer website
3. Add GA4 tracking to admin dashboard
4. Create custom events (bookings, payments, quotes)
5. Setup Google Data Studio dashboards
6. Keep critical business metrics in backend (pricing, availability)

**Estimated Time:** 4 hours **Risk:** LOW (additive, doesn't replace
anything critical)

---

### **Phase 4: Optional Enhancements (Week 3-4)**

1. Evaluate Cloudinary for images (if needed)
2. Evaluate Google Calendar API (if customers request it)
3. Evaluate Brevo for newsletters (if current system limiting)
4. Evaluate Tawk.to for live chat (if needed)

**Estimated Time:** 2-8 hours depending on selections **Risk:** VERY
LOW (all optional, non-critical)

---

## ❓ DECISION POINTS

Please decide:

### **1. Email Migration to Resend?**

- [x] ✅ YES - Migrate ASAP (recommended - $500/year savings + better
      analytics) **✅ COMPLETED Nov 24, 2025**
  - Backend migrated to Resend API
  - Frontend already had Resend configured
  - Same email addresses: cs@myhibachichef.com (kept!)
  - TODO: Add DNS records (SPF, DKIM) to myhibachichef.com domain
  - TODO: Get RESEND_API_KEY from https://resend.com/api-keys
  - TODO: Test all email types (approval, rejection, suspension,
    welcome)

### **2. QR Code Generation to QRCode.js?**

- [x] ❌ NO - Keep business card QR only **✅ USER DECISION: Option
      A**
  - Business card QR → Static URL (keep as-is)
  - NO booking confirmation QR codes needed
  - Use Google Analytics for tracking instead
  - No changes required

### **3. Add Google Analytics 4?**

- [ ] ✅ YES - Professional dashboards for free
- [ ] ❌ NO - Keep custom analytics only
- [ ] ⏸️ LATER - Delay decision

### **4. Image Storage to Cloudinary?**

- [ ] ✅ YES - CDN + auto-optimization
- [ ] ❌ NO - Keep current local storage
- [ ] ⏸️ LATER - Delay decision

### **5. Newsletter to Brevo?**

- [ ] ✅ YES - Visual editor + automation
- [ ] ❌ NO - Keep custom newsletter system
- [ ] ⏸️ LATER - Delay decision

### **6. Add Live Chat (Tawk.to)?**

- [ ] ✅ YES - Instant customer support
- [ ] ❌ NO - Not needed
- [ ] ⏸️ LATER - Delay decision

---

## 📚 ADDITIONAL RESOURCES

**Free SaaS Tools Summary:**

- **Resend** - https://resend.com/pricing (3K emails/month free)
- **QRCode.js** - https://github.com/davidshimjs/qrcodejs (open
  source)
- **Bitly** - https://bitly.com/pricing (1K links/month free)
- **Google Analytics 4** - https://analytics.google.com/ (free
  forever)
- **Cloudinary** - https://cloudinary.com/pricing (25GB free)
- **Brevo** - https://www.brevo.com/pricing (300 emails/day free)
- **Tawk.to** - https://www.tawk.to/pricing/ (100% free)
- **Cal.com** - https://cal.com/pricing (unlimited free)

---

**Next Steps:**

1. Review this document
2. Make decisions on checkboxes above
3. Prioritize implementations
4. Start with Email + QR (highest ROI)

**Questions?**

- Which services do you use most?
- Current email volume? (to size Resend tier)
- Current newsletter subscriber count?
- Do customers ask for calendar integration?
