# Meta (Facebook/Instagram) - Production Deployment TODO

## ✅ COMPLETED (Development Setup)
- ✅ Meta App created (App ID: 1839409339973429)
- ✅ App Secret configured
- ✅ Facebook Page "My hibachi" connected
- ✅ Instagram @my_hibachi_chef connected to Facebook Page
- ✅ Page Access Token generated with Instagram permissions
- ✅ All credentials added to .env file

## 📋 TODO - Before Going Live

### 1. **Configure Webhooks** (When Server is Deployed)
**Location:** https://developers.facebook.com/apps/1839409339973429/messenger/settings/

**Action Items:**
- [ ] Deploy backend to production (https://myhibachichef.com)
- [ ] Configure webhook callback URL: `https://myhibachichef.com/api/v1/webhooks/meta`
- [ ] Use verify token: `myhibachi-meta-webhook-verify-token-2025`
- [ ] Subscribe to webhook events:
  - [ ] `messages` - Receive Facebook Messenger messages
  - [ ] `messaging_postbacks` - Button clicks
  - [ ] `message_reads` - Read receipts
  - [ ] `messaging_optins` - User opt-ins

**Instagram Webhooks:**
- [ ] Add callback URL for Instagram: `https://myhibachichef.com/api/v1/webhooks/meta`
- [ ] Subscribe to Instagram events:
  - [ ] `messages` - Instagram DMs
  - [ ] `messaging_postbacks` - Instagram button clicks
  - [ ] `message_reads` - Instagram read receipts

### 2. **Facebook Page Comment Webhooks**
**Action Items:**
- [ ] Subscribe to page comment events
- [ ] Test comment auto-replies
- [ ] Configure AI response rules for comments

### 3. **App Review & Permissions** (Required for Public Access)
**Location:** https://developers.facebook.com/apps/1839409339973429/app-review/

**Permissions to Request:**
- [ ] `pages_messaging` - Send/receive Facebook Messenger messages
- [ ] `pages_manage_metadata` - Manage page settings
- [ ] `pages_read_engagement` - Read comments and engagement
- [ ] `instagram_manage_messages` - Manage Instagram DMs
- [ ] `instagram_manage_comments` - Manage Instagram comments
- [ ] `instagram_basic` - Basic Instagram profile info

**What You'll Need for App Review:**
- [ ] Screencast video showing app functionality
- [ ] Privacy Policy URL (create one)
- [ ] Terms of Service URL (optional)
- [ ] Detailed description of how you use each permission
- [ ] Test user credentials for Facebook review team

### 4. **Instagram Business Account Setup**
**Action Items:**
- [ ] Verify @my_hibachi_chef is a Business or Creator account
- [ ] Ensure Instagram is properly linked to Facebook Page
- [ ] Test Instagram DM receiving
- [ ] Test Instagram comment management

### 5. **Extension Management System** (From Your Request)
**Features to Build:**
- [ ] Admin panel to manage RingCentral extensions
- [ ] Add/remove extensions dynamically (Ext. 101, 102, 103...)
- [ ] Extension assignment (Name + Extension number)
- [ ] AI → Human escalation routing
- [ ] Extension availability status
- [ ] Call routing rules configuration

### 6. **Testing Checklist**
- [ ] Test Facebook Messenger incoming messages
- [ ] Test Facebook Messenger outgoing messages
- [ ] Test Facebook Page comment replies
- [ ] Test Instagram DM receiving
- [ ] Test Instagram DM sending
- [ ] Test Instagram comment replies
- [ ] Test AI auto-reply for all channels
- [ ] Test webhook reliability and retry logic

### 7. **Production Webhook Configuration**
**Backend Implementation Needed:**
```python
# Endpoint: /api/v1/webhooks/meta
# Method: GET (for verification), POST (for events)
# 
# Verify token: myhibachi-meta-webhook-verify-token-2025
# App Secret: f128b9779d1e80f9687800ef28aeacc3 (for signature verification)
```

---

## 📞 **Current Access Levels**

### **Development Mode (Current):**
✅ Can message administrators, developers, testers  
✅ Can read/send messages to test accounts  
⚠️ Cannot message general public  

### **Production Mode (After App Review):**
✅ Can message anyone who contacts you first  
✅ Can respond to all comments  
✅ Full Instagram DM access  
✅ Public availability  

---

## 🔑 **Important Credentials**

**Meta App ID:** `1839409339973429`  
**Facebook Page ID:** `664861203383602`  
**Instagram Username:** `@my_hibachi_chef`  
**Webhook Verify Token:** `myhibachi-meta-webhook-verify-token-2025`

---

## 📚 **Documentation Links**

- [Meta Messenger API](https://developers.facebook.com/docs/messenger-platform)
- [Instagram Messaging API](https://developers.facebook.com/docs/messenger-platform/instagram)
- [Webhook Setup Guide](https://developers.facebook.com/docs/messenger-platform/webhooks)
- [App Review Guidelines](https://developers.facebook.com/docs/app-review)

---

## ⚠️ **Important Notes**

1. **Token Expiration:** Page Access Tokens can expire. Consider implementing token refresh logic.
2. **Rate Limits:** Be aware of Meta's API rate limits in production.
3. **User Privacy:** Comply with Meta's data usage policies.
4. **Message Tags:** For sending messages outside 24-hour window, use appropriate message tags.
5. **Human Handoff:** Implement proper AI → human escalation (Ext. 101 for Suryadi).

---

**Last Updated:** October 27, 2025  
**Status:** Development setup complete, ready for backend integration and production deployment
