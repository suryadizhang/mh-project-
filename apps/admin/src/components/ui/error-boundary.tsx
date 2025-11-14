/**
 * Error Boundary Component
 * Catches React component errors and displays fallback UI
 */

'use client';

import { AlertTriangle } from 'lucide-react';
import React from 'react';

import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);

    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="flex justify-center mb-4">
                <div className="rounded-full bg-red-100 p-3">
                  <AlertTriangle className="h-8 w-8 text-red-600" />
                </div>
              </div>

              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Something went wrong
              </h2>

              <p className="text-gray-600 mb-6">
                {this.state.error?.message ||
                  'An unexpected error occurred. Please try again.'}
              </p>

              <div className="flex flex-col gap-3">
                <Button onClick={this.handleReset} className="w-full">
                  Try Again
                </Button>

                <Button
                  variant="outline"
                  onClick={() => window.location.reload()}
                  className="w-full"
                >
                  Reload Page
                </Button>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                    Error Details (Development Only)
                  </summary>
                  <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Simplified Error Boundary for page sections
 */
export function PageErrorBoundary({
  children,
  title = 'Error Loading Content',
}: {
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <ErrorBoundary
      fallback={
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <div>
              <h3 className="font-semibold text-red-900">{title}</h3>
              <p className="text-sm text-red-700 mt-1">
                Please refresh the page or contact support if the problem persists.
              </p>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
