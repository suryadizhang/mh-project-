import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { emailService, type BookingEmailData } from '@/lib/email-service'
import { emailScheduler } from '@/lib/email-scheduler'

// Enhanced validation schema with comprehensive security patterns
const createBookingSchema = z.object({
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name must be less than 50 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Name can only contain letters, spaces, hyphens, apostrophes, and periods'),
  email: z.string()
    .email('Invalid email address')
    .min(5, 'Email must be at least 5 characters')
    .max(100, 'Email must be less than 100 characters')
    .toLowerCase(),
  phone: z.string()
    .min(10, 'Phone must be at least 10 digits')
    .max(20, 'Phone number must be less than 20 characters')
    .regex(/^[\d\s\(\)\-\+\.]+$/, 'Phone can only contain digits and common formatting characters'),
  event_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (YYYY-MM-DD)'),
  event_time: z.enum(['12PM', '3PM', '6PM', '9PM'], { message: 'Invalid time slot' }),
  guestCount: z.number()
    .int('Guest count must be a whole number')
    .min(1, 'At least 1 guest required')
    .max(50, 'Maximum 50 guests allowed'),
  address_street: z.string()
    .min(5, 'Street address must be at least 5 characters')
    .max(200, 'Street address must be less than 200 characters')
    .trim(),
  address_city: z.string()
    .min(2, 'City must be at least 2 characters')
    .max(100, 'City must be less than 100 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'City can only contain letters, spaces, hyphens, apostrophes, and periods')
    .trim(),
  address_state: z.string()
    .regex(/^[A-Za-z]{2,3}$/, 'State must be a 2-3 letter state code')
    .toUpperCase(),
  address_zipcode: z.string()
    .regex(/^\d{5}(-\d{4})?$/, 'ZIP code must be in format 12345 or 12345-6789')
    .trim(),
  venue_street: z.string()
    .min(5, 'Venue street must be at least 5 characters')
    .max(200, 'Venue street must be less than 200 characters')
    .trim(),
  venue_city: z.string()
    .min(2, 'Venue city must be at least 2 characters')
    .max(100, 'Venue city must be less than 100 characters')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Venue city can only contain letters, spaces, hyphens, apostrophes, and periods')
    .trim(),
  venue_state: z.string()
    .regex(/^[A-Za-z]{2,3}$/, 'Venue state must be a 2-3 letter state code')
    .toUpperCase(),
  venue_zipcode: z.string()
    .regex(/^\d{5}(-\d{4})?$/, 'Venue ZIP code must be in format 12345 or 12345-6789')
    .trim(),
})

// Enhanced booking interface with security and audit fields
interface Booking {
  id: string
  name: string
  email: string
  phone: string
  event_date: string
  event_time: string
  guestCount: number
  address_street: string
  address_city: string
  address_state: string
  address_zipcode: string
  venue_street: string
  venue_city: string
  venue_state: string
  venue_zipcode: string
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed'
  created_at: string
  ip_address?: string
  user_agent?: string
  last_modified_at: string
}

// Interface for cached booking data
interface CachedBookingData {
  total: number
  bookings: Omit<Booking, 'ip_address' | 'user_agent' | 'address_street' | 'address_city' | 'address_state' | 'address_zipcode' | 'venue_street' | 'venue_city' | 'venue_state' | 'venue_zipcode'>[]
  timestamp: number
}

// In-memory storage (replace with database in production)
const bookings: Booking[] = []

// Enhanced caching system with enterprise observability and fallback (Redis-ready)
interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresAt: number
  hits: number
  tag?: string
}

interface CacheStats {
  hits: number
  misses: number
  expirations: number
  errors: number
  totalKeys: number
  hitRatio: number
  mostPopularKeys: Array<{ key: string; hits: number }>
  memoryUsage: number
}

class EnterpriseMemoryCache {
  private cache = new Map<string, CacheEntry<unknown>>()
  private stats = {
    hits: 0,
    misses: 0,
    expirations: 0,
    errors: 0
  }
  private tags = new Map<string, Set<string>>() // Tag-based invalidation

