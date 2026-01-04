/**
 * Public Quote Calculate Proxy API Route
 *
 * Proxies POST requests to the backend API to avoid CORS issues.
 * Used by QuoteCalculator component on /quote page.
 *
 * POST /api/v1/public/quote/calculate → Backend /api/v1/public/quote/calculate
 *
 * SSoT Note: This proxy forwards requests to the backend which is the
 * source of truth for pricing calculations. No business logic here.
 * See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const body = await request.json();

    console.log('[Public Quote Proxy] Calculating quote:', {
      adults: body?.adults,
      children: body?.children,
      hasAddress: !!body?.venue_address,
      hasZipcode: !!body?.zip_code,
    });

    const response = await fetch(`${apiUrl}/api/v1/public/quote/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(
        `[Public Quote Proxy] Backend returned ${response.status}: ${response.statusText}`,
        errorText,
      );
      return NextResponse.json(
        {
          error: 'Failed to calculate quote',
          status: response.status,
          details: errorText,
        },
        { status: response.status },
      );
    }

    const data = await response.json();

    console.log('[Public Quote Proxy] Quote calculated successfully:', {
      grandTotal: data?.grand_total,
      travelFee: data?.travel_info?.travel_fee,
      depositRequired: data?.deposit_required,
    });

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('[Public Quote Proxy] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to calculate quote',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
