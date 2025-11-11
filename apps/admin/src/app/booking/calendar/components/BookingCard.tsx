/**
 * Booking Card Component
 * Draggable card displaying booking information
 */

'use client';

import { format } from 'date-fns';
import { Clock, DollarSign, Phone, Users } from 'lucide-react';
import React from 'react';

import type { CalendarBooking } from '../types/calendar.types';

interface BookingCardProps {
  booking: CalendarBooking;
  isDragging?: boolean;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onClick?: () => void;
  compact?: boolean;
}

export function BookingCard({
  booking,
  isDragging = false,
  onDragStart,
  onDragEnd,
  onClick,
  compact = false,
}: BookingCardProps) {
  const isDraggable =
    booking.status === 'confirmed' || booking.status === 'pending';

  const handleDragStart = (e: React.DragEvent) => {
    if (!isDraggable) {
      e.preventDefault();
      return;
    }

    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('booking_id', booking.booking_id);
    onDragStart?.();
  };

  const handleDragEnd = () => {
    onDragEnd?.();
  };

  const statusStyles: Record<string, string> = {
    confirmed: 'bg-green-50 border-green-200 text-green-800',
    pending: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    cancelled: 'bg-red-50 border-red-200 text-red-800 opacity-60',
    completed: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const statusStyle =
    statusStyles[booking.status] || 'bg-gray-50 border-gray-200 text-gray-800';

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100);
  };

  if (compact) {
    return (
      <div
        draggable={isDraggable}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onClick={onClick}
        className={`
          ${statusStyle}
          border rounded px-2 py-1 text-xs mb-1
          ${isDraggable ? 'cursor-move hover:shadow-md' : 'cursor-not-allowed'}
          ${isDragging ? 'opacity-50' : ''}
          transition-all duration-150
        `}
        title={`${booking.customer.name} - ${booking.total_guests} guests`}
      >
        <div className="font-semibold truncate">{booking.customer.name}</div>
        <div className="flex items-center gap-1 text-[10px] opacity-80">
          <Users className="w-2 h-2" />
          <span>{booking.total_guests}</span>
          <span className="mx-1">•</span>
          <Clock className="w-2 h-2" />
          <span>{booking.slot}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      draggable={isDraggable}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onClick={onClick}
      className={`
        ${statusStyle}
        border-2 rounded-lg p-3 shadow-sm
        ${isDraggable ? 'cursor-move hover:shadow-lg hover:scale-[1.02]' : 'cursor-not-allowed'}
        ${isDragging ? 'opacity-50 scale-95' : ''}
        transition-all duration-200
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm truncate">
            {booking.customer.name}
          </h4>
          <p className="text-xs opacity-80 truncate">
            {booking.customer.email}
          </p>
        </div>
        <span
          className={`
          px-2 py-1 rounded text-[10px] font-semibold uppercase tracking-wide
          ${booking.status === 'confirmed' ? 'bg-green-100' : ''}
          ${booking.status === 'pending' ? 'bg-yellow-100' : ''}
          ${booking.status === 'cancelled' ? 'bg-red-100' : ''}
          ${booking.status === 'completed' ? 'bg-blue-100' : ''}
        `}
        >
          {booking.status}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-1 text-xs">
        <div className="flex items-center gap-2">
          <Clock className="w-3 h-3 opacity-60" />
          <span>
            {format(booking.startTime, 'h:mm a')} -{' '}
            {format(booking.endTime, 'h:mm a')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Users className="w-3 h-3 opacity-60" />
          <span>{booking.total_guests} guests</span>
        </div>

        {booking.customer.phone && (
          <div className="flex items-center gap-2">
            <Phone className="w-3 h-3 opacity-60" />
            <span>{booking.customer.phone}</span>
          </div>
        )}

        <div className="flex items-center gap-2">
          <DollarSign className="w-3 h-3 opacity-60" />
          <span>
            {formatCurrency(booking.total_due_cents)}
            {booking.balance_due_cents > 0 && (
              <span className="text-red-600 ml-1">
                ({formatCurrency(booking.balance_due_cents)} due)
              </span>
            )}
          </span>
        </div>
      </div>

      {/* Special Requests */}
      {booking.special_requests && (
        <div className="mt-2 pt-2 border-t border-current/10">
          <p className="text-xs italic opacity-80 line-clamp-2">
            {booking.special_requests}
          </p>
        </div>
      )}

      {/* Drag Hint */}
      {isDraggable && !isDragging && (
        <div className="mt-2 text-[10px] opacity-50 text-center">
          Drag to reschedule
        </div>
      )}
    </div>
  );
}
