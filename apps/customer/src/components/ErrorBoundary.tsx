'use client';

/**
 * Error Boundary Component
 *
 * Catches React errors in child components and displays a fallback UI.
 * Prevents entire app crashes from component errors.
 *
 * Features:
 * - Graceful error handling with user-friendly messages
 * - Retry mechanism for transient failures
 * - Error details in development mode
 * - Automatic error reporting (ready for Sentry/DataDog integration)
 * - Reset functionality to recover from errors
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary fallbackComponent={<CustomFallback />}>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */

import React from 'react';
import { ErrorBoundary as ReactErrorBoundary, FallbackProps } from 'react-error-boundary';

import { logger } from '@/lib/logger';

interface ErrorFallbackProps extends FallbackProps {
  resetKeys?: string[];
}

/**
 * Default error fallback component
 * Displays user-friendly error message with retry option
 */
function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  React.useEffect(() => {
    // Log error details for debugging
    logger.error('ErrorBoundary caught an error', error, {
      errorMessage: error?.message,
      errorStack: error?.stack,
      componentStack: error?.stack,
    });

    // TODO: Send to error reporting service (Sentry, DataDog, etc.)
    // Example: Sentry.captureException(error);
  }, [error]);

  // Determine if error is recoverable
  const isNetworkError =
    error?.message?.includes('fetch') ||
    error?.message?.includes('network') ||
    error?.message?.includes('timeout');

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          {/* Error Icon */}
          <svg
            className="mx-auto h-16 w-16 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>

          {/* Error Title */}
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {isNetworkError ? 'Connection Problem' : 'Something Went Wrong'}
          </h2>

          {/* Error Message */}
          <p className="mt-2 text-sm text-gray-600">
            {isNetworkError
              ? "We're having trouble connecting to our servers. Please check your internet connection and try again."
              : 'We encountered an unexpected error. Our team has been notified and is working on a fix.'}
          </p>

          {/* Show error details in development */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-4 rounded-lg bg-red-50 p-4 text-left">
              <h3 className="mb-2 text-sm font-semibold text-red-800">
                Error Details (Development Only)
              </h3>
              <pre className="max-h-40 overflow-auto text-xs text-red-700">{error?.message}</pre>
              {error?.stack && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-xs text-red-800 hover:underline">
                    Stack Trace
                  </summary>
                  <pre className="mt-1 max-h-40 overflow-auto text-xs text-red-700">
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <button
              onClick={resetErrorBoundary}
              className="inline-flex items-center justify-center rounded-md border border-transparent bg-red-600 px-5 py-3 text-base font-medium text-white transition-colors hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
            >
              <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Try Again
            </button>

            <button
              onClick={() => (window.location.href = '/')}
              className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-5 py-3 text-base font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
            >
              <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              Go Home
            </button>
          </div>

          {/* Contact Support Link */}
          <p className="mt-6 text-xs text-gray-500">
            If the problem persists, please{' '}
            <a href="/contact" className="font-medium text-red-600 underline hover:text-red-500">
              contact our support team
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Main Error Boundary Component
 *
 * @param children - Child components to protect
 * @param fallback - Optional custom fallback component
 * @param onReset - Optional callback when error boundary resets
 * @param onError - Optional callback when error is caught
 * @param resetKeys - Optional keys that trigger reset when changed
 */
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactElement;
  onReset?: () => void;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  resetKeys?: string[];
}

export function ErrorBoundary({
  children,
  fallback,
  onReset,
  onError,
  resetKeys = [],
}: ErrorBoundaryProps) {
  const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Log with our logger utility
    logger.error('React Error Boundary triggered', error, {
      errorMessage: error.message,
      componentStack: errorInfo.componentStack,
      errorStack: error.stack,
    });

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    // TODO: Send to error monitoring service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  };

  const handleReset = () => {
    logger.info('ErrorBoundary reset triggered');

    // Call custom reset handler if provided
    if (onReset) {
      onReset();
    }
  };

  return (
    <ReactErrorBoundary
      FallbackComponent={fallback ? () => fallback : ErrorFallback}
      onError={handleError}
      onReset={handleReset}
      resetKeys={resetKeys}
    >
      {children}
    </ReactErrorBoundary>
  );
}

/**
 * Specialized Error Boundary for Forms
 * Includes form-specific error handling and recovery
 */
export function FormErrorBoundary({
  children,
  formName,
  onFormError,
}: {
  children: React.ReactNode;
  formName: string;
  onFormError?: () => void;
}) {
  const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
    logger.error(`Form Error Boundary triggered in ${formName}`, error, {
      formName,
      componentStack: errorInfo.componentStack,
    });

    if (onFormError) {
      onFormError();
    }
  };

  return <ErrorBoundary onError={handleError}>{children}</ErrorBoundary>;
}

/**
 * Specialized Error Boundary for API calls
 * Handles network/API-specific errors differently
 */
export function ApiErrorBoundary({
  children,
  apiEndpoint,
}: {
  children: React.ReactNode;
  apiEndpoint?: string;
}) {
  const handleError = (error: Error, _errorInfo: React.ErrorInfo) => {
    logger.error('API Error Boundary triggered', error, {
      apiEndpoint,
      isNetworkError: error.message.includes('fetch') || error.message.includes('network'),
    });
  };

  return <ErrorBoundary onError={handleError}>{children}</ErrorBoundary>;
}

export default ErrorBoundary;
