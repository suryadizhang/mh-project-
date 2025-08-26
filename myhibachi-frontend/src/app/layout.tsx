import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Poppins } from "next/font/google";
import "./globals.css";
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import ClientLayout from '@/components/layout/ClientLayout'
import { PerformanceMonitoring } from '@/components/seo/TechnicalSEO'
// import TawkWrapper from '@/components/TawkWrapper' // Disabled - only using manual LiveChatButton

// Import global styles
import '@/styles/base.css'
import '@/styles/footer.css'
import '@/styles/free-quote-button.css'
import '@/styles/quote-calculator.css'

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MyHibachi - Authentic Japanese Hibachi Catering",
  description: "Premium hibachi catering service bringing authentic Japanese cuisine to your events.",
  icons: {
    icon: [
      {
        url: '/favicon.ico',
        sizes: '16x16 32x32',
      },
      {
        url: '/icon.png',
        sizes: '32x32',
        type: 'image/png',
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
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

        {/* Bootstrap JavaScript Bundle */}
        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
          async
        ></script>
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${poppins.variable} antialiased min-h-screen flex flex-col company-background`}
      >
        {/* Core Web Vitals Performance Monitoring */}
        <PerformanceMonitoring />
        
        <ClientLayout>
          <Navbar />
          <main className="flex-1">
            {children}
          </main>
          <Footer />
        </ClientLayout>
        {/* TawkWrapper disabled - only using manual LiveChatButton on contact page */}
        {/* Optional: Uncomment to enable email capture prompt
        <TawkEmailPrompt />
        */}
      </body>
    </html>
  );
}
