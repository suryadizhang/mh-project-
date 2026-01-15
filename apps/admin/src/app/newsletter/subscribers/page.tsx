'use client';

import { Download, Mail, Plus, Upload, UserCheck, UserX } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import { StatsCard } from '@/components/ui/stats-card';
import { tokenManager } from '@/services/api';

// Newsletter subscriber statuses
const STATUSES = ['active', 'unsubscribed', 'bounced', 'complained'] as const;
type SubscriberStatus = (typeof STATUSES)[number];

// Subscriber form data
interface SubscriberFormData {
  email: string;
  name?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  status?: SubscriberStatus;
}

export default function NewsletterSubscribersPage() {
  // State
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>(
    'create'
  );
  const [selectedSubscriber, setSelectedSubscriber] = useState<any>(null);
  const [formData, setFormData] = useState<SubscriberFormData>({
    email: '',
    name: '',
    tags: [],
    status: 'active',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [importing, setImporting] = useState(false);
  const [subscribers, setSubscribers] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');

  // Fetch subscribers
  const fetchSubscribers = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);
      params.append('skip', ((page - 1) * limit).toString());
      params.append('limit', limit.toString());

      const response = await fetch(
        `/api/newsletter/subscribers?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      setSubscribers(data);
    } catch (err: any) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscribers();
  }, [page, statusFilter, searchQuery]);

  // Stats calculation
  const stats = useMemo(() => {
    if (!subscribers?.data)
      return {
        total: 0,
        active: 0,
        unsubscribed: 0,
        bounced: 0,
      };

    const total = subscribers.total_count || subscribers.data.length;
    const active = subscribers.data.filter(
      (s: any) => s.status === 'active'
    ).length;
    const unsubscribed = subscribers.data.filter(
      (s: any) => s.status === 'unsubscribed'
    ).length;
    const bounced = subscribers.data.filter(
      (s: any) => s.status === 'bounced'
    ).length;

    return { total, active, unsubscribed, bounced };
  }, [subscribers]);

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setSelectedSubscriber(null);
    setFormData({
      email: '',
      name: '',
      tags: [],
      status: 'active',
    });
    setShowModal(true);
  };

  const handleEdit = (subscriber: any) => {
    setModalMode('edit');
    setSelectedSubscriber(subscriber);
    setFormData({
      email: subscriber.email,
      name: subscriber.name || '',
      tags: subscriber.tags || [],
      status: subscriber.status,
    });
    setShowModal(true);
  };

  const handleView = (subscriber: any) => {
    setModalMode('view');
    setSelectedSubscriber(subscriber);
    setShowModal(true);
  };

  const handleSubmit = async () => {
    try {
      const endpoint =
        modalMode === 'create'
          ? '/api/newsletter/subscribers'
          : `/api/newsletter/subscribers/${selectedSubscriber.id}`;

      const method = modalMode === 'create' ? 'POST' : 'PUT';

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to save subscriber');

      setShowModal(false);
      fetchSubscribers();
    } catch (err) {
      console.error('Failed to save subscriber:', err);
      alert('Failed to save subscriber. Please try again.');
    }
  };

  const handleDelete = async (subscriberId: number) => {
    if (!confirm('Are you sure you want to delete this subscriber?')) return;

    try {
      const response = await fetch(
        `/api/newsletter/subscribers/${subscriberId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to delete');

      fetchSubscribers();
    } catch (err) {
      console.error('Failed to delete subscriber:', err);
      alert('Failed to delete subscriber. Please try again.');
    }
  };

  const handleUnsubscribe = async (subscriberId: number) => {
    try {
      const response = await fetch(
        `/api/newsletter/subscribers/${subscriberId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
          body: JSON.stringify({ status: 'unsubscribed' }),
        }
      );

      if (!response.ok) throw new Error('Failed to unsubscribe');

      fetchSubscribers();
    } catch (err) {
      console.error('Failed to unsubscribe:', err);
      alert('Failed to unsubscribe. Please try again.');
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/newsletter/subscribers?export=csv', {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      });

      if (!response.ok) throw new Error('Failed to export');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `subscribers-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to export:', err);
      alert('Failed to export subscribers. Please try again.');
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImporting(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/newsletter/subscribers/import', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to import');

      const result = await response.json();
      alert(`Imported ${result.count} subscribers successfully!`);
      fetchSubscribers();
    } catch (err) {
      console.error('Failed to import:', err);
      alert('Failed to import subscribers. Please try again.');
    } finally {
      setImporting(false);
      event.target.value = ''; // Reset input
    }
  };

  const handleClearFilters = () => {
    setStatusFilter('');
    setSearchQuery('');
    setPage(1);
  };

  // Status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'unsubscribed':
        return 'bg-gray-100 text-gray-800';
      case 'bounced':
        return 'bg-red-100 text-red-800';
      case 'complained':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Newsletter Subscribers
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your email subscribers and mailing lists
          </p>
        </div>
        <div className="flex gap-3">
          <label>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleImport}
              disabled={importing}
            />
            <Button variant="outline" disabled={importing} asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" />
                {importing ? 'Importing...' : 'Import CSV'}
              </span>
            </Button>
          </label>
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="w-4 h-4 mr-2" />
            Add Subscriber
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Subscribers"
          value={stats.total}
          icon={Mail}
          trend={{ value: 12.5, isPositive: true }}
        />
        <StatsCard
          title="Active"
          value={stats.active}
          icon={UserCheck}
          trend={{ value: 8.2, isPositive: true }}
        />
        <StatsCard
          title="Unsubscribed"
          value={stats.unsubscribed}
          icon={UserX}
        />
        <StatsCard title="Bounced" value={stats.bounced} icon={Mail} />
      </div>

      {/* Search & Filter */}
      <div className="bg-white shadow sm:rounded-lg p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by email or name..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="unsubscribed">Unsubscribed</option>
            <option value="bounced">Bounced</option>
            <option value="complained">Complained</option>
          </select>
          {(statusFilter || searchQuery) && (
            <Button variant="outline" onClick={handleClearFilters}>
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Subscribers Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="p-4 text-red-600">
            Error loading subscribers: {error.message}
          </div>
        ) : !subscribers?.data || subscribers.data.length === 0 ? (
          <EmptyState
            icon={Mail}
            title="No subscribers yet"
            description="Add your first subscriber or import from CSV"
            actionLabel="Add Subscriber"
            onAction={handleCreate}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subscriber
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tags
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subscribed
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {subscribers.data.map((subscriber: any) => (
                    <tr
                      key={subscriber.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleView(subscriber)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                            <Mail className="h-5 w-5 text-gray-500" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {subscriber.name || 'No Name'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {subscriber.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(subscriber.status)}`}
                        >
                          {subscriber.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {subscriber.tags
                            ?.slice(0, 3)
                            .map((tag: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          {subscriber.tags?.length > 3 && (
                            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                              +{subscriber.tags.length - 3} more
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(subscriber.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div
                          className="flex justify-end gap-2"
                          onClick={e => e.stopPropagation()}
                        >
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(subscriber)}
                          >
                            Edit
                          </Button>
                          {subscriber.status === 'active' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleUnsubscribe(subscriber.id)}
                            >
                              Unsubscribe
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDelete(subscriber.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <Button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  variant="outline"
                >
                  Previous
                </Button>
                <Button
                  onClick={() => setPage(page + 1)}
                  disabled={
                    !subscribers?.data || subscribers.data.length < limit
                  }
                  variant="outline"
                >
                  Next
                </Button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing{' '}
                    <span className="font-medium">
                      {(page - 1) * limit + 1}
                    </span>{' '}
                    to{' '}
                    <span className="font-medium">
                      {Math.min(page * limit, stats.total)}
                    </span>{' '}
                    of <span className="font-medium">{stats.total}</span>{' '}
                    results
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <Button
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                      variant="outline"
                      className="rounded-r-none"
                    >
                      Previous
                    </Button>
                    <Button
                      onClick={() => setPage(page + 1)}
                      disabled={
                        !subscribers?.data || subscribers.data.length < limit
                      }
                      variant="outline"
                      className="rounded-l-none"
                    >
                      Next
                    </Button>
                  </nav>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={
            modalMode === 'view'
              ? 'Subscriber Details'
              : modalMode === 'edit'
                ? 'Edit Subscriber'
                : 'Add Subscriber'
          }
        >
          {modalMode === 'view' && selectedSubscriber ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <p className="mt-1 text-sm text-gray-900">
                  {selectedSubscriber.email}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Name
                </label>
                <p className="mt-1 text-sm text-gray-900">
                  {selectedSubscriber.name || 'Not provided'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Status
                </label>
                <span
                  className={`mt-1 px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(selectedSubscriber.status)}`}
                >
                  {selectedSubscriber.status}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Tags
                </label>
                <div className="mt-1 flex flex-wrap gap-1">
                  {selectedSubscriber.tags?.map((tag: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                    >
                      {tag}
                    </span>
                  )) || <p className="text-sm text-gray-500">No tags</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Subscribed
                </label>
                <p className="mt-1 text-sm text-gray-900">
                  {new Date(selectedSubscriber.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ) : (
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSubmit();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={e =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  disabled={modalMode === 'edit'}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      status: e.target.value as SubscriberStatus,
                    })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  {STATUSES.map(status => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.tags?.join(', ') || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      tags: e.target.value
                        .split(',')
                        .map(t => t.trim())
                        .filter(Boolean),
                    })
                  }
                  placeholder="e.g., vip, customer, promotion"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  {modalMode === 'edit' ? 'Update' : 'Create'} Subscriber
                </Button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
}
