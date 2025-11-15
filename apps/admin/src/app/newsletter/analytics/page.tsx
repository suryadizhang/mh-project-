'use client';

import {
  DollarSign,
  Mail,
  MessageSquare,
  Send,
  ShieldCheck,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useEffect,useState } from 'react';

import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { StatsCard } from '@/components/ui/stats-card';

interface AnalyticsData {
  overview: {
    total_subscribers: number;
    active_subscribers: number;
    sms_consented: number;
    total_campaigns: number;
    campaigns_sent: number;
    total_sms_sent: number;
    total_sms_delivered: number;
    total_sms_failed: number;
    avg_delivery_rate: number;
    total_cost_dollars: number;
    avg_cost_per_campaign: number;
    tcpa_compliance_rate: number;
  };
  subscriber_growth: Array<{
    date: string;
    total: number;
    new: number;
    unsubscribed: number;
    sms_consented: number;
  }>;
  campaign_performance: Array<{
    id: number;
    name: string;
    sent_at: string;
    recipients: number;
    delivery_rate: number;
    failed_count: number;
    cost_dollars: number;
    channel: string;
  }>;
  delivery_trends: {
    dates: string[];
    sent: number[];
    delivered: number[];
    failed: number[];
  };
  cost_analysis: {
    daily_costs: Array<{
      date: string;
      cost: number;
      sms_count: number;
    }>;
    total_monthly_cost: number;
  };
}

export default function NewsletterAnalyticsPage() {
    const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30d');

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/newsletter/analytics?period=${timeRange}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      setAnalytics(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Failed to load analytics. Please try again.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            SMS Campaign Analytics
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Track your SMS campaign performance, delivery rates, and TCPA compliance
          </p>
        </div>
        <select
          value={timeRange}
          onChange={e => setTimeRange(e.target.value)}
          className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="1y">Last year</option>
        </select>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Subscribers"
          value={analytics.overview.total_subscribers}
          icon={Users}
          trend={{
            value: 12.5,
            isPositive: true,
          }}
        />
        <StatsCard
          title="SMS Consented"
          value={analytics.overview.sms_consented}
          icon={MessageSquare}
          subtitle={`${((analytics.overview.sms_consented / analytics.overview.total_subscribers) * 100).toFixed(1)}% consent rate`}
        />
        <StatsCard
          title="SMS Delivered"
          value={analytics.overview.total_sms_delivered}
          icon={Send}
          subtitle={`${analytics.overview.avg_delivery_rate.toFixed(1)}% delivery rate`}
        />
        <StatsCard
          title="Total Cost"
          value={`$${analytics.overview.total_cost_dollars.toFixed(2)}`}
          icon={DollarSign}
          subtitle={`$${analytics.overview.avg_cost_per_campaign.toFixed(2)}/campaign avg`}
        />
        <StatsCard
          title="Campaigns Sent"
          value={analytics.overview.campaigns_sent}
          icon={Mail}
        />
        <StatsCard
          title="SMS Sent"
          value={analytics.overview.total_sms_sent}
          icon={MessageSquare}
        />
        <StatsCard
          title="SMS Failed"
          value={analytics.overview.total_sms_failed}
          icon={TrendingUp}
          subtitle={`${((analytics.overview.total_sms_failed / analytics.overview.total_sms_sent) * 100).toFixed(1)}% failure rate`}
        />
        <StatsCard
          title="TCPA Compliance"
          value={`${analytics.overview.tcpa_compliance_rate.toFixed(1)}%`}
          icon={ShieldCheck}
          trend={{
            value: analytics.overview.tcpa_compliance_rate,
            isPositive: analytics.overview.tcpa_compliance_rate >= 99,
          }}
        />
      </div>

      {/* Subscriber Growth Chart */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Subscriber Growth & SMS Consent
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    New
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unsubscribed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SMS Consented
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Net Growth
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.subscriber_growth.map((row, index) => {
                  const netGrowth = row.new - row.unsubscribed;
                  return (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(row.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {row.total.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                        +{row.new}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                        -{row.unsubscribed}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                        {row.sms_consented.toLocaleString()} ({((row.sms_consented / row.total) * 100).toFixed(1)}%)
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={
                            netGrowth >= 0 ? 'text-green-600' : 'text-red-600'
                          }
                        >
                          {netGrowth >= 0 ? '+' : ''}
                          {netGrowth}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Campaign Performance */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Recent Campaign Performance
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sent Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Delivery Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Failed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.campaign_performance.map(campaign => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {campaign.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        campaign.channel === 'SMS' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {campaign.channel}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(campaign.sent_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.recipients.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">
                          {campaign.delivery_rate.toFixed(1)}%
                        </span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              campaign.delivery_rate >= 95 ? 'bg-green-600' : 
                              campaign.delivery_rate >= 90 ? 'bg-yellow-600' : 'bg-red-600'
                            }`}
                            style={{
                              width: `${Math.min(campaign.delivery_rate, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {campaign.failed_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${campaign.cost_dollars.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Delivery Trends */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            SMS Delivery Trends
          </h2>
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  SMS Sent
                </span>
                <Send className="w-5 h-5 text-blue-600" />
              </div>
              <div className="grid grid-cols-7 gap-2">
                {analytics.delivery_trends.sent.map((value, index) => {
                  const maxValue = Math.max(
                    ...analytics.delivery_trends.sent
                  );
                  const heightPercent =
                    maxValue > 0 ? (value / maxValue) * 100 : 0;
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 rounded-t h-32 flex items-end">
                        <div
                          className="w-full bg-blue-600 rounded-t"
                          style={{ height: `${heightPercent}%` }}
                          title={`${value} sent`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {new Date(
                          analytics.delivery_trends.dates[index]
                        ).toLocaleDateString('en-US', { weekday: 'short' })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  SMS Delivered
                </span>
                <MessageSquare className="w-5 h-5 text-green-600" />
              </div>
              <div className="grid grid-cols-7 gap-2">
                {analytics.delivery_trends.delivered.map((value, index) => {
                  const maxValue = Math.max(
                    ...analytics.delivery_trends.delivered
                  );
                  const heightPercent =
                    maxValue > 0 ? (value / maxValue) * 100 : 0;
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 rounded-t h-32 flex items-end">
                        <div
                          className="w-full bg-green-600 rounded-t"
                          style={{ height: `${heightPercent}%` }}
                          title={`${value} delivered`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {new Date(
                          analytics.delivery_trends.dates[index]
                        ).toLocaleDateString('en-US', { weekday: 'short' })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  SMS Failed
                </span>
                <TrendingUp className="w-5 h-5 text-red-600" />
              </div>
              <div className="grid grid-cols-7 gap-2">
                {analytics.delivery_trends.failed.map((value, index) => {
                  const maxValue = Math.max(
                    ...analytics.delivery_trends.failed
                  );
                  const heightPercent =
                    maxValue > 0 ? (value / maxValue) * 100 : 0;
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 rounded-t h-32 flex items-end">
                        <div
                          className="w-full bg-red-600 rounded-t"
                          style={{ height: `${heightPercent}%` }}
                          title={`${value} failed`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {new Date(
                          analytics.delivery_trends.dates[index]
                        ).toLocaleDateString('en-US', { weekday: 'short' })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Analysis */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Cost Analysis
          </h2>
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                Total Monthly Cost
              </span>
              <span className="text-2xl font-bold text-gray-900">
                ${analytics.cost_analysis.total_monthly_cost.toFixed(2)}
              </span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SMS Count
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Daily Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Cost/SMS
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.cost_analysis.daily_costs.map((row, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(row.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.sms_count.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${row.cost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${(row.cost / row.sms_count).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
