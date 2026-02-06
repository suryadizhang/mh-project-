'use client';

import { ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { forwardRef } from 'react';

/**
 * CTAButton - Reusable Call-to-Action Button Component
 *
 * Provides consistent, appealing button styling across all pages.
 * Supports primary (filled) and secondary (outline) variants.
 *
 * @example
 * ```tsx
 * <CTAButton href="/book-us/" variant="primary" icon={<Calendar />}>
 *   Book Your Date Now
 * </CTAButton>
 *
 * <CTAButton href="/quote" variant="secondary" icon={<Users />}>
 *   Get Your Quote
 * </CTAButton>
 * ```
 */

export type CTAButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
export type CTAButtonSize = 'sm' | 'md' | 'lg';

interface CTAButtonProps {
  children: React.ReactNode;
  href?: string;
  variant?: CTAButtonVariant;
  size?: CTAButtonSize;
  icon?: React.ReactNode;
  showArrow?: boolean;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  fullWidth?: boolean;
}

const sizeClasses: Record<CTAButtonSize, string> = {
  sm: 'px-4 py-2 text-sm gap-2',
  md: 'px-6 py-3 text-base gap-2.5',
  lg: 'px-8 py-4 text-lg gap-3',
};

const variantClasses: Record<CTAButtonVariant, string> = {
  primary: `
    bg-gradient-to-r from-red-600 to-red-700 text-white
    shadow-lg shadow-red-500/25
    hover:from-red-700 hover:to-red-800 hover:shadow-xl hover:shadow-red-500/30
    active:from-red-800 active:to-red-900
  `,
  secondary: `
    bg-white text-red-600 border-2 border-red-600
    shadow-md
    hover:bg-red-50 hover:border-red-700 hover:shadow-lg
    active:bg-red-100
  `,
  outline: `
    bg-transparent text-white border-2 border-white
    hover:bg-white hover:text-red-600
    active:bg-gray-100
  `,
  ghost: `
    bg-transparent text-red-600
    hover:bg-red-50
    active:bg-red-100
  `,
};

const CTAButton = forwardRef<HTMLButtonElement | HTMLAnchorElement, CTAButtonProps>(
  (
    {
      children,
      href,
      variant = 'primary',
      size = 'md',
      icon,
      showArrow = true,
      className = '',
      onClick,
      disabled = false,
      type = 'button',
      fullWidth = false,
    },
    ref,
  ) => {
    const baseClasses = `
      group relative inline-flex items-center justify-center
      font-bold rounded-xl
      transition-all duration-300 ease-out
      transform hover:scale-[1.02] active:scale-[0.98]
      focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
      ${sizeClasses[size]}
      ${variantClasses[variant]}
      ${fullWidth ? 'w-full' : ''}
      ${className}
    `;

    const content = (
      <>
        {/* Hover overlay for primary variant */}
        {variant === 'primary' && (
          <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-red-700 to-orange-600 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        )}

        {/* Icon */}
        {icon && (
          <span className="relative transition-transform duration-300 group-hover:scale-110">
            {icon}
          </span>
        )}

        {/* Text */}
        <span className="relative">{children}</span>

        {/* Arrow */}
        {showArrow && (
          <ArrowRight className="relative h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
        )}
      </>
    );

    if (href) {
      return (
        <Link
          href={href}
          className={baseClasses}
          onClick={onClick}
          ref={ref as React.Ref<HTMLAnchorElement>}
        >
          {content}
        </Link>
      );
    }

    return (
      <button
        type={type}
        className={baseClasses}
        onClick={onClick}
        disabled={disabled}
        ref={ref as React.Ref<HTMLButtonElement>}
      >
        {content}
      </button>
    );
  },
);

CTAButton.displayName = 'CTAButton';

export default CTAButton;

/**
 * CTAButtonGroup - Wrapper for multiple CTA buttons
 *
 * @example
 * ```tsx
 * <CTAButtonGroup>
 *   <CTAButton href="/book-us/" variant="primary">Book Now</CTAButton>
 *   <CTAButton href="/quote" variant="secondary">Get Quote</CTAButton>
 * </CTAButtonGroup>
 * ```
 */
export function CTAButtonGroup({
  children,
  className = '',
  centered = true,
}: {
  children: React.ReactNode;
  className?: string;
  centered?: boolean;
}) {
  return (
    <div
      className={`flex flex-col gap-4 sm:flex-row ${centered ? 'justify-center' : ''} ${className} `}
    >
      {children}
    </div>
  );
}
