/**
 * DeleteConfirmationModal Component
 * 
 * Enterprise-grade reusable modal for confirming delete operations with:
 * - Mandatory delete reason (10-500 characters)
 * - Character counter with validation
 * - Two-step confirmation (checkbox + button)
 * - Loading and error states
 * - Keyboard shortcuts (ESC to cancel, Enter to confirm)
 * - Accessible (ARIA labels, focus management)
 * - Responsive design
 * 
 * @example
 * ```tsx
 * <DeleteConfirmationModal
 *   isOpen={showDeleteModal}
 *   onClose={() => setShowDeleteModal(false)}
 *   onConfirm={handleDeleteBooking}
 *   resourceType="booking"
 *   resourceName="John Doe - Dec 25, 2025"
 *   warningMessage="This booking will be soft-deleted and can be restored within 30 days."
 * />
 * ```
 */

import React, { useState, useEffect, useRef, FormEvent, KeyboardEvent } from 'react';

interface DeleteConfirmationModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  
  /** Callback when user closes modal without confirming */
  onClose: () => void;
  
  /** Callback when user confirms deletion. Receives the delete reason. */
  onConfirm: (reason: string) => Promise<void>;
  
  /** Type of resource being deleted (e.g., "booking", "customer", "lead") */
  resourceType: string;
  
  /** Name/identifier of the specific resource (e.g., "John Doe - Dec 25, 2025") */
  resourceName: string;
  
  /** Optional custom warning message. If not provided, a default warning is shown. */
  warningMessage?: string;
  
  /** Optional custom confirmation text. Default: "I understand this action cannot be undone" */
  confirmationText?: string;
}

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  resourceType,
  resourceName,
  warningMessage,
  confirmationText = "I understand this action cannot be undone"
}) => {
  // State
  const [reason, setReason] = useState<string>('');
  const [understood, setUnderstood] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  
  // Constants
  const MIN_REASON_LENGTH = 10;
  const MAX_REASON_LENGTH = 500;
  
  // Computed
  const remainingChars = MAX_REASON_LENGTH - reason.length;
  const isReasonValid = reason.length >= MIN_REASON_LENGTH && reason.length <= MAX_REASON_LENGTH;
  const canConfirm = isReasonValid && understood && !isDeleting;
  
  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setReason('');
      setUnderstood(false);
      setError('');
      setIsDeleting(false);
      
      // Focus textarea after mount
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);
  
  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isDeleting) {
        handleClose();
      }
    };
    
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, isDeleting]);
  
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
  
  /**
   * Handle modal close
   */
  const handleClose = () => {
    if (!isDeleting) {
      onClose();
    }
  };
  
  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!canConfirm) {
      return;
    }
    
    setIsDeleting(true);
    setError('');
    
    try {
      await onConfirm(reason);
      // Modal will be closed by parent component after successful deletion
    } catch (err) {
      // Handle error
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete. Please try again.';
      setError(errorMessage);
      setIsDeleting(false);
    }
  };
  
  /**
   * Handle keyboard shortcuts in textarea
   */
  const handleTextareaKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Allow Shift+Enter for multiline
    if (e.key === 'Enter' && !e.shiftKey && canConfirm) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };
  
  /**
   * Handle backdrop click
   */
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isDeleting) {
      handleClose();
    }
  };
  
  // Don't render if not open
  if (!isOpen) {
    return null;
  }
  
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 px-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
      aria-describedby="delete-modal-description"
    >
      <div
        ref={modalRef}
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-red-50">
          <div className="flex items-center">
            <svg 
              className="w-6 h-6 text-red-600 mr-3" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
              />
            </svg>
            <h2 id="delete-modal-title" className="text-xl font-bold text-gray-900">
              Confirm Deletion
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isDeleting}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-4">
          <div id="delete-modal-description" className="space-y-4">
            {/* Resource Info */}
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-600 mb-1">You are about to delete:</p>
              <p className="font-semibold text-gray-900">
                <span className="capitalize">{resourceType}</span>: {resourceName}
              </p>
            </div>
            
            {/* Warning Message */}
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="flex">
                <svg 
                  className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path 
                    fillRule="evenodd" 
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" 
                    clipRule="evenodd" 
                  />
                </svg>
                <p className="text-sm text-yellow-800">
                  {warningMessage || `This ${resourceType} will be soft-deleted and can be restored within 30 days. After 30 days, it will be permanently removed.`}
                </p>
              </div>
            </div>
            
            {/* Reason Input */}
            <div>
              <label 
                htmlFor="delete-reason" 
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Reason for deletion <span className="text-red-600" aria-label="required">*</span>
              </label>
              <textarea
                ref={textareaRef}
                id="delete-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                onKeyDown={handleTextareaKeyDown}
                disabled={isDeleting}
                placeholder="Please provide a detailed reason for this deletion (minimum 10 characters)..."
                className={`
                  w-full px-3 py-2 border rounded-lg resize-none
                  focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent
                  disabled:bg-gray-100 disabled:cursor-not-allowed
                  ${reason.length > 0 && reason.length < MIN_REASON_LENGTH ? 'border-red-300' : 'border-gray-300'}
                  ${isReasonValid ? 'border-green-300' : ''}
                `}
                rows={4}
                maxLength={MAX_REASON_LENGTH}
                required
                aria-required="true"
                aria-invalid={reason.length > 0 && !isReasonValid}
                aria-describedby="reason-help reason-counter"
              />
              
              {/* Character Counter */}
              <div className="mt-2 flex items-center justify-between">
                <div id="reason-help" className="text-sm text-gray-600">
                  {reason.length === 0 && (
                    <span>Please enter at least {MIN_REASON_LENGTH} characters</span>
                  )}
                  {reason.length > 0 && reason.length < MIN_REASON_LENGTH && (
                    <span className="text-red-600">
                      {MIN_REASON_LENGTH - reason.length} more character{MIN_REASON_LENGTH - reason.length !== 1 ? 's' : ''} required
                    </span>
                  )}
                  {isReasonValid && (
                    <span className="text-green-600 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Valid reason
                    </span>
                  )}
                </div>
                <span 
                  id="reason-counter"
                  className={`text-sm ${remainingChars < 50 ? 'text-orange-600' : 'text-gray-500'}`}
                  aria-live="polite"
                >
                  {remainingChars} character{remainingChars !== 1 ? 's' : ''} remaining
                </span>
              </div>
            </div>
            
            {/* Confirmation Checkbox */}
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="confirm-understood"
                  type="checkbox"
                  checked={understood}
                  onChange={(e) => setUnderstood(e.target.checked)}
                  disabled={isDeleting}
                  className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-required="true"
                />
              </div>
              <label 
                htmlFor="confirm-understood" 
                className="ml-3 text-sm text-gray-700"
              >
                {confirmationText}
              </label>
            </div>
            
            {/* Error Message */}
            {error && (
              <div 
                className="bg-red-50 p-4 rounded-lg border border-red-200"
                role="alert"
                aria-live="assertive"
              >
                <div className="flex">
                  <svg 
                    className="w-5 h-5 text-red-600 mr-2 flex-shrink-0" 
                    fill="currentColor" 
                    viewBox="0 0 20 20"
                  >
                    <path 
                      fillRule="evenodd" 
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" 
                      clipRule="evenodd" 
                    />
                  </svg>
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            )}
          </div>
        </form>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end space-x-3 bg-gray-50">
          <button
            type="button"
            onClick={handleClose}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={!canConfirm}
            className={`
              px-4 py-2 text-sm font-medium text-white rounded-lg
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors
              ${canConfirm && !isDeleting 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-gray-400'
              }
              ${isDeleting ? 'cursor-wait' : ''}
            `}
            aria-busy={isDeleting}
          >
            {isDeleting ? (
              <span className="flex items-center">
                <svg 
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
                  fill="none" 
                  viewBox="0 0 24 24"
                  aria-hidden="true"
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
                Deleting...
              </span>
            ) : (
              'Confirm Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;
