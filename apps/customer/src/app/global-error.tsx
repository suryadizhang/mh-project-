'use client';

import { useEffect } from 'react';

import { logger } from '@/lib/logger';
// Disable static generation for this page to avoid Next.js 15 issues
export const dynamic = 'force-dynamic';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logger.error('Global error caught', error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="p-8 text-center">
            <h2 className="mb-4 text-2xl font-bold text-gray-800">Something went wrong!</h2>
            <button
              onClick={() => reset()}
              className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
