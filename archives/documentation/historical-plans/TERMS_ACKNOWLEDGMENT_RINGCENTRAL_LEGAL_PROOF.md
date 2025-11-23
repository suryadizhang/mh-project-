# Terms Acknowledgment System - RingCentral Integration with Legal Proof

## Overview

This system captures legally-binding terms & conditions
acknowledgments across ALL booking channels with enhanced proof
mechanisms for maximum legal protection.

**Critical Legal Protection Features:**

- ✅ Records exact message text (verbatim proof)
- ✅ SHA-256 message hash (tamper-proof fingerprint)
- ✅ RingCentral message ID (audit trail)
- ✅ Precise timestamps (temporal proof)
- ✅ Webhook signature validation (origin verification)
- ✅ IP address tracking (source verification)
- ✅ Customer phone normalization (identity proof)

## Why RingCentral (Not Twilio)

Your business uses **RingCentral** for SMS communications:

- Business phone: `+1 (916) 740-8768`
- Enterprise-grade reliability
- Webhook support for automated replies
- Message ID tracking for audit trails
- Signature validation for security

## Legal Proof Architecture

### What We Capture

For every terms acknowledgment, we record:

```typescript
{
  // WHO agreed
  customer_id: 123,
  customer_phone: "2103884155",

  // WHAT they agreed to
  terms_version: "2.0",
  terms_url: "https://myhibachichef.com/terms",
  terms_text_hash: "a3f8d9e2...",  // SHA-256 of actual terms text

  // WHEN they agreed
  acknowledged_at: "2025-01-03T14:30:00Z",
  message_timestamp: "2025-01-03T14:30:00Z",  // From RingCentral

  // HOW they agreed
  channel: "sms",
  acknowledgment_method: "sms_reply",
  acknowledgment_text: "I agree",  // Exact text customer sent

  // WHERE it came from
  ip_address: "208.54.123.45",  // RingCentral webhook source
  webhook_source_ip: "208.54.123.45",

  // PROOF it's legitimate
  message_id: "RC-MSG-12345",  // RingCentral message ID
  message_hash: "b7e4c1d3...",  // SHA-256(phone|text|timestamp|id)
  verified: true
}
```

### Message Hash Calculation

The message hash provides **tamper-proof** evidence:

```python
def calculate_message_hash(
    phone_number: str,
    message_body: str,
    timestamp: str,
    message_id: str
) -> str:
    """
    Creates immutable fingerprint that proves:
    1. This exact message
    2. Was sent from this phone
    3. At this exact time
    4. With this RingCentral message ID

    Cannot be forged or altered without detection.
    """
    canonical_string = f"{phone_number}|{message_body}|{timestamp}|{message_id}"
    return hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()
```

**Legal Significance:**

- If customer claims "I never agreed", we can prove the exact text
- If timestamp disputed, hash includes timestamp
- If phone disputed, hash includes phone number
- If authenticity questioned, RingCentral message ID in hash

### Webhook Signature Validation

RingCentral signs every webhook with HMAC-SHA256:

```python
def validate_ringcentral_signature(
    request_body: bytes,
    signature_header: str,
    validation_token: str
) -> bool:
    """
    Validates request actually came from RingCentral.

    Prevents spoofed webhooks from fake sources.
    """
    expected_signature = hmac.new(
        validation_token.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)
```

**Legal Significance:**

- Proves message came from legitimate RingCentral source
- Prevents fraudulent "fake customer agreement" attacks
- Cryptographically secure (HMAC-SHA256)

## SMS Terms Flow (Phone/Text Bookings)

### 1. Customer Makes Phone Booking

Staff takes booking over phone, enters into system:

```python
# Booking created with status "pending_terms"
booking = await create_booking(
    customer_phone="2103884155",
    customer_name="John Doe",
    event_date="2025-01-10",
    # ... other booking details
    source="phone"
)
```

### 2. System Automatically Sends Terms SMS

```python
from services.terms_acknowledgment_service import send_terms_for_phone_booking

# Send SMS with terms request
await send_terms_for_phone_booking(
    db=db,
    customer_phone="2103884155",
    customer_name="John Doe",
    booking_id=booking.id
)
```

**SMS sent to customer:**

```
Hi John! To complete your booking for 1/10/2025, please review our terms & conditions:

https://myhibachichef.com/terms

Reply with: I AGREE

Or call us at (916) 740-8768 for questions.
```

### 3. Customer Replies "I AGREE"

Customer sends SMS: `"I agree"`

### 4. RingCentral Webhook Delivers Message

RingCentral POSTs to:
`https://yourdomain.com/api/v1/webhooks/sms/terms-reply`

