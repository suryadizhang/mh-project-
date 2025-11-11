/**
 * Next.js API Route: /api/leads
 * Proxy for lead generation requests to backend
 *
 * This route acts as a proxy between the frontend and the FastAPI backend,
 * providing additional validation, error handling, and logging.
 */

import { NextRequest, NextResponse } from 'next/server'

import { logger } from '@/lib/logger'

const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Valid lead sources
const VALID_SOURCES = [
  'WEB_QUOTE',
  'CHAT',
  'BOOKING_FAILED',
  'INSTAGRAM',
  'FACEBOOK',
  'GOOGLE',
  'SMS',
  'PHONE',
  'REFERRAL',
  'EVENT'
]

// Valid contact channels
const VALID_CHANNELS = ['EMAIL', 'SMS', 'INSTAGRAM', 'FACEBOOK', 'GOOGLE', 'YELP', 'WEB']

/**
 * POST /api/leads
 * Create a new lead
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate required fields
    if (!body.source) {
      return NextResponse.json(
        { error: 'Lead source is required' },
        { status: 400 }
      )
    }

    if (!VALID_SOURCES.includes(body.source)) {
      return NextResponse.json(
        { error: `Invalid lead source. Must be one of: ${VALID_SOURCES.join(', ')}` },
        { status: 400 }
      )
    }

    if (!body.contacts || !Array.isArray(body.contacts) || body.contacts.length === 0) {
      return NextResponse.json(
        { error: 'At least one contact is required' },
        { status: 400 }
      )
    }

    // Validate contacts
    for (const contact of body.contacts) {
      if (!contact.channel || !contact.handle_or_address) {
        return NextResponse.json(
          { error: 'Each contact must have channel and handle_or_address' },
          { status: 400 }
        )
      }

      if (!VALID_CHANNELS.includes(contact.channel)) {
        return NextResponse.json(
          { error: `Invalid contact channel: ${contact.channel}. Must be one of: ${VALID_CHANNELS.join(', ')}` },
          { status: 400 }
        )
      }
    }

    // Validate context if provided
    if (body.context) {
      const context = body.context

      // Validate numeric fields
      if (context.party_size_adults !== undefined && (typeof context.party_size_adults !== 'number' || context.party_size_adults < 0)) {
        return NextResponse.json(
          { error: 'party_size_adults must be a positive number' },
          { status: 400 }
        )
      }

      if (context.party_size_kids !== undefined && (typeof context.party_size_kids !== 'number' || context.party_size_kids < 0)) {
        return NextResponse.json(
          { error: 'party_size_kids must be a positive number' },
          { status: 400 }
        )
      }

      if (context.estimated_budget_dollars !== undefined && (typeof context.estimated_budget_dollars !== 'number' || context.estimated_budget_dollars < 0)) {
        return NextResponse.json(
          { error: 'estimated_budget_dollars must be a positive number' },
          { status: 400 }
        )
      }

      // Validate ZIP code format if provided
      if (context.zip_code && !/^\d{5}(-\d{4})?$/.test(context.zip_code)) {
        return NextResponse.json(
          { error: 'Invalid ZIP code format. Use 12345 or 12345-6789' },
          { status: 400 }
        )
      }
    }

    // Forward request to backend
    logger.debug('Forwarding lead creation to backend', {
      source: body.source,
      utm_campaign: body.utm_campaign
    })

    const backendResponse = await fetch(`${BACKEND_API_URL}/api/v1/leads/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Forwarded-For': request.headers.get('x-forwarded-for') || 'unknown',
        'User-Agent': request.headers.get('user-agent') || 'unknown'
      },
      body: JSON.stringify(body)
    })

    const responseData = await backendResponse.json()

    if (!backendResponse.ok) {
      logger.error('Backend lead creation failed', undefined, {
        status: backendResponse.status,
        error: responseData
      })

      return NextResponse.json(
        {
          error: responseData.detail || responseData.error || 'Failed to create lead',
          details: responseData
        },
        { status: backendResponse.status }
      )
    }

    logger.info('Lead created successfully', {
      leadId: responseData.id,
      source: body.source,
      campaign: body.utm_campaign
    })

    return NextResponse.json(responseData, { status: 201 })

  } catch (error) {
    logger.error('Lead creation error', error as Error)

    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

/**
 * GET /api/leads
 * List leads (for admin/dashboard use)
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Forward query parameters to backend
    const queryString = searchParams.toString()
    const url = `${BACKEND_API_URL}/api/v1/leads/${queryString ? `?${queryString}` : ''}`

    const backendResponse = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const responseData = await backendResponse.json()

    if (!backendResponse.ok) {
      return NextResponse.json(
        {
          error: responseData.detail || 'Failed to fetch leads'
        },
        { status: backendResponse.status }
      )
    }

    return NextResponse.json(responseData)

  } catch (error) {
    logger.error('Lead listing error', error as Error)

    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}
