# Tailwind v4 + CSS Variables Migration Guide

## 🎯 Strategy Overview

**Goal**: Consolidate from 6 styling technologies to 1 unified
approach

- ✅ **Keep**: Tailwind v4 + CSS Variables (217 design tokens)
- ❌ **Remove**: Bootstrap 5.3, CSS Modules (except 10 already done),
  Mixed global CSS
- 📈 **Result**: Faster development, smaller bundles, easier
  maintenance

---

## 🚀 Quick Start

### Using Your Design System in Tailwind

All 217 CSS variables are now available as Tailwind classes:

```tsx
// ❌ OLD: CSS Modules
<div className={styles.navbar}>

// ❌ OLD: Bootstrap
<div className="navbar navbar-expand-lg bg-light">

// ✅ NEW: Tailwind + Design Tokens
<div className="sticky top-0 z-[1020] bg-neutral-100 shadow-md">
```

---

## 📋 Available Design Tokens

### Colors

```tsx
// Brand Colors
bg-primary          // #dc2626 (red-600)
bg-primary-hover    // #b91c1c (red-700)
bg-primary-dark     // #991b1b (red-800)
bg-primary-light    // #fef2f2 (red-50)

bg-secondary        // #f97316 (orange-500)
bg-secondary-hover  // #ea580c (orange-600)
bg-secondary-dark   // #c2410c (orange-700)

// Neutral & Grays
bg-neutral-100      // #f9e8d0 (light tan - navbar)
bg-gray-50 through bg-gray-900

// Semantic
bg-success          // #10b981 (green-500)
bg-error            // #ef4444 (red-500)
bg-warning          // #f59e0b (amber-500)
bg-info             // #3b82f6 (blue-500)

// Text colors: text-primary, text-secondary, etc.
// Border colors: border-primary, border-gray-200, etc.
```

### Spacing

```tsx
// Using design system spacing
p-[var(--spacing-xs)]   // 4px
p-[var(--spacing-sm)]   // 8px
p-[var(--spacing-md)]   // 16px
p-[var(--spacing-lg)]   // 24px
p-[var(--spacing-xl)]   // 32px
p-[var(--spacing-2xl)]  // 48px
p-[var(--spacing-3xl)]  // 64px
p-[var(--spacing-4xl)]  // 96px

// Or use Tailwind's built-in scale (recommended for consistency)
p-1  // 4px
p-2  // 8px
p-4  // 16px
p-6  // 24px
p-8  // 32px
p-12 // 48px
p-16 // 64px
p-24 // 96px
```

### Border Radius

```tsx
rounded-none     // 0
rounded-sm       // 0.25rem (4px)
rounded-md       // 0.5rem (8px)
rounded-lg       // 0.75rem (12px)
rounded-xl       // 1rem (16px)
rounded-2xl      // 1.5rem (24px)
rounded-full     // 9999px
```

### Z-Index

```tsx
z - [1000]; // dropdown (--z-dropdown)
z - [1020]; // sticky (--z-sticky)
z - [1030]; // fixed (--z-fixed)
z - [1040]; // modal-backdrop (--z-modal-backdrop)
z - [1050]; // modal (--z-modal)
z - [1060]; // popover (--z-popover)
z - [1070]; // tooltip (--z-tooltip)
```

### Typography

```tsx
// Font Sizes
text-xs    // 0.75rem (12px)
text-sm    // 0.875rem (14px)
text-base  // 1rem (16px)
text-lg    // 1.125rem (18px)
text-xl    // 1.25rem (20px)
text-2xl   // 1.5rem (24px)
text-3xl   // 1.875rem (30px)
text-4xl   // 2.25rem (36px)
text-5xl   // 3rem (48px)

// Font Weights
font-normal    // 400
font-medium    // 500
font-semibold  // 600
font-bold      // 700
font-extrabold // 800

// Font Families
font-sans      // Inter, system-ui
font-primary   // Same as sans
font-secondary // Poppins, Inter
font-heading   // Poppins, Inter
```

---

## 🔄 Migration Patterns

### Pattern 1: Navigation Component