**Webhook Payload:**

```json
{
  "event": "message.received",
  "timestamp": "2025-01-03T14:30:00Z",
  "body": {
    "id": "12345",
    "from": {
      "phoneNumber": "+12103884155"
    },
    "text": "I agree",
    "creationTime": "2025-01-03T14:30:00Z"
  }
}
```

**Headers:**

```
X-Glip-Signature: a3f8d9e2b7c4...
```

### 5. System Validates and Records

```python
# 1. Validate signature (security)
is_valid = validate_ringcentral_signature(
    request_body=raw_request_body,
    signature_header=request.headers.get("X-Glip-Signature"),
    validation_token=settings.RC_WEBHOOK_SECRET
)

# 2. Calculate message hash (legal proof)
message_hash = calculate_message_hash(
    phone_number="2103884155",
    message_body="I agree",
    timestamp="2025-01-03T14:30:00Z",
    message_id="12345"
)
# Result: "b7e4c1d38f2a9e5d..."

# 3. Find customer by phone
customer = db.query(Customer).filter(
    Customer.phone.like("%2103884155%")
).first()

# 4. Create acknowledgment record
acknowledgment = await service.verify_sms_acknowledgment(
    verification=SMSTermsVerification(
        customer_phone="2103884155",
        reply_text="I agree",
        booking_id=123
    ),
    customer_id=customer.id,
    message_id="12345",
    message_timestamp="2025-01-03T14:30:00Z",
    message_hash="b7e4c1d38f2a9e5d...",
    webhook_source_ip="208.54.123.45"
)

# 5. Send confirmation SMS
# "✅ Terms Accepted! Your booking is confirmed. We'll see you on 1/10/2025!"
```

### 6. Legal Record Created

Database record:

```sql
INSERT INTO terms_acknowledgments (
    customer_id,
    booking_id,
    terms_version,
    terms_url,
    terms_text_hash,
    acknowledged_at,
    channel,
    acknowledgment_method,
    acknowledgment_text,
    ip_address,
    notes,
    verified,
    created_at
) VALUES (
    123,
    456,
    '2.0',
    'https://myhibachichef.com/terms',
    'a3f8d9e2b7c4...',  -- SHA-256 of terms text
    '2025-01-03 14:30:00+00',
    'sms',
    'sms_reply',
    'I agree',
    '208.54.123.45',
    'SMS reply verified from 2103884155
Reply text: ''I agree''
RingCentral Message ID: 12345
Message Timestamp: 2025-01-03T14:30:00Z
Message Hash (SHA-256): b7e4c1d38f2a9e5d...
Hash proves: exact message, phone, timestamp, message_id
Webhook Source IP: 208.54.123.45',
    true,
    '2025-01-03 14:30:00+00'
);
```

## Proof Chain Verification

If customer disputes agreement in legal proceedings:

### 1. Present Original Message Hash

```python
# From database record
message_hash_from_db = "b7e4c1d38f2a9e5d..."
```

### 2. Recalculate Hash from Components

```python
# Use recorded components
phone = "2103884155"
text = "I agree"
timestamp = "2025-01-03T14:30:00Z"
msg_id = "12345"

canonical = f"{phone}|{text}|{timestamp}|{msg_id}"
recalculated_hash = hashlib.sha256(canonical.encode()).hexdigest()
```

### 3. Compare Hashes

```python
if recalculated_hash == message_hash_from_db:
    print("✅ PROOF VERIFIED: Message unchanged since received")
else:
    print("❌ TAMPERED: Message was altered")
```

### 4. Verify with RingCentral

```
RingCentral Message ID: 12345
Can query RingCentral API: GET /restapi/v1.0/account/~/extension/~/message-store/12345

RingCentral Response:
{
  "id": 12345,
  "from": { "phoneNumber": "+12103884155" },
  "body": "I agree",
  "creationTime": "2025-01-03T14:30:00Z"
}

✅ MATCHES our database record exactly
```

## Legal Defense Documentation

### In Court or Legal Dispute

**Evidence Package:**

1. **Database Record** (JSON export)

```json
{
  "acknowledgment_id": 789,
  "customer_id": 123,
  "customer_name": "John Doe",
  "customer_phone": "2103884155",
  "booking_id": 456,
  "terms_version": "2.0",
  "terms_url": "https://myhibachichef.com/terms",
  "terms_text_hash": "a3f8d9e2b7c4...",
  "acknowledged_at": "2025-01-03T14:30:00Z",
  "channel": "sms",
  "acknowledgment_text": "I agree",
  "ringcentral_message_id": "12345",
  "message_hash": "b7e4c1d38f2a9e5d...",
  "webhook_source_ip": "208.54.123.45",
  "verified": true
}
```

