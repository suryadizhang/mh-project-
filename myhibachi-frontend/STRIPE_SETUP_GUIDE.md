# 🔧 STRIPE SETUP & REAL BUSINESS INFORMATION GUIDE

## 🔑 **STRIPE API KEYS LOCATION**

### **Where to Find Your Stripe API Keys:**

1. **Go to Stripe Dashboard**: https://dashboard.stripe.com
2. **Navigate to**: Developers → API keys
3. **Copy these keys**:
   ```
   Publishable key: pk_live_xxxxxxxxxxxxxxxxxx (for frontend)
   Secret key: sk_live_xxxxxxxxxxxxxxxxxx (for backend)
   ```

### **Environment Configuration:**
Create or update your `.env.local` file:
```bash
# Stripe Live Keys (for production)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key_here
STRIPE_SECRET_KEY=sk_live_your_secret_key_here

# For testing, use test keys:
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here
# STRIPE_SECRET_KEY=sk_test_your_test_key_here
```

---

## 🏢 **REAL BUSINESS INFORMATION TO UPDATE**

### **1. Payment Contact Information** 
Currently set to demo values - update these in the code:

#### **Zelle Information** (AlternativePaymentOptions.tsx):
```typescript
zelle: {
  email: 'YOUR_REAL_ZELLE_EMAIL@domain.com',  // Current: payments@myhibachi.com
  phone: 'YOUR_REAL_PHONE_NUMBER',            // Current: (916) 740-8768
  name: 'Your Real Business Name'             // Current: My Hibachi Catering
}
```

#### **Venmo Information** (AlternativePaymentOptions.tsx):
```typescript
venmo: {
  username: '@YourRealVenmoUsername',         // Current: @MyHibachi-Catering
  phone: 'YOUR_REAL_PHONE_NUMBER',           // Current: (916) 740-8768
  name: 'Your Real Business Name'            // Current: My Hibachi Catering
}
```

### **2. Business Contact Details**
Update in multiple files:

#### **Payment Success Page** (success/page.tsx):
```typescript
// Update contact information
<Phone className="w-4 h-4 mr-2 text-gray-500" />
<span>YOUR_REAL_PHONE</span>  // Current: (916) 740-8768

<Mail className="w-4 h-4 mr-2 text-gray-500" />
<span>YOUR_REAL_EMAIL</span>  // Current: info@myhibachi.com
```

#### **Alternative Payment Options** (AlternativePaymentOptions.tsx):
```typescript
// Update contact information
<Phone className="w-4 h-4 mr-1" />
<span>YOUR_REAL_PHONE</span>  // Current: (916) 740-8768

<Mail className="w-4 h-4 mr-1" />
<span>YOUR_REAL_EMAIL</span>  // Current: info@myhibachi.com
```

### **3. Environment Variables** (.env.example):
```bash
# Business Information
BUSINESS_PHONE=YOUR_REAL_PHONE_NUMBER
BUSINESS_EMAIL=YOUR_REAL_EMAIL@domain.com
WEBSITE_URL=https://yourdomain.com

# Payment Settings
ZELLE_EMAIL=YOUR_ZELLE_EMAIL@domain.com
VENMO_USERNAME=@YourRealVenmoUsername
```

---

## 📝 **SPECIFIC FILES TO UPDATE WITH REAL INFO**

### **File 1: src/components/payment/AlternativePaymentOptions.tsx**
**Lines 42-56** - Update payment details:
```typescript
const paymentDetails = {
  zelle: {
    email: 'YOUR_REAL_ZELLE_EMAIL@domain.com',
    phone: 'YOUR_REAL_PHONE',
    name: 'Your Real Business Name',
    color: 'purple',
    icon: 'Z'
  },
  venmo: {
    username: '@YourRealVenmoUsername',
    phone: 'YOUR_REAL_PHONE',
    name: 'Your Real Business Name',
    color: 'blue',
    icon: 'V'
  }
}
```

### **File 2: src/app/payment/success/page.tsx**
**Lines 250-260** - Update contact section:
```typescript
<div className="flex items-center">
  <Phone className="w-4 h-4 mr-2 text-gray-500" />
  <span>YOUR_REAL_PHONE</span>
</div>
<div className="flex items-center">
  <Mail className="w-4 h-4 mr-2 text-gray-500" />
  <span>YOUR_REAL_EMAIL</span>
</div>
```

---

## 🚨 **IMPORTANT BUSINESS INFORMATION NEEDED**

Please provide the following real information for your My Hibachi business:

### **1. Primary Business Contact**
- **Business Phone**: ________________________
- **Business Email**: ________________________
- **Official Business Name**: ________________________

### **2. Zelle Payment Information**
- **Zelle Email**: ________________________
- **Zelle Phone** (if different): ________________________

### **3. Venmo Payment Information**
- **Venmo Username**: ________________________
- **Venmo Display Name**: ________________________

### **4. Website & Domain**
- **Website URL**: ________________________
- **Domain for Email**: ________________________

---

## 🔧 **QUICK UPDATE SCRIPT**

I can create a script to automatically update all the demo information with your real business details once you provide them. Just give me:

1. **Real phone number**
2. **Real email address** 
3. **Real business name**
4. **Real Zelle email**
5. **Real Venmo username**

And I'll update all the files at once!

---

## 💳 **STRIPE BUSINESS VERIFICATION**

For live payments, Stripe requires:
- **Business Tax ID** (EIN or SSN)
- **Bank Account** for payouts
- **Business Address**
- **Identity Verification** for business owners
- **Business Type** (LLC, Corporation, etc.)

---

## 🧪 **TESTING BEFORE GOING LIVE**

### **Test Cards (Stripe Test Mode)**:
```
Success: 4242424242424242
Declined: 4000000000000002
2FA Required: 4000002500003155
```

### **Test Flow**:
1. Use test API keys first
2. Test all payment methods
3. Verify receipt generation
4. Check booking integration
5. Switch to live keys when ready

---

**Ready to update with your real business information? Just provide the details above and I'll configure everything!**