```tsx
// ❌ BEFORE: CSS Modules + Bootstrap
<nav className={cn("navbar navbar-expand-lg", styles.navbar)}>
  <Link className={cn("nav-link", styles.navLink, isActive && styles.active)}>
    Home
  </Link>
</nav>

// ✅ AFTER: Tailwind only
<nav className="sticky top-0 z-[1020] bg-neutral-100 shadow-md px-6 py-4 transition-all duration-300">
  <Link className={cn(
    "px-4 py-2 rounded-md text-gray-700 font-medium transition-all",
    "hover:bg-primary/10 hover:text-primary hover:-translate-y-0.5",
    isActive && "bg-primary text-white shadow-md"
  )}>
    Home
  </Link>
</nav>
```

### Pattern 2: Button Component

```tsx
// ❌ BEFORE: CSS Modules
<button className={styles.calculateBtn}>
  Calculate Quote
</button>

// ✅ AFTER: Tailwind
<button className={cn(
  "bg-gradient-to-br from-primary to-primary-dark",
  "text-white font-bold text-lg",
  "px-12 py-4 rounded-lg",
  "shadow-[0_4px_15px_rgba(220,38,38,0.2)]",
  "transition-all duration-300",
  "hover:shadow-[0_8px_25px_rgba(220,38,38,0.3)]",
  "hover:-translate-y-1",
  "active:translate-y-0",
  "disabled:opacity-60 disabled:cursor-not-allowed",
  isCalculating && "bg-gradient-to-br from-gray-500 to-gray-700 cursor-wait"
)}>
  {isCalculating ? 'Calculating...' : 'Calculate Quote'}
</button>
```

### Pattern 3: Card Component

```tsx
// ❌ BEFORE: CSS Modules
<div className={styles.card}>
  <h3 className={styles.cardTitle}>Title</h3>
  <p className={styles.cardContent}>Content</p>
</div>

// ✅ AFTER: Tailwind
<div className={cn(
  "bg-white rounded-xl p-8",
  "shadow-md border border-gray-200",
  "transition-all duration-300",
  "hover:shadow-lg hover:-translate-y-1 hover:border-primary"
)}>
  <h3 className="text-xl font-semibold text-primary mb-4">
    Title
  </h3>
  <p className="text-gray-700 leading-relaxed">
    Content
  </p>
</div>
```

### Pattern 4: Form Input

```tsx
// ❌ BEFORE: CSS Modules
<input className={styles.formInput} />

// ✅ AFTER: Tailwind
<input className={cn(
  "w-full px-4 py-3",
  "border-2 border-gray-200 rounded-md",
  "text-base transition-all",
  "focus:outline-none focus:border-primary",
  "focus:shadow-[0_0_0_3px_rgba(220,38,38,0.1)]",
  "disabled:bg-gray-100 disabled:cursor-not-allowed"
)} />
```

### Pattern 5: Gradient Backgrounds

```tsx
// ❌ BEFORE: CSS
background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);

// ✅ AFTER: Tailwind
className="bg-gradient-to-br from-primary to-primary-dark"

// Other gradient directions:
bg-gradient-to-r   // left to right
bg-gradient-to-l   // right to left
bg-gradient-to-t   // bottom to top
bg-gradient-to-b   // top to bottom
bg-gradient-to-tr  // bottom-left to top-right
bg-gradient-to-tl  // bottom-right to top-left
bg-gradient-to-br  // top-left to bottom-right
bg-gradient-to-bl  // top-right to bottom-left
```

### Pattern 6: Responsive Design

```tsx
// ❌ BEFORE: CSS @media queries
@media (width <= 768px) {
  .navbar { padding: 1rem; }
}

// ✅ AFTER: Tailwind responsive utilities
className="px-6 md:px-12 lg:px-16"

// Breakpoints:
sm:  // 640px
md:  // 768px
lg:  // 1024px
xl:  // 1280px
2xl: // 1536px
```

### Pattern 7: Hover & Focus States

```tsx
// ❌ BEFORE: CSS
.button:hover { transform: translateY(-2px); }
.button:focus { outline: 2px solid var(--color-primary); }

// ✅ AFTER: Tailwind
className={cn(
  "transition-transform",
  "hover:-translate-y-0.5 hover:shadow-lg",
  "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
)}
```

### Pattern 8: Animations

```tsx
// ❌ BEFORE: CSS
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.element { animation: fadeInUp 0.3s ease-out; }

// ✅ AFTER: Tailwind (with tw-animate-css plugin)
className="animate-fadeInUp"

// Or custom animation
className="animate-[fadeInUp_0.3s_ease-out]"
```

