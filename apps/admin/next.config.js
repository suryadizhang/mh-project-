/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  outputFileTracingRoot: '../../',
  compress: true, // Enable gzip compression
  images: {
    unoptimized: false,
    formats: ['image/webp', 'image/avif'],
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: [
      'lucide-react',
      'date-fns',
      '@radix-ui/react-slot',
      'framer-motion',
      'react-hook-form',
      '@hookform/resolvers',
      '@hello-pangea/dnd',
    ],
  },
  // Security headers with WebSocket support
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com",
              "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://use.fontawesome.com https://maxcdn.bootstrapcdn.com",
              "img-src 'self' data: https: blob:",
              "connect-src 'self' ws://localhost:8002 http://localhost:8002 http://localhost:8000 ws://localhost:8000",
              "frame-src 'self'",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          }
        ]
      }
    ];
  }
};

module.exports = nextConfig;
