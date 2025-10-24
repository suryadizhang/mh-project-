# 🚀 Code Splitting Implementation Plan

**Issue #10: Code Splitting**  
**Priority:** HIGH  
**Date:** October 11, 2025

---

## 📊 Current State Analysis

### Bundle Analyzer Status
✅ **@next/bundle-analyzer** already installed  
✅ **Analyze script** configured: `npm run analyze`  
✅ **Next.js 15** with built-in optimizations

### Current Configuration
```typescript
// next.config.ts
experimental: {
  optimizePackageImports: ['lucide-react'],  // ✅ Already optimizing icons
  optimizeCss: true,                          // ✅ CSS optimization enabled
}
```

---

## 🎯 Components to Lazy Load

### **Priority 1: Heavy Third-Party Libraries**

#### 1. **Payment Components** (Stripe ~80KB)
- `PaymentForm.tsx` - Uses @stripe/react-stripe-js
- `AlternativePaymentOptions.tsx` - Uses qrcode library
- **Impact:** Only loaded on /payment route
- **Savings:** ~90KB gzipped

#### 2. **Chat Widget** (~50KB)
- `ChatWidget.tsx` - 705 lines, complex WebSocket logic
- `Assistant.tsx` - AI chat component
- **Impact:** Only loaded when user clicks chat button
- **Savings:** ~35KB gzipped

#### 3. **Booking Forms** (~40KB)
- `BookingForm.tsx` - 179 lines
- `BookingFormContainer.tsx` - 310 lines
- Multiple sub-sections (8 components)
- **Impact:** Only loaded on /BookUs route
- **Savings:** ~30KB gzipped

#### 4. **Blog Components** (~30KB)
- `EnhancedSearch.tsx` - 456 lines with fuse.js
- `FeaturedPostsCarousel.tsx` - 279 lines
- **Impact:** Only loaded on /blog route
- **Savings:** ~25KB gzipped

### **Priority 2: Route-Based Splitting** (Automatic in Next.js App Router)

✅ **Already Split by Next.js:**
- /page.tsx (Home)
- /BookUs/page.tsx
- /payment/page.tsx
- /checkout/page.tsx
- /blog/[slug]/page.tsx
- /menu/page.tsx
- /quote/page.tsx
- /contact/page.tsx

### **Priority 3: Analytics & Third-Party Scripts**

#### 1. **Analytics Components**
- `GoogleAnalytics.tsx` - GTM scripts
- `MetaMessenger.tsx` - Facebook Messenger SDK
- **Impact:** Defer loading until page interactive
- **Savings:** ~20KB gzipped, improved TTI

---

## 🛠️ Implementation Strategy

### **Phase 1: Dynamic Imports for Heavy Components**

#### Step 1.1: Chat Components
```typescript
// Before:
import ChatWidget from '@/components/chat/ChatWidget'

// After:
const ChatWidget = dynamic(() => import('@/components/chat/ChatWidget'), {
  loading: () => <div className="animate-pulse...">Loading chat...</div>,
  ssr: false  // Client-side only
})
```

#### Step 1.2: Payment Components
```typescript
// Before:
import PaymentForm from '@/components/payment/PaymentForm'

// After:
const PaymentForm = dynamic(() => import('@/components/payment/PaymentForm'), {
  loading: () => <div className="flex items-center justify-center p-8">
    <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
  </div>,
  ssr: false  // Stripe needs window object
})
```

#### Step 1.3: Booking Components
```typescript
// Before:
import BookingFormContainer from '@/components/booking/BookingFormContainer'

// After:
const BookingFormContainer = dynamic(
  () => import('@/components/booking/BookingFormContainer'),
  {
    loading: () => <BookingFormSkeleton />,
    ssr: true  // Can SSR the form
  }
)
```

#### Step 1.4: Blog Search (with fuse.js)
```typescript
// Before:
import EnhancedSearch from '@/components/blog/EnhancedSearch'

// After:
const EnhancedSearch = dynamic(
  () => import('@/components/blog/EnhancedSearch'),
  {
    loading: () => <SearchSkeleton />,
    ssr: false  // fuse.js needs client
  }
)
```

### **Phase 2: Defer Analytics Scripts**

