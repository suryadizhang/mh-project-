/**
 * Pricing Summary Proxy API Route
 *
 * Proxies requests to the backend API to avoid CORS issues.
 * Used for getting pricing summary with sample quotes.
 *
 * GET /api/v1/pricing/summary → Backend /api/v1/pricing/summary
 */

import { NextResponse } from 'next/server';

// Cache the summary response for 5 minutes
const CACHE_TTL_SECONDS = 300;

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Pricing Summary Proxy] Fetching from ${apiUrl}/api/v1/pricing/summary`);

    const response = await fetch(`${apiUrl}/api/v1/pricing/summary`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      // Cache for 5 minutes
      next: { revalidate: CACHE_TTL_SECONDS },
    });

    if (!response.ok) {
      console.error(
        `[Pricing Summary Proxy] Backend returned ${response.status}: ${response.statusText}`,
      );
      return NextResponse.json(
        { error: 'Failed to fetch pricing summary from backend', status: response.status },
        { status: response.status },
      );
    }

    const data = await response.json();

    console.log('[Pricing Summary Proxy] Successfully fetched summary:', {
      hasCurrentPricing: !!data?.current_pricing,
      sampleQuotesCount: data?.sample_quotes?.length,
      hasPolicies: !!data?.policies,
    });

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
      },
    });
  } catch (error) {
    console.error('[Pricing Summary Proxy] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch pricing summary',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
