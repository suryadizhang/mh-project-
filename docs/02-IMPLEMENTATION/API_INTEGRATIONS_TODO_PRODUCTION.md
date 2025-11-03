# API Integrations - Production Deployment TODO

## 🎉 COMPLETED INTEGRATIONS

### ✅ 1. Stripe Payment Processing
- **Status:** Complete with webhook secret
- **Credentials:** All configured in `.env`
- **Webhook Secret:** `whsec_ihBPmoh1ra7SM2Ghbd9BgrNY9kEUM6yc`

### ✅ 2. RingCentral SMS & Voice
- **Status:** Credentials configured
- **Account:** my Hibachi LLC
- **Main Number:** +19167408768
- **Extension 101:** Suryadi Zhang (Human escalation)

### ✅ 3. Plaid Banking
- **Status:** Sandbox configured
- **Client ID:** `68ffbe986a1a5500222404db`
- **Environment:** sandbox (ready for testing)

### ✅ 4. Meta (Facebook/Instagram)
- **Status:** Development setup complete
- **App ID:** 1839409339973429
- **Facebook Page:** My hibachi (connected)
- **Instagram:** @my_hibachi_chef (connected)

### ✅ 5. OpenAI
- **Status:** Configured and ready
- **Model:** gpt-4

### ✅ 6. Cloudinary (Image Upload)
- **Status:** Configured for customer review images

---

## 📋 PENDING TASKS BY INTEGRATION

## 🔔 RingCentral - TODO

### **A. Authentication Setup**
**Current:** Using password authentication (username + password + extension)

**Action Items:**
- [ ] Test SMS sending functionality
- [ ] Test SMS receiving (webhook setup needed)
- [ ] Test voice call initiation
- [ ] Test call receiving and routing

### **B. Webhook Configuration** (When Server is Live)
**Webhook URL:** `https://myhibachichef.com/api/v1/webhooks/ringcentral`

**Action Items:**
- [ ] Configure RingCentral webhook in app settings
- [ ] Set webhook secret: Use `RC_WEBHOOK_SECRET` from `.env`
- [ ] Subscribe to events:
  - [ ] `SMS Inbound` - Receive incoming SMS
  - [ ] `SMS Outbound Status` - Track sent SMS
  - [ ] `Voice Call Status` - Track call status
  - [ ] `Voicemail` - Receive voicemail notifications

### **C. Extension Management System** (PRIORITY!)
**Goal:** Dynamic extension management for AI → Human escalation

**Features to Build:**
1. **Admin Panel - Extension Manager**
   - [ ] Create UI to add/remove extensions
   - [ ] Extension form fields:
     - Extension number (e.g., 101, 102, 103)
     - Employee name
     - Role/Department
     - Status (Available/Busy/Offline)
     - Working hours
   - [ ] Set primary extension for escalation (default: 101)
   
2. **Database Schema:**
   ```sql
   CREATE TABLE extensions (
     id UUID PRIMARY KEY,
     extension_number VARCHAR(10) NOT NULL,
     employee_name VARCHAR(100),
     role VARCHAR(50),
     status ENUM('available', 'busy', 'offline'),
     working_hours JSONB,
     is_primary_escalation BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP,
     updated_at TIMESTAMP
   );
   ```

3. **API Endpoints to Create:**
   - [ ] `POST /api/v1/admin/extensions` - Add new extension
   - [ ] `GET /api/v1/admin/extensions` - List all extensions
   - [ ] `PUT /api/v1/admin/extensions/{id}` - Update extension
   - [ ] `DELETE /api/v1/admin/extensions/{id}` - Remove extension
   - [ ] `POST /api/v1/admin/extensions/{id}/transfer-call` - Transfer active call

4. **AI Call Routing Logic:**
   - [ ] Implement keyword detection for human escalation
   - [ ] Keywords: "speak to human", "talk to person", "representative", "manager"
   - [ ] Check extension availability before transfer
   - [ ] Fallback to voicemail if all extensions busy
   - [ ] Round-robin distribution for multiple available extensions

