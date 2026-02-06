import React, { useCallback, useEffect, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';
interface CustomerSavings {
  totalSavingsFromZelle: number;
  potentialSavingsIfAllZelle: number;
  zelleAdoptionRate: number;
  recommendedAction: string;
  nextBookingPotentialSavings: {
    smallEvent: { amount: number; savings: number };
    mediumEvent: { amount: number; savings: number };
    largeEvent: { amount: number; savings: number };
  };
}

interface CustomerDashboardData {
  customer: {
    id: string;
    email: string;
    name: string;
    phone: string;
  };
  analytics: {
    preferredPaymentMethod: string;
    totalBookings: number;
    totalSpent: number;
    zelleUsageCount: number;
    totalSavingsFromZelle: number;
    customerSince: string;
    zelleAdoptionRate: number;
  };
  savingsInsights: CustomerSavings;
  loyaltyStatus: {
    level: string;
    benefits: string[];
    nextTier: string | null;
  };
}

interface CustomerSavingsDisplayProps {
  customerEmail?: string;
  customerId?: string;
}

export default function CustomerSavingsDisplay({
  customerEmail,
  customerId,
}: CustomerSavingsDisplayProps) {
  const [dashboardData, setDashboardData] = useState<CustomerDashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCustomerDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (customerId) params.append('customer_id', customerId);
      if (customerEmail) params.append('email', customerEmail);

      const response = await apiFetch<CustomerDashboardData>(
        `/api/v1/customers/dashboard?${params}`,
        {
          cacheStrategy: {
            strategy: 'stale-while-revalidate',
            ttl: 2 * 60 * 1000, // 2 minutes
          },
        },
      );

      if (response.success && response.data) {
        setDashboardData(response.data);
      } else {
        setError(response.error || 'Failed to fetch dashboard data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [customerEmail, customerId]);

  useEffect(() => {
    if (customerEmail || customerId) {
      fetchCustomerDashboard();
    }
  }, [customerEmail, customerId, fetchCustomerDashboard]);

  const openCustomerPortal = async () => {
    if (!dashboardData?.customer.id) return;

    try {
      const response = await apiFetch('/api/v1/customers/dashboard', {
        method: 'POST',
        body: JSON.stringify({
          customerId: dashboardData.customer.id,
          returnUrl: window.location.href,
        }),
      });

      const data = response.success ? response.data : response;
      if (data && typeof data === 'object' && 'portalUrl' in data && data.portalUrl) {
        window.open(data.portalUrl as string, '_blank');
      }
    } catch (err) {
      logger.error('Error opening customer portal', err as Error);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="animate-pulse">
          <div className="mb-4 h-4 w-3/4 rounded bg-gray-200"></div>
          <div className="h-4 w-1/2 rounded bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <p className="text-gray-600">No customer data available</p>
      </div>
    );
  }

  const { customer, analytics, savingsInsights, loyaltyStatus } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Welcome & Loyalty Status */}
      <div className="rounded-lg border bg-gradient-to-r from-green-50 to-blue-50 p-6">
        <h2 className="mb-2 text-xl font-semibold text-gray-900">Welcome back, {customer.name}!</h2>
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
            {loyaltyStatus.level} Customer
          </span>
          <span className="text-sm text-gray-600">
            {analytics.totalBookings} bookings • ${analytics.totalSpent.toFixed(2)} spent
          </span>
        </div>
        {loyaltyStatus.nextTier && (
          <p className="mt-2 text-sm text-gray-600">Next tier: {loyaltyStatus.nextTier}</p>
        )}
      </div>

      {/* Savings Summary */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Your Savings with Zelle</h3>

        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg bg-green-50 p-4">
            <div className="text-2xl font-bold text-green-600">
              ${savingsInsights.totalSavingsFromZelle.toFixed(2)}
            </div>
            <div className="text-sm text-green-800">Total Saved with Zelle</div>
          </div>

          <div className="rounded-lg bg-blue-50 p-4">
            <div className="text-2xl font-bold text-blue-600">
              {savingsInsights.zelleAdoptionRate.toFixed(1)}%
            </div>
            <div className="text-sm text-blue-800">Zelle Usage Rate</div>
          </div>

          <div className="rounded-lg bg-yellow-50 p-4">
            <div className="text-2xl font-bold text-yellow-600">
              $
              {(
                savingsInsights.potentialSavingsIfAllZelle - savingsInsights.totalSavingsFromZelle
              ).toFixed(2)}
            </div>
            <div className="text-sm text-yellow-800">Potential Additional Savings</div>
          </div>
        </div>

        {/* Recommendation */}
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="font-medium text-amber-800">💡 {savingsInsights.recommendedAction}</p>
        </div>

        {/* Future Savings Projection */}
        <div>
          <h4 className="text-md mb-3 font-semibold text-gray-900">
            Save on Your Next Event with Zelle
          </h4>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            {Object.entries(savingsInsights.nextBookingPotentialSavings).map(([size, data]) => (
              <div key={size} className="rounded-lg border p-3">
                <div className="text-sm font-medium text-gray-700 capitalize">
                  {size.replace('Event', ' Event')}
                </div>
                <div className="text-lg font-semibold text-gray-900">${data.amount}</div>
                <div className="text-sm font-medium text-green-600">
                  Save ${data.savings} with Zelle
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Payment History & Analytics */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Account Analytics</h3>
          <button
            onClick={openCustomerPortal}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Manage Payment Methods
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-600">Preferred Payment Method</div>
            <div className="text-lg font-medium text-gray-900 capitalize">
              {analytics.preferredPaymentMethod}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Customer Since</div>
            <div className="text-lg font-medium text-gray-900">
              {new Date(analytics.customerSince).toLocaleDateString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Times Used Zelle</div>
            <div className="text-lg font-medium text-gray-900">
              {analytics.zelleUsageCount} of {analytics.totalBookings}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Spent</div>
            <div className="text-lg font-medium text-gray-900">
              ${analytics.totalSpent.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Benefits */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Your Benefits</h3>
        <ul className="space-y-2">
          {loyaltyStatus.benefits.map((benefit, index) => (
            <li key={index} className="flex items-center text-gray-700">
              <span className="mr-2 text-green-500">✓</span>
              {benefit}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
