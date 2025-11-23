# Visual Testing Checklist - Bootstrap Cleanup ✅

## 🎯 Testing URL

**Dev Server**: http://localhost:3000

## 📋 Components to Verify (8 Fixed)

### 1. **Navbar** (CRITICAL)

**File**: `apps/customer/src/components/layout/Navbar.tsx`

**Test Steps**:

- [ ] Navigate to homepage
- [ ] Verify all 7 navigation icons display correctly:
  - [ ] 🏠 Home icon (House)
  - [ ] 🍴 Menu icon (Utensils Crossed)
  - [ ] 🧮 Get Quote icon (Calculator)
  - [ ] 📅 Book Us icon (Calendar)
  - [ ] ❓ FAQs icon (Help Circle)
  - [ ] 💬 Contact icon (Message Circle)
  - [ ] 📖 Blog icon (Book Open)
- [ ] Verify icon sizes (18px) and spacing
- [ ] Click each link - verify active state highlights correctly
- [ ] Test Mobile Menu:
  - [ ] Resize to mobile (< 768px)
  - [ ] Click hamburger icon (☰) - menu opens
  - [ ] Click X icon - menu closes
  - [ ] Click any nav link - menu closes automatically
- [ ] Test hover states on nav links
- [ ] Verify logo displays correctly
- [ ] Check navbar sticky behavior on scroll

**Expected Result**: All icons render, mobile menu toggles correctly,
active states work

---

### 2. **Footer** (CRITICAL)

**File**: `apps/customer/src/components/layout/Footer.tsx`

**Test Steps**:

- [ ] Scroll to page bottom
- [ ] Verify social media icons (top section):
  - [ ] Instagram icon (24px)
  - [ ] Facebook icon (24px)
  - [ ] Yelp/External Link icon (24px)
- [ ] Verify Quick Links chevron icons (16px):
  - [ ] Home → with chevron
  - [ ] Menu → with chevron
  - [ ] Book Us → with chevron
  - [ ] Get Quote → with chevron
  - [ ] Contact → with chevron
- [ ] Verify Legal section icons (16px):
  - [ ] Privacy Policy (Shield icon)
  - [ ] Terms & Conditions (File Text icon)
- [ ] Verify Contact Us icons (18px):
  - [ ] 📍 Service area (Map Pin)
  - [ ] ☎️ Phone (Phone)
  - [ ] ✉️ Email (Mail)
  - [ ] 💬 Facebook Messenger (Message Circle)
  - [ ] 📷 Instagram DM (Instagram)
- [ ] Test all footer links (click and verify navigation)
- [ ] Verify icon hover states (if any)

**Expected Result**: All icons display correctly, links work, hover
states intact

---

### 3. **Back to Top Button**

**File**: `apps/customer/src/components/ui/BackToTopButton.tsx`

**Test Steps**:

- [ ] Navigate to any page with scroll (e.g., blog)
- [ ] Scroll down 300px - button should appear
- [ ] Verify ArrowUp icon (20px) displays correctly
- [ ] Click button - page smoothly scrolls to top
- [ ] Verify button hover state
- [ ] Scroll back up - button should disappear

**Expected Result**: Button appears/disappears on scroll, smooth
scroll animation works

---

### 4. **Breadcrumb**

**File**: `apps/customer/src/components/ui/Breadcrumb.tsx`

**Test Steps**:

- [ ] Navigate to multi-level pages:
  - [ ] `/blog` - should show: Home > Blog
  - [ ] `/blog/[slug]` - should show: Home > Blog > [Post Title]
  - [ ] `/menu` - should show: Home > Menu
- [ ] Verify ChevronRight icon (14px) as separator between breadcrumbs
- [ ] Verify breadcrumb links are clickable (except current page)
- [ ] Verify current page is not a link
- [ ] Check breadcrumb hover states
- [ ] Test on light and dark backgrounds (if applicable)

**Expected Result**: Breadcrumbs generate correctly, chevron
separators display, links work

---

### 5. **BlogCard** (Already Clean - Verify)

**File**: `apps/customer/src/components/blog/BlogCard.tsx`

**Test Steps**:

- [ ] Navigate to `/blog`
- [ ] Verify blog post card icons:
  - [ ] 📅 Calendar icon (date)
  - [ ] 👤 User icon (author)
  - [ ] ⏱️ Clock icon (read time)
- [ ] Verify expand/collapse icons:
  - [ ] ChevronDown when collapsed
  - [ ] ChevronUp when expanded
- [ ] Click expand button - verify smooth animation
- [ ] Check multiple cards render correctly

**Expected Result**: All Lucide icons display (no Bootstrap Icons)

---

### 6. **BlogTags** (Already Clean - Verify)

**File**: `apps/customer/src/components/blog/BlogTags.tsx`

**Test Steps**:

- [ ] Navigate to `/blog`
- [ ] Verify Tag icon (🏷️) in header
- [ ] Verify Filter icon for "Show All Tags"
- [ ] Verify X icon for "Clear All" button
- [ ] Click tags - verify selected state (X icon appears for removal)
- [ ] Test tag counts display correctly
- [ ] Test "Clear All" clears all selected tags

**Expected Result**: All Lucide icons display, tag filtering works

---

### 7. **BlogSearch** (Already Clean - Verify)

