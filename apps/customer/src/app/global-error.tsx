'use client'

import { useEffect } from 'react'

import { logger } from '@/lib/logger';
// Disable static generation for this page to avoid Next.js 15 issues
export const dynamic = 'force-dynamic'

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    logger.error('Global error caught', error)
  }, [error])

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Something went wrong!</h2>
            <button
              onClick={() => reset()}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}