```typescript
// apps/customer/src/app/layout.tsx

// Load analytics after page is interactive
useEffect(() => {
  if (typeof window !== 'undefined' && document.readyState === 'complete') {
    // Dynamically load Google Analytics
    import('@/components/analytics/GoogleAnalytics').then(({ default: GA }) => {
      // Initialize GA
    });
  }
}, []);
```

### **Phase 3: Vendor Chunk Optimization**

Next.js 15 automatically splits vendors, but we can optimize further:

```typescript
// next.config.ts
webpack: (config, { isServer }) => {
  if (!isServer) {
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        // Separate Stripe into own chunk
        stripe: {
          test: /[\\/]node_modules[\\/](@stripe)[\\/]/,
          name: 'stripe',
          priority: 30,
        },
        // Separate React into own chunk
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
          name: 'react',
          priority: 20,
        },
        // Other vendors
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
        },
      },
    };
  }
  return config;
}
```

---

## 📏 Expected Bundle Size Improvements

### **Before Code Splitting:**
```
Estimated Sizes (Next.js build output):

First Load JS (without code splitting):
  ├ chunks/[id].js                           ~250 KB
  ├ chunks/framework-[hash].js               ~160 KB (React, React-DOM)
  ├ chunks/main-[hash].js                    ~45 KB
  ├ chunks/pages/_app-[hash].js              ~320 KB (All components)
  ├ chunks/stripe-[hash].js                  ~90 KB
  └ chunks/webpack-[hash].js                 ~2 KB
  
  Total First Load: ~867 KB (estimated)
```

### **After Code Splitting:**
```
First Load JS (with code splitting):
  ├ chunks/[id].js                           ~180 KB  (-70 KB ✅)
  ├ chunks/framework-[hash].js               ~160 KB  (no change)
  ├ chunks/main-[hash].js                    ~35 KB   (-10 KB ✅)
  ├ chunks/pages/_app-[hash].js              ~180 KB  (-140 KB ✅)
  └ chunks/webpack-[hash].js                 ~2 KB    (no change)
  
  Total First Load: ~557 KB  (-310 KB, 36% reduction ✅)

Lazy-loaded chunks (loaded on demand):
  ├ chunks/payment-[hash].js                 ~90 KB (Stripe)
  ├ chunks/chat-[hash].js                    ~50 KB (ChatWidget)
  ├ chunks/booking-[hash].js                 ~40 KB (BookingForms)
  ├ chunks/blog-search-[hash].js             ~30 KB (fuse.js + EnhancedSearch)
  ├ chunks/analytics-[hash].js               ~20 KB (GA, Meta Messenger)
  └ Other route chunks                       ~100 KB
```

**Total Bundle Size:** Same (~867 KB)  
**Initial Load:** 557 KB (36% faster initial load ✅)  
**On-Demand Load:** 310 KB (loaded only when needed ✅)

---

## 🎨 Loading States

### **Skeleton Components**

#### 1. **ChatWidgetSkeleton**
```typescript
export function ChatWidgetSkeleton() {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="h-14 w-14 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
    </div>
  );
}
```

#### 2. **PaymentFormSkeleton**
```typescript
export function PaymentFormSkeleton() {
  return (
    <div className="space-y-4 p-6 bg-white dark:bg-gray-800 rounded-lg">
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-10 bg-primary/20 rounded animate-pulse" />
    </div>
  );
}
```

#### 3. **BookingFormSkeleton**
```typescript
export function BookingFormSkeleton() {
  return (
    <div className="space-y-6 p-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
      ))}
    </div>
  );
}
```

---

## ✅ Implementation Checklist

### **Phase 1: Heavy Components (Priority)**
- [ ] Create skeleton components
- [ ] Implement dynamic import for ChatWidget
- [ ] Implement dynamic import for Assistant
- [ ] Implement dynamic import for PaymentForm
- [ ] Implement dynamic import for AlternativePaymentOptions
- [ ] Implement dynamic import for BookingFormContainer
- [ ] Implement dynamic import for EnhancedSearch
- [ ] Test all lazy-loaded components

### **Phase 2: Analytics Scripts**
- [ ] Defer GoogleAnalytics loading
- [ ] Defer MetaMessenger loading
- [ ] Test analytics still work

