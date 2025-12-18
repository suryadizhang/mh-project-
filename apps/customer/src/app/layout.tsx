import './globals.css';
// Import truly global styles only - page-specific CSS loaded at page level
import '@/styles/base.css';
import '@/styles/utilities.css';
import '@/styles/accessibility.css';
import '@/styles/footer.css';
import '@/styles/back-to-top.css';
import '@/styles/breadcrumb.css';
import '@/styles/optimized-image.css';
// PHASE 5 FIX: Cross-browser button standardization - MUST LOAD LAST
import '@/styles/components/buttons-cross-browser.css';

import type { Metadata } from 'next';
import { Inter, JetBrains_Mono, Poppins } from 'next/font/google';

import GoogleAnalytics from '@/components/analytics/GoogleAnalytics';
import ClientLayout from '@/components/layout/ClientLayout';
import Footer from '@/components/layout/Footer';
import Navbar from '@/components/layout/Navbar';
import { QueryProvider } from '@/components/providers/QueryProvider';
import RateLimitBanner from '@/components/RateLimitBanner';
import { PerformanceMonitoring } from '@/components/seo/TechnicalSEO';
import BackToTopButton from '@/components/ui/BackToTopButton';
import { Toaster } from '@/components/ui/toaster';
import {
  generateLocalBusinessSchema,
  generateOrganizationSchema,
  generatePageMetadata,
  SITE_CONFIG,
} from '@/lib/seo-config';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
  preload: true,
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin'],
  display: 'swap',
  preload: false, // Non-critical font
});

const poppins = Poppins({
  variable: '--font-poppins',
  subsets: ['latin'],
  weight: ['400', '600', '700'], // Reduced from 5 to 3 weights
  display: 'swap',
  preload: true,
});

export const metadata: Metadata = generatePageMetadata({
  title: SITE_CONFIG.title,
  description: SITE_CONFIG.description,
  path: '/',
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* LCP optimization: Preload hero poster image for instant display */}
        <link
          rel="preload"
          as="image"
          href="/images/hero-poster.jpg"
          fetchPriority="high"
        />
        
        {/* Performance optimization hints */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="preconnect" href="//fonts.gstatic.com" crossOrigin="anonymous" />
        {/* Video loads lazily via HeroVideoLazy component - after LCP */}

        {/* Google Search Console Verification - Add your verification code here when you get it */}
        {/* <meta name="google-site-verification" content="YOUR_VERIFICATION_CODE_HERE" /> */}

        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(generateOrganizationSchema()),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(generateLocalBusinessSchema()),
          }}
        />

        {/* Google Search Console Verification - Add your verification code here when you get it */}
        {/* <meta name="google-site-verification" content="YOUR_VERIFICATION_CODE_HERE" /> */}
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${poppins.variable} company-background flex min-h-screen flex-col antialiased`}
      >
        {/* Skip link for accessibility - WCAG 2.1 AA compliance */}
        <a
          href="#main-content"
          className="focus:bg-brand-red sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[9999] focus:rounded-md focus:px-4 focus:py-2 focus:font-semibold focus:text-white focus:ring-2 focus:ring-white focus:outline-none"
        >
          Skip to main content
        </a>

        <QueryProvider>
          {/* Google Analytics 4 */}
          <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || ''} />

          {/* Core Web Vitals Performance Monitoring */}
          <PerformanceMonitoring />

          {/* Rate Limit Warning Banner (HIGH PRIORITY #12) */}
          <RateLimitBanner />

          <ClientLayout>
            <Navbar />
            <main id="main-content" className="w-full flex-1">
              {children}
            </main>
            <Footer />
            <BackToTopButton />
          </ClientLayout>

          {/* Toast Notification System */}
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
