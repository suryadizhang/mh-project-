import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MessageCircle,
  Star,
  Settings,
  BarChart3,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { SocialInbox } from './SocialInbox';
import { ReviewsBoard } from './ReviewsBoard';
import { SocialConnections } from './SocialConnections';

interface SocialMetrics {
  total_messages: number;
  unread_messages: number;
  total_reviews: number;
  avg_rating: number;
  response_rate: number;
  avg_response_time_hours: number;
  connected_accounts: number;
  active_threads: number;
}

interface HealthStatus {
  overall: 'healthy' | 'warning' | 'error';
  accounts: Array<{
    platform: string;
    status: 'healthy' | 'warning' | 'error';
    message?: string;
  }>;
  last_check: string;
}

export function SocialMediaDashboard() {
  const [activeTab, setActiveTab] = useState('inbox');
  const [metrics, setMetrics] = useState<SocialMetrics | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    // Set up periodic refresh
    const interval = setInterval(fetchDashboardData, 60000); // Every minute
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [metricsResponse, healthResponse] = await Promise.all([
        fetch('/api/admin/social/analytics?days_back=7'),
        fetch('/api/admin/social/health-check'),
      ]);

      const metricsData = await metricsResponse.json();
      const healthData = await healthResponse.json();

      if (metricsData.success) {
        setMetrics(metricsData.data);
      }

      if (healthData.success) {
        setHealthStatus(healthData.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const MetricCard = ({
    title,
    value,
    icon: Icon,
    trend,
    color = 'text-gray-600',
  }: {
    title: string;
    value: string | number;
    icon: React.ElementType;
    trend?: number;
    color?: string;
  }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">{title}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            {trend !== undefined && (
              <p
                className={`text-sm ${
                  trend > 0
                    ? 'text-green-600'
                    : trend < 0
                      ? 'text-red-600'
                      : 'text-gray-600'
                }`}
              >
                {trend > 0 ? '+' : ''}
                {trend}% this week
              </p>
            )}
          </div>
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Social Media Management</h1>
          <p className="text-gray-600 mt-1">
            Unified inbox for all your social platforms
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {healthStatus && (
            <Badge className={getStatusColor(healthStatus.overall)}>
              {getStatusIcon(healthStatus.overall)}
              <span className="ml-1 capitalize">{healthStatus.overall}</span>
            </Badge>
          )}

          <Button variant="outline" size="sm" onClick={fetchDashboardData}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Unread Messages"
            value={metrics.unread_messages}
            icon={MessageCircle}
            color={
              metrics.unread_messages > 0 ? 'text-red-600' : 'text-green-600'
            }
          />
          <MetricCard
            title="Average Rating"
            value={`${metrics.avg_rating?.toFixed(1)}/5.0`}
            icon={Star}
            color="text-yellow-600"
          />
          <MetricCard
            title="Response Rate"
            value={`${(metrics.response_rate * 100).toFixed(1)}%`}
            icon={CheckCircle}
            color={
              metrics.response_rate > 0.8 ? 'text-green-600' : 'text-yellow-600'
            }
          />
          <MetricCard
            title="Avg Response Time"
            value={`${metrics.avg_response_time_hours?.toFixed(1)}h`}
            icon={Clock}
            color={
              metrics.avg_response_time_hours < 2
                ? 'text-green-600'
                : 'text-yellow-600'
            }
          />
        </div>
      )}

      {/* Platform Status */}
      {healthStatus && healthStatus.accounts.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium mb-3">Platform Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {healthStatus.accounts.map(account => (
                <div
                  key={account.platform}
                  className="flex items-center space-x-2"
                >
                  <Badge className={getStatusColor(account.status)}>
                    {getStatusIcon(account.status)}
                    <span className="ml-1 capitalize">{account.platform}</span>
                  </Badge>
                  {account.message && (
                    <span className="text-xs text-gray-500 truncate">
                      {account.message}
                    </span>
                  )}
                </div>
              ))}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Last checked: {new Date(healthStatus.last_check).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="inbox" className="flex items-center space-x-2">
            <MessageCircle className="h-4 w-4" />
            <span>Inbox</span>
            {metrics && metrics.unread_messages > 0 && (
              <Badge variant="destructive" className="ml-1">
                {metrics.unread_messages}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="reviews" className="flex items-center space-x-2">
            <Star className="h-4 w-4" />
            <span>Reviews</span>
          </TabsTrigger>
          <TabsTrigger
            value="connections"
            className="flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Connections</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inbox" className="mt-6">
          <SocialInbox />
        </TabsContent>

        <TabsContent value="reviews" className="mt-6">
          <ReviewsBoard />
        </TabsContent>

        <TabsContent value="connections" className="mt-6">
          <SocialConnections />
        </TabsContent>
      </Tabs>
    </div>
  );
}
