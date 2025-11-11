/**
 * Calendar module exports
 * Centralized exports for calendar components, hooks, and types
 */

// Components
export { BookingCard } from './components/BookingCard';
export { CalendarHeader } from './components/CalendarHeader';
export { MonthlyCalendar } from './components/MonthlyCalendar';
export { WeeklyCalendar } from './components/WeeklyCalendar';

// Hooks
export { useCalendarData } from './hooks/useCalendarData';
export { updateBookingDateTime, useDragDrop } from './hooks/useDragDrop';

// Types
export type {
  BookingMoveResult,
  CalendarBooking,
  CalendarEvent,
  CalendarFilters,
  CalendarStats,
  CalendarView,
  DayColumn,
  DragDropBooking,
  MonthView,
  TimeSlot,
  WeekView,
} from './types/calendar.types';