5. **Call Transfer Implementation:**
   - [ ] Use RingCentral Call Control API
   - [ ] Announce to customer: "Transferring you to our team member..."
   - [ ] Send SMS to extension owner: "Incoming escalated call from [customer]"
   - [ ] Log escalation reason in database

### **D. SMS Features to Implement**
- [ ] Two-way SMS conversations
- [ ] SMS booking confirmations
- [ ] SMS review requests (after event)
- [ ] SMS payment reminders
- [ ] SMS appointment reminders (day before event)
- [ ] Automated SMS responses (AI-powered)
- [ ] SMS opt-out management

### **E. Voice Features to Implement**
- [ ] Incoming call handling
- [ ] AI voice assistant (using OpenAI Realtime API)
- [ ] Call recording and transcription
- [ ] Voicemail transcription
- [ ] Call analytics and reporting
- [ ] Business hours routing (after hours → voicemail)

---

## 📱 Meta (Facebook/Instagram) - TODO

### **A. Webhook Configuration** (When Server is Live)
**Webhook URL:** `https://myhibachichef.com/api/v1/webhooks/meta`  
**Verify Token:** `myhibachi-meta-webhook-verify-token-2025`

**Action Items:**
- [ ] Configure webhook in Messenger settings
- [ ] Configure webhook in Instagram Messaging settings
- [ ] Subscribe to Facebook events:
  - [ ] `messages` - Messenger DMs
  - [ ] `messaging_postbacks` - Button clicks
  - [ ] `feed` - Page posts and comments
- [ ] Subscribe to Instagram events:
  - [ ] `messages` - Instagram DMs
  - [ ] `message_reactions` - Message reactions
  - [ ] `messaging_handovers` - Handoff to inbox

### **B. App Review & Public Access**
**Location:** https://developers.facebook.com/apps/1839409339973429/app-review/

**Required for Production:**
- [ ] Create Privacy Policy page (required by Meta)
- [ ] Record demo video showing app functionality
- [ ] Submit for app review:
  - [ ] `pages_messaging`
  - [ ] `pages_manage_metadata`
  - [ ] `pages_read_engagement`
  - [ ] `instagram_manage_messages`
  - [ ] `instagram_manage_comments`
- [ ] Provide test credentials to Meta reviewers
- [ ] Wait for approval (typically 3-5 business days)

### **C. Features to Implement**
- [ ] Facebook Messenger auto-replies (AI-powered)
- [ ] Facebook Page comment management
- [ ] Instagram DM auto-replies (AI-powered)
- [ ] Instagram comment management
- [ ] Sentiment analysis for all messages
- [ ] Lead capture from social media inquiries
- [ ] Social media → booking pipeline
- [ ] Human escalation for complex inquiries

---

## 🏦 Plaid Banking - TODO

### **A. Payment Matching System** (PRIORITY!)
**Goal:** Auto-match Zelle/Venmo/CashApp payments to bookings

**Features to Build:**
1. **Bank Account Connection:**
   - [ ] Create UI for connecting business bank account
   - [ ] Use Plaid Link to connect account
   - [ ] Store Plaid access token securely
   - [ ] Schedule daily transaction sync

2. **Payment Matching Algorithm:**
   ```python
   # Match by:
   # 1. Customer name (fuzzy matching)
   # 2. Amount (with tolerance for tips)
   # 3. Date range (event date -1 to +4 days)
   # 4. Payment description keywords
   ```

3. **Payment Types to Handle:**
   - [ ] Deposit only ($100+)
   - [ ] Full payment (deposit + balance)
   - [ ] Remaining balance only
   - [ ] Balance + tips (5-50% of total)

4. **Database Schema:**
   ```sql
   CREATE TABLE payment_matches (
     id UUID PRIMARY KEY,
     booking_id UUID REFERENCES bookings(id),
     plaid_transaction_id VARCHAR(255),
     customer_name VARCHAR(255),
     amount_cents INTEGER,
     payment_type ENUM('deposit', 'full', 'balance', 'balance_with_tip'),
     confidence_score DECIMAL(3,2), -- 0.00 to 1.00
     matched_at TIMESTAMP,
     verified_by_admin BOOLEAN DEFAULT FALSE,
     match_reason TEXT
   );
   ```

