---
applyTo: 'apps/customer/**,apps/admin/**'
---

# My Hibachi – Lighthouse & Core Web Vitals Standards

**Priority: HIGH** – Follow these rules to maintain 80+ Lighthouse
scores.

---

## 🎯 Target Metrics (Enterprise Standards)

| Metric                       | Target  | Critical Threshold |
| ---------------------------- | ------- | ------------------ |
| **Performance (Mobile)**     | 80+     | Never below 70     |
| **LCP (Largest Contentful)** | < 2.5s  | < 4.0s             |
| **FCP (First Contentful)**   | < 1.8s  | < 3.0s             |
| **TBT (Total Blocking)**     | < 200ms | < 600ms            |
| **CLS (Layout Shift)**       | < 0.1   | < 0.25             |
| **Accessibility**            | 95+     | Never below 90     |
| **Best Practices**           | 90+     | Never below 85     |
| **SEO**                      | 100     | Never below 95     |

**Note:** Slow 4G throttling (1.6 Mbps) is the test baseline. Real
users on 4G/5G/WiFi will experience better performance.

---

## 🖼️ Image Optimization (MANDATORY)

### File Format Rules:

| Use Case         | Format   | Max Size | Notes                    |
| ---------------- | -------- | -------- | ------------------------ |
| Photos/Hero      | **WebP** | 100 KB   | Use `<picture>` fallback |
| Logos/Icons      | **SVG**  | 20 KB    | Scalable, tiny           |
| Complex graphics | **WebP** | 150 KB   | Or AVIF for modern       |
| Fallback only    | JPEG     | 200 KB   | For old browsers         |

### Image Sizing Rules:

```bash
# Hero/Banner images: max 1920px width
magick input.jpg -resize 1920x -quality 75 output.webp

# Content images: max 800px width
magick input.jpg -resize 800x -quality 80 output.webp

# Thumbnails: max 400px width
magick input.jpg -resize 400x -quality 80 output.webp

# Logos: actual display size only
magick logo.png -resize 200x -quality 80 logo-small.webp
```

### ❌ NEVER DO:

- Upload images larger than 500 KB
- Use PNG for photos (use WebP)
- Use unoptimized logos (resize to display size)
- Reference same image with different paths

### ✅ ALWAYS DO:

- Convert to WebP before committing
- Size images to actual display dimensions
- Use `<picture>` for LCP images with fallbacks
- Preload LCP images in `<head>`

---

## 📦 JavaScript Bundle Rules

### Code-Splitting (MANDATORY for large components):

```tsx
// ❌ BAD - Imports entire library into main bundle
import { Calendar } from 'react-day-picker';
import { motion } from 'framer-motion';

// ✅ GOOD - Dynamic import for below-fold components
const LazyCalendar = dynamic(() => import('react-day-picker'), {
  loading: () => <Skeleton />,
  ssr: false,
});
```

### When to Lazy Load:

| Component Type                 | Lazy Load? | SSR? |
| ------------------------------ | ---------- | ---- |
| Above-the-fold content         | ❌ No      | ✅   |
| Below-fold sections            | ✅ Yes     | ✅   |
| Modals/Dialogs                 | ✅ Yes     | ❌   |
| Forms (booking, payment)       | ✅ Yes     | ❌   |
| Icons libraries (lucide-react) | ✅ Yes     | ✅   |
| Charts/Visualizations          | ✅ Yes     | ❌   |
| Chat widgets                   | ✅ Yes     | ❌   |

### Package Import Optimization:

Always add heavy packages to `next.config.ts`:

```typescript
experimental: {
  optimizePackageImports: [
    'lucide-react',      // Tree-shake icons
    'date-fns',          // Tree-shake date utils
    'framer-motion',     // Tree-shake animations
    '@radix-ui/react-*', // Tree-shake UI primitives
  ],
},
```

---

## 🎨 CSS Performance Rules

### Critical CSS (Above-the-fold):

```typescript
// In layout.tsx - inline critical CSS
<style id="critical-css" dangerouslySetInnerHTML={{ __html: criticalCSS }} />
```

**Critical CSS must include:**

- CSS reset/normalize
- Body/html base styles
- Navbar styles
- Hero section styles
- First visible content
- Responsive breakpoints for above-fold

### CSS Loading Strategy:

| CSS Type              | Loading Method     | Blocking? |
| --------------------- | ------------------ | --------- |
| Critical (above-fold) | Inline in `<head>` | Yes       |
| Page-specific         | Import in page.tsx | No        |
| Component-specific    | CSS Modules        | No        |
| Third-party           | Async load         | No        |

### ❌ NEVER DO:

- Import all CSS in layout.tsx (loads on every page)
- Use `@import` in CSS files (blocks rendering)
- Create duplicate CSS rules across files

### ✅ ALWAYS DO:

- Use CSS variables for repeated values
- Scope CSS to components (CSS Modules)
- Consolidate background images to one location
- Use WebP for CSS background-image

---

## 🔤 Font Optimization

### Font Loading Configuration:

```typescript
// In layout.tsx
const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap', // REQUIRED - prevents invisible text
  preload: true, // Only for critical fonts
});

const poppins = Poppins({
  variable: '--font-poppins',
  subsets: ['latin'],
  weight: ['400', '700'], // Only weights you USE
  display: 'swap',
  preload: true,
});

// Non-critical fonts
const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin'],
  display: 'swap',
  preload: false, // Don't preload non-critical
});
```

