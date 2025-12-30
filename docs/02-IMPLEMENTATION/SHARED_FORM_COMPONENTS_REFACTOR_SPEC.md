# Shared Form Components Refactoring Specification

**Version:** 1.0.0
**Created:** 2024-12-24
**Status:** APPROVED FOR IMPLEMENTATION
**Priority:** HIGH - Reduces code duplication by ~60%

---

## 📋 Executive Summary

This document specifies the refactoring of duplicated form patterns across the My Hibachi monorepo into shared, reusable components. The analysis found **12+ duplicated form patterns** across customer and admin apps.

### Impact Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Contact form duplications | 12 components | 1 shared | 92% reduction |
| Address form duplications | 8 components | 1 shared | 88% reduction |
| Guest count duplications | 5 components | 1 shared | 80% reduction |
| Step indicator duplications | 3 components | 1 shared | 67% reduction |
| Type definition duplications | 2 files | 1 shared | 50% reduction |
| Total lines of duplicated code | ~2,500 lines | ~400 lines | 84% reduction |

---

## 🏗️ Architecture Overview

### New Folder Structure

```
packages/
├── ui/                              # Already exists - extend it
│   └── src/
│       ├── components/
│       │   ├── Button.tsx           # Existing
│       │   ├── Card.tsx             # Existing
│       │   ├── Modal.tsx            # Existing
│       │   └── index.ts
│       └── index.ts
│
├── forms/                           # NEW PACKAGE
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── fields/                  # Individual form fields
│       │   ├── ContactFields.tsx
│       │   ├── AddressFields.tsx
│       │   ├── GuestCountField.tsx
│       │   ├── PhoneField.tsx
│       │   ├── EmailField.tsx
│       │   └── index.ts
│       │
│       ├── sections/                # Composed form sections
│       │   ├── ContactInfoSection.tsx
│       │   ├── AddressSection.tsx
│       │   ├── VenueAddressSection.tsx
│       │   ├── BillingAddressSection.tsx
│       │   ├── GuestCountSection.tsx
│       │   ├── DateTimeSection.tsx
│       │   └── index.ts
│       │
│       ├── wizards/                 # Multi-step components
│       │   ├── StepIndicator.tsx
│       │   ├── WizardContainer.tsx
│       │   └── index.ts
│       │
│       ├── hooks/                   # Form-related hooks
│       │   ├── usePhoneFormat.ts
│       │   ├── useAddressAutocomplete.ts
│       │   ├── useFormPersistence.ts
│       │   └── index.ts
│       │
│       ├── validation/              # Shared validation schemas
│       │   ├── contactSchema.ts
│       │   ├── addressSchema.ts
│       │   ├── guestCountSchema.ts
│       │   └── index.ts
│       │
│       └── index.ts                 # Barrel export
│
└── types/                           # Already exists - extend it
    └── src/
        ├── booking.ts               # CONSOLIDATE duplicates here
        ├── address.ts               # NEW - shared address types
        ├── contact.ts               # NEW - shared contact types
        └── index.ts
```

---

## 📦 Component Specifications

### 1. ContactFields Component

**Purpose:** Reusable name, email, phone input fields

**File:** `packages/forms/src/fields/ContactFields.tsx`

```tsx
// Interface
interface ContactFieldsProps {
  // Form integration (react-hook-form)
  register: UseFormRegister<any>;
  errors: FieldErrors<any>;

  // Field customization
  fieldPrefix?: string;           // e.g., "customer" → "customerName"
  required?: {
    name?: boolean;
    email?: boolean;
    phone?: boolean;
  };

  // Display options
  layout?: 'stacked' | 'inline' | 'grid';  // Default: 'grid'
  showLabels?: boolean;                     // Default: true
  showIcons?: boolean;                      // Default: false

  // Placeholders
  placeholders?: {
    name?: string;
    email?: string;
    phone?: string;
  };

  // Callbacks
  onPhoneChange?: (formatted: string, raw: string) => void;
  onEmailBlur?: (email: string) => void;
}

// Usage Examples:
<ContactFields
  register={register}
  errors={errors}
  required={{ name: true, email: true, phone: true }}
  layout="grid"
/>

// With prefix for billing
<ContactFields
  register={register}
  errors={errors}
  fieldPrefix="billing"  // → billingName, billingEmail, billingPhone
/>
```

