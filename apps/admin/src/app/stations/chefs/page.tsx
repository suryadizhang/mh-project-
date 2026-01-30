'use client';

/**
 * Station Chef Roster Page
 * ========================
 *
 * ROLES: SUPER_ADMIN, ADMIN, STATION_MANAGER
 * PURPOSE: Manage chefs assigned to stations
 *
 * Features (Batch 1):
 * - View chefs for station(s)
 * - Assign/unassign chefs to stations
 * - View chef availability overview
 * - Manage chef pay rates
 *
 * Access Rules:
 * - SUPER_ADMIN: All stations, all chefs
 * - ADMIN: Assigned stations only
 * - STATION_MANAGER: Own station only
 *
 * Related:
 * - Backend: /api/v1/stations/{id}/chefs
 * - Chef Assignments: /stations/assignments
 * - Chef Earnings: /chef-earnings
 */

import {
  Building2,
  ChefHat,
  Filter,
  Loader2,
  Plus,
  Search,
  Star,
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

interface StationChef {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  pay_rate_class: 'new_chef' | 'chef' | 'senior_chef' | 'station_manager';
  is_active: boolean;
  station_id: string;
  station_name: string;
  total_events?: number;
  avg_rating?: number;
}

interface Station {
  id: string;
  name: string;
  location: string;
}

const PAY_RATE_BADGES: Record<string, { label: string; color: string }> = {
  new_chef: { label: 'Junior', color: 'bg-blue-100 text-blue-800' },
  chef: { label: 'Chef', color: 'bg-green-100 text-green-800' },
  senior_chef: { label: 'Senior', color: 'bg-purple-100 text-purple-800' },
  station_manager: { label: 'Manager', color: 'bg-orange-100 text-orange-800' },
};

export default function StationChefsPage() {
  const { stationContext } = useAuth();
  const [chefs, setChefs] = useState<StationChef[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStation, setSelectedStation] = useState<string>('all');

  const isSuperAdmin = stationContext?.is_super_admin;
  const userStationIds = stationContext?.station_id
    ? [stationContext.station_id]
    : [];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();

        // Fetch stations user has access to
        const stationsRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/stations`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (stationsRes.ok) {
          const stationsData = await stationsRes.json();
          setStations(stationsData.data || stationsData || []);
        }

        // Fetch chefs (uses chef-portal station endpoint)
        const chefsRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chef-portal/station/chefs`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (chefsRes.ok) {
          const chefsData = await chefsRes.json();
          setChefs(chefsData.items || chefsData || []);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter chefs based on station access
  const filteredChefs = chefs.filter(chef => {
    // Search filter
    const matchesSearch =
      searchQuery === '' ||
      `${chef.first_name} ${chef.last_name}`
        .toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      chef.email?.toLowerCase().includes(searchQuery.toLowerCase());

    // Station filter
    const matchesStation =
      selectedStation === 'all' || chef.station_id === selectedStation;

    // Role-based access filter
    const hasAccess = isSuperAdmin || userStationIds.includes(chef.station_id);

    return matchesSearch && matchesStation && hasAccess;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading chef roster...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-7 h-7 text-red-600" />
            Chef Roster
          </h1>
          <p className="text-gray-500 mt-1">
            Manage chefs assigned to your station(s)
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Chef to Station
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search chefs..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        {(isSuperAdmin || userStationIds.length > 1) && (
          <Select value={selectedStation} onValueChange={setSelectedStation}>
            <SelectTrigger className="w-[200px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Filter by station" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Stations</SelectItem>
              {stations.map(station => (
                <SelectItem key={station.id} value={station.id}>
                  {station.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <ChefHat className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Chefs</p>
                <p className="text-2xl font-bold">{filteredChefs.length}</p>
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
                <p className="text-sm text-gray-500">Active</p>
                <p className="text-2xl font-bold">
                  {filteredChefs.filter(c => c.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Star className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Senior Chefs</p>
                <p className="text-2xl font-bold">
                  {
                    filteredChefs.filter(
                      c => c.pay_rate_class === 'senior_chef'
                    ).length
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Stations</p>
                <p className="text-2xl font-bold">
                  {isSuperAdmin ? stations.length : userStationIds.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chef List */}
      <Card>
        <CardHeader>
          <CardTitle>Chefs by Station</CardTitle>
          <CardDescription>
            {isSuperAdmin
              ? 'Viewing all chefs across all stations'
              : `Viewing chefs for ${userStationIds.length} station(s)`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredChefs.length === 0 ? (
            <div className="text-center py-12">
              <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No chefs found</p>
              <p className="text-sm text-gray-400 mt-1">
                Add chefs to your station to get started
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredChefs.map(chef => (
                <div
                  key={chef.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                      <ChefHat className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {chef.first_name} {chef.last_name}
                      </p>
                      <p className="text-sm text-gray-500">{chef.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant="outline">
                      {chef.station_name || 'Unassigned'}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        PAY_RATE_BADGES[chef.pay_rate_class]?.color ||
                        'bg-gray-100'
                      }
                    >
                      {PAY_RATE_BADGES[chef.pay_rate_class]?.label ||
                        chef.pay_rate_class}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        chef.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }
                    >
                      {chef.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Button variant="outline" size="sm">
                      Manage
                    </Button>
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
