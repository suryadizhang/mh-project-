/**
 * Proxy route for quote email endpoint
 *
 * This route proxies POST requests to the backend API to avoid CORS issues.
 * The backend handles sending the email with the quote details.
 *
 * Endpoint: POST /api/v1/public/quote/email
 */

import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://mhapi.mysticdatanode.net';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    console.log('[Quote Email Proxy] Sending email request to backend');

    const response = await fetch(`${API_URL}/api/v1/public/quote/email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('[Quote Email Proxy] Backend error:', data);
      return NextResponse.json(
        { error: data.detail || data.message || 'Failed to send email' },
        { status: response.status },
      );
    }

    console.log('[Quote Email Proxy] Email sent successfully');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Quote Email Proxy] Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 },
    );
  }
}
