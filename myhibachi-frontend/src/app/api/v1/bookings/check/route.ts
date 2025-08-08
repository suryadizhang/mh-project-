import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

// Validation schema for availability check
const checkAvailabilitySchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format'),
  time: z.enum(['12PM', '3PM', '6PM', '9PM'], {
    message: 'Invalid time slot'
  })
})

// In-memory storage interface (should match the bookings array from route.ts)
interface Booking {
  id: string
  name: string
  email: string
  phone: string
  event_date: string
  event_time: string
  address_street: string
  address_city: string
  address_state: string
  address_zipcode: string
  venue_street: string
  venue_city: string
  venue_state: string
  venue_zipcode: string
  status: string
  created_at: string
}

// In-memory storage (same reference as in route.ts)
// In a real application, this would be a database query
const bookings: Booking[] = []

function isDateAtLeastTwoDaysInAdvance(dateString: string): boolean {
  const eventDate = new Date(dateString)
  const today = new Date()
  const twoDaysFromNow = new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000)
  
  // Reset time to start of day for accurate comparison
  eventDate.setHours(0, 0, 0, 0)
  twoDaysFromNow.setHours(0, 0, 0, 0)
  
  return eventDate >= twoDaysFromNow
}

function isTimeSlotAvailable(date: string, time: string): boolean {
  return !bookings.some(booking => 
    booking.event_date === date && 
    booking.event_time === time &&
    booking.status !== 'cancelled'
  )
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const date = searchParams.get('date')
    const time = searchParams.get('time')
    
    // Validate query parameters
    const validationResult = checkAvailabilitySchema.safeParse({ date, time })
    
    if (!validationResult.success) {
      return NextResponse.json(
        { 
          detail: 'Invalid parameters',
          errors: validationResult.error.issues
        },
        { status: 400 }
      )
    }
    
    const { date: validDate, time: validTime } = validationResult.data
    
    // Check if the date is at least 2 days in advance
    if (!isDateAtLeastTwoDaysInAdvance(validDate)) {
      return NextResponse.json({
        available: false,
        reason: 'Date must be at least 2 days in advance'
      })
    }
    
    // Check if the time slot is available
    const available = isTimeSlotAvailable(validDate, validTime)
    
    return NextResponse.json({
      available,
      date: validDate,
      time: validTime,
      ...(available ? {} : { reason: 'Time slot is already booked' })
    })
    
  } catch (error) {
    console.error('Error checking availability:', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}
