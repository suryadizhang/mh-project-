---
applyTo: 'apps/customer/**,apps/admin/**'
---

# My Hibachi – CSS Architecture & Tailwind v4 Standards

**Priority: HIGH** – CSS organization directly impacts page load performance.

---

## 🎯 Core Principle: Import Location = Load Timing

**Where you import CSS determines WHEN it loads, not just modularity.**

| Import Location      | When Loaded              | Bundle Impact        |
| -------------------- | ------------------------ | -------------------- |
| `layout.tsx`         | Every page load          | Adds to all pages    |
| `page.tsx`           | Only that page           | Page-specific bundle |
| Component file       | When component renders   | Component bundle     |

---

## 📁 CSS File Structure

```
apps/customer/src/
├── app/
│   ├── globals.css        # Tailwind + critical global styles
│   └── layout.tsx         # Global CSS imports (minimal!)
│
├── styles/
│   ├── base.css           # Reset, typography, variables
│   ├── utilities.css      # Utility classes
│   ├── accessibility.css  # A11y styles
│   │
│   ├── components/        # Component-specific styles
│   │   ├── buttons.css
│   │   ├── forms.css
│   │   └── cards.css
│   │
│   ├── layout/            # Layout component styles
│   │   ├── footer.css
│   │   ├── header.css
│   │   └── navigation.css
│   │
│   ├── pages/             # Page-specific styles
│   │   ├── home.page.css
│   │   ├── menu.page.css
│   │   └── booking.page.css
│   │
│   └── features/          # Feature-specific styles
│       ├── menu/
│       │   ├── menu.css
│       │   ├── menu-base.css
│       │   ├── menu-features.css
│       │   └── menu-pricing.css
│       └── chat/
│           └── chat-widget.css
```

---

## ✅ What Goes in layout.tsx (Global)

**Only CSS needed on EVERY page:**

```tsx
// apps/customer/src/app/layout.tsx
import './globals.css'; // Tailwind + critical
import '@/styles/base.css'; // Reset, typography
import '@/styles/utilities.css'; // Utility classes
import '@/styles/accessibility.css'; // A11y (skip links, focus)
import '@/styles/layout/footer.css'; // Footer on all pages
import '@/styles/layout/header.css'; // Header on all pages
```

**Size budget: < 50KB combined for layout imports**

---

## ❌ What Does NOT Go in layout.tsx

```tsx
// NEVER import page-specific CSS in layout.tsx!
import '@/styles/pages/menu.page.css'; // ❌ Only needed on /menu
import '@/styles/features/menu/menu.css'; // ❌ Only needed on /menu
import '@/styles/quote-calculator.css'; // ❌ Only needed on /BookUs
```

---

## ✅ Page-Specific CSS Pattern

Import CSS directly in the page that needs it:

```tsx
// apps/customer/src/app/menu/page.tsx
import '@/styles/features/menu/menu.css';
import '@/styles/features/menu/menu-base.css';
import '@/styles/features/menu/menu-features.css';
import '@/styles/features/menu/menu-pricing.css';
import '@/styles/pages/menu.page.css';

export default function MenuPage() {
  return <MenuContent />;
}
```

---

## 🎨 Tailwind CSS v4 Specifics

### The `--spacing` Fix (CRITICAL)

**Problem:** `tw-animate-css` uses `--spacing()` function which requires
the theme variable to be defined FIRST.

```css
/* ❌ BAD - Error: --spacing not defined */
@import url('tailwindcss');
@import url('tw-animate-css'); /* Uses --spacing before it exists! */
```

```css
/* ✅ GOOD - Define --spacing before tw-animate-css */
@import url('tailwindcss');

@theme inline {
  --spacing: 0.25rem;
}

@import url('tw-animate-css'); /* Now --spacing exists */
```

### Theme Variables

```css
/* apps/customer/src/app/globals.css */
@import url('tailwindcss');

/* MUST come before tw-animate-css */
@theme inline {
  --spacing: 0.25rem;

  /* Brand colors */
  --color-brand-primary: #dc2626;
  --color-brand-secondary: #1f2937;
  --color-brand-accent: #f59e0b;

  /* Semantic colors */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}

@import url('tw-animate-css');
```

### Import Order in globals.css

```css
/* 1. Tailwind base */
@import url('tailwindcss');

/* 2. Theme variables (BEFORE any plugins that use them) */
@theme inline {
  --spacing: 0.25rem;
  /* other theme vars */
}

/* 3. Tailwind plugins */
@import url('tw-animate-css');

/* 4. Custom base styles */
@layer base {
  /* typography, reset overrides */
}

/* 5. Custom components */
@layer components {
  /* reusable component classes */
}

/* 6. Custom utilities */
@layer utilities {
  /* utility classes */
}
```

