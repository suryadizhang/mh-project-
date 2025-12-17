# My Hibachi Web App – Product Requirements Document (PRD)

**Last Updated:** December 16, 2025 **Status:** Active **Version:**
1.0

---

## 🎯 Product Vision

My Hibachi is a **premium hibachi catering service** that brings the
restaurant experience to customers' homes. This web application
powers:

1. **Customer booking flow** – Quote → Availability → Book → Pay
2. **Admin operations** – Booking management, chef scheduling, CRM
3. **AI assistance** – Chat, voice, automated responses
4. **Business intelligence** – Analytics, funnel tracking, marketing

---

## 👥 User Types

| User Type       | Description                          | Access                                       |
| --------------- | ------------------------------------ | -------------------------------------------- |
| **Guest**       | Public visitor, potential customer   | Public pages, quote calculator, booking form |
| **Customer**    | Registered user with booking history | Customer portal, past bookings, invoices     |
| **Chef**        | Hibachi chef (contractor)            | Chef schedule, assigned bookings, earnings   |
| **Staff**       | Office/support team                  | Admin panel (limited), customer support      |
| **Admin**       | Operations manager                   | Full admin panel, reports, chef management   |
| **Super Admin** | Business owner/developer             | Everything + system config, RBAC, logs       |

---

## 🏗️ Application Structure

### Customer Site (apps/customer)

Public-facing Next.js application for booking and information.

| Page         | Purpose                                         | Priority    |
| ------------ | ----------------------------------------------- | ----------- |
| `/`          | Homepage – Hero, value proposition, quick quote | 🔴 Critical |
| `/menu`      | Menu display with pricing                       | 🔴 Critical |
| `/quote`     | Interactive price calculator                    | 🔴 Critical |
| `/BookUs`    | Full booking form with payment                  | 🔴 Critical |
| `/faqs`      | Frequently asked questions                      | 🟠 High     |
| `/blog`      | SEO content, recipes, tips                      | 🟡 Medium   |
| `/locations` | Service areas (SF Bay Area)                     | 🟡 Medium   |
| `/reviews`   | Customer testimonials                           | 🟡 Medium   |
| `/contact`   | Contact form, phone, email                      | 🟠 High     |

### Admin Panel (apps/admin)

Internal Next.js application for operations.

| Section         | Purpose                                | Access Level |
| --------------- | -------------------------------------- | ------------ |
| `/dashboard`    | Overview, today's bookings, alerts     | Staff+       |
| `/bookings`     | Booking management CRUD                | Staff+       |
| `/customers`    | CRM, customer profiles                 | Staff+       |
| `/chefs`        | Chef management, scheduling            | Admin+       |
| `/leads`        | Lead pipeline, follow-ups              | Staff+       |
| `/inbox`        | Unified messaging (SMS, email, social) | Staff+       |
| `/reports`      | Analytics, revenue, performance        | Admin+       |
| `/superadmin/*` | RBAC, logs, system config              | Super Admin  |

### Backend API (apps/backend)

FastAPI Python application powering all business logic.

| Domain                | Endpoints                    | Description |
| --------------------- | ---------------------------- | ----------- |
| `/api/v1/public/*`    | Quote, availability, booking | Public API  |
| `/api/v1/bookings/*`  | Booking CRUD, status updates | Protected   |
| `/api/v1/customers/*` | Customer management          | Protected   |
| `/api/v1/leads/*`     | Lead tracking, funnel events | Protected   |
| `/api/v1/chefs/*`     | Chef schedules, assignments  | Admin       |
| `/api/v1/payments/*`  | Stripe integration           | Protected   |
| `/api/v1/admin/*`     | Admin operations             | Admin+      |

---

## 🎯 Core Features by Batch

### Batch 1: Core Booking + Security ✅ (Current)

- [x] Quote calculator with dynamic pricing
- [x] Booking form with validation
- [x] Chef availability checking
- [x] Customer CRUD
- [x] 4-tier RBAC (Guest, Staff, Admin, Super Admin)
- [x] JWT + API key authentication
- [x] Audit trail logging
- [x] Lead funnel tracking

### Batch 2: Payment Processing (Upcoming)

- [ ] Stripe payment intents
- [ ] Deposit collection ($100 minimum)
- [ ] Invoice generation
- [ ] Refund processing
- [ ] Dynamic pricing admin

### Batch 3: Core AI

- [ ] AI chat assistant (booking help)
- [ ] Smart escalation to humans
- [ ] Knowledge base integration
- [ ] OpenAI integration

### Batch 4: Communications

- [ ] RingCentral SMS/Voice
- [ ] WhatsApp Business
- [ ] Facebook/Instagram DMs
- [ ] Unified inbox

### Batch 5: Advanced AI + Marketing

- [ ] Sentiment analysis
- [ ] Automated follow-ups
- [ ] Review management
- [ ] Marketing intelligence

### Batch 6: AI Training & Scaling

- [ ] Multi-LLM ensemble
- [ ] Shadow learning
- [ ] Loyalty program
- [ ] Multi-station support

---

## 💰 Business Rules

### Pricing Structure

| Item                 | Price       | Notes               |
| -------------------- | ----------- | ------------------- |
| Base per adult       | $55         | Minimum 10 adults   |
| Base per kid (5-12)  | $30         | Under 5 free        |
| Filet mignon upgrade | +$15/person | Optional            |
| Lobster upgrade      | +$25/person | Optional            |
| Travel fee           | $2/mile     | After 30 free miles |
| Gratuity             | 20%         | Auto-calculated     |

### Booking Rules

- **Minimum guests:** 10 adults
- **Deposit:** $100 or 25% (whichever higher)
- **Cancellation:** 48 hours notice for refund
- **Service area:** SF Bay Area (30-mile radius from Fremont)

---

## 🚫 Out of Scope (Explicitly NOT Building)

| Feature                 | Reason                 |
| ----------------------- | ---------------------- |
| Mobile native apps      | Web-first, PWA later   |
| Multi-tenant SaaS       | Single business focus  |
| Real-time chef tracking | Unnecessary complexity |
| Customer loyalty points | Deferred to Batch 6    |
| Gift cards              | Future consideration   |

---

## 📊 Success Metrics

| Metric                  | Target         | Measurement        |
| ----------------------- | -------------- | ------------------ |
| Quote-to-booking rate   | >15%           | Funnel tracking    |
| Page load time          | <3s            | Lighthouse         |
| Booking completion rate | >80%           | Once started       |
| Customer satisfaction   | >4.5/5         | Post-event surveys |
| Admin task time         | <5 min/booking | Time tracking      |

---

## 🔗 Related Documents

- [Architecture](../01-ARCHITECTURE/ARCHITECTURE.md)
- [ERD](../01-ARCHITECTURE/ERD.md)
- [Data Flow](../01-ARCHITECTURE/DATA_FLOW.md)
- [Batch Strategy](../04-DEPLOYMENT/DEPLOYMENT_BATCH_STRATEGY.md)
