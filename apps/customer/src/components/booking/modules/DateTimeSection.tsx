'use client';

import { AlertCircle, Calendar, Clock, Loader2 } from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';
import { Control, Controller, FieldErrors, UseFormWatch } from 'react-hook-form';

import { apiFetch } from '@/lib/api-client';
import { VenueCoordinates } from './VenueAddressSection';

/**
 * Time slot configuration
 */
export type TimeSlotValue = '12PM' | '3PM' | '6PM' | '9PM';

export interface TimeSlot {
  time: TimeSlotValue;
  label: string;
  available: boolean;
  availableChefs?: number;
  reason?: string;
}

/**
 * Date/Time form data structure
 */
export interface DateTimeFormData {
  eventDate: Date | null;
  eventTime: TimeSlotValue | '';
}

export interface DateTimeSectionProps {
  // Use 'any' to allow parent forms with additional fields
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  control: Control<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  errors: FieldErrors<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  watch: UseFormWatch<any>;
  className?: string;
  showCompletionBadge?: boolean;
  /** Venue coordinates for smart scheduling (travel-aware availability) */
  venueCoordinates?: VenueCoordinates | null;
  /** Minimum days in advance for booking (default 2) */
  minDaysAdvance?: number;
  /** Maximum days in advance for booking (default 365 = 1 year) */
  maxDaysAdvance?: number;
  /** Callback when availability is fetched */
  onAvailabilityFetched?: (slots: TimeSlot[]) => void;
  /** Callback when date/time selection changes */
  onSelectionChange?: (date: Date | null, time: TimeSlotValue | '') => void;
}

/**
 * Default time slots
 */
const DEFAULT_TIME_SLOTS: TimeSlot[] = [
  { time: '12PM', label: '12:00 PM - Lunch', available: true },
  { time: '3PM', label: '3:00 PM - Afternoon', available: true },
  { time: '6PM', label: '6:00 PM - Dinner', available: true },
  { time: '9PM', label: '9:00 PM - Late Dinner', available: true },
];

/**
 * Format date for API
 */
const formatDateForAPI = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * DateTimeSection - Date and time selection with smart scheduling awareness
 *
 * Features:
 * - Date picker with min/max date constraints
 * - Time slot selection with availability status
 * - Smart scheduling awareness (fetches availability based on venue location)
 * - Visual indicators for fully booked slots
 */
