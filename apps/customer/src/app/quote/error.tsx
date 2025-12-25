'use client';

import { useEffect } from 'react';

export default function QuoteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to browser console for debugging
    console.error('Quote page error:', error);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    console.error('Error digest:', error.digest);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="max-w-md p-8 text-center">
        <h2 className="mb-4 text-2xl font-bold text-gray-800">
          Something went wrong loading the quote calculator!
        </h2>
        <p className="mb-4 text-gray-600">Error: {error.message || 'Unknown error'}</p>
        {error.digest && <p className="mb-4 text-sm text-gray-500">Error ID: {error.digest}</p>}
        <button
          onClick={() => reset()}
          className="rounded-lg bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
