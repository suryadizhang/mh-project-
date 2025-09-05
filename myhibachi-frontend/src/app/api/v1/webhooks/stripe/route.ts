import { NextResponse } from 'next/server';

/**
 * ⚠️  MIGRATED TO BACKEND ⚠️
 *
 * This endpoint has been migrated to the FastAPI backend.
 *
 * OLD: /api/v1/webhooks/stripe
 * NEW: ${NEXT_PUBLIC_API_URL}/api/stripe/v1/webhooks/stripe
 *
 * This stub returns HTTP 410 Gone to indicate permanent migration.
 * Update your Stripe webhook configuration to point to the new backend endpoint.
 *
 * Migration Date: $(date)
 * Backend Route: FastAPI backend - /api/stripe/v1/webhooks/stripe
 *
 * IMPORTANT: Update your Stripe Dashboard webhook endpoints!
 * Remove this endpoint and add the new backend endpoint.
 */

export async function POST() {
  return NextResponse.json(
    {
      error: 'Webhook endpoint migrated to backend',
      migration: {
        from: '/api/v1/webhooks/stripe',
        to: `${
          process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        }/api/stripe/v1/webhooks/stripe`,
        status: 'MIGRATED',
        date: new Date().toISOString(),
        instructions: 'Update Stripe webhook configuration to use backend endpoint',
      },
    },
    { status: 410 },
  );
}
