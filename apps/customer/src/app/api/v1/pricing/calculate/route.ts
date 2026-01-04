/**
 * Pricing Calculate Proxy API Route
 *
 * Proxies POST requests to the backend API to avoid CORS issues.
 * Used for calculating party quotes with travel fees.
 *
 * POST /api/v1/pricing/calculate → Backend /api/v1/pricing/calculate
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const body = await request.json();

    console.log('[Pricing Calculate Proxy] Calculating quote:', {
      adults: body?.adults,
      children: body?.children,
      hasAddress: !!body?.customer_address,
      hasZipcode: !!body?.customer_zipcode,
    });

    const response = await fetch(`${apiUrl}/api/v1/pricing/calculate`, {
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
        `[Pricing Calculate Proxy] Backend returned ${response.status}: ${response.statusText}`,
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

    console.log('[Pricing Calculate Proxy] Quote calculated successfully:', {
      grandTotal: data?.totals?.grand_total,
      travelFee: data?.travel_fee?.travel_fee,
      meetsMinimum: data?.minimum_enforcement?.meets_minimum,
    });

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('[Pricing Calculate Proxy] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to calculate quote',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
