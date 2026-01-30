'use client';

/**
 * Chef Personal Earnings Page
 * ===========================
 *
 * ROLE: CHEF only
 * PURPOSE: View personal earnings and payment history
 *
 * Features (Batch 1):
 * - View earnings summary
 * - See pending vs paid amounts
 * - Filter by date range
 * - Download earnings statement
 *
 * Different from /chef-earnings (admin view):
 * - This is SELF-SERVICE for chefs
 * - Shows only YOUR earnings
 * - No ability to modify pay rates
 *
 * Related:
 * - Backend: /api/v1/chef-portal/me/earnings (TODO: implement)
 * - Admin Earnings: /chef-earnings
 */

import {
  Calendar,
  ChefHat,
  DollarSign,
  Download,
  Loader2,
  TrendingUp,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { tokenManager } from '@/services/api';

interface EarningRecord {
  id: string;
  event_date: string;
  customer_name: string;
  guest_count: number;
  base_earnings_cents: number;
  travel_earnings_cents: number;
  total_earnings_cents: number;
  status: 'pending' | 'approved' | 'paid';
}

interface EarningsSummary {
  total_earnings_cents: number;
  pending_cents: number;
  paid_cents: number;
  events_count: number;
  avg_per_event_cents: number;
}

export default function ChefEarningsPage() {
  const [earnings, setEarnings] = useState<EarningRecord[]>([]);
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('this_month');

  useEffect(() => {
    const fetchEarnings = async () => {
      try {
        setLoading(true);
        const token = tokenManager.getToken();
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chef-portal/me/earnings?period=${period}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          console.log('Earnings endpoint not yet implemented');
          setEarnings([]);
          setSummary({
            total_earnings_cents: 0,
            pending_cents: 0,
            paid_cents: 0,
            events_count: 0,
            avg_per_event_cents: 0,
          });
          return;
        }

        const data = await response.json();
        setEarnings(data.items || []);
        setSummary(data.summary || null);
      } catch (err) {
        console.error('Error fetching earnings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEarnings();
  }, [period]);

  const formatCents = (cents: number) => `$${(cents / 100).toFixed(2)}`;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
        <span className="ml-2">Loading earnings...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <DollarSign className="w-7 h-7 text-green-600" />
            My Earnings
          </h1>
          <p className="text-gray-500 mt-1">
            Track your earnings and payment history
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="this_month">This Month</SelectItem>
              <SelectItem value="last_month">Last Month</SelectItem>
              <SelectItem value="this_year">This Year</SelectItem>
              <SelectItem value="all_time">All Time</SelectItem>
            </SelectContent>
          </Select>
          <Badge variant="outline" className="text-lg px-4 py-2">
            <ChefHat className="w-5 h-5 mr-2" />
            Chef Portal
          </Badge>
        </div>
      </div>

      {/* Coming Soon Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="text-amber-800">
            🚧 Batch 1 - In Development
          </CardTitle>
          <CardDescription className="text-amber-700">
            Your earnings will appear here once events are completed. Backend
            endpoint:{' '}
            <code className="mx-1 px-2 py-1 bg-amber-100 rounded">
              /api/v1/chefs/me/earnings
            </code>
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Earnings</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCents(summary.total_earnings_cents)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Pending</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {formatCents(summary.pending_cents)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Calendar className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Events</p>
                  <p className="text-2xl font-bold">{summary.events_count}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg per Event</p>
                  <p className="text-2xl font-bold">
                    {formatCents(summary.avg_per_event_cents)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Earnings List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Earnings History</CardTitle>
              <CardDescription>Individual event earnings</CardDescription>
            </div>
            <Button variant="outline" disabled>
              <Download className="w-4 h-4 mr-2" />
              Download Statement
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {earnings.length === 0 ? (
            <div className="text-center py-12">
              <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No earnings records yet</p>
              <p className="text-sm text-gray-400 mt-1">
                Complete events to start earning
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {earnings.map(record => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{record.customer_name}</p>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span>{record.event_date}</span>
                      <span>{record.guest_count} guests</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">
                      {formatCents(record.total_earnings_cents)}
                    </p>
                    <Badge
                      variant="outline"
                      className={
                        record.status === 'paid'
                          ? 'bg-green-100 text-green-800'
                          : record.status === 'approved'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-yellow-100 text-yellow-800'
                      }
                    >
                      {record.status}
                    </Badge>
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
