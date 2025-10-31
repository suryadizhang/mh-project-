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
import {
  Star,
  MessageCircle,
  Clock,
  AlertTriangle,
  CheckCircle,
  Filter,
  Search,
  TrendingUp,
  TrendingDown,
  Eye,
  Flag,
  Calendar,
  BarChart3,
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

interface Review {
  id: string;
  platform: 'google' | 'yelp' | 'facebook';
  customer_name: string;
  rating: number;
  body: string;
  sentiment_score: number;
  sentiment_label: 'positive' | 'negative' | 'neutral';
  created_at: string;
  replied_at?: string;
  status: 'new' | 'acknowledged' | 'replied' | 'escalated' | 'resolved';
  priority: number;
  tags: string[];
  business_response?: string;
  needs_follow_up: boolean;
  escalation_reason?: string;
  assigned_to?: string;
  review_url: string;
}

interface ReviewMetrics {
  total_reviews: number;
  average_rating: number;
  sentiment_breakdown: {
    positive: number;
    negative: number;
    neutral: number;
  };
  response_rate: number;
  avg_response_time_hours: number;
  trend: {
    rating_change: number;
    volume_change: number;
  };
}

const PLATFORM_COLORS = {
  google: 'bg-green-100 text-green-800',
  yelp: 'bg-red-100 text-red-800',
  facebook: 'bg-blue-100 text-blue-800',
};

const STATUS_COLORS = {
  new: 'bg-blue-100 text-blue-800',
  acknowledged: 'bg-yellow-100 text-yellow-800',
  replied: 'bg-green-100 text-green-800',
  escalated: 'bg-red-100 text-red-800',
  resolved: 'bg-gray-100 text-gray-800',
};

const SENTIMENT_COLORS = {
  positive: 'bg-green-100 text-green-800',
  negative: 'bg-red-100 text-red-800',
  neutral: 'bg-gray-100 text-gray-800',
};

export function ReviewsBoard() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [metrics, setMetrics] = useState<ReviewMetrics | null>(null);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    platform: '',
    status: '',
    sentiment: '',
    rating: '',
    search: '',
    needs_follow_up: false,
    date_range: '30',
  });
  const [responseText, setResponseText] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [showResponseDialog, setShowResponseDialog] = useState(false);

  useEffect(() => {
    fetchReviews();
    fetchMetrics();
  }, [filters]);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      if (filters.platform) params.append('platforms', filters.platform);
      if (filters.status) params.append('statuses', filters.status);
      if (filters.sentiment) params.append('sentiment', filters.sentiment);
      if (filters.rating) params.append('min_rating', filters.rating);
      if (filters.search) params.append('search', filters.search);
      if (filters.needs_follow_up) params.append('needs_follow_up', 'true');
      if (filters.date_range) params.append('days_back', filters.date_range);

      const response = await fetch(
        `/api/admin/social/reviews?${params.toString()}`
      );
      const data = await response.json();

      if (data.success) {
        setReviews(data.data.reviews);
      }
    } catch (error) {
      console.error('Error fetching reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.date_range) params.append('days_back', filters.date_range);

      const response = await fetch(
        `/api/admin/social/analytics?${params.toString()}`
      );
      const data = await response.json();

      if (data.success) {
        setMetrics(data.data.reviews);
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const acknowledgeReview = async (reviewId: string) => {
    try {
      const response = await fetch(
        `/api/admin/social/review/${reviewId}/acknowledge`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            acknowledgment_note: 'Review acknowledged by admin',
          }),
        }
      );

      if (response.ok) {
        fetchReviews();
      }
    } catch (error) {
      console.error('Error acknowledging review:', error);
    }
  };

  const escalateReview = async (reviewId: string, reason: string) => {
    try {
      const response = await fetch(
        `/api/admin/social/review/${reviewId}/escalate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            escalation_reason: reason,
            priority_bump: 1,
          }),
        }
      );

      if (response.ok) {
        fetchReviews();
      }
    } catch (error) {
      console.error('Error escalating review:', error);
    }
  };

  const generateAiResponse = async (review: Review) => {
    try {
      setAiGenerating(true);
      const response = await fetch(
        `/api/admin/social/review/${review.id}/ai-response`,
        {
          method: 'POST',
        }
      );
      const data = await response.json();

      if (data.success) {
        setResponseText(data.data.response);
      }
    } catch (error) {
      console.error('Error generating AI response:', error);
    } finally {
      setAiGenerating(false);
    }
  };

  const submitResponse = async () => {
    if (!selectedReview || !responseText.trim()) return;

    try {
      const response = await fetch(
        `/api/admin/social/review/${selectedReview.id}/respond`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            response: responseText,
            requires_approval: false,
          }),
        }
      );

      if (response.ok) {
        setShowResponseDialog(false);
        setSelectedReview(null);
        setResponseText('');
        fetchReviews();
      }
    } catch (error) {
      console.error('Error submitting response:', error);
    }
  };

  const StarRating = ({
    rating,
    size = 'sm',
  }: {
    rating: number;
    size?: 'sm' | 'md';
  }) => {
    const starSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5';

    return (
      <div className="flex items-center">
        {[1, 2, 3, 4, 5].map(star => (
          <Star
            key={star}
            className={`${starSize} ${
              star <= rating
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  const ReviewCard = ({ review }: { review: Review }) => (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setSelectedReview(review)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Badge className={PLATFORM_COLORS[review.platform]}>
              {review.platform.toUpperCase()}
            </Badge>
            <Badge className={STATUS_COLORS[review.status]}>
              {review.status.toUpperCase()}
            </Badge>
            <Badge className={SENTIMENT_COLORS[review.sentiment_label]}>
              {review.sentiment_label.toUpperCase()}
            </Badge>
            {review.needs_follow_up && (
              <Badge variant="destructive">FOLLOW UP</Badge>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <StarRating rating={review.rating} />
            {review.priority <= 2 && (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            )}
          </div>
        </div>

        <div className="mb-3">
          <div className="font-medium text-sm mb-1">{review.customer_name}</div>
          <div className="text-sm text-gray-600 line-clamp-3">
            {review.body}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>
            {formatDistanceToNow(new Date(review.created_at), {
              addSuffix: true,
            })}
          </span>
          <div className="flex items-center space-x-2">
            {review.business_response ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <MessageCircle className="h-4 w-4 text-gray-400" />
            )}
            {review.escalation_reason && (
              <Flag className="h-4 w-4 text-red-500" />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const MetricsCard = ({
    title,
    value,
    change,
    icon: Icon,
  }: {
    title: string;
    value: string | number;
    change?: number;
    icon: React.ElementType;
  }) => (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {change !== undefined && (
              <div
                className={`flex items-center text-sm ${
                  change > 0
                    ? 'text-green-600'
                    : change < 0
                      ? 'text-red-600'
                      : 'text-gray-600'
                }`}
              >
                {change > 0 ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : change < 0 ? (
                  <TrendingDown className="h-4 w-4 mr-1" />
                ) : null}
                {change > 0 ? '+' : ''}
                {change}%
              </div>
            )}
          </div>
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Reviews Board</h1>
        <div className="flex items-center space-x-2">
          <Select
            value={filters.date_range}
            onValueChange={value =>
              setFilters({ ...filters, date_range: value })
            }
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 days</SelectItem>
              <SelectItem value="30">30 days</SelectItem>
              <SelectItem value="90">90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricsCard
            title="Total Reviews"
            value={metrics.total_reviews}
            change={metrics.trend.volume_change}
            icon={MessageCircle}
          />
          <MetricsCard
            title="Average Rating"
            value={metrics.average_rating.toFixed(1)}
            change={metrics.trend.rating_change}
            icon={Star}
          />
          <MetricsCard
            title="Response Rate"
            value={`${(metrics.response_rate * 100).toFixed(1)}%`}
            icon={CheckCircle}
          />
          <MetricsCard
            title="Avg Response Time"
            value={`${metrics.avg_response_time_hours.toFixed(1)}h`}
            icon={Clock}
          />
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Platform</label>
              <Select
                value={filters.platform}
                onValueChange={value =>
                  setFilters({ ...filters, platform: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All platforms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Platforms</SelectItem>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="yelp">Yelp</SelectItem>
                  <SelectItem value="facebook">Facebook</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Status</label>
              <Select
                value={filters.status}
                onValueChange={value =>
                  setFilters({ ...filters, status: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="replied">Replied</SelectItem>
                  <SelectItem value="escalated">Escalated</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">
                Sentiment
              </label>
              <Select
                value={filters.sentiment}
                onValueChange={value =>
                  setFilters({ ...filters, sentiment: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All sentiment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Sentiment</SelectItem>
                  <SelectItem value="positive">Positive</SelectItem>
                  <SelectItem value="negative">Negative</SelectItem>
                  <SelectItem value="neutral">Neutral</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Search</label>
              <Input
                placeholder="Search reviews..."
                value={filters.search}
                onChange={e =>
                  setFilters({ ...filters, search: e.target.value })
                }
              />
            </div>
          </div>

          <div className="flex items-center space-x-4 mt-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={filters.needs_follow_up}
                onChange={e =>
                  setFilters({ ...filters, needs_follow_up: e.target.checked })
                }
              />
              <span className="text-sm">Needs follow-up only</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Reviews Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-8">
            Loading reviews...
          </div>
        ) : reviews.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-500">
            No reviews found
          </div>
        ) : (
          reviews.map(review => <ReviewCard key={review.id} review={review} />)
        )}
      </div>

      {/* Review Detail Dialog */}
      <Dialog
        open={!!selectedReview}
        onOpenChange={open => !open && setSelectedReview(null)}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedReview && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Badge className={PLATFORM_COLORS[selectedReview.platform]}>
                    {selectedReview.platform.toUpperCase()}
                  </Badge>
                  <StarRating rating={selectedReview.rating} />
                  <span>{selectedReview.customer_name}</span>
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Badge className={STATUS_COLORS[selectedReview.status]}>
                    {selectedReview.status.toUpperCase()}
                  </Badge>
                  <Badge
                    className={SENTIMENT_COLORS[selectedReview.sentiment_label]}
                  >
                    {selectedReview.sentiment_label.toUpperCase()}
                  </Badge>
                  <span className="text-sm text-gray-500">
                    Priority: {selectedReview.priority}
                  </span>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Review Content</h4>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    {selectedReview.body}
                  </div>
                </div>

                <div className="text-sm text-gray-600">
                  Posted {format(new Date(selectedReview.created_at), 'PPP')}
                </div>

                {selectedReview.business_response && (
                  <div>
                    <h4 className="font-medium mb-2">Business Response</h4>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      {selectedReview.business_response}
                    </div>
                  </div>
                )}

                {selectedReview.escalation_reason && (
                  <div>
                    <h4 className="font-medium mb-2 text-red-600">
                      Escalation Reason
                    </h4>
                    <div className="p-3 bg-red-50 rounded-lg text-red-800">
                      {selectedReview.escalation_reason}
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => acknowledgeReview(selectedReview.id)}
                    disabled={selectedReview.status !== 'new'}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Acknowledge
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      escalateReview(
                        selectedReview.id,
                        'Manual escalation by admin'
                      )
                    }
                  >
                    <Flag className="h-4 w-4 mr-1" />
                    Escalate
                  </Button>

                  {!selectedReview.business_response && (
                    <Button
                      size="sm"
                      onClick={() => setShowResponseDialog(true)}
                    >
                      <MessageCircle className="h-4 w-4 mr-1" />
                      Respond
                    </Button>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      window.open(selectedReview.review_url, '_blank')
                    }
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    View Original
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Response Dialog */}
      <Dialog open={showResponseDialog} onOpenChange={setShowResponseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Respond to Review</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Response</label>
              <Textarea
                placeholder="Type your response..."
                value={responseText}
                onChange={e => setResponseText(e.target.value)}
                rows={4}
              />
            </div>

            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                onClick={() =>
                  selectedReview && generateAiResponse(selectedReview)
                }
                disabled={aiGenerating}
              >
                {aiGenerating ? 'Generating...' : 'Generate AI Response'}
              </Button>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setShowResponseDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={submitResponse}
                  disabled={!responseText.trim()}
                >
                  Send Response
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