  set<T>(key: string, data: T, ttlSeconds: number, tag?: string): void {
    try {
      const now = Date.now()
      this.cache.set(key, {
        data,
        timestamp: now,
        expiresAt: now + (ttlSeconds * 1000),
        hits: 0,
        tag
      })

      // Track tags for smart invalidation
      if (tag) {
        if (!this.tags.has(tag)) {
          this.tags.set(tag, new Set())
        }
        this.tags.get(tag)!.add(key)
      }

      console.log(`[CACHE SET] ${key} (TTL: ${ttlSeconds}s${tag ? `, tag: ${tag}` : ''})`)
    } catch (error) {
      this.stats.errors++
      console.error(`[CACHE ERROR] Failed to set ${key}:`, error)
    }
  }

  get<T>(key: string): T | null {
    try {
      const entry = this.cache.get(key) as CacheEntry<T> | undefined

      if (!entry) {
        this.stats.misses++
        console.log(`[CACHE MISS] ${key}`)
        return null
      }

      // Check TTL expiration
      if (Date.now() > entry.expiresAt) {
        this.cache.delete(key)
        this.stats.expirations++
        this.stats.misses++
        console.log(`[CACHE EXPIRED] ${key} (expired ${Math.round((Date.now() - entry.expiresAt) / 1000)}s ago)`)
        return null
      }

      // Track hit statistics
      entry.hits++
      this.stats.hits++
      const age = Math.round((Date.now() - entry.timestamp) / 1000)
      console.log(`[CACHE HIT] ${key} (age: ${age}s, hits: ${entry.hits})`)

      return entry.data as T
    } catch (error) {
      this.stats.errors++
      this.stats.misses++ // Treat errors as misses for fallback
      console.error(`[CACHE ERROR] Failed to get ${key}:`, error)
      return null
    }
  }

  // Pattern-based invalidation with enhanced logging
  invalidate(pattern: string): number {
    try {
      const keysToDelete = Array.from(this.cache.keys()).filter(key =>
        key.includes(pattern) || key.startsWith(pattern)
      )

      keysToDelete.forEach(key => {
        const entry = this.cache.get(key)
        if (entry?.tag) {
          // Clean up tag references
          const tagSet = this.tags.get(entry.tag)
          if (tagSet) {
            tagSet.delete(key)
            if (tagSet.size === 0) {
              this.tags.delete(entry.tag)
            }
          }
        }
        this.cache.delete(key)
      })

      console.log(`[CACHE INVALIDATED] Cleared ${keysToDelete.length} entries matching pattern: ${pattern}`)
      return keysToDelete.length
    } catch (error) {
      this.stats.errors++
      console.error(`[CACHE ERROR] Failed to invalidate pattern ${pattern}:`, error)
      return 0
    }
  }

  // Tag-based invalidation for smart cache management
  invalidateByTag(tag: string): number {
    try {
      const keys = this.tags.get(tag)
      if (!keys) {
        console.log(`[CACHE TAG] No keys found for tag: ${tag}`)
        return 0
      }

      let deletedCount = 0
      keys.forEach(key => {
        if (this.cache.delete(key)) {
          deletedCount++
        }
      })

      this.tags.delete(tag)
      console.log(`[CACHE TAG INVALIDATED] Cleared ${deletedCount} entries for tag: ${tag}`)
      return deletedCount
    } catch (error) {
      this.stats.errors++
      console.error(`[CACHE ERROR] Failed to invalidate tag ${tag}:`, error)
      return 0
    }
  }

  // Graceful fallback test
  testFallback(): boolean {
    try {
      // Simulate cache failure
      const testKey = '__health_check__'
      this.set(testKey, { test: true }, 1)
      const result = this.get(testKey)
      this.cache.delete(testKey)
      return result !== null
    } catch (error) {
      console.error('[CACHE HEALTH CHECK] Cache system unhealthy:', error)
      return false
    }
  }

