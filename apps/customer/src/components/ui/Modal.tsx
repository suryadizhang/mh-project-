/**
 * Modal Component
 * Reusable modal dialog for customer app
 *
 * @example
 * <Modal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   title="Contact Support"
 * >
 *   <p>Please contact us for large parties.</p>
 * </Modal>
 */

'use client';

import { X } from 'lucide-react';
import { useEffect, useCallback } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
  /** Optional icon to display next to title */
  icon?: React.ReactNode;
  /** Variant styling */
  variant?: 'default' | 'warning' | 'info';
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  showCloseButton = true,
  icon,
  variant = 'default',
}: ModalProps) {
  // Memoize close handler
  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, handleClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  const variantStyles = {
    default: {
      header: 'bg-white border-b border-gray-200',
      title: 'text-gray-900',
      icon: 'text-gray-500',
    },
    warning: {
      header: 'bg-amber-50 border-b border-amber-200',
      title: 'text-amber-900',
      icon: 'text-amber-500',
    },
    info: {
      header: 'bg-blue-50 border-b border-blue-200',
      title: 'text-blue-900',
      icon: 'text-blue-500',
    },
  };

  const styles = variantStyles[variant];

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={`relative rounded-xl bg-white shadow-2xl ${sizeClasses[size]} animate-in fade-in zoom-in-95 w-full duration-200`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`flex items-center justify-between rounded-t-xl p-5 ${styles.header}`}>
            <h2
              id="modal-title"
              className={`flex items-center gap-2 text-xl font-semibold ${styles.title}`}
            >
              {icon && <span className={styles.icon}>{icon}</span>}
              {title}
            </h2>
            {showCloseButton && (
              <button
                onClick={handleClose}
                className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Body */}
          <div className="max-h-[70vh] overflow-y-auto p-6">{children}</div>

          {/* Footer */}
          {footer && (
            <div className="flex items-center justify-end gap-3 rounded-b-xl border-t border-gray-200 bg-gray-50 p-5">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Modal;
