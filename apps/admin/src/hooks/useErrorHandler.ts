import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

import { useToast } from '@/components/ui/Toast';
import {
  getErrorMessage,
  getShortErrorMessage,
  isTemporaryError,
  parseError,
  requiresReauth,
} from '@/lib/errors';

/**
 * Hook for handling errors with user-friendly messages
 *
 * @example
 * ```tsx
 * const { handleError } = useErrorHandler();
 *
 * try {
 *   await deleteBooking(id);
 * } catch (error) {
 *   handleError(error);
 * }
 * ```
 */
export function useErrorHandler() {
  const toast = useToast();
  const router = useRouter();

  const handleError = useCallback(
    (
      error: unknown,
      options?: {
        showToast?: boolean;
        onRetry?: () => void;
        silent?: boolean;
      }
    ) => {
      const {
        showToast: shouldShowToast = true,
        onRetry,
        silent = false,
      } = options || {};

      if (silent) return;

      const parsedError = parseError(error);

      // Handle authentication errors
      if (requiresReauth(error)) {
        if (shouldShowToast) {
          toast.error(parsedError.title, parsedError.message);
        }
        // Redirect to login after a short delay
        setTimeout(() => {
          router.push('/login');
        }, 2000);
        return;
      }

      // Show toast notification
      if (shouldShowToast) {
        if (onRetry && isTemporaryError(error)) {
          toast.showToast({
            type: 'error',
            title: parsedError.title,
            message: parsedError.message,
            action: {
              label: 'Retry',
              onClick: onRetry,
            },
            duration: 7000,
          });
        } else {
          toast.error(parsedError.title, parsedError.message);
        }
      }

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.error('Error handled:', {
          type: parsedError.type,
          title: parsedError.title,
          message: parsedError.message,
          details: parsedError.details,
          original: error,
        });
      }
    },
    [toast, router]
  );

  const handleSuccess = useCallback(
    (message: string, description?: string) => {
      toast.success(message, description);
    },
    [toast]
  );

  return {
    handleError,
    handleSuccess,
    parseError,
    getErrorMessage,
    getShortErrorMessage,
  };
}

/**
 * Higher-order function to wrap async functions with error handling
 *
 * @example
 * ```tsx
 * const { withErrorHandling } = useErrorHandler();
 *
 * const handleDelete = withErrorHandling(async () => {
 *   await deleteBooking(id);
 *   toast.success('Booking deleted successfully');
 * }, {
 *   successMessage: 'Booking deleted!',
 *   errorMessage: 'Failed to delete booking',
 * });
 * ```
 */
export function useErrorBoundary() {
  const { handleError, handleSuccess } = useErrorHandler();

  const withErrorHandling = useCallback(
    <T extends (...args: unknown[]) => Promise<unknown>>(
      fn: T,
      options?: {
        successMessage?: string;
        errorMessage?: string;
        onRetry?: () => void;
        silent?: boolean;
      }
    ) => {
      return async (...args: Parameters<T>) => {
        try {
          const result = await fn(...args);
          if (options?.successMessage) {
            handleSuccess(options.successMessage);
          }
          return result;
        } catch (error) {
          handleError(error, {
            showToast: !options?.silent,
            onRetry: options?.onRetry,
          });
          throw error;
        }
      };
    },
    [handleError, handleSuccess]
  );

  return {
    withErrorHandling,
    handleError,
    handleSuccess,
  };
}
