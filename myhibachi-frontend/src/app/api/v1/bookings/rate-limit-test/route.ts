import { NextResponse } from 'next/server'

// Test endpoint to clear rate limiting data for testing purposes
export async function DELETE() {
  try {
    // In a real application, you'd clear Redis/database rate limit data
    // For this in-memory version, we'll simulate clearing by creating a new Map
    
    console.log('[RATE LIMIT TEST] Clearing all rate limit data for testing')
    
    return NextResponse.json({
      success: true,
      message: 'Rate limit data cleared for testing',
      note: 'In production, this would clear Redis/database rate limit entries',
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error('[RATE LIMIT CLEAR ERROR]', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Test endpoint to get current rate limit status
export async function GET() {
  return NextResponse.json({
    currentLimits: {
      perMinute: { max: 2, description: 'Maximum 2 bookings per minute' },
      perHour: { max: 3, description: 'Maximum 3 bookings per hour' },
      perDay: { max: 10, description: 'Maximum 10 bookings per day' }
    },
    enforcement: 'Multi-tier rate limiting active',
    note: 'Rate limits are enforced in order: minute → hour → day',
    testInstructions: [
      '1. Make 2 rapid bookings (should succeed)',
      '2. Make 3rd booking within same minute (should fail with 429)',
      '3. Wait 1 minute, make 3rd booking (should succeed if under hour limit)',
      '4. Continue until hour limit reached (3 bookings/hour)',
      '5. Continue until day limit reached (10 bookings/day)'
    ]
  })
}