**Used By:**
- `BookUsPageClient.tsx` - Step 1 (Contact)
- `QuoteCalculator.tsx` - Contact section
- `ContactPage.tsx` - Contact form
- `StripePaymentForm.tsx` - Customer info
- `AlternativePaymentPage.tsx` - Customer info
- Admin: `StationForm.tsx` - Station contact

---

### 2. AddressFields Component

**Purpose:** Reusable street, city, state, zip input fields

**File:** `packages/forms/src/fields/AddressFields.tsx`

```tsx
interface AddressFieldsProps {
  // Form integration
  register: UseFormRegister<any>;
  errors: FieldErrors<any>;

  // Field customization
  fieldPrefix?: string;           // e.g., "venue" → "venueStreet"
  required?: boolean;             // Default: true

  // Google Places integration
  enableAutocomplete?: boolean;   // Default: false
  onPlaceSelect?: (place: GooglePlace) => void;
  onGeocode?: (coords: { lat: number; lng: number }) => void;

  // Display options
  layout?: 'stacked' | 'inline';  // Default: 'stacked'
  showLabels?: boolean;           // Default: true

  // State dropdown options
  stateOptions?: 'all' | 'west-coast' | StateCode[];  // Default: 'west-coast'

  // "Same as" toggle
  sameAsSource?: {
    enabled: boolean;
    label: string;                // e.g., "Same as venue address"
    sourcePrefix: string;         // e.g., "venue"
  };
}

// Usage Examples:

// Venue address with Google Places
<AddressFields
  register={register}
  errors={errors}
  fieldPrefix="venue"
  enableAutocomplete={true}
  onGeocode={handleGeocode}
  stateOptions="west-coast"
/>

// Billing address with "same as venue"
<AddressFields
  register={register}
  errors={errors}
  fieldPrefix="billing"
  sameAsSource={{
    enabled: true,
    label: "Same as venue address",
    sourcePrefix: "venue"
  }}
/>
```

**Used By:**
- `BookUsPageClient.tsx` - Step 2 (Venue), Step 4 (Billing)
- `QuoteCalculator.tsx` - Venue address
- `AddressForm.tsx` - Generic address
- `StripePaymentForm.tsx` - Billing address
- Admin: `StationForm.tsx` - Station address

---

### 3. GuestCountField Component

**Purpose:** Reusable guest/party size selector

**File:** `packages/forms/src/fields/GuestCountField.tsx`

```tsx
interface GuestCountFieldProps {
  // Form integration
  register: UseFormRegister<any>;
  errors: FieldErrors<any>;

  // Field customization
  fieldName?: string;             // Default: "guestCount"

  // Limits
  min?: number;                   // Default: 1
  max?: number;                   // Default: 50

  // Display options
  variant?: 'input' | 'stepper' | 'slider';  // Default: 'stepper'
  showLabel?: boolean;            // Default: true
  label?: string;                 // Default: "Number of Guests"
  helperText?: string;            // e.g., "Including adults and children"

  // Split adults/children
  splitByAge?: boolean;           // Default: false

  // Callbacks
  onChange?: (count: number) => void;
}

// Usage Examples:

// Simple guest count
<GuestCountField
  register={register}
  errors={errors}
  min={10}
  max={50}
  variant="stepper"
/>

// Split adults and children (for QuoteCalculator)
<GuestCountField
  register={register}
  errors={errors}
  splitByAge={true}
  helperText="Pricing varies for children under 12"
/>
```

**Used By:**
- `BookUsPageClient.tsx` - Step 3 (Party Size)
- `QuoteCalculator.tsx` - Guest count (adults/children split)
- `BookingStepTwo.tsx` - Guest count

---

### 4. StepIndicator Component

