import React, { useCallback, useEffect, useState } from 'react'

import { apiFetch } from '@/lib/api'
import { logger } from '@/lib/logger';
interface CustomerSavings {
  totalSavingsFromZelle: number
  potentialSavingsIfAllZelle: number
  zelleAdoptionRate: number
  recommendedAction: string
  nextBookingPotentialSavings: {
    smallEvent: { amount: number; savings: number }
    mediumEvent: { amount: number; savings: number }
    largeEvent: { amount: number; savings: number }
  }
}

interface CustomerDashboardData {
  customer: {
    id: string
    email: string
    name: string
    phone: string
  }
  analytics: {
    preferredPaymentMethod: string
    totalBookings: number
    totalSpent: number
    zelleUsageCount: number
    totalSavingsFromZelle: number
    customerSince: string
    zelleAdoptionRate: number
  }
  savingsInsights: CustomerSavings
  loyaltyStatus: {
    level: string
    benefits: string[]
    nextTier: string | null
  }
}

interface CustomerSavingsDisplayProps {
  customerEmail?: string
  customerId?: string
}

export default function CustomerSavingsDisplay({
  customerEmail,
  customerId
}: CustomerSavingsDisplayProps) {
  const [dashboardData, setDashboardData] = useState<CustomerDashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCustomerDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (customerId) params.append('customer_id', customerId)
      if (customerEmail) params.append('email', customerEmail)

      const response = await apiFetch<CustomerDashboardData>(
        `/api/v1/customers/dashboard?${params}`,
        {
          cacheStrategy: {
            strategy: 'stale-while-revalidate',
            ttl: 2 * 60 * 1000, // 2 minutes
          },
        }
      )

      if (response.success && response.data) {
        setDashboardData(response.data)
      } else {
        setError(response.error || 'Failed to fetch dashboard data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [customerEmail, customerId])

  useEffect(() => {
    if (customerEmail || customerId) {
      fetchCustomerDashboard()
    }
  }, [customerEmail, customerId, fetchCustomerDashboard])

  const openCustomerPortal = async () => {
    if (!dashboardData?.customer.id) return

    try {
      const response = await apiFetch('/api/v1/customers/dashboard', {
        method: 'POST',
        body: JSON.stringify({
          customerId: dashboardData.customer.id,
          returnUrl: window.location.href
        })
      })

      const data = response.success ? response.data : response;
      if (data && typeof data === 'object' && 'portalUrl' in data && data.portalUrl) {
        window.open(data.portalUrl as string, '_blank');
      }
    } catch (err) {
      logger.error('Error opening customer portal', err as Error)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-600">No customer data available</p>
      </div>
    )
  }

  const { customer, analytics, savingsInsights, loyaltyStatus } = dashboardData

  return (
    <div className="space-y-6">
      {/* Welcome & Loyalty Status */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome back, {customer.name}!</h2>
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            {loyaltyStatus.level} Customer
          </span>
          <span className="text-sm text-gray-600">
            {analytics.totalBookings} bookings • ${analytics.totalSpent.toFixed(2)} spent
          </span>
        </div>
        {loyaltyStatus.nextTier && (
          <p className="text-sm text-gray-600 mt-2">Next tier: {loyaltyStatus.nextTier}</p>
        )}
      </div>

      {/* Savings Summary */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Savings with Zelle</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">
              ${savingsInsights.totalSavingsFromZelle.toFixed(2)}
            </div>
            <div className="text-sm text-green-800">Total Saved with Zelle</div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {savingsInsights.zelleAdoptionRate.toFixed(1)}%
            </div>
            <div className="text-sm text-blue-800">Zelle Usage Rate</div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4">
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
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
          <p className="text-amber-800 font-medium">💡 {savingsInsights.recommendedAction}</p>
        </div>

        {/* Future Savings Projection */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">
            Save on Your Next Event with Zelle
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {Object.entries(savingsInsights.nextBookingPotentialSavings).map(([size, data]) => (
              <div key={size} className="border rounded-lg p-3">
                <div className="text-sm font-medium text-gray-700 capitalize">
                  {size.replace('Event', ' Event')}
                </div>
                <div className="text-lg font-semibold text-gray-900">${data.amount}</div>
                <div className="text-sm text-green-600 font-medium">
                  Save ${data.savings} with Zelle
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Payment History & Analytics */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Account Analytics</h3>
          <button
            onClick={openCustomerPortal}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
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
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Benefits</h3>
        <ul className="space-y-2">
          {loyaltyStatus.benefits.map((benefit, index) => (
            <li key={index} className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              {benefit}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

