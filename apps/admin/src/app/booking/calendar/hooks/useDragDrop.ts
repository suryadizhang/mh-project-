/**
 * Drag and drop hook for calendar bookings
 * Handles drag state, drop logic, and API updates
 */

import { format } from 'date-fns';
import { useCallback, useState } from 'react';

import type {
  BookingMoveResult,
  CalendarBooking,
} from '../types/calendar.types';

interface UseDragDropProps {
  onBookingMoved: (
    booking: CalendarBooking,
    newDate: string,
    newSlot: string
  ) => Promise<BookingMoveResult>;
}

interface UseDragDropReturn {
  isDragging: boolean;
  draggedBooking: CalendarBooking | null;
  handleDragStart: (booking: CalendarBooking) => void;
  handleDragEnd: () => void;
  handleDrop: (targetDate: string, targetSlot: string) => Promise<void>;
  isDroppable: (targetDate: string, targetSlot: string) => boolean;
}

export function useDragDrop({
  onBookingMoved,
}: UseDragDropProps): UseDragDropReturn {
  const [isDragging, setIsDragging] = useState(false);
  const [draggedBooking, setDraggedBooking] = useState<CalendarBooking | null>(
    null
  );

  const handleDragStart = useCallback((booking: CalendarBooking) => {
    // Only allow dragging of confirmed or pending bookings
    if (booking.status === 'cancelled' || booking.status === 'completed') {
      return;
    }

    setIsDragging(true);
    setDraggedBooking(booking);
  }, []);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    setDraggedBooking(null);
  }, []);

  const handleDrop = useCallback(
    async (targetDate: string, targetSlot: string) => {
      if (!draggedBooking) return;

      // Don't do anything if dropped on the same slot
      const originalDate = format(draggedBooking.startTime, 'yyyy-MM-dd');
      const originalSlot = draggedBooking.slot;

      if (originalDate === targetDate && originalSlot === targetSlot) {
        handleDragEnd();
        return;
      }

      try {
        const result = await onBookingMoved(
          draggedBooking,
          targetDate,
          targetSlot
        );

        if (!result.success) {
          console.error('Failed to move booking:', result.error);
          // Could show toast notification here
        }
      } catch (error) {
        console.error('Error moving booking:', error);
      } finally {
        handleDragEnd();
      }
    },
    [draggedBooking, onBookingMoved, handleDragEnd]
  );

  const isDroppable = useCallback(
    (targetDate: string, targetSlot: string): boolean => {
      if (!draggedBooking) return false;

      // Can't drop on cancelled or completed bookings' slots
      // Can't drop in the past
      const targetDateTime = new Date(`${targetDate}T${targetSlot}`);
      const now = new Date();

      if (targetDateTime < now) {
        return false;
      }

      return true;
    },
    [draggedBooking]
  );

  return {
    isDragging,
    draggedBooking,
    handleDragStart,
    handleDragEnd,
    handleDrop,
    isDroppable,
  };
}

/**
 * API call to update booking date/time
 */
export async function updateBookingDateTime(
  bookingId: string,
  newDate: string,
  newSlot: string
): Promise<BookingMoveResult> {
  try {
    const response = await fetch(`/api/bookings/admin/${bookingId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        date: newDate,
        slot: newSlot,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update booking');
    }

    const data = await response.json();

    return {
      success: true,
      booking: data.data,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}
