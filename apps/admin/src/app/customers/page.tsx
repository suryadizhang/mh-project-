'use client';

import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  DollarSign,
  Filter,
  Search,
  Star,
  UserPlus,
  Users,
} from 'lucide-react';
import { useCallback, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/Toast';
import {
  useCustomers,
  useFilters,
  usePagination,
  useSearch,
} from '@/hooks/useApi';
import { api } from '@/lib/api';
import type { CustomerFilters } from '@/types';

export default function CustomersPage() {
  // Hooks
  const toast = useToast();

  // Modal state
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [customerDetail, setCustomerDetail] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Pagination state
  const { page, limit, setPage, nextPage, prevPage } = usePagination(1, 20);

  // Search state
  const {
    query: searchQuery,
    debouncedQuery,
    setQuery: setSearchQuery,
  } = useSearch();

  // Filter state
  const { filters, updateFilter, resetFilters } = useFilters<CustomerFilters>({
    status: '',
  });

  // Combine all filters for API call
  const apiFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedQuery,
      page,
      limit,
      sort_by: 'created_at',
      sort_order: 'desc' as const,
    }),
    [filters, debouncedQuery, page, limit]
  );

  // Fetch customers data
  const {
    data: customersResponse,
    loading,
    error,
    refetch,
  } = useCustomers(apiFilters);

  const customers = customersResponse?.data || [];
  const totalCount = customersResponse?.total_count || 0;
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
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }, []);

  // Get status color
  const getStatusColor = useCallback((status: string) => {
    switch (status?.toLowerCase()) {
      case 'vip':
        return 'bg-purple-100 text-purple-800';
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  }, []);

  // Handle status filter change
  const handleStatusFilter = (status: string) => {
    updateFilter('status', status === 'all' ? '' : status);
    setPage(1); // Reset to first page when filtering
  };

  // Handle search
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(1); // Reset to first page when searching
  };

  // Clear all filters
  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
    setPage(1);
  };

  // View customer detail
  const handleViewCustomer = async (customer: any) => {
    setSelectedCustomer(customer);
    setIsDetailModalOpen(true);
    setLoadingDetail(true);

    try {
      const response = await api.get(
        `/api/v1/bookings/admin/customer/${customer.email}`
      );
      if (response.success) {
        setCustomerDetail(response.data);
        toast.success(
          'Customer Details Loaded',
          `Showing details for ${customer.name}`
        );
      } else {
        throw new Error(response.error || 'Failed to load customer details');
      }
    } catch (error) {
      console.error('Error loading customer detail:', error);
      toast.error(
        'Failed to Load Customer',
        error instanceof Error ? error.message : 'Please try again'
      );
      // Close modal on error
      setIsDetailModalOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Close detail modal
  const handleCloseDetail = () => {
    setIsDetailModalOpen(false);
    setSelectedCustomer(null);
    setCustomerDetail(null);
  };

  // Calculate stats
  const stats = useMemo(() => {
    return {
      total: totalCount,
      active: customers.filter(
        (c: any) => (c.status || 'active').toLowerCase() === 'active'
      ).length,
      vip: customers.filter(
        (c: any) => (c.status || '').toLowerCase() === 'vip'
      ).length,
      avgBookings:
        customers.length > 0
          ? (
              customers.reduce(
                (sum: number, c: any) => sum + (c.total_bookings || 0),
                0
              ) / customers.length
            ).toFixed(1)
          : '0',
    };
  }, [customers, totalCount]);

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="text-red-600 mb-4">
            <Users className="w-12 h-12 mx-auto mb-2" />
            <h3 className="text-lg font-semibold">Error Loading Customers</h3>
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
          <h1 className="text-3xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-600">Manage your customer database</p>
        </div>
        <Button>
          <UserPlus className="w-4 h-4 mr-2" />
          Add Customer
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">1,234</p>
            <p className="text-sm text-gray-600">Total Customers</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-green-600">156</p>
            <p className="text-sm text-gray-600">Active This Month</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-purple-600">42</p>
            <p className="text-sm text-gray-600">VIP Customers</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-blue-600">2.8</p>
            <p className="text-sm text-gray-600">Avg. Bookings</p>
          </div>
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
                placeholder="Search customers..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option>All Status</option>
              <option>Active</option>
              <option>VIP</option>
              <option>Inactive</option>
            </select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
            <p className="text-sm text-gray-600">Total Customers</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-green-600">{stats.active}</p>
            <p className="text-sm text-gray-600">Active This Month</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-purple-600">{stats.vip}</p>
            <p className="text-sm text-gray-600">VIP Customers</p>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="text-center">
            <p className="text-3xl font-bold text-blue-600">
              {stats.avgBookings}
            </p>
            <p className="text-sm text-gray-600">Avg. Bookings</p>
          </div>
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
                placeholder="Search customers..."
                value={searchQuery}
                onChange={e => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filters.status || 'all'}
              onChange={e => handleStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="vip">VIP</option>
              <option value="inactive">Inactive</option>
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
            <p className="text-gray-600">Loading customers...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && customers.length === 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
          <div className="text-center">
            <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No customers found
            </h3>
            <p className="text-gray-600 mb-4">
              {Object.values(filters).some(Boolean) || debouncedQuery
                ? 'Try adjusting your filters or search query'
                : 'Get started by adding your first customer'}
            </p>
            <Button>
              <UserPlus className="w-4 h-4 mr-2" />
              Add Customer
            </Button>
          </div>
        </div>
      )}

      {/* Customers Table */}
      {!loading && customers.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bookings
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Spent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Booking
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customers.map((customer: any) => (
                  <tr key={customer.customer_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {customer.name
                              .split(' ')
                              .map((n: string) => n[0])
                              .join('')}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {customer.name}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>{customer.email}</div>
                        <div>{customer.phone || 'No phone'}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1 text-gray-400" />
                        {customer.total_bookings || 0}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      <div className="flex items-center">
                        <DollarSign className="w-4 h-4 mr-1 text-gray-400" />
                        {customer.total_spent_cents
                          ? formatCurrency(customer.total_spent_cents)
                          : '$0.00'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(customer.last_booking_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(customer.status || 'active')}`}
                      >
                        {customer.status === 'vip' && (
                          <Star className="w-3 h-3 mr-1" />
                        )}
                        {(customer.status || 'Active').charAt(0).toUpperCase() +
                          (customer.status || 'Active').slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleViewCustomer(customer)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View
                        </button>
                        <button
                          onClick={() =>
                            toast.info(
                              'Coming Soon',
                              'Edit customer functionality will be available in the next update'
                            )
                          }
                          className="text-gray-600 hover:text-gray-900"
                        >
                          Edit
                        </button>
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

      {/* Customer Detail Modal */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetail}
        title={
          selectedCustomer
            ? `Customer: ${selectedCustomer.name}`
            : 'Customer Detail'
        }
      >
        {loadingDetail ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading customer details...</p>
          </div>
        ) : customerDetail ? (
          <div className="space-y-6">
            {/* Contact Information */}
            <div>
              <h3 className="text-lg font-semibold mb-3">
                Contact Information
              </h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Email</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {customerDetail.email}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Phone</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {customerDetail.phone || 'N/A'}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Booking Statistics */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Booking Statistics</h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Total Bookings
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {customerDetail.total_bookings || 0}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Total Spent
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {customerDetail.total_spent_cents
                      ? formatCurrency(customerDetail.total_spent_cents)
                      : '$0.00'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Last Booking
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {formatDate(customerDetail.last_booking_date)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(customerDetail.status || 'active')}`}
                    >
                      {(customerDetail.status || 'Active')
                        .charAt(0)
                        .toUpperCase() +
                        (customerDetail.status || 'Active').slice(1)}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No details available
          </div>
        )}
      </Modal>
    </div>
  );
}
