# 💳 Payment Page UI Specification

## Overview
Customer payment flow with 4 payment methods, QR codes, and real-time fee calculation.

---

## 📱 Page Structure

### **Page 1: Payment Input** (`/payment`)

```
┌─────────────────────────────────────────┐
│         Payment Information             │
├─────────────────────────────────────────┤
│                                         │
│  Base Amount:     $____.__              │
│  (Order balance)                        │
│                                         │
│  Tip Amount:      $____.__              │
│  (Optional gratuity)                    │
│                                         │
│  ├─ Subtotal: $500.00                  │
│                                         │
│  [Continue to Payment Methods →]       │
│                                         │
└─────────────────────────────────────────┘
```

**Fields**:
- Base Amount (required, > 0)
- Tip Amount (optional, >= 0)
- Calculated Subtotal (read-only)

---

### **Page 2: Payment Method Selection** (`/payment/select-method`)

```
┌─────────────────────────────────────────────────────────────┐
│         Choose Your Payment Method                          │
│                                                             │
│  Payment Details:                                           │
│  • Base Amount: $500.00                                     │
│  • Tip: $50.00                                              │
│  • Subtotal: $550.00                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    Z     │  │    🏦    │  │    V     │  │    💳    │  │
│  │  Zelle   │  │   Bank   │  │  Venmo   │  │  Credit  │  │
│  │          │  │ Transfer │  │          │  │   Card   │  │
│  │   FREE   │  │   FREE   │  │ +3% fee  │  │ +3% fee  │  │
│  │ 1-2 hrs  │  │ Instant! │  │ 1-2 hrs  │  │ Instant  │  │
│  │          │  │    ⭐    │  │          │  │          │  │
│  │ $550.00  │  │ $550.00  │  │ $566.50  │  │ $566.50  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  💡 Recommendation:                                         │
│  Use Bank Transfer (Plaid) - FREE + Instant!               │
│  Save $16.50 vs credit card                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Payment Method Cards**:

Each card shows:
- Icon/Logo
- Method Name
- Fee (FREE or +X%)
- Confirmation Time
- **Total Amount** (subtotal + fee)
- Special badges (⭐ for best option)

**Card Styles**:
- **Selected**: Border highlight, background color
- **Hover**: Scale up slightly, shadow
- **Disabled**: Gray out, "Not Available"

---

### **Page 3A: Zelle Payment** (`/payment/zelle`)

```
┌─────────────────────────────────────────┐
│         Pay with Zelle                  │
├─────────────────────────────────────────┤
│                                         │
│  Payment Amount: $550.00                │
│  Processing Fee: FREE                   │
│  ─────────────────────────              │
│  Total: $550.00 ✨                      │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │      [QR CODE HERE]              │ │
│  │                                   │ │
│  │  Scan to pay with Zelle app      │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Or send manually to:                   │
│  📧 Email: myhibachichef@gmail.com      │
│  📱 Phone: +1 (916) 740-8768            │
│                                         │
│  Reference: ORDER-#12345                │
│                                         │
│  ⏱️ Confirmation Time:                  │
│  We'll confirm your payment within      │
│  1-2 hours and send you an email.       │
│                                         │
│  [✓ I've sent the payment]             │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- QR Code for Zelle app (generated from email/phone)
- Manual payment info (email, phone)
- Order reference number
- Confirmation button
- Estimated confirmation time

---

### **Page 3B: Bank Transfer (Plaid RTP)** (`/payment/plaid`)

```
┌─────────────────────────────────────────┐
│    Pay with Bank Transfer (Plaid)      │
├─────────────────────────────────────────┤
│                                         │
│  Payment Amount: $550.00                │
│  Processing Fee: FREE                   │
│  ─────────────────────────              │
│  Total: $550.00 ✨                      │
│                                         │
│  ⚡ Instant confirmation!               │
│  🔒 Bank-level security                 │
│  💰 No processing fees                  │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │  [Select Your Bank] 🏦            │ │
│  │                                   │ │
│  │  • Chase                          │ │
│  │  • Bank of America                │ │
│  │  • Wells Fargo                    │ │
│  │  • Other... (2,000+ banks)        │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Continue with Bank Transfer →]        │
│                                         │
│  How it works:                          │
│  1. Select your bank                    │
│  2. Log in securely (Plaid Link)        │
│  3. Confirm payment                     │
│  4. Instant confirmation! ✅            │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Plaid Link integration (opens on button click)
- Bank selection list
- Security badges
- Step-by-step guide
- Instant confirmation messaging

---

### **Page 3C: Venmo Payment** (`/payment/venmo`)

```
┌─────────────────────────────────────────┐
│         Pay with Venmo                  │
├─────────────────────────────────────────┤
│                                         │
│  Payment Amount: $550.00                │
│  Processing Fee: $16.50 (3%)            │
│  ─────────────────────────              │
│  Total: $566.50                         │
│                                         │
│  💡 Save $16.50 with Bank Transfer!     │
│  [Switch to Bank Transfer (FREE) →]     │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │      [QR CODE HERE]              │ │
│  │                                   │ │
│  │  Scan to pay with Venmo app       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Or send manually to:                   │
│  @myhibachichef                         │
│                                         │
│  Reference: ORDER-#12345                │
│                                         │
│  ⏱️ Confirmation Time:                  │
│  We'll confirm your payment within      │
│  1-2 hours and send you an email.       │
│                                         │
│  [✓ I've sent the payment]             │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- QR Code for Venmo app
- Fee warning (3%)
- Savings suggestion (switch to free method)
- Manual username
- Confirmation button

---

### **Page 3D: Credit Card (Stripe)** (`/payment/stripe`)

```
┌─────────────────────────────────────────┐
│      Pay with Credit Card               │
├─────────────────────────────────────────┤
│                                         │
│  Payment Amount: $550.00                │
│  Processing Fee: $16.50 (3%)            │
│  ─────────────────────────              │
│  Total: $566.50                         │
│                                         │
│  💡 Save $16.50 with Bank Transfer!     │
│  [Switch to Bank Transfer (FREE) →]     │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Card Number                      │ │
│  │  [____-____-____-____]            │ │
│  │                                   │ │
│  │  Expiry        CVV                │ │
│  │  [MM/YY]      [___]               │ │
│  │                                   │ │
│  │  Name on Card                     │ │
│  │  [____________________]           │ │
│  │                                   │ │
│  │  🔒 Secure payment via Stripe     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Pay $566.50 →]                        │
│                                         │
│  ⚡ Instant confirmation                │
│  🔒 256-bit SSL encryption              │
│  💳 Visa, MC, Amex, Discover            │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Stripe Elements (card input)
- Fee warning (3%)
- Savings suggestion
- Security badges
- Instant processing

---

## 🔧 API Integration

### **1. Calculate Payment** (on method selection)

```typescript
// Call when user enters amount or changes method
const response = await fetch('/api/v1/payments/calculate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    base_amount: 500.00,
    tip_amount: 50.00,
    payment_method: 'plaid'
  })
});

