'use client';

/**
 * Lazy-loaded DatePicker Component
 *
 * Wraps react-datepicker with React.lazy() and Suspense for better
 * initial page load performance. The calendar library (~50KB gzipped)
 * is only loaded when the user interacts with the date field.
 */

import dynamic from 'next/dynamic';
import React, { Suspense } from 'react';
import type ReactDatePicker from 'react-datepicker';

// Import CSS for styling
import 'react-datepicker/dist/react-datepicker.css';

/**
 * Skeleton loader shown while DatePicker is loading
 */
function DatePickerSkeleton() {
  return (
    <div
      className="date-picker-skeleton"
      style={{
        width: '100%',
        height: '42px',
        backgroundColor: '#f3f4f6',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }}
    >
      <style jsx>{`
        @keyframes pulse {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}

// Dynamic import with no SSR - datepicker doesn't work server-side
// Type assertion needed due to react-datepicker's complex defaultProps types
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DatePickerComponent = dynamic<any>(() => import('react-datepicker'), {
  ssr: false,
  loading: () => <DatePickerSkeleton />,
});

/**
 * Props for LazyDatePicker - matches react-datepicker props
 */
export type LazyDatePickerProps = React.ComponentProps<typeof ReactDatePicker> & {
  /** Show skeleton while loading */
  showSkeleton?: boolean;
};

/**
 * Lazy-loaded DatePicker with Suspense boundary
 *
 * @example
 * ```tsx
 * <LazyDatePicker
 *   selected={date}
 *   onChange={(date) => setDate(date)}
 *   minDate={new Date()}
 *   dateFormat="MMMM d, yyyy"
 * />
 * ```
 */
export function LazyDatePicker({ showSkeleton = true, ...props }: LazyDatePickerProps) {
  return (
    <Suspense fallback={showSkeleton ? <DatePickerSkeleton /> : null}>
      <DatePickerComponent
        portalId="datepicker-portal"
        popperClassName="datepicker-popper-portal"
        {...props}
      />
    </Suspense>
  );
}

export default LazyDatePicker;
