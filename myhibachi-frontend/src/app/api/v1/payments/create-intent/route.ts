import { NextResponse } from 'next/server'

/**
 * ⚠️  MIGRATED TO BACKEND ⚠️
 *
 * This endpoint has been migrated to the FastAPI backend.
 *
 * OLD: /api/v1/payments/create-intent
 * NEW: ${NEXT_PUBLIC_API_URL}/api/stripe/v1/payments/create-intent
 *
 * This stub returns HTTP 410 Gone to indicate permanent migration.
 * Update your frontend code to use the new backend endpoint.
 *
 * Migration Date: $(date)
 * Backend Route: FastAPI backend - /api/stripe/v1/payments/create-intent
 */

export async function POST() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/api/v1/payments/create-intent',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/stripe/v1/payments/create-intent`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}

export async function GET() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/api/v1/payments/create-intent',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/stripe/v1/payments/create-intent`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}
