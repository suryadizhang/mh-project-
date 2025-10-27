/**
 * Admin Review Moderation Panel
 * View and moderate pending customer reviews
 *
 * Features:
 * - FIFO queue (oldest pending first)
 * - Image + video preview gallery
 * - Approve/reject buttons with confirmation
 * - Bulk actions (select multiple)
 * - Customer details context
 * - Real-time count updates
 * - Pagination (20 per page)
 */

'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';

// ============================================================================
// Types
// ============================================================================

interface MediaItem {
  url: string;
  thumbnail: string;
  resource_type: 'image' | 'video';
  width: number;
  height: number;
  format: string;
}

interface PendingReview {
  id: number;
  title: string;
  content: string;
  rating: number;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  images: MediaItem[];
  google_review_url?: string;
  yelp_review_url?: string;
  status: string;
  created_at: string;
  has_external_reviews: boolean;
  media_count: number;
  image_count: number;
  video_count: number;
}

// ============================================================================
// Main Component
// ============================================================================

export default function PendingReviewsList() {
  // Data state
  const [reviews, setReviews] = useState<PendingReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // UI state
  const [selectedReviews, setSelectedReviews] = useState<Set<number>>(new Set());
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReviewId, setRejectReviewId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());
  const [expandedReviewId, setExpandedReviewId] = useState<number | null>(null);
  const [selectedMediaPreview, setSelectedMediaPreview] = useState<MediaItem | null>(null);

  // Mock admin ID (in real app, get from auth context)
  const adminId = 1;

  // ============================================================================
  // Data Fetching
  // ============================================================================

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/review-moderation/pending-reviews?page=${page}&limit=20`
      );
      const data = await response.json();

      if (data.success) {
        setReviews(data.data);
        setTotalPages(data.pagination.total_pages);
        setTotalCount(data.pagination.total);
      }
    } catch (error) {
      console.error('Error fetching reviews:', error);
      alert('Failed to load reviews');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [page]);

  // ============================================================================
  // Action Handlers
  // ============================================================================

  const handleApprove = async (reviewId: number) => {
    if (!confirm('Approve this review and make it public?')) return;

    setProcessingIds(new Set([...processingIds, reviewId]));

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/review-moderation/approve-review/${reviewId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_id: adminId,
            comment: 'Approved from admin panel',
            notify_customer: true,
          }),
        }
      );

      if (response.ok) {
        alert('Review approved successfully!');
        fetchReviews(); // Refresh list
        setSelectedReviews(new Set()); // Clear selection
      } else {
        throw new Error('Failed to approve');
      }
    } catch (error) {
      console.error('Approve error:', error);
      alert('Failed to approve review');
    } finally {
      const newProcessing = new Set(processingIds);
      newProcessing.delete(reviewId);
      setProcessingIds(newProcessing);
    }
  };

  const handleReject = async () => {
    if (!rejectReviewId || !rejectReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    setProcessingIds(new Set([...processingIds, rejectReviewId]));

    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/review-moderation/reject-review/${rejectReviewId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_id: adminId,
            reason: rejectReason,
            notify_customer: true,
          }),
        }
      );

      if (response.ok) {
        alert('Review rejected successfully!');
        setShowRejectModal(false);
        setRejectReviewId(null);
        setRejectReason('');
        fetchReviews(); // Refresh list
        setSelectedReviews(new Set()); // Clear selection
      } else {
        throw new Error('Failed to reject');
      }
    } catch (error) {
      console.error('Reject error:', error);
      alert('Failed to reject review');
    } finally {
      const newProcessing = new Set(processingIds);
      newProcessing.delete(rejectReviewId);
      setProcessingIds(newProcessing);
    }
  };

  const handleBulkAction = async (action: 'approve' | 'reject') => {
    if (selectedReviews.size === 0) {
      alert('Please select reviews first');
      return;
    }

    let reason = '';
    if (action === 'reject') {
      reason = prompt('Enter rejection reason for all selected reviews:') || '';
      if (!reason.trim()) {
        alert('Rejection reason is required');
        return;
      }
    }

    if (!confirm(`${action === 'approve' ? 'Approve' : 'Reject'} ${selectedReviews.size} reviews?`)) {
      return;
    }

    try {
      const response = await fetch(
        'http://localhost:8000/api/admin/review-moderation/bulk-action',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            review_ids: Array.from(selectedReviews),
            action,
            admin_id: adminId,
            reason,
            notify_customers: true,
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        alert(
          `Bulk action completed!\nSuccess: ${data.data.success_count}\nFailed: ${data.data.failed_count}`
        );
        fetchReviews(); // Refresh list
        setSelectedReviews(new Set()); // Clear selection
      } else {
        throw new Error('Bulk action failed');
      }
    } catch (error) {
      console.error('Bulk action error:', error);
      alert('Failed to perform bulk action');
    }
  };

  // ============================================================================
  // Selection Handlers
  // ============================================================================

  const toggleSelection = (reviewId: number) => {
    const newSelection = new Set(selectedReviews);
    if (newSelection.has(reviewId)) {
      newSelection.delete(reviewId);
    } else {
      newSelection.add(reviewId);
    }
    setSelectedReviews(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedReviews.size === reviews.length) {
      setSelectedReviews(new Set());
    } else {
      setSelectedReviews(new Set(reviews.map((r) => r.id)));
    }
  };

  // ============================================================================
  // Render Functions
  // ============================================================================

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-spin">⏳</div>
            <p className="text-lg text-gray-600">Loading pending reviews...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold">Pending Reviews</h1>
            <p className="text-gray-600 mt-1">
              {totalCount} review{totalCount !== 1 ? 's' : ''} waiting for approval
            </p>
          </div>

          {/* Bulk Actions */}
          {selectedReviews.size > 0 && (
            <div className="flex gap-3">
              <button
                onClick={() => handleBulkAction('approve')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                ✓ Approve ({selectedReviews.size})
              </button>
              <button
                onClick={() => handleBulkAction('reject')}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                ✕ Reject ({selectedReviews.size})
              </button>
            </div>
          )}
        </div>

        {/* Select All */}
        {reviews.length > 0 && (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={selectedReviews.size === reviews.length}
              onChange={toggleSelectAll}
              className="w-4 h-4 cursor-pointer"
            />
            <label className="text-sm text-gray-600 cursor-pointer" onClick={toggleSelectAll}>
              Select all on this page
            </label>
          </div>
        )}
      </div>

      {/* Reviews List */}
      {reviews.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-2">All caught up!</h2>
          <p className="text-gray-600">No pending reviews at the moment.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {reviews.map((review) => {
            const isProcessing = processingIds.has(review.id);
            const isExpanded = expandedReviewId === review.id;

            return (
              <div
                key={review.id}
                className={`bg-white rounded-lg shadow-md border-2 transition ${
                  selectedReviews.has(review.id) ? 'border-blue-500' : 'border-gray-200'
                } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
              >
                <div className="p-6">
                  {/* Header Row */}
                  <div className="flex gap-4 mb-4">
                    {/* Checkbox */}
                    <div className="pt-1">
                      <input
                        type="checkbox"
                        checked={selectedReviews.has(review.id)}
                        onChange={() => toggleSelection(review.id)}
                        className="w-5 h-5 cursor-pointer"
                      />
                    </div>

                    {/* Main Content */}
                    <div className="flex-1">
                      {/* Rating Stars */}
                      <div className="flex items-center gap-2 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <span
                            key={star}
                            className={`text-2xl ${
                              star <= review.rating ? 'text-yellow-400' : 'text-gray-300'
                            }`}
                          >
                            ★
                          </span>
                        ))}
                        <span className="text-sm text-gray-500 ml-2">
                          {new Date(review.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-xl font-bold mb-2">{review.title}</h3>

                      {/* Content */}
                      <p
                        className={`text-gray-700 mb-4 ${
                          isExpanded ? '' : 'line-clamp-3'
                        }`}
                      >
                        {review.content}
                      </p>

                      {review.content.length > 200 && (
                        <button
                          onClick={() =>
                            setExpandedReviewId(isExpanded ? null : review.id)
                          }
                          className="text-blue-600 hover:underline text-sm mb-4"
                        >
                          {isExpanded ? 'Show less' : 'Read more'}
                        </button>
                      )}

                      {/* Media Gallery */}
                      {review.images.length > 0 && (
                        <div className="mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-semibold">
                              Media ({review.media_count}):
                            </span>
                            <span className="text-xs text-gray-600">
                              {review.image_count} image{review.image_count !== 1 ? 's' : ''}
                              {review.video_count > 0 &&
                                `, ${review.video_count} video${review.video_count !== 1 ? 's' : ''}`}
                            </span>
                          </div>
                          <div className="grid grid-cols-4 gap-2">
                            {review.images.slice(0, 8).map((media, idx) => (
                              <div
                                key={idx}
                                className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition"
                                onClick={() => setSelectedMediaPreview(media)}
                              >
                                {media.resource_type === 'image' ? (
                                  <Image
                                    src={media.thumbnail}
                                    alt={`Media ${idx + 1}`}
                                    fill
                                    className="object-cover"
                                  />
                                ) : (
                                  <div className="relative w-full h-full">
                                    <Image
                                      src={media.thumbnail}
                                      alt={`Video ${idx + 1}`}
                                      fill
                                      className="object-cover"
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                                      <span className="text-white text-2xl">▶</span>
                                    </div>
                                  </div>
                                )}
                                <div className="absolute top-1 right-1 bg-black/70 text-white px-1.5 py-0.5 rounded text-xs">
                                  {media.resource_type}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Customer Info */}
                      <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <h4 className="font-semibold mb-2 text-sm text-gray-600">
                          Customer Details
                        </h4>
                        <div className="space-y-1 text-sm">
                          <p>
                            <span className="font-semibold">Name:</span> {review.customer_name}
                          </p>
                          <p>
                            <span className="font-semibold">Email:</span> {review.customer_email}
                          </p>
                          {review.customer_phone && (
                            <p>
                              <span className="font-semibold">Phone:</span> {review.customer_phone}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* External Links */}
                      {review.has_external_reviews && (
                        <div className="mb-4">
                          <p className="text-sm font-semibold mb-2 text-gray-600">
                            Also reviewed on:
                          </p>
                          <div className="flex gap-3">
                            {review.google_review_url && (
                              <a
                                href={review.google_review_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline text-sm"
                              >
                                Google Reviews →
                              </a>
                            )}
                            {review.yelp_review_url && (
                              <a
                                href={review.yelp_review_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline text-sm"
                              >
                                Yelp →
                              </a>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleApprove(review.id)}
                          disabled={isProcessing}
                          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:bg-gray-400"
                        >
                          ✓ Approve
                        </button>
                        <button
                          onClick={() => {
                            setRejectReviewId(review.id);
                            setShowRejectModal(true);
                          }}
                          disabled={isProcessing}
                          className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:bg-gray-400"
                        >
                          ✕ Reject
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex justify-center gap-2">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="px-4 py-2">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
            className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Reject Review</h2>
            <p className="text-gray-600 mb-4">
              Please provide a reason for rejecting this review. This will be sent to the customer.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none h-32 resize-none mb-4"
              placeholder="Reason for rejection..."
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReviewId(null);
                  setRejectReason('');
                }}
                className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Reject Review
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Media Preview Modal */}
      {selectedMediaPreview && (
        <div
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8"
          onClick={() => setSelectedMediaPreview(null)}
        >
          <div className="max-w-5xl w-full max-h-full flex items-center justify-center">
            {selectedMediaPreview.resource_type === 'image' ? (
              <Image
                src={selectedMediaPreview.url}
                alt="Preview"
                width={selectedMediaPreview.width}
                height={selectedMediaPreview.height}
                className="max-w-full max-h-full object-contain"
              />
            ) : (
              <video
                src={selectedMediaPreview.url}
                controls
                autoPlay
                className="max-w-full max-h-full"
              />
            )}
          </div>
          <button
            onClick={() => setSelectedMediaPreview(null)}
            className="absolute top-4 right-4 bg-white text-black w-12 h-12 rounded-full text-2xl hover:bg-gray-200"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