**Purpose:** Reusable multi-step wizard indicator

**File:** `packages/forms/src/wizards/StepIndicator.tsx`

```tsx
interface StepIndicatorProps {
  // Step state
  currentStep: number;
  totalSteps: number;

  // Labels and icons
  steps: Array<{
    label: string;
    icon?: React.ReactNode;
    description?: string;
  }>;

  // Display options
  variant?: 'horizontal' | 'vertical';  // Default: 'horizontal'
  size?: 'sm' | 'md' | 'lg';            // Default: 'md'
  showLabels?: boolean;                  // Default: true
  showConnectors?: boolean;              // Default: true

  // Interaction
  allowStepClick?: boolean;              // Default: false
  onStepClick?: (step: number) => void;

  // Styling
  activeColor?: string;                  // Default: 'red-600'
  completedColor?: string;               // Default: 'green-600'
}

// Usage Example:
<StepIndicator
  currentStep={currentStep}
  totalSteps={4}
  steps={[
    { label: 'Contact', icon: <Users /> },
    { label: 'Venue', icon: <MapPin /> },
    { label: 'Party', icon: <Users2 /> },
    { label: 'Date & Time', icon: <Calendar /> },
  ]}
  variant="horizontal"
  allowStepClick={true}
  onStepClick={setCurrentStep}
/>
```

**Used By:**
- `BookUsPageClient.tsx` - 4-step booking wizard
- `ReviewFlow/page.tsx` - 4-step review wizard
- `QuoteCalculator.tsx` - 3-step funnel (if converted)

---

### 5. DateTimeSection Component

**Purpose:** Reusable date picker + time slot selector

**File:** `packages/forms/src/sections/DateTimeSection.tsx`

```tsx
interface DateTimeSectionProps {
  // Date state
  selectedDate: Date | null;
  onDateChange: (date: Date | null) => void;

  // Time slots
  timeSlots?: TimeSlot[];         // If not provided, uses default 4 slots
  selectedTime: string | null;
  onTimeChange: (time: string) => void;

  // Availability
  availableDates?: Date[];        // Highlight available dates
  unavailableDates?: Date[];      // Disable specific dates

  // Smart scheduling integration
  onCheckAvailability?: (date: Date) => Promise<TimeSlot[]>;
  suggestions?: AlternativeSuggestion[];
  onSuggestionSelect?: (suggestion: AlternativeSuggestion) => void;

  // Display options
  showTimeSlots?: boolean;        // Default: true
  datePickerProps?: DatePickerProps;

  // Labels
  dateLabel?: string;             // Default: "Select Date"
  timeLabel?: string;             // Default: "Select Time"
}

// Usage Example:
<DateTimeSection
  selectedDate={selectedDate}
  onDateChange={setSelectedDate}
  selectedTime={selectedTime}
  onTimeChange={setSelectedTime}
  onCheckAvailability={fetchAvailability}
  suggestions={alternativeSuggestions}
  onSuggestionSelect={handleSuggestionSelect}
/>
```

**Used By:**
- `BookUsPageClient.tsx` - Step 4 (Date & Time)
- `BookingStepTwo.tsx` - Date/time selection

---

### 6. PriceSummaryCard Component

**Purpose:** Reusable pricing breakdown display

**File:** `packages/forms/src/sections/PriceSummaryCard.tsx`

```tsx
interface PriceSummaryCardProps {
  // Pricing data
  pricing: {
    basePrice?: number;
    addOnsTotal?: number;
    travelFee?: number;
    subtotal: number;
    processingFee?: number;
    tax?: number;
    total: number;
    deposit?: number;
  };

  // Display options
  showBreakdown?: boolean;        // Default: true
  showDeposit?: boolean;          // Default: true
  showTax?: boolean;              // Default: false
  variant?: 'compact' | 'detailed';  // Default: 'detailed'

  // Labels
  title?: string;                 // Default: "Price Summary"
  depositLabel?: string;          // Default: "Deposit Required Today"
}

// Usage Example:
<PriceSummaryCard
  pricing={{
    basePrice: 450,
    addOnsTotal: 85,
    travelFee: 30,
    subtotal: 565,
    deposit: 150,
    total: 565,
  }}
  showDeposit={true}
  variant="detailed"
/>
```

