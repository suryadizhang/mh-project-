'use client';

import { Mail, Plus, Send, TrendingUp, Users } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import CampaignList from './components/CampaignList';

interface NewsletterStats {
  totalSubscribers: number;
  activeSubscribers: number;
  campaignsSent: number;
  averageOpenRate: number;
  averageClickRate: number;
}

export default function NewsletterPage() {
  const [stats, setStats] = useState<NewsletterStats>({
    totalSubscribers: 0,
    activeSubscribers: 0,
    campaignsSent: 0,
    averageOpenRate: 0,
    averageClickRate: 0,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // TODO: Connect to /api/newsletter/newsletter/stats endpoint
      setStats({
        totalSubscribers: 892,
        activeSubscribers: 856,
        campaignsSent: 24,
        averageOpenRate: 68.5,
        averageClickRate: 24.3,
      });
    } catch (error) {
      console.error('Failed to fetch newsletter stats:', error);
    }
  };

  const handleCreateCampaign = () => {
    // TODO: Open campaign creation dialog
    console.log('Create new campaign');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Newsletter Management
          </h1>
          <p className="mt-1 text-gray-600">
            Manage email campaigns, subscribers, and analytics
          </p>
        </div>
        <Button onClick={handleCreateCampaign}>
          <Plus className="mr-2 h-4 w-4" />
          Create Campaign
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Subscribers
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.totalSubscribers.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.activeSubscribers.toLocaleString()} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Campaigns Sent
            </CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.campaignsSent}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg. Open Rate
            </CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.averageOpenRate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Industry avg: 21.3%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg. Click Rate
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.averageClickRate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Industry avg: 2.6%</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content - Tabs */}
      <Tabs defaultValue="campaigns" className="space-y-4">
        <TabsList>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="subscribers">Subscribers</TabsTrigger>
          <TabsTrigger value="segments">Segments</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="campaigns" className="space-y-4">
          <CampaignList onCreateNew={handleCreateCampaign} />
        </TabsContent>

        <TabsContent value="subscribers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Subscriber List</CardTitle>
              <CardDescription>
                Manage your newsletter subscribers and their preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Subscriber management coming soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Audience Segments</CardTitle>
              <CardDescription>
                Create targeted segments based on subscriber behavior and
                preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Segment management coming soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Email Templates</CardTitle>
              <CardDescription>
                Create and manage reusable email templates for your campaigns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Template editor coming soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
