/**
 * React hooks for admin dashboard data fetching
 */

import { useCallback, useEffect, useState } from 'react';
import {
  bookingService,
  customerService,
  dashboardService,
  paymentService,
  invoiceService,
  leadService,
  socialService,
  reviewService,
  analyticsService,
  qrService,
  smsService,
  couponService,
} from '@/services/api';
import { requestDeduplicator } from '@/lib/cache/RequestDeduplicator';
import type {
  Booking,
  BookingFilters,
  Customer,
  CustomerFilters,
  DashboardStats,
  Payment,
  Invoice,
} from '@/types';

interface UseDataState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Generic hook for API data fetching
 */
function useApiData<T>(
  fetchFunction: () => Promise<any>,
  deps: any[] = []
): UseDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Create a cache key from the fetch function and deps
      const cacheKey = JSON.stringify({ fn: fetchFunction.toString(), deps });

      // Use request deduplicator to prevent duplicate simultaneous calls
      const response = await requestDeduplicator.dedupe(cacheKey, fetchFunction);

      if (response.success) {
        setData(response.data || response);
      } else {
        setError(response.error || 'Failed to fetch data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // CRITICAL: Use deps array passed from parent, don't include data/loading/error
  }, deps);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for fetching bookings with filters
 */
export function useBookings(filters: BookingFilters = {}) {
  return useApiData<{ data: Booking[]; total_count: number }>(
    () => bookingService.getBookings(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching a single booking
 */
export function useBooking(bookingId: string | null) {
  return useApiData<Booking>(
    () => bookingId ? bookingService.getBooking(bookingId) : Promise.resolve({ data: null, success: true }),
    [bookingId]
  );
}

/**
 * Hook for fetching customers with filters
 */
export function useCustomers(filters: CustomerFilters = {}) {
  return useApiData<{ data: Customer[]; total_count: number }>(
    () => customerService.getCustomers(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching a single customer
 */
export function useCustomer(customerId: string | null) {
  return useApiData<Customer>(
    () => customerId ? customerService.getCustomer(customerId) : Promise.resolve({ data: null, success: true }),
    [customerId]
  );
}

/**
 * Hook for fetching dashboard stats
 */
export function useDashboardStats() {
  return useApiData<DashboardStats>(
    () => dashboardService.getStats(),
    []
  );
}

/**
 * Hook for fetching payments
 */
export function usePayments(filters: any = {}) {
  return useApiData<Payment[]>(
    () => paymentService.getPayments(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching invoices
 */
export function useInvoices(filters: any = {}) {
  return useApiData<Invoice[]>(
    () => invoiceService.getInvoices(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for managing pagination
 */
export function usePagination(initialPage = 1, initialLimit = 20) {
  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);

  const nextPage = useCallback(() => setPage(p => p + 1), []);
  const prevPage = useCallback(() => setPage(p => Math.max(1, p - 1)), []);
  const goToPage = useCallback((newPage: number) => setPage(Math.max(1, newPage)), []);
  const resetPagination = useCallback(() => setPage(1), []);

  return {
    page,
    limit,
    setPage: goToPage,
    setLimit,
    nextPage,
    prevPage,
    resetPagination,
  };
}

/**
 * Hook for managing filters
 */
export function useFilters<T extends Record<string, any>>(initialFilters: T) {
  const [filters, setFilters] = useState<T>(initialFilters);

  const updateFilter = useCallback((key: keyof T, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateFilters = useCallback((newFilters: Partial<T>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  return {
    filters,
    updateFilter,
    updateFilters,
    resetFilters,
  };
}

/**
 * Hook for search functionality
 */
export function useSearch(initialQuery = '', debounceMs = 500) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  return {
    query,
    debouncedQuery,
    setQuery,
  };
}

/**
 * Hook for sorting functionality
 */
export function useSort<T extends string>(initialSortBy?: T, initialSortOrder: 'asc' | 'desc' = 'asc') {
  const [sortBy, setSortBy] = useState<T | undefined>(initialSortBy);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(initialSortOrder);

  const toggleSort = useCallback((field: T) => {
    if (sortBy === field) {
      setSortOrder(order => order === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  }, [sortBy]);

  return {
    sortBy,
    sortOrder,
    setSortBy,
    setSortOrder,
    toggleSort,
  };
}

/**
 * Hook for fetching leads with filters
 */
export function useLeads(filters: any = {}) {
  return useApiData<{ data: any[]; total_count: number }>(
    () => leadService.getLeads(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching a single lead
 */
export function useLead(leadId: string | null) {
  return useApiData<any>(
    () => leadId ? leadService.getLead(leadId) : Promise.resolve({ data: null, success: true }),
    [leadId]
  );
}

/**
 * Hook for fetching social media threads
 */
export function useSocialThreads(filters: any = {}) {
  return useApiData<{ data: any[]; total_count: number }>(
    () => socialService.getSocialThreads(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching a single social thread
 */
export function useSocialThread(threadId: string | null) {
  return useApiData<any>(
    () => threadId ? socialService.getSocialThread(threadId) : Promise.resolve({ data: null, success: true }),
    [threadId]
  );
}

/**
 * Hook for fetching reviews with filters
 */
export function useReviews(filters: any = {}) {
  return useApiData<{ data: any[]; total_count: number }>(
    () => reviewService.getReviews(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching escalated reviews
 */
export function useEscalatedReviews() {
  return useApiData<{ data: any[] }>(
    () => reviewService.getEscalatedReviews(),
    []
  );
}

/**
 * Hook for fetching review analytics
 */
export function useReviewAnalytics() {
  return useApiData<any>(
    () => reviewService.getReviewAnalytics(),
    []
  );
}

/**
 * Hook for fetching analytics overview
 */
export function useAnalyticsOverview(filters: any = {}) {
  return useApiData<any>(
    () => analyticsService.getOverview(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching lead analytics
 */
export function useLeadAnalytics(filters: any = {}) {
  return useApiData<any>(
    () => analyticsService.getLeadAnalytics(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching conversion funnel
 */
export function useConversionFunnel() {
  return useApiData<any>(
    () => analyticsService.getConversionFunnel(),
    []
  );
}

/**
 * Hook for fetching QR codes
 */
export function useQRCodes(filters: any = {}) {
  return useApiData<{ data: any[] }>(
    () => qrService.listQRCodes(filters),
    [JSON.stringify(filters)]
  );
}

/**
 * Hook for fetching QR analytics
 */
export function useQRAnalytics(code: string | null) {
  return useApiData<any>(
    () => code ? qrService.getQRAnalytics(code) : Promise.resolve({ data: null, success: true }),
    [code]
  );
}