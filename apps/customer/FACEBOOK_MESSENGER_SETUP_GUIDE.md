# Facebook Messenger Integration Setup Guide

## 🎯 Complete Setup Instructions for My Hibachi

### **Current Status:**

- ✅ Instagram DM: **Fully Functional**
- ⚠️ Facebook Messenger: **Needs App Creation**
- ✅ Page ID: `61577483702847` (verified)
- ✅ Code Implementation: **Complete**

---

## 📋 **Step-by-Step Facebook App Setup**

### **Step 1: Create Facebook App**

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **"Create App"**
3. Choose **"Business"** as app type
4. Fill in app details:
   - **App Name:** "My Hibachi Messenger"
   - **App Contact Email:** Your business email
   - **Business Use Case:** "Customer Service"

### **Step 2: Add Messenger Product**

1. In your app dashboard, click **"Add Product"**
2. Find **"Messenger"** and click **"Set up"**
3. You'll be taken to Messenger settings

### **Step 3: Connect Your Facebook Page**

1. In Messenger settings, find **"Access Tokens"**
2. Click **"Add or Remove Pages"**
3. Select your **"My-hibachi"** page (ID: 61577483702847)
4. Grant permissions for messaging

### **Step 4: Get Your App ID**

1. Go to **Settings > Basic** in your app dashboard
2. Copy the **App ID** (16-digit number)
3. Copy the **App Secret** (keep this secure!)

### **Step 5: Update Environment Variables**

Replace in `.env.local`:

```bash
# OLD (placeholder)
NEXT_PUBLIC_FB_APP_ID=1234567890123456

# NEW (your real App ID)
NEXT_PUBLIC_FB_APP_ID=YOUR_REAL_APP_ID_HERE
```

### **Step 6: Configure Webhooks (Optional)**

1. In Messenger settings, find **"Webhooks"**
2. Click **"Add Callback URL"**
3. Enter your website URL + `/api/webhooks/messenger`
4. Enter a verify token (random string)

### **Step 7: Domain Whitelist**

1. Go to **Settings > Basic**
2. Add these domains to **"App Domains"**:
   - `myhibachi.com` (your production domain)
   - `localhost` (for development)

### **Step 8: Go Live**

1. Complete Facebook's review process
2. Switch app from **"Development"** to **"Live"**
3. Test the Messenger widget on your website

---

## 🔧 **Current Code Setup (Already Complete)**

### **Environment Variables:**

```bash
# Facebook Messenger - My Hibachi Page
NEXT_PUBLIC_FB_PAGE_ID=61577483702847
NEXT_PUBLIC_FB_APP_ID=YOUR_REAL_APP_ID_HERE  # ← Update this
```

### **Contact Page Integration:**

- ✅ Messenger button already implemented
- ✅ Facebook SDK loaded
- ✅ Page ID configured
- ✅ Click handlers ready

### **Components Ready:**

- ✅ `src/components/chat/MetaMessenger.tsx`
- ✅ Contact page integration
- ✅ Error handling implemented

---

## 🧪 **Testing Checklist**

### **After Setup:**

1. **Development Test:**

   - Visit `http://localhost:3000/contact`
   - Click "💬 Chat on Messenger" button
   - Should open Messenger widget

2. **Production Test:**

   - Deploy to your domain
   - Test Messenger button
   - Verify messages reach your business page

3. **Mobile Test:**
   - Test on mobile devices
   - Verify Messenger app integration

---

## 🚀 **Benefits After Setup**

### **Customer Experience:**

- **Instant Communication:** Real-time chat with customers
- **Message History:** Persistent conversation threads
- **Mobile Integration:** Seamless mobile app experience
- **Rich Media:** Send photos, files, quick replies

### **Business Benefits:**

- **Centralized Inbox:** All messages in Facebook Business Suite
- **Automated Responses:** Set up auto-replies
- **Customer Insights:** Analytics on engagement
- **Professional Presence:** Official verified communication

---

## 📞 **Current Working Alternatives**

While setting up Facebook App:

### **Instagram DM (Fully Working):**

- ✅ Direct message link: `https://ig.me/m/my_hibachi_chef`
- ✅ Mobile app integration
- ✅ Fallback to web version

### **Contact Form:**

- ✅ Website contact form working
- ✅ Email notifications
- ✅ Form validation

### **Phone & Email:**

- ✅ Phone: (916) 740-8768
- ✅ Email: cs@myhibachichef.com

---

## ⏱️ **Timeline Estimate**

- **Facebook App Creation:** 15-30 minutes
- **Testing & Configuration:** 15 minutes
- **Facebook Review (if needed):** 1-3 business days
- **Total Active Setup Time:** ~1 hour

---

## 🎯 **Priority**

**Current Status: OPTIONAL**

- Website is fully functional without Facebook Messenger
- Instagram DM provides complete chat functionality
- Can be completed when convenient

**Recommendation:** Set up during a scheduled maintenance window or when you have 1 hour of focused time.

---

## 📚 **Resources**

- [Facebook Messenger Platform Docs](https://developers.facebook.com/docs/messenger-platform/)
- [Facebook App Review Guidelines](https://developers.facebook.com/docs/app-review/)
- [Business Manager Setup](https://business.facebook.com/)

**Need Help?** Your development team can assist with any technical aspects of this setup.
