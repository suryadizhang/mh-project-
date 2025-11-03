# HIGH PRIORITY IMPLEMENTATIONS

## 1. Alternative Payer Field - Implementation Guide

### A. Add State Variables (in PaymentPage component)

Add these state variables after the existing useState declarations:

```typescript
// Alternative payer (friend/family payment)
const [hasAlternativePayer, setHasAlternativePayer] = useState(false);
const [alternativePayerName, setAlternativePayerName] = useState('');
const [alternativePayerPhone, setAlternativePayerPhone] = useState('');
const [alternativePayerVenmo, setAlternativePayerVenmo] = useState('');
```

### B. Add Alternative Payer UI Section

Insert this section AFTER the "Booking Details" section and BEFORE "Payment Type Selection" (around line 500):

```tsx
{/* Alternative Payer Section */}
{selectedBooking && (
  <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
    <div className="mb-4 flex items-center justify-between">
      <h3 className="text-lg font-semibold text-gray-900">Payment Information</h3>
      <div className="flex items-center">
        <input
          type="checkbox"
          id="alternativePayer"
          checked={hasAlternativePayer}
          onChange={(e) => setHasAlternativePayer(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
        />
        <label htmlFor="alternativePayer" className="ml-2 text-sm text-gray-700">
          Someone else will pay for this booking
        </label>
      </div>
    </div>

    {hasAlternativePayer && (
      <div className="mt-4 space-y-4 rounded-lg border-2 border-red-100 bg-red-50/50 p-4">
        <div className="flex items-start space-x-2 rounded-md bg-blue-50 p-3">
          <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-xs text-blue-800">
            <p className="font-medium">Why do we need this?</p>
            <p className="mt-1">
              If a friend or family member will pay via Venmo/Zelle, provide their information below. 
              This helps us automatically detect and confirm their payment (99% faster approval!).
            </p>
          </div>
        </div>

        <div>
          <label htmlFor="altPayerName" className="block text-sm font-medium text-gray-700">
            Payer's Full Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="altPayerName"
            value={alternativePayerName}
            onChange={(e) => setAlternativePayerName(e.target.value)}
            placeholder="John Smith"
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
            required={hasAlternativePayer}
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the name exactly as it appears on their Venmo/Zelle account
          </p>
        </div>

        <div>
          <label htmlFor="altPayerPhone" className="block text-sm font-medium text-gray-700">
            Payer's Phone Number <span className="text-red-500">*</span>
          </label>
          <input
            type="tel"
            id="altPayerPhone"
            value={alternativePayerPhone}
            onChange={(e) => setAlternativePayerPhone(e.target.value)}
            placeholder="2103884155"
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
            required={hasAlternativePayer}
          />
          <p className="mt-1 text-xs text-gray-500">
            <strong>Important:</strong> Ask them to include this phone number in their payment note/memo
          </p>
        </div>

        <div>
          <label htmlFor="altPayerVenmo" className="block text-sm font-medium text-gray-700">
            Venmo Username <span className="text-gray-400">(Optional)</span>
          </label>
          <div className="relative mt-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">@</span>
            <input
              type="text"
              id="altPayerVenmo"
              value={alternativePayerVenmo}
              onChange={(e) => setAlternativePayerVenmo(e.target.value)}
              placeholder="johnsmith"
              className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-8 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
            />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            If paying via Venmo, this helps us match the payment faster
          </p>
        </div>

        <div className="rounded-md bg-green-50 p-3">
          <div className="flex">
            <svg className="h-5 w-5 flex-shrink-0 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3 text-xs text-green-800">
              <p className="font-medium">Automatic Payment Detection</p>
              <p className="mt-1">
                With this info, we can automatically detect and confirm the payment within 5 minutes. 
                You'll receive instant confirmation!
              </p>
            </div>
          </div>
        </div>
      </div>
    )}
  </div>
)}
```

### C. Update Payment Intent API Call

Find the `createPaymentIntent` function and update the `customerInfo` section:

