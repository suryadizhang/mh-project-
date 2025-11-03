"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Mail, 
  DollarSign, 
  User, 
  Calendar,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

interface PaymentNotification {
  email_id: string;
  provider: string;
  amount: number;
  status: string;
  subject: string;
  from: string;
  received_at: string;
  sender_name?: string;
  sender_username?: string;
  sender_email?: string;
  sender_phone?: string;
  transaction_id?: string;
  matched_payment_id?: string;
  matched_booking_id?: string;
  confidence_score?: number;
}

interface UnmatchedNotification extends PaymentNotification {
  possible_matches: {
    payment_id: string;
    booking_id: string;
    customer_name: string;
    amount: number;
    created_at: string;
  }[];
}

export default function PaymentEmailMonitoringDashboard() {
  const [recentNotifications, setRecentNotifications] = useState<PaymentNotification[]>([]);
  const [unmatchedNotifications, setUnmatchedNotifications] = useState<UnmatchedNotification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [monitorStatus, setMonitorStatus] = useState<any>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch recent notifications
      const recentRes = await fetch('/api/v1/payments/email-notifications/recent?since_hours=48&limit=20');
      if (!recentRes.ok) throw new Error('Failed to fetch recent notifications');
      const recentData = await recentRes.json();
      setRecentNotifications(recentData);

      // Fetch unmatched notifications
      const unmatchedRes = await fetch('/api/v1/payments/email-notifications/unmatched?since_hours=48');
      if (!unmatchedRes.ok) throw new Error('Failed to fetch unmatched notifications');
      const unmatchedData = await unmatchedRes.json();
      setUnmatchedNotifications(unmatchedData);

      // Fetch monitor status
      const statusRes = await fetch('/api/v1/payments/email-notifications/status');
      if (!statusRes.ok) throw new Error('Failed to fetch monitor status');
      const statusData = await statusRes.json();
      setMonitorStatus(statusData);

      setLastChecked(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualProcess = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/payments/email-notifications/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          since_hours: 24,
          auto_confirm: true,
          mark_as_read: true
        })
      });

      if (!res.ok) throw new Error('Failed to process emails');
      
      const result = await res.json();
      
      // Show result message
      alert(
        `✅ Processing complete!\n\n` +
        `Emails found: ${result.emails_found}\n` +
        `Payments matched: ${result.payments_matched}\n` +
        `Payments confirmed: ${result.payments_confirmed}\n` +
        `Errors: ${result.errors.length}`
      );

      // Refresh data
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualMatch = async (emailId: string, paymentId: string) => {
    if (!confirm('Are you sure you want to match this payment?')) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/payments/email-notifications/manual-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          payment_id: paymentId,
          confirm_payment: true
        })
      });

      if (!res.ok) throw new Error('Failed to match payment');
      
      const result = await res.json();
      alert(`✅ ${result.message}`);

      // Refresh data
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getProviderBadge = (provider: string) => {
    const colors = {
      stripe: 'bg-purple-100 text-purple-800',
      venmo: 'bg-blue-100 text-blue-800',
      zelle: 'bg-green-100 text-green-800',
      bank_of_america: 'bg-red-100 text-red-800'
    };
    return colors[provider as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status: string) => {
    const config = {
      confirmed: { icon: CheckCircle, color: 'bg-green-100 text-green-800' },
      pending: { icon: Clock, color: 'bg-yellow-100 text-yellow-800' },
      failed: { icon: XCircle, color: 'bg-red-100 text-red-800' }
    };
    const { icon: Icon, color } = config[status as keyof typeof config] || config.pending;
    return (
      <Badge className={color}>
        <Icon className="w-3 h-3 mr-1" />
        {status.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Payment Email Monitoring</h1>
          <p className="text-gray-600 mt-1">
            Automatic payment confirmation from email notifications
          </p>
        </div>
        <Button onClick={fetchData} disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Monitor Status */}
      {monitorStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Monitor Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <Badge className={monitorStatus.status === 'connected' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                  {monitorStatus.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-mono text-sm">{monitorStatus.email_address}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Last Checked</p>
                <p className="text-sm">{lastChecked ? lastChecked.toLocaleTimeString() : 'Never'}</p>
              </div>
              <div>
                <Button onClick={handleManualProcess} disabled={isLoading} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Process Now
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Unmatched Notifications */}
      {unmatchedNotifications.length > 0 && (
        <Card className="border-orange-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <AlertCircle className="w-5 h-5" />
              Unmatched Payments ({unmatchedNotifications.length})
            </CardTitle>
            <CardDescription>
              These payment notifications need manual review
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {unmatchedNotifications.map((notification) => (
              <div key={notification.email_id} className="p-4 border border-orange-200 rounded-lg bg-orange-50">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className={getProviderBadge(notification.provider)}>
                        {notification.provider.toUpperCase()}
                      </Badge>
                      <span className="text-2xl font-bold text-green-600">
                        ${notification.amount.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{notification.subject}</p>
                    {notification.sender_name && (
                      <p className="text-sm font-medium mt-1">From: {notification.sender_name}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(notification.received_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {notification.possible_matches && notification.possible_matches.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Possible Matches:</p>
                    {notification.possible_matches.map((match) => (
                      <div key={match.payment_id} className="flex items-center justify-between p-3 bg-white rounded border">
                        <div>
                          <p className="font-medium">{match.customer_name}</p>
                          <p className="text-sm text-gray-600">
                            ${match.amount.toFixed(2)} • Booking #{match.booking_id}
                          </p>
                          <p className="text-xs text-gray-500">
                            Created: {new Date(match.created_at).toLocaleString()}
                          </p>
                        </div>
                        <Button 
                          size="sm" 
                          onClick={() => handleManualMatch(notification.email_id, match.payment_id)}
                          disabled={isLoading}
                        >
                          Match This
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recent Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Recent Payment Notifications (Last 48 Hours)
          </CardTitle>
          <CardDescription>
            All payment emails detected from Stripe, Venmo, Zelle, and Bank of America
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentNotifications.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No payment notifications found in the last 48 hours
            </p>
          ) : (
            <div className="space-y-4">
              {recentNotifications.map((notification) => (
                <div key={notification.email_id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getProviderBadge(notification.provider)}>
                          {notification.provider.toUpperCase()}
                        </Badge>
                        {getStatusBadge(notification.status)}
                        <span className="text-xl font-bold text-green-600">
                          ${notification.amount.toFixed(2)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-1">{notification.subject}</p>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {notification.sender_name && (
                          <div className="flex items-center gap-1">
                            <User className="w-4 h-4 text-gray-400" />
                            <span>{notification.sender_name}</span>
                          </div>
                        )}
                        {notification.sender_username && (
                          <div className="flex items-center gap-1">
                            <User className="w-4 h-4 text-gray-400" />
                            <span className="font-mono">{notification.sender_username}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <span>{new Date(notification.received_at).toLocaleString()}</span>
                        </div>
                      </div>

                      {notification.transaction_id && (
                        <p className="text-xs text-gray-500 mt-2 font-mono">
                          TX: {notification.transaction_id}
                        </p>
                      )}

                      {notification.matched_booking_id && (
                        <div className="mt-2">
                          <Badge variant="outline" className="bg-green-50">
                            ✅ Matched to Booking #{notification.matched_booking_id}
                          </Badge>
                        </div>
                      )}
                    </div>
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
