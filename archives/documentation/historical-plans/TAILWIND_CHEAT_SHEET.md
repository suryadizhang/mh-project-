# Tailwind Quick Reference Cheat Sheet

## 🎨 Your Design System in Tailwind

### Colors

```
bg-primary          text-primary          border-primary
bg-secondary        text-secondary        border-secondary
bg-neutral-100      text-neutral-100      border-neutral-100
bg-gray-50          text-gray-500         border-gray-200
bg-success          text-success          border-success
bg-error            text-error            border-error
bg-warning          text-warning          border-warning
```

### Spacing (Padding & Margin)

```
p-1 = 4px    m-1 = 4px     gap-1 = 4px
p-2 = 8px    m-2 = 8px     gap-2 = 8px
p-4 = 16px   m-4 = 16px    gap-4 = 16px
p-6 = 24px   m-6 = 24px    gap-6 = 24px
p-8 = 32px   m-8 = 32px    gap-8 = 32px
p-12 = 48px  m-12 = 48px   gap-12 = 48px
```

### Typography

```
text-xs      font-normal     leading-tight
text-sm      font-medium     leading-normal
text-base    font-semibold   leading-relaxed
text-lg      font-bold
text-xl      font-extrabold
text-2xl
text-3xl
text-4xl
text-5xl
```

### Border Radius

```
rounded-none  rounded-sm  rounded-md  rounded-lg
rounded-xl    rounded-2xl  rounded-full
```

### Shadows

```
shadow-sm   shadow-md   shadow-lg   shadow-xl   shadow-2xl
```

### Z-Index

```
z-[1000]  // dropdown
z-[1020]  // sticky
z-[1030]  // fixed
z-[1040]  // modal-backdrop
z-[1050]  // modal
z-[1060]  // popover
z-[1070]  // tooltip
```

## 🚀 Common Patterns

### Button (Primary)

```tsx
<button className="bg-gradient-to-br from-primary to-primary-dark text-white font-bold px-8 py-4 rounded-lg shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all">
  Click Me
</button>
```

### Button (Outline)

```tsx
<button className="bg-white border-2 border-primary text-primary font-semibold px-6 py-3 rounded-lg hover:bg-primary hover:text-white transition-all">
  Learn More
</button>
```

### Card

```tsx
<div className="bg-white rounded-xl p-8 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all">
  <h3 className="text-xl font-semibold text-primary mb-4">Title</h3>
  <p className="text-gray-700">Content here...</p>
</div>
```

### Input

```tsx
<input className="w-full px-4 py-3 border-2 border-gray-200 rounded-md focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all" />
```

### Navbar Link

```tsx
<Link
  className={cn(
    'px-4 py-2 rounded-md font-medium transition-all',
    'hover:bg-primary/10 hover:text-primary',
    isActive && 'bg-primary text-white'
  )}
>
  Home
</Link>
```

### Container

```tsx
<div className="max-w-7xl mx-auto px-4 lg:px-8">{/* Content */}</div>
```

### Grid Layout

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Items */}
</div>
```

### Flex Layout

```tsx
<div className="flex flex-col md:flex-row items-center justify-between gap-4">
  {/* Items */}
</div>
```

### Gradient Background

```tsx
<div className="bg-gradient-to-br from-primary to-primary-dark">
  {/* Content */}
</div>
```

### Sticky Header

```tsx
<nav className="sticky top-0 z-[1020] bg-white shadow-md">
  {/* Nav content */}
</nav>
```

## 🎯 Responsive Design

### Breakpoints

```
sm:   640px+   (mobile landscape)
md:   768px+   (tablet)
lg:   1024px+  (laptop)
xl:   1280px+  (desktop)
2xl:  1536px+  (large desktop)
```

### Example

```tsx
<div className="
  px-4 md:px-8 lg:px-16
  text-sm md:text-base lg:text-lg
  grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3
">
```

## 🎨 States

### Hover

```tsx
hover: bg - primary;
hover: text - white;
hover: -translate - y - 1;
hover: shadow - lg;
hover: scale - 105;
```

### Focus

```tsx
focus: outline - none;
focus: ring - 2;
focus: ring - primary;
focus: border - primary;
```

### Active

```tsx
active: scale - 95;
active: translate - y - 0;
```

### Disabled

```tsx
disabled: opacity - 60;
disabled: cursor - not - allowed;
disabled: bg - gray - 300;
```

## 🔧 Utilities

### Transitions

```tsx
transition-all duration-300
transition-colors duration-200
transition-transform duration-150
```

### Transforms

```tsx
translate-x-4     -translate-y-2
rotate-45         scale-105
skew-x-12
```

### Opacity

```tsx
opacity-0  opacity-50  opacity-100
bg-black/50  text-white/80  border-gray-200/30
```

### Display

```tsx
hidden  block  inline-block  flex  inline-flex  grid  inline-grid
```

### Position

```tsx
static  fixed  absolute  relative  sticky
```

### Overflow

```tsx
overflow-hidden  overflow-auto  overflow-scroll
truncate  text-ellipsis  whitespace-nowrap
```

## 📝 Quick Tips

1. **Use `cn()` for conditional classes:**

   ```tsx
   className={cn("base-classes", condition && "conditional-classes")}
   ```

2. **Arbitrary values with brackets:**

   ```tsx
   w-[350px]  h-[calc(100vh-80px)]  bg-[#1a2b3c]
   ```

3. **Design system variables:**

   ```tsx
   bg-[var(--color-primary)]  p-[var(--spacing-lg)]
   ```

4. **Group hover states:**

   ```tsx
   <div className="group">
     <span className="group-hover:text-primary">Hover parent</span>
   </div>
   ```

5. **Peer states:**
   ```tsx
   <input className="peer" />
   <label className="peer-focus:text-primary">Label</label>
   ```

## 🚫 Don't Do This

```tsx
// ❌ Don't mix Bootstrap
<div className="container-fluid bg-primary">

// ❌ Don't use inline styles
<div style={{backgroundColor: 'red'}}>

// ❌ Don't create new CSS files
// use Tailwind classes instead

// ✅ Do this
<div className="w-full bg-primary">
```

## 💡 Pro Tips

1. Install Tailwind IntelliSense for VS Code
2. Use `@apply` in CSS only for repeated complex patterns
3. Keep Tailwind classes in logical order: layout → spacing →
   typography → colors → effects
4. Use consistent breakpoints across the app
5. Refer to TAILWIND_MIGRATION_GUIDE.md for full examples

---

**Quick Links:**

- [Tailwind Docs](https://tailwindcss.com/docs)
- [Full Migration Guide](./TAILWIND_MIGRATION_GUIDE.md)
- [Design System Variables](./apps/customer/src/styles/variables.css)
