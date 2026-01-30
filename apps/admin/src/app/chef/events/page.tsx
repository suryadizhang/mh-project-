'use client';

/**
 * Chef Events History Page
 * ========================
 *
 * ROLE: CHEF only
 * PURPOSE: View past event details and history
 *
 * Features (Batch 1):
 * - View completed events
 * - See customer feedback/ratings
 * - Access event photos
 * - View earnings per event
 *
 * Related:
 * - Backend: /api/v1/chef-portal/me/events
 * - Chef Earnings: /chef/earnings
 */

import {
  Calendar,
  ChefHat,
  Clock,
  Loader2,
  MapPin,
  Star,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { tokenManager } from '@/services/api';

interface PastEvent {
  id: string;
  booking_id: string;
  event_date: string;
  customer_name: string;
  venue_address: string;
  guest_count: number;
  earnings_cents: number;
  rating?: number;
  feedback?: string;
}

export default function ChefEventsPage() {
  const [events, setEvents] = useState<PastEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalEvents: 0,
    avgRating: 0,
    totalGuests: 0,
  });

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chef-portal/me/events`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          console.log('Events endpoint not yet implemented');
          setEvents([]);
          return;
        }

        const data = await response.json();
        setEvents(data.items || []);
        setStats({
          totalEvents: data.total || 0,
          avgRating: data.avg_rating || 0,
          totalGuests: data.total_guests || 0,
        });
      } catch (err) {
        console.error('Error fetching events:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading event history...</span>
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
            My Events
          </h1>
          <p className="text-gray-500 mt-1">
            Your completed events and performance history
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
            Event history will be populated once the booking system is
            connected. Backend endpoint:{' '}
            <code className="mx-1 px-2 py-1 bg-amber-100 rounded">
              /api/v1/chef-portal/me/events
            </code>
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Events</p>
                <p className="text-2xl font-bold">{stats.totalEvents}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Star className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Average Rating</p>
                <p className="text-2xl font-bold">
                  {stats.avgRating > 0 ? stats.avgRating.toFixed(1) : 'N/A'}
                </p>
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
                <p className="text-sm text-gray-500">Guests Served</p>
                <p className="text-2xl font-bold">{stats.totalGuests}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Events List */}
      <Card>
        <CardHeader>
          <CardTitle>Event History</CardTitle>
          <CardDescription>Your completed events</CardDescription>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No completed events yet</p>
              <p className="text-sm text-gray-400 mt-1">
                Your event history will appear here after completing assignments
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {events.map(event => (
                <div
                  key={event.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gray-100 rounded-lg">
                      <Calendar className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium">{event.customer_name}</p>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {event.event_date}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {event.guest_count} guests
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {event.venue_address?.split(',')[0]}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">
                      ${(event.earnings_cents / 100).toFixed(2)}
                    </p>
                    {event.rating && (
                      <div className="flex items-center gap-1 text-sm text-yellow-600">
                        <Star className="w-4 h-4 fill-current" />
                        {event.rating.toFixed(1)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
