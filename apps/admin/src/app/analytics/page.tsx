'use client';

import { useState, useMemo, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Calendar,
  Target,
  Star,
  MessageSquare,
  QrCode,
  Mail,
  ShoppingCart,
  BarChart3,
  Download,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { StatsCard } from '@/components/ui/stats-card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { mockDataService } from '@/services/mockDataService';
import { logger } from '@/lib/logger';

// Date range options
const DATE_RANGES = {
  '7d': { label: 'Last 7 Days', days: 7 },
  '30d': { label: 'Last 30 Days', days: 30 },
  '90d': { label: 'Last 90 Days', days: 90 },
  'custom': { label: 'Custom Range', days: null },
} as const;

type DateRangeKey = keyof typeof DATE_RANGES;

export default function AnalyticsPage() {
  // State
  const [dateRange, setDateRange] = useState<DateRangeKey>('30d');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);

  // Calculate date filters
  const dateFilters = useMemo(() => {
    if (dateRange === 'custom' && customStartDate && customEndDate) {
      return {
        date_from: customStartDate,
        date_to: customEndDate,
      };
    }

    const days = DATE_RANGES[dateRange].days;
    if (!days) return {};

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    return {
      date_from: startDate.toISOString().split('T')[0],
      date_to: endDate.toISOString().split('T')[0],
    };
  }, [dateRange, customStartDate, customEndDate]);

  // Fetch analytics data from mock service
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await mockDataService.getAnalytics();
        setAnalyticsData(data);
      } catch (err) {
        logger.error(err as Error, { context: 'fetch_analytics' });
        setError('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [dateFilters]);

  // Parse overview data from mock service
  const overview = useMemo(() => {
    if (!analyticsData?.overview) {
      return {
        revenue: 0,
        revenueChange: 5.2, // Mock trend
        bookings: 0,
        bookingsChange: 12.3, // Mock trend
        customers: 0,
        customersChange: 8.7, // Mock trend
        avgOrderValue: 0,
        avgOrderValueChange: 3.5, // Mock trend
        leads: 0,
        leadsChange: 15.8, // Mock trend
        conversionRate: 0,
        conversionRateChange: 2.1, // Mock trend
      };
    }

    const data = analyticsData.overview;
    return {
      revenue: data.totalRevenue,
      revenueChange: 5.2, // Mock trend - in production calculate from historical data
      bookings: data.totalBookings,
      bookingsChange: 12.3,
      customers: data.totalCustomers,
      customersChange: 8.7,
      avgOrderValue: data.avgBookingValue,
      avgOrderValueChange: 3.5,
      leads: data.totalLeads,
      leadsChange: 15.8,
      conversionRate: data.conversionRate,
      conversionRateChange: 2.1,
    };
  }, [analyticsData]);

  // Parse lead analytics from mock service
  const leadAnalytics = useMemo(() => {
    if (!analyticsData?.leadsBySource) {
      return {
        qualified: 0,
        converted: 0,
        lost: 0,
        avgScore: 0,
        topSources: [],
      };
    }

    // Calculate lead stats from bookingsByStatus
    const total = analyticsData.overview?.totalLeads || 0;
    const converted = Math.floor(total * 0.35); // 35% conversion rate
    const qualified = Math.floor(total * 0.55); // 55% qualified
    const lost = total - converted - qualified;

    return {
      qualified,
      converted,
      lost,
      avgScore: 78, // Mock AI score
      topSources: analyticsData.leadsBySource,
    };
  }, [analyticsData]);

  // Parse conversion funnel from mock service
  const funnel = useMemo(() => {
    if (!analyticsData?.overview) {
      return [
        { stage: 'Visitors', count: 0, dropoff: 0 },
        { stage: 'Leads', count: 0, dropoff: 0 },
        { stage: 'Qualified', count: 0, dropoff: 0 },
        { stage: 'Converted', count: 0, dropoff: 0 },
      ];
    }

    // Create realistic funnel data
    const leads = analyticsData.overview.totalLeads;
    const qualified = Math.floor(leads * 0.65); // 65% qualification rate
    const converted = analyticsData.overview.totalBookings;
    const visitors = Math.floor(leads * 3.5); // Assume 3.5 visitors per lead

    return [
      { stage: 'Visitors', count: visitors, dropoff: 0 },
      { stage: 'Leads', count: leads, dropoff: ((visitors - leads) / visitors) * 100 },
      { stage: 'Qualified', count: qualified, dropoff: ((leads - qualified) / leads) * 100 },
      { stage: 'Converted', count: converted, dropoff: ((qualified - converted) / qualified) * 100 },
    ];
  }, [analyticsData]);

  // Parse review analytics from mock service
  const reviews = useMemo(() => {
    if (!analyticsData?.overview) {
      return {
        avgRating: 0,
        totalReviews: 0,
        positive: 0,
        neutral: 0,
        negative: 0,
        escalated: 0,
      };
    }

    // Generate realistic review distribution
    const totalReviews = analyticsData.overview.pendingReviews || 0;
    const positive = Math.floor(totalReviews * 0.75); // 75% positive
    const neutral = Math.floor(totalReviews * 0.15); // 15% neutral
    const negative = totalReviews - positive - neutral; // 10% negative
    const escalated = Math.floor(negative * 0.3); // 30% of negative escalated

    return {
      avgRating: 4.6, // Mock average rating
      totalReviews,
      positive,
      neutral,
      negative,
      escalated,
    };
  }, [analyticsData]);

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  // Export data as CSV
  const handleExport = () => {
    const csvData = [
      ['Metric', 'Value', 'Change'],
      ['Revenue', overview.revenue, formatPercent(overview.revenueChange)],
      ['Bookings', overview.bookings, formatPercent(overview.bookingsChange)],
      ['Customers', overview.customers, formatPercent(overview.customersChange)],
      ['Avg Order Value', overview.avgOrderValue, formatPercent(overview.avgOrderValueChange)],
      ['Leads', overview.leads, formatPercent(overview.leadsChange)],
      ['Conversion Rate', `${overview.conversionRate}%`, formatPercent(overview.conversionRateChange)],
    ];

    const csv = csvData.map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${dateRange}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={BarChart3}
          title="Error Loading Analytics"
          description={error}
          actionLabel="Try Again"
          onAction={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Business Analytics</h1>
          <p className="text-gray-600">Track performance and growth metrics</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Date Range Selector */}
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
        <div className="flex flex-wrap items-center gap-4">
          <span className="text-sm font-medium text-gray-700">Date Range:</span>
          {Object.entries(DATE_RANGES).map(([key, { label }]) => (
            <button
              key={key}
              onClick={() => setDateRange(key as DateRangeKey)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                dateRange === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label}
            </button>
          ))}

          {/* Custom Date Range Inputs */}
          {dateRange === 'custom' && (
            <div className="flex items-center gap-2 ml-4">
              <input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading && <LoadingSpinner message="Loading analytics data..." />}

      {/* Key Metrics */}
      {!loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Revenue */}
            <StatsCard
              title="Total Revenue"
              value={formatCurrency(overview.revenue)}
              subtitle="vs previous period"
              icon={DollarSign}
              color="green"
              trend={{
                value: Math.abs(overview.revenueChange),
                isPositive: overview.revenueChange >= 0,
              }}
            />

            {/* Bookings */}
            <StatsCard
              title="Total Bookings"
              value={overview.bookings.toLocaleString()}
              subtitle="vs previous period"
              icon={Calendar}
              color="blue"
              trend={{
                value: Math.abs(overview.bookingsChange),
                isPositive: overview.bookingsChange >= 0,
              }}
            />

            {/* Customers */}
            <StatsCard
              title="New Customers"
              value={overview.customers.toLocaleString()}
              subtitle="vs previous period"
              icon={Users}
              color="purple"
              trend={{
                value: Math.abs(overview.customersChange),
                isPositive: overview.customersChange >= 0,
              }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Average Order Value */}
            <StatsCard
              title="Avg Order Value"
              value={formatCurrency(overview.avgOrderValue)}
              subtitle="per booking"
              icon={ShoppingCart}
              color="yellow"
              trend={{
                value: Math.abs(overview.avgOrderValueChange),
                isPositive: overview.avgOrderValueChange >= 0,
              }}
            />

            {/* Total Leads */}
            <StatsCard
              title="Total Leads"
              value={overview.leads.toLocaleString()}
              subtitle="vs previous period"
              icon={Target}
              color="red"
              trend={{
                value: Math.abs(overview.leadsChange),
                isPositive: overview.leadsChange >= 0,
              }}
            />

            {/* Conversion Rate */}
            <StatsCard
              title="Conversion Rate"
              value={`${overview.conversionRate.toFixed(1)}%`}
              subtitle="lead to booking"
              icon={TrendingUp}
              color="green"
              trend={{
                value: Math.abs(overview.conversionRateChange),
                isPositive: overview.conversionRateChange >= 0,
              }}
            />
          </div>

          {/* Revenue Trend Chart */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-green-50 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Revenue Trend</h2>
                  <p className="text-sm text-gray-600">Last 6 months performance</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  {formatCurrency(overview.revenue)}
                </div>
                <div className="text-sm text-gray-600">Last 30 days</div>
              </div>
            </div>

            {/* Simple bar chart */}
            {analyticsData?.revenueByMonth && (
              <div className="space-y-4">
                {analyticsData.revenueByMonth.map((month: any, index: number) => {
                  const maxRevenue = Math.max(...analyticsData.revenueByMonth.map((m: any) => m.revenue));
                  const width = maxRevenue > 0 ? (month.revenue / maxRevenue) * 100 : 0;
                  
                  return (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 w-24">{month.month}</span>
                        <span className="text-sm text-gray-900 font-semibold">
                          {formatCurrency(month.revenue)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-6">
                        <div
                          className="bg-gradient-to-r from-green-600 to-green-400 h-6 rounded-full transition-all duration-500"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Lead Analytics */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-red-50 rounded-lg">
                  <Target className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Lead Performance</h2>
                  <p className="text-sm text-gray-600">Track lead quality and sources</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="text-sm font-medium text-yellow-800 mb-1">Qualified Leads</div>
                <div className="text-2xl font-bold text-yellow-900">{leadAnalytics.qualified}</div>
              </div>

              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="text-sm font-medium text-green-800 mb-1">Converted</div>
                <div className="text-2xl font-bold text-green-900">{leadAnalytics.converted}</div>
              </div>

              <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="text-sm font-medium text-red-800 mb-1">Lost</div>
                <div className="text-2xl font-bold text-red-900">{leadAnalytics.lost}</div>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-sm font-medium text-blue-800 mb-1">Avg AI Score</div>
                <div className="text-2xl font-bold text-blue-900">{leadAnalytics.avgScore.toFixed(0)}</div>
              </div>
            </div>

            {/* Top Lead Sources */}
            {leadAnalytics.topSources.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Top Lead Sources</h3>
                <div className="space-y-2">
                  {leadAnalytics.topSources.map((source: any, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <span className="text-sm font-medium text-gray-700">{source.source || 'Unknown'}</span>
                      <span className="text-sm text-gray-900 font-semibold">{source.count} leads</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Bookings by Status */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-blue-50 rounded-lg">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Bookings by Status</h2>
                <p className="text-sm text-gray-600">Distribution across all statuses</p>
              </div>
            </div>

            {analyticsData?.bookingsByStatus && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {analyticsData.bookingsByStatus.map((status: any, index: number) => {
                  const colors = [
                    { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-900' },
                    { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-900' },
                    { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-900' },
                    { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-900' },
                  ];
                  const color = colors[index % colors.length];
                  
                  return (
                    <div key={index} className={`p-4 ${color.bg} rounded-lg border ${color.border}`}>
                      <div className={`text-sm font-medium ${color.text} mb-1`}>{status.status}</div>
                      <div className={`text-2xl font-bold ${color.text}`}>{status.count}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Conversion Funnel */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-blue-50 rounded-lg">
                <TrendingDown className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Conversion Funnel</h2>
                <p className="text-sm text-gray-600">Track visitor journey to booking</p>
              </div>
            </div>

            <div className="space-y-4">
              {funnel.map((stage, index) => {
                const maxCount = funnel[0].count || 1;
                const width = (stage.count / maxCount) * 100;

                return (
                  <div key={stage.stage}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">{stage.stage}</span>
                      <span className="text-sm text-gray-900 font-semibold">
                        {stage.count.toLocaleString()}
                        {index > 0 && stage.dropoff > 0 && (
                          <span className="text-xs text-red-600 ml-2">
                            -{stage.dropoff.toFixed(0)}%
                          </span>
                        )}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-8">
                      <div
                        className="bg-gradient-to-r from-blue-600 to-blue-400 h-8 rounded-full flex items-center justify-center transition-all duration-500"
                        style={{ width: `${width}%` }}
                      >
                        {width > 20 && (
                          <span className="text-xs font-medium text-white">
                            {((stage.count / maxCount) * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Review Analytics */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-yellow-50 rounded-lg">
                  <Star className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Customer Reviews</h2>
                  <p className="text-sm text-gray-600">Monitor satisfaction and feedback</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="text-center p-6 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg">
                <div className="text-4xl font-bold text-yellow-900 mb-2">
                  {reviews.avgRating.toFixed(1)}
                </div>
                <div className="flex items-center justify-center mb-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-5 h-5 ${
                        i < Math.floor(reviews.avgRating)
                          ? 'text-yellow-500 fill-yellow-500'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <div className="text-sm text-gray-600">Average Rating</div>
              </div>

              <div className="p-6 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {reviews.totalReviews.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Reviews</div>
              </div>

              <div className="p-6 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-red-600 mb-2">{reviews.escalated}</div>
                <div className="text-sm text-gray-600">Escalated Issues</div>
              </div>
            </div>

            {/* Sentiment Breakdown */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Positive</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{reviews.positive}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Neutral</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{reviews.neutral}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Negative</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">{reviews.negative}</span>
              </div>
            </div>
          </div>

          {/* Top Customers */}
          {analyticsData?.topRevenueCustomers && analyticsData.topRevenueCustomers.length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-purple-50 rounded-lg">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Top Customers</h2>
                  <p className="text-sm text-gray-600">Highest revenue contributors</p>
                </div>
              </div>

              <div className="space-y-3">
                {analyticsData.topRevenueCustomers.map((customer: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-lg font-bold text-purple-700">
                          {index + 1}
                        </span>
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-gray-900">{customer.name}</div>
                        <div className="text-xs text-gray-500">{customer.email}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">
                        {formatCurrency(customer.totalSpent)}
                      </div>
                      <div className="text-xs text-gray-500">Total Spent</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Newsletter */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-50 rounded-lg">
                  <Mail className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900">Newsletter</h3>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-gray-900">-</div>
                <div className="text-sm text-gray-600">Coming Soon</div>
              </div>
            </div>

            {/* QR Codes */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <QrCode className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900">QR Scans</h3>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-gray-900">-</div>
                <div className="text-sm text-gray-600">Coming Soon</div>
              </div>
            </div>

            {/* Social Media */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-pink-50 rounded-lg">
                  <MessageSquare className="w-5 h-5 text-pink-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900">Social Engagement</h3>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-gray-900">-</div>
                <div className="text-sm text-gray-600">Coming Soon</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
