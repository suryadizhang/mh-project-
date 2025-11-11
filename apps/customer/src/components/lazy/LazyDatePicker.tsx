/**
 * Lazy-loaded wrapper for DatePicker component
 * Reduces initial bundle size by ~250KB (react-datepicker + date-fns)
 * Only loaded when user needs to select a date (BookUs page, etc.)
 */

'use client';

import type { ComponentType } from 'react';
import dynamic from 'next/dynamic';

import { DatePickerSkeleton } from '@/components/loading';

// Import the DatePicker props type from react-datepicker
// We'll use a generic props type to avoid importing the full library here
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DatePickerProps = any; // Will be properly typed when the component loads

// Lazy load react-datepicker
// Need to load both the component and its CSS
const DynamicDatePicker = dynamic<DatePickerProps>(
  async () => {
    // Load CSS first (side effect)
    await import('react-datepicker/dist/react-datepicker.css');
    // Then load and return the component
    const DatePicker = await import('react-datepicker');
    return DatePicker.default as ComponentType<DatePickerProps>;
  },
  {
    loading: () => <DatePickerSkeleton />,
    ssr: false, // DatePicker requires browser APIs (date manipulation, calendar)
  }
);

export default function LazyDatePicker(props: DatePickerProps) {
  return <DynamicDatePicker {...props} />;
}