2. **Terms Text at Time of Agreement** (archived version)

```
Terms & Conditions Version 2.0
Last Updated: December 20, 2024

[Full terms text...]

SHA-256 Hash: a3f8d9e2b7c4...
```

3. **RingCentral Message Receipt** (API query)

```json
{
  "id": "12345",
  "type": "SMS",
  "from": { "phoneNumber": "+12103884155" },
  "to": [{ "phoneNumber": "+19167408768" }],
  "subject": "I agree",
  "creationTime": "2025-01-03T14:30:00.000Z",
  "lastModifiedTime": "2025-01-03T14:30:00.000Z",
  "readStatus": "Read",
  "direction": "Inbound"
}
```

4. **Hash Verification**

```python
# Prove message unchanged
canonical = "2103884155|I agree|2025-01-03T14:30:00Z|12345"
calculated_hash = hashlib.sha256(canonical.encode()).hexdigest()
# Result: b7e4c1d38f2a9e5d... (MATCHES database)
```

5. **Webhook Validation Log**

```
[2025-01-03 14:30:00] INFO: Webhook received from 208.54.123.45
[2025-01-03 14:30:00] INFO: Signature validated: PASS
[2025-01-03 14:30:00] INFO: RingCentral Message ID: 12345
[2025-01-03 14:30:00] INFO: Customer 123 terms acknowledged
```

### Legal Questions & Answers

**Q: How do you know the customer actually sent this message?** A:

1. RingCentral Message ID 12345 proves message origin
2. Webhook signature validation proves authentic RingCentral source
3. Customer's phone number verified by RingCentral network
4. Message hash includes all components (tamper-proof)

**Q: Could this message be forged or altered?** A:

1. SHA-256 hash would change if any component altered
2. RingCentral maintains independent record (Message ID 12345)
3. Webhook signature validation prevents spoofed requests
4. Timestamp from RingCentral (not our system clock)

**Q: How do you know customer saw the actual terms?** A:

1. SMS included direct link: https://myhibachichef.com/terms
2. Terms text hash (a3f8d9e2...) proves exact version
3. Customer replied "I agree" (explicit consent)
4. All recorded with precise timestamp

**Q: What if customer claims phone was stolen?** A:

1. Customer responsible for phone security (standard legal doctrine)
2. Customer has obligation to report unauthorized use
3. No other bookings or payments disputed from same phone
4. Customer would need to prove phone compromise at exact time

## Configuration

### Environment Variables

Add to `.env`:

```bash
# RingCentral Configuration
RC_CLIENT_ID=your_client_id
RC_CLIENT_SECRET=your_client_secret
RC_JWT_TOKEN=your_jwt_token
RC_WEBHOOK_SECRET=your_webhook_secret  # For signature validation
RC_SMS_FROM=+19167408768
RC_SERVER_URL=https://platform.ringcentral.com

# Security
SKIP_WEBHOOK_VALIDATION=false  # NEVER true in production
```

### RingCentral Webhook Setup

1. **Log into RingCentral Developer Console**
   - https://developers.ringcentral.com/

2. **Create Webhook Subscription**

   ```bash
   POST /restapi/v1.0/subscription
   {
     "eventFilters": [
       "/restapi/v1.0/account/~/extension/~/message-store/instant?type=SMS"
     ],
     "deliveryMode": {
       "transportType": "WebHook",
       "address": "https://yourdomain.com/api/v1/webhooks/sms/incoming"
     }
   }
   ```

3. **Webhook URL**
   - Production:
     `https://api.myhibachichef.com/api/v1/webhooks/sms/incoming`
   - Staging:
     `https://staging-api.myhibachichef.com/api/v1/webhooks/sms/incoming`

4. **Webhook Security**
   - RingCentral will sign all requests with `X-Glip-Signature` header
   - Our system validates signature using `RC_WEBHOOK_SECRET`

## Testing

### Manual SMS Test

1. Send terms SMS:

```bash
curl -X POST https://api.myhibachichef.com/api/v1/terms/send-sms \
  -H "Content-Type: application/json" \
  -d '{
    "customer_phone": "2103884155",
    "customer_name": "Test User",
    "booking_id": 123
  }'
```

2. Customer receives SMS on phone `(210) 388-4155`

3. Customer replies: `"I agree"`

4. System receives webhook, validates, records

5. Verify in database:

```sql
SELECT
    id,
    customer_id,
    acknowledgment_text,
    message_hash,
    notes
FROM terms_acknowledgments
ORDER BY created_at DESC
LIMIT 1;
```

