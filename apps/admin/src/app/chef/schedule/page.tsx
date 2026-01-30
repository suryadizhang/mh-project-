'use client';

/**
 * Chef Schedule Page
 * ==================
 *
 * ROLE: CHEF only
 * PURPOSE: View assigned events and upcoming schedule
 *
 * Features (Batch 1):
 * - View all assigned bookings
 * - Filter by date range
 * - See event details (customer, venue, menu)
 * - Quick access to prep checklist
 *
 * Related:
 * - Backend: /api/v1/chef-portal/me/schedule
 * - Station Management: /stations/assignments
 */

import { Calendar, ChefHat, Clock, Loader2, MapPin, Users } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { tokenManager } from '@/services/api';

interface ChefAssignment {
  id: string;
  booking_id: string;
  event_date: string;
  event_time: string;
  customer_name: string;
  venue_address: string;
  guest_count: number;
  status: 'upcoming' | 'today' | 'completed';
  menu_summary?: string;
}

export default function ChefSchedulePage() {
  const [assignments, setAssignments] = useState<ChefAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chef-portal/me/schedule`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          // Expected to fail until backend endpoint is created
          console.log('Schedule endpoint not yet implemented');
          setAssignments([]);
          return;
        }

        const data = await response.json();
        setAssignments(data.items || []);
      } catch (err) {
        console.error('Error fetching schedule:', err);
        setError('Schedule endpoint coming soon');
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading your schedule...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Calendar className="w-7 h-7 text-red-600" />
            My Schedule
          </h1>
          <p className="text-gray-500 mt-1">
            Your upcoming events and assignments
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          <ChefHat className="w-5 h-5 mr-2" />
          Chef Portal
        </Badge>
      </div>

      {/* Coming Soon Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="text-amber-800">
            🚧 Batch 1 - In Development
          </CardTitle>
          <CardDescription className="text-amber-700">
            This page is part of the core booking system. Backend endpoint
            <code className="mx-1 px-2 py-1 bg-amber-100 rounded">
              /api/v1/chef-portal/me/schedule
            </code>
            needs to be implemented.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Placeholder Schedule Cards */}
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Today&apos;s Events
              </span>
              <Badge className="bg-green-100 text-green-800">0 events</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-500 text-center py-8">
              No events scheduled for today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Upcoming This Week
              </span>
              <Badge variant="outline">0 events</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-500 text-center py-8">
              No upcoming events this week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">This Month</p>
                <p className="text-2xl font-bold">0 events</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Guests Served</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <MapPin className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Locations Visited</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
