'use client';

/**
 * Chef Booking Assignments Page
 * =============================
 *
 * ROLES: SUPER_ADMIN, ADMIN, STATION_MANAGER
 * PURPOSE: Assign chefs to bookings
 *
 * Features (Batch 1 - CRITICAL):
 * - View unassigned bookings for station(s)
 * - Assign chefs to bookings
 * - View chef availability during booking time
 * - Bulk assignment for multiple bookings
 * - Urgent booking alerts (within 7 days)
 *
 * Access Rules:
 * - SUPER_ADMIN: All stations, can override any assignment
 * - ADMIN: Assigned stations only
 * - STATION_MANAGER: Own station only
 *
 * Related:
 * - Backend: /api/v1/bookings/unassigned
 * - Backend: /api/v1/chef-assignments
 * - Chef Roster: /stations/chefs
 * - Booking Calendar: /booking/calendar
 */

import {
  AlertCircle,
  Calendar,
  Check,
  ChefHat,
  Clock,
  Filter,
  Loader2,
  MapPin,
  Search,
  Users,
} from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import { tokenManager } from '@/services/api';

interface UnassignedBooking {
  id: string;
  booking_number: string;
  customer_name: string;
  event_date: string;
  event_time: string;
  venue_address: string;
  guest_count: number;
  station_id: string;
  station_name: string;
  days_until_event: number;
  is_urgent: boolean;
}

interface AvailableChef {
  id: string;
  name: string;
  pay_rate_class: string;
  is_available: boolean;
  distance_miles?: number;
  conflicting_event?: string;
}