---

## 🛠️ Helper Utilities

### The `cn()` Helper

Keep using the `cn()` utility for conditional classes:

```tsx
import { cn } from '@/lib/utils';

<div
  className={cn(
    'base classes',
    condition && 'conditional classes',
    anotherCondition ? 'true classes' : 'false classes'
  )}
/>;
```

### Common Utility Patterns

```tsx
// Centering
<div className="flex items-center justify-center">

// Spacing children
<div className="space-y-4">  // vertical spacing
<div className="space-x-4">  // horizontal spacing

// Grid layouts
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

// Flexbox
<div className="flex flex-col md:flex-row items-start md:items-center gap-4">

// Truncate text
<p className="truncate">Long text...</p>
<p className="line-clamp-3">Multi-line text...</p>

// Aspect ratios
<div className="aspect-square">   // 1:1
<div className="aspect-video">    // 16:9
<div className="aspect-[4/3]">    // custom

// Backdrop blur
<div className="backdrop-blur-sm bg-white/80">
```

---

## 📦 Bootstrap Removal Checklist

### Components to Replace:

1. **Navbar** → Tailwind flex/grid layout
2. **Container** → `max-w-7xl mx-auto px-4`
3. **Row/Col** → Tailwind grid system
4. **Button** → Custom Tailwind classes
5. **Card** → Custom Tailwind classes
6. **Form controls** → Custom Tailwind classes
7. **Modal** → Headless UI + Tailwind
8. **Dropdown** → Headless UI + Tailwind

### Bootstrap Grid → Tailwind Grid

```tsx
// ❌ BEFORE: Bootstrap
<div className="container">
  <div className="row">
    <div className="col-md-6 col-lg-4">Content</div>
    <div className="col-md-6 col-lg-8">Content</div>
  </div>
</div>

// ✅ AFTER: Tailwind
<div className="max-w-7xl mx-auto px-4">
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6">
    <div className="md:col-span-1 lg:col-span-4">Content</div>
    <div className="md:col-span-1 lg:col-span-8">Content</div>
  </div>
</div>
```

---

## 🎨 Component Examples

### Complete Navbar Example

```tsx
export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="sticky top-0 z-[1020] bg-neutral-100 shadow-md transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/logo.png"
              alt="Logo"
              width={40}
              height={40}
            />
            <span className="text-xl font-bold text-primary">
              My Hibachi
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center gap-2">
            {navLinks.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'px-4 py-2 rounded-md text-sm font-medium transition-all',
                  'hover:bg-primary/10 hover:text-primary hover:-translate-y-0.5',
                  isActive(link.href)
                    ? 'bg-primary text-white shadow-md'
                    : 'text-gray-700'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Nav */}
        {isOpen && (
          <div className="lg:hidden py-4 space-y-2">
            {navLinks.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'block px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive(link.href)
                    ? 'bg-primary text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
                onClick={() => setIsOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
```

### Complete Button Component

