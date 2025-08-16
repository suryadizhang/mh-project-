# Performance Optimization Notes

## Files Split and Modules Created

### Components Split from `src/app/menu/page.tsx`:
- **MenuHero.tsx** - Hero section with floating icons and value proposition
- **PricingSection.tsx** - Pricing tiers with features and CTAs
- **ProteinsSection.tsx** - Protein categories and descriptions
- **AdditionalSection.tsx** - Optional add-on services
- **ServiceAreas.tsx** - Service area coverage with CTA buttons
- **CTASection.tsx** - Final call-to-action with trust signals

### CSS Modules Created in `src/styles/menu/`:
- **base.css** - CSS variables and global menu tokens
- **hero.module.css** - Hero section styles with animations
- **pricing.module.css** - Pricing card layouts and responsive design
- **proteins.module.css** - Protein category grid and item styles
- **additional.module.css** - Additional services styling
- **service-areas.module.css** - Service areas grid and responsive layout
- **cta.module.css** - Call-to-action section with gradients

### Static Data Extraction:
- **src/data/menu.ts** - All menu data extracted to TypeScript object
  - Hero content (title, subtitle, features, value proposition)
  - Pricing tiers with features and pricing
  - Protein categories with descriptions
  - Service areas (primary and extended)
  - Additional services with pricing

## Performance Improvements Implemented

### Code Splitting:
- **Dynamic imports** for below-the-fold content (Proteins, Additional, ServiceAreas, CTA)
- **SSR disabled** for dynamically loaded sections to reduce initial bundle
- **Loading states** added for better UX during chunk loading

### CSS Optimization:
- **CSS Variables** centralized in base.css for consistency
- **Modular CSS** reduces style conflicts and improves tree-shaking
- **Consolidated media queries** within each module
- **Removed duplicate styles** and consolidated common patterns

### Server-Side Optimization:
- **Static generation** enabled with `export const dynamic = 'force-static'`
- **Revalidation** set to 1 hour for data freshness
- **Server components** by default (MenuHero, PricingSection render server-side)

### Bundle Size Reduction:
- **Lucide React icons** imported individually instead of full library
- **Dynamic loading** reduces initial JavaScript bundle
- **CSS modules** enable better CSS tree-shaking

## ClassName Mappings Changed

### Global to Module CSS:
- `.hero-section` → `styles.heroSection`
- `.pricing-section` → `styles.pricingSection`
- `.section-title` → `styles.sectionTitle`
- `.feature-badge` → `styles.featureBadge`
- `.service-area-card` → `styles.serviceAreaCard`
- `.protein-category` → `styles.proteinCategory`

### CSS Variables Added:
- `--menu-primary: #dc3545`
- `--menu-spacing-*: (xs, sm, md, lg, xl, xxl)`
- `--menu-border-radius-*: (sm, md, lg, xl)`
- `--menu-shadow-*: (sm, md, lg, xl)`
- `--menu-transition-*: (fast, normal, slow)`

## Expected Performance Gains

### Development:
- **Faster compilation** due to smaller individual files
- **Better HMR** as changes only affect specific modules
- **Reduced full page reloads** during development

### Production:
- **Smaller initial bundle** with code splitting
- **Better caching** with modular CSS
- **Faster page loads** with static generation
- **Progressive loading** of below-the-fold content

### Maintenance:
- **Better code organization** with single-responsibility components
- **Easier debugging** with isolated modules
- **Improved developer experience** with TypeScript data types

## Migration Status

- ✅ Data extraction to `menu.ts`
- ✅ Component splitting (6 components created)
- ✅ CSS modularization (7 CSS modules)
- ✅ Dynamic imports implemented
- ✅ Static generation configured
- ⏳ Original page replacement (pending)
- ⏳ Production bundle size verification (pending)

## Next Steps

1. Replace original `page.tsx` with optimized version
2. Verify all functionality works correctly
3. Test responsive design across breakpoints
4. Measure bundle size improvements
5. Apply same pattern to other large pages (home, faqs, blog)