5. **API Endpoints:**
   - [ ] `POST /api/v1/admin/plaid/connect` - Connect bank account
   - [ ] `GET /api/v1/admin/plaid/transactions` - View recent transactions
   - [ ] `POST /api/v1/admin/plaid/match-payment` - Manual match
   - [ ] `GET /api/v1/admin/plaid/unmatched` - View unmatched payments
   - [ ] `POST /api/v1/admin/plaid/verify-match/{id}` - Verify auto-match

6. **Matching Logic:**
   - [ ] Fuzzy name matching (using Levenshtein distance)
   - [ ] Amount matching with tip tolerance
   - [ ] Date window filtering
   - [ ] Confidence scoring
   - [ ] Manual review queue for low-confidence matches
   - [ ] Automatic marking as paid when confidence > 90%

7. **Admin Notifications:**
   - [ ] Email notification for unmatched payments
   - [ ] Dashboard widget showing pending matches
   - [ ] Weekly reconciliation report

### **B. Bank Verification (Optional)**
- [ ] Implement bank account verification for customers
- [ ] Use for ACH payment processing
- [ ] Store verified bank details securely

---

## 🗺️ Google Business Profile - TODO

### **A. Initial Setup** ✅ COMPLETED
- [x] Create Google Cloud Project (`my-hibachi-crm`)
- [x] Enable Google Business Profile API
- [x] Create OAuth 2.0 credentials
- [ ] OAuth authorization flow (first-time browser auth)
- [ ] Get Account ID and Location ID via API
- [ ] Store refresh token for auto-renewal

### **B. Review Management - SMART FEATURES**

#### **B.1 Basic Review Handling**
- [ ] Fetch new reviews every hour
- [ ] Store reviews in database
- [ ] AI sentiment analysis (positive/negative/neutral)
- [ ] Auto-respond to 4-5 star reviews
- [ ] Draft responses for 1-3 star reviews (require approval)

#### **B.2 Under 3-Star Review - Customer Verification (NEW!)**
**Priority: HIGH** - Prevent fake/competitor reviews

**Features:**
- [ ] Extract reviewer name from Google review
- [ ] Search customer database for matches:
  - Fuzzy name matching
  - Phone number lookup
  - Email address lookup
  - Event date correlation
- [ ] If NO MATCH found:
  - [ ] AI generates friendly inquiry response:
  ```
  "Thank you for your feedback. We take all reviews seriously and want 
  to make this right. Could you help us identify which event you attended 
  (date or location)? We don't have a record of serving you yet, but we'd 
  love the opportunity to address your concerns and provide the excellent 
  service we're known for. Please contact us at +19167408768 or 
  cs@myhibachichef.com."
  ```
  - [ ] Flag review for manual investigation
  - [ ] Notify Ext. 101 (Suryadi) via SMS
  - [ ] Create admin task to verify legitimacy
  
- [ ] If MATCH found but unexpected low rating:
  - [ ] Load customer event details
  - [ ] AI generates personalized response with event reference
  - [ ] Offer specific compensation (10% off next event)
  - [ ] Immediate escalation to Ext. 101
  - [ ] Create follow-up task in CRM

#### **B.3 Review Response Templates by Rating**
- [ ] 5-star: Enthusiastic thank you + invite back
- [ ] 4-star: Thank you + address any minor concerns mentioned
- [ ] 3-star: Acknowledge + ask for details + offer to improve
- [ ] 2-star: Apologize + verify customer + offer resolution
- [ ] 1-star: Immediate escalation + draft empathetic response

#### **B.4 Review Analytics Dashboard**
- [ ] Average rating trend (weekly/monthly)
- [ ] Response rate tracking (target: 100%)
- [ ] Time-to-respond metrics
- [ ] Keyword frequency analysis
- [ ] Competitor comparison
- [ ] Sentiment trend graph

### **C. Google Maps Integration - Travel Fee Calculator (NEW!)**
**Priority: HIGH** - Auto-pricing for quotes

