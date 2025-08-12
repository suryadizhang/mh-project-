import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  images: {
    unoptimized: false,
  },
  reactStrictMode: false, // Temporarily disable strict mode
  output: 'standalone', // Try standalone output
};

export default nextConfig;
