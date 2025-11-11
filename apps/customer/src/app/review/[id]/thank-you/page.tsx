"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import Confetti from "react-confetti";

export default function ThankYouPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const reviewId = params.id as string;
  const couponCode = searchParams.get("coupon");

  const [showConfetti, setShowConfetti] = useState(true);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight,
    });

    const timer = setTimeout(() => {
      setShowConfetti(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-orange-50 to-red-50 py-12 px-4">
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={200}
        />
      )}

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
            We truly appreciate you taking the time to share your thoughts with us.
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
            <div className="text-5xl mb-4">💬</div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-3">
              We Hear You Loud and Clear
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Your feedback is incredibly valuable to us. Our team has been notified and
              will review your concerns carefully. We're committed to making things right
              and ensuring your next experience exceeds your expectations.
            </p>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="font-semibold text-gray-800 mb-3 text-center">
              What happens next?
            </h3>
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 flex-1">
                  <strong>Within 24 hours:</strong> Our team will review your feedback
                </p>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 flex-1">
                  <strong>Within 48 hours:</strong> A manager may reach out to discuss your experience
                </p>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 flex-1">
                  <strong>Ongoing:</strong> Your feedback helps us improve our service for everyone
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Discount Coupon */}
        {couponCode && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-br from-green-400 to-green-600 rounded-2xl shadow-2xl p-8 text-white mb-6 relative overflow-hidden"
          >
            {/* Decorative Elements */}
            <div className="absolute top-0 right-0 transform translate-x-6 -translate-y-6 opacity-20">
              <div className="text-9xl">🎁</div>
            </div>
            
            <div className="relative z-10">
              <div className="text-center mb-6">
                <div className="text-5xl mb-3">✨</div>
                <h2 className="text-3xl font-bold mb-2">
                  Here's Our Apology Gift
                </h2>
                <p className="text-green-100">
                  Use this coupon code for 10% off your next booking
                </p>
              </div>

              <div className="bg-white rounded-xl p-6 text-center">
                <p className="text-sm text-gray-600 mb-2">Your Discount Code</p>
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 mb-3">
                  <code className="text-3xl font-bold text-green-700 tracking-wider">
                    {couponCode}
                  </code>
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(couponCode);
                    alert("Coupon code copied!");
                  }}
                  className="text-green-600 hover:text-green-700 font-semibold flex items-center justify-center mx-auto"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                  Copy Code
                </button>
              </div>

              <div className="mt-6 text-center">
                <p className="text-sm text-green-100 mb-4">
                  Valid for 90 days • Minimum order $50 • One-time use
                </p>
                <motion.a
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  href="/booking"
                  className="inline-block bg-white text-green-600 px-8 py-3 rounded-lg font-bold hover:bg-green-50 transition shadow-lg"
                >
                  Book Your Next Event
                </motion.a>
              </div>
            </div>
          </motion.div>
        )}

        {/* Call to Action */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="bg-white rounded-2xl shadow-xl p-8 text-center"
        >
          <h3 className="text-2xl font-semibold text-gray-800 mb-3">
            Give Us Another Chance?
          </h3>
          <p className="text-gray-600 mb-6">
            We'd love the opportunity to provide you with the amazing hibachi experience
            you deserve. Our team is working hard to address your concerns.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/booking"
              className="bg-red-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-red-700 transition"
            >
              Book Another Event
            </a>
            <a
              href="/contact"
              className="bg-gray-100 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-200 transition"
            >
              Contact Us
            </a>
          </div>
        </motion.div>

        {/* Social Proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="mt-8 text-center"
        >
          <p className="text-gray-500 text-sm mb-4">
            Join thousands of satisfied customers who love our hibachi experience
          </p>
          <div className="flex justify-center space-x-2">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className="w-6 h-6 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
        </motion.div>

        {/* Return Home */}
        <div className="text-center mt-8">
          <a
            href="/"
            className="text-gray-500 hover:text-gray-700 underline text-sm"
          >
            Return to Homepage
          </a>
        </div>
      </div>
    </div>
  );
}
