import { NextRequest, NextResponse } from 'next/server'

// Same client ID generation as bookings endpoint
function getClientId(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for')
  const ip = forwarded ? forwarded.split(',')[0] : 'unknown'
  const userAgent = request.headers.get('user-agent') || 'unknown'
  return `${ip}-${Buffer.from(userAgent).toString('base64').slice(0, 10)}`
}

// Import the rate limit store (in production, this would be shared through Redis/database)
// For now, we'll create a simple endpoint to check current limits
export async function GET(request: NextRequest) {
  try {
    const clientId = getClientId(request)
    const now = Date.now()
    
    // This is a simplified version - in production you'd access the shared rate limit store
    return NextResponse.json({
      clientId: clientId.substring(0, 20) + '...', // Partially obscure for privacy
      limits: {
        perMinute: {
          max: 2,
          window: '60 seconds',
          remaining: 'Check booking response headers'
        },
        perHour: {
          max: 3,
          window: '1 hour',
          remaining: 'Check booking response headers'
        },
        perDay: {
          max: 10,
          window: '24 hours',
          remaining: 'Check booking response headers'
        }
      },
      message: 'Rate limit information. Actual remaining counts are provided in booking response headers.',
      timestamp: new Date(now).toISOString(),
      headers: {
        'X-RateLimit-Remaining-Minute': 'Provided after booking attempts',
        'X-RateLimit-Remaining-Hour': 'Provided after booking attempts',
        'X-RateLimit-Remaining-Day': 'Provided after booking attempts'
      }
    })
  } catch (error) {
    console.error('[RATE LIMIT STATUS ERROR]', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}
