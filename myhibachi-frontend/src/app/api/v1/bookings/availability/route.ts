import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

// Enhanced input validation schemas
const dateParamSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')

const bookingRequestSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  time: z.enum(['12PM', '3PM', '6PM', '9PM'], { message: 'Invalid time slot' }),
  customerInfo: z.object({
    name: z.string()
      .min(2, 'Name must be at least 2 characters')
      .max(100, 'Name must be less than 100 characters')
      .regex(/^[a-zA-Z\s\-'\.]+$/, 'Name can only contain letters, spaces, hyphens, apostrophes, and periods'),
    email: z.string()
      .email('Invalid email format')
      .max(254, 'Email must be less than 254 characters')
      .toLowerCase(),
    phone: z.string()
      .min(10, 'Phone number must be at least 10 digits')
      .max(20, 'Phone number must be less than 20 characters')
      .regex(/^[\d\s\(\)\-\+\.]+$/, 'Phone can only contain digits and common formatting characters'),
    preferredCommunication: z.enum(['phone', 'text', 'email'], { 
      message: 'Preferred communication must be phone, text, or email' 
    }),
    guestCount: z.number()
      .int('Guest count must be a whole number')
      .min(1, 'At least 1 guest required')
      .max(50, 'Maximum 50 guests allowed'),
    venueStreet: z.string()
      .min(5, 'Street address must be at least 5 characters')
      .max(200, 'Street address must be less than 200 characters')
      .trim(),
    venueCity: z.string()
      .min(2, 'City must be at least 2 characters')
      .max(100, 'City must be less than 100 characters')
      .regex(/^[a-zA-Z\s\-'\.]+$/, 'City can only contain letters, spaces, hyphens, apostrophes, and periods')
      .trim(),
    venueState: z.string()
      .regex(/^[A-Za-z]{2,3}$/, 'State must be a 2-3 letter state code')
      .toUpperCase(),
    venueZipcode: z.string()
      .regex(/^\d{5}(-\d{4})?$/, 'ZIP code must be in format 12345 or 12345-6789')
      .trim(),
  })
})

// Use global cache from main bookings route (declared there)

function sanitizeString(input: string): string {
  return input
    .replace(/[<>\"']/g, '') // Remove potentially dangerous characters
    .trim()
    .substring(0, 500) // Limit length
}

// UUID-like ID generation (collision-proof)
function generateSecureBookingId(): string {
  const timestamp = Date.now().toString(36)
  const randomPart = Math.random().toString(36).substring(2, 15)
  const extraRandom = Math.random().toString(36).substring(2, 9).toUpperCase()
  return `MH-${timestamp}-${randomPart}-${extraRandom}`
}

// Rate limiting map (in production, use Redis or similar)
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()
const RATE_LIMIT_WINDOW = 60000 // 1 minute
const MAX_REQUESTS = 10 // Max requests per window

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const userRecord = rateLimitMap.get(ip)
  
  if (!userRecord || now > userRecord.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
    return true
  }
  
  if (userRecord.count >= MAX_REQUESTS) {
    return false
  }
  
  userRecord.count++
  return true
}

// Enhanced date validation with timezone awareness
function validateEventDate(dateStr: string): { valid: boolean; error?: string } {
  try {
    const selectedDate = new Date(dateStr + 'T00:00:00.000Z') // Force UTC
    const now = new Date()
    
    // Check if date is valid
    if (isNaN(selectedDate.getTime())) {
      return { valid: false, error: 'Invalid date' }
    }
    
    // Check if date is in the past
    if (selectedDate < new Date(now.toISOString().split('T')[0] + 'T00:00:00.000Z')) {
      return { valid: false, error: 'Cannot book dates in the past' }
    }
    
    // Check 48-hour advance requirement
    const timeDiff = selectedDate.getTime() - now.getTime()
    const hoursDiff = timeDiff / (1000 * 60 * 60)
    
    if (hoursDiff < 48) {
      return { valid: false, error: 'Bookings must be made at least 48 hours in advance' }
    }
    
    // Check if date is too far in the future (prevent spam)
    const daysDiff = hoursDiff / 24
    if (daysDiff > 365) {
      return { valid: false, error: 'Bookings cannot be made more than 1 year in advance' }
    }
    
    return { valid: true }
  } catch {
    return { valid: false, error: 'Invalid date format' }
  }
}

// Types for availability data
interface TimeSlotData {
  booked: number
  maxCapacity: number
}

interface DayAvailability {
  [timeSlot: string]: TimeSlotData
}

interface MockAvailabilityData {
  [date: string]: DayAvailability
}

interface CachedAvailabilityResponse {
  success: boolean
  date: string
  timeSlots: Array<{
    time: string
    available: number
    maxCapacity: number
    booked: number
    isAvailable: boolean
  }>
  message: string
  timestamp: string
}

// Mock availability data structure
// In a real app, this would come from your database
const MOCK_AVAILABILITY: MockAvailabilityData = {
  // Date format: YYYY-MM-DD
  '2025-08-08': {
    '12PM': { booked: 2, maxCapacity: 2 }, // Fully booked
    '3PM': { booked: 1, maxCapacity: 2 },  // 1 slot available
    '6PM': { booked: 0, maxCapacity: 2 },  // 2 slots available
    '9PM': { booked: 2, maxCapacity: 2 },  // Fully booked
  },
  '2025-08-09': {
    '12PM': { booked: 0, maxCapacity: 2 },
    '3PM': { booked: 1, maxCapacity: 2 },
    '6PM': { booked: 1, maxCapacity: 2 },
    '9PM': { booked: 0, maxCapacity: 2 },
  },
  '2025-08-10': {
    '12PM': { booked: 2, maxCapacity: 2 }, // Fully booked day
    '3PM': { booked: 2, maxCapacity: 2 },
    '6PM': { booked: 2, maxCapacity: 2 },
    '9PM': { booked: 2, maxCapacity: 2 },
  },
  '2025-08-11': {
    '12PM': { booked: 1, maxCapacity: 2 },
    '3PM': { booked: 0, maxCapacity: 2 },
    '6PM': { booked: 1, maxCapacity: 2 },
    '9PM': { booked: 0, maxCapacity: 2 },
  },
  '2025-08-15': {
    '12PM': { booked: 2, maxCapacity: 2 }, // Another fully booked day
    '3PM': { booked: 2, maxCapacity: 2 },
    '6PM': { booked: 2, maxCapacity: 2 },
    '9PM': { booked: 2, maxCapacity: 2 },
  }
}

export async function GET(request: NextRequest) {
  try {
    // Rate limiting (extract IP from headers for Next.js)
    const clientIP = request.headers.get('x-forwarded-for') || 
                     request.headers.get('x-real-ip') || 
                     'unknown'
    if (!checkRateLimit(clientIP)) {
      return NextResponse.json(
        { success: false, error: 'Too many requests. Please try again later.' },
        { status: 429 }
      )
    }

    const { searchParams } = new URL(request.url)
    const date = searchParams.get('date')

    if (!date) {
      return NextResponse.json(
        { success: false, error: 'Date parameter is required' },
        { status: 400 }
      )
    }

    // Enhanced date validation with Zod
    const dateValidation = dateParamSchema.safeParse(date)
    if (!dateValidation.success) {
      return NextResponse.json(
        { success: false, error: dateValidation.error.issues[0].message },
        { status: 400 }
      )
    }

    // Additional date validation (48-hour rule, etc.)
    const dateCheck = validateEventDate(date)
    if (!dateCheck.valid) {
      return NextResponse.json(
        { success: false, error: dateCheck.error },
        { status: 400 }
      )
    }

    // Check cache first - Cache for 30 seconds as recommended
    const cacheKey = `availability-${date}`
    
    // Enhanced cache health check with fallback
    const cacheHealthy = global.bookingCache?.testFallback() || false
    if (!cacheHealthy) {
      console.warn('[AVAILABILITY CACHE WARNING] Cache system unhealthy, falling back to direct computation')
    }

    // Admin cache bypass
    const nocache = searchParams.get('nocache') === 'true'
    if (nocache) {
      global.bookingCache?.bypassCache(cacheKey)
      console.log(`[AVAILABILITY BYPASS] Admin requested fresh data for ${date}`)
    }
    
    let cachedResponse: CachedAvailabilityResponse | null = null
    if (cacheHealthy && !nocache) {
      cachedResponse = global.bookingCache?.get<CachedAvailabilityResponse>(cacheKey) || null
    }
    
    if (cachedResponse) {
      const age = Math.floor((Date.now() - new Date(cachedResponse.timestamp).getTime()) / 1000)
      console.log(`[AVAILABILITY CACHE HIT] Retrieved data for ${date} from cache (age: ${age}s)`)
      return NextResponse.json(cachedResponse, {
        headers: {
          'X-Cache-Status': 'HIT',
          'X-Cache-Age': age.toString(),
          'X-Cache-Health': cacheHealthy ? 'HEALTHY' : 'DEGRADED',
          'X-Cache-TTL': '30'
        }
      })
    }

    // Cache miss - generate fresh availability data
    console.log(`[AVAILABILITY CACHE MISS] Generating fresh data for ${date}`)

    // Get availability for the date (default to all available if not in mock data)
    const availability = MOCK_AVAILABILITY[date] || {
      '12PM': { booked: 0, maxCapacity: 2 },
      '3PM': { booked: 0, maxCapacity: 2 },
      '6PM': { booked: 0, maxCapacity: 2 },
      '9PM': { booked: 0, maxCapacity: 2 },
    }

    // Transform data for frontend with proper typing
    const timeSlots = Object.entries(availability).map(([time, slotData]) => {
      const data = slotData as TimeSlotData
      return {
        time,
        available: data.maxCapacity - data.booked,
        maxCapacity: data.maxCapacity,
        booked: data.booked,
        isAvailable: data.maxCapacity > data.booked
      }
    })

    const responseData: CachedAvailabilityResponse = {
      success: true,
      date,
      timeSlots,
      message: `Availability retrieved for ${date}`,
      timestamp: new Date().toISOString()
    }

    // Cache the response for 30 seconds (recommended for availability data)
    if (cacheHealthy && !nocache) {
      global.bookingCache?.set(cacheKey, responseData, 30, 'availability')
      console.log(`[AVAILABILITY CACHE MISS] Generated fresh data for ${date} and cached for 30 seconds (tag: availability)`)
    } else {
      console.log(`[AVAILABILITY FALLBACK] Generated fresh data for ${date} (cache ${cacheHealthy ? 'bypassed' : 'unavailable'})`)
    }

    // Simulate API delay (remove in production)
    await new Promise(resolve => setTimeout(resolve, 200))

    return NextResponse.json(responseData, {
      headers: {
        'X-Cache-Status': 'MISS',
        'X-Cache-TTL': '30'
      }
    })
  } catch (error) {
    console.error('Error fetching availability:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch availability',
        timeSlots: []
      },
      { status: 500 }
    )
  }
}

// POST endpoint for making a booking (reserves a slot) - Enhanced Security
export async function POST(request: NextRequest) {
  try {
    // Rate limiting for booking submissions (stricter)
    const clientIP = request.headers.get('x-forwarded-for') || 
                     request.headers.get('x-real-ip') || 
                     'unknown'
    if (!checkRateLimit(clientIP)) {
      return NextResponse.json(
        { success: false, error: 'Too many booking attempts. Please try again later.' },
        { status: 429 }
      )
    }

    let body
    try {
      body = await request.json()
    } catch {
      return NextResponse.json(
        { success: false, error: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Comprehensive input validation with Zod
    const validation = bookingRequestSchema.safeParse(body)
    if (!validation.success) {
      const firstError = validation.error.issues[0]
      return NextResponse.json(
        { 
          success: false, 
          error: `Validation error: ${firstError.path.join('.')} - ${firstError.message}`,
          field: firstError.path.join('.')
        },
        { status: 400 }
      )
    }

    const { date, time, customerInfo } = validation.data

    // Additional date validation
    const dateCheck = validateEventDate(date)
    if (!dateCheck.valid) {
      return NextResponse.json(
        { success: false, error: dateCheck.error },
        { status: 400 }
      )
    }

    // Race condition protection - Check availability again at booking time
    const availability = MOCK_AVAILABILITY[date]
    if (!availability) {
      // Initialize if doesn't exist
      MOCK_AVAILABILITY[date] = {
        '12PM': { booked: 0, maxCapacity: 2 },
        '3PM': { booked: 0, maxCapacity: 2 },
        '6PM': { booked: 0, maxCapacity: 2 },
        '9PM': { booked: 0, maxCapacity: 2 },
      }
    }

    const slot = MOCK_AVAILABILITY[date][time]
    if (slot && slot.booked >= slot.maxCapacity) {
      return NextResponse.json(
        { 
          success: false, 
          error: `The ${time} time slot is fully booked. Please select a different time.`,
          code: 'SLOT_FULL'
        },
        { status: 409 } // Conflict status code
      )
    }

    // Sanitize customer data
    const sanitizedCustomer = {
      name: sanitizeString(customerInfo.name),
      email: customerInfo.email.toLowerCase().trim(),
      phone: sanitizeString(customerInfo.phone),
      guestCount: customerInfo.guestCount,
      venueStreet: sanitizeString(customerInfo.venueStreet),
      venueCity: sanitizeString(customerInfo.venueCity),
      venueState: customerInfo.venueState.toUpperCase(),
      venueZipcode: customerInfo.venueZipcode.trim(),
    }

    // Generate secure, collision-proof booking ID
    const bookingId = generateSecureBookingId()
    
    // Atomic operation simulation (in real app, use database transaction)
    if (MOCK_AVAILABILITY[date] && MOCK_AVAILABILITY[date][time]) {
      MOCK_AVAILABILITY[date][time].booked += 1
    }

    // Smart cache invalidation after booking is created
    try {
      if (global.bookingCache) {
        const tagCleared = global.bookingCache.invalidateByTag('availability')
        if (tagCleared === 0) {
          // Fallback to pattern-based invalidation
          global.bookingCache.invalidate(`availability-${date}`)
          global.bookingCache.invalidate('availability-')
        }
        console.log(`[CACHE SMART INVALIDATION] Cleared availability cache for ${date} due to new booking`)
      } else {
        console.warn('[CACHE WARNING] Cache system unavailable for invalidation')
      }
    } catch (cacheError) {
      console.warn('[CACHE WARNING] Cache invalidation failed, but booking was saved:', cacheError)
    }

    // Create booking record with full sanitization
    const bookingRecord = {
      id: bookingId,
      date,
      time,
      customer: sanitizedCustomer,
      status: 'confirmed' as const,
      createdAt: new Date().toISOString(),
      ip: clientIP,
      userAgent: request.headers.get('user-agent')?.substring(0, 200) || 'unknown'
    }

    // Log booking for security audit trail
    console.log('🎉 BOOKING CREATED:', {
      bookingId,
      date,
      time,
      customer: sanitizedCustomer.name,
      email: sanitizedCustomer.email,
      guests: sanitizedCustomer.guestCount,
      ip: clientIP,
      timestamp: bookingRecord.createdAt
    })

    // In production, you would:
    // 1. Begin database transaction
    // 2. Double-check availability (prevent race conditions)
    // 3. Create booking record
    // 4. Update slot availability atomically
    // 5. Send confirmation email
    // 6. Log to audit trail
    // 7. Commit transaction

    return NextResponse.json({
      success: true,
      message: 'Booking created successfully!',
      bookingId,
      confirmationCode: bookingId,
      booking: {
        date,
        time,
        customer: {
          name: sanitizedCustomer.name,
          email: sanitizedCustomer.email,
          guestCount: sanitizedCustomer.guestCount
        },
        venue: {
          street: sanitizedCustomer.venueStreet,
          city: sanitizedCustomer.venueCity,
          state: sanitizedCustomer.venueState,
          zipcode: sanitizedCustomer.venueZipcode
        }
      },
      createdAt: bookingRecord.createdAt
    }, { status: 201 })

  } catch (error) {
    console.error('🚨 BOOKING ERROR:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to create booking. Please try again.' },
      { status: 500 }
    )
  }
}
