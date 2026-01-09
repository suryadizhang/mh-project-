'use client';

import { format } from 'date-fns';
import { Bot, Building, Calendar, Mail, TrendingUp, Users } from 'lucide-react';
import React, { useEffect, useState } from 'react';

import { AdminChatWidget } from '@/components/AdminChatWidget';
import { StationManager } from '@/components/StationManager';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';
import { type MockBooking, mockDataService } from '@/services/mockDataService';

// Use MockBooking type from service
type Booking = MockBooking;

export default function AdminDashboard() {
  const { stationContext, hasPermission, isSuperAdmin } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'stations' | 'chat'>(
    'dashboard'
  );

  // Permissions
  const canViewBookings =
    hasPermission('view_bookings') || hasPermission('manage_bookings');
  const canManageStations = isSuperAdmin() || hasPermission('manage_stations');
  const canUseChat =
    hasPermission('use_ai_chat') || hasPermission('manage_ai_chat');

  // Load bookings using centralized mock data service
  // FUTURE: Replace mockDataService with real API when database is ready
  useEffect(() => {
    if (!canViewBookings) return;

    const fetchBookings = async () => {
      try {
        // Fetch from centralized mock data service
        const data = await mockDataService.getBookings({
          stationId: stationContext?.station_id?.toString(),
        });

        setBookings(data);
        setLoading(false);
      } catch (error) {
        logger.error(error as Error, { context: 'fetch_bookings' });
        setLoading(false);
      }
    };

    fetchBookings();
  }, [canViewBookings, stationContext]);

  // Calculate stats from real data
  const stats = [
    {
      title: 'Total Bookings',
      value: bookings.length.toString(),
      change: '+12%',
      icon: Calendar,
      color: 'text-blue-600',
    },
    {
      title: 'Confirmed Bookings',
      value: bookings.filter(b => b.status === 'confirmed').length.toString(),
      change: '+8%',
      icon: Users,
      color: 'text-green-600',
    },
    {
      title: 'Pending Approvals',
      value: bookings.filter(b => b.status === 'pending').length.toString(),
      change: `${
        bookings.filter(b => b.status === 'pending').length > 0
          ? 'Action needed'
          : 'All clear'
      }`,
      icon: Mail,
      color: 'text-purple-600',
    },
    {
      title: 'Total Guests',
      value: bookings.reduce((sum, b) => sum + b.guestCount, 0).toString(),
      change: '+23%',
      icon: TrendingUp,
      color: 'text-orange-600',
    },
  ];

  // Filter bookings based on status and date
  const filteredBookings = bookings.filter(booking => {
    if (statusFilter !== 'all' && booking.status !== statusFilter) return false;
    if (dateFilter && booking.eventDate !== dateFilter) return false;
    return true;
  });

  // Export bookings to CSV
  const exportToCSV = () => {
    const csvContent = [
      [
        'ID',
        'Customer Name',
        'Email',
        'Phone',
        'Event Date',
        'Time',
        'Guests',
        'Status',
        'Venue Address',
        'Created At',
      ],
      ...filteredBookings.map(booking => [
        booking.id,
        booking.customerName,
        booking.customerEmail,
        booking.customerPhone,
        booking.eventDate,
        booking.eventTime,
        booking.guestCount.toString(),
        booking.status,
        booking.venueAddress,
        new Date(booking.createdAt).toLocaleString(),
      ]),
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute(
      'download',
      `hibachi-bookings-${format(new Date(), 'yyyy-MM-dd')}.csv`
    );
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Update booking status
  const updateBookingStatus = async (
    bookingId: string,
    newStatus: 'confirmed' | 'cancelled'
  ) => {
    try {
      // Use mock data service to update booking
      const updatedBooking = await mockDataService.updateBookingStatus(
        bookingId,
        newStatus
      );

      if (updatedBooking) {
        // Update local state
        setBookings(prev =>
          prev.map(booking =>
            booking.id === bookingId ? updatedBooking : booking
          )
        );

        // Show success message (you could add a toast notification here)
        logger.info('Booking status updated', {
          booking_id: bookingId,
          new_status: newStatus,
        });
      }
    } catch (error) {
      logger.error(error as Error, {
        context: 'update_booking_status',
        booking_id: bookingId,
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const IconComponent = stat.icon;
          return (
            <div
              key={index}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {stat.title}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                  <p
                    className={`mt-1 text-sm ${
                      stat.change.includes('+')
                        ? 'text-green-600'
                        : stat.change.includes('needed')
                          ? 'text-red-600'
                          : 'text-gray-500'
                    }`}
                  >
                    {stat.change}
                  </p>
                </div>
                <div className={`${stat.color} bg-opacity-10 rounded-lg p-3`}>
                  <IconComponent className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center space-x-2 text-lg font-semibold text-gray-900">
            <span>🔍</span>
            <span>Filter Bookings</span>
          </h2>
          <div className="text-sm text-gray-500">
            {filteredBookings.length} of {bookings.length} bookings shown
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-red-500 focus:ring-2 focus:ring-red-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Event Date
            </label>
            <input
              type="date"
              value={dateFilter}
              onChange={e => setDateFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-red-500 focus:ring-2 focus:ring-red-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setStatusFilter('all');
                setDateFilter('');
              }}
              className="w-full rounded-lg bg-gray-600 px-4 py-2 font-medium text-white transition-colors hover:bg-gray-700"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Recent Bookings */}
      {canViewBookings && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              📋 Booking Management
            </h2>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-red-600"></div>
              <p className="mt-4 text-gray-500">Loading bookings...</p>
            </div>
          ) : filteredBookings.length === 0 ? (
            <div className="p-12 text-center">
              <div className="mb-4 text-6xl">📭</div>
              <p className="text-lg text-gray-500">No bookings found</p>
              <p className="mt-2 text-sm text-gray-400">
                {statusFilter !== 'all' || dateFilter
                  ? 'Try adjusting your filters'
                  : 'Bookings will appear here once customers start booking'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto -mx-4 sm:mx-0">
              <div className="inline-block min-w-full align-middle">
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 hidden sm:table-header-group">
                      <tr>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                          Booking Details
                        </th>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                          Customer
                        </th>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                          Event Info
                        </th>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                          Status
                        </th>
                        <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {filteredBookings.map(booking => (
                        <tr
                          key={booking.id}
                          className="hover:bg-gray-50 flex flex-col sm:table-row border-b-4 sm:border-b-0 border-gray-100"
                        >
                          {/* Mobile Card Layout */}
                          <td
                            className="px-4 sm:px-6 py-4 sm:whitespace-nowrap block sm:table-cell"
                            data-label="Booking Details"
                          >
                            <div className="text-sm">
                              <div className="font-mono text-xs font-medium text-gray-900">
                                {booking.id}
                              </div>
                              <div className="text-gray-500">
                                Created:{' '}
                                {format(
                                  new Date(booking.createdAt),
                                  'MMM dd, yyyy HH:mm'
                                )}
                              </div>
                            </div>
                          </td>
                          <td
                            className="px-4 sm:px-6 py-2 sm:py-4 block sm:table-cell"
                            data-label="Customer"
                          >
                            <div className="text-sm">
                              <div className="font-medium text-gray-900">
                                {booking.customerName}
                              </div>
                              <div className="text-gray-500 text-xs sm:text-sm">
                                {booking.customerEmail}
                              </div>
                              <div className="text-gray-500 text-xs sm:text-sm">
                                {booking.customerPhone}
                              </div>
                            </div>
                          </td>
                          <td
                            className="px-4 sm:px-6 py-2 sm:py-4 block sm:table-cell"
                            data-label="Event Info"
                          >
                            <div className="text-sm">
                              <div className="font-medium text-gray-900">
                                📅{' '}
                                {format(
                                  new Date(booking.eventDate),
                                  'MMM dd, yyyy'
                                )}
                              </div>
                              <div className="text-gray-500">
                                🕐 {booking.eventTime}
                              </div>
                              <div className="text-gray-500">
                                👥 {booking.guestCount} guests
                              </div>
                              <div className="mt-1 text-xs text-gray-400 line-clamp-2">
                                {booking.venueAddress}
                              </div>
                            </div>
                          </td>
                          <td
                            className="px-4 sm:px-6 py-2 sm:py-4 sm:whitespace-nowrap block sm:table-cell"
                            data-label="Status"
                          >
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(
                                booking.status
                              )}`}
                            >
                              {booking.status.charAt(0).toUpperCase() +
                                booking.status.slice(1)}
                            </span>
                          </td>
                          <td
                            className="px-4 sm:px-6 py-2 sm:py-4 text-sm font-medium block sm:table-cell sm:whitespace-nowrap"
                            data-label="Actions"
                          >
                            <div className="flex flex-wrap gap-2 sm:flex-col sm:space-y-1 sm:gap-0">
                              {booking.status === 'pending' && (
                                <>
                                  <button
                                    onClick={() =>
                                      updateBookingStatus(
                                        booking.id,
                                        'confirmed'
                                      )
                                    }
                                    className="flex-1 sm:flex-none sm:block w-auto sm:w-full rounded bg-green-600 px-3 py-1.5 sm:py-1 text-xs text-white transition-colors hover:bg-green-700"
                                  >
                                    ✅ Confirm
                                  </button>
                                  <button
                                    onClick={() =>
                                      updateBookingStatus(
                                        booking.id,
                                        'cancelled'
                                      )
                                    }
                                    className="flex-1 sm:flex-none sm:block w-auto sm:w-full rounded bg-red-600 px-3 py-1.5 sm:py-1 text-xs text-white transition-colors hover:bg-red-700"
                                  >
                                    ❌ Cancel
                                  </button>
                                </>
                              )}
                              {booking.status === 'confirmed' && (
                                <button
                                  onClick={() =>
                                    updateBookingStatus(booking.id, 'cancelled')
                                  }
                                  className="flex-1 sm:flex-none sm:block w-auto sm:w-full rounded bg-red-600 px-3 py-1.5 sm:py-1 text-xs text-white transition-colors hover:bg-red-700"
                                >
                                  ❌ Cancel
                                </button>
                              )}
                              <a
                                href={`mailto:${
                                  booking.customerEmail
                                }?subject=Hibachi Booking ${booking.id}&body=Hello ${
                                  booking.customerName
                                },%0D%0A%0D%0ARegarding your hibachi booking for ${format(
                                  new Date(booking.eventDate),
                                  'MMM dd, yyyy'
                                )} at ${booking.eventTime}...`}
                                className="block w-full rounded bg-blue-600 px-3 py-1 text-center text-xs text-white transition-colors hover:bg-blue-700"
                              >
                                ✉️ Email
                              </a>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            🍤 MyHibachi Admin Dashboard
          </h1>
          <div className="flex items-center space-x-4 text-gray-600">
            <p>
              Station:{' '}
              <strong>
                {stationContext?.station_code ||
                  stationContext?.station_name ||
                  'N/A'}
              </strong>
            </p>
            <p>
              Role:{' '}
              <strong>
                {stationContext?.highest_role || stationContext?.role}
              </strong>
            </p>
            {isSuperAdmin() && (
              <span className="text-red-600 font-semibold">SUPER ADMIN</span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {canViewBookings && (
            <button
              onClick={exportToCSV}
              className="flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
            >
              <span>📊 Export CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'dashboard'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Calendar className="h-4 w-4 inline mr-2" />
            Dashboard
          </button>

          {canManageStations && (
            <button
              onClick={() => setActiveTab('stations')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'stations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Building className="h-4 w-4 inline mr-2" />
              Station Management
            </button>
          )}

          {canUseChat && (
            <button
              onClick={() => setActiveTab('chat')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Bot className="h-4 w-4 inline mr-2" />
              AI Assistant
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'stations' && canManageStations && (
        <StationManager className="min-h-[600px]" />
      )}
      {activeTab === 'chat' && canUseChat && (
        <AdminChatWidget className="max-w-4xl mx-auto" defaultOpen={true} />
      )}
    </div>
  );
}
