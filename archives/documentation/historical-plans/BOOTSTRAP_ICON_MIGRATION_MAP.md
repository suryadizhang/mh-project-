# Bootstrap Icon → Lucide React Migration Map

## Complete Icon Replacement Reference

### Homepage (page.tsx) - 9 icons

- `bi bi-calendar-event` → `CalendarDays` (24px)
- `bi bi-check-circle` (9x) → `CheckCircle` (18px)
- `bi bi-building` → `Building2` (24px)
- `bi bi-stars` → `Sparkles` (24px)
- `bi bi-calendar-check` → `CalendarCheck` (20px)

### 404 Page (not-found.tsx) - 9 icons

- `bi bi-exclamation-triangle` → `AlertTriangle` (text-6xl = 60px)
- `bi bi-house-door` → `Home` (20px)
- `bi bi-calendar-check` → `CalendarCheck` (20px)
- `bi bi-menu-button-wide` → `Menu` (24px)
- `bi bi-calculator` → `Calculator` (24px)
- `bi bi-journal-text` → `BookOpen` (24px)
- `bi bi-telephone` (2x) → `Phone` (24px, 20px)

### Menu Page (menu/page.tsx) - 1 icon

- `bi bi-info-circle-fill` → `Info` (18px)

### Contact Page (contact/ContactPageClient.tsx) - 29 icons

- `bi bi-messenger` → `MessageCircle` (social: 24px)
- `bi bi-instagram` (3x) → `Instagram` (24px)
- `bi bi-heart-fill` → `Heart` (20px)
- `bi bi-trophy-fill` → `Trophy` (24px)
- `bi bi-stars` → `Sparkles` (24px)
- `bi bi-geo-alt-fill` (8x) → `MapPin` (24px title, 18px contact, 16px
  locations)
- `bi bi-envelope-fill` (2x) → `Mail` (24px title, 18px)
- `bi bi-chat-dots-fill` (2x) → `MessageCircle` (18px, 20px)
- `bi bi-clock-fill` → `Clock` (18px)
- `bi bi-star-fill` → `Star` (24px)
- `bi bi-yelp` → `ExternalLink` (20px)
- `bi bi-google` → `ExternalLink` or custom Google icon (20px)
- `bi bi-facebook` → `Facebook` (24px)
- `bi bi-calendar-check-fill` → `CalendarCheck` (32px)
- `bi bi-telephone-fill` → `Phone` (20px)
- `bi bi-quote` → `Quote` (20px)

## Icon Size Guidelines

### Standard Sizes by Context:

- **Hero/Header Icons**: 32-36px
- **Section Title Icons**: 24px
- **Feature Icons**: 20-24px
- **Inline Icons**: 18px
- **Small Icons**: 16px
- **Social Media**: 24px

### Color Classes:

- `text-primary` → Keep (Tailwind class)
- `text-warning` → Keep (Tailwind class)
- `text-orange-400` → Keep (Tailwind class)
- `text-gray-*` → Keep (Tailwind classes)

### Spacing Classes (Bootstrap → Tailwind):

- `me-1` → `mr-1`
- `me-2` → `mr-2`
- `me-3` → `mr-3`
- `mb-2` → `mb-2` (already Tailwind)
- `block` → `block` (already Tailwind)

## Migration Pattern Template

```tsx
// BEFORE (Bootstrap Icon):
<i className="bi bi-calendar-check me-2"></i>;

// AFTER (Lucide React):
import { CalendarCheck } from 'lucide-react';
<CalendarCheck size={20} className="inline-block mr-2" />;
```

## Special Cases

### Google Icon (no Lucide equivalent):

```tsx
// Option 1: Use ExternalLink
<ExternalLink size={20} className="review-icon" />

// Option 2: Keep as custom SVG or use Globe
<Globe size={20} className="review-icon" />
```

### Heart Fill:

```tsx
// Lucide Heart is outline by default
// For filled version, use fill prop:
<Heart size={20} fill="currentColor" className="text-primary" />
```

### Stars/Sparkles:

```tsx
// bi-stars → Sparkles
<Sparkles size={24} className="feature-icon" />
```

## Files to Update

1. ✅ **Booking Components** (COMPLETED)
   - BookingModals.tsx
   - BookUsHero.tsx
   - ContactInfoSection.tsx
   - CustomerAddressSection.tsx
   - EventDetailsSection.tsx
   - SubmitSection.tsx
   - VenueAddressSection.tsx

2. ✅ **Utility Components** (COMPLETED)
   - LiveChatButton.tsx
   - OptimizedImage.tsx

3. ⏳ **Page Components** (IN PROGRESS)
   - app/page.tsx (homepage)
   - app/not-found.tsx
   - app/menu/page.tsx
   - app/contact/ContactPageClient.tsx

## Import Organization

Group imports logically:

```tsx
// 1. CSS imports
import './styles.module.css';

// 2. External library icons
import { Home, Calendar, Check } from 'lucide-react';

// 3. React/Next
import React from 'react';
import Link from 'next/link';

// 4. Internal imports
import { SomeComponent } from './SomeComponent';
```
