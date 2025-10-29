/**
 * Weekly Calendar View Component
 * Displays bookings in a 7-day grid with time slots
 * Supports drag-and-drop rescheduling
 */

'use client';

import React, { useState, useCallback } from 'react';
import { format } from 'date-fns';
import { Clock, AlertCircle } from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import type { WeekView, CalendarBooking, BookingMoveResult } from '../types/calendar.types';
import { BookingCard } from './BookingCard';
import { updateBookingDateTime } from '../hooks/useDragDrop';

interface WeeklyCalendarProps {
  weekView: WeekView;
  onBookingClick?: (booking: CalendarBooking) => void;
  onRefresh?: () => void;
}

export function WeeklyCalendar({ weekView, onBookingClick, onRefresh }: WeeklyCalendarProps) {
  const toast = useToast();
  const [draggedBooking, setDraggedBooking] = useState<CalendarBooking | null>(null);
  const [dropTarget, setDropTarget] = useState<{ date: string; slot: string } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleDragStart = useCallback((booking: CalendarBooking) => {
    setDraggedBooking(booking);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedBooking(null);
    setDropTarget(null);
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent, date: string, slot: string) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      
      if (draggedBooking) {
        setDropTarget({ date, slot });
      }
    },
    [draggedBooking]
  );

  const handleDragLeave = useCallback(() => {
    setDropTarget(null);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent, targetDate: string, targetSlot: string) => {
      e.preventDefault();
      
      if (!draggedBooking) return;

      const originalDate = format(draggedBooking.startTime, 'yyyy-MM-dd');
      const originalSlot = draggedBooking.slot;

      // Don't do anything if dropped on the same slot
      if (originalDate === targetDate && originalSlot === targetSlot) {
        handleDragEnd();
        return;
      }

      setIsUpdating(true);

      try {
        const result: BookingMoveResult = await updateBookingDateTime(
          draggedBooking.booking_id,
          targetDate,
          targetSlot
        );

        if (result.success) {
          toast.success('Booking rescheduled', `Event moved to ${format(new Date(targetDate), 'MMM d')} at ${targetSlot}`);
          // Refresh calendar data
          onRefresh?.();
        } else {
          toast.error('Reschedule failed', result.error || 'Unable to move booking');
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

  const isDropTarget = (date: string, slot: string): boolean => {
    return dropTarget?.date === date && dropTarget?.slot === slot;
  };

  const getBookingsForSlot = (date: string, slot: string): CalendarBooking[] => {
    const day = weekView.days.find(d => d.dateString === date);
    if (!day) return [];

    return day.bookings.filter(b => b.slot === slot);
  };

  const timeSlots = Array.from({ length: 13 }, (_, i) => {
    const hour = i + 10; // 10 AM to 10 PM
    return {
      time: `${hour.toString().padStart(2, '0')}:00`,
      display: format(new Date(2000, 0, 1, hour, 0), 'h a'),
    };
  });

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

      {/* Header Row - Days */}
      <div className="grid grid-cols-8 border-b border-gray-200 bg-gray-50">
        {/* Time column header */}
        <div className="p-3 text-xs font-semibold text-gray-500 border-r border-gray-200">
          <Clock className="w-4 h-4" />
        </div>

        {/* Day headers */}
        {weekView.days.map((day) => (
          <div
            key={day.dateString}
            className={`p-3 text-center border-r border-gray-200 last:border-r-0 ${
              day.isToday ? 'bg-blue-50' : ''
            }`}
          >
            <div className="text-xs font-semibold text-gray-600 uppercase">
              {day.dayName}
            </div>
            <div
              className={`text-lg font-bold mt-1 ${
                day.isToday
                  ? 'bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto'
                  : 'text-gray-900'
              }`}
            >
              {day.dayNumber}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {day.bookingCount} {day.bookingCount === 1 ? 'booking' : 'bookings'}
            </div>
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="overflow-auto max-h-[calc(100vh-300px)]">
        <div className="grid grid-cols-8">
          {/* Time slots */}
          {timeSlots.map((timeSlot) => (
            <React.Fragment key={timeSlot.time}>
              {/* Time label */}
              <div className="p-2 text-xs font-medium text-gray-500 border-r border-b border-gray-200 bg-gray-50 sticky left-0 z-10">
                {timeSlot.display}
              </div>

              {/* Day cells */}
              {weekView.days.map((day) => {
                const bookings = getBookingsForSlot(day.dateString, timeSlot.time);
                const isTarget = isDropTarget(day.dateString, timeSlot.time);
                const isPast = new Date(`${day.dateString}T${timeSlot.time}`) < new Date();

                return (
                  <div
                    key={`${day.dateString}-${timeSlot.time}`}
                    className={`
                      min-h-[100px] p-2 border-r border-b border-gray-200 last:border-r-0
                      ${day.isWeekend ? 'bg-gray-50/50' : 'bg-white'}
                      ${isTarget ? 'bg-blue-100 ring-2 ring-blue-500 ring-inset' : ''}
                      ${isPast ? 'bg-gray-100/50' : ''}
                      ${!isPast && !draggedBooking ? 'hover:bg-gray-50' : ''}
                      transition-colors duration-150
                    `}
                    onDragOver={(e) => !isPast && handleDragOver(e, day.dateString, timeSlot.time)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => !isPast && handleDrop(e, day.dateString, timeSlot.time)}
                  >
                    {bookings.length > 0 ? (
                      <div className="space-y-1">
                        {bookings.map((booking) => (
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
                      </div>
                    ) : isPast ? (
                      <div className="h-full flex items-center justify-center">
                        <span className="text-xs text-gray-400">Past</span>
                      </div>
                    ) : isTarget ? (
                      <div className="h-full flex items-center justify-center">
                        <span className="text-xs text-blue-600 font-medium">Drop here</span>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
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
            <span>Drag bookings to reschedule</span>
          </div>
        </div>
      </div>
    </div>
  );
}
