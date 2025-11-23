# 🎯 Phone Number Unification - Visual Flow

## Scenario: Customer Journey Across 3 Channels

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER: John Doe                               │
│                     Phone: (916) 555-1234                                 │
└──────────────────────────────────────────────────────────────────────────┘

DAY 1: Instagram DM
═══════════════════════════════════════════════════════════════════════════

┌─────────────┐                                      ┌──────────────────┐
│  Instagram  │  "Hi! Book for 6 people"            │  Your Instagram  │
│             │  "My number is (916) 555-1234" ────▶│  Business Page   │
│  @johndoe   │                                      │  @myhibachisac   │
└─────────────┘                                      └──────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  WEBHOOK RECEIVED                                │
          │  ─────────────────                               │
          │  Platform: instagram                             │
          │  Sender: @johndoe                                │
          │  Content: "Hi! Book... (916) 555-1234"          │
          └──────────────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  PHONE EXTRACTION (Auto)                         │
          │  ────────────────────────                        │
          │  Regex: Extract "(916) 555-1234"                │
          │  Normalize: → "+19165551234" (E.164)            │
          └──────────────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  DATABASE SEARCH                                 │
          │  ───────────────                                 │
          │  SELECT * FROM customers                         │
          │  WHERE phone = '+19165551234'                    │
          │                                                  │
          │  Result: NOT FOUND (New Customer)               │
          └──────────────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  CREATE CUSTOMER                                 │
          │  ───────────────                                 │
          │  id: 550e8400-e29b-41d4-a716-446655440000       │
          │  phone: +19165551234                             │
          │  name: @johndoe                                  │
          │  source: instagram                               │
          └──────────────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  CREATE SOCIAL IDENTITY                          │
          │  ──────────────────────                          │
          │  platform: instagram                             │
          │  handle: johndoe                                 │
          │  customer_id: 550e8400-... (linked!)            │
          │  confidence_score: 0.95                          │
          └──────────────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────────────────────────────────────┐
          │  CREATE SOCIAL THREAD                            │
          │  ──────────────────                              │
          │  platform: instagram                             │
          │  customer_id: 550e8400-... (linked!)            │
          │  status: open                                    │
          └──────────────────────────────────────────────────┘
```

**DATABASE STATE AFTER DAY 1:**

All conversations → ONE customer → ONE timeline via SAME phone number! 🎉