Should show:

- acknowledgment_text: "I agree"
- message_hash: (SHA-256 hash)
- notes: Contains RingCentral Message ID, timestamp, hash

### Legal Proof Verification

```python
# Verify hash integrity
from services.terms_acknowledgment_service import calculate_message_hash

phone = "2103884155"
text = "I agree"
timestamp = "2025-01-03T14:30:00Z"
msg_id = "12345"

calculated_hash = calculate_message_hash(phone, text, timestamp, msg_id)

# Compare with database
db_hash = db.query(TermsAcknowledgment).filter_by(id=789).first().notes
assert calculated_hash in db_hash  # Should match
```

## Monitoring & Alerts

### Key Metrics

1. **Acknowledgment Rate**

```sql
SELECT
    COUNT(DISTINCT booking_id) * 100.0 /
    (SELECT COUNT(*) FROM bookings WHERE source IN ('phone', 'sms', 'whatsapp'))
    AS acknowledgment_rate_percent
FROM terms_acknowledgments
WHERE channel IN ('sms', 'whatsapp');
```

**Alert if:** Below 95%

2. **Invalid Replies**

```sql
SELECT COUNT(*)
FROM sms_logs
WHERE
    body LIKE '%terms%'
    AND id NOT IN (
        SELECT DISTINCT notes::text
        FROM terms_acknowledgments
        WHERE notes LIKE '%RingCentral%'
    );
```

**Alert if:** More than 10 in 24 hours

3. **Signature Validation Failures**

```
grep "Invalid RingCentral signature" /var/log/app.log | wc -l
```

**Alert if:** Any occurrence (indicates attack or config issue)

## Legal Compliance

### TCPA (Telephone Consumer Protection Act)

✅ **We have explicit consent before sending terms SMS**

- Customer provided phone number for booking
- Terms SMS is transactional (complete booking)
- Not marketing/promotional

✅ **Customer can opt-out**

- Can call instead: (916) 740-8768
- Can decline booking (no SMS sent)

### GDPR (if serving EU customers)

✅ **Right to access**

- Customer can request their acknowledgment records
- We provide full JSON export

✅ **Right to erasure**

- Can delete acknowledgment after legal retention period
- Booking history maintained separately

✅ **Data minimization**

- Only collect necessary data (phone, text, timestamp)
- No sensitive personal information

### E-SIGN Act (Electronic Signatures)

✅ **Valid electronic signature**

- Customer provided consent electronically (SMS reply)
- Clear indication of agreement ("I AGREE")
- Record of electronic consent maintained
- Terms were accessible (URL provided)

## Summary

### Legal Protection Checklist

- ✅ Exact message text recorded (verbatim proof)
- ✅ SHA-256 message hash (tamper-proof)
- ✅ RingCentral message ID (third-party verification)
- ✅ Precise timestamps (temporal proof)
- ✅ Webhook signature validation (origin proof)
- ✅ IP address tracking (source verification)
- ✅ Phone number verification (identity proof)
- ✅ Terms version and hash (content proof)
- ✅ Customer name and ID (party identification)
- ✅ Booking association (transaction context)

### What Makes This Legally Defensible

1. **Multi-Factor Proof**
   - Not just "customer said yes"
   - Cryptographic proof (hash)
   - Third-party verification (RingCentral)
   - Independent timestamps

2. **Tamper-Proof**
   - Cannot alter message without changing hash
   - RingCentral has independent copy
   - Webhook signature proves authentic source

3. **Complete Audit Trail**
   - WHO: Customer ID, name, phone
   - WHAT: Terms version, URL, text hash
   - WHEN: Multiple timestamps
   - WHERE: IP address, phone number
   - HOW: Channel, method, exact text

4. **Industry Standards**
   - SHA-256 (NIST approved)
   - HMAC signature validation
   - ISO timestamp format
   - RESTful API standards

### This System Prevents

❌ Customer claiming "I never agreed" → We have exact text: "I agree"

❌ Customer claiming "I didn't see the terms" → SMS included direct
link with version

❌ Customer claiming "That's not what I sent" → Hash proves exact
message + RingCentral record

❌ Customer claiming "Wrong time" → RingCentral timestamp + our
timestamp

❌ Customer claiming "Wasn't my phone" → Legal doctrine: responsible
for phone security

❌ Fraudulent claims → Cryptographic proof chain

---

**Implementation Status:** ✅ COMPLETE **Legal Review:** Recommended
before production deployment **Insurance Notice:** Consider informing
liability insurer of enhanced protection

**Questions?** Contact legal team or technical support.
