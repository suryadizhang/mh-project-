/**
 * Calendar-specific type definitions
 * Extends base Booking types for calendar views
 */

import { Booking } from '@/types';

export type CalendarView = 'week' | 'month';

export interface CalendarBooking extends Booking {
  // Computed properties for calendar display
  startTime: Date;
  endTime: Date;
  duration: number; // in minutes
  color?: string;
  isConflict?: boolean;
}

export interface TimeSlot {
  time: string; // HH:mm format
  hour: number;
  bookings: CalendarBooking[];
}

export interface DayColumn {
  date: Date;
  dateString: string; // ISO format YYYY-MM-DD
  dayName: string;
  dayNumber: number;
  isToday: boolean;
  isWeekend: boolean;
  bookings: CalendarBooking[];
  bookingCount: number;
}

export interface WeekView {
  weekStart: Date;
  weekEnd: Date;
  days: DayColumn[];
  timeSlots: TimeSlot[];
}

export interface MonthView {
  monthStart: Date;
  monthEnd: Date;
  weeks: DayColumn[][];
  totalBookings: number;
}

export interface CalendarFilters {
  view: CalendarView;
  startDate: Date;
  endDate: Date;
  status?: string[];
  search?: string;
}

export interface DragDropBooking {
  booking: CalendarBooking;
  originalDate: string;
  originalSlot: string;
}

export interface BookingMoveResult {
  success: boolean;
  booking?: CalendarBooking;
  error?: string;
}

export interface CalendarStats {
  totalBookings: number;
  confirmedBookings: number;
  pendingBookings: number;
  revenue: number;
  averageGuests: number;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  booking: CalendarBooking;
  color: string;
  isDraggable: boolean;
}
