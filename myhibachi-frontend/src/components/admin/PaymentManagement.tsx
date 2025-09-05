'use client';

import { format } from 'date-fns';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  CreditCard,
  DollarSign,
  Download,
  ExternalLink,
  Eye,
  RefreshCw,
  RotateCcw,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface Payment {
  id: string;
  user_id: string;
  booking_id?: string;
  stripe_payment_intent_id?: string;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'succeeded' | 'failed' | 'canceled' | 'refunded';
  method: 'stripe' | 'zelle' | 'venmo';
  payment_type?: string;
  description?: string;
  stripe_fee: number;
  net_amount?: number;
  created_at: string;
  updated_at?: string;
}

interface PaymentAnalytics {
  total_payments: number;
  total_amount: number;
  avg_payment: number;
  payment_methods: Record;
  monthly_revenue: Array;
}

interface RefundRequest {
  payment_id: string;
  amount?: number;
  reason?: string;
  notes?: string;
}

export default function PaymentManagement() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [analytics, setAnalytics] = useState<PaymentAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: '',
    method: '',
    booking_id: '',
    user_id: '',
    start_date: '',
    end_date: '',
  });
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [refundData, setRefundData] = useState<RefundRequest>({
    payment_id: '',
    amount: undefined,
    reason: '',
    notes: '',
  });
  const [refundLoading, setRefundLoading] = useState(false);

  useEffect(() => {
    fetchPayments();
    fetchAnalytics();
  }, [filter]);

  const fetchPayments = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      Object.entries(filter).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(`/api/stripe/payments?${params}`);
      if (response.ok) {
        const data = await response.json();
        setPayments(data);
      }
    } catch (error) {
      console.error('Error fetching payments:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchAnalytics = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter.start_date) params.append('start_date', filter.start_date);
      if (filter.end_date) params.append('end_date', filter.end_date);

      const response = await fetch(`/api/stripe/analytics/payments?${params}`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  }, [filter]);

  const handleRefund = async () => {
    if (!selectedPayment || !refundData.payment_id) return;

    try {
      setRefundLoading(true);
      const response = await fetch('/api/stripe/refund', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(refundData),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Refund successful: ${result.message}`);
        setShowRefundModal(false);
        setSelectedPayment(null);
        fetchPayments(); // Refresh payments list
      } else {
        const error = await response.json();
        alert(`Refund failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error processing refund:', error);
      alert('Refund failed. Please try again.');
    } finally {
      setRefundLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'succeeded':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'processing':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />;
      case 'refunded':
        return <RotateCcw className="h-4 w-4 text-purple-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'refunded':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const exportPayments = () => {
    const csv = [
      [
        'Date',
        'Payment ID',
        'Booking ID',
        'Customer',
        'Amount',
        'Fee',
        'Net',
        'Status',
        'Method',
      ].join(','),
      ...payments.map((payment) =>
        [
          format(new Date(payment.created_at), 'yyyy-MM-dd'),
          payment.id,
          payment.booking_id || 'N/A',
          payment.user_id,
          payment.amount,
          payment.stripe_fee,
          payment.net_amount || payment.amount,
          payment.status,
          payment.method,
        ].join(','),
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payments-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">Payment Management</h1>
        <p className="text-gray-600">Monitor and manage all payment transactions</p>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
          <div className="rounded-lg bg-white p-6 shadow">
            <div className="flex items-center">
              <div className="rounded-lg bg-blue-100 p-2">
                <DollarSign className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${analytics.total_amount.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-white p-6 shadow">
            <div className="flex items-center">
              <div className="rounded-lg bg-green-100 p-2">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Payment</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${analytics.avg_payment.toFixed(0)}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-white p-6 shadow">
            <div className="flex items-center">
              <div className="rounded-lg bg-purple-100 p-2">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Payments</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.total_payments}</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-white p-6 shadow">
            <div className="flex items-center">
              <div className="rounded-lg bg-orange-100 p-2">
                <CreditCard className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Stripe Payments</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.payment_methods.stripe || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 rounded-lg bg-white p-6 shadow">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          <div className="flex space-x-2">
            <button
              onClick={exportPayments}
              className="flex items-center rounded-lg bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700"
            >
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </button>
            <button
              onClick={fetchPayments}
              className="flex items-center rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Status</label>
            <select
              value={filter.status}
              onChange={(e) => setFilter((prev) => ({ ...prev, status: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="succeeded">Succeeded</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Method</label>
            <select
              value={filter.method}
              onChange={(e) => setFilter((prev) => ({ ...prev, method: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Methods</option>
              <option value="stripe">Stripe</option>
              <option value="zelle">Zelle</option>
              <option value="venmo">Venmo</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Booking ID</label>
            <input
              type="text"
              value={filter.booking_id}
              onChange={(e) => setFilter((prev) => ({ ...prev, booking_id: e.target.value }))}
              placeholder="Search booking..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">User ID</label>
            <input
              type="text"
              value={filter.user_id}
              onChange={(e) => setFilter((prev) => ({ ...prev, user_id: e.target.value }))}
              placeholder="Search user..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Start Date</label>
            <input
              type="date"
              value={filter.start_date}
              onChange={(e) => setFilter((prev) => ({ ...prev, start_date: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">End Date</label>
            <input
              type="date"
              value={filter.end_date}
              onChange={(e) => setFilter((prev) => ({ ...prev, end_date: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Payments Table */}
      <div className="overflow-hidden rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Payments</h2>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading payments...</p>
          </div>
        ) : payments.length === 0 ? (
          <div className="p-8 text-center">
            <CreditCard className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <p className="text-gray-600">No payments found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Method
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm whitespace-nowrap text-gray-900">
                      {format(new Date(payment.created_at), 'MMM dd, yyyy')}
                      <div className="text-xs text-gray-500">
                        {format(new Date(payment.created_at), 'HH:mm')}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {payment.id.slice(0, 8)}...
                      </div>
                      <div className="text-sm text-gray-500">
                        {payment.booking_id
                          ? `Booking: ${payment.booking_id.slice(0, 8)}...`
                          : 'Manual Payment'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm whitespace-nowrap text-gray-900">
                      {payment.user_id.slice(0, 12)}...
                    </td>
                    <td className="px-6 py-4 text-sm whitespace-nowrap text-gray-900">
                      <div className="font-medium">${payment.amount.toFixed(2)}</div>
                      {payment.stripe_fee > 0 && (
                        <div className="text-xs text-gray-500">
                          Fee: ${payment.stripe_fee.toFixed(2)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(
                          payment.status,
                        )}`}
                      >
                        {getStatusIcon(payment.status)}
                        <span className="ml-1 capitalize">{payment.status}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm whitespace-nowrap text-gray-900 capitalize">
                      {payment.method}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium whitespace-nowrap">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedPayment(payment)}
                          className="flex items-center text-blue-600 hover:text-blue-900"
                        >
                          <Eye className="mr-1 h-4 w-4" />
                          View
                        </button>
                        {payment.status === 'succeeded' && payment.method === 'stripe' && (
                          <button
                            onClick={() => {
                              setSelectedPayment(payment);
                              setRefundData({
                                payment_id: payment.id,
                                amount: undefined,
                                reason: '',
                                notes: '',
                              });
                              setShowRefundModal(true);
                            }}
                            className="flex items-center text-red-600 hover:text-red-900"
                          >
                            <RotateCcw className="mr-1 h-4 w-4" />
                            Refund
                          </button>
                        )}
                        {payment.stripe_payment_intent_id && (
                          <a
                            href={`https://dashboard.stripe.com/payments/${payment.stripe_payment_intent_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center text-purple-600 hover:text-purple-900"
                          >
                            <ExternalLink className="mr-1 h-4 w-4" />
                            Stripe
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payment Detail Modal */}
      {selectedPayment && !showRefundModal && (
        <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
          <div className="max-h-screen w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-xl">
            <div className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Payment Details</h3>
                <button
                  onClick={() => setSelectedPayment(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Payment ID</label>
                    <p className="font-mono text-sm text-gray-900">{selectedPayment.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(
                        selectedPayment.status,
                      )}`}
                    >
                      {getStatusIcon(selectedPayment.status)}
                      <span className="ml-1 capitalize">{selectedPayment.status}</span>
                    </span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Amount</label>
                    <p className="text-sm text-gray-900">${selectedPayment.amount.toFixed(2)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Method</label>
                    <p className="text-sm text-gray-900 capitalize">{selectedPayment.method}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Created</label>
                    <p className="text-sm text-gray-900">
                      {format(new Date(selectedPayment.created_at), 'PPpp')}
                    </p>
                  </div>
                  {selectedPayment.stripe_fee > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Processing Fee
                      </label>
                      <p className="text-sm text-gray-900">
                        ${selectedPayment.stripe_fee.toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>

                {selectedPayment.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <p className="text-sm text-gray-900">{selectedPayment.description}</p>
                  </div>
                )}

                {selectedPayment.stripe_payment_intent_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Stripe Payment Intent
                    </label>
                    <div className="flex items-center space-x-2">
                      <p className="font-mono text-sm text-gray-900">
                        {selectedPayment.stripe_payment_intent_id}
                      </p>
                      <a
                        href={`https://dashboard.stripe.com/payments/${selectedPayment.stripe_payment_intent_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Refund Modal */}
      {showRefundModal && selectedPayment && (
        <div className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
            <div className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Process Refund</h3>
                <button
                  onClick={() => setShowRefundModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="rounded-lg bg-gray-50 p-4">
                  <p className="text-sm text-gray-600">
                    Original Payment:{' '}
                    <span className="font-medium">${selectedPayment.amount.toFixed(2)}</span>
                  </p>
                  <p className="text-sm text-gray-600">
                    Payment ID: <span className="font-mono text-xs">{selectedPayment.id}</span>
                  </p>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Refund Amount (leave empty for full refund)
                  </label>
                  <div className="relative">
                    <span className="absolute top-1/2 left-3 -translate-y-1/2 transform text-gray-500">
                      $
                    </span>
                    <input
                      type="number"
                      value={refundData.amount || ''}
                      onChange={(e) =>
                        setRefundData((prev) => ({
                          ...prev,
                          amount: e.target.value ? parseFloat(e.target.value) : undefined,
                        }))
                      }
                      placeholder={selectedPayment.amount.toFixed(2)}
                      max={selectedPayment.amount}
                      step="0.01"
                      className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-8 focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Reason</label>
                  <select
                    value={refundData.reason}
                    onChange={(e) => setRefundData((prev) => ({ ...prev, reason: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select reason...</option>
                    <option value="requested_by_customer">Requested by customer</option>
                    <option value="duplicate">Duplicate payment</option>
                    <option value="fraudulent">Fraudulent</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Internal Notes
                  </label>
                  <textarea
                    value={refundData.notes}
                    onChange={(e) => setRefundData((prev) => ({ ...prev, notes: e.target.value }))}
                    placeholder="Add any internal notes about this refund..."
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setShowRefundModal(false)}
                    className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRefund}
                    disabled={refundLoading}
                    className="flex flex-1 items-center justify-center rounded-lg bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700 disabled:opacity-50"
                  >
                    {refundLoading ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Process Refund
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