### Font Rules:

| Rule                             | Reason                      |
| -------------------------------- | --------------------------- |
| Max 2-3 font families            | Each font = network request |
| Max 2-3 weights per font         | Each weight = more bytes    |
| Always `display: 'swap'`         | Prevents invisible text     |
| Only preload critical fonts      | Reduce initial load         |
| Use system fonts for code blocks | No extra download           |

---

## 📡 Caching & CDN Rules

### Vercel/CDN Cache Headers:

```json
{
  "headers": [
    {
      "source": "/_next/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/images/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### Cache Duration Guide:

| Asset Type        | Cache Duration | Header                                 |
| ----------------- | -------------- | -------------------------------------- |
| `/_next/static/*` | 1 year         | `max-age=31536000, immutable`          |
| `/images/*`       | 1 year         | `max-age=31536000, immutable`          |
| `/videos/*`       | 1 year         | `max-age=31536000, immutable`          |
| `/fonts/*`        | 1 year         | `max-age=31536000, immutable`          |
| HTML pages        | 1 hour         | `max-age=3600, stale-while-revalidate` |
| API responses     | Varies         | Based on data freshness needs          |

---

## 🚀 LCP Optimization Checklist

The Largest Contentful Paint is usually the hero image. Optimize it:

### 1. Image Preparation:

```bash
# Create optimized WebP
magick hero.jpg -resize 1920x -quality 75 hero.webp
# Should be < 100 KB
```

### 2. HTML Structure:

```tsx
// Use native <picture> for LCP - NO JavaScript dependency
<picture>
  <source srcSet="/images/hero.webp" type="image/webp" />
  <source srcSet="/images/hero.avif" type="image/avif" />
  <img
    src="/images/hero.jpg"
    alt="Hero"
    width={1920}
    height={1080}
    decoding="sync"
    fetchPriority="high"
  />
</picture>
```

### 3. Preload in Head:

```tsx
<link
  rel="preload"
  as="image"
  href="/images/hero.webp"
  type="image/webp"
  fetchPriority="high"
/>
```

### 4. Avoid LCP Killers:

| ❌ Don't                            | ✅ Do                             |
| ----------------------------------- | --------------------------------- |
| Load hero via JavaScript            | Use native `<img>` or `<picture>` |
| Use CSS background-image for hero   | Use HTML image element            |
| Lazy load LCP image                 | Eager load with fetchPriority     |
| Use client component for hero image | Server component                  |

---

## 📊 Third-Party Script Rules

### Loading Strategy:

```tsx
// Google Analytics - load after interaction
<Script
  src="https://www.googletagmanager.com/gtag/js"
  strategy="afterInteractive"
/>

// Non-critical scripts - load when idle
<Script src="/scripts/chat-widget.js" strategy="lazyOnload" />

// Critical scripts only - load immediately
<Script src="/scripts/critical.js" strategy="beforeInteractive" />
```

### Third-Party Impact:

| Script           | Impact    | Strategy             |
| ---------------- | --------- | -------------------- |
| Google Analytics | Medium    | `afterInteractive`   |
| Google Fonts     | Medium    | Preconnect + display |
| Chat widgets     | High      | `lazyOnload`         |
| Payment (Stripe) | High      | Load on payment page |
| Social embeds    | Very High | Lazy load on scroll  |

---

## ✅ Pre-Commit Performance Checklist

Before adding new images or components:

- [ ] Images converted to WebP and < 100 KB
- [ ] Images sized to actual display dimensions
- [ ] Heavy components lazy-loaded
- [ ] New packages added to optimizePackageImports
- [ ] No new fonts without approval
- [ ] CSS scoped to component (not global)
- [ ] LCP element not behind JavaScript

---

## 🔍 Lighthouse Testing Requirements

### When to Test:

| Trigger                  | Required? |
| ------------------------ | --------- |
| New images added         | ✅ Yes    |
| New page created         | ✅ Yes    |
| Major component changes  | ✅ Yes    |
| New third-party scripts  | ✅ Yes    |
| CSS architecture changes | ✅ Yes    |
| Minor text changes       | ❌ No     |

### How to Test:

1. Run production build: `npm run build`
2. Use Chrome DevTools Lighthouse
3. Test on "Mobile" with "Slow 4G throttling"
4. Score must meet targets before merge

---

## 📁 File Organization for Performance

```
public/
├── images/
│   ├── hero-poster.webp     # LCP image (< 100 KB)
│   ├── background.webp      # Shared background (< 200 KB)
│   └── icons/               # SVG icons
├── videos/
│   └── hero_video.mp4       # Compressed (< 2 MB)
└── fonts/                   # Self-hosted fonts only

src/
├── lib/performance/
│   ├── criticalCSS.ts       # Inlined CSS
│   ├── lazyComponents.ts    # Dynamic imports
│   └── AsyncCSSLoader.tsx   # Deferred CSS
└── styles/
    ├── globals.css          # Only truly global styles
    └── pages/               # Page-specific CSS
```

---

## 🔗 Related Docs

- `14-MEDIA_OPTIMIZATION.instructions.md` – ImageMagick/FFmpeg
  commands
- `11-REACT_PERFORMANCE.instructions.md` – React re-render prevention
- `12-CSS_ARCHITECTURE.instructions.md` – Tailwind v4 patterns
