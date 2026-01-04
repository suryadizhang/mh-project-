/**
 * Base Location Proxy API Route
 *
 * Proxies requests to the backend API to avoid CORS issues.
 * Used for travel fee calculation based on station coordinates.
 *
 * GET /api/v1/admin/base-location → Backend /api/v1/admin/base-location
 */

import { NextResponse } from 'next/server';

// Cache the location response for 5 minutes
const CACHE_TTL_SECONDS = 300;

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    console.log(`[Base Location Proxy] Fetching from ${apiUrl}/api/v1/admin/base-location`);

    const response = await fetch(`${apiUrl}/api/v1/admin/base-location`, {
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
        `[Base Location Proxy] Backend returned ${response.status}: ${response.statusText}`,
      );
      // Return fallback location if backend fails
      return NextResponse.json(
        {
          zipCode: '94536',
          city: 'Bay Area',
          state: 'CA',
          lat: 37.4958,
          lng: -121.9405,
          lastUpdated: new Date().toISOString(),
          updatedBy: 'Fallback',
        },
        {
          status: 200,
          headers: {
            'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
          },
        },
      );
    }

    const data = await response.json();

    console.log('[Base Location Proxy] Successfully fetched location:', {
      city: data?.city,
      lat: data?.lat,
      lng: data?.lng,
    });

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
      },
    });
  } catch (error) {
    console.error('[Base Location Proxy] Error:', error);

    // Return fallback location on error
    return NextResponse.json(
      {
        zipCode: '94536',
        city: 'Bay Area',
        state: 'CA',
        lat: 37.4958,
        lng: -121.9405,
        lastUpdated: new Date().toISOString(),
        updatedBy: 'Error Fallback',
      },
      {
        status: 200,
        headers: {
          'Cache-Control': `public, s-maxage=${CACHE_TTL_SECONDS}, stale-while-revalidate`,
        },
      },
    );
  }
}
