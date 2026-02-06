import Link from 'next/link';

export default function Custom500() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-red-50 to-orange-50">
      <div className="max-w-md p-8 text-center">
        <div className="mb-8">
          <h1 className="mb-4 text-6xl font-bold text-gray-800">500</h1>
          <h2 className="mb-4 text-2xl font-semibold text-gray-700">Server Error</h2>
          <p className="mb-6 text-gray-600">
            Oops! Something went wrong on our end. Our hibachi chefs are working to fix this issue.
          </p>
        </div>
        <div className="space-x-4">
          <Link
            href="/"
            className="inline-block rounded-lg bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700"
          >
            Back to Home
          </Link>
          <Link
            href="/contact"
            className="inline-block rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700"
          >
            Contact Us
          </Link>
        </div>
      </div>
    </div>
  );
}

// Disable static generation for this page
export const dynamic = 'force-dynamic';