---

## 📊 Performance Budgets

| Metric                    | Budget   | Action if Exceeded         |
| ------------------------- | -------- | -------------------------- |
| Global CSS (layout)       | < 50KB   | Move to page-specific      |
| Page-specific CSS         | < 30KB   | Split or lazy load         |
| First Load JS (shared)    | < 110KB  | Check optimizePackageImports |
| Compile time (dev)        | < 3s     | Check for errors/loops     |

---

## 🔧 next.config.ts Optimization

```typescript
// apps/customer/next.config.ts
const nextConfig: NextConfig = {
  experimental: {
    optimizeCss: true,
    optimizePackageImports: [
      'lucide-react',
      'date-fns',
      '@radix-ui/react-slot',
      'framer-motion',
      'react-hook-form',
      '@hookform/resolvers',
    ],
  },
};
```

---

## 📋 Adding New Pages Checklist

When creating a new page:

1. **Create page-specific CSS** (if needed):
   ```
   src/styles/pages/[page-name].page.css
   ```

2. **Import in page.tsx, NOT layout.tsx**:
   ```tsx
   // src/app/[page-name]/page.tsx
   import '@/styles/pages/[page-name].page.css';
   ```

3. **Check bundle size**:
   ```bash
   npm run build
   # Check page size in output
   ```

4. **Verify no global pollution**:
   - Run other pages, ensure no style conflicts
   - CSS should be scoped or use unique class names

---

## 📋 Adding New Features Checklist

When adding a feature with its own styles:

1. **Create feature folder**:
   ```
   src/styles/features/[feature-name]/
   ├── [feature-name].css        # Main styles
   ├── [feature-name]-base.css   # Base/reset for feature
   └── [feature-name]-utils.css  # Feature utilities
   ```

2. **Import in relevant pages only**:
   ```tsx
   // Each page that uses the feature
   import '@/styles/features/[feature-name]/[feature-name].css';
   ```

3. **Use scoped class names**:
   ```css
   /* Prefix with feature name to avoid conflicts */
   .feature-name__container { }
   .feature-name__header { }
   .feature-name--variant { }
   ```

---

## 🚫 CSS Anti-Patterns

### 1. Global Imports for Page-Specific Styles

```tsx
// ❌ BAD - in layout.tsx
import '@/styles/pages/menu.page.css'; // Loads on ALL pages!

// ✅ GOOD - in menu/page.tsx
import '@/styles/pages/menu.page.css'; // Loads only on /menu
```

### 2. Unscoped Global Styles

```css
/* ❌ BAD - pollutes global namespace */
.container {
  max-width: 1200px;
}
button {
  background: red;
}

/* ✅ GOOD - scoped to feature */
.menu-container {
  max-width: 1200px;
}
.menu-cta-button {
  background: red;
}
```

### 3. Importing CSS in Components Used Everywhere

```tsx
// ❌ BAD - Header is on every page, so this loads everywhere
// components/Header.tsx
import '@/styles/pages/menu.page.css'; // Why is menu CSS in header?!

// ✅ GOOD - Keep component CSS minimal
import '@/styles/components/header.css'; // Only header styles
```

### 4. Duplicate Tailwind Classes AND Custom CSS

```tsx
// ❌ BAD - mixing systems
<div className="p-4 custom-padding">  {/* Which wins? */}

// ✅ GOOD - one system per property
<div className="p-4">  {/* Tailwind */}
<div className="custom-card-padding">  {/* OR custom CSS */}
```

---

## 🔍 Debugging CSS Issues

### Check What's Loading

```bash
# Build and check output
npm run build

# Look for page sizes
Route (app)                    Size     First Load JS
├ ○ /                         5.2 kB        105 kB
├ ○ /menu                     12.1 kB       112 kB  # Menu CSS adds ~7KB
```

### Check for Tailwind Errors

```bash
# Look for theme variable errors
npm run dev 2>&1 | grep -i "spacing\|error\|warning"
```

### Verify Import Order

```bash
# In globals.css, check order:
# 1. tailwindcss
# 2. @theme inline { --spacing }
# 3. tw-animate-css
# 4. @layer directives
```

---

## 🎯 Quick Reference: Where to Import

| CSS Type              | Import Location           | Example                     |
| --------------------- | ------------------------- | --------------------------- |
| Tailwind/Theme        | `globals.css`             | `@import 'tailwindcss'`     |
| Base reset            | `layout.tsx`              | `base.css`                  |
| Header/Footer         | `layout.tsx`              | `header.css`, `footer.css`  |
| Page-specific         | `[page]/page.tsx`         | `menu.page.css`             |
| Feature styles        | Pages using feature       | `menu/menu.css`             |
| Component styles      | Component file            | `card.module.css`           |