export const DateTimeSection: React.FC<DateTimeSectionProps> = ({
  control,
  errors,
  watch,
  className = '',
  showCompletionBadge = true,
  venueCoordinates,
  minDaysAdvance = 2,
  maxDaysAdvance = 365,
  onAvailabilityFetched,
  onSelectionChange,
}) => {
  // State
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>(DEFAULT_TIME_SLOTS);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [availabilityError, setAvailabilityError] = useState<string | null>(null);
  const [bookedDates, setBookedDates] = useState<Set<string>>(new Set());

  // Watch values
  const eventDate = watch('eventDate');
  const eventTime = watch('eventTime');

  // Check if section is complete
  const isComplete = Boolean(eventDate && eventTime);

  // Calculate min and max dates
  const minDate = new Date();
  minDate.setDate(minDate.getDate() + minDaysAdvance);
  minDate.setHours(0, 0, 0, 0);

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + maxDaysAdvance);
  maxDate.setHours(23, 59, 59, 999);

  /**
   * Fetch availability for a specific date
   */
  const fetchAvailability = useCallback(
    async (date: Date) => {
      setIsLoadingSlots(true);
      setAvailabilityError(null);

      try {
        const dateStr = formatDateForAPI(date);

        // Build query params
        const params = new URLSearchParams({ date: dateStr });

        // Add venue coordinates if available for travel-aware scheduling
        if (venueCoordinates) {
          params.append('venue_lat', venueCoordinates.lat.toString());
          params.append('venue_lng', venueCoordinates.lng.toString());
        }

        const response = await apiFetch<{
          timeSlots?: TimeSlot[];
          data?: { timeSlots?: TimeSlot[] };
        }>(`/api/v1/bookings/availability?${params.toString()}`, {
          cacheStrategy: {
            strategy: 'cache-first',
            ttl: 3 * 60 * 1000, // 3 minutes
          },
        });

        if (response.success && response.data) {
          // Handle both possible response shapes
          const slots =
            response.data.timeSlots ||
            (response.data as { data?: { timeSlots?: TimeSlot[] } }).data?.timeSlots ||
            DEFAULT_TIME_SLOTS;

          setTimeSlots(slots);

          if (onAvailabilityFetched) {
            onAvailabilityFetched(slots);
          }
        } else {
          // Fallback to default slots on error
          setTimeSlots(DEFAULT_TIME_SLOTS);
          console.warn('Could not fetch availability, using default slots');
        }
      } catch (error) {
        console.error('Error fetching availability:', error);
        setAvailabilityError('Could not check availability. Please try again.');
        setTimeSlots(DEFAULT_TIME_SLOTS);
      } finally {
        setIsLoadingSlots(false);
      }
    },
    [venueCoordinates, onAvailabilityFetched],
  );

  /**
   * Fetch booked dates for the calendar
   */
  const fetchBookedDates = useCallback(async () => {
    try {
      const response = await apiFetch<{ bookedDates?: string[] }>('/api/v1/bookings/booked-dates', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 5 * 60 * 1000, // 5 minutes
        },
      });

      if (response.success && response.data?.bookedDates) {
        setBookedDates(new Set(response.data.bookedDates));
      }
    } catch (error) {
      console.error('Error fetching booked dates:', error);
    }
  }, []);

  // Fetch booked dates on mount
  useEffect(() => {
    fetchBookedDates();
  }, [fetchBookedDates]);

  // Fetch availability when date changes
  useEffect(() => {
    if (eventDate) {
      fetchAvailability(eventDate);
    }
  }, [eventDate, fetchAvailability]);

  // Notify parent of selection changes
  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(eventDate || null, eventTime || '');
    }
  }, [eventDate, eventTime, onSelectionChange]);

  /**
   * Check if a date is bookable (not in past, not fully booked)
   */
  const isDateBookable = useCallback(
    (date: Date): boolean => {
      const dateStr = formatDateForAPI(date);
      return !bookedDates.has(dateStr) && date >= minDate && date <= maxDate;
    },
    [bookedDates, minDate, maxDate],
  );

  /**
   * Get time slot button classes based on availability
   */
  const getTimeSlotClasses = (slot: TimeSlot, isSelected: boolean): string => {
    const baseClasses =
      'relative flex flex-col items-center justify-center rounded-lg border-2 p-4 transition-all duration-200';

    if (!slot.available) {
      return `${baseClasses} cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400`;
    }

    if (isSelected) {
      return `${baseClasses} border-red-500 bg-red-50 text-red-700 ring-2 ring-red-200`;
    }

    return `${baseClasses} cursor-pointer border-gray-200 bg-white text-gray-700 hover:border-red-300 hover:bg-red-50`;
  };

  return (
    <div className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      {/* Section Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Calendar className="h-5 w-5 text-red-500" />
          Date &amp; Time
        </h2>
        {showCompletionBadge && (
          <div className="text-xs">
            {isComplete ? (
              <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                ✅ Complete
              </span>
            ) : (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                ⏳ Pending
              </span>
            )}
          </div>
        )}
      </div>

      {/* Smart scheduling notice */}
      {venueCoordinates && (
        <div className="mb-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
          <span className="font-semibold">🧠 Smart Scheduling:</span> Availability is calculated
          based on your venue location for accurate chef assignments.
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Date Picker */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="eventDate"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <Calendar className="h-4 w-4 text-gray-400" />
            Event Date
            <span className="text-red-500">*</span>
          </label>
          <Controller
            name="eventDate"
            control={control}
            rules={{
              required: 'Please select an event date',
              validate: (value) => {
                if (!value) return 'Please select an event date';
                if (value < minDate)
                  return `Please select a date at least ${minDaysAdvance} days from now`;
                if (value > maxDate)
                  return `Please select a date within the next ${maxDaysAdvance} days`;
                return true;
              },
            }}
            render={({ field }) => (
              <input
                id="eventDate"
                type="date"
                value={field.value ? formatDateForAPI(field.value) : ''}
                min={formatDateForAPI(minDate)}
                max={formatDateForAPI(maxDate)}
                onChange={(e) => {
                  const dateValue = e.target.value ? new Date(e.target.value + 'T00:00:00') : null;
                  field.onChange(dateValue);
                }}
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.eventDate
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
              />
            )}
          />
          {errors.eventDate && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {(errors.eventDate as { message?: string })?.message || 'Invalid date'}
            </p>
          )}
          <p className="text-xs text-gray-500">
            Bookings require at least {minDaysAdvance} days advance notice
          </p>
          <p className="mt-1 flex items-center gap-1 text-xs font-medium text-amber-600">
            <span>⚡</span> High demand on weekends! Secure your preferred time slot today.
          </p>
        </div>

        {/* Time Slot Selection - Only show after date is selected */}
        <div className="flex flex-col space-y-1.5">
          <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
            <Clock className="h-4 w-4 text-gray-400" />
            Event Time
            <span className="text-red-500">*</span>
          </label>

          {/* Prompt to enter address first */}
          {!venueCoordinates && (
            <div className="rounded-lg border-2 border-dashed border-amber-300 bg-amber-50 p-6 text-center">
              <AlertCircle className="mx-auto h-8 w-8 text-amber-500" />
              <p className="mt-2 text-sm font-medium text-amber-700">
                Please enter your venue address first
              </p>
              <p className="mt-1 text-xs text-amber-600">
                We use smart scheduling to find the best available times for your location
              </p>
            </div>
          )}

          {/* Prompt to select date (after address is entered) */}
          {venueCoordinates && !eventDate && (
            <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center">
              <Calendar className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm font-medium text-gray-600">Now select your event date</p>
              <p className="mt-1 text-xs text-gray-500">
                Available time slots will appear based on chef availability in your area
              </p>
            </div>
          )}

          {/* Loading state */}
          {venueCoordinates && eventDate && isLoadingSlots && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-red-500" />
              <span className="ml-2 text-sm text-gray-500">
                Checking chef availability in your area...
              </span>
            </div>
          )}

          {/* Error state */}
          {venueCoordinates && eventDate && availabilityError && (
            <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
              {availabilityError}
            </div>
          )}

          {/* Time slots grid - only show when address entered, date selected, and not loading */}
          {venueCoordinates && eventDate && !isLoadingSlots && (
            <Controller
              name="eventTime"
              control={control}
              rules={{ required: 'Please select a time slot' }}
              render={({ field }) => (
                <div className="grid grid-cols-2 gap-3">
                  {timeSlots.map((slot) => {
                    const isSelected = field.value === slot.time;
                    return (
                      <button
                        key={slot.time}
                        type="button"
                        onClick={() => {
                          if (slot.available) {
                            field.onChange(slot.time);
                          }
                        }}
                        disabled={!slot.available}
                        className={getTimeSlotClasses(slot, isSelected)}
                        aria-label={`Select ${slot.label}${!slot.available ? ' (unavailable)' : ''}`}
                      >
                        <span className="text-lg font-bold">{slot.time}</span>
                        <span className="text-xs">{slot.label.split(' - ')[1]}</span>
                        {!slot.available && (
                          <span className="absolute -top-2 right-2 rounded-full bg-gray-500 px-2 py-0.5 text-xs font-medium text-white">
                            {slot.reason || 'Booked'}
                          </span>
                        )}
                        {slot.available && slot.availableChefs !== undefined && (
                          <span className="mt-1 text-xs text-green-600">
                            {slot.availableChefs} chef{slot.availableChefs !== 1 ? 's' : ''}{' '}
                            available
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            />
          )}

          {errors.eventTime && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {(errors.eventTime as { message?: string })?.message || 'Please select a time'}
            </p>
          )}
        </div>
      </div>

      {/* Selected date/time summary */}
      {eventDate && eventTime && (
        <div className="mt-4 rounded-lg bg-green-50 p-4 text-center">
          <p className="text-sm text-green-800">
            <span className="font-semibold">Selected:</span>{' '}
            {eventDate.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}{' '}
            at {eventTime}
          </p>
        </div>
      )}
    </div>
  );
};

export default DateTimeSection;
