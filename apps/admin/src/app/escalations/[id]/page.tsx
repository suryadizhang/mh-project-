'use client';

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Download,
  ExternalLink,
  Loader2,
  Mail,
  MessageSquare,
  Phone,
  PhoneCall,
  Play,
  Send,
  User,
} from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

interface Escalation {
  id: string;
  conversation_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  reason: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  method: 'phone' | 'email' | 'preferred_method';
  status:
    | 'pending'
    | 'assigned'
    | 'in_progress'
    | 'waiting_customer'
    | 'resolved'
    | 'closed'
    | 'error';
  assigned_to_id?: string;
  assigned_to?: {
    id: string;
    full_name: string;
    email: string;
  };
  sms_sent: boolean;
  call_initiated: boolean;
  escalated_at?: string;
  resolved_at?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
  escalation_metadata: {
    sms_messages?: Array<{
      message_id: string;
      from: string;
      to: string;
      text: string;
      direction: 'inbound' | 'outbound';
      timestamp: string;
      source?: 'admin_panel' | 'ringcentral_app';
      read_at?: string;
    }>;
    calls?: Array<{
      rc_call_id: string;
      from: string;
      to: string;
      started_at: string;
      ended_at?: string;
      duration?: number;
      status: string;
      has_recording?: boolean;
    }>;
    source?: string;
    timestamp?: string;
  };
}

interface CallRecording {
  id: string;
  rc_call_id: string;
  rc_recording_id: string;
  duration_seconds?: number;
  file_size_bytes?: number;
  s3_uri?: string;
  status:
    | 'pending'
    | 'downloading'
    | 'available'
    | 'archived'
    | 'deleted'
    | 'error';
  created_at: string;
}