**File**: `apps/customer/src/components/blog/BlogSearch.tsx`

**Test Steps**:

- [ ] Navigate to `/blog`
- [ ] Verify Search icon (🔍) in search input
- [ ] Type search query - verify X icon appears to clear
- [ ] Click X - search clears
- [ ] Click "Filters" button - verify Filter icon
- [ ] Verify filter badge appears when filters active
- [ ] Test dropdown selects work
- [ ] Test "Clear All" button

**Expected Result**: All Lucide icons display, search/filter
functionality works

---

### 8. **FreeQuoteButton** (Already Clean - Verify)

**File**: `apps/customer/src/components/quote/FreeQuoteButton.tsx`

**Test Steps**:

- [ ] Find FreeQuoteButton on homepage or other pages
- [ ] Verify 💰 emoji icon displays
- [ ] Test 3 variants (if visible):
  - [ ] Primary button
  - [ ] Secondary button
  - [ ] Floating button
- [ ] Click button - verify navigation to `/quote`
- [ ] Verify hover/active states

**Expected Result**: Button displays with emoji icon, navigation works

---

## 🖥️ Cross-Browser Testing

Test in:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (if on Mac)
- [ ] Edge (latest)

---

## 📱 Responsive Testing

Test at breakpoints:

- [ ] Mobile (375px) - iPhone SE
- [ ] Mobile (414px) - iPhone Pro Max
- [ ] Tablet (768px) - iPad
- [ ] Desktop (1024px) - Small laptop
- [ ] Desktop (1440px) - Standard desktop
- [ ] Large (1920px) - Full HD

**Key Focus**:

- Navbar mobile menu toggle
- Icon sizes scale appropriately
- Footer layout stacks correctly
- Blog components remain readable

---

## 🎨 Visual Parity Checklist

Compare against previous Bootstrap version:

- [ ] Same icon positions
- [ ] Same icon sizes (or better)
- [ ] Same colors (using CSS variables)
- [ ] Same hover effects
- [ ] Same active states
- [ ] Same animations (menu toggle, scroll)
- [ ] No layout shifts
- [ ] No broken images/icons

---

## 🐛 Known Issues to Check

### Potential Issues:

1. **Icon Sizing**: Lucide icons may appear slightly different sizes
   - **Fix**: Adjust `size` prop if needed (already set to 18px
     navbar, 24px footer, etc.)

2. **Icon Colors**: CSS variable inheritance
   - **Fix**: Ensure icons use `className={styles.navIcon}` etc. for
     color

3. **Mobile Menu**: Animation timing
   - **Fix**: CSS transitions should be in `.module.css` files

4. **Hover States**: May need adjustment
   - **Fix**: Check `:hover` styles in CSS Modules

---

## ✅ Acceptance Criteria

All tests pass if:

- ✅ All icons render correctly (no broken icons)
- ✅ Mobile menu toggle works (open/close)
- ✅ All navigation links work
- ✅ Footer icons display and links work
- ✅ Back to top button appears/disappears on scroll
- ✅ Breadcrumbs generate and navigate correctly
- ✅ Blog components display icons properly
- ✅ No console errors in browser
- ✅ Visual appearance matches design (same or better)
- ✅ Responsive behavior intact across all breakpoints

---

## 📊 Performance Verification

After visual testing, verify bundle size reduction:

```bash
# Build production bundle
cd apps/customer
npm run build

# Check bundle size
# Look for "CSS" line in build output
# Expected: ~145-195KB (down from ~530KB)
```

**Expected Bundle Reduction**: 60-70% smaller CSS bundle

---

## 🚀 Testing Commands

```bash
# Start dev server (already running)
cd apps/customer
npm run dev
# Visit: http://localhost:3000

# Run tests
npm test
# Expected: 24/24 pass

# Build check
npm run build
# Expected: Build succeeds, no errors

# Lighthouse audit (optional)
# Open Chrome DevTools > Lighthouse
# Run audit on http://localhost:3000
# Check: Performance, Accessibility, Best Practices
```

---

## 📝 Testing Notes

**Date**: ****\_\_\_\_****  
**Tester**: ****\_\_\_\_****  
**Browser**: ****\_\_\_\_****  
**Screen Size**: ****\_\_\_\_****

**Issues Found**:

1. ***
2. ***
3. ***

**Overall Assessment**: [ ] PASS [ ] FAIL [ ] NEEDS ADJUSTMENT

**Recommendations**:

---

---

---

## 🎯 Next Actions After Visual Testing

### If Tests Pass ✅:

1. Mark this checklist complete
2. Take screenshots for documentation
3. Proceed to migrate remaining 47+ Bootstrap Icon usages (booking
   components)
4. Continue Tailwind v4 consolidation

### If Tests Fail ❌:

1. Document specific issues in "Issues Found" section
2. Fix icon sizing/positioning issues
3. Adjust CSS Module styles if needed
4. Re-test after fixes
5. Commit fixes separately

---

**Status**: ⏳ PENDING MANUAL TESTING  
**Priority**: 🔴 HIGH (Critical functionality verification)  
**Estimated Time**: 15-20 minutes

---

**Generated**: 2025-01-XX  
**Branch**: `nuclear-refactor-clean-architecture`  
**Commit**: `cdcd5f5` (fix: Remove Bootstrap dependencies from CSS
Module components - CRITICAL)