**Used By:**
- `BookUsPageClient.tsx` - Order summary sidebar
- `QuoteCalculator.tsx` - Quote result
- `StripePaymentForm.tsx` - Payment summary

---

## 🔧 Shared Validation Schemas

### File: `packages/forms/src/validation/contactSchema.ts`

```typescript
import { z } from 'zod';

export const contactSchema = z.object({
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters'),

  email: z.string()
    .email('Please enter a valid email address'),

  phone: z.string()
    .regex(/^\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$/,
      'Please enter a valid phone number'),
});

export type ContactFormData = z.infer<typeof contactSchema>;
```

### File: `packages/forms/src/validation/addressSchema.ts`

```typescript
import { z } from 'zod';

export const addressSchema = z.object({
  street: z.string()
    .min(5, 'Please enter a valid street address')
    .max(200, 'Address is too long'),

  city: z.string()
    .min(2, 'City is required')
    .max(100, 'City name is too long'),

  state: z.string()
    .length(2, 'Please select a state'),

  zipcode: z.string()
    .regex(/^[0-9]{5}(-[0-9]{4})?$/, 'Please enter a valid ZIP code'),
});

export type AddressFormData = z.infer<typeof addressSchema>;
```

### File: `packages/forms/src/validation/guestCountSchema.ts`

```typescript
import { z } from 'zod';

export const guestCountSchema = z.object({
  guestCount: z.number()
    .min(1, 'At least 1 guest is required')
    .max(100, 'Maximum 100 guests allowed'),
});

// With adults/children split
export const guestCountSplitSchema = z.object({
  adults: z.number()
    .min(1, 'At least 1 adult is required')
    .max(50, 'Maximum 50 adults'),
  children: z.number()
    .min(0, 'Cannot be negative')
    .max(30, 'Maximum 30 children'),
}).refine(data => data.adults + data.children >= 10, {
  message: 'Minimum 10 guests required for hibachi service',
});

export type GuestCountFormData = z.infer<typeof guestCountSchema>;
export type GuestCountSplitFormData = z.infer<typeof guestCountSplitSchema>;
```

---

## 📁 Shared Types (Consolidation)

### File: `packages/types/src/address.ts`

```typescript
export interface Address {
  street: string;
  street2?: string;
  city: string;
  state: string;
  zipcode: string;
  country?: string;
  lat?: number;
  lng?: number;
}

export interface VenueAddress extends Address {
  venueName?: string;
  venueType?: 'house' | 'apartment' | 'park' | 'venue' | 'other';
  accessInstructions?: string;
}

export interface BillingAddress extends Address {
  sameAsVenue?: boolean;
}

export type StateCode = 'CA' | 'NV' | 'OR' | 'WA' | 'AZ' | 'CO' | 'TX' | /* ... */;

export const US_STATES: Record<StateCode, string> = {
  CA: 'California',
  NV: 'Nevada',
  OR: 'Oregon',
  WA: 'Washington',
  // ... all 50 states
};

export const WEST_COAST_STATES: StateCode[] = ['CA', 'NV', 'OR', 'WA'];
```

### File: `packages/types/src/contact.ts`

```typescript
export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
}

export interface CustomerContact extends ContactInfo {
  preferredContactMethod?: 'email' | 'phone' | 'sms';
  smsOptIn?: boolean;
}
```

### File: `packages/types/src/booking.ts` (CONSOLIDATE)

