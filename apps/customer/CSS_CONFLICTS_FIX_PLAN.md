# CSS Conflicts Resolution Plan

## Problem Analysis

- **100+ instances** of `color: white` declarations across CSS files
- **Multiple conflicting definitions** for the same CSS classes across different pages
- **CSS cascade conflicts** during navigation causing different displays in VS Code vs Chrome
- **Hydration timing issues** where styles load in different orders

## Root Causes Identified

1. **Global CSS imports** in layout.tsx conflict with page-specific CSS
2. **Common class names** (`.card-title`, `.btn-primary`, `.radius-card`) used across multiple pages
3. **White text** appears before dark backgrounds load during CSS hydration
4. **Specificity wars** between different CSS files

## Comprehensive Solution Strategy

### Phase 1: CSS Scoping & Defensive Programming (CURRENT)

- ✅ Scope `.radius-card` to specific containers
- ✅ Add fallback colors for white text
- 🔄 Apply same pattern to ALL problematic classes

### Phase 2: Page-Specific CSS Namespacing (NEXT)

- Add unique page classes to each page component
- Scope all CSS rules to their specific page namespaces
- Remove global conflicting styles

### Phase 3: Color Safety Audit (CRITICAL)

- Review all 100+ white color declarations
- Add dark fallbacks for every white text element
- Ensure proper contrast ratios during hydration

### Phase 4: Testing & Validation

- Test navigation between all major pages
- Verify VS Code browser matches Chrome display
- Validate CSS loading order consistency

## Priority Classes for Immediate Fix

1. `.card-title` - conflicts across menu, contact, and global
2. `.btn-primary` - conflicts across home, quote, contact
3. `.included-item` - conflicts across quote and menu
4. All white text elements without safe fallbacks

## Implementation Notes

- Use defensive CSS: dark text as default, white only with confirmed dark backgrounds
- Add page-specific class wrappers to prevent cross-page conflicts
- Comment out deprecated global CSS rules
- Test each fix in both browsers before moving to next