export default function ChefAssignmentsPage() {
  const { stationContext } = useAuth();
  const [unassignedBookings, setUnassignedBookings] = useState<
    UnassignedBooking[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterUrgent, setFilterUrgent] = useState<'all' | 'urgent' | 'normal'>(
    'all'
  );
  const [selectedBooking, setSelectedBooking] =
    useState<UnassignedBooking | null>(null);
  const [availableChefs, setAvailableChefs] = useState<AvailableChef[]>([]);
  const [loadingChefs, setLoadingChefs] = useState(false);

  const isSuperAdmin = stationContext?.is_super_admin;
  // StationContext has station_id (singular) - wrap in array for includes() check
  const userStationIds = stationContext?.station_id
    ? [stationContext.station_id]
    : [];

  useEffect(() => {
    const fetchUnassigned = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/bookings/unassigned`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          console.log('Unassigned bookings endpoint not yet implemented');
          setUnassignedBookings([]);
          return;
        }

        const data = await response.json();
        setUnassignedBookings(data.items || []);
      } catch (err) {
        console.error('Error fetching unassigned bookings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUnassigned();
  }, []);

  // Fetch available chefs when a booking is selected
  const handleSelectBooking = async (booking: UnassignedBooking) => {
    setSelectedBooking(booking);
    setLoadingChefs(true);

    try {
      const token = tokenManager.getToken();
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/scheduling/available-chefs?date=${booking.event_date}&time=${booking.event_time}&station_id=${booking.station_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAvailableChefs(data.items || []);
      } else {
        setAvailableChefs([]);
      }
    } catch (err) {
      console.error('Error fetching available chefs:', err);
      setAvailableChefs([]);
    } finally {
      setLoadingChefs(false);
    }
  };

  // Filter bookings
  const filteredBookings = unassignedBookings.filter(booking => {
    const matchesSearch =
      searchQuery === '' ||
      booking.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      booking.booking_number.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesUrgency =
      filterUrgent === 'all' ||
      (filterUrgent === 'urgent' && booking.is_urgent) ||
      (filterUrgent === 'normal' && !booking.is_urgent);

    const hasAccess =
      isSuperAdmin || userStationIds.includes(booking.station_id);

    return matchesSearch && matchesUrgency && hasAccess;
  });

  const urgentCount = filteredBookings.filter(b => b.is_urgent).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading bookings...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ChefHat className="w-7 h-7 text-red-600" />
            Chef Assignments
          </h1>
          <p className="text-gray-500 mt-1">
            Assign chefs to upcoming bookings
          </p>
        </div>
        {urgentCount > 0 && (
          <Badge className="bg-red-100 text-red-800 text-lg px-4 py-2">
            <AlertCircle className="w-5 h-5 mr-2" />
            {urgentCount} Urgent
          </Badge>
        )}
      </div>

      {/* Coming Soon Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="text-amber-800">
            🚧 Batch 1 - CRITICAL for Booking Flow
          </CardTitle>
          <CardDescription className="text-amber-700">
            Chef assignment is required to complete bookings. Backend endpoints
            needed:
            <ul className="mt-2 list-disc list-inside">
              <li>
                <code className="px-2 py-1 bg-amber-100 rounded">
                  /api/v1/bookings/unassigned
                </code>{' '}
                - List bookings needing chef
              </li>
              <li>
                <code className="px-2 py-1 bg-amber-100 rounded">
                  /api/v1/scheduling/available-chefs
                </code>{' '}
                - Check chef availability
              </li>
              <li>
                <code className="px-2 py-1 bg-amber-100 rounded">
                  /api/v1/chef-assignments
                </code>{' '}
                - Create assignments
              </li>
            </ul>
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search bookings..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={filterUrgent}
          onValueChange={(v: 'all' | 'urgent' | 'normal') => setFilterUrgent(v)}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Bookings</SelectItem>
            <SelectItem value="urgent">Urgent Only (&lt;7 days)</SelectItem>
            <SelectItem value="normal">Normal</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Calendar className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Unassigned</p>
                <p className="text-2xl font-bold">{filteredBookings.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Urgent</p>
                <p className="text-2xl font-bold text-red-600">{urgentCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Check className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Assigned Today</p>
                <p className="text-2xl font-bold">0</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unassigned Bookings */}
        <Card>
          <CardHeader>
            <CardTitle>Bookings Needing Chef</CardTitle>
            <CardDescription>
              Click a booking to see available chefs
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredBookings.length === 0 ? (
              <div className="text-center py-12">
                <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <p className="text-gray-500">All bookings are assigned!</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {filteredBookings.map(booking => (
                  <div
                    key={booking.id}
                    onClick={() => handleSelectBooking(booking)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedBooking?.id === booking.id
                        ? 'border-red-500 bg-red-50'
                        : 'hover:bg-gray-50'
                    } ${
                      booking.is_urgent ? 'border-l-4 border-l-red-500' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium">{booking.customer_name}</p>
                      {booking.is_urgent && (
                        <Badge className="bg-red-100 text-red-800">
                          {booking.days_until_event} days
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {booking.event_date}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {booking.event_time}
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {booking.guest_count}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-400 mt-1">
                      <MapPin className="w-4 h-4" />
                      {booking.venue_address?.split(',')[0]}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Available Chefs */}
        <Card>
          <CardHeader>
            <CardTitle>
              {selectedBooking
                ? `Available Chefs for ${selectedBooking.customer_name}`
                : 'Select a Booking'}
            </CardTitle>
            <CardDescription>
              {selectedBooking
                ? `${selectedBooking.event_date} at ${selectedBooking.event_time}`
                : 'Click a booking to see available chefs'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedBooking ? (
              <div className="text-center py-12">
                <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Select a booking first</p>
              </div>
            ) : loadingChefs ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-red-600" />
                <span className="ml-2">Finding available chefs...</span>
              </div>
            ) : availableChefs.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                <p className="text-gray-500">No available chefs found</p>
                <p className="text-sm text-gray-400 mt-1">
                  Try adjusting the booking time or check chef availability
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {availableChefs.map(chef => (
                  <div
                    key={chef.id}
                    className={`p-4 border rounded-lg ${
                      chef.is_available
                        ? 'hover:bg-green-50 cursor-pointer'
                        : 'bg-gray-50 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                          <ChefHat className="w-5 h-5 text-red-600" />
                        </div>
                        <div>
                          <p className="font-medium">{chef.name}</p>
                          <p className="text-sm text-gray-500">
                            {chef.distance_miles &&
                              `${chef.distance_miles} mi away`}
                          </p>
                        </div>
                      </div>
                      <Button size="sm" disabled={!chef.is_available}>
                        {chef.is_available ? 'Assign' : 'Unavailable'}
                      </Button>
                    </div>
                    {chef.conflicting_event && (
                      <p className="text-sm text-red-500 mt-2">
                        ⚠️ Conflict: {chef.conflicting_event}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
