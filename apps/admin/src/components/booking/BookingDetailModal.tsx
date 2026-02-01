'use client';

/**
 * Booking Detail Modal
 * ====================
 *
 * Modal for viewing full booking details including:
 * - Customer information
 * - Event details (date, time, guests)
 * - Chef assignment
 * - Customer preferences (chef request + allergens)
 *
 * @see CustomerPreferencesPanel for preferences editing
 */

import React, { useEffect, useRef } from 'react';
import {
  Calendar,
  ChefHat,
  Clock,
  DollarSign,
  Mail,
  MapPin,
  Phone,
  Users,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CustomerPreferencesPanel } from './CustomerPreferencesPanel';

interface BookingDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  booking: {
    booking_id: string;
    customer_name: string;
    customer_email?: string;
    customer_phone?: string;
    event_date: string;
    event_time?: string;
    guest_count?: number;
    adult_count?: number;
    child_count?: number;
    venue_address?: string;
    chef_name?: string;
    chef_id?: string;
    status: string;
    payment_status?: string;
    total_amount?: number;
    deposit_amount?: number;
    balance_due?: number;
    special_requests?: string;
    created_at?: string;
  } | null;
}

export function BookingDetailModal({
  isOpen,
  onClose,
  booking,
}: BookingDetailModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Format currency
  const formatCurrency = (cents: number | undefined) => {
    if (cents === undefined) return '-';
    return `$${(cents / 100).toFixed(2)}`;
  };

  // Format date
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Format time
  const formatTime = (timeString: string | undefined) => {
    if (!timeString) return '-';
    return timeString;
  };

  // Status badge colors
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'cancellation_requested':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentStatusColor = (status: string | undefined) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800';
      case 'unpaid':
        return 'bg-red-100 text-red-800';
      case 'refunded':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isOpen || !booking) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={handleBackdropClick}
      aria-modal="true"
      role="dialog"
    >
      <div
        ref={modalRef}
        className="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white shadow-xl"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Booking Details
            </h2>
            <p className="text-sm text-gray-500">ID: {booking.booking_id}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status Badges */}
          <div className="flex flex-wrap gap-2">
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(
                booking.status
              )}`}
            >
              {booking.status?.replace(/_/g, ' ').toUpperCase()}
            </span>
            {booking.payment_status && (
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getPaymentStatusColor(
                  booking.payment_status
                )}`}
              >
                {booking.payment_status.toUpperCase()}
              </span>
            )}
          </div>

          {/* Customer Info */}
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <Users className="h-4 w-4" />
              Customer Information
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">
                  {booking.customer_name}
                </span>
              </div>
              {booking.customer_email && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Mail className="h-4 w-4" />
                  <span>{booking.customer_email}</span>
                </div>
              )}
              {booking.customer_phone && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="h-4 w-4" />
                  <span>{booking.customer_phone}</span>
                </div>
              )}
            </div>
          </div>

          {/* Event Details */}
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <Calendar className="h-4 w-4" />
              Event Details
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-4 w-4" />
                <span>{formatDate(booking.event_date)}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Clock className="h-4 w-4" />
                <span>{formatTime(booking.event_time)}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Users className="h-4 w-4" />
                <span>
                  {booking.guest_count ??
                    (booking.adult_count || 0) +
                      (booking.child_count || 0)}{' '}
                  guests
                  {booking.adult_count !== undefined && (
                    <span className="text-gray-400 ml-1">
                      ({booking.adult_count} adults, {booking.child_count || 0}{' '}
                      kids)
                    </span>
                  )}
                </span>
              </div>
              {booking.venue_address && (
                <div className="flex items-start gap-2 text-gray-600 sm:col-span-2">
                  <MapPin className="h-4 w-4 mt-0.5" />
                  <span>{booking.venue_address}</span>
                </div>
              )}
            </div>
          </div>

          {/* Chef Assignment */}
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <ChefHat className="h-4 w-4" />
              Chef Assignment
            </h3>
            <div className="flex items-center gap-2 text-gray-600">
              {booking.chef_name ? (
                <>
                  <ChefHat className="h-4 w-4" />
                  <span>{booking.chef_name}</span>
                </>
              ) : (
                <span className="text-gray-400 italic">Not assigned</span>
              )}
            </div>
          </div>

          {/* Payment Summary */}
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
              <DollarSign className="h-4 w-4" />
              Payment Summary
            </h3>
            <div className="grid gap-2 sm:grid-cols-3">
              <div>
                <span className="text-sm text-gray-500">Total</span>
                <p className="font-semibold text-gray-900">
                  {formatCurrency(booking.total_amount)}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Deposit</span>
                <p className="font-semibold text-gray-900">
                  {formatCurrency(booking.deposit_amount)}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Balance Due</span>
                <p className="font-semibold text-gray-900">
                  {formatCurrency(booking.balance_due)}
                </p>
              </div>
            </div>
          </div>

          {/* Special Requests */}
          {booking.special_requests && (
            <div className="rounded-lg border bg-gray-50 p-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">
                Special Requests
              </h3>
              <p className="text-gray-600 whitespace-pre-wrap">
                {booking.special_requests}
              </p>
            </div>
          )}

          {/* Customer Preferences Panel */}
          <div className="border-t pt-6">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Customer Preferences
            </h3>
            <CustomerPreferencesPanel bookingId={booking.booking_id} />
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 border-t bg-gray-50 px-6 py-4">
          <div className="flex justify-end">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
