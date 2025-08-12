interface BaseLocationData {
  zipCode: string
  city: string
  state: string
  lat: number
  lng: number
  lastUpdated: string
  updatedBy: string
}

// Cache for base location to avoid repeated API calls
let baseLocationCache: BaseLocationData | null = null
let cacheTimestamp = 0
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

/**
 * Get the current base location for distance calculations
 * Uses caching to minimize API calls
 */
export async function getBaseLocation(): Promise<BaseLocationData> {
  const now = Date.now()
  
  // Return cached data if still valid
  if (baseLocationCache && (now - cacheTimestamp) < CACHE_DURATION) {
    return baseLocationCache
  }

  try {
    const response = await fetch('/api/v1/admin/base-location', {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache'
      }
    })

    if (!response.ok) {
      throw new Error('Failed to fetch base location')
    }

    const location = await response.json()
    
    // Update cache
    baseLocationCache = location
    cacheTimestamp = now
    
    return location
  } catch (error) {
    console.error('Error fetching base location:', error)
    
    // Return default Fremont location as fallback
    const defaultLocation: BaseLocationData = {
      zipCode: '94536',
      city: 'Fremont',
      state: 'CA',
      lat: 37.4958,
      lng: -121.9405,
      lastUpdated: '2025-01-15',
      updatedBy: 'Default Fallback'
    }
    
    return defaultLocation
  }
}

/**
 * Calculate distance between two points using Haversine formula
 * @param lat1 Base location latitude
 * @param lng1 Base location longitude  
 * @param lat2 Customer location latitude
 * @param lng2 Customer location longitude
 * @returns Distance in miles
 */
export function calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 3959 // Earth's radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng/2) * Math.sin(dLng/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

/**
 * Calculate travel fee based on distance from base location
 * @param distance Distance in miles
 * @returns Travel fee in dollars
 */
export function calculateTravelFee(distance: number): number {
  if (distance <= 30) {
    return 0 // Free within 30 miles
  }
  return Math.round((distance - 30) * 2) // $2 per mile after 30 miles
}

/**
 * Clear the base location cache (useful when location is updated)
 */
export function clearBaseLocationCache(): void {
  baseLocationCache = null
  cacheTimestamp = 0
}