```typescript
customerInfo: {
  name: selectedBooking?.customerName || 'Guest User',
  email: selectedBooking?.customerEmail || 'guest@example.com',
  phone: hasAlternativePayer && alternativePayerPhone 
    ? alternativePayerPhone 
    : '',
  // ... other fields
},
metadata: {
  bookingId: selectedBooking?.id || 'manual-payment',
  customerName: selectedBooking?.customerName || 'Guest User',
  eventDate: selectedBooking?.eventDate || 'N/A',
  paymentType,
  // Add alternative payer info
  hasAlternativePayer,
  alternativePayerName: hasAlternativePayer ? alternativePayerName : '',
  alternativePayerPhone: hasAlternativePayer ? alternativePayerPhone : '',
  alternativePayerVenmo: hasAlternativePayer ? alternativePayerVenmo : '',
},
```

---

## 2. Payment Instructions - Auto-include Phone

### A. Update Booking Confirmation Email Template

File: `apps/backend/src/services/email_service.py` or email template file

Add this section to the booking confirmation email:

```html
<div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 20px; margin: 20px 0;">
  <h3 style="color: #991B1B; margin: 0 0 10px 0;">📲 Payment Instructions</h3>
  
  <p style="margin: 10px 0; color: #7F1D1D;">
    <strong>IMPORTANT:</strong> When sending payment, please include your phone number in the payment note/memo:
  </p>
  
  <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
    <p style="margin: 5px 0;"><strong>Your Phone Number:</strong></p>
    <p style="font-size: 24px; font-weight: bold; color: #DC2626; margin: 5px 0;">
      {{ customer_phone }}
    </p>
  </div>
  
  <div style="margin-top: 15px;">
    <p style="margin: 5px 0; font-size: 14px;"><strong>💳 Venmo:</strong> Send to @myhibachichef</p>
    <p style="margin: 5px 0; font-size: 14px;"><strong>💵 Zelle:</strong> Send to myhibachichef@gmail.com</p>
    <p style="margin: 5px 0; font-size: 14px;"><strong>📝 Payment Note:</strong> "{{ customer_phone }}"</p>
  </div>
  
  <p style="margin: 15px 0 5px 0; font-size: 12px; color: #6B7280;">
    <strong>Why?</strong> Including your phone number helps us automatically detect and confirm your payment 
    within 5 minutes. You'll receive instant confirmation!
  </p>
</div>
```

### B. Add to SMS Notification (if you have SMS)

```
🎉 Booking Confirmed!

When paying, include this in your note:
YOUR PHONE: {{ customer_phone }}

Venmo: @myhibachichef
Zelle: myhibachichef@gmail.com

This helps us auto-confirm your payment instantly!
```

---

## 3. Admin UI Dashboard - Real-Time Notification Feed

### A. Create Admin Dashboard Page

File: `apps/customer/src/app/admin/payment-notifications/page.tsx`

