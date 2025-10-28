'use client';

import { useState, useCallback, useMemo } from 'react';
import {
  Target,
  Plus,
  Phone,
  Mail,
  Calendar,
  DollarSign,
  TrendingUp,
  Users,
  CheckCircle,
  XCircle,
  Sparkles,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { StatsCard } from '@/components/ui/stats-card';
import { FilterBar, FilterDefinition } from '@/components/ui/filter-bar';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import { useLeads, usePagination, useFilters, useSearch } from '@/hooks/useApi';

// Lead status enum
const LEAD_STATUSES = {
  NEW: 'new',
  QUALIFIED: 'qualified',
  CONVERTED: 'converted',
  LOST: 'lost',
};

const STATUS_LABELS = {
  [LEAD_STATUSES.NEW]: 'New',
  [LEAD_STATUSES.QUALIFIED]: 'Qualified',
  [LEAD_STATUSES.CONVERTED]: 'Converted',
  [LEAD_STATUSES.LOST]: 'Lost',
};

const STATUS_COLORS = {
  [LEAD_STATUSES.NEW]: 'bg-blue-50 border-blue-200',
  [LEAD_STATUSES.QUALIFIED]: 'bg-yellow-50 border-yellow-200',
  [LEAD_STATUSES.CONVERTED]: 'bg-green-50 border-green-200',
  [LEAD_STATUSES.LOST]: 'bg-gray-50 border-gray-200',
};

export default function LeadsPage() {
  // State
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [isLeadModalOpen, setIsLeadModalOpen] = useState(false);
  const [isNewLeadModalOpen, setIsNewLeadModalOpen] = useState(false);

  // Pagination and filters
  const { page, limit, setPage, nextPage, prevPage } = usePagination(1, 100);
  const { query: searchQuery, debouncedQuery, setQuery: setSearchQuery } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    status: '',
    quality: '',
    source: '',
  });

  // Combine all filters for API call
  const apiFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedQuery,
      page,
      limit,
      sort_by: 'created_at',
      sort_order: 'desc' as const,
    }),
    [filters, debouncedQuery, page, limit]
  );

  // Fetch leads data
  const { data: leadsResponse, loading, error, refetch } = useLeads(apiFilters);

  const leads = leadsResponse?.data || [];
  const totalCount = leadsResponse?.total_count || 0;

  // Group leads by status
  const leadsByStatus = useMemo(() => {
    return Object.values(LEAD_STATUSES).reduce((acc, status) => {
      acc[status] = leads.filter((lead: any) => lead.status === status);
      return acc;
    }, {} as Record<string, any[]>);
  }, [leads]);

  // Calculate stats
  const stats = useMemo(() => {
    const newCount = leadsByStatus[LEAD_STATUSES.NEW]?.length || 0;
    const qualifiedCount = leadsByStatus[LEAD_STATUSES.QUALIFIED]?.length || 0;
    const convertedCount = leadsByStatus[LEAD_STATUSES.CONVERTED]?.length || 0;
    const lostCount = leadsByStatus[LEAD_STATUSES.LOST]?.length || 0;

    const avgScore =
      leads.length > 0
        ? (
            leads.reduce((sum: number, lead: any) => sum + (lead.ai_score || 0), 0) / leads.length
          ).toFixed(0)
        : 0;

    const conversionRate =
      newCount + qualifiedCount + convertedCount > 0
        ? ((convertedCount / (newCount + qualifiedCount + convertedCount)) * 100).toFixed(1)
        : 0;

    return {
      total: totalCount,
      new: newCount,
      qualified: qualifiedCount,
      converted: convertedCount,
      lost: lostCount,
      avgScore,
      conversionRate,
    };
  }, [leads, leadsByStatus, totalCount]);

  // Filter definitions
  const filterDefinitions: FilterDefinition[] = [
    {
      key: 'status',
      label: 'All Status',
      options: [
        { label: 'New', value: LEAD_STATUSES.NEW },
        { label: 'Qualified', value: LEAD_STATUSES.QUALIFIED },
        { label: 'Converted', value: LEAD_STATUSES.CONVERTED },
        { label: 'Lost', value: LEAD_STATUSES.LOST },
      ],
      value: filters.status,
    },
    {
      key: 'quality',
      label: 'All Quality',
      options: [
        { label: 'Hot', value: 'hot' },
        { label: 'Warm', value: 'warm' },
        { label: 'Cold', value: 'cold' },
      ],
      value: filters.quality,
    },
    {
      key: 'source',
      label: 'All Sources',
      options: [
        { label: 'Website Form', value: 'website_form' },
        { label: 'Social Media', value: 'social_media' },
        { label: 'Referral', value: 'referral' },
        { label: 'Direct', value: 'direct' },
      ],
      value: filters.source,
    },
  ];

  // Handlers
  const handleLeadClick = (lead: any) => {
    setSelectedLead(lead);
    setIsLeadModalOpen(true);
  };

  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
    setPage(1);
  };

  // Get score color
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  // Get quality badge color
  const getQualityColor = (quality: string) => {
    switch (quality?.toLowerCase()) {
      case 'hot':
        return 'bg-red-100 text-red-800';
      case 'warm':
        return 'bg-yellow-100 text-yellow-800';
      case 'cold':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={Target}
          title="Error Loading Leads"
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
          <h1 className="text-3xl font-bold text-gray-900">Lead Management</h1>
          <p className="text-gray-600">Track and manage your sales pipeline</p>
        </div>
        <Button onClick={() => setIsNewLeadModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Lead
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Total Leads"
          value={stats.total}
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Conversion Rate"
          value={`${stats.conversionRate}%`}
          icon={TrendingUp}
          color="green"
        />
        <StatsCard
          title="Avg AI Score"
          value={stats.avgScore}
          subtitle="out of 100"
          icon={Sparkles}
          color="purple"
        />
        <StatsCard
          title="Qualified"
          value={stats.qualified}
          subtitle={`${stats.converted} converted`}
          icon={CheckCircle}
          color="yellow"
        />
      </div>

      {/* Filters */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search leads by name, email, phone..."
        filters={filterDefinitions}
        onFilterChange={(key, value) => updateFilter(key as 'status' | 'quality' | 'source', value)}
        onClearFilters={handleClearFilters}
        showClearButton
      />

      {/* Loading State */}
      {loading && <LoadingSpinner message="Loading leads..." />}

      {/* Empty State */}
      {!loading && leads.length === 0 && (
        <EmptyState
          icon={Target}
          title="No leads found"
          description={
            Object.values(filters).some(Boolean) || debouncedQuery
              ? 'Try adjusting your filters or search query'
              : 'Get started by adding your first lead'
          }
          actionLabel="Add Lead"
          onAction={() => setIsNewLeadModalOpen(true)}
        />
      )}

      {/* Kanban Board */}
      {!loading && leads.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries(LEAD_STATUSES).map(([key, status]) => {
            const statusLeads = leadsByStatus[status] || [];
            const count = statusLeads.length;

            return (
              <div key={status} className="flex flex-col">
                {/* Column Header */}
                <div
                  className={`p-4 rounded-t-lg border-t-4 ${STATUS_COLORS[status]}`}
                >
                  <h3 className="font-semibold text-gray-900 flex items-center justify-between">
                    <span>{STATUS_LABELS[status]}</span>
                    <span className="text-sm bg-white px-2 py-1 rounded">{count}</span>
                  </h3>
                </div>

                {/* Lead Cards */}
                <div className="flex-1 bg-gray-50 p-2 space-y-2 min-h-[400px] max-h-[600px] overflow-y-auto">
                  {statusLeads.map((lead: any) => (
                    <div
                      key={lead.lead_id}
                      onClick={() => handleLeadClick(lead)}
                      className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                    >
                      {/* Lead Name */}
                      <h4 className="font-medium text-gray-900 mb-2">
                        {lead.contact?.name || 'Unknown'}
                      </h4>

                      {/* AI Score */}
                      {lead.ai_score && (
                        <div className="mb-2">
                          <div
                            className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${getScoreColor(lead.ai_score)}`}
                          >
                            <Sparkles className="w-3 h-3 mr-1" />
                            Score: {lead.ai_score}
                          </div>
                        </div>
                      )}

                      {/* Quality Badge */}
                      {lead.quality && (
                        <span
                          className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${getQualityColor(lead.quality)} mb-2`}
                        >
                          {lead.quality.toUpperCase()}
                        </span>
                      )}

                      {/* Lead Info */}
                      <div className="space-y-1 text-sm text-gray-600">
                        {lead.contact?.email && (
                          <div className="flex items-center">
                            <Mail className="w-3 h-3 mr-2" />
                            <span className="truncate">{lead.contact.email}</span>
                          </div>
                        )}
                        {lead.contact?.phone && (
                          <div className="flex items-center">
                            <Phone className="w-3 h-3 mr-2" />
                            {lead.contact.phone}
                          </div>
                        )}
                        {lead.context?.event_date && (
                          <div className="flex items-center">
                            <Calendar className="w-3 h-3 mr-2" />
                            {formatDate(lead.context.event_date)}
                          </div>
                        )}
                        {lead.context?.budget_range && (
                          <div className="flex items-center">
                            <DollarSign className="w-3 h-3 mr-2" />
                            {lead.context.budget_range}
                          </div>
                        )}
                      </div>

                      {/* Source */}
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <span className="text-xs text-gray-500">
                          {lead.source_type || 'Unknown source'}
                        </span>
                      </div>

                      {/* Last Contact */}
                      {lead.last_contact_date && (
                        <div className="mt-1 text-xs text-gray-500">
                          Last contact: {formatDate(lead.last_contact_date)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lead Detail Modal */}
      {selectedLead && (
        <Modal
          isOpen={isLeadModalOpen}
          onClose={() => setIsLeadModalOpen(false)}
          title={`Lead Details - ${selectedLead.contact?.name || 'Unknown'}`}
          size="lg"
          footer={
            <>
              <Button variant="outline" onClick={() => setIsLeadModalOpen(false)}>
                Close
              </Button>
              <Button>
                <Phone className="w-4 h-4 mr-2" />
                Call
              </Button>
              <Button>
                <Mail className="w-4 h-4 mr-2" />
                Email
              </Button>
              <Button>
                <CheckCircle className="w-4 h-4 mr-2" />
                Convert
              </Button>
            </>
          }
        >
          <div className="space-y-6">
            {/* AI Score */}
            {selectedLead.ai_score && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">AI Score</h3>
                <div className="flex items-center">
                  <div className="flex-1 bg-gray-200 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full ${
                        selectedLead.ai_score >= 80
                          ? 'bg-green-500'
                          : selectedLead.ai_score >= 60
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${selectedLead.ai_score}%` }}
                    />
                  </div>
                  <span className="ml-3 text-sm font-semibold">
                    {selectedLead.ai_score}/100
                  </span>
                </div>
              </div>
            )}

            {/* Contact Information */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Contact Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <Mail className="w-4 h-4 mr-2 text-gray-400" />
                  <span>{selectedLead.contact?.email || 'No email'}</span>
                </div>
                <div className="flex items-center">
                  <Phone className="w-4 h-4 mr-2 text-gray-400" />
                  <span>{selectedLead.contact?.phone || 'No phone'}</span>
                </div>
              </div>
            </div>

            {/* Event Details */}
            {selectedLead.context && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Event Details
                </h3>
                <div className="space-y-2 text-sm">
                  {selectedLead.context.event_date && (
                    <div>
                      <span className="text-gray-600">Date:</span>{' '}
                      <span className="font-medium">
                        {formatDate(selectedLead.context.event_date)}
                      </span>
                    </div>
                  )}
                  {selectedLead.context.guest_count && (
                    <div>
                      <span className="text-gray-600">Guests:</span>{' '}
                      <span className="font-medium">
                        {selectedLead.context.guest_count} people
                      </span>
                    </div>
                  )}
                  {selectedLead.context.budget_range && (
                    <div>
                      <span className="text-gray-600">Budget:</span>{' '}
                      <span className="font-medium">
                        {selectedLead.context.budget_range}
                      </span>
                    </div>
                  )}
                  {selectedLead.context.location && (
                    <div>
                      <span className="text-gray-600">Location:</span>{' '}
                      <span className="font-medium">{selectedLead.context.location}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Source Information */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Source</h3>
              <div className="text-sm">
                <span className="inline-block px-3 py-1 bg-gray-100 rounded">
                  {selectedLead.source_type || 'Unknown'}
                </span>
              </div>
            </div>

            {/* Timeline */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Timeline</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Created:</span>{' '}
                  {formatDate(selectedLead.created_at)}
                </div>
                {selectedLead.last_contact_date && (
                  <div>
                    <span className="font-medium">Last Contact:</span>{' '}
                    {formatDate(selectedLead.last_contact_date)}
                  </div>
                )}
                {selectedLead.updated_at && (
                  <div>
                    <span className="font-medium">Updated:</span>{' '}
                    {formatDate(selectedLead.updated_at)}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* New Lead Modal */}
      <Modal
        isOpen={isNewLeadModalOpen}
        onClose={() => setIsNewLeadModalOpen(false)}
        title="Add New Lead"
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setIsNewLeadModalOpen(false)}>
              Cancel
            </Button>
            <Button>Create Lead</Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Lead creation form coming soon. This will include fields for contact info,
            event details, and source tracking.
          </p>
        </div>
      </Modal>
    </div>
  );
}
