# My Hibachi – Business Glossary

**Purpose:** Define business terms used throughout the codebase
**Audience:** Developers, AI agents, new team members

---

## 📖 Core Business Terms

### Booking

A confirmed reservation for hibachi catering service.

| Field               | Meaning                                |
| ------------------- | -------------------------------------- |
| `date`              | Event date (not booking creation date) |
| `slot`              | Event start time (e.g., 6:00 PM)       |
| `party_adults`      | Number of adults (min 10)              |
| `party_kids`        | Number of children 5-12                |
| `deposit_due_cents` | Required deposit in cents              |
| `total_due_cents`   | Full event cost in cents               |
| `status`            | Booking lifecycle state                |

**Booking Statuses:** | Status | Meaning | |--------|---------| |
`pending` | Just created, awaiting deposit | | `deposit_pending` |
Deposit requested but not paid | | `deposit_paid` | Deposit received,
booking secured | | `confirmed` | Fully confirmed, chef assigned | |
`in_progress` | Event is happening now | | `completed` | Event
finished successfully | | `cancelled` | Customer or admin cancelled |
| `no_show` | Customer didn't show up |

---

### Customer

A person who books or has booked our service.

| Field                     | Meaning                      |
| ------------------------- | ---------------------------- |
| `first_name`, `last_name` | Customer name                |
| `email`                   | Primary contact email        |
| `phone`                   | Primary phone (for SMS)      |
| `sms_consent`             | TCPA compliance flag         |
| `booking_count`           | Total bookings (for loyalty) |
| `total_spend_cents`       | Lifetime spend               |

---

### Lead

A potential customer who hasn't booked yet.

**Lead Sources:** | Source | Meaning | |--------|---------| |
`WEB_QUOTE` | Used quote calculator | | `WEB_CONTACT` | Filled contact
form | | `CHAT` | Interacted with AI chat | | `PHONE` | Called our
number | | `SMS` | Texted our number | | `INSTAGRAM` | DM on Instagram
| | `FACEBOOK` | Message on Facebook | | `REFERRAL` | Referred by
existing customer |

**Lead Statuses:** | Status | Meaning | |--------|---------| | `new` |
Just captured, not contacted | | `contacted` | We reached out | |
`qualified` | Good fit, likely to book | | `negotiating` | Discussing
dates/pricing | | `converted` | Became a booking! | | `lost` | Did not
convert |

**Lead Quality:** | Quality | Meaning | |---------|---------| | `hot`
| Ready to book (contact ASAP) | | `warm` | Interested, needs
follow-up | | `cold` | Low intent, nurture list |

---

### Chef

A hibachi chef (independent contractor) who performs events.

| Field        | Meaning                       |
| ------------ | ----------------------------- |
| `name`       | Chef's display name           |
| `phone`      | Contact number                |
| `station_id` | Home station (for scheduling) |
| `is_active`  | Available for bookings        |
| `rating`     | Performance rating (1-5)      |

---

### Station

A geographic service location (business hub).

| Field            | Meaning                             |
| ---------------- | ----------------------------------- |
| `name`           | Station name (e.g., "Fremont")      |
| `address`        | Base address for travel calculation |
| `free_miles`     | Miles included in base price        |
| `price_per_mile` | Travel fee beyond free miles        |
| `is_active`      | Station accepting bookings          |

**Current Station:** Fremont, CA (47481 Towhee St)

---

## 💰 Pricing Terms

### Quote

An estimated price shown to customer before booking.

**Quote Components:** | Component | Calculation |
|-----------|-------------| | `base_total` | (adults × $55) + (kids ×
$30) | | `upgrades` | Filet (+$15/person), Lobster (+$25/person) | |
`travel_fee` | (miles - 30) × $2 if beyond free miles | | `subtotal` |
base + upgrades + travel | | `gratuity` | subtotal × 20% | | `total` |
subtotal + gratuity |

### Deposit

Upfront payment to secure booking.

| Rule       | Value               |
| ---------- | ------------------- |
| Minimum    | $100                |
| Percentage | 25% of total        |
| Applied    | Whichever is higher |

### Travel Fee

Extra charge for events far from station.

| Rule          | Value              |
| ------------- | ------------------ |
| Free miles    | 30 miles           |
| Per mile rate | $2.00              |
| Example       | 45 miles = $30 fee |

---

## 🔐 Access & Permissions

### RBAC (Role-Based Access Control)

4-tier permission system.

| Tier | Role        | Access                           |
| ---- | ----------- | -------------------------------- |
| 0    | Guest       | Public pages only                |
| 1    | Staff       | View bookings, basic CRM         |
| 2    | Admin       | Full operations, chef management |
| 3    | Super Admin | System config, RBAC, logs        |

### JWT (JSON Web Token)

Authentication token for API access.

### API Key

Service-to-service authentication (for integrations).

---

## 📊 Analytics Terms

### Funnel

Customer journey from awareness to booking.

**Funnel Stages:**

1. `visit` - Landed on website
2. `quote` - Used quote calculator
3. `availability` - Checked available dates
4. `booking_started` - Began booking form
5. `booking_completed` - Submitted booking
6. `deposit_paid` - Paid deposit
7. `event_completed` - Successful event

### Lead Event

A tracked action in the lead's journey.

| Event Type                    | Meaning                      |
| ----------------------------- | ---------------------------- |
| `lead_created`                | New lead captured            |
| `funnel_checked_availability` | Selected date/time           |
| `funnel_started_booking`      | Clicked "Book Now"           |
| `funnel_completed_booking`    | Submitted form               |
| `funnel_dropped`              | Abandoned without completing |

---

## 🤖 AI Terms

### Conversation

An AI chat session with a customer.

### Escalation

When AI transfers to human support.

**Escalation Triggers:**

- Complex questions
- Complaints
- Payment issues
- Custom requests

### Knowledge Base

Structured information the AI uses to answer questions.

---

## 📞 Communication Terms

### Thread

A conversation with a customer across any channel.

### Channel

Communication method.

| Channel     | Description         |
| ----------- | ------------------- |
| `SMS`       | Text message        |
| `EMAIL`     | Email               |
| `PHONE`     | Voice call          |
| `WEB_CHAT`  | Website chat widget |
| `INSTAGRAM` | Instagram DM        |
| `FACEBOOK`  | Facebook Messenger  |

### TCPA

Telephone Consumer Protection Act - requires SMS consent.

---

## 🔗 Related Documents

- [PRD](./PRD.md) - Product requirements
- [ERD](../01-ARCHITECTURE/ERD.md) - Database relationships
- [Data Dictionary](../02-IMPLEMENTATION/DATA_DICTIONARY.md) - All
  fields explained
