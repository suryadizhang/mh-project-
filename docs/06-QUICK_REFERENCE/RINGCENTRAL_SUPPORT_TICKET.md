# RingCentral Support Ticket - Password Authentication Request

## FORM FIELDS TO FILL:

---

### Select a topic:
**API & Developer Tools** (or "Application Development" if available)

---

### Enter a short title/summary:
**Request to Enable Password Grant Type for Private Server Application**

---

### Are you requesting help with a specific application?
**Yes - Select: "My Hibachi CRM"**
(App ID: 3ADYc6Nv8qxeddtHygnfIK)

---

### Describe the problem (COPY THIS):

Subject: Request to Enable Password/Resource Owner Password Credentials Grant Type

Hello RingCentral Support Team,

I am developing a private server-side CRM application for my business (My Hibachi LLC) that needs to send SMS notifications and handle incoming SMS messages programmatically.

**Application Details:**
- App Name: My Hibachi CRM
- App ID/Client ID: 3ADYc6Nv8qxeddtHygnfIK
- App Type: REST API App (Private - internal use only)
- Account: my Hibachi LLC
- Primary Contact: Suryadi Zhang (suryadizhang.chef@gmail.com)
- Phone: +19167408768, Extension: 101

**Current Issue:**
I cannot authenticate to the RingCentral API because the Password Grant Type (Resource Owner Password Credentials) is not enabled for my application.

**Error Received:**
```
HTTP 400 Bad Request
Error: "unauthorized_client"
Error Description: "Unauthorized for this grant type"
Error Code: OAU-251
```

**What I Need:**
Please enable the "Password" or "Resource Owner Password Credentials" OAuth grant type for my application so I can authenticate using:
- Username: suryadizhang.chef@gmail.com
- Extension: 101
- Password: [my account password]

**Why I Need This:**
This is a private, server-side application that will:
1. Send automated SMS notifications to customers (booking confirmations, reminders)
2. Receive and process incoming SMS messages
3. Integrate with our CRM system for customer communication
4. Run as a backend service without user interface

**Current Authentication Settings:**
- JWT auth flow: Enabled
- 3-legged OAuth: Available but not suitable for server-side automation
- Password grant type: NOT enabled (this is what I need)

**What I've Tried:**
1. Downloaded credentials JSON file (only contains Client ID and Secret)
2. Checked application Settings page - Password grant type not listed as option
3. Enabled JWT auth flow, but this requires complex private key setup
4. Tested authentication with SDK - confirmed Password flow is not authorized

**Request:**
Could you please either:
1. Enable the "Password" OAuth grant type for my application, OR
2. Provide guidance on the proper authentication method for a private server-side app that needs to send/receive SMS programmatically

**Additional Information:**
- This is for internal business use only (not a public application)
- App is set to "Private" (only callable using credentials from same RingCentral account)
- I understand SMS messaging requires additional verification/approval
- I'm willing to complete any necessary verification steps

**Technical Environment:**
- Programming Language: Python
- SDK: ringcentral-python (latest version)
- Application Type: FastAPI backend service
- Use Case: Customer relationship management system

Thank you for your assistance. Please let me know if you need any additional information or if there's a different authentication approach you recommend for this use case.

Best regards,
Suryadi Zhang
My Hibachi LLC
suryadizhang.chef@gmail.com
+19167408768

---

### Optional CC Email:
(Leave blank or add your business email if you have one)

---

## AFTER SUBMITTING:

You should receive:
1. Confirmation email
2. Ticket number
3. Response within 1-2 business days

Expected outcomes:
- They enable Password grant type, OR
- They provide alternative authentication method for private apps, OR
- They explain what documentation/verification is needed

---

## WHILE WAITING FOR SUPPORT:

Let's proceed with webhook testing for the 7 working integrations!
This way you make progress while RingCentral support processes your request.

---

**Ready to submit this ticket?** Copy the "Describe the problem" section into the form!
