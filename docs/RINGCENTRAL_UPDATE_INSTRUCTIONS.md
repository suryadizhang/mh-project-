# RingCentral Application Update Instructions

## RINGCENTRAL DEVELOPER PORTAL UPDATE

### Login Information:

- Portal: https://developers.ringcentral.com/
- Account: [Your existing RingCentral developer account]

### CRITICAL: SMS Campaign Compliance Requirements

Based on rejection of Campaign C43VV7B, the following must be fixed:

1. **NO EMOJIS ALLOWED** in any campaign field (Rejection Code 6103)
2. **OPT-IN FORM MUST LIST MESSAGE TYPES** (Rejection Code 2114)

### Required Updates:

#### 1. Application Settings Update (NO EMOJIS)

```
Business Email: cs@myhibachichef.com
Company: My Hibachi LLC
```

#### 2. SMS Compliance URLs (CRITICAL)

```
Privacy Policy URL: https://myhibachichef.com/privacy
Terms & Conditions URL: https://myhibachichef.com/terms
```

#### 3. Application Description Update (NO EMOJIS - PLAIN TEXT ONLY)

```
Application Name: My Hibachi Chef CRM

Description: Customer relationship management system for hibachi catering business.
Handles booking confirmations, event reminders, and customer support via SMS.

SMS Message Types Sent to Customers:
- Booking confirmation messages with order details and confirmation numbers
- Event reminder messages sent 48 hours and 24 hours before scheduled events
- Chef arrival and status notification messages
- Customer support response messages
- Important booking change and update alerts
- Account and service-related notifications

SMS Use Cases:
- Booking confirmations (transactional)
- Event reminders 24-48 hours before service (transactional)
- Chef arrival notifications (transactional)
- Customer support responses (transactional)
- Optional promotional offers (promotional - with explicit opt-in only)
```

#### 4. Opt-In/Call-To-Action Description (REQUIRED - NO EMOJIS)

```
Opt-In Process Description:
Customers provide SMS consent during the online booking process at https://myhibachichef.com/BookUs/

The opt-in form clearly states the following message types customers will receive:
- Booking confirmations with deposit payment instructions
- Event reminders (48 hours and 24 hours before scheduled event)
- Chef arrival and status notifications
- Customer support responses to inquiries
- Important booking updates and changes
- Account and service-related notifications

Consent Language:
"I agree to receive text messages from My Hibachi Chef including booking confirmations,
event reminders, chef arrival notifications, customer support responses, and booking updates.
Message frequency varies. Message and data rates may apply. Reply STOP to opt-out anytime."

Opt-Out Instructions:
- Reply STOP to unsubscribe from all messages
- Reply START to re-subscribe
- Reply HELP for assistance
- Contact: (916) 740-8768 or https://myhibachichef.com/contact
```

#### 5. Sample Messages (NO EMOJIS - PLAIN TEXT)

```
Sample Booking Confirmation:
"My Hibachi Chef: Your booking #12345 is confirmed for Nov 15 at 6:00 PM.
10 guests at 123 Main St, Sacramento CA. Reply STOP to opt-out."

Sample Event Reminder:
"My Hibachi Chef: Reminder - Your hibachi event is tomorrow at 6:00 PM.
Your chef will arrive 30 minutes early. Reply STOP to opt-out."

Sample Chef Arrival:
"My Hibachi Chef: Your chef is on the way and will arrive in approximately 15 minutes.
Reply STOP to opt-out."
```

#### 6. Technical Details

```
Webhook URL: https://mhapi.mysticdatanode.net/webhooks/ringcentral
OAuth Redirect URI: https://mhapi.mysticdatanode.net/auth/ringcentral/callback
```

#### 7. Compliance Verification Checklist

- [x] Privacy Policy includes SMS consent language
- [x] Privacy Policy states: "We do not share your SMS consent with
      third parties"
- [x] Terms page includes STOP/START/HELP instructions
- [x] Terms page lists all message types
- [x] Business email is not Gmail (cs@myhibachichef.com)
- [x] All pages accessible and properly formatted
- [x] Opt-in form lists specific message types customers will receive
- [x] NO EMOJIS in any campaign field or description

### SUBMISSION NOTES:

- Application is for business SMS communications only
- All messages are transactional or explicitly opted-in promotional
- Full TCPA compliance with STOP/START/HELP support
- Privacy policy exceeds RingCentral requirements
- Opt-in form clearly describes message types per rejection code 2114
- No emojis in any campaign fields per rejection code 6103

### ESTIMATED APPROVAL TIME: 3-5 business days
