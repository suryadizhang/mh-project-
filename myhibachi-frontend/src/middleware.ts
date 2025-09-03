import { NextRequest, NextResponse } from 'next/server'

// Security configuration
const SECURITY_HEADERS = {
  // HSTS - Force HTTPS for 1 year
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

  // Prevent MIME sniffing
  'X-Content-Type-Options': 'nosniff',

  // Prevent embedding in frames
  'X-Frame-Options': 'DENY',

  // XSS Protection
  'X-XSS-Protection': '1; mode=block',

  // DNS prefetch control
  'X-DNS-Prefetch-Control': 'on',

  // Referrer policy
  'Referrer-Policy': 'strict-origin-when-cross-origin',

  // Cross-Origin policies
  'Cross-Origin-Embedder-Policy': 'require-corp',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin',

  // Permissions policy - restrict dangerous APIs
  'Permissions-Policy': [
    'camera=()',
    'microphone=()',
    'geolocation=()',
    'payment=()',
    'usb=()',
    'magnetometer=()',
    'gyroscope=()',
    'speaker=()',
    'fullscreen=(self)',
    'encrypted-media=(self)'
  ].join(', ')
}

// Rate limiting configuration
const RATE_LIMIT = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: 100, // Limit each IP to 100 requests per windowMs
  skipSuccessfulRequests: false,
  skipFailedRequests: false
}

// Simple in-memory rate limiting (for production, use Redis)
const rateLimit = new Map<string, { count: number; resetTime: number }>()

function getRateLimitKey(request: NextRequest): string {
  // Use forwarded IP if available, otherwise fallback to connection IP
  const forwarded = request.headers.get('x-forwarded-for')
  const ip = forwarded ? forwarded.split(',')[0] : request.ip || 'unknown'
  return ip
}

function isRateLimited(key: string): boolean {
  const now = Date.now()
  const record = rateLimit.get(key)

  if (!record) {
    rateLimit.set(key, { count: 1, resetTime: now + RATE_LIMIT.windowMs })
    return false
  }

  if (now > record.resetTime) {
    rateLimit.set(key, { count: 1, resetTime: now + RATE_LIMIT.windowMs })
    return false
  }

  if (record.count >= RATE_LIMIT.maxRequests) {
    return true
  }

  record.count++
  return false
}

function validateRequest(request: NextRequest): boolean {
  const userAgent = request.headers.get('user-agent') || ''
  const contentType = request.headers.get('content-type') || ''

  // Block suspicious user agents
  const suspiciousPatterns = [
    /curl/i,
    /wget/i,
    /python-requests/i,
    /bot/i,
    /crawler/i,
    /scanner/i
  ]

  // Allow legitimate bots (Google, Bing, etc.)
  const allowedBots = [
    /googlebot/i,
    /bingbot/i,
    /slurp/i,
    /duckduckbot/i,
    /facebookexternalhit/i,
    /twitterbot/i,
    /linkedinbot/i
  ]

  const isSuspicious = suspiciousPatterns.some(pattern => pattern.test(userAgent))
  const isAllowedBot = allowedBots.some(pattern => pattern.test(userAgent))

  if (isSuspicious && !isAllowedBot) {
    return false
  }

  // Validate content-type for POST requests
  if (request.method === 'POST' && !contentType.includes('application/json') && !contentType.includes('multipart/form-data')) {
    return false
  }

  return true
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Skip middleware for static assets and Next.js internals
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/_next/') ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }

  // Rate limiting
  const rateLimitKey = getRateLimitKey(request)
  if (isRateLimited(rateLimitKey)) {
    return new NextResponse('Too Many Requests', {
      status: 429,
      headers: {
        'Retry-After': '900', // 15 minutes
        ...SECURITY_HEADERS
      }
    })
  }

  // Security validation
  if (!validateRequest(request)) {
    return new NextResponse('Forbidden', {
      status: 403,
      headers: SECURITY_HEADERS
    })
  }

  // Continue with the request and add security headers
  const response = NextResponse.next()

  // Add all security headers
  Object.entries(SECURITY_HEADERS).forEach(([key, value]) => {
    response.headers.set(key, value)
  })

  // Add security headers for API responses
  if (pathname.startsWith('/api/')) {
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
