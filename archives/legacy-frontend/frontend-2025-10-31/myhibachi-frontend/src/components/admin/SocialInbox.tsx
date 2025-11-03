import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Instagram,
  Facebook,
  MessageCircle,
  Clock,
  User,
  Search,
  Filter,
  Send,
  Bot,
  CheckCircle,
  AlertTriangle,
  Eye,
  UserPlus,
  RefreshCw,
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

interface SocialThread {
  id: string;
  platform: 'instagram' | 'facebook' | 'google' | 'yelp';
  status: 'new' | 'pending' | 'resolved' | 'closed';
  priority: number;
  customer_name?: string;
  handle?: string;
  unread_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string;
  assigned_to?: string;
  tags: string[];
  latest_message?: {
    id: string;
    body: string;
    kind: string;
    direction: 'inbound' | 'outbound';
    created_at: string;
    sender_name: string;
  };
  customer_profile?: {
    id: string;
    name?: string;
    avatar?: string;
  };
}

interface SocialMessage {
  id: string;
  direction: 'inbound' | 'outbound';
  body: string;
  sender: string;
  created_at: string;
  kind: string;
}

interface ThreadDetail {
  thread: {
    id: string;
    platform: string;
    status: string;
    priority: number;
    created_at: string;
  };
  messages: SocialMessage[];
  customer_context: {
    name?: string;
    email?: string;
    phone?: string;
    social_handle?: string;
    linked: boolean;
  };
  conversation_summary: string;
}

const PLATFORM_ICONS = {
  instagram: Instagram,
  facebook: Facebook,
  google: MessageCircle,
  yelp: MessageCircle,
};

const PLATFORM_COLORS = {
  instagram: 'bg-pink-100 text-pink-800',
  facebook: 'bg-blue-100 text-blue-800',
  google: 'bg-green-100 text-green-800',
  yelp: 'bg-red-100 text-red-800',
};

const STATUS_COLORS = {
  new: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
};

