/**
 * Monthly Calendar View Component
 * Displays bookings in a month grid
 * Supports drag-and-drop between days
 */

'use client';

import React, { useState, useCallback } from 'react';
import { format, isSameMonth } from 'date-fns';
import { ChevronRight, AlertCircle } from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import type { MonthView, CalendarBooking, DayColumn, BookingMoveResult } from '../types/calendar.types';
import { BookingCard } from './BookingCard';
import { updateBookingDateTime } from '../hooks/useDragDrop';

interface MonthlyCalendarProps {
  monthView: MonthView;
  onBookingClick?: (booking: CalendarBooking) => void;
  onDayClick?: (day: DayColumn) => void;
  onRefresh?: () => void;
}

export function MonthlyCalendar({ monthView, onBookingClick, onDayClick, onRefresh }: MonthlyCalendarProps) {
  const toast = useToast();
  const [draggedBooking, setDraggedBooking] = useState<CalendarBooking | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleDragStart = useCallback((booking: CalendarBooking) => {
    setDraggedBooking(booking);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedBooking(null);
    setDropTarget(null);
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent, date: string) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      
      if (draggedBooking) {
        setDropTarget(date);
      }
    },
    [draggedBooking]
  );

  const handleDragLeave = useCallback(() => {
    setDropTarget(null);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent, targetDate: string) => {
      e.preventDefault();
      
      if (!draggedBooking) return;

      const originalDate = format(draggedBooking.startTime, 'yyyy-MM-dd');

      // Don't do anything if dropped on the same day
      if (originalDate === targetDate) {
        handleDragEnd();
        return;
      }

      setIsUpdating(true);

      try {
        // Keep the same time slot when moving to a different day
        const result: BookingMoveResult = await updateBookingDateTime(
          draggedBooking.booking_id,
          targetDate,
          draggedBooking.slot
        );

        if (result.success) {
          toast.success('Booking moved', `Event rescheduled to ${format(new Date(targetDate), 'MMM d')}`);
          // Refresh calendar data
          onRefresh?.();
        } else {
          toast.error('Failed to move booking', result.error || 'Unable to reschedule event');
        }
      } catch (error) {
        console.error('Error moving booking:', error);
        toast.error('Move failed', 'An error occurred while moving the booking');
      } finally {
        setIsUpdating(false);
        handleDragEnd();
      }
    },
    [draggedBooking, onRefresh, handleDragEnd, toast]
  );

  const isDropTarget = (date: string): boolean => {
    return dropTarget === date;
  };

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100);
  };

  const getDayStats = (day: DayColumn) => {
    const confirmed = day.bookings.filter(b => b.status === 'confirmed').length;
    const pending = day.bookings.filter(b => b.status === 'pending').length;
    const revenue = day.bookings
      .filter(b => b.status !== 'cancelled')
      .reduce((sum, b) => sum + b.total_due_cents, 0);

    return { confirmed, pending, revenue };
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Loading Overlay */}
      {isUpdating && (
        <div className="absolute inset-0 bg-white/80 z-50 flex items-center justify-center">
          <div className="flex items-center gap-2 text-blue-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="font-medium">Updating booking...</span>
          </div>
        </div>
      )}

      {/* Day of Week Headers */}
      <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
        {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((day) => (
          <div
            key={day}
            className="p-3 text-center text-xs font-semibold text-gray-600 uppercase border-r border-gray-200 last:border-r-0"
          >
            {day.slice(0, 3)}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7">
        {monthView.weeks.map((week, weekIndex) => (
          <React.Fragment key={weekIndex}>
            {week.map((day) => {
              const isTarget = isDropTarget(day.dateString);
              const isPast = day.date < new Date(new Date().setHours(0, 0, 0, 0));
              const isCurrentMonth = isSameMonth(day.date, monthView.monthStart);
              const stats = getDayStats(day);

              return (
                <div
                  key={day.dateString}
                  className={`
                    min-h-[140px] border-r border-b border-gray-200 last:border-r-0
                    ${!isCurrentMonth ? 'bg-gray-50/50' : 'bg-white'}
                    ${day.isWeekend && isCurrentMonth ? 'bg-blue-50/20' : ''}
                    ${isTarget ? 'bg-blue-100 ring-2 ring-blue-500 ring-inset' : ''}
                    ${isPast ? 'opacity-60' : ''}
                    transition-colors duration-150
                  `}
                  onDragOver={(e) => !isPast && handleDragOver(e, day.dateString)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => !isPast && handleDrop(e, day.dateString)}
                >
                  {/* Day Header */}
                  <div
                    className={`
                      p-2 flex items-center justify-between cursor-pointer
                      ${day.isToday ? 'bg-blue-600 text-white' : ''}
                      hover:bg-gray-100 transition-colors
                    `}
                    onClick={() => onDayClick?.(day)}
                  >
                    <span
                      className={`
                        text-sm font-semibold
                        ${day.isToday ? 'text-white' : isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
                      `}
                    >
                      {day.dayNumber}
                    </span>
                    {day.bookingCount > 0 && (
                      <span
                        className={`
                          text-xs px-1.5 py-0.5 rounded-full font-medium
                          ${day.isToday ? 'bg-white text-blue-600' : 'bg-blue-100 text-blue-600'}
                        `}
                      >
                        {day.bookingCount}
                      </span>
                    )}
                  </div>

                  {/* Bookings List */}
                  <div className="p-2 space-y-1 overflow-y-auto max-h-[100px]">
                    {day.bookings.slice(0, 3).map((booking) => (
                      <BookingCard
                        key={booking.booking_id}
                        booking={booking}
                        compact
                        isDragging={draggedBooking?.booking_id === booking.booking_id}
                        onDragStart={() => handleDragStart(booking)}
                        onDragEnd={handleDragEnd}
                        onClick={() => onBookingClick?.(booking)}
                      />
                    ))}

                    {/* Show more indicator */}
                    {day.bookingCount > 3 && (
                      <button
                        onClick={() => onDayClick?.(day)}
                        className="w-full text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center justify-center gap-1 py-1"
                      >
                        <span>+{day.bookingCount - 3} more</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}

                    {/* Drop target indicator */}
                    {isTarget && day.bookingCount === 0 && (
                      <div className="flex items-center justify-center h-16 text-xs text-blue-600 font-medium">
                        Drop booking here
                      </div>
                    )}

                    {/* Empty state */}
                    {day.bookingCount === 0 && !isTarget && isCurrentMonth && !isPast && (
                      <div className="flex items-center justify-center h-16 text-xs text-gray-400">
                        No bookings
                      </div>
                    )}
                  </div>

                  {/* Day Stats */}
                  {day.bookingCount > 0 && (
                    <div className="px-2 pb-2 text-[10px] text-gray-500 space-y-0.5">
                      {stats.confirmed > 0 && (
                        <div className="flex items-center justify-between">
                          <span>Confirmed:</span>
                          <span className="font-medium text-green-600">{stats.confirmed}</span>
                        </div>
                      )}
                      {stats.pending > 0 && (
                        <div className="flex items-center justify-between">
                          <span>Pending:</span>
                          <span className="font-medium text-yellow-600">{stats.pending}</span>
                        </div>
                      )}
                      <div className="flex items-center justify-between pt-0.5 border-t border-gray-200">
                        <span>Revenue:</span>
                        <span className="font-semibold text-gray-900">{formatCurrency(stats.revenue)}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      {/* Legend */}
      <div className="border-t border-gray-200 bg-gray-50 p-3">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-100 border border-green-200"></div>
              <span className="text-gray-600">Confirmed</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-yellow-100 border border-yellow-200"></div>
              <span className="text-gray-600">Pending</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-blue-100 border border-blue-200"></div>
              <span className="text-gray-600">Completed</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-red-100 border border-red-200"></div>
              <span className="text-gray-600">Cancelled</span>
            </div>
          </div>
          <div className="flex-1"></div>
          <div className="flex items-center gap-1 text-gray-500">
            <AlertCircle className="w-3 h-3" />
            <span>Drag bookings between days • Click day for details</span>
          </div>
        </div>
      </div>

      {/* Month Summary */}
      <div className="border-t border-gray-200 bg-gray-50 p-3">
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold text-gray-700">
            {format(monthView.monthStart, 'MMMM yyyy')} Summary
          </span>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">
              Total Bookings: <span className="font-semibold text-gray-900">{monthView.totalBookings}</span>
            </span>
            <span className="text-gray-600">
              Total Revenue: <span className="font-semibold text-gray-900">
                {formatCurrency(
                  monthView.weeks.flat().reduce((sum, day) => 
                    sum + day.bookings
                      .filter(b => b.status !== 'cancelled')
                      .reduce((daySum, b) => daySum + b.total_due_cents, 0)
                  , 0)
                )}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
