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
  },
};

module.exports = nextConfig;