```tsx
import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-2',
          'font-semibold rounded-lg transition-all duration-300',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-60 disabled:cursor-not-allowed',

          // Variants
          variant === 'primary' && [
            'bg-gradient-to-br from-primary to-primary-dark',
            'text-white shadow-[0_4px_15px_rgba(220,38,38,0.2)]',
            'hover:shadow-[0_6px_20px_rgba(220,38,38,0.3)] hover:-translate-y-0.5',
            'focus:ring-primary',
          ],
          variant === 'secondary' && [
            'bg-gradient-to-br from-secondary to-secondary-dark',
            'text-white shadow-[0_4px_15px_rgba(249,115,22,0.2)]',
            'hover:shadow-[0_6px_20px_rgba(249,115,22,0.3)] hover:-translate-y-0.5',
            'focus:ring-secondary',
          ],
          variant === 'outline' && [
            'bg-white border-2 border-primary text-primary',
            'hover:bg-primary hover:text-white',
            'focus:ring-primary',
          ],
          variant === 'ghost' && [
            'text-primary hover:bg-primary/10',
            'focus:ring-primary',
          ],

          // Sizes
          size === 'sm' && 'px-4 py-2 text-sm',
          size === 'md' && 'px-6 py-3 text-base',
          size === 'lg' && 'px-8 py-4 text-lg',

          // Loading state
          isLoading && 'cursor-wait',

          className
        )}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

---

## 🚀 Migration Steps

### Phase 1: Setup (DONE ✅)

- [x] Update globals.css with Tailwind @theme configuration
- [x] Map all 217 CSS variables to Tailwind theme
- [x] Test Tailwind classes are working

### Phase 2: Remove Bootstrap

- [ ] Remove Bootstrap CDN from `layout.tsx`
- [ ] Search for `className=".*btn.*"` and replace with Tailwind
- [ ] Search for `className=".*container.*"` and replace
- [ ] Search for `className=".*row.*"` and replace
- [ ] Search for `className=".*col-.*"` and replace

### Phase 3: Component Migration

- [ ] Update Navbar component
- [ ] Update Footer component
- [ ] Update Button components
- [ ] Update Form components
- [ ] Update Card components
- [ ] Update Modal components

### Phase 4: CSS Modules Cleanup

- [ ] Keep the 10 CSS Module files we already created (they work fine)
- [ ] Don't migrate more components to CSS Modules
- [ ] Use Tailwind for all NEW components
- [ ] Document which components use CSS Modules vs Tailwind

### Phase 5: Testing

- [ ] Visual regression testing
- [ ] Lighthouse performance audit
- [ ] Bundle size comparison
- [ ] Cross-browser testing

---

## 📊 Benefits

### Before (6 Technologies)

```
Tailwind v4: 100% imported
Bootstrap 5.3: ~200KB (CDN)
CSS Modules: ~50KB compiled
Global CSS: ~150KB
Lucide Icons: ~30KB
CSS Variables: 217 tokens

Total: ~530KB+ CSS
```

### After (1 Technology)

```
Tailwind v4 with design tokens: ~100-150KB (tree-shaken)
Lucide Icons: ~30KB
CSS Modules (10 files): ~15KB (kept as-is)

Total: ~145-195KB CSS (60-70% reduction!)
```

### Developer Experience

**Before:**

- "Should I use Tailwind or CSS Modules?"
- "Is this a Bootstrap class or custom CSS?"
- "Where is this style defined?"
- CSS conflicts between Bootstrap and Tailwind

**After:**

- One way to style: Tailwind classes
- All styles in JSX (co-located)
- Autocomplete in VS Code
- No context switching

---

## 🎓 Learning Resources

### Official Docs

- [Tailwind v4 Documentation](https://tailwindcss.com/docs)
- [Tailwind v4 Theme Configuration](https://tailwindcss.com/docs/theme)

### Video Tutorials

- Tailwind Labs YouTube channel
- "Tailwind CSS Tutorial" by Traversy Media

### Tools

- [Tailwind IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss) -
  VS Code extension
- [Tailwind CSS Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet)
- [Headless UI](https://headlessui.com/) - Unstyled accessible
  components

---

## ❓ FAQ

### Q: What about the 10 CSS Modules we already created?

**A:** Keep them! They work great. Don't migrate them to Tailwind. Use
Tailwind for all NEW work.

### Q: Can I still use CSS variables?

**A:** Yes! All 217 variables are still available. Use them via
Tailwind: `bg-[var(--color-primary)]` or the mapped classes like
`bg-primary`.

### Q: What about animations?

**A:** Use Tailwind's built-in animations or the `tw-animate-css`
plugin we have installed for complex animations.

### Q: How do I handle complex responsive designs?

**A:** Tailwind's responsive utilities are very powerful. See "Pattern
6" above for examples.

### Q: What about the admin app?

**A:** Apply the exact same approach - update
`apps/admin/src/app/globals.css` with the same @theme configuration.

---

## 📝 Next Steps

1. **Review this guide** with the team
2. **Test the Tailwind configuration** - verify classes work
3. **Start with one component** - pick something simple like a button
4. **Create a pull request** for team review
5. **Iterate and improve** based on feedback

---

## 🎉 Success Metrics

Track these metrics before/after migration:

- [ ] Bundle size reduced by 60%+
- [ ] Build time improved
- [ ] Development velocity increased
- [ ] CSS conflicts eliminated
- [ ] Team satisfaction improved
- [ ] Onboarding time for new developers reduced

---

**Questions? Issues? Improvements?** Update this guide as we learn and
improve the migration process!
