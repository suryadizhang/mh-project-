const { withSentryConfig } = require('@sentry/nextjs');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  outputFileTracingRoot: '../../',
  compress: true, // Enable gzip compression
  eslint: {
    // Skip linting during builds - we run ESLint separately in CI
    // ESLint 9 is installed to match Vercel's Next.js 15 requirements
    ignoreDuringBuilds: true,
  },
  images: {
    unoptimized: false,
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [320, 420, 640, 768, 1024, 1200, 1536],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 7, // 1 week
  },
  // Remove console logs in production for smaller bundle
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: [
      'lucide-react',
      'date-fns',
      // NOTE: Do NOT add @radix-ui/react-slot here - it causes infinite loop issues
      // due to how the Slot component handles children forwarding
      'framer-motion',
      'react-hook-form',
      '@hookform/resolvers',
      '@hello-pangea/dnd',
      'recharts',
      '@tiptap/react',
      '@tiptap/starter-kit',
    ],
  },
  // Security headers with WebSocket support
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
            key: 'X-Robots-Tag',
            value: 'noindex, nofollow', // Admin should not be indexed
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Scripts: self, inline, eval, Stripe, Google OAuth, Cloudflare
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://accounts.google.com https://apis.google.com https://static.cloudflareinsights.com",
              // Styles: self, inline, Google Fonts, CDNs
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com",
              // Fonts: self, Google Fonts, CDNs
              "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com data:",
              "img-src 'self' data: https: blob:",
              // Connect: API, Stripe, Vercel, Google OAuth, Cloudflare, localhost, WebSocket
              "connect-src 'self' https://mhapi.mysticdatanode.net wss://mhapi.mysticdatanode.net https://api.stripe.com https://vitals.vercel-insights.com https://accounts.google.com https://oauth2.googleapis.com ws://localhost:8002 http://localhost:8002 http://localhost:8000 ws://localhost:8000",
              // Frames: Stripe, Google OAuth
              "frame-src 'self' https://js.stripe.com https://accounts.google.com",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self' https://accounts.google.com",
            ].join('; '),
          },
        ],
      },
      // Static asset cache headers
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
      // JS/CSS cache headers
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
};

// Sentry configuration options
const sentryWebpackPluginOptions = {
  // Suppresses source map uploading logs during build
  silent: true,
  // Organization and project from Sentry
  org: process.env.SENTRY_ORG || 'myhibachi',
  project: process.env.SENTRY_PROJECT || 'admin-frontend',
  // Auth token from environment
  authToken: process.env.SENTRY_AUTH_TOKEN,
  // Hide source maps in production
  hideSourceMaps: true,
  // Disable Sentry telemetry
  telemetry: false,
};

module.exports = withSentryConfig(nextConfig, sentryWebpackPluginOptions);