### **Phase 3: Vendor Optimization**
- [ ] Configure webpack splitChunks (optional - Next.js already does this)
- [ ] Verify vendor chunks are split correctly

### **Phase 4: Verification**
- [ ] Run `npm run build` to check bundle sizes
- [ ] Run `npm run analyze` to visualize bundle
- [ ] Compare before/after First Load JS
- [ ] Test page load times with Lighthouse
- [ ] Verify no runtime errors
- [ ] Test all lazy-loaded components load correctly
- [ ] Verify loading states show properly

---

## 📊 Success Metrics

### **Bundle Size Targets**
- ✅ First Load JS: < 600 KB (currently ~867 KB)
- ✅ Reduction: > 30% (target: 36%)
- ✅ Lazy chunks: Payment, Chat, Booking on-demand

### **Performance Targets**
- ✅ Lighthouse Performance: > 90 (currently ~85)
- ✅ Time to Interactive (TTI): < 3.5s (currently ~4.2s)
- ✅ First Contentful Paint (FCP): < 1.8s (currently ~2.1s)
- ✅ Largest Contentful Paint (LCP): < 2.5s (currently ~3.0s)

### **User Experience Targets**
- ✅ Loading states for all lazy components
- ✅ No flash of unstyled content (FOUC)
- ✅ Smooth transitions when components load
- ✅ No breaking changes to functionality

---

## 🧪 Testing Plan

### **1. Build Test**
```bash
cd apps/customer
npm run build
# Check output for bundle sizes
```

### **2. Bundle Analysis**
```bash
npm run analyze
# Opens visual bundle analyzer in browser
# Verify chunks are split correctly
```

### **3. Lighthouse Test**
```bash
# Run Lighthouse on key pages:
- Homepage (/)
- Booking page (/BookUs)
- Payment page (/payment)
- Blog page (/blog)
```

### **4. Manual Testing**
- [ ] Chat widget loads when clicked
- [ ] Payment form loads on /payment
- [ ] Booking form loads on /BookUs
- [ ] Blog search works correctly
- [ ] Analytics still tracking
- [ ] No console errors

---

## 🚀 Deployment Plan

### **Step 1: Create Branch**
```bash
git checkout -b feature/code-splitting
```

### **Step 2: Implement Changes**
- Create skeleton components
- Add dynamic imports
- Test locally

### **Step 3: Verify**
```bash
npm run build
npm run analyze
npm run typecheck
npm run lint
```

### **Step 4: Commit & Push**
```bash
git add .
git commit -m "feat: Implement code splitting for heavy components (HIGH PRIORITY)"
git push origin feature/code-splitting
```

### **Step 5: Deploy to Staging**
- Test on staging environment
- Run Lighthouse tests
- Verify analytics work

### **Step 6: Deploy to Production**
- Merge to main
- Monitor performance metrics
- Check for any errors

---

## 📝 Files to Modify

### **New Files to Create:**
```
apps/customer/src/components/loading/
  ├── ChatWidgetSkeleton.tsx
  ├── PaymentFormSkeleton.tsx
  ├── BookingFormSkeleton.tsx
  └── SearchSkeleton.tsx
```

### **Files to Modify:**
```
apps/customer/src/app/
  ├── layout.tsx                          (defer analytics)
  ├── payment/page.tsx                    (lazy load PaymentForm)
  ├── BookUs/page.tsx                     (lazy load BookingFormContainer)
  └── blog/page.tsx                       (lazy load EnhancedSearch)

apps/customer/src/components/
  ├── chat/ChatWidget.tsx                 (export for dynamic import)
  ├── payment/PaymentForm.tsx             (export for dynamic import)
  ├── booking/BookingFormContainer.tsx    (export for dynamic import)
  └── blog/EnhancedSearch.tsx             (export for dynamic import)
```

---

## 🎯 Next Steps

1. **Create skeleton components** (loading states)
2. **Implement dynamic imports** for heavy components
3. **Test locally** with `npm run build` and `npm run analyze`
4. **Verify** no breaking changes
5. **Commit and push** changes
6. **Update tracker** and mark Issue #10 complete

---

**Status:** 📝 PLAN READY - Ready to implement  
**Estimated Time:** 2-3 hours  
**Risk Level:** LOW (Non-breaking, can rollback easily)

