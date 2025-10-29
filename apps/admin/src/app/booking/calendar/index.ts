/**
 * Calendar module exports
 * Centralized exports for calendar components, hooks, and types
 */

// Components
export { WeeklyCalendar } from './components/WeeklyCalendar';
export { MonthlyCalendar } from './components/MonthlyCalendar';
export { CalendarHeader } from './components/CalendarHeader';
export { BookingCard } from './components/BookingCard';

// Hooks
export { useCalendarData } from './hooks/useCalendarData';
export { useDragDrop, updateBookingDateTime } from './hooks/useDragDrop';

// Types
export type {
  CalendarView,
  CalendarBooking,
  TimeSlot,
  DayColumn,
  WeekView,
  MonthView,
  CalendarFilters,
  DragDropBooking,
  BookingMoveResult,
  CalendarStats,
  CalendarEvent,
} from './types/calendar.types';