const data = await response.json();
// {
//   base_amount: 500.00,
//   tip_amount: 50.00,
//   subtotal: 550.00,
//   selected_method: {
//     method: 'plaid',
//     total_amount: 550.00,
//     processing_fee: 0.00,
//     savings_vs_stripe: 16.50
//   },
//   recommendation: '✅ Great choice! No processing fees.'
// }
```

### **2. Compare All Methods** (show all 4 cards)

```typescript
const response = await fetch('/api/v1/payments/compare', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    base_amount: 500.00,
    tip_amount: 50.00
  })
});

const data = await response.json();
// {
//   methods: [
//     { method: 'zelle', total_amount: 550.00, ... },
//     { method: 'plaid', total_amount: 550.00, ... },
//     { method: 'venmo', total_amount: 566.50, ... },
//     { method: 'stripe', total_amount: 566.50, ... }
//   ],
//   recommendation: '💰 Best: Bank Transfer (Plaid) - FREE + Instant!'
// }
```

### **3. Get Payment Methods Info** (for icons/colors)

```typescript
const response = await fetch('/api/v1/payments/methods');
const data = await response.json();
// {
//   methods: [
//     {
//       id: 'zelle',
//       name: 'Zelle',
//       icon: 'Z',
//       color: 'purple',
//       fee_percentage: 0.00,
//       qr_code_available: true,
//       email: 'myhibachichef@gmail.com'
//     },
//     ...
//   ]
// }
```

---

## 🎨 UI Components

### **PaymentMethodCard.tsx**

```tsx
interface PaymentMethodCardProps {
  method: {
    id: string;
    name: string;
    icon: string;
    color: string;
    totalAmount: number;
    processingFee: number;
    isFree: boolean;
    isInstant: boolean;
  };
  selected: boolean;
  onSelect: () => void;
}

