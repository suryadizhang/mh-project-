/**
 * CancellationReviewModal Component
 *
 * Modal for admins to approve or reject a cancellation request (2-step workflow - Step 2)
 * Shows the original cancellation reason and allows admin to add notes
 *
 * @example
 * ```tsx
 * <CancellationReviewModal
 *   isOpen={showReviewModal}
 *   onClose={() => setShowReviewModal(false)}
 *   onApprove={handleApprove}
 *   onReject={handleReject}
 *   bookingName="John Doe - Dec 25, 2025"
 *   cancellationReason="Customer changed travel plans"
 *   requestedAt="2025-01-27T10:00:00Z"
 * />
 * ```
 */

import React, { FormEvent, useEffect, useRef, useState } from 'react';

interface CancellationReviewModalProps {
  /** Whether the modal is open */
  isOpen: boolean;

  /** Callback when user closes modal without action */
  onClose: () => void;

  /** Callback when admin approves the cancellation. Receives optional notes. */
  onApprove: (adminNotes?: string) => Promise<void>;

  /** Callback when admin rejects the cancellation. Receives optional notes. */
  onReject: (adminNotes?: string) => Promise<void>;

  /** Name/identifier of the booking (e.g., "John Doe - Dec 25, 2025") */
  bookingName: string;

  /** The reason provided when cancellation was requested */
  cancellationReason?: string;

  /** When the cancellation was requested (ISO date string) */
  requestedAt?: string;

  /** Who requested the cancellation */
  requestedBy?: string;
}

export const CancellationReviewModal: React.FC<
  CancellationReviewModalProps
> = ({
  isOpen,
  onClose,
  onApprove,
  onReject,
  bookingName,
  cancellationReason,
  requestedAt,
  requestedBy,
}) => {
  // State
  const [adminNotes, setAdminNotes] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);
  const [error, setError] = useState<string>('');

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Constants
  const MAX_NOTES_LENGTH = 500;
  const remainingChars = MAX_NOTES_LENGTH - adminNotes.length;

  // Format date
  const formattedRequestDate = requestedAt
    ? new Date(requestedAt).toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : 'Unknown date';

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setAdminNotes('');
      setError('');
      setIsProcessing(false);
      setAction(null);
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isProcessing) {
        handleClose();
      }
    };

    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, isProcessing]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleClose = () => {
    if (!isProcessing) {
      onClose();
    }
  };

  const handleAction = async (selectedAction: 'approve' | 'reject') => {
    if (isProcessing) {
      return;
    }

    setAction(selectedAction);
    setIsProcessing(true);
    setError('');

    try {
      if (selectedAction === 'approve') {
        await onApprove(adminNotes.trim() || undefined);
      } else {
        await onReject(adminNotes.trim() || undefined);
      }
      // Modal will be closed by parent component after successful action
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : `Failed to ${selectedAction} cancellation. Please try again.`;
      setError(errorMessage);
      setIsProcessing(false);
      setAction(null);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isProcessing) {
      handleClose();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 px-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2
              id="review-modal-title"
              className="text-lg font-semibold text-gray-900"
            >
              Review Cancellation Request
            </h2>
            <p className="text-sm text-gray-500 mt-1">{bookingName}</p>
          </div>
          <button
            onClick={handleClose}
            disabled={isProcessing}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            aria-label="Close modal"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {/* Pending Badge */}
          <div className="flex items-center justify-center mb-4">
            <span className="inline-flex items-center px-4 py-2 rounded-full bg-orange-100 text-orange-800">
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Pending Cancellation
            </span>
          </div>

          {/* Request Details */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Request Details
            </h3>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Requested:</span>
                <span className="text-gray-900">{formattedRequestDate}</span>
              </div>
              {requestedBy && (
                <div className="flex justify-between">
                  <span className="text-gray-500">By:</span>
                  <span className="text-gray-900">{requestedBy}</span>
                </div>
              )}
            </div>

            {/* Cancellation Reason */}
            {cancellationReason && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-1">
                  Reason:
                </p>
                <p className="text-sm text-gray-600 bg-white p-3 rounded border border-gray-200">
                  {cancellationReason}
                </p>
              </div>
            )}
          </div>

          {/* Approve Info */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
            <div className="flex">
              <svg
                className="w-5 h-5 text-green-600 mr-2 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <div>
                <p className="text-sm text-green-800">
                  <strong>Approve:</strong> The booking will be cancelled and
                  the time slot will be released for new bookings.
                </p>
              </div>
            </div>
          </div>

          {/* Reject Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <div className="flex">
              <svg
                className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              <div>
                <p className="text-sm text-blue-800">
                  <strong>Reject:</strong> The booking will return to its
                  previous status and remain active.
                </p>
              </div>
            </div>
          </div>

          {/* Admin Notes Textarea */}
          <div className="mb-4">
            <label
              htmlFor="admin-notes"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Admin Notes (optional)
            </label>
            <textarea
              ref={textareaRef}
              id="admin-notes"
              value={adminNotes}
              onChange={e => setAdminNotes(e.target.value)}
              disabled={isProcessing}
              placeholder="Add any notes about your decision..."
              rows={3}
              maxLength={MAX_NOTES_LENGTH}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-1 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <div className="flex justify-end mt-1 text-xs text-gray-500">
              {remainingChars} characters remaining
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex justify-between items-center bg-gray-50">
          <button
            type="button"
            onClick={handleClose}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>

          <div className="flex space-x-3">
            {/* Reject Button */}
            <button
              type="button"
              onClick={() => handleAction('reject')}
              disabled={isProcessing}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
            >
              {isProcessing && action === 'reject' && (
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              Reject Request
            </button>

            {/* Approve Button */}
            <button
              type="button"
              onClick={() => handleAction('approve')}
              disabled={isProcessing}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
            >
              {isProcessing && action === 'approve' && (
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              Approve & Cancel Booking
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CancellationReviewModal;