```typescript
// Move from apps/customer/src/data/booking/types.ts
// AND apps/admin/src/data/booking/types.ts

export interface TimeSlot {
  slot_time: string;      // "12PM", "3PM", "6PM", "9PM"
  is_available: boolean;
  available_chefs?: number;
  estimated_duration?: number;
}

export interface BookingFormData {
  // Contact
  name: string;
  email: string;
  phone: string;

  // Venue
  venueStreet: string;
  venueCity: string;
  venueState: string;
  venueZipcode: string;

  // Party
  guestCount: number;
  specialRequests?: string;

  // Date/Time
  eventDate: string;
  eventTime: string;

  // Billing
  sameAsVenue: boolean;
  addressStreet?: string;
  addressCity?: string;
  addressState?: string;
  addressZipcode?: string;
}

export type BookingStatus =
  | 'PENDING'
  | 'DEPOSIT_PAID'
  | 'CONFIRMED'
  | 'COMPLETED'
  | 'CANCELLED';
```

---

## 🔄 Migration Plan

### Phase 1: Create Shared Package (Day 1)

1. Create `packages/forms/` package structure
2. Set up `package.json`, `tsconfig.json`
3. Add to workspace configuration
4. Create barrel exports

### Phase 2: Extract Components (Days 2-3)

| Order | Component | Extract From | Complexity |
|-------|-----------|--------------|------------|
| 1 | `ContactFields` | `BookUsPageClient.tsx` | Medium |
| 2 | `AddressFields` | `BookUsPageClient.tsx` | High (Google Places) |
| 3 | `GuestCountField` | `BookUsPageClient.tsx` | Low |
| 4 | `StepIndicator` | `BookUsPageClient.tsx` | Low |
| 5 | `DateTimeSection` | `BookUsPageClient.tsx` | Medium |
| 6 | `PriceSummaryCard` | `QuoteCalculator.tsx` | Medium |

### Phase 3: Validation & Types (Day 3)

1. Create shared Zod schemas
2. Consolidate type definitions
3. Update imports in both apps

### Phase 4: Refactor Consumer Components (Days 4-5)

| Component | App | Lines Before | Lines After | Reduction |
|-----------|-----|--------------|-------------|-----------|
| `BookUsPageClient.tsx` | Customer | 1,559 | ~400 | 74% |
| `QuoteCalculator.tsx` | Customer | ~700 | ~250 | 64% |
| `ContactPage.tsx` | Customer | ~300 | ~100 | 67% |
| `StripePaymentForm.tsx` | Customer | ~320 | ~150 | 53% |
| `StationForm.tsx` | Admin | ~350 | ~150 | 57% |
| `BookingForm.tsx` | Admin | ~400 | ~200 | 50% |

### Phase 5: Testing & Verification (Day 6)

1. Unit tests for shared components
2. Integration tests for forms
3. Visual regression tests
4. Build verification for both apps

---

## ✅ Acceptance Criteria

### Must Have
- [ ] All shared components build successfully
- [ ] Both apps build successfully after refactor
- [ ] No regression in form functionality
- [ ] Form validation works identically
- [ ] Google Places autocomplete works
- [ ] Lead capture still functions

### Should Have
- [ ] Unit tests for each shared component
- [ ] Storybook stories for visual testing
- [ ] TypeScript strict mode passes

### Nice to Have
- [ ] Component documentation
- [ ] Usage examples in comments
- [ ] Performance benchmarks

---

## 🚨 Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Create new package alongside existing code
- Refactor one component at a time
- Keep old code until new is verified

### Risk 2: Form State Issues
**Mitigation:**
- Use same react-hook-form patterns
- Keep register/errors prop interface consistent
- Test form submission thoroughly

### Risk 3: Styling Inconsistencies
**Mitigation:**
- Use Tailwind classes only
- Document styling conventions
- Visual regression tests

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Code duplication | < 10% remaining |
| Bundle size | No increase |
| Build time | < 10% increase |
| Test coverage | > 80% for shared components |
| Developer satisfaction | Easier to maintain |

---

## 🔗 Related Documents

- `11-REACT_PERFORMANCE.instructions.md` - React best practices
- `12-CSS_ARCHITECTURE.instructions.md` - Tailwind conventions
- `01-CORE_PRINCIPLES.instructions.md` - Code quality standards

---

## 📝 Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-12-24 | 1.0.0 | Initial specification created |
