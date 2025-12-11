import './globals.css';
// Import global styles
import '@/styles/base.css';
import '@/styles/utilities.css';
import '@/styles/accessibility.css';
import '@/styles/menu.css';
import '@/styles/menu/menu-features.css';
import '@/styles/menu/menu-pricing.css';
import '@/styles/menu/menu-base.css';
import '@/styles/menu/base.css';
import '@/styles/pages/menu.page.css';
import '@/styles/footer.css';
import '@/styles/free-quote-button.css';
import '@/styles/quote-calculator.css';
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
import StickyBookNowButton from '@/components/ui/StickyBookNowButton';
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
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin'],
});

const poppins = Poppins({
  variable: '--font-poppins',
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
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
        {/* Performance optimization hints */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="preconnect" href="//fonts.gstatic.com" crossOrigin="anonymous" />

        {/* Video preload hint for hero video */}
        <link rel="preload" href="/videos/hero_video.mp4" as="video" type="video/mp4" />

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
        <QueryProvider>
          {/* Google Analytics 4 */}
          <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || ''} />

          {/* Core Web Vitals Performance Monitoring */}
          <PerformanceMonitoring />

          {/* Rate Limit Warning Banner (HIGH PRIORITY #12) */}
          <RateLimitBanner />

          <ClientLayout>
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
            <BackToTopButton />
            <StickyBookNowButton />
          </ClientLayout>

          {/* Toast Notification System */}
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
