import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import styles from './Button.module.css'

// Preserve existing Radix/CVA pattern for compatibility
const buttonVariants = cva(
  "inline-flex items-center justify-content gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow-xs hover:bg-primary/90',
        destructive:
          'bg-destructive text-white shadow-xs hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60',
        outline:
          'border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50',
        secondary: 'bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50',
        link: 'text-primary underline-offset-4 hover:underline'
      },
      size: {
        default: 'h-9 px-4 py-2 has-[>svg]:px-3',
        sm: 'h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5',
        lg: 'h-10 rounded-md px-6 has-[>svg]:px-4',
        icon: 'size-9'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
)

// Standard Tailwind/Radix Button (existing)
function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : 'button'

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

// My Hibachi Button Component - Pixel-Perfect Legacy Match
export interface HibachiButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button visual variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  /** Button size */
  size?: 'sm' | 'md' | 'lg'
  /** Loading state */
  loading?: boolean
  /** Render as child component (for links, etc.) */
  asChild?: boolean
  children: React.ReactNode
}

/**
 * My Hibachi Button Component
 *
 * Centralized button styling that eliminates .btn-primary conflicts.
 * Designed to match existing visual design pixel-for-pixel while
 * providing a scalable component architecture.
 */
function HibachiButton({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  disabled,
  asChild = false,
  ...props
}: HibachiButtonProps) {
  const classes = cn(
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    className
  )

  if (asChild) {
    return React.cloneElement(React.Children.only(children) as React.ReactElement, {
      className: classes,
      ...props
    })
  }

  return (
    <button className={classes} disabled={disabled || loading} {...props}>
      {loading && <span className={styles.spinner} />}
      {children}
    </button>
  )
}

export { Button, buttonVariants, HibachiButton }
