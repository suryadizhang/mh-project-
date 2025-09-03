import type { Metadata } from 'next'
import { Inter, JetBrains_Mono, Poppins } from 'next/font/google'

import './globals.css'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import ClientLayout from '@/components/layout/ClientLayout'
import BackToTopButton from '@/components/ui/BackToTopButton'
import GoogleAnalytics from '@/components/analytics/GoogleAnalytics'
import { PerformanceMonitoring } from '@/components/seo/TechnicalSEO'
import {
  generatePageMetadata,
  SITE_CONFIG,
  generateOrganizationSchema,
  generateLocalBusinessSchema
} from '@/lib/seo-config'

// Import global styles
import '@/styles/base.css'
import '@/styles/utilities.css'
import '@/styles/accessibility.css'
import '@/styles/menu.css'
import '@/styles/menu/menu-features.css'
import '@/styles/menu/menu-pricing.css'
import '@/styles/menu/menu-base.css'
import '@/styles/menu/base.css'
import '@/styles/pages/menu.page.css'
import '@/styles/footer.css'
import '@/styles/free-quote-button.css'
import '@/styles/quote-calculator.css'
import '@/styles/back-to-top.css'
import '@/styles/breadcrumb.css'
import '@/styles/optimized-image.css'
// PHASE 5 FIX: Cross-browser button standardization - MUST LOAD LAST
import '@/styles/components/buttons-cross-browser.css'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin']
})

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin']
})

const poppins = Poppins({
  variable: '--font-poppins',
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap'
})

export const metadata: Metadata = generatePageMetadata({
  title: SITE_CONFIG.title,
  description: SITE_CONFIG.description,
  path: '/'
})

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        {/* Bootstrap CSS */}
        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
          rel="stylesheet"
        />

        {/* Bootstrap Icons */}
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css"
        />

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
            __html: JSON.stringify(generateOrganizationSchema())
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(generateLocalBusinessSchema())
          }}
        />

        {/* Bootstrap JavaScript Bundle */}
        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
          async
        ></script>
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${poppins.variable} antialiased min-h-screen flex flex-col company-background`}
      >
        {/* Google Analytics 4 */}
        <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || ''} />

        {/* Core Web Vitals Performance Monitoring */}
        <PerformanceMonitoring />

        <ClientLayout>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
          <BackToTopButton />
        </ClientLayout>
      </body>
    </html>
  )
}
