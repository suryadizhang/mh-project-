'use client';

import {
  Eye,
  Mail,
  MousePointerClick,
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
    total_campaigns: number;
    campaigns_sent: number;
    avg_open_rate: number;
    avg_click_rate: number;
  };
  subscriber_growth: Array<{
    date: string;
    total: number;
    new: number;
    unsubscribed: number;
  }>;
  campaign_performance: Array<{
    id: number;
    name: string;
    sent_at: string;
    recipients: number;
    open_rate: number;
    click_rate: number;
  }>;
  engagement_trends: {
    dates: string[];
    opens: number[];
    clicks: number[];
  };
}

export default function NewsletterAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);
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
    } catch (err: any) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
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
            Newsletter Analytics
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Track your email campaign performance
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
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
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
          title="Active Subscribers"
          value={analytics.overview.active_subscribers}
          icon={Mail}
        />
        <StatsCard
          title="Campaigns Sent"
          value={analytics.overview.campaigns_sent}
          icon={TrendingUp}
        />
        <StatsCard
          title="Avg Open Rate"
          value={`${analytics.overview.avg_open_rate.toFixed(1)}%`}
          icon={Eye}
        />
        <StatsCard
          title="Avg Click Rate"
          value={`${analytics.overview.avg_click_rate.toFixed(1)}%`}
          icon={MousePointerClick}
        />
        <StatsCard
          title="Total Campaigns"
          value={analytics.overview.total_campaigns}
          icon={Mail}
        />
      </div>

      {/* Subscriber Growth Chart */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Subscriber Growth
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
                    Sent Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Open Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Click Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.campaign_performance.map(campaign => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {campaign.name}
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
                          {campaign.open_rate.toFixed(1)}%
                        </span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${Math.min(campaign.open_rate, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 mr-2">
                          {campaign.click_rate.toFixed(1)}%
                        </span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{
                              width: `${Math.min(campaign.click_rate, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Engagement Trends */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Engagement Trends
          </h2>
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Email Opens
                </span>
                <Eye className="w-5 h-5 text-blue-600" />
              </div>
              <div className="grid grid-cols-7 gap-2">
                {analytics.engagement_trends.opens.map((value, index) => {
                  const maxValue = Math.max(
                    ...analytics.engagement_trends.opens
                  );
                  const heightPercent =
                    maxValue > 0 ? (value / maxValue) * 100 : 0;
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 rounded-t h-32 flex items-end">
                        <div
                          className="w-full bg-blue-600 rounded-t"
                          style={{ height: `${heightPercent}%` }}
                          title={`${value} opens`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {new Date(
                          analytics.engagement_trends.dates[index]
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
                  Link Clicks
                </span>
                <MousePointerClick className="w-5 h-5 text-green-600" />
              </div>
              <div className="grid grid-cols-7 gap-2">
                {analytics.engagement_trends.clicks.map((value, index) => {
                  const maxValue = Math.max(
                    ...analytics.engagement_trends.clicks
                  );
                  const heightPercent =
                    maxValue > 0 ? (value / maxValue) * 100 : 0;
                  return (
                    <div key={index} className="flex flex-col items-center">
                      <div className="w-full bg-gray-200 rounded-t h-32 flex items-end">
                        <div
                          className="w-full bg-green-600 rounded-t"
                          style={{ height: `${heightPercent}%` }}
                          title={`${value} clicks`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {new Date(
                          analytics.engagement_trends.dates[index]
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
    </div>
  );
}
