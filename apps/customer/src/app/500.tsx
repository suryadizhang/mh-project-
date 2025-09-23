import Link from 'next/link'

export default function Custom500() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50">
      <div className="text-center p-8 max-w-md">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-gray-800 mb-4">500</h1>
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Server Error</h2>
          <p className="text-gray-600 mb-6">
            Oops! Something went wrong on our end. Our hibachi chefs are working to fix this issue.
          </p>
        </div>
        <div className="space-x-4">
          <Link
            href="/"
            className="inline-block bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Home
          </Link>
          <Link
            href="/contact"
            className="inline-block bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Contact Us
          </Link>
        </div>
      </div>
    </div>
  )
}

// Disable static generation for this page
export const dynamic = 'force-dynamic'