#### **C.1 Enable Google Maps APIs**
- [ ] Enable Distance Matrix API
- [ ] Enable Geocoding API
- [ ] Enable Places API (for address validation)
- [ ] Configure API key with restrictions

#### **C.2 Travel Fee Calculator Features**
- [ ] Store business base location: `47481 Towhee Street, Fremont, CA 94539`
- [ ] When customer requests quote:
  1. [ ] Validate customer address via Geocoding API
  2. [ ] Calculate distance using Distance Matrix API
  3. [ ] Factor in traffic conditions (real-time)
  4. [ ] Calculate drive time
  5. [ ] Apply pricing rules:
  ```python
  # Travel Fee Calculation (Updated per your request)
  # Business location: 47481 Towhee Street, Fremont, CA 94539 (stored securely in .env)
  
  if distance <= 30 miles:
      travel_fee = 0  # FREE within 30 miles
  else:
      travel_fee = (distance - 30) * 2  # $2 per mile after 30 miles
  
  # Example:
  # - 20 miles → $0 (free)
  # - 30 miles → $0 (free)
  # - 40 miles → $20 (10 miles × $2)
  # - 50 miles → $40 (20 miles × $2)
  # - 80 miles → $100 (50 miles × $2)
  
  # Max distance check
  if distance > 100 miles:
      return "Service area exceeded. Please contact us for special arrangements."
  ```
  6. [ ] Display breakdown to customer:
     - Base event price: $XXX
     - Travel fee: $XX (X miles, Y minutes)
     - Total: $XXX

#### **C.3 Service Area Management**
- [ ] Define service areas:
  - Primary: Fremont, Bay Area (free/low fee)
  - Secondary: Sacramento, Central Valley (moderate fee)
  - Extended: Northern California (high fee)
- [ ] Auto-decline if distance > 100 miles (configurable)
- [ ] Show service area map on website

#### **C.4 Route Optimization (Future)**
- [ ] If multiple events same day:
  - Calculate optimal route
  - Reduce travel fees for clustered events
  - Suggest scheduling based on location

#### **C.5 Database Schema**
```sql
CREATE TABLE travel_calculations (
  id UUID PRIMARY KEY,
  booking_id UUID REFERENCES bookings(id),
  origin_address TEXT,
  destination_address TEXT,
  distance_miles DECIMAL(10,2),
  drive_time_minutes INTEGER,
  traffic_conditions VARCHAR(50),
  calculated_travel_fee INTEGER, -- in cents
  calculation_date TIMESTAMP,
  google_maps_response JSONB
);
```

### **D. Business Info Management**
- [ ] Update business hours programmatically
- [ ] Post updates and announcements
- [ ] Upload event photos automatically
- [ ] Manage Q&A section
- [ ] Respond to customer questions

### **E. Q&A Auto-Response**
- [ ] Monitor Q&A daily
- [ ] AI answers common questions:
  - "Do you cater?" → Yes, details...
  - "What's minimum?" → $100+
  - "Service area?" → Sacramento to Bay Area
  - "Vegetarian options?" → Yes, details...
- [ ] Flag complex questions for human response

### **F. OAuth Connection Flow** (IMPORTANT!)
**No username/password needed!**

Steps to connect:
1. [ ] Backend initiates OAuth flow
2. [ ] User (you) clicks "Connect Google Business" in admin panel
3. [ ] Browser redirects to Google
4. [ ] You authorize the app (one-time)
5. [ ] Google redirects back with authorization code
6. [ ] Backend exchanges code for access token + refresh token
7. [ ] Store tokens encrypted in database
8. [ ] Auto-refresh when token expires (every 1 hour)

**Implementation:**
- [ ] Create `/api/v1/admin/google/connect` endpoint
- [ ] Handle OAuth callback
- [ ] Store tokens securely
- [ ] Implement token refresh logic

---

## 🔐 Production Security Checklist

