'use client';

import {
  Calendar,
  Copy,
  DollarSign,
  Edit,
  Eye,
  Mail,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  Trash2,
  Users,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect,useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Modal } from '@/components/ui/modal';
import { StatsCard } from '@/components/ui/stats-card';

interface Campaign {
  id: number;
  name: string;
  subject: string;
  content: string;
  status: 'draft' | 'scheduled' | 'sent' | 'failed' | 'active' | 'completed';
  channel: 'EMAIL' | 'SMS' | 'BOTH';
  scheduled_at?: string;
  sent_at?: string;
  total_recipients: number;
  // Email metrics (legacy)
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  // SMS metrics (new)
  total_sent?: number;
  total_delivered?: number;
  total_failed?: number;
  delivery_rate_cached?: number;
  cost_dollars?: number;
  created_at: string;
  last_metrics_updated?: string;
}

interface CampaignFormData {
  name: string;
  subject: string;
  content: string;
  scheduled_at?: string;
}

export default function NewsletterCampaignsPage() {
  // State
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'ai'>(
    'create'
  );
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(
    null
  );
  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    subject: '',
    content: '',
    scheduled_at: '',
  });
    const [campaigns, setCampaigns] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');

  // Fetch campaigns
  const fetchCampaigns = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/newsletter/campaigns', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      setCampaigns(data);
    } catch (err: unknown) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  // Stats calculations
  const stats = campaigns
    ? {
        total: campaigns.campaigns?.length || 0,
        sent:
          campaigns.campaigns?.filter((c: Campaign) => c.status === 'sent')
            .length || 0,
        scheduled:
          campaigns.campaigns?.filter((c: Campaign) => c.status === 'scheduled')
            .length || 0,
        drafts:
          campaigns.campaigns?.filter((c: Campaign) => c.status === 'draft')
            .length || 0,
      }
    : { total: 0, sent: 0, scheduled: 0, drafts: 0 };

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setFormData({
      name: '',
      subject: '',
      content: '',
      scheduled_at: '',
    });
    setSelectedCampaign(null);
    setShowModal(true);
  };

  const handleEdit = (campaign: Campaign) => {
    setModalMode('edit');
    setFormData({
      name: campaign.name,
      subject: campaign.subject,
      content: campaign.content,
      scheduled_at: campaign.scheduled_at || '',
    });
    setSelectedCampaign(campaign);
    setShowModal(true);
  };

  const handleAIGenerate = () => {
    setModalMode('ai');
    setAiPrompt('');
    setShowModal(true);
  };

  const handleGenerateAIContent = async () => {
    if (!aiPrompt.trim()) return;

    try {
      setAiGenerating(true);
      const response = await fetch('/api/newsletter/campaigns/ai-content', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: aiPrompt }),
      });

      if (!response.ok) throw new Error('Failed to generate content');

      const data = await response.json();
      setFormData({
        name: data.name || '',
        subject: data.subject || '',
        content: data.content || '',
        scheduled_at: '',
      });
      setModalMode('create');
      setAiPrompt('');
    } catch (err) {
      console.error('Failed to generate AI content:', err);
      alert('Failed to generate content. Please try again.');
    } finally {
      setAiGenerating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const url =
        modalMode === 'edit' && selectedCampaign
          ? `/api/newsletter/campaigns/${selectedCampaign.id}`
          : '/api/newsletter/campaigns';

      const response = await fetch(url, {
        method: modalMode === 'edit' ? 'PUT' : 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to save');

      setShowModal(false);
      fetchCampaigns();
    } catch (err) {
      console.error('Failed to save campaign:', err);
      alert('Failed to save campaign. Please try again.');
    }
  };

  const handleDelete = async (campaignId: number) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return;

    try {
      const response = await fetch(`/api/newsletter/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete');

      fetchCampaigns();
    } catch (err) {
      console.error('Failed to delete campaign:', err);
      alert('Failed to delete campaign. Please try again.');
    }
  };

  const handleSend = async (campaignId: number) => {
    if (
      !confirm(
        'Are you sure you want to send this campaign to all subscribers?'
      )
    )
      return;

    try {
      const response = await fetch(
        `/api/newsletter/campaigns/${campaignId}/send`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to send');

      alert('Campaign is being sent!');
      fetchCampaigns();
    } catch (err) {
      console.error('Failed to send campaign:', err);
      alert('Failed to send campaign. Please try again.');
    }
  };

  const handleDuplicate = async (campaign: Campaign) => {
    try {
      const response = await fetch('/api/newsletter/campaigns', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: `${campaign.name} (Copy)`,
          subject: campaign.subject,
          content: campaign.content,
        }),
      });

      if (!response.ok) throw new Error('Failed to duplicate');

      fetchCampaigns();
    } catch (err) {
      console.error('Failed to duplicate campaign:', err);
      alert('Failed to duplicate campaign. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent':
        return 'bg-green-100 text-green-800';
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (error) {
    return (
      <div className="p-6">
        <EmptyState
          icon={Mail}
          title="Failed to load campaigns"
          description="There was an error loading the campaigns. Please try again."
          actionLabel="Retry"
          onAction={fetchCampaigns}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Newsletter Campaigns
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Create and manage SMS and email campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleAIGenerate}>
            <Sparkles className="w-4 h-4 mr-2" />
            AI Generate
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="w-4 h-4 mr-2" />
            New Campaign
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Total Campaigns" value={stats.total} icon={Mail} />
        <StatsCard title="Sent" value={stats.sent} icon={Send} />
        <StatsCard title="Scheduled" value={stats.scheduled} icon={Calendar} />
        <StatsCard title="Drafts" value={stats.drafts} icon={Edit} />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      ) : !campaigns?.campaigns || campaigns.campaigns.length === 0 ? (
        <EmptyState
          icon={Mail}
          title="No campaigns yet"
          description="Create your first email campaign or generate one with AI"
          actionLabel="Create Campaign"
          onAction={handleCreate}
        />
      ) : (
        <div className="bg-white shadow sm:rounded-lg">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.campaigns.map((campaign: Campaign) => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <Link
                          href={`/newsletter/campaigns/${campaign.id}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {campaign.name}
                        </Link>
                        <span className="text-sm text-gray-500">
                          {campaign.subject}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        campaign.channel === 'SMS' ? 'bg-blue-100 text-blue-800' :
                        campaign.channel === 'EMAIL' ? 'bg-purple-100 text-purple-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {campaign.channel === 'SMS' && <MessageSquare className="w-3 h-3 mr-1" />}
                        {campaign.channel === 'EMAIL' && <Mail className="w-3 h-3 mr-1" />}
                        {campaign.channel}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(campaign.status)}`}
                      >
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.total_recipients.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      {campaign.channel === 'SMS' && campaign.status === 'sent' ? (
                        <div className="text-sm">
                          <div className="flex flex-col gap-1">
                            <span className="text-gray-600">
                              <Send className="w-4 h-4 inline mr-1" />
                              {campaign.total_sent || 0} sent
                            </span>
                            <span className={`${
                              (campaign.delivery_rate_cached || 0) >= 95 ? 'text-green-600' : 'text-yellow-600'
                            }`}>
                              <MessageSquare className="w-4 h-4 inline mr-1" />
                              {(campaign.delivery_rate_cached || 0).toFixed(1)}% delivered
                            </span>
                            {(campaign.total_failed || 0) > 0 && (
                              <span className="text-red-600 text-xs">
                                {campaign.total_failed} failed
                              </span>
                            )}
                          </div>
                        </div>
                      ) : campaign.status === 'sent' ? (
                        <div className="text-sm">
                          <div className="flex items-center gap-4">
                            <span className="text-gray-600">
                              <Eye className="w-4 h-4 inline mr-1" />
                              {campaign.total_recipients > 0
                                ? (
                                    (campaign.opened /
                                      campaign.total_recipients) *
                                    100
                                  ).toFixed(1)
                                : 0}
                              %
                            </span>
                            <span className="text-gray-600">
                              <Users className="w-4 h-4 inline mr-1" />
                              {campaign.total_recipients > 0
                                ? (
                                    (campaign.clicked /
                                      campaign.total_recipients) *
                                    100
                                  ).toFixed(1)
                                : 0}
                              %
                            </span>
                          </div>
                        </div>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {campaign.channel === 'SMS' && campaign.cost_dollars !== undefined ? (
                        <span className="text-gray-900 font-medium">
                          <DollarSign className="w-4 h-4 inline" />
                          {campaign.cost_dollars.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {campaign.sent_at
                        ? formatDate(campaign.sent_at)
                        : campaign.scheduled_at
                          ? formatDate(campaign.scheduled_at)
                          : formatDate(campaign.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/newsletter/campaigns/${campaign.id}`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        {campaign.status === 'draft' && (
                          <>
                            <button
                              onClick={() => handleEdit(campaign)}
                              className="text-gray-600 hover:text-gray-900"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleSend(campaign.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              <Send className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDuplicate(campaign)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(campaign.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && modalMode !== 'ai' && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={modalMode === 'edit' ? 'Edit Campaign' : 'Create Campaign'}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Campaign Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={e =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject Line
              </label>
              <input
                type="text"
                value={formData.subject}
                onChange={e =>
                  setFormData({ ...formData, subject: e.target.value })
                }
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Content
              </label>
              <textarea
                value={formData.content}
                onChange={e =>
                  setFormData({ ...formData, content: e.target.value })
                }
                rows={10}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-mono"
                placeholder="Enter HTML content or plain text..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Schedule For (Optional)
              </label>
              <input
                type="datetime-local"
                value={formData.scheduled_at}
                onChange={e =>
                  setFormData({ ...formData, scheduled_at: e.target.value })
                }
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                {modalMode === 'edit' ? 'Update' : 'Create'} Campaign
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* AI Generation Modal */}
      {showModal && modalMode === 'ai' && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title="AI Content Generation"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Describe your campaign
              </label>
              <textarea
                value={aiPrompt}
                onChange={e => setAiPrompt(e.target.value)}
                rows={6}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="e.g., Create a summer promotion email for our hibachi catering service with a 15% discount..."
              />
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowModal(false)}
                disabled={aiGenerating}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleGenerateAIContent}
                disabled={!aiPrompt.trim() || aiGenerating}
              >
                {aiGenerating ? (
                  <>
                    <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Content
                  </>
                )}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
