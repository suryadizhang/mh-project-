'use client';

import { AlertTriangle, CheckCircle, Info, Loader2 } from 'lucide-react';
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * Confirmation Dialog Types
 */
export type ConfirmDialogVariant = 'danger' | 'warning' | 'info' | 'success';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmDialogVariant;
  isLoading?: boolean;
  showCancel?: boolean;
}

/**
 * Reusable Confirmation Dialog Component
 *
 * @example
 * ```tsx
 * const [showDialog, setShowDialog] = useState(false);
 *
 * <ConfirmDialog
 *   isOpen={showDialog}
 *   onClose={() => setShowDialog(false)}
 *   onConfirm={async () => {
 *     await deleteBooking(id);
 *     setShowDialog(false);
 *   }}
 *   title="Delete Booking"
 *   message="Are you sure you want to delete this booking? This action cannot be undone."
 *   variant="danger"
 * />
 * ```
 */
export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText,
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
  showCancel = true,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = React.useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Handle ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, isLoading, onClose]);

  // Focus management
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[focusableElements.length - 1]?.focus();
      }
    }
  }, [isOpen]);

  const handleConfirm = async () => {
    try {
      await onConfirm();
    } catch (error) {
      console.error('Confirmation action failed:', error);
    }
  };

  const variantConfig = {
    danger: {
      icon: AlertTriangle,
      iconBgColor: 'bg-red-100',
      iconColor: 'text-red-600',
      buttonBgColor: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
      buttonText: confirmText || 'Delete',
    },
    warning: {
      icon: AlertTriangle,
      iconBgColor: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      buttonBgColor: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
      buttonText: confirmText || 'Proceed',
    },
    info: {
      icon: Info,
      iconBgColor: 'bg-blue-100',
      iconColor: 'text-blue-600',
      buttonBgColor: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
      buttonText: confirmText || 'Confirm',
    },
    success: {
      icon: CheckCircle,
      iconBgColor: 'bg-green-100',
      iconColor: 'text-green-600',
      buttonBgColor: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
      buttonText: confirmText || 'Confirm',
    },
  };

  const config = variantConfig[variant];
  const Icon = config.icon;

  if (!isOpen || !mounted) return null;

  const dialog = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={!isLoading ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Dialog Panel */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-md transform rounded-2xl bg-white p-6 shadow-2xl transition-all animate-in zoom-in-95 duration-200"
      >
        <div className="sm:flex sm:items-start">
          <div
            className={`mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${config.iconBgColor} sm:mx-0 sm:h-10 sm:w-10`}
          >
            <Icon
              className={`h-6 w-6 ${config.iconColor}`}
              aria-hidden="true"
            />
          </div>
          <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left flex-1">
            <h3
              id="dialog-title"
              className="text-lg font-semibold leading-6 text-gray-900"
            >
              {title}
            </h3>
            <div className="mt-2">
              <p className="text-sm text-gray-500">{message}</p>
            </div>
          </div>
        </div>

        <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse gap-2">
          <button
            type="button"
            disabled={isLoading}
            className={`inline-flex w-full items-center justify-center rounded-md px-4 py-2 text-sm font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${config.buttonBgColor}`}
            onClick={handleConfirm}
            autoFocus
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Processing...
              </>
            ) : (
              config.buttonText
            )}
          </button>
          {showCancel && (
            <button
              type="button"
              disabled={isLoading}
              className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              onClick={onClose}
            >
              {cancelText}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(dialog, document.body);
}

/**
 * Hook for managing confirmation dialogs
 *
 * @example
 * ```tsx
 * const { confirm, ConfirmDialogComponent } = useConfirmDialog();
 *
 * const handleDelete = async () => {
 *   const confirmed = await confirm({
 *     title: 'Delete Item',
 *     message: 'Are you sure?',
 *     variant: 'danger',
 *   });
 *
 *   if (confirmed) {
 *     await deleteItem();
 *   }
 * };
 *
 * return (
 *   <>
 *     <button onClick={handleDelete}>Delete</button>
 *     <ConfirmDialogComponent />
 *   </>
 * );
 * ```
 */
export function useConfirmDialog() {
  const [dialogState, setDialogState] = React.useState<{
    isOpen: boolean;
    title: string;
    message: string;
    variant: ConfirmDialogVariant;
    confirmText?: string;
    cancelText?: string;
    resolve?: (value: boolean) => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    variant: 'danger',
  });

  const confirm = React.useCallback(
    (options: {
      title: string;
      message: string;
      variant?: ConfirmDialogVariant;
      confirmText?: string;
      cancelText?: string;
    }): Promise<boolean> => {
      return new Promise(resolve => {
        setDialogState({
          isOpen: true,
          ...options,
          variant: options.variant || 'danger',
          resolve,
        });
      });
    },
    []
  );

  const handleClose = React.useCallback(() => {
    dialogState.resolve?.(false);
    setDialogState(prev => ({ ...prev, isOpen: false }));
  }, [dialogState.resolve]);

  const handleConfirm = React.useCallback(() => {
    dialogState.resolve?.(true);
    setDialogState(prev => ({ ...prev, isOpen: false }));
  }, [dialogState.resolve]);

  const ConfirmDialogComponent = React.useCallback(
    () => (
      <ConfirmDialog
        isOpen={dialogState.isOpen}
        onClose={handleClose}
        onConfirm={handleConfirm}
        title={dialogState.title}
        message={dialogState.message}
        variant={dialogState.variant}
        confirmText={dialogState.confirmText}
        cancelText={dialogState.cancelText}
      />
    ),
    [dialogState, handleClose, handleConfirm]
  );

  return { confirm, ConfirmDialogComponent };
}
