'use client';

import { useState, useMemo, useCallback } from 'react';
import {
  QrCode,
  Download,
  Plus,
  BarChart3,
  Eye,
  Copy,
  CheckCircle,
  ExternalLink,
  Smartphone,
  Monitor,
  Tablet,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { StatsCard } from '@/components/ui/stats-card';
import { FilterBar } from '@/components/ui/filter-bar';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/Toast';
import { useQRCodes, useQRAnalytics, useFilters, useSearch } from '@/hooks/useApi';
import { qrService } from '@/services/api';

export default function QRCodeManagementPage() {
  const toast = useToast();
  
  // State
  const [selectedCode, setSelectedCode] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Form state for creating QR codes
  const [newQRForm, setNewQRForm] = useState({
    name: '',
    url: '',
    campaign: '',
    description: '',
  });

  // Filters
  const { query: searchQuery, debouncedQuery, setQuery: setSearchQuery } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    campaign: '',
    active: '',
  });

  // Combine filters
  const apiFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedQuery,
    }),
    [filters, debouncedQuery]
  );

  // Fetch QR codes data
  const { data: qrResponse, loading, error, refetch } = useQRCodes(apiFilters);
  const qrCodes = qrResponse?.data || [];

  // Fetch analytics for selected code
  const { data: analyticsData, loading: loadingAnalytics } = useQRAnalytics(
    selectedCode?.code
  );

  // Calculate stats
  const stats = useMemo(() => {
    const totalScans = qrCodes.reduce((sum: number, qr: any) => sum + (qr.scan_count || 0), 0);
    const activeCount = qrCodes.filter((qr: any) => qr.is_active).length;
    const totalConversions = qrCodes.reduce(
      (sum: number, qr: any) => sum + (qr.conversion_count || 0),
      0
    );
    const conversionRate =
      totalScans > 0 ? ((totalConversions / totalScans) * 100).toFixed(1) : '0.0';

    return {
      total: qrCodes.length,
      active: activeCount,
      scans: totalScans,
      conversions: totalConversions,
      conversionRate,
    };
  }, [qrCodes]);

  // Handlers
  const handleCreateQR = async () => {
    if (!newQRForm.name || !newQRForm.url) {
      toast.warning('Missing information', 'Please fill in Name and URL fields');
      return;
    }

    try {
      await qrService.createQRCode({
        name: newQRForm.name,
        target_url: newQRForm.url,
        campaign: newQRForm.campaign || 'default',
        description: newQRForm.description,
      });

      toast.success('QR code created!', 'Your QR code is ready to use');
      setShowCreateModal(false);
      setNewQRForm({ name: '', url: '', campaign: '', description: '' });
      refetch();
    } catch (err) {
      console.error('Failed to create QR code:', err);
      toast.error('Creation failed', 'Unable to create QR code. Please try again');
    }
  };

  const handleDownloadQR = (qrCode: any, format: 'png' | 'svg' = 'png') => {
    // Generate download URL (assuming backend provides this)
    const downloadUrl = `/api/qr/download/${qrCode.code}?format=${format}`;
    
    // Create temporary link and trigger download
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `${qrCode.name}-qr.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleCopyURL = (url: string) => {
    navigator.clipboard.writeText(url);
  };

  const handleViewAnalytics = (qrCode: any) => {
    setSelectedCode(qrCode);
    setShowAnalyticsModal(true);
  };

  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
  };

  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Analytics data parsing
  const analytics = useMemo(() => {
    if (!analyticsData?.data) {
      return {
        totalScans: 0,
        uniqueScans: 0,
        conversions: 0,
        conversionRate: 0,
        deviceBreakdown: { mobile: 0, desktop: 0, tablet: 0 },
        scansByDate: [],
      };
    }

    const data = analyticsData.data;
    return {
      totalScans: data.total_scans || 0,
      uniqueScans: data.unique_scans || 0,
      conversions: data.conversions || 0,
      conversionRate: data.conversion_rate || 0,
      deviceBreakdown: data.device_breakdown || { mobile: 0, desktop: 0, tablet: 0 },
      scansByDate: data.scans_by_date || [],
    };
  }, [analyticsData]);

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={QrCode}
          title="Error Loading QR Codes"
          description={error}
          actionLabel="Try Again"
          onAction={refetch}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">QR Code Management</h1>
          <p className="text-gray-600">Create, track, and analyze QR code campaigns</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create QR Code
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Total QR Codes"
          value={stats.total}
          icon={QrCode}
          color="blue"
        />
        <StatsCard
          title="Active Codes"
          value={stats.active}
          subtitle="currently active"
          icon={CheckCircle}
          color="green"
        />
        <StatsCard
          title="Total Scans"
          value={stats.scans.toLocaleString()}
          subtitle="all time"
          icon={Eye}
          color="purple"
        />
        <StatsCard
          title="Conversion Rate"
          value={`${stats.conversionRate}%`}
          subtitle={`${stats.conversions} conversions`}
          icon={BarChart3}
          color="yellow"
        />
      </div>

      {/* Filters */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search QR codes..."
        filters={[
          {
            key: 'campaign',
            label: 'All Campaigns',
            options: [
              { label: 'Marketing', value: 'marketing' },
              { label: 'Events', value: 'events' },
              { label: 'Menu', value: 'menu' },
              { label: 'Default', value: 'default' },
            ],
            value: filters.campaign,
          },
          {
            key: 'active',
            label: 'All Status',
            options: [
              { label: 'Active', value: 'true' },
              { label: 'Inactive', value: 'false' },
            ],
            value: filters.active,
          },
        ]}
        onFilterChange={(key, value) => updateFilter(key as 'campaign' | 'active', value)}
        onClearFilters={handleClearFilters}
        showClearButton
      />

      {/* Loading State */}
      {loading && <LoadingSpinner message="Loading QR codes..." />}

      {/* Empty State */}
      {!loading && qrCodes.length === 0 && (
        <EmptyState
          icon={QrCode}
          title="No QR codes found"
          description={
            Object.values(filters).some(Boolean) || debouncedQuery
              ? 'Try adjusting your filters or search query'
              : 'Create your first QR code to start tracking scans'
          }
          actionLabel="Create QR Code"
          onAction={() => setShowCreateModal(true)}
        />
      )}

      {/* QR Codes Grid */}
      {!loading && qrCodes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {qrCodes.map((qr: any) => (
            <div
              key={qr.id}
              className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* QR Code Preview */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 flex items-center justify-center">
                <div className="w-48 h-48 bg-white p-4 rounded-lg shadow-md">
                  {/* QR Code Image - Replace with actual QR code image */}
                  <div className="w-full h-full bg-gray-200 rounded flex items-center justify-center">
                    <QrCode className="w-24 h-24 text-gray-400" />
                  </div>
                </div>
              </div>

              {/* QR Code Info */}
              <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {qr.name}
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        qr.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {qr.is_active ? '✓ Active' : '○ Inactive'}
                    </span>
                  </div>
                </div>

                {qr.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {qr.description}
                  </p>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 gap-3 mb-3 p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-xs text-gray-500">Scans</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {qr.scan_count || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Conversions</div>
                    <div className="text-lg font-semibold text-green-600">
                      {qr.conversion_count || 0}
                    </div>
                  </div>
                </div>

                {/* Code & Campaign */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Code:</span>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {qr.code}
                      </code>
                      <button
                        onClick={() => handleCopyCode(qr.code)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Copy code"
                      >
                        {copiedCode === qr.code ? (
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Campaign:</span>
                    <span className="text-xs font-medium text-gray-700">
                      {qr.campaign || 'Default'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Created:</span>
                    <span className="text-xs text-gray-700">
                      {formatDate(qr.created_at)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleViewAnalytics(qr)}
                  >
                    <BarChart3 className="w-4 h-4 mr-1" />
                    Analytics
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownloadQR(qr, 'png')}
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopyURL(qr.target_url)}
                    title="Copy URL"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create QR Code Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setNewQRForm({ name: '', url: '', campaign: '', description: '' });
        }}
        title="Create New QR Code"
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={newQRForm.name}
              onChange={(e) => setNewQRForm({ ...newQRForm, name: e.target.value })}
              placeholder="e.g., Menu QR Code"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={newQRForm.url}
              onChange={(e) => setNewQRForm({ ...newQRForm, url: e.target.value })}
              placeholder="https://myhibachi.com/menu"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Campaign
            </label>
            <select
              value={newQRForm.campaign}
              onChange={(e) => setNewQRForm({ ...newQRForm, campaign: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Default</option>
              <option value="marketing">Marketing</option>
              <option value="events">Events</option>
              <option value="menu">Menu</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={newQRForm.description}
              onChange={(e) =>
                setNewQRForm({ ...newQRForm, description: e.target.value })
              }
              placeholder="Optional description for internal use"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                setShowCreateModal(false);
                setNewQRForm({ name: '', url: '', campaign: '', description: '' });
              }}
            >
              Cancel
            </Button>
            <Button className="flex-1" onClick={handleCreateQR}>
              Create QR Code
            </Button>
          </div>
        </div>
      </Modal>

      {/* Analytics Modal */}
      <Modal
        isOpen={showAnalyticsModal}
        onClose={() => {
          setShowAnalyticsModal(false);
          setSelectedCode(null);
        }}
        title={`Analytics: ${selectedCode?.name || 'QR Code'}`}
        size="lg"
      >
        {loadingAnalytics ? (
          <LoadingSpinner message="Loading analytics..." />
        ) : (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-blue-600 mb-1">Total Scans</div>
                <div className="text-2xl font-bold text-blue-900">
                  {analytics.totalScans}
                </div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="text-sm text-purple-600 mb-1">Unique Scans</div>
                <div className="text-2xl font-bold text-purple-900">
                  {analytics.uniqueScans}
                </div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-sm text-green-600 mb-1">Conversions</div>
                <div className="text-2xl font-bold text-green-900">
                  {analytics.conversions}
                </div>
              </div>
              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="text-sm text-yellow-600 mb-1">Conv. Rate</div>
                <div className="text-2xl font-bold text-yellow-900">
                  {analytics.conversionRate.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Device Breakdown */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Device Breakdown
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-5 h-5 text-blue-600" />
                    <span className="text-sm text-gray-700">Mobile</span>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {analytics.deviceBreakdown.mobile || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Monitor className="w-5 h-5 text-purple-600" />
                    <span className="text-sm text-gray-700">Desktop</span>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {analytics.deviceBreakdown.desktop || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Tablet className="w-5 h-5 text-green-600" />
                    <span className="text-sm text-gray-700">Tablet</span>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {analytics.deviceBreakdown.tablet || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => handleDownloadQR(selectedCode, 'png')}
              >
                <Download className="w-4 h-4 mr-2" />
                Download PNG
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => handleDownloadQR(selectedCode, 'svg')}
              >
                <Download className="w-4 h-4 mr-2" />
                Download SVG
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
