# RingCentral Application Update Instructions

## 🎯 RINGCENTRAL DEVELOPER PORTAL UPDATE

### Login Information:
- Portal: https://developers.ringcentral.com/
- Account: [Your existing RingCentral developer account]

### Required Updates:

#### 1. Application Settings Update
```
Business Email: cs@myhibachichef.com
Company: My Hibachi LLC
```

#### 2. SMS Compliance URLs (CRITICAL)
```
Privacy Policy URL: https://myhibachichef.com/privacy
Terms & Conditions URL: https://myhibachichef.com/terms
```

#### 3. Application Description Update
```
Application Name: My Hibachi Chef CRM
Description: Customer relationship management system for hibachi catering business. 
Handles booking confirmations, event reminders, and customer support via SMS.

SMS Use Cases:
- Booking confirmations (transactional)
- Event reminders 24-48 hours before service (transactional)
- Chef arrival notifications (transactional)  
- Customer support responses (transactional)
- Optional promotional offers (promotional - with explicit opt-in only)
```

#### 4. Technical Details
```
Webhook URL: https://api.myhibachichef.com/webhooks/ringcentral
OAuth Redirect URI: https://api.myhibachichef.com/auth/ringcentral/callback
```

#### 5. Compliance Verification
✅ Privacy Policy includes SMS consent language: "We do not share your SMS consent with third parties"
✅ Terms page includes STOP/START/HELP instructions
✅ Business email is not Gmail (cs@myhibachichef.com)
✅ All pages accessible and properly formatted

### 📝 SUBMISSION NOTES:
- Application is for business SMS communications only
- All messages are transactional or explicitly opted-in promotional
- Full TCPA compliance with STOP/START/HELP support
- Privacy policy exceeds RingCentral requirements

### ⏱️ ESTIMATED APPROVAL TIME: 3-5 business days