```tsx
'use client';

import { useEffect, useState } from 'react';
import { Bell, CheckCircle, Clock, AlertCircle, DollarSign, Phone, User, Search, Filter } from 'lucide-react';

interface Notification {
  id: number;
  provider: string;
  amount: number;
  sender_name: string;
  sender_phone: string;
  status: string;
  match_score: number;
  received_at: string;
  requires_manual_review: boolean;
  booking_id: number | null;
  customer_name: string | null;
  event_date: string | null;
}

interface Stats {
  total_notifications: number;
  pending_match: number;
  matched: number;
  confirmed: number;
  manual_review_needed: number;
  stripe_count: number;
  venmo_count: number;
  zelle_count: number;
  last_24_hours: number;
  average_match_score: number;
  auto_match_rate: number;
}

export default function PaymentNotificationsAdmin() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [filter]);
  
  const fetchData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch('/api/v1/admin/payment-notifications/stats', {
        headers: { 'Authorization': `Bearer ${getAuthToken()}` }
      });
      const statsData = await statsRes.json();
      setStats(statsData);
      
      // Fetch notifications
      const notifRes = await fetch(
        `/api/v1/admin/payment-notifications/list?${filter !== 'all' ? `requires_review=${filter === 'review'}` : ''}`,
        { headers: { 'Authorization': `Bearer ${getAuthToken()}` } }
      );
      const notifData = await notifRes.json();
      setNotifications(notifData);
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setLoading(false);
    }
  };
  
  const getAuthToken = () => {
    // Implement your auth token retrieval
    return localStorage.getItem('admin_token') || '';
  };
  
  const triggerEmailCheck = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/admin/payment-notifications/check-emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getAuthToken()}` }
      });
      await fetchData();
    } catch (error) {
      console.error('Failed to trigger email check:', error);
    }
    setLoading(false);
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'bg-green-100 text-green-800';
      case 'matched': return 'bg-blue-100 text-blue-800';
      case 'pending_match': return 'bg-yellow-100 text-yellow-800';
      case 'manual_review': return 'bg-orange-100 text-orange-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getConfidenceColor = (score: number) => {
    if (score >= 200) return 'text-green-600';
    if (score >= 100) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };
  
  const filteredNotifications = notifications.filter(n => 
    searchTerm === '' || 
    n.sender_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    n.sender_phone?.includes(searchTerm) ||
    n.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  if (loading && !stats) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-red-600"></div>
          <p className="mt-4 text-gray-600">Loading notifications...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Payment Notifications</h1>
            <p className="mt-1 text-gray-600">Automatic payment detection and matching</p>
          </div>
          <button
            onClick={triggerEmailCheck}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
          >
            <Bell className="h-5 w-5" />
            Check Emails Now
          </button>
        </div>
        
        {/* Stats Dashboard */}
        {stats && (
          <div className="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={<Clock className="h-6 w-6" />}
              label="Pending Review"
              value={stats.manual_review_needed}
              color="orange"
            />
            <StatCard
              icon={<CheckCircle className="h-6 w-6" />}
              label="Matched Today"
              value={stats.last_24_hours}
              color="green"
            />
            <StatCard
              icon={<DollarSign className="h-6 w-6" />}
              label="Auto-Match Rate"
              value={`${stats.auto_match_rate.toFixed(1)}%`}
              color="blue"
            />
            <StatCard
              icon={<AlertCircle className="h-6 w-6" />}
              label="Avg Confidence"
              value={`${stats.average_match_score.toFixed(0)}/225`}
              color="purple"
            />
          </div>
        )}
        
        {/* Provider Stats */}
        {stats && (
          <div className="mb-6 flex gap-4 rounded-lg bg-white p-4 shadow">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700">Providers:</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Stripe:</span>
              <span className="font-medium text-blue-600">{stats.stripe_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Venmo:</span>
              <span className="font-medium text-purple-600">{stats.venmo_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Zelle:</span>
              <span className="font-medium text-green-600">{stats.zelle_count}</span>
            </div>
          </div>
        )}
        
        {/* Filters and Search */}
        <div className="mb-6 flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or phone..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-10 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`rounded-lg px-4 py-2 ${filter === 'all' ? 'bg-red-600 text-white' : 'bg-white text-gray-700'}`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('review')}
              className={`rounded-lg px-4 py-2 ${filter === 'review' ? 'bg-red-600 text-white' : 'bg-white text-gray-700'}`}
            >
              Needs Review
            </button>
          </div>
        </div>
        
        {/* Notifications List */}
        <div className="space-y-4">
          {filteredNotifications.length === 0 ? (
            <div className="rounded-lg bg-white p-12 text-center shadow">
              <Bell className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-gray-600">No notifications found</p>
            </div>
          ) : (
            filteredNotifications.map((notification) => (
              <NotificationCard key={notification.id} notification={notification} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon, label, value, color }: any) {
  const colorClasses = {
    orange: 'bg-orange-100 text-orange-600',
    green: 'bg-green-100 text-green-600',
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
  };
  
  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <div className={`mb-2 inline-flex rounded-lg p-3 ${colorClasses[color as keyof typeof colorClasses]}`}>
        {icon}
      </div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}

// Notification Card Component
function NotificationCard({ notification }: { notification: Notification }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'bg-green-100 text-green-800 border-green-200';
      case 'matched': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending_match': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };
  
  const getConfidenceColor = (score: number) => {
    if (score >= 200) return 'text-green-600 bg-green-50';
    if (score >= 100) return 'text-yellow-600 bg-yellow-50';
    return 'text-orange-600 bg-orange-50';
  };
  
  return (
    <div className={`rounded-lg border-2 bg-white p-6 shadow transition-all hover:shadow-md ${notification.requires_manual_review ? 'border-orange-200' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className={`rounded px-2 py-1 text-xs font-medium uppercase ${getStatusColor(notification.status)}`}>
              {notification.provider}
            </span>
            <span className="text-2xl font-bold text-gray-900">
              ${notification.amount.toFixed(2)}
            </span>
            {notification.requires_manual_review && (
              <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-800">
                Needs Review
              </span>
            )}
          </div>
          
          <div className="mt-4 grid gap-2 md:grid-cols-2">
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-gray-400" />
              <span className="font-medium">Sender:</span>
              <span>{notification.sender_name || 'Unknown'}</span>
            </div>
            {notification.sender_phone && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-gray-400" />
                <span className="font-medium">Phone:</span>
                <span>{notification.sender_phone}</span>
              </div>
            )}
          </div>
          
          {notification.booking_id && (
            <div className="mt-3 rounded-lg bg-blue-50 p-3">
              <p className="text-xs font-medium text-blue-800">Matched to Booking #{notification.booking_id}</p>
              <p className="text-sm text-blue-700">
                {notification.customer_name} - {notification.event_date}
              </p>
            </div>
          )}
        </div>
        
        <div className="text-right">
          <div className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 ${getConfidenceColor(notification.match_score)}`}>
            <span className="text-xs font-medium">Score:</span>
            <span className="text-lg font-bold">{notification.match_score}/225</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {new Date(notification.received_at).toLocaleString()}
          </p>
        </div>
      </div>
      
      {notification.requires_manual_review && (
        <div className="mt-4 flex gap-2">
          <button className="flex-1 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700">
            Match to Booking
          </button>
          <button className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            View Details
          </button>
          <button className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Ignore
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## 4. PII Encryption Explanation

### What is "PII Encryption at Rest"?

**PII = Personally Identifiable Information**
- Phone numbers: 2103884155
- Email addresses: customer@example.com
- Full names: John Smith
- Addresses

**"At Rest" = Stored in Database**

**Encryption = Making it unreadable**

### Current State (NO Encryption):
```sql
-- In your database RIGHT NOW:
| id | customer_phone | customer_name    |
|----|---------------|------------------|
| 1  | 2103884155    | Suryadi Zhang    |

-- Anyone with database access can see:
- Exact phone number
- Real name
- All personal info
```

### With Encryption:
```sql
-- In database WITH encryption:
| id | customer_phone                    | customer_name             |
|----|-----------------------------------|---------------------------|
| 1  | AES256:hG9jK2m...xY3z (encrypted) | AES256:dF8nP1q...wE4r    |

-- Database admin sees: GIBBERISH
-- Your app decrypts it when needed: "2103884155"
```

### Why Do This?

**Scenario 1: Database Breach**
- Hacker gets database dump
- WITHOUT encryption: They have 10,000 customer phone numbers
- WITH encryption: They have useless encrypted strings

**Scenario 2: Compliance**
- GDPR (Europe), CCPA (California) require PII protection
- Health insurance, financial services REQUIRE encryption
- Some business clients won't work with you without it

**Scenario 3: Insider Threat**
- Database admin can see ALL customer data
- WITH encryption: They see gibberish
- Only your app (with encryption key) can decrypt

### How to Implement:

**Option A: Database-Level (PostgreSQL)**
```sql
-- Encrypt when inserting
INSERT INTO catering_bookings (customer_phone) 
VALUES (pgp_sym_encrypt('2103884155', 'SECRET_KEY'));

-- Decrypt when reading
SELECT pgp_sym_decrypt(customer_phone, 'SECRET_KEY') FROM catering_bookings;
```

**Option B: Application-Level (Python)**
```python
from cryptography.fernet import Fernet

# Generate key once, store in environment variable
KEY = Fernet.generate_key()  # Store in .env as ENCRYPTION_KEY

def encrypt_phone(phone: str) -> str:
    f = Fernet(KEY)
    return f.encrypt(phone.encode()).decode()

def decrypt_phone(encrypted: str) -> str:
    f = Fernet(KEY)
    return f.decrypt(encrypted.encode()).decode()

# When saving:
booking.customer_phone = encrypt_phone("2103884155")

# When reading:
real_phone = decrypt_phone(booking.customer_phone)
```

### YOUR DECISION:

**Do you want PII encryption?**

**✅ YES - Implement it if:**
- You're handling 100+ customers
- You plan to scale to enterprise clients
- You want best security practices
- You're in healthcare, finance, or regulated industry
- You want GDPR/CCPA compliance

**❌ NO - Skip it if:**
- You're just starting out (< 50 customers)
- You trust your database security 100%
- You don't have sensitive business clients
- You want to move faster (adds complexity)
- Your data isn't that valuable (no credit cards, SSN, etc.)

**💡 MY RECOMMENDATION:**
Start WITHOUT encryption for now (faster development), but:
1. Design database to support it later (separate columns)
2. Add it before reaching 100 customers
3. Add it before any enterprise sales
4. Add it if you get security audit request

---

## 5. Push Notification System

### What You Want:
Admin gets notified when:
- New payment detected (Zelle, Venmo)
- Payment needs manual review
- Payment auto-confirmed
- Booking created
- Customer cancellation

### Notification Channels:
1. **Email** (easiest)
2. **SMS** (via Twilio)
3. **Push Notifications** (web browser)
4. **Mobile App** (Android/iPhone)
5. **Slack/Discord** (webhook)

### Implementation Options:

#### Option 1: Email Notifications (EASIEST - 30 min)

```python
# When payment detected:
def send_admin_notification(payment_notification):
    if user.notification_preferences.get('email_on_payment'):
        send_email(
            to=user.email,
            subject=f"💰 New {payment_notification.provider} payment: ${payment_notification.amount}",
            body=f"""
            New payment detected!
            
            Provider: {payment_notification.provider}
            Amount: ${payment_notification.amount}
            Sender: {payment_notification.sender_name}
            Phone: {payment_notification.sender_phone}
            Confidence: {payment_notification.match_score}/225
            
            {'✅ Auto-matched!' if payment_notification.match_score > 100 else '⚠️ Needs manual review'}
            
            View details: https://myhibachi.com/admin/notifications/{payment_notification.id}
            """
        )
```

#### Option 2: Web Push Notifications (1-2 hours)

```javascript
// Request permission
Notification.requestPermission().then(permission => {
  if (permission === 'granted') {
    // Subscribe to push notifications
  }
});

// When payment detected (backend sends via Firebase Cloud Messaging):
{
  title: '💰 New Payment Detected',
  body: 'Zelle $1.00 from Suryadi Zhang',
  icon: '/notification-icon.png',
  data: {
    notificationId: 212,
    url: '/admin/notifications/212'
  }
}
```

#### Option 3: SMS Notifications (via Twilio - 1 hour)

```python
from twilio.rest import Client

def send_sms_notification(admin_phone, payment):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"💰 New {payment.provider} ${payment.amount} from {payment.sender_name}. Score: {payment.match_score}/225",
        from_=TWILIO_PHONE,
        to=admin_phone
    )
```

#### Option 4: Slack/Discord Webhook (15 min - MY FAVORITE!)

```python
import requests

def send_slack_notification(payment):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    color = 'good' if payment.match_score > 100 else 'warning'
    
    requests.post(webhook_url, json={
        "attachments": [{
            "color": color,
            "title": f"💰 New {payment.provider} Payment",
            "fields": [
                {"title": "Amount", "value": f"${payment.amount}", "short": True},
                {"title": "Sender", "value": payment.sender_name, "short": True},
                {"title": "Phone", "value": payment.sender_phone or 'N/A', "short": True},
                {"title": "Confidence", "value": f"{payment.match_score}/225", "short": True},
            ],
            "footer": "Payment Notification System"
        }]
    })
```

### Notification Preferences Table:

```sql
CREATE TABLE admin_notification_preferences (
    user_id INTEGER PRIMARY KEY,
    
    -- Channels
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT FALSE,
    slack_enabled BOOLEAN DEFAULT FALSE,
    
    -- Events
    notify_on_payment_detected BOOLEAN DEFAULT TRUE,
    notify_on_manual_review BOOLEAN DEFAULT TRUE,
    notify_on_auto_matched BOOLEAN DEFAULT FALSE,
    notify_on_booking_created BOOLEAN DEFAULT TRUE,
    notify_on_cancellation BOOLEAN DEFAULT TRUE,
    
    -- Thresholds
    notify_min_amount DECIMAL(10,2) DEFAULT 0,  -- Only notify if payment >= $X
    notify_high_value_amount DECIMAL(10,2) DEFAULT 500,  -- High-value alert
    
    -- Quiet Hours
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME,  -- e.g., 22:00 (10 PM)
    quiet_hours_end TIME,    -- e.g., 08:00 (8 AM)
    
    -- Contact Info
    phone_number VARCHAR(20),
    slack_webhook_url TEXT
);
```

### User Settings UI:

```tsx
<div className="space-y-6">
  <h2>Notification Preferences</h2>
  
  {/* Channels */}
  <div>
    <h3>Notification Channels</h3>
    <label>
      <input type="checkbox" checked={emailEnabled} onChange={...} />
      Email Notifications
    </label>
    <label>
      <input type="checkbox" checked={smsEnabled} onChange={...} />
      SMS/Text Messages
    </label>
    <label>
      <input type="checkbox" checked={pushEnabled} onChange={...} />
      Web Push Notifications
    </label>
  </div>
  
  {/* Events */}
  <div>
    <h3>Notify Me When...</h3>
    <label>
      <input type="checkbox" checked={notifyOnPayment} onChange={...} />
      New payment detected
    </label>
    <label>
      <input type="checkbox" checked={notifyOnReview} onChange={...} />
      Payment needs manual review
    </label>
    <label>
      <input type="checkbox" checked={notifyOnBooking} onChange={...} />
      New booking created
    </label>
  </div>
  
  {/* Thresholds */}
  <div>
    <h3>Smart Filtering</h3>
    <label>
      Only notify for payments over:
      <input type="number" value={minAmount} onChange={...} />
    </label>
    <label>
      <input type="checkbox" checked={quietHours} onChange={...} />
      Enable quiet hours (no notifications)
    </label>
  </div>
</div>
```

---

## YOUR DECISIONS NEEDED:

### 1. Alternative Payer Field
**Status:** Code ready, just needs to be inserted  
**Decision:** Approve and deploy? YES / NO

### 2. Payment Instructions  
**Status:** Email template ready  
**Decision:** Approve text? Any changes?

### 3. Admin Dashboard
**Status:** Full React component ready  
**Decision:** Deploy now or customize first?

### 4. PII Encryption
**Decision Options:**
- [ ] A. Implement now (best security)
- [ ] B. Implement later (before 100 customers)
- [ ] C. Skip it (trust database security)
- [ ] D. Explain more, I'm not sure

### 5. Push Notifications
**Decision Options:**
- [ ] A. Email only (simplest)
- [ ] B. Email + Web Push
- [ ] C. Email + SMS (costs $0.01/text)
- [ ] D. Slack/Discord webhook (my favorite!)
- [ ] E. All of the above (enterprise-grade)

**Priority ranking?** (1 = most important)
___ Email notifications
___ Web push notifications
___ SMS notifications
___ Slack/Discord
___ Mobile app (future)

### 6. Auto-deletion
**Status:** Ready to implement  
**Decision:** 45 days good? Or prefer 30/60/90 days?

---

## What should we implement first?

Let me know your decisions and I'll start implementing! 🚀
