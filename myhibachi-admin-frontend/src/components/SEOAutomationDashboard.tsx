'use client';

import React, { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { AutomationManager } from '@/lib/advancedAutomation';

interface DashboardStats {
  gmbPosts: number;
  directorySubmissions: number;
  emailSequences: number;
  trackingKeywords: number;
  lastRun?: string;
  automationStatus: string;
}

export default function SEOAutomationDashboard() {
  const [automationManager] = useState(new AutomationManager());
  const [selectedLocation, setSelectedLocation] = useState('San Jose');
  const [stats, setStats] = useState<DashboardStats>({
    gmbPosts: 125,
    directorySubmissions: 12,
    emailSequences: 18,
    trackingKeywords: 216,
    lastRun: new Date().toISOString(),
    automationStatus: 'active',
  });
  const [isRunning, setIsRunning] = useState(false);

  const locations = [
    'San Jose',
    'San Francisco',
    'Palo Alto',
    'Oakland',
    'Mountain View',
    'Santa Clara',
    'Sunnyvale',
    'Sacramento',
    'Fremont',
  ];

  useEffect(() => {
    // Load initial dashboard stats
    const dashboardData = automationManager.getAutomationDashboard();
    setStats({
      gmbPosts: (dashboardData.totalGMBPosts as number) || 125,
      directorySubmissions: 12,
      emailSequences: (dashboardData.emailCampaigns as number) || 18,
      trackingKeywords: (dashboardData.activeKeywords as number) || 216,
      lastRun: (dashboardData.lastRun as string) || new Date().toISOString(),
      automationStatus: (dashboardData.automationStatus as string) || 'active',
    });
  }, [automationManager]);

  const runAutomation = async () => {
    setIsRunning(true);
    try {
      const result = automationManager.runFullAutomation(selectedLocation);
      const updatedData = automationManager.getAutomationDashboard();
      setStats({
        gmbPosts: (updatedData.totalGMBPosts as number) || stats.gmbPosts,
        directorySubmissions: stats.directorySubmissions + 1,
        emailSequences:
          (updatedData.emailCampaigns as number) || stats.emailSequences,
        trackingKeywords:
          (updatedData.activeKeywords as number) || stats.trackingKeywords,
        lastRun: new Date().toISOString(),
        automationStatus: 'active',
      });
      console.log('Automation completed:', result);
    } catch (error) {
      console.error('Automation failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            SEO Automation Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Manage automated SEO and marketing tasks across all locations
          </p>
        </div>
        <Badge
          variant={
            stats.automationStatus === 'active' ? 'default' : 'secondary'
          }
        >
          {stats.automationStatus === 'active' ? '🟢 Active' : '🟡 Paused'}
        </Badge>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GMB Posts</CardTitle>
            <span className="text-2xl">📍</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.gmbPosts}</div>
            <p className="text-xs text-muted-foreground">
              Scheduled this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Directory Submissions
            </CardTitle>
            <span className="text-2xl">🏢</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.directorySubmissions}
            </div>
            <p className="text-xs text-muted-foreground">Active platforms</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Email Campaigns
            </CardTitle>
            <span className="text-2xl">📧</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.emailSequences}</div>
            <p className="text-xs text-muted-foreground">Automated sequences</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tracking Keywords
            </CardTitle>
            <span className="text-2xl">🔍</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.trackingKeywords}</div>
            <p className="text-xs text-muted-foreground">Monitored daily</p>
          </CardContent>
        </Card>
      </div>

      {/* Location Selection & Automation Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Location Management</CardTitle>
            <CardDescription>
              Select a location to run automation tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Location</label>
              <select
                value={selectedLocation}
                onChange={e => setSelectedLocation(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                {locations.map(location => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </div>

            <Button
              onClick={runAutomation}
              disabled={isRunning}
              className="w-full"
            >
              {isRunning ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Running Automation...
                </>
              ) : (
                <>🚀 Run Full Automation for {selectedLocation}</>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Automation Status</CardTitle>
            <CardDescription>System health and recent activity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Last Run:</span>
                <span className="text-sm font-medium">
                  {stats.lastRun
                    ? new Date(stats.lastRun).toLocaleString()
                    : 'Never'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">System Status:</span>
                <Badge
                  variant={
                    stats.automationStatus === 'active'
                      ? 'default'
                      : 'secondary'
                  }
                >
                  {stats.automationStatus}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Active Locations:</span>
                <span className="text-sm font-medium">{locations.length}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Automation Features */}
      <Card>
        <CardHeader>
          <CardTitle>Automation Features</CardTitle>
          <CardDescription>
            Comprehensive SEO and marketing automation capabilities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">📍</span>
                <h3 className="font-semibold">Google My Business</h3>
              </div>
              <p className="text-sm text-gray-600">
                Automated post generation and scheduling for all locations
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Weekly content calendar</li>
                <li>• Event-specific posts</li>
                <li>• Performance tracking</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">🏢</span>
                <h3 className="font-semibold">Directory Management</h3>
              </div>
              <p className="text-sm text-gray-600">
                Automated submissions to 12+ business directories
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Yelp, TripAdvisor, Foursquare</li>
                <li>• Delivery platforms</li>
                <li>• Local directories</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">📧</span>
                <h3 className="font-semibold">Email Marketing</h3>
              </div>
              <p className="text-sm text-gray-600">
                Location-specific email campaigns and sequences
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Welcome sequences</li>
                <li>• Birthday campaigns</li>
                <li>• Holiday promotions</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">⭐</span>
                <h3 className="font-semibold">Review Management</h3>
              </div>
              <p className="text-sm text-gray-600">
                Automated review responses and reputation monitoring
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Smart response templates</li>
                <li>• Sentiment analysis</li>
                <li>• Multi-platform monitoring</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">📱</span>
                <h3 className="font-semibold">Social Media</h3>
              </div>
              <p className="text-sm text-gray-600">
                Content generation for Instagram and Facebook
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Location-specific content</li>
                <li>• Hashtag optimization</li>
                <li>• Scheduled posting</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xl">🔍</span>
                <h3 className="font-semibold">SEO Monitoring</h3>
              </div>
              <p className="text-sm text-gray-600">
                Keyword tracking and position monitoring
              </p>
              <ul className="text-xs text-gray-500 space-y-1">
                <li>• Local keyword tracking</li>
                <li>• Competitor analysis</li>
                <li>• Performance reports</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
