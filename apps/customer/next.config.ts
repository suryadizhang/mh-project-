import path from 'path';

import type { NextConfig } from 'next';

// Dynamic import for bundle analyzer
const withBundleAnalyzer =
  process.env.ANALYZE === 'true'
    ? // eslint-disable-next-line @typescript-eslint/no-require-imports
      require('@next/bundle-analyzer')({ enabled: true })
    : (config: NextConfig) => config;

const nextConfig: NextConfig = {
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname, '../../'),
  compress: true, // Enable gzip compression
  eslint: {
    // Skip linting during builds - we run ESLint separately in CI
    // ESLint 9 is installed to match Vercel's Next.js 15 requirements
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      'date-fns',
      '@radix-ui/react-slot',
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-toast',
      '@radix-ui/react-tooltip',
      '@radix-ui/react-popover',
      'framer-motion',
      'react-hook-form',
      '@hookform/resolvers',
      'zod',
      'react-day-picker',
      'clsx',
      'class-variance-authority',
    ],
    // optimizeCss disabled - causes critters module resolution issues in Vercel monorepo
    // optimizeCss: true,
  },
  images: {
    unoptimized: false,
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [320, 420, 640, 768, 1024, 1200, 1536],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 7, // 1 week
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.vercel.app',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
  reactStrictMode: true,
  trailingSlash: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Enhanced Security headers for Phase 9
  async headers() {
    const isProduction = process.env.NODE_ENV === 'production';

    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Permissions-Policy',
            value:
              'camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
          },
          // Only enable HSTS in production
          ...(isProduction
            ? [
                {
                  key: 'Strict-Transport-Security',
                  value: 'max-age=31536000; includeSubDomains; preload',
                },
              ]
            : []),
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Permitted-Cross-Domain-Policies',
            value: 'none',
          },
          // COEP/CORP headers intentionally NOT included here
          // These headers (Cross-Origin-Embedder-Policy: require-corp and Cross-Origin-Resource-Policy: same-origin)
          // were removed because they block API calls to external services like mhapi.mysticdatanode.net
          // and Google Maps API. These headers require CORP headers on ALL cross-origin resources.
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin-allow-popups', // Allows OAuth popups while maintaining isolation
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Scripts: Google Maps, Analytics, Facebook, CDN
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com https://connect.facebook.net https://cdn.jsdelivr.net https://maps.googleapis.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com",
              "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com",
              "img-src 'self' data: https: blob:",
              // CRITICAL: API URL, Google Maps Places API, Stripe, Analytics
              "connect-src 'self' https://mhapi.mysticdatanode.net https://maps.googleapis.com https://www.google-analytics.com https://api.stripe.com https://vitals.vercel-insights.com https://cdn.jsdelivr.net ws://localhost:8002 http://localhost:8002",
              "frame-src 'self' https://js.stripe.com https://www.facebook.com",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'none'",
              // Only upgrade to HTTPS in production
              ...(isProduction ? ['upgrade-insecure-requests'] : []),
            ].join('; '),
          },
        ],
      },
      // Static asset cache headers - improves LCP by 674 KiB (Lighthouse recommendation)
      {
        source: '/:all*(svg|jpg|jpeg|png|gif|webp|avif|ico)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // Font cache headers
      {
        source: '/:all*(woff|woff2|ttf|otf|eot)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // Video cache headers
      {
        source: '/:all*(mp4|webm|ogg)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // JS/CSS cache headers (Next.js handles versioning)
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
  // URL redirects for legacy/shortened paths
  async redirects() {
    return [
      // Redirect /booking and /book to /BookUs
      {
        source: '/booking',
        destination: '/BookUs/',
        permanent: true,
      },
      {
        source: '/booking/',
        destination: '/BookUs/',
        permanent: true,
      },
      {
        source: '/book',
        destination: '/BookUs/',
        permanent: true,
      },
      {
        source: '/book/',
        destination: '/BookUs/',
        permanent: true,
      },
      // Case-insensitive redirects for bookus variations
      {
        source: '/bookus',
        destination: '/BookUs/',
        permanent: true,
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