  // Enhanced statistics for production monitoring
  getAdvancedStats(): CacheStats {
    const totalRequests = this.stats.hits + this.stats.misses
    const hitRatio = totalRequests > 0 ? this.stats.hits / totalRequests : 0

    // Get most popular cache keys
    const keyHits = Array.from(this.cache.entries())
      .map(([key, entry]) => ({ key, hits: entry.hits }))
      .sort((a, b) => b.hits - a.hits)
      .slice(0, 5)

    // Estimate memory usage (rough calculation)
    const memoryUsage = Array.from(this.cache.values())
      .reduce((total, entry) => total + JSON.stringify(entry.data).length, 0)

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      expirations: this.stats.expirations,
      errors: this.stats.errors,
      totalKeys: this.cache.size,
      hitRatio: Math.round(hitRatio * 100) / 100,
      mostPopularKeys: keyHits,
      memoryUsage: Math.round(memoryUsage / 1024) // KB
    }
  }

  // Production-ready cache bypass for admin routes
  bypassCache(key: string): void {
    console.log(`[CACHE BYPASS] Forcing cache miss for: ${key}`)
    this.cache.delete(key)
  }

  // Cleanup expired entries (background process)
  cleanup(): number {
    let cleanedCount = 0
    const now = Date.now()

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key)

        // Clean up tag references
        if (entry.tag) {
          const tagSet = this.tags.get(entry.tag)
          if (tagSet) {
            tagSet.delete(key)
            if (tagSet.size === 0) {
              this.tags.delete(entry.tag)
            }
          }
        }

        cleanedCount++
      }
    }

    if (cleanedCount > 0) {
      console.log(`[CACHE CLEANUP] Removed ${cleanedCount} expired entries`)
    }

    return cleanedCount
  }

  clear(): void {
    this.cache.clear()
    this.tags.clear()
    console.log('[CACHE CLEARED] All cache entries removed')
  }

  // Legacy stats method for compatibility
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    }
  }
}

// Global enterprise cache instance with background cleanup
const cache = new EnterpriseMemoryCache()

// Make cache globally accessible for monitoring
declare global {
  var bookingCache: EnterpriseMemoryCache | undefined
}

global.bookingCache = cache

// Background cleanup process - runs every 5 minutes
setInterval(() => {
  cache.cleanup()
}, 5 * 60 * 1000)

// Multi-tier rate limiting store (in production, use Redis or similar)
interface RateLimitData {
  minute: { count: number; resetTime: number }
  hour: { count: number; resetTime: number }
  day: { count: number; resetTime: number }
}

const rateLimitStore = new Map<string, RateLimitData>()

// Utility functions
function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

function sanitizeInput(input: string): string {
  return input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .trim()
}

function checkRateLimit(clientId: string): { allowed: boolean; error?: string; retryAfter?: number } {
  const now = Date.now()
  let clientLimits = rateLimitStore.get(clientId)

  // Initialize rate limiting data if not exists
  if (!clientLimits) {
    clientLimits = {
      minute: { count: 0, resetTime: now + 60000 },      // 1 minute window
      hour: { count: 0, resetTime: now + 3600000 },      // 1 hour window
      day: { count: 0, resetTime: now + 86400000 }       // 24 hour window
    }
    rateLimitStore.set(clientId, clientLimits)
  }

  // Reset counters if time windows have passed
  if (now > clientLimits.minute.resetTime) {
    clientLimits.minute = { count: 0, resetTime: now + 60000 }
  }
  if (now > clientLimits.hour.resetTime) {
    clientLimits.hour = { count: 0, resetTime: now + 3600000 }
  }
  if (now > clientLimits.day.resetTime) {
    clientLimits.day = { count: 0, resetTime: now + 86400000 }
  }

  // Check limits (most restrictive first)
  if (clientLimits.minute.count >= 2) {
    return {
      allowed: false,
      error: 'Too many booking requests. Maximum 2 bookings per minute allowed.',
      retryAfter: Math.ceil((clientLimits.minute.resetTime - now) / 1000)
    }
  }

  if (clientLimits.hour.count >= 3) {
    return {
      allowed: false,
      error: 'Hourly booking limit exceeded. Maximum 3 bookings per hour allowed.',
      retryAfter: Math.ceil((clientLimits.hour.resetTime - now) / 1000)
    }
  }

  if (clientLimits.day.count >= 10) {
    return {
      allowed: false,
      error: 'Daily booking limit exceeded. Maximum 10 bookings per day allowed.',
      retryAfter: Math.ceil((clientLimits.day.resetTime - now) / 1000)
    }
  }

  // Increment all counters
  clientLimits.minute.count++
  clientLimits.hour.count++
  clientLimits.day.count++

  // Update the store
  rateLimitStore.set(clientId, clientLimits)

  return { allowed: true }
}

