'use client';

import {
  AlertCircle,
  Calendar,
  CheckCircle,
  ExternalLink,
  Gift,
  Meh,
  MessageSquare,
  Star,
  ThumbsDown,
  ThumbsUp,
  User,
} from 'lucide-react';
import { useMemo,useState } from 'react';

import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { FilterBar, FilterDefinition } from '@/components/ui/filter-bar';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ConfirmModal,Modal } from '@/components/ui/modal';
import { StatsCard } from '@/components/ui/stats-card';
import { useToast } from '@/components/ui/Toast';
import {
  useEscalatedReviews,
  useFilters,
  usePagination,
  useReviewAnalytics,
  useReviews,
  useSearch,
} from '@/hooks/useApi';
import { api } from '@/lib/api';

// Tab types
type ReviewTab = 'all' | 'escalated' | 'resolved';

export default function ReviewsPage() {
  // Hooks
  const toast = useToast();

  // State
  const [activeTab, setActiveTab] = useState<ReviewTab>('all');
  const [selectedReview, setSelectedReview] = useState<any>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [isIssueCouponOpen, setIsIssueCouponOpen] = useState(false);
  const [selectedReviewForCoupon, setSelectedReviewForCoupon] =
    useState<any>(null);
  const [isIssuingCoupon, setIsIssuingCoupon] = useState(false);
  const [isResolvingReview, setIsResolvingReview] = useState(false);

  // Pagination and filters
  const { page, limit, setPage, nextPage, prevPage } = usePagination(1, 20);
  const {
    query: searchQuery,
    debouncedQuery,
    setQuery: setSearchQuery,
  } = useSearch();
  const { filters, updateFilter, resetFilters } = useFilters({
    rating: '',
    sentiment: '',
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

  // Fetch data
  const {
    data: reviewsResponse,
    loading,
    error,
    refetch,
  } = useReviews(apiFilters);
  const { data: escalatedResponse, loading: escalatedLoading } =
    useEscalatedReviews();
  const { data: analyticsData } = useReviewAnalytics();

  const reviews = reviewsResponse?.data || [];
  const escalatedReviews = escalatedResponse?.data || [];
  const totalCount = reviewsResponse?.total_count || 0;

  // Calculate stats from analytics or reviews
  const stats = useMemo(() => {
    if (analyticsData) {
      return {
        avgRating: analyticsData.average_rating?.toFixed(1) || '0.0',
        totalReviews: analyticsData.total_reviews || 0,
        escalated: analyticsData.escalated_count || 0,
        positive: analyticsData.positive_count || 0,
      };
    }

    const avgRating =
      reviews.length > 0
        ? (
            reviews.reduce((sum: number, r: any) => sum + (r.rating || 0), 0) /
            reviews.length
          ).toFixed(1)
        : '0.0';

    return {
      avgRating,
      totalReviews: totalCount,
      escalated: escalatedReviews.length,
      positive: reviews.filter((r: any) => (r.rating || 0) >= 4).length,
    };
  }, [reviews, analyticsData, totalCount, escalatedReviews]);

  // Rating distribution (simplified)
  const ratingDistribution = useMemo(() => {
    const distribution = [0, 0, 0, 0, 0]; // 1-5 stars
    reviews.forEach((review: any) => {
      const rating = review.rating || 0;
      if (rating >= 1 && rating <= 5) {
        distribution[rating - 1]++;
      }
    });

    const maxCount = Math.max(...distribution, 1);

    return distribution.map((count, index) => ({
      stars: index + 1,
      count,
      percentage: reviews.length > 0 ? (count / reviews.length) * 100 : 0,
      barWidth: (count / maxCount) * 100,
    }));
  }, [reviews]);

  // Filter definitions
  const filterDefinitions: FilterDefinition[] = [
    {
      key: 'rating',
      label: 'All Ratings',
      options: [
        { label: '5 Stars', value: '5' },
        { label: '4 Stars', value: '4' },
        { label: '3 Stars', value: '3' },
        { label: '2 Stars', value: '2' },
        { label: '1 Star', value: '1' },
      ],
      value: filters.rating,
    },
    {
      key: 'sentiment',
      label: 'All Sentiment',
      options: [
        { label: 'Positive', value: 'positive' },
        { label: 'Neutral', value: 'neutral' },
        { label: 'Negative', value: 'negative' },
      ],
      value: filters.sentiment,
    },
  ];

  // Handlers
  const handleReviewClick = (review: any) => {
    setSelectedReview(review);
    setIsReviewModalOpen(true);
  };

  const handleIssueCoupon = (review: any) => {
    setSelectedReviewForCoupon(review);
    setIsIssueCouponOpen(true);
  };

  const handleConfirmCoupon = async () => {
    if (!selectedReviewForCoupon || isIssuingCoupon) return;
    
    setIsIssuingCoupon(true);
    try {
      const response = await api.post('/api/v1/reviews/ai/issue-coupon', {
        review_id: selectedReviewForCoupon.review_id,
        ai_interaction_notes: 'Admin manually issued coupon for negative experience',
        discount_percentage: 10,
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to issue coupon');
      }

      toast.success('Coupon Issued', 'Discount coupon has been created successfully');
      
      // Close modal and refresh
      setIsIssueCouponOpen(false);
      setSelectedReviewForCoupon(null);
      refetch();
    } catch (error) {
      console.error('Error issuing coupon:', error);
      toast.error(
        'Failed to Issue Coupon',
        error instanceof Error ? error.message : 'Please try again'
      );
    } finally {
      setIsIssuingCoupon(false);
    }
  };

  const handleResolve = async (review: any) => {
    if (!review?.review_id || isResolvingReview) return;
    
    setIsResolvingReview(true);
    try {
      const response = await api.post(`/api/v1/reviews/${review.review_id}/resolve`, {
        resolved_by: '00000000-0000-0000-0000-000000000000', // TODO: Get from auth context
        resolution_notes: 'Resolved by admin',
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to resolve review');
      }

      toast.success('Review Resolved', 'The review has been marked as resolved');
      
      // Close modal if open and refresh
      setIsReviewModalOpen(false);
      refetch();
    } catch (error) {
      console.error('Error resolving review:', error);
      toast.error(
        'Failed to Resolve Review',
        error instanceof Error ? error.message : 'Please try again'
      );
    } finally {
      setIsResolvingReview(false);
    }
  };

  const handleClearFilters = () => {
    resetFilters();
    setSearchQuery('');
    setPage(1);
  };

  // Get sentiment icon and color
  const getSentimentDisplay = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return {
          icon: ThumbsUp,
          color: 'text-green-600',
          bg: 'bg-green-50',
          label: 'Positive',
        };
      case 'negative':
        return {
          icon: ThumbsDown,
          color: 'text-red-600',
          bg: 'bg-red-50',
          label: 'Negative',
        };
      default:
        return {
          icon: Meh,
          color: 'text-gray-600',
          bg: 'bg-gray-50',
          label: 'Neutral',
        };
    }
  };

  // Render star rating
  const renderStars = (rating: number, size: 'sm' | 'md' | 'lg' = 'md') => {
    const sizeClasses = {
      sm: 'w-3 h-3',
      md: 'w-4 h-4',
      lg: 'w-5 h-5',
    };

    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(star => (
          <Star
            key={star}
            className={`${sizeClasses[size]} ${
              star <= rating
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
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

  // Get reviews based on active tab
  const displayReviews = useMemo(() => {
    switch (activeTab) {
      case 'escalated':
        return escalatedReviews;
      case 'resolved':
        return reviews.filter((r: any) => r.status === 'resolved');
      default:
        return reviews;
    }
  }, [activeTab, reviews, escalatedReviews]);

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <EmptyState
          icon={Star}
          title="Error Loading Reviews"
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
          <h1 className="text-3xl font-bold text-gray-900">
            Reviews & Feedback
          </h1>
          <p className="text-gray-600">
            Manage customer reviews and resolve issues
          </p>
        </div>
        <Button variant="outline">
          <ExternalLink className="w-4 h-4 mr-2" />
          View on Google
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Average Rating"
          value={`⭐ ${stats.avgRating}`}
          subtitle="out of 5.0"
          icon={Star}
          color="yellow"
        />
        <StatsCard
          title="Total Reviews"
          value={stats.totalReviews}
          icon={MessageSquare}
          color="blue"
        />
        <StatsCard
          title="Escalated Issues"
          value={stats.escalated}
          subtitle="needs attention"
          icon={AlertCircle}
          color="red"
        />
        <StatsCard
          title="Positive Reviews"
          value={stats.positive}
          subtitle={`${reviews.length > 0 ? ((stats.positive / reviews.length) * 100).toFixed(0) : 0}%`}
          icon={ThumbsUp}
          color="green"
        />
      </div>

      {/* Rating Distribution */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Rating Distribution
        </h3>
        <div className="space-y-2">
          {ratingDistribution.reverse().map(dist => (
            <div key={dist.stars} className="flex items-center gap-4">
              <div className="flex items-center gap-1 w-20">
                {renderStars(dist.stars, 'sm')}
              </div>
              <div className="flex-1">
                <div className="bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-yellow-400 h-4 rounded-full transition-all"
                    style={{ width: `${dist.barWidth}%` }}
                  />
                </div>
              </div>
              <div className="text-sm text-gray-600 w-20 text-right">
                {dist.count} ({dist.percentage.toFixed(0)}%)
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex gap-4 px-6">
            <button
              onClick={() => setActiveTab('all')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'all'
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              All Reviews ({reviews.length})
            </button>
            <button
              onClick={() => setActiveTab('escalated')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center ${
                activeTab === 'escalated'
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <AlertCircle className="w-4 h-4 mr-1" />
              Escalated ({escalatedReviews.length})
            </button>
            <button
              onClick={() => setActiveTab('resolved')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center ${
                activeTab === 'resolved'
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Resolved
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-6">
          <FilterBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            searchPlaceholder="Search reviews by customer name or booking..."
            filters={filterDefinitions}
            onFilterChange={(key, value) =>
              updateFilter(key as 'rating' | 'sentiment', value)
            }
            onClearFilters={handleClearFilters}
            showClearButton
          />
        </div>
      </div>

      {/* Loading State */}
      {loading && <LoadingSpinner message="Loading reviews..." />}

      {/* Empty State */}
      {!loading && displayReviews.length === 0 && (
        <EmptyState
          icon={Star}
          title={
            activeTab === 'escalated'
              ? 'No escalated issues'
              : activeTab === 'resolved'
                ? 'No resolved reviews'
                : 'No reviews found'
          }
          description={
            Object.values(filters).some(Boolean) || debouncedQuery
              ? 'Try adjusting your filters or search query'
              : 'Reviews will appear here once customers submit feedback'
          }
        />
      )}

      {/* Reviews List */}
      {!loading && displayReviews.length > 0 && (
        <div className="space-y-4">
          {displayReviews.map((review: any) => {
            const sentiment = getSentimentDisplay(review.sentiment);
            const SentimentIcon = sentiment.icon;

            return (
              <div
                key={review.review_id}
                className={`bg-white p-6 rounded-lg shadow border ${
                  review.is_escalated
                    ? 'border-red-300 border-l-4'
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Header */}
                    <div className="flex items-center gap-4 mb-3">
                      {renderStars(review.rating || 0, 'lg')}
                      {review.is_escalated && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-800">
                          <AlertCircle className="w-3 h-3 mr-1" />
                          ESCALATED
                        </span>
                      )}
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${sentiment.bg} ${sentiment.color}`}
                      >
                        <SentimentIcon className="w-3 h-3 mr-1" />
                        {sentiment.label}
                      </span>
                    </div>

                    {/* Customer Info */}
                    <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
                      <span className="flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        {review.customer_name || 'Anonymous'}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {formatDate(review.created_at)}
                      </span>
                      {review.booking_id && (
                        <span className="text-blue-600">
                          Booking #{review.booking_id}
                        </span>
                      )}
                    </div>

                    {/* Review Text */}
                    {review.review_text && (
                      <p className="text-gray-700 mb-4">{review.review_text}</p>
                    )}

                    {/* Issue Details (if escalated) */}
                    {review.is_escalated && review.issue_description && (
                      <div className="mt-4 p-4 bg-red-50 rounded border border-red-200">
                        <h4 className="text-sm font-semibold text-red-900 mb-1">
                          Issue Reported:
                        </h4>
                        <p className="text-sm text-red-800">
                          {review.issue_description}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReviewClick(review)}
                    >
                      View Full
                    </Button>
                    {review.is_escalated && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleIssueCoupon(review)}
                        >
                          <Gift className="w-4 h-4 mr-1" />
                          Issue Coupon
                        </Button>
                        <Button size="sm" onClick={() => handleResolve(review)}>
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Resolve
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Review Detail Modal */}
      {selectedReview && (
        <Modal
          isOpen={isReviewModalOpen}
          onClose={() => setIsReviewModalOpen(false)}
          title="Review Details"
          size="lg"
          footer={
            <>
              <Button
                variant="outline"
                onClick={() => setIsReviewModalOpen(false)}
              >
                Close
              </Button>
              {selectedReview.is_escalated && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsReviewModalOpen(false);
                      handleIssueCoupon(selectedReview);
                    }}
                  >
                    <Gift className="w-4 h-4 mr-2" />
                    Issue Coupon
                  </Button>
                  <Button onClick={() => handleResolve(selectedReview)}>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Mark Resolved
                  </Button>
                </>
              )}
            </>
          }
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>{renderStars(selectedReview.rating || 0, 'lg')}</div>
              <span className="text-sm text-gray-600">
                {formatDate(selectedReview.created_at)}
              </span>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">
                Customer
              </h4>
              <p className="text-gray-900">
                {selectedReview.customer_name || 'Anonymous'}
              </p>
              {selectedReview.booking_id && (
                <p className="text-sm text-gray-600">
                  Booking #{selectedReview.booking_id}
                </p>
              )}
            </div>

            {selectedReview.review_text && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-1">
                  Review
                </h4>
                <p className="text-gray-900">{selectedReview.review_text}</p>
              </div>
            )}

            {selectedReview.is_escalated &&
              selectedReview.issue_description && (
                <div className="p-4 bg-red-50 rounded border border-red-200">
                  <h4 className="text-sm font-semibold text-red-900 mb-1">
                    Issue Description
                  </h4>
                  <p className="text-red-800">
                    {selectedReview.issue_description}
                  </p>
                </div>
              )}

            {selectedReview.photos && selectedReview.photos.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">
                  Photos
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  {selectedReview.photos.map((photo: string, index: number) => (
                    <img
                      key={index}
                      src={photo}
                      alt={`Review photo ${index + 1}`}
                      className="w-full h-24 object-cover rounded"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Issue Coupon Confirmation */}
      <ConfirmModal
        isOpen={isIssueCouponOpen}
        onClose={() => !isIssuingCoupon && setIsIssueCouponOpen(false)}
        onConfirm={handleConfirmCoupon}
        title="Issue Apology Coupon"
        message={`Are you sure you want to issue an AI-generated apology coupon for this review? The system will automatically determine the appropriate discount amount.`}
        confirmLabel={isIssuingCoupon ? 'Issuing...' : 'Issue Coupon'}
        variant="info"
        loading={isIssuingCoupon}
      />
    </div>
  );
}
