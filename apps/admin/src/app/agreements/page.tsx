'use client';

import {
  Calendar,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Copy,
  ExternalLink,
  FileCheck,
  FileSignature,
  Link as LinkIcon,
  Mail,
  Phone,
  RefreshCcw,
  Search,
  Send,
  User,
} from 'lucide-react';
import { useCallback, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/Toast';
import {
  usePagination,
  useSearch,
  useSignedAgreements,
  useSlotHolds,
} from '@/hooks/useApi';
import {
  agreementService,
  type GenerateLinkRequest,
  type SignedAgreementDetail,
} from '@/services/api';

export default function AgreementsPage() {
  const toast = useToast();

  // Tab state
  const [activeTab, setActiveTab] = useState<'signed' | 'pending' | 'generate'>(
    'signed'
  );

  // Pagination state
  const { page, limit, setPage, nextPage, prevPage } = usePagination(1, 20);

  // Search state
  const { query: searchQuery, debouncedQuery, setQuery: setSearchQuery } = useSearch();

  // Modal state
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedAgreement, setSelectedAgreement] =
    useState<SignedAgreementDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Generate link state
  const [generateForm, setGenerateForm] = useState<GenerateLinkRequest>({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    event_date: '',
    time_slot: '12:00 PM',
  });
  const [generatedLink, setGeneratedLink] = useState<{
    url: string;
    expires: string;
    holdId: string;
  } | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSendingLink, setIsSendingLink] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  // Combine filters for API
  const apiFilters = useMemo(
    () => ({
      page,
      limit,
      search: debouncedQuery,
    }),
    [page, limit, debouncedQuery]
  );

  // Fetch data
  const {
    data: agreementsData,
    loading: agreementsLoading,
    error: agreementsError,
    refetch: refetchAgreements,
  } = useSignedAgreements(apiFilters);

  const {
    data: holdsData,
    loading: holdsLoading,
    refetch: refetchHolds,
  } = useSlotHolds(false);

  const agreements = agreementsData?.agreements || [];
  const totalAgreements = agreementsData?.total || 0;
  const totalPages = Math.ceil(totalAgreements / limit);

  const holds = holdsData?.holds || [];

  // Format date
  const formatDate = useCallback((dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }, []);

  // Format datetime
  const formatDateTime = useCallback((dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  }, []);

  // View agreement detail
  const handleViewAgreement = async (agreementId: string) => {
    setLoadingDetail(true);
    setIsDetailModalOpen(true);
    try {
      const response = await agreementService.getSignedAgreement(agreementId);
      if (response.success && response.data) {
        setSelectedAgreement(response.data);
      } else {
        throw new Error('Failed to load agreement details');
      }
    } catch (error) {
      console.error('Error loading agreement:', error);
      toast.error('Error', 'Failed to load agreement details');
      setIsDetailModalOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Copy link to clipboard
  const handleCopyLink = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedLink(true);
      toast.success('Copied!', 'Signing link copied to clipboard');
      setTimeout(() => setCopiedLink(false), 2000);
    } catch {
      toast.error('Error', 'Failed to copy link');
    }
  };

  // Generate new signing link
  const handleGenerateLink = async () => {
    if (
      !generateForm.customer_name ||
      !generateForm.customer_email ||
      !generateForm.customer_phone ||
      !generateForm.event_date
    ) {
      toast.error('Error', 'Please fill in all required fields');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await agreementService.generateLink(generateForm);
      if (response.success && response.data) {
        setGeneratedLink({
          url: response.data.signing_url,
          expires: response.data.expires_at,
          holdId: response.data.slot_hold_id,
        });
        toast.success('Success', 'Signing link generated successfully');
        refetchHolds();
      } else {
        throw new Error('Failed to generate link');
      }
    } catch (error) {
      console.error('Error generating link:', error);
      toast.error('Error', 'Failed to generate signing link');
    } finally {
      setIsGenerating(false);
    }
  };

  // Send link via SMS/email
  const handleSendLink = async (holdId: string, channel: 'sms' | 'email' | 'both') => {
    setIsSendingLink(true);
    try {
      const response = await agreementService.sendLink({
        slot_hold_id: holdId,
        channel,
      });
      if (response.success) {
        toast.success('Sent!', `Signing link sent via ${channel}`);
      } else {
        throw new Error('Failed to send link');
      }
    } catch (error) {
      console.error('Error sending link:', error);
      toast.error('Error', 'Failed to send signing link');
    } finally {
      setIsSendingLink(false);
    }
  };

  // Reset generate form
  const handleResetForm = () => {
    setGenerateForm({
      customer_name: '',
      customer_email: '',
      customer_phone: '',
      event_date: '',
      time_slot: '12:00 PM',
    });
    setGeneratedLink(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Agreement Management
          </h1>
          <p className="text-gray-600">
            View signed agreements, manage pending signatures, and generate
            signing links
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('signed')}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'signed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              <FileCheck className="h-4 w-4" />
              Signed Agreements
              {totalAgreements > 0 && (
                <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                  {totalAgreements}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('pending')}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              <Clock className="h-4 w-4" />
              Pending Signatures
              {holds.length > 0 && (
                <span className="ml-2 rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800">
                  {holds.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('generate')}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'generate'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              <LinkIcon className="h-4 w-4" />
              Generate Link
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'signed' && (
          <div className="rounded-lg bg-white shadow">
            {/* Search and filters */}
            <div className="border-b border-gray-200 p-4">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by customer name, email, or phone..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(1);
                    }}
                    className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <Button
                  onClick={() => refetchAgreements()}
                  variant="outline"
                  className="gap-2"
                >
                  <RefreshCcw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </div>

            {/* Table */}
            {agreementsLoading ? (
              <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
              </div>
            ) : agreementsError ? (
              <div className="p-8 text-center text-red-500">
                Error loading agreements. Please try again.
              </div>
            ) : agreements.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No signed agreements found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Customer
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Event Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Signed At
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Booking
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {agreements.map((agreement) => (
                      <tr
                        key={agreement.id}
                        className="hover:bg-gray-50"
                      >
                        <td className="whitespace-nowrap px-4 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                              <FileSignature className="h-5 w-5 text-green-600" />
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">
                                {agreement.customer_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {agreement.customer_email}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-500">
                          {formatDate(agreement.event_date)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-500">
                          {formatDateTime(agreement.signed_at)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4">
                          {agreement.booking_created ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                              <CheckCircle2 className="h-3 w-3" />
                              Created
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
                              Pending
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewAgreement(agreement.id)}
                          >
                            View Details
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
                <div className="text-sm text-gray-500">
                  Showing {(page - 1) * limit + 1} to{' '}
                  {Math.min(page * limit, totalAgreements)} of {totalAgreements}{' '}
                  agreements
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={prevPage}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="flex items-center px-2 text-sm">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={nextPage}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'pending' && (
          <div className="rounded-lg bg-white shadow">
            <div className="border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Active Slot Holds</h2>
                <Button
                  onClick={() => refetchHolds()}
                  variant="outline"
                  className="gap-2"
                >
                  <RefreshCcw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Slot holds waiting for customer signature (2-hour expiration)
              </p>
            </div>

            {holdsLoading ? (
              <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
              </div>
            ) : holds.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No active slot holds. Generate a signing link to create one.
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {holds.map((hold) => (
                  <div
                    key={hold.id}
                    className="p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100">
                          <Clock className="h-5 w-5 text-yellow-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {hold.customer_name || 'Unknown Customer'}
                          </div>
                          <div className="mt-1 flex items-center gap-4 text-sm text-gray-500">
                            {hold.customer_email && (
                              <span className="flex items-center gap-1">
                                <Mail className="h-3 w-3" />
                                {hold.customer_email}
                              </span>
                            )}
                            {hold.customer_phone && (
                              <span className="flex items-center gap-1">
                                <Phone className="h-3 w-3" />
                                {hold.customer_phone}
                              </span>
                            )}
                          </div>
                          <div className="mt-2 flex items-center gap-4 text-sm">
                            <span className="flex items-center gap-1 text-gray-600">
                              <Calendar className="h-3 w-3" />
                              {formatDate(hold.event_date)} at {hold.time_slot}
                            </span>
                            <span
                              className={`font-medium ${
                                hold.minutes_remaining < 30
                                  ? 'text-red-600'
                                  : 'text-yellow-600'
                              }`}
                            >
                              {hold.minutes_remaining} min remaining
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCopyLink(hold.signing_url)}
                          className="gap-1"
                        >
                          {copiedLink ? (
                            <Check className="h-3 w-3" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          Copy Link
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSendLink(hold.id, 'sms')}
                          disabled={isSendingLink || !hold.customer_phone}
                          className="gap-1"
                        >
                          <Phone className="h-3 w-3" />
                          SMS
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSendLink(hold.id, 'email')}
                          disabled={isSendingLink || !hold.customer_email}
                          className="gap-1"
                        >
                          <Mail className="h-3 w-3" />
                          Email
                        </Button>
                        <a
                          href={hold.signing_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Button variant="ghost" size="sm" className="gap-1">
                            <ExternalLink className="h-3 w-3" />
                            Open
                          </Button>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'generate' && (
          <div className="mx-auto max-w-2xl">
            <div className="rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-lg font-semibold">
                Generate Signing Link
              </h2>
              <p className="mb-6 text-sm text-gray-500">
                Create a signing link to share with the customer. The link will
                expire after 2 hours.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Customer Name *
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={generateForm.customer_name}
                      onChange={(e) =>
                        setGenerateForm({
                          ...generateForm,
                          customer_name: e.target.value,
                        })
                      }
                      placeholder="John Smith"
                      className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Customer Email *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="email"
                      value={generateForm.customer_email}
                      onChange={(e) =>
                        setGenerateForm({
                          ...generateForm,
                          customer_email: e.target.value,
                        })
                      }
                      placeholder="customer@example.com"
                      className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Customer Phone *
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="tel"
                      value={generateForm.customer_phone}
                      onChange={(e) =>
                        setGenerateForm({
                          ...generateForm,
                          customer_phone: e.target.value,
                        })
                      }
                      placeholder="+1 (555) 123-4567"
                      className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      Event Date *
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                      <input
                        type="date"
                        value={generateForm.event_date}
                        onChange={(e) =>
                          setGenerateForm({
                            ...generateForm,
                            event_date: e.target.value,
                          })
                        }
                        className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      Time Slot
                    </label>
                    <select
                      value={generateForm.time_slot}
                      onChange={(e) =>
                        setGenerateForm({
                          ...generateForm,
                          time_slot: e.target.value,
                        })
                      }
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="11:00 AM">11:00 AM</option>
                      <option value="12:00 PM">12:00 PM</option>
                      <option value="1:00 PM">1:00 PM</option>
                      <option value="2:00 PM">2:00 PM</option>
                      <option value="3:00 PM">3:00 PM</option>
                      <option value="4:00 PM">4:00 PM</option>
                      <option value="5:00 PM">5:00 PM</option>
                      <option value="6:00 PM">6:00 PM</option>
                      <option value="7:00 PM">7:00 PM</option>
                      <option value="8:00 PM">8:00 PM</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={handleGenerateLink}
                    disabled={isGenerating}
                    className="flex-1 gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <LinkIcon className="h-4 w-4" />
                        Generate Link
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleResetForm}
                    disabled={isGenerating}
                  >
                    Reset
                  </Button>
                </div>
              </div>

              {/* Generated Link Display */}
              {generatedLink && (
                <div className="mt-6 rounded-lg border border-green-200 bg-green-50 p-4">
                  <div className="mb-2 flex items-center gap-2 font-medium text-green-800">
                    <CheckCircle2 className="h-5 w-5" />
                    Signing Link Generated
                  </div>
                  <p className="mb-3 text-sm text-green-700">
                    Expires: {formatDateTime(generatedLink.expires)}
                  </p>

                  <div className="mb-4 flex gap-2">
                    <input
                      type="text"
                      value={generatedLink.url}
                      readOnly
                      className="flex-1 rounded-lg border border-green-300 bg-white px-3 py-2 text-sm"
                    />
                    <Button
                      variant="outline"
                      onClick={() => handleCopyLink(generatedLink.url)}
                      className="gap-1"
                    >
                      {copiedLink ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                      Copy
                    </Button>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendLink(generatedLink.holdId, 'sms')}
                      disabled={isSendingLink}
                      className="gap-1"
                    >
                      <Send className="h-3 w-3" />
                      Send SMS
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendLink(generatedLink.holdId, 'email')}
                      disabled={isSendingLink}
                      className="gap-1"
                    >
                      <Mail className="h-3 w-3" />
                      Send Email
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendLink(generatedLink.holdId, 'both')}
                      disabled={isSendingLink}
                      className="gap-1"
                    >
                      <Send className="h-3 w-3" />
                      Send Both
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Agreement Detail Modal */}
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title="Agreement Details"
        >
          {loadingDetail ? (
            <div className="flex h-48 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
            </div>
          ) : selectedAgreement ? (
            <div className="space-y-6">
              {/* Customer Info */}
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">
                  Customer Information
                </h3>
                <div className="rounded-lg bg-gray-50 p-4">
                  <div className="grid gap-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Name:</span>
                      <span className="font-medium">
                        {selectedAgreement.full_customer_name ||
                          selectedAgreement.customer_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Email:</span>
                      <span className="font-medium">
                        {selectedAgreement.full_customer_email ||
                          selectedAgreement.customer_email}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Phone:</span>
                      <span className="font-medium">
                        {selectedAgreement.full_customer_phone ||
                          selectedAgreement.customer_phone}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Signature Info */}
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">
                  Signature Details
                </h3>
                <div className="rounded-lg bg-gray-50 p-4">
                  <div className="grid gap-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Signed At:</span>
                      <span className="font-medium">
                        {formatDateTime(selectedAgreement.signed_at)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">IP Address:</span>
                      <span className="font-medium">
                        {selectedAgreement.signing_ip || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Template Version:</span>
                      <span className="font-medium">
                        {selectedAgreement.template_version}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Event Date:</span>
                      <span className="font-medium">
                        {formatDate(selectedAgreement.event_date)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Agreement Text */}
              {selectedAgreement.agreement_text && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-500">
                    Agreement Text (as signed)
                  </h3>
                  <div className="max-h-64 overflow-y-auto rounded-lg border bg-white p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {selectedAgreement.agreement_text}
                    </pre>
                  </div>
                </div>
              )}

              {/* Booking Status */}
              <div className="flex items-center justify-between rounded-lg border p-4">
                <span className="text-gray-600">Booking Status:</span>
                {selectedAgreement.booking_created ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
                    <CheckCircle2 className="h-4 w-4" />
                    Booking Created
                  </span>
                ) : (
                  <span className="inline-flex items-center rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800">
                    Pending Booking Creation
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              No agreement data available
            </div>
          )}
        </Modal>
      </div>
    </div>
  );
}
