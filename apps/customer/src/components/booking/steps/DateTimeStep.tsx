'use client';

import React, { useState, useCallback } from 'react';
import { UseFormSetValue, UseFormWatch } from 'react-hook-form';
import { Calendar, Clock, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { BookingFormData, BaseStepProps, StepVariant, TimeSlot, AlternativeSuggestion, VenueCoordinates } from './types';

// Default time slots
const DEFAULT_TIME_SLOTS: TimeSlot[] = [
  { time: '12PM', label: '12:00 PM', available: 10, isAvailable: true },
  { time: '3PM', label: '3:00 PM', available: 10, isAvailable: true },
  { time: '6PM', label: '6:00 PM', available: 10, isAvailable: true },
  { time: '9PM', label: '9:00 PM', available: 10, isAvailable: true },
];

interface DateTimeStepProps extends Omit<BaseStepProps<BookingFormData>, 'isValid'> {
  setValue: UseFormSetValue<BookingFormData>;
  watch: UseFormWatch<BookingFormData>;
  onBack: () => void;
  isValid?: boolean;
  venueCoordinates?: VenueCoordinates | null;
  guestCount?: number;
  onCheckAvailability?: (date: string, venueCoords: VenueCoordinates, guestCount: number) => Promise<{
    slots: TimeSlot[];
    suggestions?: AlternativeSuggestion[];
  }>;
}

/**
 * Style configuration for different variants
 */
const getStyles = (variant: StepVariant = 'booking') => {
  if (variant === 'quote') {
    return {
      container: 'space-y-6',
      label: 'block text-sm font-semibold text-gray-700 mb-4',
      calendar: {
        wrapper: 'bg-white rounded-xl p-4 border border-gray-200',
        header: 'text-lg font-semibold text-gray-900',
        nav: 'p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
        navIcon: 'w-5 h-5 text-gray-600',
        weekday: 'text-center text-xs font-medium text-gray-500 py-2',
        dayBase: 'p-2 text-center rounded-lg transition-all text-gray-700',
        daySelected: 'bg-red-600 text-white font-bold',
        dayToday: 'bg-gray-100 text-red-600 font-semibold',
        daySelectable: 'hover:bg-red-50',
        dayDisabled: 'text-gray-300 cursor-not-allowed',
      },
      timeSlots: {
        wrapper: 'grid grid-cols-2 gap-3',
        base: 'p-4 rounded-xl border transition-all',
        selected: 'bg-red-600 border-red-600 text-white',
        available: 'bg-white border-gray-200 text-gray-700 hover:border-red-300',
        unavailable: 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed',
      },
      loading: 'flex items-center justify-center py-8',
      spinner: 'animate-spin rounded-full h-8 w-8 border-b-2 border-red-600',
      suggestions: 'bg-blue-50 border border-blue-200 rounded-xl p-4',
      suggestionsText: 'text-sm text-blue-700 font-medium mb-2',
      suggestionButton: 'px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition-colors',
      backButton: 'flex-1 py-3 px-6 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-all',
      continueButton: 'flex-1 py-3 px-6 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-xl hover:from-red-700 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all',
      errorText: 'mt-2 text-sm text-red-600',
    };
  }

  // Default 'booking' variant (dark theme from original)
  return {
    container: 'space-y-6',
    label: 'block text-sm font-medium text-gray-300 mb-4',
    calendar: {
      wrapper: 'bg-gray-800/50 rounded-lg p-4 border border-gray-700',
      header: 'text-lg font-semibold text-white',
      nav: 'p-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
      navIcon: 'w-5 h-5 text-gray-400',
      weekday: 'text-center text-xs font-medium text-gray-500 py-2',
      dayBase: 'p-2 text-center rounded-lg transition-all',
      daySelected: 'bg-amber-500 text-white font-bold',
      dayToday: 'bg-gray-700 text-amber-500 font-semibold',
      daySelectable: 'hover:bg-gray-700 text-gray-300',
      dayDisabled: 'text-gray-600 cursor-not-allowed',
    },
    timeSlots: {
      wrapper: 'grid grid-cols-2 gap-3',
      base: 'p-4 rounded-lg border transition-all',
      selected: 'bg-amber-500 border-amber-500 text-white',
      available: 'bg-gray-800/50 border-gray-700 text-gray-300 hover:border-amber-500/50',
      unavailable: 'bg-gray-800/30 border-gray-700 text-gray-600 cursor-not-allowed',
    },
    loading: 'flex items-center justify-center py-8',
    spinner: 'animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500',
    suggestions: 'bg-blue-500/10 border border-blue-500/20 rounded-lg p-4',
    suggestionsText: 'text-sm text-blue-400 font-medium mb-2',
    suggestionButton: 'px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm hover:bg-blue-500/30 transition-colors',
    backButton: 'flex-1 py-3 px-6 bg-gray-700 text-white font-semibold rounded-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all',
    continueButton: 'flex-1 py-3 px-6 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold rounded-lg hover:from-amber-600 hover:to-orange-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all',
    errorText: 'mt-2 text-sm text-red-400',
  };
};

/**
 * Step 4: Date & Time Selection
 * Calendar date picker and time slot selection with availability check
 * Supports both 'booking' (dark theme) and 'quote' (light theme) styling
 */
export function DateTimeStep({
  register,
  errors,
  setValue,
  watch,
  onContinue,
  onBack,
  venueCoordinates,
  guestCount = 10,
  onCheckAvailability,
  variant = 'booking',
}: DateTimeStepProps) {
  const selectedDate = watch('eventDate');
  const selectedTime = watch('eventTime');
  const styles = getStyles(variant);

  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>(DEFAULT_TIME_SLOTS);
  const [suggestions, setSuggestions] = useState<AlternativeSuggestion[]>([]);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);

  // Get days in current month view
  const getDaysInMonth = useCallback(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: (Date | null)[] = [];

    // Add empty slots for days before first day of month
    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(null);
    }

    // Add all days of month
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  }, [currentMonth]);

  // Check if a date is selectable (today or future)
  const isDateSelectable = useCallback((date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date >= today;
  }, []);

  // Handle date selection
  const handleDateSelect = useCallback(
    async (date: Date) => {
      setValue('eventDate', date, { shouldValidate: true });

      // Check availability if callback provided and we have coordinates
      if (onCheckAvailability && venueCoordinates) {
        setIsLoadingSlots(true);
        try {
          const dateStr = date.toISOString().split('T')[0];
          const result = await onCheckAvailability(dateStr, venueCoordinates, guestCount);
          setTimeSlots(result.slots);
          setSuggestions(result.suggestions || []);
        } catch (error) {
          console.error('Failed to check availability:', error);
          setTimeSlots(DEFAULT_TIME_SLOTS);
        } finally {
          setIsLoadingSlots(false);
        }
      }
    },
    [setValue, onCheckAvailability, venueCoordinates, guestCount]
  );

  // Handle time selection
  const handleTimeSelect = useCallback(
    (time: '12PM' | '3PM' | '6PM' | '9PM') => {
      setValue('eventTime', time, { shouldValidate: true });
    },
    [setValue]
  );

  // Navigate months
  const goToPreviousMonth = useCallback(() => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }, []);

  const goToNextMonth = useCallback(() => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }, []);

  // Check if previous month navigation should be disabled
  const isPreviousMonthDisabled = useCallback(() => {
    const today = new Date();
    return (
      currentMonth.getFullYear() === today.getFullYear() &&
      currentMonth.getMonth() === today.getMonth()
    );
  }, [currentMonth]);

  const days = getDaysInMonth();
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className={styles.container} data-testid="date-time-step">
      {/* Calendar Section */}
      <div>
        <label className={styles.label}>
          <Calendar className="inline-block w-5 h-5 mr-2" style={{ color: variant === 'quote' ? '#dc2626' : '#f59e0b' }} />
          Select Event Date
        </label>

        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            type="button"
            onClick={goToPreviousMonth}
            disabled={isPreviousMonthDisabled()}
            className={styles.calendar.nav}
            aria-label="Previous month"
          >
            <ChevronLeft className={styles.calendar.navIcon} />
          </button>
          <span className={styles.calendar.header}>
            {currentMonth.toLocaleDateString('en-US', {
              month: 'long',
              year: 'numeric',
            })}
          </span>
          <button
            type="button"
            onClick={goToNextMonth}
            className={styles.calendar.nav}
            aria-label="Next month"
          >
            <ChevronRight className={styles.calendar.navIcon} />
          </button>
        </div>

        {/* Calendar Grid */}
        <div className={styles.calendar.wrapper}>
          {/* Week day headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {weekDays.map((day) => (
              <div key={day} className={styles.calendar.weekday}>
                {day}
              </div>
            ))}
          </div>

          {/* Calendar days */}
          <div className="grid grid-cols-7 gap-1">
            {days.map((date, index) => {
              if (!date) {
                return <div key={`empty-${index}`} className="p-2" />;
              }

              const isSelectable = isDateSelectable(date);
              const isSelected =
                selectedDate &&
                date.toDateString() === new Date(selectedDate).toDateString();
              const isToday = date.toDateString() === new Date().toDateString();

              let dayClass = styles.calendar.dayBase;
              if (isSelected) {
                dayClass += ` ${styles.calendar.daySelected}`;
              } else if (isToday) {
                dayClass += ` ${styles.calendar.dayToday}`;
              } else if (isSelectable) {
                dayClass += ` ${styles.calendar.daySelectable}`;
              } else {
                dayClass += ` ${styles.calendar.dayDisabled}`;
              }

              return (
                <button
                  key={date.toISOString()}
                  type="button"
                  onClick={() => isSelectable && handleDateSelect(date)}
                  disabled={!isSelectable}
                  className={dayClass}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
        </div>
        {errors.eventDate && (
          <p className={styles.errorText}>{errors.eventDate.message}</p>
        )}
      </div>

      {/* Time Slots Section */}
      {selectedDate && (
        <div>
          <label className={styles.label}>
            <Clock className="inline-block w-5 h-5 mr-2" style={{ color: variant === 'quote' ? '#dc2626' : '#f59e0b' }} />
            Select Time Slot
          </label>

          {isLoadingSlots ? (
            <div className={styles.loading}>
              <div className={styles.spinner} />
              <span className="ml-3 text-gray-400">Checking availability...</span>
            </div>
          ) : (
            <div className={styles.timeSlots.wrapper}>
              {timeSlots.map((slot) => {
                let slotClass = styles.timeSlots.base;
                if (selectedTime === slot.time) {
                  slotClass += ` ${styles.timeSlots.selected}`;
                } else if (slot.isAvailable) {
                  slotClass += ` ${styles.timeSlots.available}`;
                } else {
                  slotClass += ` ${styles.timeSlots.unavailable}`;
                }

                return (
                  <button
                    key={slot.time}
                    type="button"
                    onClick={() => slot.isAvailable && handleTimeSelect(slot.time as '12PM' | '3PM' | '6PM' | '9PM')}
                    disabled={!slot.isAvailable}
                    className={slotClass}
                  >
                    <div className="text-lg font-semibold">{slot.label}</div>
                    <div className="text-sm opacity-75">
                      {slot.isAvailable
                        ? `${slot.available} chefs available`
                        : 'Unavailable'}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          {errors.eventTime && (
            <p className={styles.errorText}>{errors.eventTime.message}</p>
          )}
        </div>
      )}

      {/* Alternative Suggestions */}
      {suggestions.length > 0 && (
        <div className={styles.suggestions}>
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: variant === 'quote' ? '#3b82f6' : '#60a5fa' }} />
            <div>
              <p className={styles.suggestionsText}>
                Your selected time is limited. Consider these alternatives:
              </p>
              <div className="flex flex-wrap gap-2">
                {suggestions.slice(0, 3).map((suggestion, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      const [year, month, day] = suggestion.slot_date.split('-').map(Number);
                      handleDateSelect(new Date(year, month - 1, day));
                      handleTimeSelect(suggestion.slot_time as '12PM' | '3PM' | '6PM' | '9PM');
                    }}
                    className={styles.suggestionButton}
                  >
                    {suggestion.slot_date} at {suggestion.slot_time}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hidden inputs for form state */}
      <input type="hidden" {...register('eventDate', { required: 'Please select a date' })} />
      <input type="hidden" {...register('eventTime', { required: 'Please select a time slot' })} />

      {/* Navigation Buttons */}
      <div className="flex gap-4 pt-4">
        <button
          type="button"
          onClick={onBack}
          className={styles.backButton}
        >
          Back
        </button>
        <button
          type="button"
          onClick={onContinue}
          disabled={!selectedDate || !selectedTime}
          className={styles.continueButton}
        >
          Review Booking
        </button>
      </div>
    </div>
  );
}
