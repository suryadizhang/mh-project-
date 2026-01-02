'use client';

import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  DollarSign,
  Filter,
  Plus,
  Search,
  Users,
  XCircle,
  CheckCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { CancellationRequestModal } from '@/components/booking/CancellationRequestModal';
import { CancellationReviewModal } from '@/components/booking/CancellationReviewModal';
import {
  useBookings,
  useFilters,
  usePagination,
  useSearch,
  useSort,
} from '@/hooks/useApi';
import { bookingService } from '@/services/api';
import type { BookingFilters } from '@/types';

export default function BookingPage() {
  const router = useRouter();

  // Pagination state
  const { page, limit, setPage, nextPage, prevPage } = usePagination(1, 20);

  // Search state
  const {
    query: searchQuery,
    debouncedQuery,
    setQuery: setSearchQuery,
  } = useSearch();

  // Filter state
  const { filters, updateFilter, resetFilters } = useFilters<BookingFilters>({
    status: '',
    payment_status: '',
    date_from: '',
    date_to: '',
  });

  // Cancellation modal state
  const [cancelModalBooking, setCancelModalBooking] = useState<any | null>(
    null
  );
  const [reviewModalBooking, setReviewModalBooking] = useState<any | null>(
    null
  );

  // Sort state - default to upcoming events first
  const { sortBy, sortOrder, toggleSort } = useSort<
    'date' | 'booking_id' | 'total_guests' | 'created_at'
  >('date', 'asc');

  // Combine all filters for API call
  const apiFilters = useMemo(
    () => ({
      ...filters,
      customer_search: debouncedQuery,
      page,
      limit,
      sort_by: sortBy,
      sort_order: sortOrder,
    }),
    [filters, debouncedQuery, page, limit, sortBy, sortOrder]
  );

  // Fetch bookings data
  const {
    data: bookingsResponse,
    loading,
    error,
    refetch,
  } = useBookings(apiFilters);

  const bookings = bookingsResponse?.data || [];
  const totalCount = bookingsResponse?.total_count || 0;
  const totalPages = Math.ceil(totalCount / limit);

  // Format currency
  const formatCurrency = useCallback((cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(cents / 100);
  }, []);

  // Format date
  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }, []);

  // Get status color
  const getStatusColor = useCallback((status: string) => {
    switch (status.toLowerCase()) {
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
  }, []);

  // Get payment status color
  const getPaymentStatusColor = useCallback((status: string) => {
    switch (status.toLowerCase()) {
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
  }, []);

  // Check if booking is upcoming
  const isUpcoming = useCallback((dateString: string) => {
    const bookingDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return bookingDate >= today;
  }, []);

  // Handle status filter change
  const handleStatusFilter = (status: string) => {
    updateFilter('status', status === 'all' ? '' : status);
    setPage(1); // Reset to first page when filtering
  };

  // Handle payment status filter change
  const handlePaymentStatusFilter = (status: string) => {
    updateFilter('payment_status', status === 'all' ? '' : status);
    setPage(1);
  };

  // Handle search
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(1); // Reset to first page when searching
  };

  // Handle sort
  const handleSort = (field: string) => {
    toggleSort(field as any);
    setPage(1); // Reset to first page when sorting
  };

  // Clear all filters
  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
    setPage(1);
  };

  // Handle cancellation request submission
  const handleRequestCancellation = async (reason: string) => {
    if (!cancelModalBooking) return;
    await bookingService.requestCancellation(
      cancelModalBooking.booking_id,
      reason
    );
    setCancelModalBooking(null);
    // Refresh bookings list
    window.location.reload();
  };

  // Handle cancellation approval
  const handleApproveCancellation = async (adminNotes?: string) => {
    if (!reviewModalBooking) return;
    await bookingService.approveCancellation(
      reviewModalBooking.booking_id,
      adminNotes
    );
    setReviewModalBooking(null);
    // Refresh bookings list
    window.location.reload();
  };

  // Handle cancellation rejection
  const handleRejectCancellation = async (adminNotes?: string) => {
    if (!reviewModalBooking) return;
    await bookingService.rejectCancellation(
      reviewModalBooking.booking_id,
      adminNotes
    );
    setReviewModalBooking(null);
    // Refresh bookings list
    window.location.reload();
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="text-red-600 mb-4">
            <Clock className="w-12 h-12 mx-auto mb-2" />
            <h3 className="text-lg font-semibold">Error Loading Bookings</h3>
            <p className="text-sm text-gray-600 mt-1">{error}</p>
          </div>
          <Button onClick={refetch} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Bookings</h1>
          <p className="text-gray-600">Manage all your hibachi bookings</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push('/booking/calendar')}
          >
            <Calendar className="w-4 h-4 mr-2" />
            Calendar View
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Booking
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search bookings..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option>All Status</option>
              <option>Confirmed</option>
              <option>Pending</option>
              <option>Cancellation Requested</option>
              <option>Cancelled</option>
            </select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <Calendar className="w-6 h-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">
                Total Bookings
              </p>
              <p className="text-2xl font-bold text-gray-900">{totalCount}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <Users className="w-6 h-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">
                Upcoming Events
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {bookings.filter((b: any) => isUpcoming(b.date)).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <Clock className="w-6 h-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">
                {bookings.filter((b: any) => b.status === 'pending').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <DollarSign className="w-6 h-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(
                  bookings.reduce(
                    (sum: number, b: any) => sum + b.total_due_cents,
                    0
                  )
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search bookings..."
                value={searchQuery}
                onChange={e => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <select
              value={filters.status || 'all'}
              onChange={e => handleStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <select
              value={filters.payment_status || 'all'}
              onChange={e => handlePaymentStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Payments</option>
              <option value="unpaid">Unpaid</option>
              <option value="partial">Partial</option>
              <option value="paid">Paid</option>
              <option value="refunded">Refunded</option>
            </select>

            <Button variant="outline" onClick={handleClearFilters}>
              <Filter className="w-4 h-4 mr-2" />
              Clear Filters
            </Button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading bookings...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && bookings.length === 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
          <div className="text-center">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No bookings found
            </h3>
            <p className="text-gray-600 mb-4">
              {Object.values(filters).some(Boolean) || debouncedQuery
                ? 'Try adjusting your filters or search query'
                : 'Get started by creating your first booking'}
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Booking
            </Button>
          </div>
        </div>
      )}

      {/* Bookings Table */}
      {!loading && bookings.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('booking_id')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Booking ID</span>
                      {sortBy === 'booking_id' ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('date')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Event Date</span>
                      {sortBy === 'date' ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button
                      onClick={() => handleSort('total_guests')}
                      className="flex items-center space-x-1 hover:text-gray-700"
                    >
                      <span>Guests</span>
                      {sortBy === 'total_guests' ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bookings.map((booking: any) => (
                  <tr
                    key={booking.booking_id}
                    className={`hover:bg-gray-50 ${isUpcoming(booking.date) ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div className="flex items-center">
                        {isUpcoming(booking.date) && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                        )}
                        {booking.booking_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="font-medium">{booking.customer.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>{booking.customer.email}</div>
                        <div>{booking.customer.phone}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div className="font-medium">
                          {formatDate(booking.date)}
                        </div>
                        <div>{booking.slot}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        {booking.total_guests}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div>
                        <div>{formatCurrency(booking.total_due_cents)}</div>
                        {booking.balance_due_cents > 0 && (
                          <div className="text-xs text-red-600">
                            {formatCurrency(booking.balance_due_cents)} due
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(booking.status)}`}
                      >
                        {booking.status === 'cancellation_requested'
                          ? 'Pending Cancellation'
                          : booking.status.charAt(0).toUpperCase() +
                            booking.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPaymentStatusColor(booking.payment_status)}`}
                      >
                        {booking.payment_status.charAt(0).toUpperCase() +
                          booking.payment_status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          View
                        </button>
                        <button className="text-gray-600 hover:text-gray-900">
                          Edit
                        </button>
                        {/* Show Approve/Reject for cancellation_requested status */}
                        {booking.status === 'cancellation_requested' && (
                          <>
                            <button
                              className="text-green-600 hover:text-green-900 flex items-center"
                              onClick={() => setReviewModalBooking(booking)}
                            >
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Review
                            </button>
                          </>
                        )}
                        {/* Show Cancel button for non-cancelled, non-pending-cancellation bookings */}
                        {booking.status !== 'cancelled' &&
                          booking.status !== 'cancellation_requested' && (
                            <button
                              className="text-red-600 hover:text-red-900 flex items-center"
                              onClick={() => setCancelModalBooking(booking)}
                            >
                              <XCircle className="w-3 h-3 mr-1" />
                              Cancel
                            </button>
                          )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <Button variant="outline" onClick={prevPage} disabled={page <= 1}>
                Previous
              </Button>
              <Button
                variant="outline"
                onClick={nextPage}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">{(page - 1) * limit + 1}</span>{' '}
                  to{' '}
                  <span className="font-medium">
                    {Math.min(page * limit, totalCount)}
                  </span>{' '}
                  of <span className="font-medium">{totalCount}</span> results
                </p>
              </div>
              <div>
                <nav
                  className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
                  aria-label="Pagination"
                >
                  <button
                    onClick={prevPage}
                    disabled={page <= 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>

                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const pageNum = Math.max(1, page - 2) + i;
                    if (pageNum > totalPages) return null;

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          page === pageNum
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}

                  <button
                    onClick={nextPage}
                    disabled={page >= totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancellation Request Modal - Step 1 */}
      <CancellationRequestModal
        isOpen={cancelModalBooking !== null}
        onClose={() => setCancelModalBooking(null)}
        onSubmit={handleRequestCancellation}
        bookingName={cancelModalBooking?.customer?.name ?? ''}
      />

      {/* Cancellation Review Modal - Step 2 */}
      <CancellationReviewModal
        isOpen={reviewModalBooking !== null}
        onClose={() => setReviewModalBooking(null)}
        onApprove={handleApproveCancellation}
        onReject={handleRejectCancellation}
        bookingName={reviewModalBooking?.customer?.name ?? ''}
        cancellationReason={reviewModalBooking?.cancellation_reason ?? ''}
        requestedAt={reviewModalBooking?.cancellation_requested_at}
        requestedBy={reviewModalBooking?.cancellation_requested_by?.name}
      />
    </div>
  );
}