function getClientId(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for')
  const ip = forwarded ? forwarded.split(',')[0] : 'unknown'
  const userAgent = request.headers.get('user-agent') || 'unknown'
  return `${ip}-${Buffer.from(userAgent).toString('base64').slice(0, 10)}`
}

function isDateAtLeastTwoDaysInAdvance(dateString: string): boolean {
  const eventDate = new Date(dateString)
  const today = new Date()
  const twoDaysFromNow = new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000)

  // Reset time to start of day for accurate comparison
  eventDate.setHours(0, 0, 0, 0)
  twoDaysFromNow.setHours(0, 0, 0, 0)

  return eventDate >= twoDaysFromNow
}

export async function POST(request: NextRequest) {
  try {
    const clientId = getClientId(request)

    // Check multi-tier rate limiting
    const rateLimitResult = checkRateLimit(clientId)
    if (!rateLimitResult.allowed) {
      return NextResponse.json(
        {
          detail: rateLimitResult.error,
          retryAfter: rateLimitResult.retryAfter,
          limits: {
            perMinute: '2 bookings maximum',
            perHour: '3 bookings maximum',
            perDay: '10 bookings maximum'
          }
        },
        {
          status: 429,
          headers: {
            'Retry-After': rateLimitResult.retryAfter?.toString() || '60',
            'X-RateLimit-Limit-Minute': '2',
            'X-RateLimit-Limit-Hour': '3',
            'X-RateLimit-Limit-Day': '10'
          }
        }
      )
    }

    const body = await request.json()

    // Sanitize all string inputs to prevent XSS
    const sanitizedBody = {
      ...body,
      name: sanitizeInput(body.name || ''),
      email: sanitizeInput(body.email || '').toLowerCase(),
      phone: sanitizeInput(body.phone || ''),
      address_street: sanitizeInput(body.address_street || ''),
      address_city: sanitizeInput(body.address_city || ''),
      address_state: sanitizeInput(body.address_state || '').toUpperCase(),
      address_zipcode: sanitizeInput(body.address_zipcode || ''),
      venue_street: sanitizeInput(body.venue_street || ''),
      venue_city: sanitizeInput(body.venue_city || ''),
      venue_state: sanitizeInput(body.venue_state || '').toUpperCase(),
      venue_zipcode: sanitizeInput(body.venue_zipcode || ''),
    }

    // Validate the request body
    const validationResult = createBookingSchema.safeParse(sanitizedBody)

    if (!validationResult.success) {
      return NextResponse.json(
        {
          detail: 'Validation error',
          errors: validationResult.error.issues.map(issue => ({
            field: issue.path.join('.'),
            message: issue.message
          }))
        },
        { status: 400 }
      )
    }

    const data = validationResult.data

    // Check if the date is at least 2 days in advance (48 hours)
    if (!isDateAtLeastTwoDaysInAdvance(data.event_date)) {
      return NextResponse.json(
        { detail: 'Event date must be at least 48 hours (2 days) in advance' },
        { status: 400 }
      )
    }

    // Check if the time slot is available (with race condition protection)
    const existingBookingCount = bookings.filter(booking =>
      booking.event_date === data.event_date &&
      booking.event_time === data.event_time &&
      booking.status !== 'cancelled'
    ).length

    if (existingBookingCount >= 2) { // Maximum 2 bookings per time slot
      return NextResponse.json(
        {
          detail: 'This time slot is fully booked. Please select a different time.',
          available_slots: 0,
          max_slots: 2
        },
        { status: 409 }
      )
    }

    const currentTime = new Date().toISOString()

    // Create the booking with enhanced security fields
    const newBooking: Booking = {
      id: generateId(),
      name: data.name,
      email: data.email,
      phone: data.phone,
      event_date: data.event_date,
      event_time: data.event_time,
      guestCount: data.guestCount,
      address_street: data.address_street,
      address_city: data.address_city,
      address_state: data.address_state,
      address_zipcode: data.address_zipcode,
      venue_street: data.venue_street,
      venue_city: data.venue_city,
      venue_state: data.venue_state,
      venue_zipcode: data.venue_zipcode,
      status: 'pending',
      created_at: currentTime,
      last_modified_at: currentTime,
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || 'unknown'
    }

    // Save the booking (atomic operation simulation with fallback)
    bookings.push(newBooking)

    // Smart cache invalidation with tag-based and pattern-based clearing
    try {
      // Tag-based invalidation for efficient cache management
      const bookingTagCleared = cache.invalidateByTag('bookings')
      const availabilityTagCleared = cache.invalidateByTag('availability')
      const datesTagCleared = cache.invalidateByTag('booked-dates')

      // Pattern-based fallback if tags aren't available
      if (bookingTagCleared === 0 && availabilityTagCleared === 0 && datesTagCleared === 0) {
        cache.invalidate('booked-dates')
        cache.invalidate('availability')
        cache.invalidate('bookings-list')
        console.log('[CACHE FALLBACK] Used pattern-based invalidation as fallback')
      }

      console.log(`[CACHE SMART INVALIDATION] Tags cleared - bookings: ${bookingTagCleared}, availability: ${availabilityTagCleared}, dates: ${datesTagCleared}`)
    } catch (cacheError) {
      console.warn('[CACHE WARNING] Cache invalidation failed, but booking was saved:', cacheError)
      // Booking still succeeds even if cache invalidation fails
    }

    // 🎉 EMAIL AUTOMATION: Send confirmation and schedule follow-ups
    try {
      // Prepare email data
      const emailData: BookingEmailData = {
        customerName: newBooking.name,
        customerEmail: newBooking.email,
        bookingId: newBooking.id,
        eventDate: newBooking.event_date,
        eventTime: newBooking.event_time,
        guestCount: newBooking.guestCount,
        venueAddress: {
          street: newBooking.venue_street,
          city: newBooking.venue_city,
          state: newBooking.venue_state,
          zipcode: newBooking.venue_zipcode
        },
        confirmationNumber: `MH-${newBooking.event_date.replace(/-/g, '')}-${newBooking.id.slice(-4).toUpperCase()}`
      }

      // 1. Send immediate booking confirmation email
      const confirmationSent = await emailService.sendBookingConfirmation(emailData)
      console.log(`[EMAIL AUTOMATION] Booking confirmation ${confirmationSent ? 'sent' : 'failed'} to ${newBooking.email}`)

      // 2. Schedule review request email (24 hours after event)
      emailScheduler.scheduleReviewRequest(
        newBooking.id,
        newBooking.event_date,
        newBooking.event_time,
        newBooking.email,
        emailData
      )

      // 3. Schedule upsell email (30 days after booking)
      emailScheduler.scheduleUpsellEmail(
        newBooking.id,
        newBooking.email,
        emailData
      )

      console.log(`[EMAIL AUTOMATION] Scheduled follow-up emails for booking ${newBooking.id}`)

    } catch (emailError) {
      console.error('[EMAIL ERROR] Email automation failed, but booking was saved:', emailError)
      // Don't fail the booking if email fails - email is enhancement, not core functionality
    }

    // Log successful booking creation with rate limit info (audit trail)
    const currentLimits = rateLimitStore.get(clientId)
    console.log(`[BOOKING CREATED] ID: ${newBooking.id}, Date: ${newBooking.event_date}, Time: ${newBooking.event_time}, Client: ${clientId}, Limits: ${currentLimits?.minute.count}/2 min, ${currentLimits?.hour.count}/3 hr, ${currentLimits?.day.count}/10 day`)
    console.log(`[CACHE INVALIDATED] Cleared availability and booked-dates cache due to new booking`)

    // Return success response with booking details and rate limit headers
    return NextResponse.json(
      {
        id: newBooking.id,
        message: 'Booking created successfully',
        booking: {
          id: newBooking.id,
          event_date: newBooking.event_date,
          event_time: newBooking.event_time,
          guestCount: newBooking.guestCount,
          status: newBooking.status,
          created_at: newBooking.created_at
        }
      },
      {
        status: 201,
        headers: {
          'X-RateLimit-Remaining-Minute': (2 - (currentLimits?.minute.count || 0)).toString(),
          'X-RateLimit-Remaining-Hour': (3 - (currentLimits?.hour.count || 0)).toString(),
          'X-RateLimit-Remaining-Day': (10 - (currentLimits?.day.count || 0)).toString()
        }
      }
    )

  } catch (error) {
    console.error('[BOOKING ERROR]', error)
    return NextResponse.json(
      { detail: 'Internal server error. Please try again later.' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    // Enhanced cache health check with fallback
    const cacheHealthy = cache.testFallback()
    if (!cacheHealthy) {
      console.warn('[CACHE WARNING] Cache system unhealthy, falling back to direct DB access')
    }

    const url = new URL(request.url)
    const nocache = url.searchParams.get('nocache') === 'true' // Admin bypass
    const includeStats = url.searchParams.get('stats') === 'true' // Performance monitoring

    // Admin cache bypass
    if (nocache) {
      cache.bypassCache('bookings-list')
      console.log('[CACHE BYPASS] Admin requested fresh data, bypassing cache')
    }

    // Try to get cached bookings list with graceful fallback
    const cacheKey = 'bookings-list'
    let cachedBookings: CachedBookingData | null = null

    if (cacheHealthy && !nocache) {
      cachedBookings = cache.get<CachedBookingData>(cacheKey)
    }

    if (cachedBookings) {
      const age = Math.floor((Date.now() - cachedBookings.timestamp) / 1000)
      console.log(`[CACHE HIT] Retrieved bookings list from cache (age: ${age}s)`)

      const response = {
        total: cachedBookings.total,
        bookings: cachedBookings.bookings,
        ...(includeStats && { cacheStats: cache.getAdvancedStats() })
      }

      return NextResponse.json(response, {
        headers: {
          'X-Cache-Status': 'HIT',
          'X-Cache-Age': age.toString(),
          'X-Cache-Health': cacheHealthy ? 'HEALTHY' : 'DEGRADED'
        }
      })
    }

    // Cache miss or bypass - generate fresh data with error handling
    try {
      const bookingsData: CachedBookingData = {
        total: bookings.length,
        bookings: bookings.map(booking => ({
          id: booking.id,
          name: booking.name,
          email: booking.email,
          phone: booking.phone,
          event_date: booking.event_date,
          event_time: booking.event_time,
          guestCount: booking.guestCount,
          status: booking.status,
          created_at: booking.created_at,
          last_modified_at: booking.last_modified_at
        })),
        timestamp: Date.now()
      }

      // Cache with tag-based invalidation (if cache is healthy)
      if (cacheHealthy && !nocache) {
        cache.set(cacheKey, bookingsData, 300, 'bookings') // 5 minutes with 'bookings' tag
        console.log(`[CACHE MISS] Generated fresh bookings list and cached for 5 minutes (tag: bookings)`)
      } else {
        console.log(`[CACHE FALLBACK] Generated fresh bookings list (cache ${cacheHealthy ? 'bypassed' : 'unavailable'})`)
      }

      const response = {
        total: bookingsData.total,
        bookings: bookingsData.bookings,
        ...(includeStats && { cacheStats: cache.getAdvancedStats() })
      }

      return NextResponse.json(response, {
        headers: {
          'X-Cache-Status': nocache ? 'BYPASS' : 'MISS',
          'X-Cache-TTL': cacheHealthy && !nocache ? '300' : '0',
          'X-Cache-Health': cacheHealthy ? 'HEALTHY' : 'DEGRADED',
          'Cache-Control': 'private, max-age=60' // CDN/browser caching
        }
      })
    } catch (dbError) {
      console.error('[DATABASE ERROR] Failed to fetch bookings from storage:', dbError)
      return NextResponse.json(
        {
          detail: 'Database temporarily unavailable. Please try again later.',
          error: 'STORAGE_ERROR'
        },
        { status: 503 }
      )
    }
  } catch (error) {
    console.error('[BOOKING FETCH ERROR]', error)
    return NextResponse.json(
      {
        detail: 'Internal server error',
        error: 'SYSTEM_ERROR'
      },
      { status: 500 }
    )
  }
}
