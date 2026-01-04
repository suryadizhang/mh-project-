/**
 * Config Proxy API Route
 *
 * Proxies requests to the backend API to avoid CORS issues.
 * The backend API may not have CORS headers configured for browser requests.
 *
 * GET /api/v1/config → Backend /api/v1/config/all
 */

import { NextResponse } from 'next/server';

// Cache the config response for 5 minutes to reduce backend load
const CACHE_TTL_SECONDS = 300;

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Config Proxy] Fetching from ${apiUrl}/api/v1/config/all`);

    const response = await fetch(`${apiUrl}/api/v1/config/all`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      // Cache for 5 minutes
      next: { revalidate: CACHE_TTL_SECONDS },
    });

    if (!response.ok) {
      console.error(`[Config Proxy] Backend returned ${response.status}: ${response.statusText}`);
      return NextResponse.json(
        { error: 'Failed to fetch config from backend', status: response.status },
        { status: response.status },
      );
    }

    const data = await response.json();

    console.log('[Config Proxy] Successfully fetched config:', {
      hasPricing: !!data?.pricing,
      adultPrice: data?.pricing?.adult_price_cents,
      hasDeposit: !!data?.deposit,
    });

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
      },
    });
  } catch (error) {
    console.error('[Config Proxy] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch config',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
