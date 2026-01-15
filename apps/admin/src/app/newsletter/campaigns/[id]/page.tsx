'use client';

import {
  AlertCircle,
  ArrowLeft,
  Edit,
  Eye,
  Mail,
  MousePointerClick,
  Send,
  Trash2,
  Users,
  UserX,
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { StatsCard } from '@/components/ui/stats-card';
import { tokenManager } from '@/services/api';

interface Campaign {
  id: number;
  name: string;
  subject: string;
  content: string;
  status: 'draft' | 'scheduled' | 'sent' | 'failed';
  scheduled_at?: string;
  sent_at?: string;
  total_recipients: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  created_at: string;
}

export default function CampaignDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Fetch campaign
  const fetchCampaign = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/newsletter/campaigns/${campaignId}`, {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      setCampaign(data);
    } catch (err: any) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  const handleSend = async () => {
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
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to send');

      alert('Campaign is being sent!');
      fetchCampaign();
    } catch (err) {
      console.error('Failed to send campaign:', err);
      alert('Failed to send campaign. Please try again.');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this campaign?')) return;

    try {
      const response = await fetch(`/api/newsletter/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete');

      router.push('/newsletter/campaigns');
    } catch (err) {
      console.error('Failed to delete campaign:', err);
      alert('Failed to delete campaign. Please try again.');
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="p-6">
        <EmptyState
          icon={Mail}
          title="Campaign not found"
          description="The campaign you're looking for doesn't exist or has been deleted."
          actionLabel="Go Back"
          onAction={() => router.push('/newsletter/campaigns')}
        />
      </div>
    );
  }

  const openRate =
    campaign.total_recipients > 0
      ? ((campaign.opened / campaign.total_recipients) * 100).toFixed(1)
      : '0.0';
  const clickRate =
    campaign.total_recipients > 0
      ? ((campaign.clicked / campaign.total_recipients) * 100).toFixed(1)
      : '0.0';
  const bounceRate =
    campaign.total_recipients > 0
      ? ((campaign.bounced / campaign.total_recipients) * 100).toFixed(1)
      : '0.0';
  const unsubscribeRate =
    campaign.total_recipients > 0
      ? ((campaign.unsubscribed / campaign.total_recipients) * 100).toFixed(1)
      : '0.0';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Link
            href="/newsletter/campaigns"
            className="mt-1 text-gray-400 hover:text-gray-600"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {campaign.name}
              </h1>
              <span
                className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(campaign.status)}`}
              >
                {campaign.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-600">{campaign.subject}</p>
            <p className="mt-1 text-sm text-gray-500">
              {campaign.sent_at
                ? `Sent on ${formatDate(campaign.sent_at)}`
                : campaign.scheduled_at
                  ? `Scheduled for ${formatDate(campaign.scheduled_at)}`
                  : `Created on ${formatDate(campaign.created_at)}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {campaign.status === 'draft' && (
            <>
              <Button
                variant="outline"
                onClick={() =>
                  router.push(`/newsletter/campaigns/${campaignId}/edit`)
                }
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button onClick={handleSend}>
                <Send className="w-4 h-4 mr-2" />
                Send Now
              </Button>
            </>
          )}
          <Button
            variant="outline"
            onClick={handleDelete}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Performance Stats (only for sent campaigns) */}
      {campaign.status === 'sent' && (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Recipients"
              value={campaign.total_recipients}
              icon={Users}
            />
            <StatsCard title="Open Rate" value={`${openRate}%`} icon={Eye} />
            <StatsCard
              title="Click Rate"
              value={`${clickRate}%`}
              icon={MousePointerClick}
            />
            <StatsCard
              title="Bounce Rate"
              value={`${bounceRate}%`}
              icon={AlertCircle}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            <div className="bg-white shadow sm:rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Opens</p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {campaign.opened.toLocaleString()}
                  </p>
                </div>
                <Eye className="w-8 h-8 text-blue-600" />
              </div>
            </div>

            <div className="bg-white shadow sm:rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Clicks</p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {campaign.clicked.toLocaleString()}
                  </p>
                </div>
                <MousePointerClick className="w-8 h-8 text-green-600" />
              </div>
            </div>

            <div className="bg-white shadow sm:rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    Unsubscribed
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {campaign.unsubscribed.toLocaleString()}
                  </p>
                </div>
                <UserX className="w-8 h-8 text-red-600" />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Content Preview */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Email Content</h2>
            <Button
              variant="outline"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? 'Show HTML' : 'Show Preview'}
            </Button>
          </div>

          {showPreview ? (
            <div
              className="border border-gray-300 rounded-lg p-6 bg-white"
              dangerouslySetInnerHTML={{ __html: campaign.content }}
            />
          ) : (
            <pre className="border border-gray-300 rounded-lg p-6 bg-gray-50 overflow-x-auto text-sm">
              <code>{campaign.content}</code>
            </pre>
          )}
        </div>
      </div>

      {/* Campaign Details */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Campaign Details
          </h2>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Campaign ID</dt>
              <dd className="mt-1 text-sm text-gray-900">{campaign.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(campaign.status)}`}
                >
                  {campaign.status}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">
                Subject Line
              </dt>
              <dd className="mt-1 text-sm text-gray-900">{campaign.subject}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">
                Total Recipients
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {campaign.total_recipients.toLocaleString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created At</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(campaign.created_at)}
              </dd>
            </div>
            {campaign.scheduled_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  Scheduled For
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatDate(campaign.scheduled_at)}
                </dd>
              </div>
            )}
            {campaign.sent_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Sent At</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatDate(campaign.sent_at)}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
}
