/**
 * CancellationRequestModal Component
 *
 * Modal for requesting booking cancellation (2-step workflow - Step 1)
 * Staff enters a reason, booking status changes to CANCELLATION_REQUESTED
 * Slot remains held until admin approves/rejects the request
 *
 * @example
 * ```tsx
 * <CancellationRequestModal
 *   isOpen={showCancelModal}
 *   onClose={() => setShowCancelModal(false)}
 *   onSubmit={handleRequestCancellation}
 *   bookingName="John Doe - Dec 25, 2025"
 * />
 * ```
 */

import React, {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from 'react';

interface CancellationRequestModalProps {
  /** Whether the modal is open */
  isOpen: boolean;

  /** Callback when user closes modal without submitting */
  onClose: () => void;

  /** Callback when user submits cancellation request. Receives the reason. */
  onSubmit: (reason: string) => Promise<void>;

  /** Name/identifier of the booking (e.g., "John Doe - Dec 25, 2025") */
  bookingName: string;
}

export const CancellationRequestModal: React.FC<
  CancellationRequestModalProps
> = ({ isOpen, onClose, onSubmit, bookingName }) => {
  // State
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Constants
  const MIN_REASON_LENGTH = 10;
  const MAX_REASON_LENGTH = 500;

  // Computed
  const remainingChars = MAX_REASON_LENGTH - reason.length;
  const isReasonValid =
    reason.length >= MIN_REASON_LENGTH && reason.length <= MAX_REASON_LENGTH;
  const canSubmit = isReasonValid && !isSubmitting;

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setReason('');
      setError('');
      setIsSubmitting(false);

      // Focus textarea after mount
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        handleClose();
      }
    };

    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, isSubmitting]);

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
    if (!isSubmitting) {
      onClose();
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!canSubmit) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await onSubmit(reason);
      // Modal will be closed by parent component after successful submission
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Failed to submit cancellation request. Please try again.';
      setError(errorMessage);
      setIsSubmitting(false);
    }
  };

  const handleTextareaKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && canSubmit) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isSubmitting) {
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
      aria-labelledby="cancel-modal-title"
      aria-describedby="cancel-modal-description"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2
              id="cancel-modal-title"
              className="text-lg font-semibold text-gray-900"
            >
              Request Cancellation
            </h2>
            <p className="text-sm text-gray-500 mt-1">{bookingName}</p>
          </div>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
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
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4">
            {/* Info Box */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex">
                <svg
                  className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div>
                  <p className="text-sm text-yellow-800 font-medium">
                    2-Step Cancellation Process
                  </p>
                  <p className="text-sm text-yellow-700 mt-1">
                    This will mark the booking as &quot;Pending
                    Cancellation&quot;. The time slot remains held until an
                    admin approves or rejects the request.
                  </p>
                </div>
              </div>
            </div>

            {/* Reason Textarea */}
            <div className="mb-4">
              <label
                htmlFor="cancellation-reason"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Cancellation Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                ref={textareaRef}
                id="cancellation-reason"
                value={reason}
                onChange={e => setReason(e.target.value)}
                onKeyDown={handleTextareaKeyDown}
                disabled={isSubmitting}
                placeholder="Please provide a reason for the cancellation request (minimum 10 characters)..."
                rows={4}
                maxLength={MAX_REASON_LENGTH}
                className={`w-full px-3 py-2 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:bg-gray-100 disabled:cursor-not-allowed ${
                  reason.length > 0 && !isReasonValid
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-orange-500'
                }`}
              />
              <div className="flex justify-between mt-1 text-xs">
                <span
                  className={
                    reason.length > 0 && reason.length < MIN_REASON_LENGTH
                      ? 'text-red-500'
                      : 'text-gray-500'
                  }
                >
                  {reason.length > 0 && reason.length < MIN_REASON_LENGTH
                    ? `Minimum ${MIN_REASON_LENGTH} characters required`
                    : 'Shift+Enter for new line'}
                </span>
                <span
                  className={
                    remainingChars < 50 ? 'text-red-500' : 'text-gray-500'
                  }
                >
                  {remainingChars} characters remaining
                </span>
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
          <div className="border-t border-gray-200 px-6 py-4 flex justify-end space-x-3 bg-gray-50">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="px-4 py-2 text-sm font-medium text-white bg-orange-600 border border-transparent rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
            >
              {isSubmitting && (
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
              Request Cancellation
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CancellationRequestModal;