export default function EscalationDetailPage() {
  const params = useParams();
  const escalationId = params?.id as string;

  const [escalation, setEscalation] = useState<Escalation | null>(null);
  const [recordings, setRecordings] = useState<CallRecording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // SMS composer
  const [smsMessage, setSmsMessage] = useState('');
  const [sendingSms, setSendingSms] = useState(false);
  const [smsError, setSmsError] = useState<string | null>(null);

  // Actions
  const [actionLoading, setActionLoading] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');

  // Fetch escalation details
  const fetchEscalation = async () => {
    try {
      const response = await fetch(`/api/v1/escalations/${escalationId}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Escalation not found');
        }
        throw new Error('Failed to fetch escalation');
      }

      const data = await response.json();
      setEscalation(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load escalation'
      );
    } finally {
      setLoading(false);
    }
  };

  // Fetch call recordings
  const fetchRecordings = async () => {
    if (!escalation) return;

    try {
      const response = await fetch(
        `/api/v1/escalations/${escalationId}/recordings`
      );
      if (response.ok) {
        const data = await response.json();
        setRecordings(data.recordings || []);
      }
    } catch (err) {
      console.error('Failed to fetch recordings:', err);
    }
  };

  useEffect(() => {
    if (escalationId) {
      fetchEscalation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [escalationId]);

  useEffect(() => {
    if (escalation) {
      fetchRecordings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [escalation]);

  // Send SMS
  const handleSendSms = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!smsMessage.trim() || !escalation) return;

    setSendingSms(true);
    setSmsError(null);

    try {
      const response = await fetch(`/api/v1/escalations/${escalationId}/sms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: smsMessage.trim(),
          metadata: {
            source: 'admin_panel',
            sent_at: new Date().toISOString(),
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to send SMS');
      }

      setSmsMessage('');
      await fetchEscalation(); // Refresh to show new message
    } catch (err) {
      setSmsError(err instanceof Error ? err.message : 'Failed to send SMS');
    } finally {
      setSendingSms(false);
    }
  };

  // Initiate call
  const handleInitiateCall = async () => {
    if (!escalation) return;

    setActionLoading(true);
    try {
      const response = await fetch(`/api/v1/escalations/${escalationId}/call`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to initiate call');
      }

      await fetchEscalation();
      alert('Call initiated! Check your RingCentral app.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to initiate call');
    } finally {
      setActionLoading(false);
    }
  };

  // Assign to me
  const handleAssignToMe = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(
        `/api/v1/escalations/${escalationId}/assign`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_id: 'current_admin_id', // TODO: Get from auth context
            notes: 'Self-assigned from admin panel',
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to assign escalation');

      await fetchEscalation();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to assign');
    } finally {
      setActionLoading(false);
    }
  };

  // Resolve escalation
  const handleResolve = async () => {
    if (!resolutionNotes.trim()) {
      alert('Please provide resolution notes');
      return;
    }

    setActionLoading(true);
    try {
      const response = await fetch(
        `/api/v1/escalations/${escalationId}/resolve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resolution_notes: resolutionNotes.trim(),
            resume_ai: true,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to resolve escalation');

      await fetchEscalation();
      setResolutionNotes('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to resolve');
    } finally {
      setActionLoading(false);
    }
  };

  // Priority styling
  const getPriorityStyle = (priority: Escalation['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  // Status styling
  const getStatusStyle = (status: Escalation['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'assigned':
        return 'bg-blue-100 text-blue-800';
      case 'in_progress':
        return 'bg-purple-100 text-purple-800';
      case 'waiting_customer':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-gray-100 text-gray-600';
      case 'error':
        return 'bg-red-100 text-red-800';
    }
  };

  // Format time
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading escalation...</p>
        </div>
      </div>
    );
  }

  if (error || !escalation) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <AlertCircle className="text-red-600" size={24} />
              <h2 className="text-lg font-semibold text-red-900">Error</h2>
            </div>
            <p className="text-red-700 mb-4">
              {error || 'Escalation not found'}
            </p>
            <Link
              href="/escalations"
              className="inline-flex items-center space-x-2 text-orange-600 hover:text-orange-700"
            >
              <ArrowLeft size={16} />
              <span>Back to Escalations</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const smsMessages = escalation.escalation_metadata.sms_messages || [];
  const calls = escalation.escalation_metadata.calls || [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/escalations"
            className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft size={20} />
            <span>Back to Escalations</span>
          </Link>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {escalation.customer_name}
                  </h1>
                  <span
                    className={`px-3 py-1 text-xs font-medium rounded-full border ${getPriorityStyle(escalation.priority)}`}
                  >
                    {escalation.priority.toUpperCase()}
                  </span>
                  <span
                    className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusStyle(escalation.status)}`}
                  >
                    {escalation.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Phone size={14} />
                    <span>{escalation.customer_phone}</span>
                  </div>
                  {escalation.customer_email && (
                    <div className="flex items-center space-x-1">
                      <Mail size={14} />
                      <span>{escalation.customer_email}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-1">
                    <Clock size={14} />
                    <span>Created: {formatTime(escalation.created_at)}</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center space-x-2">
                {escalation.status !== 'resolved' &&
                  escalation.status !== 'closed' && (
                    <>
                      <button
                        onClick={handleInitiateCall}
                        disabled={actionLoading}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                      >
                        <PhoneCall size={16} />
                        <span>Call Customer</span>
                      </button>
                      {!escalation.assigned_to_id && (
                        <button
                          onClick={handleAssignToMe}
                          disabled={actionLoading}
                          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                        >
                          <User size={16} />
                          <span>Assign to Me</span>
                        </button>
                      )}
                    </>
                  )}
              </div>
            </div>

            {/* Reason */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Escalation Reason:
              </h3>
              <p className="text-gray-900">{escalation.reason}</p>
            </div>

            {/* Assignment Info */}
            {escalation.assigned_to && (
              <div className="mt-4 flex items-center space-x-2 text-sm text-gray-600">
                <User size={16} />
                <span>
                  Assigned to:{' '}
                  <strong>{escalation.assigned_to.full_name}</strong>
                </span>
              </div>
            )}

            {/* Resolution Info */}
            {escalation.resolved_at && (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-green-800 mb-2">
                  <CheckCircle size={16} />
                  <span className="font-medium">
                    Resolved at {formatTime(escalation.resolved_at)}
                  </span>
                </div>
                {escalation.resolution_notes && (
                  <p className="text-sm text-green-700">
                    {escalation.resolution_notes}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Left Column - Communication History */}
          <div className="col-span-2 space-y-6">
            {/* SMS Thread */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <MessageSquare size={20} />
                <span>SMS Thread</span>
              </h2>

              {/* Messages */}
              <div className="space-y-3 mb-4 max-h-96 overflow-y-auto">
                {smsMessages.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    No SMS messages yet
                  </p>
                ) : (
                  smsMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-md rounded-lg p-3 ${
                          msg.direction === 'outbound'
                            ? 'bg-orange-100 text-gray-900'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <div className="flex items-start justify-between space-x-2 mb-1">
                          <p className="text-xs font-medium text-gray-600">
                            {msg.direction === 'outbound'
                              ? 'You'
                              : escalation.customer_name}
                          </p>
                          {msg.source && (
                            <span className="text-xs text-gray-500 flex items-center space-x-1">
                              {msg.source === 'admin_panel' ? (
                                <>
                                  <span>💻</span>
                                  <span>Panel</span>
                                </>
                              ) : (
                                <>
                                  <span>📱</span>
                                  <span>RC App</span>
                                </>
                              )}
                            </span>
                          )}
                        </div>
                        <p className="text-sm">{msg.text}</p>
                        <div className="flex items-center justify-between mt-2">
                          <p className="text-xs text-gray-500">
                            {formatTime(msg.timestamp)}
                          </p>
                          {msg.read_at && (
                            <span className="text-xs text-green-600 flex items-center space-x-1">
                              <CheckCircle size={12} />
                              <span>Read</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* SMS Composer */}
              {escalation.status !== 'resolved' &&
                escalation.status !== 'closed' && (
                  <form onSubmit={handleSendSms} className="border-t pt-4">
                    {smsError && (
                      <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        {smsError}
                      </div>
                    )}
                    <div className="flex items-end space-x-2">
                      <div className="flex-1">
                        <textarea
                          value={smsMessage}
                          onChange={e => setSmsMessage(e.target.value)}
                          placeholder="Type your message..."
                          rows={3}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                          disabled={sendingSms}
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={sendingSms || !smsMessage.trim()}
                        className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-fit"
                      >
                        {sendingSms ? (
                          <>
                            <Loader2 size={16} className="animate-spin" />
                            <span>Sending...</span>
                          </>
                        ) : (
                          <>
                            <Send size={16} />
                            <span>Send</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                )}
            </div>

            {/* Call Recordings */}
            {(calls.length > 0 || recordings.length > 0) && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                  <Phone size={20} />
                  <span>Call History & Recordings</span>
                </h2>

                <div className="space-y-3">
                  {calls.map((call, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <PhoneCall size={16} className="text-gray-600" />
                          <span className="text-sm font-medium text-gray-900">
                            Call {call.status}
                          </span>
                        </div>
                        {call.duration && (
                          <span className="text-sm text-gray-600">
                            Duration: {formatDuration(call.duration)}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <p>Started: {formatTime(call.started_at)}</p>
                        {call.ended_at && (
                          <p>Ended: {formatTime(call.ended_at)}</p>
                        )}
                      </div>

                      {/* Recording Player */}
                      {call.has_recording && (
                        <div className="mt-3 bg-gray-50 rounded p-3">
                          <p className="text-xs text-gray-600 mb-2">
                            Recording available
                          </p>
                          <div className="flex items-center space-x-2">
                            <button className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
                              <Play size={12} />
                              <span>Play</span>
                            </button>
                            <button className="flex items-center space-x-1 px-3 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700">
                              <Download size={12} />
                              <span>Download</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {recordings.length === 0 && calls.length === 0 && (
                    <p className="text-center text-gray-500 py-4">
                      No call history yet
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Actions & Info */}
          <div className="space-y-6">
            {/* Resolution Panel */}
            {escalation.status !== 'resolved' &&
              escalation.status !== 'closed' && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Resolve Escalation
                  </h3>
                  <textarea
                    value={resolutionNotes}
                    onChange={e => setResolutionNotes(e.target.value)}
                    placeholder="Enter resolution notes..."
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none mb-3"
                  />
                  <button
                    onClick={handleResolve}
                    disabled={actionLoading || !resolutionNotes.trim()}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    <CheckCircle size={16} />
                    <span>Mark as Resolved</span>
                  </button>
                </div>
              )}

            {/* Customer Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Customer Details
              </h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-gray-600">Name</p>
                  <p className="font-medium text-gray-900">
                    {escalation.customer_name}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Phone</p>
                  <p className="font-medium text-gray-900">
                    {escalation.customer_phone}
                  </p>
                </div>
                {escalation.customer_email && (
                  <div>
                    <p className="text-gray-600">Email</p>
                    <p className="font-medium text-gray-900">
                      {escalation.customer_email}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-gray-600">Preferred Method</p>
                  <p className="font-medium text-gray-900 capitalize">
                    {escalation.method.replace('_', ' ')}
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Escalation Info
              </h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-gray-600">Conversation ID</p>
                  <p className="font-mono text-xs text-gray-900 break-all">
                    {escalation.conversation_id}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Escalation ID</p>
                  <p className="font-mono text-xs text-gray-900 break-all">
                    {escalation.id}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Source</p>
                  <p className="font-medium text-gray-900">
                    {escalation.escalation_metadata.source || 'Unknown'}
                  </p>
                </div>
                {escalation.escalation_metadata.timestamp && (
                  <div>
                    <p className="text-gray-600">Submitted At</p>
                    <p className="text-gray-900">
                      {formatTime(escalation.escalation_metadata.timestamp)}
                    </p>
                  </div>
                )}
              </div>

              {/* View Original Chat */}
              <Link
                href={`/inbox?conversation=${escalation.conversation_id}`}
                className="mt-4 flex items-center justify-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
              >
                <ExternalLink size={16} />
                <span>View Original Chat</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
