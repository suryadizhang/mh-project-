'use client';

/**
 * Chef Earnings Management Page
 * ==============================
 *
 * Admin UI for managing chef earnings, pay rates, and performance.
 *
 * Features:
 * - View chef earnings list with filters
 * - Calculate earnings for specific bookings
 * - View and update chef pay rate classes
 * - View chef performance scores
 * - Export earnings data
 *
 * Access: Station Manager, Super Admin
 *
 * Related:
 * - Backend: /api/v1/chef-pay/*
 * - Service: services/chef_pay_service.py
 * - Migration: 020_chef_pay_system.sql
 */

import {
  AlertCircle,
  Calculator,
  ChefHat,
  DollarSign,
  Download,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  Star,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

// =============================================================================
// Types
// =============================================================================

interface ChefPayConfig {
  // Per-tier rates (in cents) - loaded from SSoT
  junior_adult_cents: number;
  junior_kid_cents: number;
  junior_toddler_cents: number;
  chef_adult_cents: number;
  chef_kid_cents: number;
  chef_toddler_cents: number;
  senior_adult_cents: number;
  senior_kid_cents: number;
  senior_toddler_cents: number;
  manager_adult_cents: number;
  manager_kid_cents: number;
  manager_toddler_cents: number;
  // Travel
  travel_pct: number;
  source: string;
}

interface EarningsRecord {
  earnings_id: string;
  booking_id: string;
  chef_id: string;
  chef_name: string;
  event_date: string;
  base_earnings_cents: number;
  final_earnings_cents: number;
  pay_rate_class: string;
  status: string;
  created_at: string;
}

interface Chef {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  pay_rate_class: string;
  seniority_level: string;
  total_events?: number;
  avg_score?: number;
}

interface EarningsSummary {
  chef_id: string;
  chef_name: string;
  period_start: string;
  period_end: string;
  total_events: number;
  total_earnings_cents: number;
  pending_cents: number;
  approved_cents: number;
  paid_cents: number;
  average_per_event_cents: number;
}

type StatusFilter = 'all' | 'pending' | 'approved' | 'paid' | 'disputed';
type PayRateClass = 'new_chef' | 'chef' | 'senior_chef' | 'station_manager';

// =============================================================================
// Constants
// =============================================================================

const PAY_RATE_LABELS: Record<PayRateClass, { label: string; color: string }> =
  {
    new_chef: { label: 'Junior Chef', color: 'bg-blue-100 text-blue-800' },
    chef: { label: 'Chef', color: 'bg-green-100 text-green-800' },
    senior_chef: {
      label: 'Senior Chef',
      color: 'bg-purple-100 text-purple-800',
    },
    station_manager: {
      label: 'Station Manager',
      color: 'bg-orange-100 text-orange-800',
    },
  };

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
  approved: { label: 'Approved', color: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Paid', color: 'bg-green-100 text-green-800' },
  disputed: { label: 'Disputed', color: 'bg-red-100 text-red-800' },
};

// =============================================================================
// Helper Functions
// =============================================================================

function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function getPayRateBadge(payRateClass: string) {
  const config = PAY_RATE_LABELS[payRateClass as PayRateClass] || {
    label: payRateClass,
    color: 'bg-gray-100 text-gray-800',
  };
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
}

function getStatusBadge(status: string) {
  const config = STATUS_LABELS[status] || {
    label: status,
    color: 'bg-gray-100 text-gray-800',
  };
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function ChefEarningsPage() {
  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Config state
  const [payConfig, setPayConfig] = useState<ChefPayConfig | null>(null);

  // Earnings list state
  const [earnings, setEarnings] = useState<EarningsRecord[]>([]);
  const [earningsTotal, setEarningsTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Additional filter state
  const [stationFilter, setStationFilter] = useState<string>('all');
  const [monthFilter, setMonthFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>(
    new Date().getFullYear().toString()
  );
  const [stations, setStations] = useState<{ id: string; name: string }[]>([]);

  // Chefs list state
  const [chefs, setChefs] = useState<Chef[]>([]);

  // Selected chef for details
  const [selectedChef, setSelectedChef] = useState<Chef | null>(null);
  const [chefSummary, setChefSummary] = useState<EarningsSummary | null>(null);

  // Dialog state
  const [updatePayRateDialog, setUpdatePayRateDialog] = useState(false);
  const [updatingChef, setUpdatingChef] = useState<Chef | null>(null);
  const [newPayRateClass, setNewPayRateClass] = useState<PayRateClass>('chef');
  const [updateReason, setUpdateReason] = useState('');
  const [updating, setUpdating] = useState(false);

  // Stats
  const [stats, setStats] = useState({
    totalChefs: 0,
    totalEarnings: 0,
    pendingEarnings: 0,
    avgPerEvent: 0,
  });

  // =============================================================================
  // Data Fetching
  // =============================================================================

  const fetchPayConfig = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/chef-pay/config`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pay config');
      }

      const data = await response.json();
      setPayConfig(data);
    } catch (err) {
      console.error('Error fetching pay config:', err);
      setError('Failed to load pay configuration');
    }
  }, [API_BASE_URL]);

  const fetchEarnings = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        limit: '50',
        offset: '0',
      });

      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      if (stationFilter !== 'all') {
        params.append('station_id', stationFilter);
      }

      if (monthFilter !== 'all') {
        params.append('month', monthFilter);
      }

      if (yearFilter !== 'all') {
        params.append('year', yearFilter);
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/chef-pay/earnings?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch earnings');
      }

      const data = await response.json();
      setEarnings(data.items || []);
      setEarningsTotal(data.total || 0);

      // Calculate stats
      const total =
        data.items?.reduce(
          (sum: number, e: EarningsRecord) => sum + e.final_earnings_cents,
          0
        ) || 0;
      const pending =
        data.items
          ?.filter((e: EarningsRecord) => e.status === 'pending')
          .reduce(
            (sum: number, e: EarningsRecord) => sum + e.final_earnings_cents,
            0
          ) || 0;

      setStats(prev => ({
        ...prev,
        totalEarnings: total,
        pendingEarnings: pending,
        avgPerEvent:
          data.items?.length > 0 ? Math.round(total / data.items.length) : 0,
      }));
    } catch (err) {
      console.error('Error fetching earnings:', err);
      setError('Failed to load earnings data');
    }
  }, [API_BASE_URL, statusFilter, stationFilter, monthFilter, yearFilter]);

  // Fetch stations for filter dropdown
  const fetchStations = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/stations`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.warn('Failed to fetch stations for filter');
        return;
      }

      const data = await response.json();
      const stationList = (data.items || data || []).map(
        (s: { id: string; name: string; code?: string }) => ({
          id: s.id,
          name: s.name || s.code || 'Unknown Station',
        })
      );
      setStations(stationList);
    } catch (err) {
      console.warn('Error fetching stations:', err);
    }
  }, [API_BASE_URL]);

  const fetchChefs = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/chefs`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chefs');
      }

      const data = await response.json();
      setChefs(data.items || data || []);
      setStats(prev => ({
        ...prev,
        totalChefs: Array.isArray(data) ? data.length : data.items?.length || 0,
      }));
    } catch (err) {
      console.error('Error fetching chefs:', err);
      // Don't set error - chefs list is secondary
    }
  }, [API_BASE_URL]);

  const fetchChefSummary = useCallback(
    async (chefId: string) => {
      try {
        const token = localStorage.getItem('access_token');
        const today = new Date();
        const thirtyDaysAgo = new Date(
          today.getTime() - 30 * 24 * 60 * 60 * 1000
        );

        const params = new URLSearchParams({
          start_date: thirtyDaysAgo.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0],
        });

        const response = await fetch(
          `${API_BASE_URL}/api/v1/chef-pay/chefs/${chefId}/earnings?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch chef summary');
        }

        const data = await response.json();
        setChefSummary(data);
      } catch (err) {
        console.error('Error fetching chef summary:', err);
      }
    },
    [API_BASE_URL]
  );

  // =============================================================================
  // Actions
  // =============================================================================

  const handleUpdatePayRate = async () => {
    if (!updatingChef) return;

    setUpdating(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chef-pay/chefs/${updatingChef.id}/pay-rate-class`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            pay_rate_class: newPayRateClass,
            reason: updateReason || undefined,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update pay rate class');
      }

      // Refresh data
      await fetchChefs();
      await fetchEarnings();

      setUpdatePayRateDialog(false);
      setUpdatingChef(null);
      setUpdateReason('');
    } catch (err) {
      console.error('Error updating pay rate:', err);
      setError('Failed to update pay rate class');
    } finally {
      setUpdating(false);
    }
  };

  const openUpdatePayRateDialog = (chef: Chef) => {
    setUpdatingChef(chef);
    setNewPayRateClass((chef.pay_rate_class as PayRateClass) || 'chef');
    setUpdatePayRateDialog(true);
  };

  const handleExportCSV = () => {
    const headers = [
      'Chef Name',
      'Event Date',
      'Base Earnings',
      'Final Earnings',
      'Pay Rate',
      'Status',
    ];
    const rows = earnings.map(e => [
      e.chef_name,
      formatDate(e.event_date),
      formatCents(e.base_earnings_cents),
      formatCents(e.final_earnings_cents),
      e.pay_rate_class,
      e.status,
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chef-earnings-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // =============================================================================
  // Effects
  // =============================================================================

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      await Promise.all([
        fetchPayConfig(),
        fetchEarnings(),
        fetchChefs(),
        fetchStations(),
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchPayConfig, fetchEarnings, fetchChefs, fetchStations]);

  useEffect(() => {
    fetchEarnings();
  }, [statusFilter, fetchEarnings]);

  useEffect(() => {
    if (selectedChef) {
      fetchChefSummary(selectedChef.id);
    }
  }, [selectedChef, fetchChefSummary]);

  // =============================================================================
  // Render
  // =============================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2 text-gray-600">Loading chef earnings...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-7 h-7 text-red-600" />
            Chef Earnings Management
          </h1>
          <p className="text-gray-500 mt-1">
            Manage chef pay rates, view earnings, and track performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchEarnings();
              fetchChefs();
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExportCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{error}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
            className="ml-auto"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Chefs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              <ChefHat className="w-6 h-6 text-red-600" />
              {stats.totalChefs}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Earnings (30 days)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCents(stats.totalEarnings)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending Payouts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {formatCents(stats.pendingEarnings)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Avg per Event</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              {formatCents(stats.avgPerEvent)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pay Rate Config Card */}
      {payConfig && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="w-5 h-5" />
              Current Pay Rates (SSoT)
            </CardTitle>
            <CardDescription>
              Pay configuration loaded from {payConfig.source}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 text-sm">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-gray-500">Travel Fee %</div>
                <div className="font-semibold text-lg">
                  {payConfig.travel_pct}%
                </div>
              </div>
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-blue-600">Junior Chef</div>
                <div className="font-semibold text-lg">
                  {formatCents(payConfig.junior_adult_cents)}/
                  {formatCents(payConfig.junior_kid_cents)}
                </div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-green-600">Chef</div>
                <div className="font-semibold text-lg">
                  {formatCents(payConfig.chef_adult_cents)}/
                  {formatCents(payConfig.chef_kid_cents)}
                </div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg">
                <div className="text-purple-600">Senior Chef</div>
                <div className="font-semibold text-lg">
                  {formatCents(payConfig.senior_adult_cents)}/
                  {formatCents(payConfig.senior_kid_cents)}
                </div>
              </div>
              <div className="bg-orange-50 p-3 rounded-lg">
                <div className="text-orange-600">Station Manager</div>
                <div className="font-semibold text-lg">
                  {formatCents(payConfig.manager_adult_cents)}/
                  {formatCents(payConfig.manager_kid_cents)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs for Earnings and Chefs */}
      <Tabs defaultValue="earnings" className="space-y-4">
        <TabsList>
          <TabsTrigger value="earnings" className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Earnings Records
          </TabsTrigger>
          <TabsTrigger value="chefs" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Chef Pay Rates
          </TabsTrigger>
        </TabsList>

        {/* Earnings Tab */}
        <TabsContent value="earnings" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search by chef name..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select
              value={statusFilter}
              onValueChange={(value: StatusFilter) => setStatusFilter(value)}
            >
              <SelectTrigger className="w-[180px]">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="disputed">Disputed</SelectItem>
              </SelectContent>
            </Select>

            {/* Station Filter */}
            <Select
              value={stationFilter}
              onValueChange={(value: string) => setStationFilter(value)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Stations" />
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

            {/* Month Filter */}
            <Select
              value={monthFilter}
              onValueChange={(value: string) => setMonthFilter(value)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="All Months" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Months</SelectItem>
                <SelectItem value="1">January</SelectItem>
                <SelectItem value="2">February</SelectItem>
                <SelectItem value="3">March</SelectItem>
                <SelectItem value="4">April</SelectItem>
                <SelectItem value="5">May</SelectItem>
                <SelectItem value="6">June</SelectItem>
                <SelectItem value="7">July</SelectItem>
                <SelectItem value="8">August</SelectItem>
                <SelectItem value="9">September</SelectItem>
                <SelectItem value="10">October</SelectItem>
                <SelectItem value="11">November</SelectItem>
                <SelectItem value="12">December</SelectItem>
              </SelectContent>
            </Select>

            {/* Year Filter */}
            <Select
              value={yearFilter}
              onValueChange={(value: string) => setYearFilter(value)}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                <SelectItem value="2025">2025</SelectItem>
                <SelectItem value="2024">2024</SelectItem>
                <SelectItem value="2023">2023</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Earnings Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chef</TableHead>
                  <TableHead>Event Date</TableHead>
                  <TableHead className="text-right">Base Earnings</TableHead>
                  <TableHead className="text-right">Final Earnings</TableHead>
                  <TableHead>Pay Rate</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {earnings.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-8 text-gray-500"
                    >
                      No earnings records found
                    </TableCell>
                  </TableRow>
                ) : (
                  earnings
                    .filter(
                      e =>
                        !searchQuery ||
                        e.chef_name
                          .toLowerCase()
                          .includes(searchQuery.toLowerCase())
                    )
                    .map(record => (
                      <TableRow key={record.earnings_id}>
                        <TableCell className="font-medium">
                          {record.chef_name}
                        </TableCell>
                        <TableCell>{formatDate(record.event_date)}</TableCell>
                        <TableCell className="text-right">
                          {formatCents(record.base_earnings_cents)}
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCents(record.final_earnings_cents)}
                        </TableCell>
                        <TableCell>
                          {getPayRateBadge(record.pay_rate_class)}
                        </TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell className="text-gray-500 text-sm">
                          {formatDate(record.created_at)}
                        </TableCell>
                      </TableRow>
                    ))
                )}
              </TableBody>
            </Table>
          </Card>

          {/* Pagination info */}
          <div className="text-sm text-gray-500 text-center">
            Showing {earnings.length} of {earningsTotal} records
          </div>
        </TabsContent>

        {/* Chefs Tab */}
        <TabsContent value="chefs" className="space-y-4">
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chef</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Pay Rate Class</TableHead>
                  <TableHead>Seniority Level</TableHead>
                  <TableHead>Total Events</TableHead>
                  <TableHead>Avg Score</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {chefs.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-8 text-gray-500"
                    >
                      No chefs found
                    </TableCell>
                  </TableRow>
                ) : (
                  chefs.map(chef => (
                    <TableRow
                      key={chef.id}
                      className={
                        selectedChef?.id === chef.id ? 'bg-red-50' : ''
                      }
                    >
                      <TableCell className="font-medium">
                        <button
                          onClick={() => setSelectedChef(chef)}
                          className="text-left hover:text-red-600"
                        >
                          {chef.first_name} {chef.last_name}
                        </button>
                      </TableCell>
                      <TableCell className="text-gray-500">
                        {chef.email}
                      </TableCell>
                      <TableCell>
                        {getPayRateBadge(chef.pay_rate_class)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{chef.seniority_level}</Badge>
                      </TableCell>
                      <TableCell>{chef.total_events || '-'}</TableCell>
                      <TableCell>
                        {chef.avg_score ? (
                          <span className="flex items-center gap-1">
                            <Star className="w-4 h-4 text-yellow-500" />
                            {chef.avg_score.toFixed(1)}
                          </span>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openUpdatePayRateDialog(chef)}
                        >
                          Update Rate
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Chef Summary Sidebar (if selected) */}
      {selectedChef && chefSummary && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChefHat className="w-5 h-5 text-red-600" />
              {selectedChef.first_name} {selectedChef.last_name} - 30 Day
              Summary
            </CardTitle>
            <CardDescription>
              {formatDate(chefSummary.period_start)} to{' '}
              {formatDate(chefSummary.period_end)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-gray-500 text-sm">Total Events</div>
                <div className="text-2xl font-bold">
                  {chefSummary.total_events}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-green-600 text-sm">Total Earnings</div>
                <div className="text-2xl font-bold text-green-700">
                  {formatCents(chefSummary.total_earnings_cents)}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-yellow-600 text-sm">Pending</div>
                <div className="text-2xl font-bold text-yellow-700">
                  {formatCents(chefSummary.pending_cents)}
                </div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-blue-600 text-sm">Avg per Event</div>
                <div className="text-2xl font-bold text-blue-700">
                  {formatCents(chefSummary.average_per_event_cents)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Update Pay Rate Dialog */}
      <Dialog open={updatePayRateDialog} onOpenChange={setUpdatePayRateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Pay Rate Class</DialogTitle>
            <DialogDescription>
              Change the pay rate class for{' '}
              {updatingChef
                ? `${updatingChef.first_name} ${updatingChef.last_name}`
                : 'this chef'}
              . This affects their earnings multiplier.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Current Rate</label>
              <div>
                {updatingChef && getPayRateBadge(updatingChef.pay_rate_class)}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">New Rate</label>
              <Select
                value={newPayRateClass}
                onValueChange={(value: PayRateClass) =>
                  setNewPayRateClass(value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new_chef">
                    Junior Chef ($10/$5 per person)
                  </SelectItem>
                  <SelectItem value="chef">Chef ($12/$6 per person)</SelectItem>
                  <SelectItem value="senior_chef">
                    Senior Chef ($13/$6.50 per person)
                  </SelectItem>
                  <SelectItem value="station_manager">
                    Station Manager ($15/$7.50 per person)
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Reason for Change (optional)
              </label>
              <Input
                value={updateReason}
                onChange={e => setUpdateReason(e.target.value)}
                placeholder="e.g., Promoted after 50 successful events"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setUpdatePayRateDialog(false)}
              disabled={updating}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdatePayRate} disabled={updating}>
              {updating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Update Pay Rate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
