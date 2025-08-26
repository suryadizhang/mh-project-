# My Hibachi CSS Architecture Guide

## Overview

This document outlines the CSS architecture implemented to eliminate style conflicts while preserving the existing visual design pixel-for-pixel. The methodology provides long-term stability, componentized styling, and no visible design drift.

## Design Principles

### 1. Zero Visual Regression Policy
- No spacing, size, color, or typography changes
- No global selector behavior changes
- No breaking changes to page markup
- Hardcoded fallbacks for critical values

### 2. Scoped Architecture
- Page-scoped styles using `data-page` attributes
- Component-scoped styles using CSS Modules
- Utility classes for common patterns
- Legacy compatibility layer during migration

## File Structure

```
src/
├── app/
│   ├── globals.css           # Design tokens + base styles
│   └── (routes)/
│       ├── menu/layout.tsx   # data-page="menu"
│       ├── contact/layout.tsx # data-page="contact"
│       └── quote/layout.tsx   # data-page="quote"
├── components/
│   └── ui/
│       ├── Button.tsx        # Centralized button component
│       └── Button.module.css # Scoped button styles
└── styles/
    ├── utilities.css         # Defensive utility classes
    ├── legacy.css           # Legacy styles (temp)
    └── pages/
        ├── menu.page.css    # [data-page="menu"] scoped
        ├── contact.page.css # [data-page="contact"] scoped
        └── quote.page.css   # [data-page="quote"] scoped
```

## CSS Layer Architecture

### Layer 1: Design Tokens (globals.css)
```css
:root {
  --color-primary: #DB2B28;
  --color-primary-contrast: #ffffff;
  --text-strong: #111111;
  --text-default: #222222;
  --text-on-dark: #ffffff;
  /* ... additional tokens */
}
```

### Layer 2: Normalize & Base (globals.css)
```css
*, *::before, *::after { 
  box-sizing: border-box; 
}

html { 
  -webkit-font-smoothing: antialiased; 
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.5;
}
```

### Layer 3: Utilities (utilities.css)
```css
.u-text-on-dark {
  color: var(--text-on-dark);
  text-shadow: 0 1px 2px rgb(0 0 0 / 0.25);
}
```

### Layer 4: Components (Button.module.css)
```css
.button {
  /* Scoped component styles */
}
```

### Layer 5: Page Scopes (pages/*.page.css)
```css
[data-page="menu"] .pricing-card {
  /* Page-specific styles */
}
```

### Layer 6: Legacy Overrides (legacy.css)
```css
/* Temporary compatibility layer */
.btn-primary {
  /* Legacy global styles */
}
```

## Page Scoping Implementation

### Layout Components
Each critical page has a layout wrapper:

```tsx
// app/menu/layout.tsx
export default function MenuLayout({ children }: { children: React.ReactNode }) {
  return <div data-page="menu">{children}</div>
}
```

### Page-Specific Styles
Styles are scoped to prevent conflicts:

```css
/* menu.page.css */
[data-page="menu"] .pricing-card {
  background: var(--color-background);
  /* ... styles only apply to menu page */
}
```

## Button Centralization

### Component Usage
Replace legacy `.btn-primary` with centralized component:

```tsx
// Before (legacy)
<button className="btn-primary">Get Quote</button>

// After (scoped)
import { HibachiButton } from '@/components/ui/button'
<HibachiButton variant="primary">Get Quote</HibachiButton>
```

### Visual Compatibility
The `HibachiButton` component matches legacy `.btn-primary` exactly:

```css
.primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  color: var(--color-primary-contrast);
  min-width: 280px; /* Preserved from legacy */
  /* ... exact visual match */
}
```

## White Text Visibility

### Defensive Utility Class
```css
.u-text-on-dark {
  color: var(--text-on-dark);
  text-shadow: 0 1px 2px rgb(0 0 0 / 0.25);
}
```

### Usage
Apply to white text over videos/gradients:
```html
<h1 class="u-text-on-dark">Hibachi Catering</h1>
```

## Migration Strategy

### Phase 1: Foundation ✅
- [x] Design tokens in globals.css
- [x] Page hooks with data-page attributes
- [x] Utility classes for defensive CSS
- [x] Legacy compatibility layer

