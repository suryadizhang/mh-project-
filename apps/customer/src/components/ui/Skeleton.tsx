'use client';

/**
 * Skeleton Loading Components
 *
 * A comprehensive set of skeleton components for loading states.
 * Uses Tailwind CSS for styling with pulse animation.
 *
 * @example
 * ```tsx
 * // Basic skeleton
 * <Skeleton className="h-4 w-32" />
 *
 * // Card skeleton
 * <SkeletonCard />
 *
 * // Text block
 * <SkeletonText lines={3} />
 * ```
 */

import React from 'react';

/**
 * Base skeleton element with pulse animation
 */
export function Skeleton({ className = '', ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} {...props} />;
}

/**
 * Skeleton for text content with multiple lines
 */
export function SkeletonText({
  lines = 3,
  className = '',
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4" style={{ width: i === lines - 1 ? '60%' : '100%' }} />
      ))}
    </div>
  );
}

/**
 * Skeleton for a card component
 */
export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      <Skeleton className="mb-4 h-6 w-3/4" />
      <SkeletonText lines={3} />
      <div className="mt-4 flex gap-2">
        <Skeleton className="h-10 w-24 rounded-md" />
        <Skeleton className="h-10 w-24 rounded-md" />
      </div>
    </div>
  );
}

/**
 * Skeleton for image/avatar
 */
export function SkeletonAvatar({
  size = 'md',
  className = '',
}: {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
    xl: 'h-24 w-24',
  };

  return <Skeleton className={`rounded-full ${sizeClasses[size]} ${className}`} />;
}

/**
 * Skeleton for a button
 */
export function SkeletonButton({
  size = 'md',
  className = '',
}: {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'h-8 w-20',
    md: 'h-10 w-28',
    lg: 'h-12 w-36',
  };

  return <Skeleton className={`rounded-md ${sizeClasses[size]} ${className}`} />;
}

/**
 * Skeleton for table rows
 */
export function SkeletonTable({
  rows = 5,
  cols = 4,
  className = '',
}: {
  rows?: number;
  cols?: number;
  className?: string;
}) {
  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex gap-4 border-b border-gray-200 pb-3">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="flex gap-4 border-b border-gray-100 py-3">
          {Array.from({ length: cols }).map((_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton for form inputs
 */
export function SkeletonInput({ className = '' }: { className?: string }) {
  return (
    <div className={className}>
      <Skeleton className="mb-2 h-4 w-24" />
      <Skeleton className="h-10 w-full rounded-md" />
    </div>
  );
}

/**
 * Skeleton for a page header
 */
export function SkeletonPageHeader({ className = '' }: { className?: string }) {
  return (
    <div className={`space-y-4 ${className}`}>
      <Skeleton className="h-10 w-1/3" />
      <Skeleton className="h-5 w-2/3" />
    </div>
  );
}

/**
 * Full page loading skeleton
 */
export function SkeletonPage({ className = '' }: { className?: string }) {
  return (
    <div className={`min-h-screen bg-gray-50 p-8 ${className}`}>
      <div className="mx-auto max-w-7xl">
        <SkeletonPageHeader className="mb-8" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}

/**
 * Booking form skeleton
 */
export function SkeletonBookingForm({ className = '' }: { className?: string }) {
  return (
    <div className={`space-y-6 rounded-xl bg-white p-6 shadow-lg ${className}`}>
      <SkeletonPageHeader />
      <div className="grid gap-4 md:grid-cols-2">
        <SkeletonInput />
        <SkeletonInput />
        <SkeletonInput />
        <SkeletonInput />
      </div>
      <Skeleton className="h-32 w-full rounded-md" />
      <div className="flex justify-end gap-4">
        <SkeletonButton />
        <SkeletonButton size="lg" />
      </div>
    </div>
  );
}

/**
 * Menu item skeleton
 */
export function SkeletonMenuItem({ className = '' }: { className?: string }) {
  return (
    <div className={`flex gap-4 rounded-lg border p-4 ${className}`}>
      <Skeleton className="h-20 w-20 rounded-lg" />
      <div className="flex-1">
        <Skeleton className="mb-2 h-5 w-2/3" />
        <SkeletonText lines={2} />
        <Skeleton className="mt-2 h-6 w-16" />
      </div>
    </div>
  );
}

/**
 * Review card skeleton
 */
export function SkeletonReviewCard({ className = '' }: { className?: string }) {
  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-3 flex items-center gap-3">
        <SkeletonAvatar size="sm" />
        <div className="flex-1">
          <Skeleton className="mb-1 h-4 w-32" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <div className="mb-2 flex gap-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-4 rounded" />
        ))}
      </div>
      <SkeletonText lines={3} />
    </div>
  );
}

export default Skeleton;
