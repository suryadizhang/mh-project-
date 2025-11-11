"use client";

import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";

export default function AcknowledgedPage() {
  const params = useParams();
  const _reviewId = params.id as string;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Thank You Message */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="text-8xl mb-6"
          >
            🙏
          </motion.div>
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Thank You for Your Feedback!
          </h1>
          <p className="text-xl text-gray-600">
            We appreciate you taking the time to share your thoughts.
          </p>
        </motion.div>

        {/* Acknowledgment */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl shadow-xl p-8 mb-6"
        >
          <div className="text-center mb-6">
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-3">
              We&apos;ve Received Your Feedback
            </h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              Our AI customer service team will review your comments and may reach out
              to learn more about your experience. Your input helps us continuously
              improve our service.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              What happens next?
            </h3>
            <div className="space-y-2 text-gray-700">
              <p className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Our AI assistant may text you to understand your experience better</span>
              </p>
              <p className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>If needed, our team will follow up personally</span>
              </p>
              <p className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
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
          className="bg-white rounded-2xl shadow-xl p-8 text-center"
        >
          <h3 className="text-2xl font-semibold text-gray-800 mb-3">
            Ready for Another Event?
          </h3>
          <p className="text-gray-600 mb-6">
            We&apos;d love to serve you again and provide an even better experience.
          </p>
          <a
            href="/booking"
            className="inline-block bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700 transition"
          >
            Book Your Next Event
          </a>
        </motion.div>

        {/* Return Home */}
        <div className="text-center mt-8">
          <Link
            href="/"
            className="text-gray-500 hover:text-gray-700 underline text-sm"
          >
            Return to Homepage
          </Link>
        </div>
      </div>
    </div>
  );
}
