/**
 * Calendar data fetching and management hook
 * Handles API calls for weekly and monthly views
 */

import {
  endOfMonth,
  endOfWeek,
  format,
  startOfMonth,
  startOfWeek,
} from 'date-fns';
import { useCallback, useEffect, useMemo, useState } from 'react';

import type { Booking } from '@/types';

import type {
  CalendarBooking,
  CalendarView,
  DayColumn,
  MonthView,
  WeekView,
} from '../types/calendar.types';

interface UseCalendarDataProps {
  view: CalendarView;
  currentDate: Date;
  /** Filter by station ID (for Station Managers) */
  stationId?: string | null;
  /** Filter by chef ID (for Chef role viewing own events) */
  chefId?: string | null;
}

interface UseCalendarDataReturn {
  bookings: CalendarBooking[];
  weekView: WeekView | null;
  monthView: MonthView | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  moveToNext: () => void;
  moveToPrevious: () => void;
  moveToToday: () => void;
}

export function useCalendarData({
  view,
  currentDate,
  stationId,
  chefId,
}: UseCalendarDataProps): UseCalendarDataReturn {
  const [bookings, setBookings] = useState<CalendarBooking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate date range based on view
  const dateRange = useMemo(() => {
    if (view === 'week') {
      return {
        start: startOfWeek(currentDate, { weekStartsOn: 0 }), // Sunday
        end: endOfWeek(currentDate, { weekStartsOn: 0 }),
      };
    } else {
      return {
        start: startOfMonth(currentDate),
        end: endOfMonth(currentDate),
      };
    }
  }, [view, currentDate]);

  // Fetch bookings from API
  const fetchBookings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        date_from: format(dateRange.start, 'yyyy-MM-dd'),
        date_to: format(dateRange.end, 'yyyy-MM-dd'),
      });

      // Add role-based filters
      if (stationId) {
        params.append('station_id', stationId);
      }
      if (chefId) {
        params.append('chef_id', chefId);
      }

      const endpoint =
        view === 'week'
          ? `/api/bookings/admin/weekly?${params}`
          : `/api/bookings/admin/monthly?${params}`;

      const response = await fetch(endpoint, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch bookings: ${response.statusText}`);
      }

      const data = await response.json();

      // Transform bookings to calendar bookings with time data
      const calendarBookings: CalendarBooking[] = (data.data || []).map(
        (booking: Booking) => {
          const bookingDate = new Date(booking.date);
          const [hours, minutes] = booking.slot.split(':').map(Number);

          const startTime = new Date(bookingDate);
          startTime.setHours(hours, minutes, 0);

          // Assume 2-hour duration for hibachi events
          const endTime = new Date(startTime);
          endTime.setHours(hours + 2, minutes, 0);

          return {
            ...booking,
            startTime,
            endTime,
            duration: 120, // 2 hours in minutes
            color: getStatusColor(booking.status),
          };
        }
      );

      setBookings(calendarBookings);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch bookings';
      setError(errorMessage);
      console.error('Error fetching calendar bookings:', err);
    } finally {
      setLoading(false);
    }
  }, [view, dateRange, stationId, chefId]);

  // Fetch on mount and when dependencies change
  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  // Generate week view data
  const weekView = useMemo<WeekView | null>(() => {
    if (view !== 'week') return null;

    const days: DayColumn[] = [];
    const currentDay = new Date(dateRange.start);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < 7; i++) {
      const dateString = format(currentDay, 'yyyy-MM-dd');
      const dayBookings = bookings.filter(
        b => format(b.startTime, 'yyyy-MM-dd') === dateString
      );

      days.push({
        date: new Date(currentDay),
        dateString,
        dayName: format(currentDay, 'EEE'),
        dayNumber: currentDay.getDate(),
        isToday:
          format(currentDay, 'yyyy-MM-dd') === format(today, 'yyyy-MM-dd'),
        isWeekend: currentDay.getDay() === 0 || currentDay.getDay() === 6,
        bookings: dayBookings,
        bookingCount: dayBookings.length,
      });

      currentDay.setDate(currentDay.getDate() + 1);
    }

    // Generate time slots (10 AM to 10 PM)
    const timeSlots = [];
    for (let hour = 10; hour <= 22; hour++) {
      timeSlots.push({
        time: format(new Date(2000, 0, 1, hour, 0), 'HH:mm'),
        hour,
        bookings: bookings.filter(b => b.startTime.getHours() === hour),
      });
    }

    return {
      weekStart: dateRange.start,
      weekEnd: dateRange.end,
      days,
      timeSlots,
    };
  }, [view, bookings, dateRange]);

  // Generate month view data
  const monthView = useMemo<MonthView | null>(() => {
    if (view !== 'month') return null;

    const weeks: DayColumn[][] = [];
    const firstDay = startOfMonth(currentDate);
    const lastDay = endOfMonth(currentDate);

    // Start from the first Sunday of the week containing the first day
    const currentDay = startOfWeek(firstDay, { weekStartsOn: 0 });
    const endDay = endOfWeek(lastDay, { weekStartsOn: 0 });

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    while (currentDay <= endDay) {
      const week: DayColumn[] = [];

      for (let i = 0; i < 7; i++) {
        const dateString = format(currentDay, 'yyyy-MM-dd');
        const dayBookings = bookings.filter(
          b => format(b.startTime, 'yyyy-MM-dd') === dateString
        );

        week.push({
          date: new Date(currentDay),
          dateString,
          dayName: format(currentDay, 'EEE'),
          dayNumber: currentDay.getDate(),
          isToday:
            format(currentDay, 'yyyy-MM-dd') === format(today, 'yyyy-MM-dd'),
          isWeekend: currentDay.getDay() === 0 || currentDay.getDay() === 6,
          bookings: dayBookings,
          bookingCount: dayBookings.length,
        });

        currentDay.setDate(currentDay.getDate() + 1);
      }

      weeks.push(week);
    }

    return {
      monthStart: dateRange.start,
      monthEnd: dateRange.end,
      weeks,
      totalBookings: bookings.length,
    };
  }, [view, bookings, dateRange, currentDate]);

  // Navigation functions
  const moveToNext = useCallback(() => {
    // Implementation handled by parent component
  }, []);

  const moveToPrevious = useCallback(() => {
    // Implementation handled by parent component
  }, []);

  const moveToToday = useCallback(() => {
    // Implementation handled by parent component
  }, []);

  return {
    bookings,
    weekView,
    monthView,
    loading,
    error,
    refetch: fetchBookings,
    moveToNext,
    moveToPrevious,
    moveToToday,
  };
}

// Helper function to get status color
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'confirmed':
      return '#10b981'; // green
    case 'pending':
      return '#f59e0b'; // yellow
    case 'cancelled':
      return '#ef4444'; // red
    case 'completed':
      return '#3b82f6'; // blue
    default:
      return '#6b7280'; // gray
  }
}
