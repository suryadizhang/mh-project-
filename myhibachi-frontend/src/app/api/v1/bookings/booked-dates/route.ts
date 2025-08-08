import { NextResponse } from 'next/server'

// Enhanced caching system for booked dates
interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresAt: number
}

class MemoryCache {
  private cache = new Map<string, CacheEntry<unknown>>()

  set<T>(key: string, data: T, ttlSeconds: number): void {
    const now = Date.now()
    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + (ttlSeconds * 1000)
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null
    
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      return null
    }
    
    return entry.data as T
  }

  invalidate(pattern: string): void {
    const keysToDelete = Array.from(this.cache.keys()).filter(key => 
      key.includes(pattern) || key.startsWith(pattern)
    )
    keysToDelete.forEach(key => this.cache.delete(key))
    console.log(`[BOOKED-DATES CACHE INVALIDATED] Cleared ${keysToDelete.length} entries matching: ${pattern}`)
  }

  clear(): void {
    this.cache.clear()
  }

  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    }
  }
}

// Global cache instance for booked dates
const bookedDatesCache = new MemoryCache()

// Interface for cached booked dates response
interface CachedBookedDatesResponse {
  success: boolean
  bookedDates: string[]
  message: string
  timestamp: string
}

// Mock availability data - same structure as availability endpoint
const MOCK_AVAILABILITY = {
  '2025-08-08': {
    '12PM': { booked: 2, maxCapacity: 2 },
    '3PM': { booked: 1, maxCapacity: 2 },
    '6PM': { booked: 0, maxCapacity: 2 },
    '9PM': { booked: 2, maxCapacity: 2 },
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

export async function GET() {
  try {
    // Check cache first - Cache for 10 minutes as recommended
    const cacheKey = 'booked-dates-all'
    const cachedResponse = bookedDatesCache.get<CachedBookedDatesResponse>(cacheKey)
    
    if (cachedResponse) {
      console.log('[BOOKED-DATES CACHE HIT] Retrieved booked dates from cache')
      return NextResponse.json(cachedResponse, {
        headers: {
          'X-Cache-Status': 'HIT',
          'X-Cache-Age': Math.floor((Date.now() - new Date(cachedResponse.timestamp).getTime()) / 1000).toString(),
          'X-Cache-TTL': '600'
        }
      })
    }

    console.log('[BOOKED-DATES CACHE MISS] Generating fresh booked dates data')
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Find dates where ALL time slots are fully booked
    const fullyBookedDates: string[] = []
    
    Object.entries(MOCK_AVAILABILITY).forEach(([date, daySlots]) => {
      const allSlotsFull = Object.values(daySlots).every(
        slot => slot.booked >= slot.maxCapacity
      )
      
      if (allSlotsFull) {
        fullyBookedDates.push(date)
      }
    })

    const responseData: CachedBookedDatesResponse = {
      success: true,
      bookedDates: fullyBookedDates,
      message: `Found ${fullyBookedDates.length} fully booked date(s)`,
      timestamp: new Date().toISOString()
    }

    // Cache for 10 minutes (600 seconds) as recommended
    bookedDatesCache.set(cacheKey, responseData, 600)
    console.log(`[BOOKED-DATES CACHED] Stored data with 10-minute TTL`)
    
    // Return the fully booked dates
    return NextResponse.json(responseData, {
      headers: {
        'X-Cache-Status': 'MISS',
        'X-Cache-TTL': '600'
      }
    })
  } catch (error) {
    console.error('Error fetching booked dates:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch booked dates',
        bookedDates: [] 
      },
      { status: 500 }
    )
  }
}
