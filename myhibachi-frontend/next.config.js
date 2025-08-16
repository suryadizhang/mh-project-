/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  images: {
    unoptimized: false,
  },
  reactStrictMode: true,
  trailingSlash: true,
};

module.exports = nextConfig;