export function SocialInbox() {
  const [threads, setThreads] = useState<SocialThread[]>([]);
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [threadDetail, setThreadDetail] = useState<ThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    platform: '',
    status: '',
    search: '',
    assigned_to: '',
    has_unread: false,
  });
  const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>({});
  const [replyText, setReplyText] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [showAiResponse, setShowAiResponse] = useState(false);
  const [aiResponse, setAiResponse] = useState<any>(null);

  useEffect(() => {
    fetchInbox();
    fetchUnreadCounts();
    // Set up polling for real-time updates
    const interval = setInterval(fetchUnreadCounts, 30000);
    return () => clearInterval(interval);
  }, [filters]);

  const fetchInbox = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      if (filters.platform) params.append('platforms', filters.platform);
      if (filters.status) params.append('statuses', filters.status);
      if (filters.search) params.append('search', filters.search);
      if (filters.assigned_to)
        params.append('assigned_to', filters.assigned_to);
      if (filters.has_unread) params.append('has_unread', 'true');

      const response = await fetch(
        `/api/admin/social/inbox?${params.toString()}`
      );
      const data = await response.json();

      if (data.success) {
        setThreads(data.data.threads);
      }
    } catch (error) {
      console.error('Error fetching inbox:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCounts = async () => {
    try {
      const response = await fetch('/api/admin/social/unread-counts');
      const data = await response.json();

      if (data.success) {
        setUnreadCounts(data.data.counts);
      }
    } catch (error) {
      console.error('Error fetching unread counts:', error);
    }
  };

  const fetchThreadDetail = async (threadId: string) => {
    try {
      const response = await fetch(`/api/admin/social/thread/${threadId}`);
      const data = await response.json();

      if (data.success) {
        setThreadDetail(data.data);
      }
    } catch (error) {
      console.error('Error fetching thread detail:', error);
    }
  };

  const handleThreadSelect = (threadId: string) => {
    setSelectedThread(threadId);
    setThreadDetail(null);
    fetchThreadDetail(threadId);
  };

  const generateAiResponse = async () => {
    if (!selectedThread) return;

    try {
      setAiGenerating(true);
      const response = await fetch(
        `/api/admin/social/thread/${selectedThread}/ai-response`,
        {
          method: 'POST',
        }
      );
      const data = await response.json();

      if (data.success) {
        setAiResponse(data.data);
        setShowAiResponse(true);
        setReplyText(data.data.response);
      }
    } catch (error) {
      console.error('Error generating AI response:', error);
    } finally {
      setAiGenerating(false);
    }
  };

  const sendReply = async () => {
    if (!selectedThread || !replyText.trim()) return;

    try {
      const response = await fetch(
        `/api/admin/social/thread/${selectedThread}/reply`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            body: replyText,
            reply_kind: 'dm',
            requires_approval: false,
            safety: {
              manual_review: true,
              approved_by_admin: true,
            },
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        setReplyText('');
        setShowAiResponse(false);
        setAiResponse(null);
        // Refresh thread detail
        fetchThreadDetail(selectedThread);
        fetchInbox(); // Refresh inbox
      }
    } catch (error) {
      console.error('Error sending reply:', error);
    }
  };

  const updateThreadStatus = async (threadId: string, status: string) => {
    try {
      const response = await fetch(
        `/api/admin/social/thread/${threadId}/status`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status,
            reason: `Status updated to ${status} by admin`,
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        fetchInbox(); // Refresh inbox
        if (selectedThread === threadId) {
          fetchThreadDetail(threadId); // Refresh thread detail
        }
      }
    } catch (error) {
      console.error('Error updating thread status:', error);
    }
  };

  const createLead = async (thread: SocialThread) => {
    try {
      const response = await fetch('/api/admin/social/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: thread.platform,
          thread_id: thread.id,
          handle: thread.handle,
          inferred_interest: 'general_inquiry',
          consent_dm: true,
          consent_sms: false,
          consent_email: false,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Show success message
        console.log('Lead created:', data.data);
      }
    } catch (error) {
      console.error('Error creating lead:', error);
    }
  };

  const ThreadItem = ({ thread }: { thread: SocialThread }) => {
    const PlatformIcon = PLATFORM_ICONS[thread.platform];

    return (
      <Card
        className={`cursor-pointer transition-all hover:shadow-md ${
          selectedThread === thread.id ? 'ring-2 ring-blue-500' : ''
        }`}
        onClick={() => handleThreadSelect(thread.id)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <div className="flex-shrink-0">
                <PlatformIcon className="h-5 w-5 text-gray-500" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <Badge className={PLATFORM_COLORS[thread.platform]}>
                    {thread.platform.toUpperCase()}
                  </Badge>
                  <Badge className={STATUS_COLORS[thread.status]}>
                    {thread.status.toUpperCase()}
                  </Badge>
                  {thread.unread_count > 0 && (
                    <Badge variant="destructive">{thread.unread_count}</Badge>
                  )}
                </div>

                <div className="text-sm font-medium text-gray-900 mb-1">
                  {thread.customer_name || thread.handle || 'Unknown Customer'}
                </div>

                {thread.latest_message && (
                  <div className="text-sm text-gray-600 truncate">
                    <span
                      className={`inline-block w-2 h-2 rounded-full mr-2 ${
                        thread.latest_message.direction === 'inbound'
                          ? 'bg-blue-400'
                          : 'bg-green-400'
                      }`}
                    ></span>
                    {thread.latest_message.body.length > 60
                      ? `${thread.latest_message.body.substring(0, 60)}...`
                      : thread.latest_message.body}
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end space-y-1">
              <div className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(thread.updated_at), {
                  addSuffix: true,
                })}
              </div>

              <div className="flex items-center space-x-1">
                {thread.priority <= 2 && (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                )}
                {thread.assigned_to && (
                  <User className="h-4 w-4 text-blue-500" />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Sidebar - Inbox List */}
      <div className="w-1/3 bg-white border-r">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Social Inbox</h2>
            <Button variant="ghost" size="sm" onClick={fetchInbox}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>

          {/* Filters */}
          <div className="space-y-2">
            <div className="flex space-x-2">
              <Select
                value={filters.platform}
                onValueChange={value =>
                  setFilters({ ...filters, platform: value })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Platforms</SelectItem>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="facebook">Facebook</SelectItem>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="yelp">Yelp</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={filters.status}
                onValueChange={value =>
                  setFilters({ ...filters, status: value })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Input
              placeholder="Search messages..."
              value={filters.search}
              onChange={e => setFilters({ ...filters, search: e.target.value })}
              className="w-full"
            />

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="unread"
                checked={filters.has_unread}
                onChange={e =>
                  setFilters({ ...filters, has_unread: e.target.checked })
                }
              />
              <label htmlFor="unread" className="text-sm">
                Show only unread
              </label>
            </div>
          </div>

          {/* Unread Counts */}
          <div className="flex space-x-2 mt-3">
            {Object.entries(unreadCounts).map(([platform, count]) => (
              <Badge
                key={platform}
                className={
                  PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS]
                }
              >
                {platform}: {count}
              </Badge>
            ))}
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-2">
            {loading ? (
              <div className="text-center py-8">Loading...</div>
            ) : threads.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No messages found
              </div>
            ) : (
              threads.map(thread => (
                <ThreadItem key={thread.id} thread={thread} />
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Right Panel - Thread Detail */}
      <div className="flex-1 flex flex-col">
        {selectedThread && threadDetail ? (
          <>
            {/* Thread Header */}
            <div className="p-4 border-b bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <Badge
                      className={
                        PLATFORM_COLORS[
                          threadDetail.thread
                            .platform as keyof typeof PLATFORM_COLORS
                        ]
                      }
                    >
                      {threadDetail.thread.platform.toUpperCase()}
                    </Badge>
                    <Badge
                      className={
                        STATUS_COLORS[
                          threadDetail.thread
                            .status as keyof typeof STATUS_COLORS
                        ]
                      }
                    >
                      {threadDetail.thread.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div>
                    <div className="font-medium">
                      {threadDetail.customer_context.name ||
                        threadDetail.customer_context.social_handle ||
                        'Unknown Customer'}
                    </div>
                    <div className="text-sm text-gray-500">
                      {threadDetail.conversation_summary}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const thread = threads.find(t => t.id === selectedThread);
                      if (thread) createLead(thread);
                    }}
                  >
                    <UserPlus className="h-4 w-4 mr-1" />
                    Create Lead
                  </Button>

                  <Select
                    value={threadDetail.thread.status}
                    onValueChange={value =>
                      updateThreadStatus(selectedThread, value)
                    }
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new">New</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                      <SelectItem value="closed">Closed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {threadDetail.messages.map(message => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.direction === 'outbound'
                        ? 'justify-end'
                        : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.direction === 'outbound'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      <div className="text-sm mb-1">
                        <strong>{message.sender}</strong>
                        <span className="ml-2 text-xs opacity-75">
                          {format(
                            new Date(message.created_at),
                            'MMM dd, HH:mm'
                          )}
                        </span>
                      </div>
                      <div>{message.body}</div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Reply Section */}
            <div className="p-4 border-t bg-white">
              {showAiResponse && aiResponse && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">
                        AI Generated Response
                      </span>
                      <Badge variant="outline">
                        Safety: {(aiResponse.safety_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAiResponse(false)}
                    >
                      ×
                    </Button>
                  </div>

                  <div className="text-sm text-blue-700 mb-2">
                    Scenario: {aiResponse.scenario} | Confidence:{' '}
                    {(aiResponse.confidence * 100).toFixed(0)}%
                  </div>

                  {aiResponse.safety_issues.length > 0 && (
                    <div className="mb-2">
                      <div className="text-sm text-red-600">Safety Issues:</div>
                      <ul className="text-xs text-red-600 ml-4">
                        {aiResponse.safety_issues.map(
                          (issue: string, idx: number) => (
                            <li key={idx}>• {issue}</li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  <div className="text-sm text-gray-600">
                    Suggested actions: {aiResponse.suggested_actions.join(', ')}
                  </div>
                </div>
              )}

              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <Textarea
                    placeholder="Type your reply..."
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    rows={3}
                    className="resize-none"
                  />
                </div>

                <div className="flex flex-col space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={generateAiResponse}
                    disabled={aiGenerating}
                  >
                    {aiGenerating ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                    AI
                  </Button>

                  <Button
                    size="sm"
                    onClick={sendReply}
                    disabled={!replyText.trim()}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a conversation to view details
          </div>
        )}
      </div>
    </div>
  );
}
