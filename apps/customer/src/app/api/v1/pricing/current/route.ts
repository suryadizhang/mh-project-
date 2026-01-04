/**
 * Pricing Current Proxy API Route
 *
 * Proxies requests to the backend API to avoid CORS issues.
 * Used for fetching current pricing from the database.
 *
 * GET /api/v1/pricing/current → Backend /api/v1/pricing/current
 */

import { NextResponse } from 'next/server';

// Cache the pricing response for 5 minutes to reduce backend load
const CACHE_TTL_SECONDS = 300;

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Pricing Current Proxy] Fetching from ${apiUrl}/api/v1/pricing/current`);

    const response = await fetch(`${apiUrl}/api/v1/pricing/current`, {
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
        `[Pricing Current Proxy] Backend returned ${response.status}: ${response.statusText}`,
      );
      return NextResponse.json(
        { error: 'Failed to fetch pricing from backend', status: response.status },
        { status: response.status },
      );
    }

    const data = await response.json();

    console.log('[Pricing Current Proxy] Successfully fetched pricing:', {
      hasBasePricing: !!data?.base_pricing,
      hasMenuItems: !!data?.menu_items,
      hasAddonItems: !!data?.addon_items,
    });

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
      },
    });
  } catch (error) {
    console.error('[Pricing Current Proxy] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch pricing',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
