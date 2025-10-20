# Blog Troubleshooting Guide - Common Issues & Solutions

**Date:** October 19, 2025  
**Project:** MyHibachi Customer Portal  
**Scope:** Blog Migration + Client-Side Caching (HIGH #14 & #15)

---

## 📚 Table of Contents

1. [Build Issues](#build-issues)
2. [Cache Issues](#cache-issues)
3. [TypeScript Errors](#typescript-errors)
4. [Performance Issues](#performance-issues)
5. [MDX Content Issues](#mdx-content-issues)
6. [Component Issues](#component-issues)
7. [API Issues](#api-issues)
8. [Deployment Issues](#deployment-issues)

---

## 🔨 Build Issues

### Issue 1: Build Fails with "Cannot find module"

**Error:**
```
Error: Cannot find module '@/lib/cache/CacheService'
```

**Cause:** TypeScript path alias not configured correctly.

**Solution:**
```typescript
// Check tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Verification:**
```powershell
npm run typecheck
```

---

### Issue 2: Build Fails During Static Generation

**Error:**
```
Error: ENOENT: no such file or directory, open 'content/blog/...'
```

**Cause:** MDX files not found in expected location.

**Solution:**
1. Verify content directory exists:
```powershell
Test-Path "content/blog"
```

2. Check file structure:
```powershell
Get-ChildItem -Path "content/blog" -Recurse -Filter "*.mdx"
```

3. Ensure files are committed to git:
```powershell
git status
git add content/blog
```

---

### Issue 3: ESLint Errors Block Build

**Error:**
```
ESLint: Invalid Options: - Unknown options: useEslintrc, extensions
```

**Cause:** ESLint configuration outdated for Next.js 15.

**Solution:**

**File:** `.eslintrc.json`
```json
{
  "extends": ["next/core-web-vitals", "next/typescript"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": "warn"
  }
}
```

**Verification:**
```powershell
npm run lint
```

---

### Issue 4: Out of Memory During Build

**Error:**
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**Cause:** Large number of MDX files (84) + dependencies.

**Solution:**
```powershell
# Increase Node.js memory limit
$env:NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

**Permanent Fix (package.json):**
```json
{
  "scripts": {
    "build": "NODE_OPTIONS='--max-old-space-size=4096' next build"
  }
}
```

---

## 💾 Cache Issues

### Issue 5: Cache Not Working (No Cache Hits)

**Symptoms:**
- Console always shows "Cache miss"
- Data fetches on every page visit
- Cache stats show `hits: 0`

**Diagnosis:**
```javascript
// In browser console
window.blogCache.getStats()
// Expected: { size: >0, hits: >0, hitRate: >0 }
// Actual: { size: 0, hits: 0, hitRate: 0 }
```

**Solution 1: Check Cache Instance**
```typescript
// Verify CacheService is singleton
console.log(window.blogCache === blogCache) // Should be true
```

**Solution 2: Check Hook Implementation**
```typescript
// In useCachedFetch.ts
const cachedData = cache.get(cacheKey);
console.log('[Cache]', cacheKey, cachedData ? 'HIT' : 'MISS');
```

**Solution 3: Verify Cache Key Consistency**
```typescript
// Keys must be identical between cache set and get
const key1 = 'featured-posts-3';
const key2 = 'featured-posts-3'; // ✅ Same
const key3 = 'featured-posts-5'; // ❌ Different
```

---

### Issue 6: Cache Expires Too Quickly

**Symptoms:**
- Cache hit rate <50%
- Frequent refetches
- Poor performance

**Diagnosis:**
```javascript
window.blogCache.getStats()
// Check: hitRate < 0.5
```

**Solution: Adjust TTL Values**

**File:** `apps/customer/src/hooks/useBlogAPI.ts`
```typescript
// Current: 5 minutes
export const blogCache = new CacheService<BlogPost[]>({
  maxSize: 50,
  ttl: 5 * 60 * 1000, // Increase to 10-15 minutes
});

// Recommended for production:
export const blogCache = new CacheService<BlogPost[]>({
  maxSize: 50,
  ttl: 15 * 60 * 1000, // 15 minutes
});
```

---

### Issue 7: Memory Leak (Cache Growing Indefinitely)

**Symptoms:**
- Browser becomes sluggish over time
- Memory usage increases continuously
- Cache size exceeds maxSize

**Diagnosis:**
```javascript
window.blogCache.getStats()
// Check: size > maxSize (should never happen)
```

**Solution 1: Verify LRU Eviction**
```typescript
// In CacheService.ts
private set(key: string, value: T): void {
  if (this.cache.size >= this.maxSize) {
    const oldestKey = this.cache.keys().next().value;
    this.cache.delete(oldestKey);
    this.stats.evictions++;
  }
  // ... rest of set logic
}
```

**Solution 2: Manual Cache Cleanup**
```javascript
// Clear cache periodically (e.g., on route change)
useEffect(() => {
  return () => {
    blogCache.clear();
  };
}, []);
```

**Solution 3: Implement Auto-Pruning**
```typescript
// In CacheService.ts
setInterval(() => {
  this.prune(); // Remove expired entries
}, 60 * 1000); // Every minute
```

---

### Issue 8: Stale Data Displayed

**Symptoms:**
- New blog posts don't appear
- Updated content not showing
- Cache shows old data

**Diagnosis:**
```javascript
// Check cache freshness
const stats = window.blogCache.getStats();
console.log('Last updated:', new Date(stats.lastUpdated));
```

**Solution 1: Manual Cache Invalidation**
```javascript
// In browser console (for testing)
window.blogCache.clear()
location.reload()
```

**Solution 2: Implement Cache Invalidation API**
```typescript
// POST /api/cache/invalidate
export async function POST(req: Request) {
  const { cacheKey } = await req.json();
  
  // Trigger client-side cache clear via WebSocket or polling
  // OR set a cache version in database and check on fetch
  
  return Response.json({ success: true });
}
```

**Solution 3: Add Refresh Button**
```typescript
// In BlogPage component
const handleRefresh = () => {
  blogCache.clear();
  refetch(); // From useCachedFetch hook
};

<button onClick={handleRefresh}>Refresh Content</button>
```

---

## 📝 TypeScript Errors

### Issue 9: "Type 'any' is not assignable" Errors

**Error:**
```typescript
Type 'any' is not assignable to type 'BlogPost[]'
```

**Cause:** Strict mode enabled, implicit `any` not allowed.

**Solution 1: Add Explicit Types**
```typescript
// ❌ Before
const [posts, setPosts] = useState();

// ✅ After
const [posts, setPosts] = useState<BlogPost[]>([]);
```

**Solution 2: Define Proper Interfaces**
```typescript
// types/blog.ts
export interface BlogPost {
  slug: string;
  title: string;
  date: string;
  excerpt: string;
  category: string;
  tags: string[];
  featured?: boolean;
  seasonal?: boolean;
  serviceArea?: string;
  eventType?: string;
  body: string;
}
```

---

### Issue 10: "Cannot find name" Errors

**Error:**
```typescript
Cannot find name 'BlogPost'. Did you mean 'blogPost'?
```

**Cause:** Type not imported or defined.

**Solution:**
```typescript
// Add import at top of file
import type { BlogPost } from '@/types/blog';
```

---

### Issue 11: "Argument of type is not assignable" in useMemo

**Error:**
```typescript
Argument of type 'BlogPost | undefined' is not assignable to parameter of type 'BlogPost'
```

**Cause:** Strict null checks enabled.

**Solution: Add Type Guards**
```typescript
// ❌ Before
const post = useMemo(() => posts.find(p => p.slug === slug), [slug]);

// ✅ After
const post = useMemo(() => {
  return posts.find(p => p.slug === slug) || null;
}, [slug]);

// Or with type assertion
const post = useMemo(() => {
  return posts.find(p => p.slug === slug)!; // Use with caution
}, [slug]);
```

---

## ⚡ Performance Issues

### Issue 12: Slow Initial Page Load

**Symptoms:**
- First page load >3 seconds
- Lighthouse score <70
- Poor Core Web Vitals

**Diagnosis:**
1. Run Lighthouse audit
2. Check Network tab waterfall
3. Analyze bundle size

**Solution 1: Code Splitting**
```typescript
// Dynamic import for heavy components
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />,
  ssr: false, // Disable SSR if client-only
});
```

**Solution 2: Optimize Images**
```typescript
import Image from 'next/image';

// ❌ Before
<img src="/blog-image.jpg" alt="..." />

// ✅ After
<Image 
  src="/blog-image.jpg" 
  alt="..."
  width={800}
  height={600}
  loading="lazy"
  placeholder="blur"
/>
```

**Solution 3: Preload Critical Resources**
```typescript
// In layout.tsx or page.tsx
export const metadata = {
  other: {
    preload: [
      { rel: 'preload', href: '/fonts/font.woff2', as: 'font', type: 'font/woff2' },
    ],
  },
};
```

---

### Issue 13: Cached Pages Still Slow

**Symptoms:**
- Cache hit confirmed
- Still takes >100ms to render
- Browser feels sluggish

**Diagnosis:**
```javascript
// Check render time
console.time('render');
// Navigate to page
console.timeEnd('render');
```

**Solution 1: Optimize React Rendering**
```typescript
// Use React.memo for expensive components
export const ExpensiveComponent = React.memo(({ data }) => {
  // ... component logic
});

// Use useMemo for expensive calculations
const sortedPosts = useMemo(() => {
  return posts.sort((a, b) => a.date.localeCompare(b.date));
}, [posts]);
```

**Solution 2: Virtualize Long Lists**
```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={posts.length}
  itemSize={100}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <BlogPostCard post={posts[index]} />
    </div>
  )}
</FixedSizeList>
```

**Solution 3: Debounce Search Input**
```typescript
import { useDebouncedValue } from '@/hooks/useDebounce';

const [searchQuery, setSearchQuery] = useState('');
const debouncedQuery = useDebouncedValue(searchQuery, 300);

// Use debouncedQuery for filtering
const filteredPosts = useMemo(() => {
  return posts.filter(p => p.title.includes(debouncedQuery));
}, [posts, debouncedQuery]);
```

---

## 📄 MDX Content Issues

### Issue 14: MDX Parsing Errors

**Error:**
```
Unexpected token '<' in MDX
```

**Cause:** Invalid MDX syntax or HTML in content.

**Solution 1: Validate MDX Syntax**
```mdx
<!-- ❌ Invalid -->
<div class="wrapper">Content</div>

<!-- ✅ Valid -->
<div className="wrapper">Content</div>
```

**Solution 2: Escape Special Characters**
```mdx
<!-- ❌ Invalid -->
Use curly braces { like this }

<!-- ✅ Valid -->
Use curly braces \{ like this \}
```

**Solution 3: Use MDX Playground**
Visit: https://mdxjs.com/playground/

---

### Issue 15: Frontmatter Not Parsed

**Symptoms:**
- Post metadata missing
- Title/date/category undefined
- Filtering doesn't work

**Diagnosis:**
```typescript
// In lib/blog.ts
const { data, content } = matter(fileContent);
console.log('Frontmatter:', data); // Check parsed data
```

**Solution: Fix Frontmatter Format**
```mdx
---
title: "Your Post Title"
date: "2024-03-15"
excerpt: "Brief description"
category: "wedding"
tags: ["hibachi", "catering"]
featured: true
seasonal: false
---

Your MDX content here...
```

**Common Mistakes:**
- Missing opening/closing `---`
- Invalid YAML syntax (tabs instead of spaces)
- Unquoted strings with special characters
- Missing required fields

---

## 🧩 Component Issues

### Issue 16: "Hooks can only be called inside body of function component"

**Error:**
```
Error: Hooks can only be called inside the body of a function component
```

**Cause:** Hook called outside React component or in wrong order.

**Solution:**
```typescript
// ❌ Wrong - Hook in regular function
function getData() {
  const { data } = useFeaturedPosts(); // Error!
  return data;
}

// ✅ Correct - Hook in component
function BlogPage() {
  const { data } = useFeaturedPosts(); // ✓
  return <div>{data}</div>;
}
```

---

### Issue 17: Infinite Re-render Loop

**Symptoms:**
- Browser freezes
- Console flooded with logs
- "Maximum update depth exceeded" error

**Diagnosis:**
```typescript
// Add logging to detect loop
useEffect(() => {
  console.log('[RENDER]', Date.now());
}, [/* check dependencies */]);
```

**Solution: Fix useEffect Dependencies**
```typescript
// ❌ Wrong - Missing dependencies or object recreation
useEffect(() => {
  fetchData({ limit: 10 }); // Object recreated each render!
}, [fetchData]); // fetchData might not be stable

// ✅ Correct - Proper dependencies
const options = useMemo(() => ({ limit: 10 }), []);
useEffect(() => {
  fetchData(options);
}, [options, fetchData]);

// Or use useCallback for functions
const fetchData = useCallback(async (opts) => {
  // ... fetch logic
}, []);
```

---

## 🌐 API Issues

### Issue 18: CORS Errors

**Error:**
```
Access to fetch at 'http://localhost:3000/api/blog' from origin '...' has been blocked by CORS
```

**Cause:** API route not allowing cross-origin requests.

**Solution:**
```typescript
// In API route
export async function GET(req: Request) {
  const response = NextResponse.json({ data });
  
  // Add CORS headers
  response.headers.set('Access-Control-Allow-Origin', '*');
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  
  return response;
}
```

---

### Issue 19: API Returns 404

**Symptoms:**
- `/api/blog` returns 404
- Console shows "Failed to fetch"

**Diagnosis:**
```powershell
# Test API directly
curl http://localhost:3000/api/blog
```

**Solution: Verify API Route Exists**
```
apps/customer/src/app/api/blog/
└── route.ts   # Must be named 'route.ts' in App Router
```

---

## 🚀 Deployment Issues

### Issue 20: Build Succeeds Locally But Fails in Production

**Symptoms:**
- `npm run build` works locally
- Vercel/production build fails
- Different errors in CI/CD

**Diagnosis:**
```powershell
# Test production build locally
$env:NODE_ENV="production"
npm run build
```

**Solution 1: Check Environment Variables**
```bash
# Verify .env.local is not committed
# Verify production env vars are set in Vercel/hosting platform

# Required env vars:
NEXT_PUBLIC_GA_MEASUREMENT_ID=...
DATABASE_URL=...
```

**Solution 2: Clean Build**
```powershell
# Remove cached files
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Reinstall and rebuild
npm install
npm run build
```

---

### Issue 21: Static Pages Not Generated

**Symptoms:**
- Blog posts return 404 in production
- `generateStaticParams` not working
- Only homepage accessible

**Diagnosis:**
```typescript
// Check console during build
export async function generateStaticParams() {
  const posts = await getAllPosts();
  console.log('[SSG] Generating', posts.length, 'pages'); // Should show 84
  return posts.map(p => ({ slug: p.slug }));
}
```

**Solution: Verify Build Output**
```
Build Output:
● /blog/[slug]    ← Should show SSG symbol (●)
  ├ /blog/post-1
  ├ /blog/post-2
  └ [+82 more paths]
```

If not showing:
1. Check `getAllPosts()` returns data at build time
2. Verify MDX files are in source control
3. Ensure no async errors in `generateStaticParams`

---

## 🛠️ Debugging Tools

### Browser Console Commands

```javascript
// Check cache status
window.blogCache.getStats()

// View all cached keys
window.blogCache.keys()

// Get specific cached data
window.blogCache.get('featured-posts-3')

// Clear cache
window.blogCache.clear()

// Test cache manually
window.blogCache.set('test-key', { data: 'test' }, 60000)
window.blogCache.get('test-key')
```

### Development Tools

```powershell
# TypeScript check
npm run typecheck

# Lint check
npm run lint

# Build check
npm run build

# Test dev server
npm run dev

# Analyze bundle
npm run analyze # (if bundle analyzer installed)
```

---

## 📞 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review error messages carefully
3. ✅ Search GitHub Issues
4. ✅ Check Next.js documentation
5. ✅ Enable verbose logging

### How to Report an Issue

**Include:**
- Error message (full stack trace)
- Steps to reproduce
- Expected vs actual behavior
- Environment (Node version, OS, browser)
- Relevant code snippets
- Screenshots (if applicable)

**Template:**
```markdown
## Issue Description
[Brief description]

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Node.js: v18.17.0
- Next.js: 15.5.4
- Browser: Chrome 120
- OS: Windows 11

## Error Message
```
[Full error message]
```

## Additional Context
[Any other relevant information]
```

---

**Last Updated:** October 19, 2025  
**Maintained By:** Development Team  
**Status:** Living Document (update as new issues discovered)
