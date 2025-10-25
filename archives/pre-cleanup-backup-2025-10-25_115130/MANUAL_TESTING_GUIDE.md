# Manual Testing Guide - HIGH #14 & #15

**Date:** October 19, 2025  
**Tester:** Development Team  
**Features Tested:** Client-Side Caching (HIGH #14) + TypeScript Strict Mode (HIGH #15)

---

## 🎯 Testing Objectives

1. Verify client-side cache functionality works correctly
2. Confirm data loads properly on first visit (cache miss)
3. Verify subsequent visits use cached data (cache hit)
4. Test all 6 updated components
5. Validate cache statistics and performance
6. Ensure no console errors or TypeScript issues

---

## 📋 Pre-Testing Checklist

- [x] Dev server running on http://localhost:3000
- [x] Production build succeeds (4.3s compile, 135 pages)
- [x] TypeScript strict mode enabled (0 errors)
- [x] All 6 components updated with caching hooks

---

## 🧪 Test Cases

### **Test 1: Blog Page - Cache Miss → Cache Hit**

**Steps:**
1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Navigate to http://localhost:3000/blog
4. **Expected (First Load - Cache Miss):**
   - Console shows: "Cache miss for key: ..."
   - Blog posts load from API
   - Featured posts section displays
   - Seasonal posts section displays
   - Recent posts section displays
   - Load time: ~200-500ms

5. Navigate away (e.g., click "Home")
6. Navigate back to /blog
7. **Expected (Second Load - Cache Hit):**
   - Console shows: "Cache hit for key: ..."
   - Blog posts load instantly from cache
   - All sections display immediately
   - Load time: <10ms (99% faster!)

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 2: Blog Search - Cached Filter Options**

**Steps:**
1. Clear browser cache (Ctrl+Shift+Del)
2. Navigate to http://localhost:3000/blog
3. Open DevTools Console
4. Click on "Categories" dropdown
5. **Expected (First Load):**
   - Console: "Fetching categories..."
   - Categories load from API
   - All category options display

6. Navigate away and back
7. Click on "Categories" dropdown again
8. **Expected (Second Load):**
   - Console: "Cache hit for categories"
   - Categories load instantly
   - No API call made (check Network tab)

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 3: Featured Posts Carousel - Conditional Logic**

**Steps:**
1. Navigate to http://localhost:3000 (homepage)
2. Scroll to Featured Posts Carousel
3. **Expected:**
   - If featured posts >= 3: Shows featured posts
   - If featured posts < 3: Shows recent posts instead
   - Carousel animates smoothly
   - No loading flicker on second visit

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 4: Cache Statistics**

**Steps:**
1. Navigate to http://localhost:3000/blog
2. Open DevTools Console
3. Run: `window.blogCache.getStats()`
4. **Expected Output:**
```javascript
{
  size: 5,           // Number of cached items
  maxSize: 50,       // Maximum cache capacity
  hits: 12,          // Cache hit count
  misses: 5,         // Cache miss count
  hitRate: 0.71,     // 71% hit rate
  sets: 5,           // Items added to cache
  evictions: 0       // Items evicted (should be 0)
}
```

5. Navigate between pages multiple times
6. Run `window.blogCache.getStats()` again
7. **Expected:**
   - hits increases with each cached access
   - hitRate improves over time
   - evictions remains 0 (unless 50+ items cached)

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 5: Trending Posts Component**

**Steps:**
1. Navigate to http://localhost:3000
2. Scroll to Trending Posts section
3. Open Network tab in DevTools
4. **Expected (First Load):**
   - API call to /api/blog
   - Posts display correctly
   - Proper rendering

5. Navigate away and back
6. **Expected (Second Load):**
   - No API call (check Network tab)
   - Posts load instantly from cache
   - Same content displays

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 6: Enhanced Search Component**

**Steps:**
1. Navigate to http://localhost:3000/blog
2. Use search box to search for "hibachi"
3. **Expected:**
   - Search results display
   - Filter by category works
   - Filter by tag works
   - Cached posts used for filtering

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 7: Advanced Tag Cloud**

**Steps:**
1. Navigate to http://localhost:3000/blog
2. Scroll to Tag Cloud section
3. **Expected:**
   - Tags display with proper sizing
   - Click tag filters posts
   - Tag calculations use cached posts
   - No lag when hovering tags

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 8: TypeScript Strict Mode - No Errors**

**Steps:**
1. Open DevTools Console
2. Navigate through entire application:
   - http://localhost:3000
   - http://localhost:3000/blog
   - http://localhost:3000/blog/[any-post]
   - http://localhost:3000/BookUs
   - http://localhost:3000/menu

3. **Expected:**
   - No TypeScript errors in console
   - No "undefined" or "null" errors
   - No type-related warnings
   - All features work as expected

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 9: Cache TTL Expiration**

**Steps:**
1. Navigate to http://localhost:3000/blog
2. Wait 6 minutes (TTL is 5 minutes)
3. Navigate to different page and back to /blog
4. **Expected:**
   - Console shows "Cache expired, refetching..."
   - New API call made
   - Fresh data loaded
   - Cache statistics show new miss + set

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

### **Test 10: Memory Management**

**Steps:**
1. Open browser for extended period
2. Navigate between pages 100+ times
3. Run: `window.blogCache.getStats()`
4. **Expected:**
   - Cache size never exceeds 50 items
   - evictions > 0 (LRU eviction working)
   - No memory leaks
   - Browser remains responsive

**Result:** ✅ PASS / ❌ FAIL  
**Notes:**

---

## 🔍 Validation Commands

### Check Cache in Browser Console:
```javascript
// Get cache statistics
window.blogCache.getStats()

// Check if specific data is cached
window.blogCache.has('featured-posts-3')

// Manually clear cache (for testing)
window.blogCache.clear()

// Get all cache entries
window.blogCache.keys()
```

### Check Build Output:
```powershell
# From apps/customer directory
npm run build

# Expected output:
# ✓ Compiled successfully in ~4-5s
# ✓ Generating static pages (135/135)
# First Load JS shared by all: 103 kB
```

### Check TypeScript:
```powershell
# From apps/customer directory
npm run typecheck

# Expected output:
# 0 errors
```

---

## 📊 Performance Metrics

### Expected Results:

| Metric | Before Caching | After Caching | Improvement |
|--------|---------------|---------------|-------------|
| **First Load (Cache Miss)** | ~300ms | ~300ms | 0% (baseline) |
| **Second Load (Cache Hit)** | ~300ms | <10ms | **~97%** |
| **API Calls per Page** | 5-10 | 1-2 | **80% reduction** |
| **Cache Hit Rate** | N/A | >90% | N/A |
| **Bundle Size** | 103 kB | 103 kB | 0% (no increase) |

---

## ✅ Acceptance Criteria

- [ ] All 10 test cases PASS
- [ ] No console errors during testing
- [ ] Cache hit rate >90% after multiple visits
- [ ] Page load time <10ms for cached content
- [ ] TypeScript strict mode: 0 errors
- [ ] Production build succeeds
- [ ] No memory leaks detected
- [ ] All 6 components render correctly

---

## 🐛 Issues Found

| Issue # | Component | Description | Severity | Status |
|---------|-----------|-------------|----------|--------|
| - | - | - | - | - |

---

## 📝 Notes

- Dev server started successfully in 2.2s
- Production build compiled in 4.3s
- 135 static pages generated (84 blog posts)
- All TypeScript checks passed
- No ESLint errors blocking build

---

## ✅ Manual Testing Completed

**Date:** _______________  
**Tester:** _______________  
**Overall Result:** ✅ PASS / ❌ FAIL  
**Additional Comments:**

---

**Next Step:** Proceed to Performance Testing (Step 8) with Lighthouse audit
