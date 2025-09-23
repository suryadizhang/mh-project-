import { NextResponse } from 'next/server'

/**
 * ⚠️  MIGRATED TO BACKEND ⚠️
 *
 * This endpoint has been migrated to the FastAPI backend.
 *
 * OLD: /support/contact
 * NEW: ${NEXT_PUBLIC_API_URL}/api/support/contact
 *
 * This stub returns HTTP 410 Gone to indicate permanent migration.
 * Update your frontend code to use the new backend endpoint.
 *
 * Migration Date: 2025-09-02T05:45:43.899Z
 * Backend Route: FastAPI backend - /api/support/contact
 */

export async function GET() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/support/contact',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/support/contact`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}

export async function POST() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/support/contact',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/support/contact`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}

export async function PUT() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/support/contact',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/support/contact`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}

export async function DELETE() {
  return NextResponse.json(
    {
      error: 'Endpoint migrated to backend',
      migration: {
        from: '/support/contact',
        to: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/support/contact`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update frontend to use backend API endpoint'
      }
    },
    { status: 410 }
  )
}