### Phase 2: Component Migration (In Progress)
- [x] Button component centralization
- [ ] Replace .btn-primary in critical areas
- [ ] Form component creation
- [ ] Hero component creation

### Phase 3: Cleanup (Future)
- [ ] Remove legacy CSS dependencies
- [ ] Delete unused global styles
- [ ] Enforce component-only architecture

## Development Guidelines

### Adding New Styles

#### ✅ DO
```css
/* Page-scoped */
[data-page="menu"] .new-feature { }

/* Component-scoped */
.feature { } /* in Component.module.css */

/* Utility class */
.u-new-utility { }
```

#### ❌ DON'T
```css
/* Global styles (causes conflicts) */
.btn-primary { }
.hero-section { }
.new-feature { }
```

### Specificity Rules
- Prefer component classes over descendant chains
- Use `:where()` for low-specificity grouping
- Avoid `!important` except in escape-hatch.css
- Maximum specificity: `0,3,0` (enforced by Stylelint)

### Naming Conventions
- **Components**: PascalCase files, camelCase classes
- **Utilities**: `u-` prefix (e.g., `u-text-center`)
- **Page scopes**: `[data-page="name"] .class`
- **Legacy**: Keep existing names during migration

## Quality Assurance

### Automated Checks
```bash
# Lint CSS for conflicts
npm run lint:css

# Check for style problems
npm run check:styles

# Build verification
npm run build
```

### Stylelint Configuration
```json
{
  "extends": ["stylelint-config-standard"],
  "rules": {
    "declaration-block-no-duplicate-properties": true,
    "selector-max-specificity": "0,3,0",
    "no-descending-specificity": null
  }
}
```

### Manual Testing Checklist
- [ ] `/menu` page visual comparison
- [ ] `/contact` page visual comparison  
- [ ] `/quote` page visual comparison
- [ ] Button hover states match exactly
- [ ] No console CSS warnings
- [ ] Mobile responsiveness preserved

## Performance Considerations

### CSS Loading Order
1. Tailwind base styles
2. Design tokens & normalize
3. Utility classes
4. Component styles (CSS Modules)
5. Page-specific styles
6. Legacy overrides (last)

### Bundle Size Impact
- **Design tokens**: +2KB (shared across pages)
- **Utilities**: +5KB (cached utility classes)
- **Page styles**: +3KB per page (only loaded when needed)
- **Component styles**: +1KB per component (tree-shaken)

### Caching Strategy
- CSS Modules automatically generate unique class names
- Page-specific CSS loaded only when route accessed
- Utility classes shared across all pages

## Browser Support

### Target Browsers
```json
"browserslist": [
  ">=0.5%",
  "last 2 versions", 
  "not dead"
]
```

### CSS Features Used
- CSS Custom Properties (CSS Variables)
- CSS Grid & Flexbox
- CSS Modules
- Modern selectors (`:where()`, `:is()`)

## Troubleshooting

### Common Issues

#### Duplicate .btn-primary Declarations
**Problem**: Multiple CSS files defining `.btn-primary`
**Solution**: Replace with `<HibachiButton>` component

#### Specificity Conflicts
**Problem**: Styles not applying due to specificity
**Solution**: Use data-page scoping or CSS Modules

#### Visual Regression
**Problem**: Buttons/elements look different after migration
**Solution**: Copy computed styles from DOM before migration

### Debug Commands
```bash
# Find conflicting selectors
npm run lint:css

# Check for duplicates
grep -r "\.btn-primary" src/styles/

# Verify page scoping
grep -r "data-page" src/
```

## Future Roadmap

### Q1 2025: Component System
- [ ] Form component library
- [ ] Hero component variants
- [ ] Card component system
- [ ] Navigation components

### Q2 2025: Design System
- [ ] Comprehensive design tokens
- [ ] Component documentation (Storybook)
- [ ] Design system guidelines
- [ ] Automated visual regression testing

### Q3 2025: Performance Optimization
- [ ] Critical CSS inlining
- [ ] Unused CSS elimination
- [ ] CSS-in-JS evaluation
- [ ] Bundle size optimization

---

## Support

For questions about this CSS architecture:
1. Review this documentation
2. Check existing component patterns
3. Follow the migration guidelines
4. Test thoroughly for visual regressions

**Remember**: Preservation of existing visual design is the top priority during migration.