---

## �️ Image Optimization Standards

### WebP Format (MANDATORY)

**All images in the project MUST use WebP format for optimal performance.**

| Format | Use Case            | Why                          |
| ------ | ------------------- | ---------------------------- |
| WebP   | All images          | 25-35% smaller than PNG/JPEG |
| SVG    | Icons, logos (vector) | Scalable, tiny file size   |
| PNG    | ❌ AVOID            | Convert to WebP              |
| JPEG   | ❌ AVOID            | Convert to WebP              |

### ImageMagick Conversion Commands

**Install ImageMagick (one-time):**

```powershell
scoop install imagemagick
```

**Convert single image:**

```powershell
magick "image.png" -quality 85 "image.webp"
magick "photo.jpg" -quality 85 "photo.webp"
```

**Batch convert all PNGs in a folder:**

```powershell
Get-ChildItem -Filter "*.png" | ForEach-Object {
  magick $_.FullName -quality 85 ($_.BaseName + ".webp")
}
```

**Batch convert all JPEGs:**

```powershell
Get-ChildItem -Filter "*.jpg" | ForEach-Object {
  magick $_.FullName -quality 85 ($_.BaseName + ".webp")
}
```

### Quality Settings

| Image Type    | Quality | Command                           |
| ------------- | ------- | --------------------------------- |
| Photos        | 80-85   | `magick img.jpg -quality 85 img.webp` |
| Logos         | 85-90   | `magick logo.png -quality 85 logo.webp` |
| UI elements   | 90      | `magick ui.png -quality 90 ui.webp` |
| Screenshots   | 75-80   | `magick screen.png -quality 75 screen.webp` |

### After Conversion: Clean Up Duplicates

**MANDATORY:** After converting images to WebP, DELETE the original
PNG/JPEG files to prevent file pile-up.

```powershell
# After verifying WebP files work correctly
Remove-Item "image.png"
Remove-Item "photo.jpg"
```

**Batch cleanup:**

```powershell
# Remove all PNGs that have WebP equivalents
Get-ChildItem -Filter "*.png" | Where-Object {
  Test-Path ($_.BaseName + ".webp")
} | Remove-Item

# Remove all JPEGs that have WebP equivalents
Get-ChildItem -Filter "*.jpg" | Where-Object {
  Test-Path ($_.BaseName + ".webp")
} | Remove-Item
```

### Image File Locations

```
apps/customer/public/
├── images/
│   ├── myhibachi-logo.webp     # Main logo
│   ├── hero-bg.webp            # Hero backgrounds
│   └── chefs/                  # Chef photos
│       ├── chef-1.webp
│       └── chef-2.webp
├── My Hibachi logo.webp        # Root logo (legacy path)
└── logo.webp                   # Alternate logo

apps/admin/public/
├── images/
│   └── myhibachi-logo.webp     # Admin logo (same as customer)
└── My Hibachi logo.webp        # Root logo
```

### Using Images in Next.js

```tsx
import Image from 'next/image';

// ✅ CORRECT - Use WebP format
<Image
  src="/images/myhibachi-logo.webp"
  alt="My Hibachi"
  width={120}
  height={40}
  priority // For above-the-fold images
/>

// ❌ WRONG - Never use PNG/JPEG
<Image src="/images/logo.png" ... />
```

### Adding New Images Checklist

When adding new images to the project:

1. **Convert to WebP first:**
   ```powershell
   magick "new-image.png" -quality 85 "new-image.webp"
   ```

2. **Place in correct folder:**
   - Customer: `apps/customer/public/images/`
   - Admin: `apps/admin/public/images/`

3. **Delete original file:**
   ```powershell
   Remove-Item "new-image.png"
   ```

4. **Use in code with .webp extension:**
   ```tsx
   <Image src="/images/new-image.webp" ... />
   ```

5. **Verify build passes:**
   ```powershell
   npm run build
   ```

### Image Size Budgets

| Image Type      | Max Size | Action if Exceeded              |
| --------------- | -------- | ------------------------------- |
| Logo            | 50KB     | Reduce quality or dimensions    |
| Hero background | 200KB    | Use lower quality, resize       |
| Thumbnails      | 20KB     | Resize to display dimensions    |
| Icons           | 5KB      | Use SVG instead                 |

---

## �🔗 Related Docs

- `10-COPILOT_PERFORMANCE.instructions.md` – General performance
- `11-REACT_PERFORMANCE.instructions.md` – React optimization
- [Tailwind CSS v4 docs](https://tailwindcss.com/docs)

