import Link from 'next/link'
import Breadcrumb from '@/components/ui/Breadcrumb'
import { generatePageMetadata } from '@/lib/seo-config'

export const metadata = generatePageMetadata({
  title: "Page Not Found - 404 Error",
  description: "The page you're looking for doesn't exist. Return to My Hibachi Chef homepage or explore our hibachi catering services.",
  noIndex: true,
})

export default function NotFound() {
  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: '404 Error', href: '/404' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4">
        <Breadcrumb items={breadcrumbItems} className="pt-4" />
        
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center">
          {/* 404 Visual */}
          <div className="mb-8">
            <div className="text-8xl md:text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500 mb-4">
              404
            </div>
            <div className="flex justify-center mb-6">
              <i className="bi bi-exclamation-triangle text-6xl text-orange-400"></i>
            </div>
          </div>

          {/* Error Message */}
          <div className="max-w-2xl mb-8">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Oops! Page Not Found
            </h1>
            <p className="text-lg text-gray-300 mb-6">
              The page you&apos;re looking for seems to have vanished like sizzling hibachi steam! 
              Don&apos;t worry, let&apos;s get you back to the delicious action.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <Link 
              href="/"
              className="px-8 py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-lg hover:from-orange-600 hover:to-red-600 transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
            >
              <i className="bi bi-house-door mr-2"></i>
              Back to Home
            </Link>
            
            <Link 
              href="/BookUs"
              className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
            >
              <i className="bi bi-calendar-check mr-2"></i>
              Book Hibachi
            </Link>
          </div>

          {/* Helpful Links */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl">
            <Link 
              href="/menu"
              className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors text-center group"
            >
              <i className="bi bi-menu-button-wide text-2xl text-orange-400 group-hover:text-orange-300 mb-2 block"></i>
              <span className="text-white text-sm">Menu</span>
            </Link>
            
            <Link 
              href="/quote"
              className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors text-center group"
            >
              <i className="bi bi-calculator text-2xl text-orange-400 group-hover:text-orange-300 mb-2 block"></i>
              <span className="text-white text-sm">Get Quote</span>
            </Link>
            
            <Link 
              href="/blog"
              className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors text-center group"
            >
              <i className="bi bi-journal-text text-2xl text-orange-400 group-hover:text-orange-300 mb-2 block"></i>
              <span className="text-white text-sm">Blog</span>
            </Link>
            
            <Link 
              href="/contact"
              className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors text-center group"
            >
              <i className="bi bi-telephone text-2xl text-orange-400 group-hover:text-orange-300 mb-2 block"></i>
              <span className="text-white text-sm">Contact</span>
            </Link>
          </div>

          {/* Contact Info */}
          <div className="mt-8 text-center">
            <p className="text-gray-400 mb-2">Need immediate assistance?</p>
            <a 
              href="tel:(916) 740-8768"
              className="text-orange-400 hover:text-orange-300 font-semibold text-lg"
            >
              <i className="bi bi-telephone mr-2"></i>
              (916) 740-8768
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
