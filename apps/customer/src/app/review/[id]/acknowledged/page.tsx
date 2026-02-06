'use client';

import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function AcknowledgedPage() {
  const params = useParams();
  const _reviewId = params.id as string;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 px-4 py-12">
      <div className="mx-auto max-w-3xl">
        {/* Thank You Message */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="mb-6 text-8xl"
          >
            🙏
          </motion.div>
          <h1 className="mb-4 text-4xl font-bold text-gray-800">Thank You for Your Feedback!</h1>
          <p className="text-xl text-gray-600">
            We appreciate you taking the time to share your thoughts.
          </p>
        </motion.div>

        {/* Acknowledgment */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6 rounded-2xl bg-white p-8 shadow-xl"
        >
          <div className="mb-6 text-center">
            <div className="mb-4 text-5xl">✅</div>
            <h2 className="mb-3 text-2xl font-semibold text-gray-800">
              We&apos;ve Received Your Feedback
            </h2>
            <p className="mb-4 leading-relaxed text-gray-600">
              Our AI customer service team will review your comments and may reach out to learn more
              about your experience. Your input helps us continuously improve our service.
            </p>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
            <h3 className="mb-3 flex items-center font-semibold text-gray-800">
              <svg
                className="mr-2 h-5 w-5 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              What happens next?
            </h3>
            <div className="space-y-2 text-gray-700">
              <p className="flex items-start">
                <span className="mr-2 text-blue-600">•</span>
                <span>Our AI assistant may text you to understand your experience better</span>
              </p>
              <p className="flex items-start">
                <span className="mr-2 text-blue-600">•</span>
                <span>If needed, our team will follow up personally</span>
              </p>
              <p className="flex items-start">
                <span className="mr-2 text-blue-600">•</span>
                <span>Your feedback helps us improve for all customers</span>
              </p>
            </div>
          </div>
        </motion.div>

        {/* Book Again */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="rounded-2xl bg-white p-8 text-center shadow-xl"
        >
          <h3 className="mb-3 text-2xl font-semibold text-gray-800">Ready for Another Event?</h3>
          <p className="mb-6 text-gray-600">
            We&apos;d love to serve you again and provide an even better experience.
          </p>
          <a
            href="/booking"
            className="inline-block rounded-lg bg-red-600 px-8 py-3 font-semibold text-white transition hover:bg-red-700"
          >
            Book Your Next Event
          </a>
        </motion.div>

        {/* Return Home */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-gray-500 underline hover:text-gray-700">
            Return to Homepage
          </Link>
        </div>
      </div>
    </div>
  );
}
