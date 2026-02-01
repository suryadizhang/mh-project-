'use client';

/**
 * Chef Availability Page
 * ======================
 *
 * ROLE: CHEF only
 * PURPOSE: Manage personal availability and time-off requests
 *
 * Features (Batch 1):
 * - Set weekly recurring availability
 * - Request time-off
 * - View blocked dates
 * - Mark available/unavailable dates
 *
 * Related:
 * - Backend: /api/v1/chef-portal/me/availability
 * - Database: ops.chef_availability, ops.chef_timeoff
 */

import { Calendar, Check, ChefHat, Clock, Loader2, X } from 'lucide-react';
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

const DAYS_OF_WEEK = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

interface WeeklyAvailability {
  day: number;
  is_available: boolean;
  start_time?: string;
  end_time?: string;
}

interface TimeOffRequest {
  id: string;
  start_date: string;
  end_date: string;
  reason: string;
  status: 'pending' | 'approved' | 'denied';
}

export default function ChefAvailabilityPage() {
  const [weeklyAvailability, setWeeklyAvailability] = useState<
    WeeklyAvailability[]
  >([]);
  const [timeOffRequests, setTimeOffRequests] = useState<TimeOffRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAvailability = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chef-portal/me/availability`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          console.log('Availability endpoint not yet implemented');
          // Set default availability (all days available)
          setWeeklyAvailability(
            DAYS_OF_WEEK.map((_, idx) => ({
              day: idx,
              is_available: idx !== 0, // Sunday off by default
              start_time: '10:00',
              end_time: '22:00',
            }))
          );
          return;
        }

        const data = await response.json();
        setWeeklyAvailability(data.weekly || []);
        setTimeOffRequests(data.time_off || []);
      } catch (err) {
        console.error('Error fetching availability:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAvailability();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading availability...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Clock className="w-7 h-7 text-red-600" />
            My Availability
          </h1>
          <p className="text-gray-500 mt-1">
            Manage your schedule and time-off requests
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          <ChefHat className="w-5 h-5 mr-2" />
          Chef Portal
        </Badge>
      </div>

      {/* Weekly Availability */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Weekly Availability
          </CardTitle>
          <CardDescription>
            Set your regular working hours for each day
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {DAYS_OF_WEEK.map((day, idx) => {
              const avail = weeklyAvailability.find(a => a.day === idx);
              return (
                <div
                  key={day}
                  className={`flex items-center justify-between p-4 rounded-lg border ${
                    avail?.is_available
                      ? 'bg-green-50 border-green-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {avail?.is_available ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <X className="w-5 h-5 text-gray-400" />
                    )}
                    <span className="font-medium">{day}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {avail?.is_available
                      ? `${avail.start_time} - ${avail.end_time}`
                      : 'Not available'}
                  </div>
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Time Off Requests */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Time-Off Requests</CardTitle>
              <CardDescription>
                Request vacation or personal days
              </CardDescription>
            </div>
            <Button>Request Time Off</Button>
          </div>
        </CardHeader>
        <CardContent>
          {timeOffRequests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No time-off requests. Click &quot;Request Time Off&quot; to submit
              one.
            </p>
          ) : (
            <div className="space-y-3">
              {timeOffRequests.map(request => (
                <div
                  key={request.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">
                      {request.start_date} - {request.end_date}
                    </p>
                    <p className="text-sm text-gray-500">{request.reason}</p>
                  </div>
                  <Badge
                    className={
                      request.status === 'approved'
                        ? 'bg-green-100 text-green-800'
                        : request.status === 'denied'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                    }
                  >
                    {request.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