### **Environment Variables**
- [ ] Use production secrets (not test/sandbox)
- [ ] Store in secure environment (not committed to git)
- [ ] Use secret management service (AWS Secrets Manager / Azure Key Vault)
- [ ] Rotate secrets regularly

### **Webhook Security**
- [ ] Verify webhook signatures (all APIs)
- [ ] Use HTTPS only
- [ ] Implement rate limiting
- [ ] Log all webhook events
- [ ] Retry logic for failed processing

### **API Security**
- [ ] Implement request validation
- [ ] Rate limiting per endpoint
- [ ] API authentication/authorization
- [ ] Input sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention

---

## 🚀 Deployment Checklist

### **Backend Deployment**
- [ ] Choose hosting (AWS / Azure / DigitalOcean / Vercel)
- [ ] Set up domain: myhibachichef.com
- [ ] Configure SSL certificate
- [ ] Set up environment variables
- [ ] Configure database (production)
- [ ] Set up Redis (production)
- [ ] Deploy backend API
- [ ] Test all endpoints

### **Webhook Configuration** (Do After Deployment)
1. [ ] RingCentral webhooks
2. [ ] Meta webhooks (Facebook + Instagram)
3. [ ] Stripe webhooks (already have secret)
4. [ ] Google Business webhooks

### **DNS Configuration**
- [ ] Main domain: myhibachichef.com → Frontend
- [ ] API subdomain: api.myhibachichef.com → Backend
- [ ] Admin subdomain: admin.myhibachichef.com → Admin panel

---

## 📊 Testing Plan

### **Unit Tests**
- [ ] RingCentral SMS send/receive
- [ ] RingCentral call handling
- [ ] Extension routing logic
- [ ] Meta message send/receive
- [ ] Plaid transaction fetching
- [ ] Payment matching algorithm
- [ ] Stripe webhook processing

### **Integration Tests**
- [ ] End-to-end booking flow
- [ ] Payment processing (Stripe + Plaid)
- [ ] AI auto-reply (SMS + Messenger + Instagram)
- [ ] Human escalation flow
- [ ] Review request automation
- [ ] Email notifications

### **Load Testing**
- [ ] API endpoint performance
- [ ] Webhook processing speed
- [ ] Database query optimization
- [ ] Redis caching effectiveness

---

## 📈 Monitoring & Analytics

### **Set Up Monitoring**
- [ ] Application performance monitoring (APM)
- [ ] Error tracking (Sentry / Rollbar)
- [ ] Log aggregation (CloudWatch / Datadog)
- [ ] Uptime monitoring
- [ ] API response time tracking

### **Business Metrics to Track**
- [ ] Total bookings
- [ ] Conversion rate (inquiry → booking)
- [ ] Average response time (AI vs Human)
- [ ] Customer satisfaction score
- [ ] Payment matching accuracy
- [ ] Review sentiment trends
- [ ] Channel performance (SMS vs Messenger vs Instagram)

---

## 🔄 Ongoing Maintenance

### **Daily**
- [ ] Monitor error logs
- [ ] Check unmatched payments
- [ ] Review AI conversation quality
- [ ] Respond to urgent inquiries

### **Weekly**
- [ ] Review payment reconciliation
- [ ] Check API usage and costs
- [ ] Update AI response templates
- [ ] Analyze customer feedback

### **Monthly**
- [ ] Rotate API secrets
- [ ] Review and optimize costs
- [ ] Update documentation
- [ ] Train AI on new conversation patterns
- [ ] Performance optimization

---

## 🎯 Priority Order

1. **🔥 HIGHEST PRIORITY:**
   - Extension management system (for call routing)
   - Plaid payment matching system
   - Webhook setup (all APIs)

2. **HIGH PRIORITY:**
   - Meta app review submission
   - Google Business Profile setup
   - Production deployment

3. **MEDIUM PRIORITY:**
   - AI voice assistant implementation
   - Advanced call routing
   - Analytics dashboard

4. **LOWER PRIORITY:**
   - Advanced features and optimizations
   - Additional integrations
   - Performance tuning

---

**Last Updated:** October 27, 2025  
**Status:** Development credentials complete, ready for feature implementation and production deployment