export function PaymentMethodCard({ method, selected, onSelect }: Props) {
  return (
    <button
      onClick={onSelect}
      className={`
        relative p-6 rounded-lg border-2 transition-all
        ${selected 
          ? `border-${method.color}-500 bg-${method.color}-50 scale-105` 
          : 'border-gray-200 hover:border-gray-300 hover:scale-102'
        }
      `}
    >
      {/* Icon */}
      <div className={`mx-auto mb-3 w-12 h-12 rounded-full bg-${method.color}-600 
                       flex items-center justify-center text-white text-xl font-bold`}>
        {method.icon}
      </div>
      
      {/* Name */}
      <h3 className="text-lg font-semibold mb-2">{method.name}</h3>
      
      {/* Fee Badge */}
      {method.isFree ? (
        <span className="inline-block px-3 py-1 bg-green-100 text-green-800 
                         rounded-full text-sm font-medium mb-2">
          FREE ✨
        </span>
      ) : (
        <span className="text-sm text-gray-600 mb-2">
          +{method.processingFee.toFixed(2)} fee
        </span>
      )}
      
      {/* Speed */}
      <p className="text-sm text-gray-500 mb-3">
        {method.isInstant ? '⚡ Instant' : '⏱️ 1-2 hours'}
      </p>
      
      {/* Total Amount */}
      <p className="text-2xl font-bold text-gray-900">
        ${method.totalAmount.toFixed(2)}
      </p>
      
      {/* Best Badge */}
      {method.isFree && method.isInstant && (
        <span className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 
                         px-2 py-1 rounded text-xs font-bold">
          ⭐ BEST
        </span>
      )}
    </button>
  );
}
```

---

## 📋 QR Code Generation

### **Zelle QR Code**

```typescript
import QRCode from 'qrcode';

// Generate Zelle QR code
const zelleData = {
  email: 'myhibachichef@gmail.com',
  phone: '+19167408768',
  amount: 550.00,
  note: 'ORDER-12345'
};

const qrCodeUrl = await QRCode.toDataURL(JSON.stringify(zelleData));
```

### **Venmo QR Code**

```typescript
// Generate Venmo deep link QR code
const venmoUrl = `venmo://paycharge?txn=pay&recipients=myhibachichef&amount=${amount}&note=ORDER-${orderId}`;
const qrCodeUrl = await QRCode.toDataURL(venmoUrl);
```

---

## ✅ Next Steps

1. **Create Payment Input Page**
   - Base amount field
   - Tip amount field
   - Subtotal calculation

2. **Create Method Selection Page**
   - 4 payment method cards
   - Compare API integration
   - Fee warnings

3. **Create Individual Payment Pages**
   - Zelle with QR code
   - Plaid with Link integration
   - Venmo with QR code
   - Stripe with Elements

4. **Add QR Code Generation**
   - Install `qrcode` package
   - Generate Zelle QR codes
   - Generate Venmo QR codes

5. **Test Complete Flow**
   - Input → Select → Pay → Confirm
   - All 4 payment methods
   - Fee calculations

---

## 🎯 User Flow Summary

```
1. Enter payment amount + tip
   ↓
2. See 4 payment options with total costs
   ↓
3. Select method (FREE options highlighted)
   ↓
4a. Zelle → Scan QR → Send → Wait for confirmation
4b. Plaid → Select bank → Login → Instant confirm ✅
4c. Venmo → Scan QR → Send → Wait for confirmation
4d. Stripe → Enter card → Pay → Instant confirm ✅
   ↓
5. Confirmation page with receipt
```

**Optimal Path**: Plaid RTP (FREE + Instant!)
