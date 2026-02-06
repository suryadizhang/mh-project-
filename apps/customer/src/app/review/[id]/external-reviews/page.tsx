'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function ExternalReviewsPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const [redirecting, setRedirecting] = useState(false);

  const yelpUrl =
    process.env.NEXT_PUBLIC_YELP_REVIEW_URL || 'https://www.yelp.com/biz/my-hibachi-chef';
  const googleUrl =
    process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL || 'https://g.page/r/YOUR_GOOGLE_PLACE_ID/review';

  const trackExternalReview = async (platform: string) => {
    try {
      await fetch(`/api/reviews/${reviewId}/track-external`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform }),
      });
    } catch (err) {
      console.error('Failed to track external review:', err);
    }
  };

  const handleYelpClick = async () => {
    setRedirecting(true);
    await trackExternalReview('yelp');
    window.open(yelpUrl, '_blank');
    setTimeout(() => setRedirecting(false), 2000);
  };

  const handleGoogleClick = async () => {
    setRedirecting(true);
    await trackExternalReview('google');
    window.open(googleUrl, '_blank');
    setTimeout(() => setRedirecting(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 px-4 py-12">
      <div className="mx-auto max-w-3xl">
        {/* Success Message */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-12 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="mb-6 text-8xl"
          >
            🎉
          </motion.div>
          <h1 className="mb-4 text-4xl font-bold text-gray-800">
            Thank You for Your Positive Feedback!
          </h1>
          <p className="text-xl text-gray-600">
            {"We're thrilled you enjoyed your hibachi experience! 🍱✨"}
          </p>
        </motion.div>

        {/* Review Platforms */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8 rounded-2xl bg-white p-8 shadow-xl"
        >
          <h2 className="mb-2 text-center text-2xl font-semibold text-gray-800">
            Share Your Experience Online
          </h2>
          <p className="mb-8 text-center text-gray-600">
            Help others discover the joy of My Hibachi Chef!
          </p>

          <div className="space-y-4">
            {/* Yelp Review Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleYelpClick}
              disabled={redirecting}
              className="flex w-full items-center justify-between rounded-xl bg-red-600 px-6 py-5 text-white shadow-lg transition-all hover:bg-red-700"
            >
              <div className="flex items-center">
                <div className="mr-4 rounded-lg bg-white p-3">
                  <svg className="h-8 w-8 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.271,16.718v1.417q-.011,3.257-.04,3.469a.671.671,0,0,1-.316.545,3.045,3.045,0,0,1-.793.5,4.167,4.167,0,0,1-1.658.5,1.776,1.776,0,0,1-1.113-.269.858.858,0,0,1-.3-.576q-.04-.427.255-3.394a1.266,1.266,0,0,1,.156-.549,2.072,2.072,0,0,1,.524-.505l5.4-3.932a.549.549,0,0,1,.807.178,1.356,1.356,0,0,1,.143.807,2.538,2.538,0,0,1-.183.795l-2.032,3.43A.252.252,0,0,0,12.271,16.718Z" />
                  </svg>
                </div>
                <div className="text-left">
                  <div className="text-lg font-bold">Leave a Yelp Review</div>
                  <div className="text-sm opacity-90">Share on Yelp.com</div>
                </div>
              </div>
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </motion.button>

            {/* Google Review Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleGoogleClick}
              disabled={redirecting}
              className="flex w-full items-center justify-between rounded-xl bg-blue-600 px-6 py-5 text-white shadow-lg transition-all hover:bg-blue-700"
            >
              <div className="flex items-center">
                <div className="mr-4 rounded-lg bg-white p-3">
                  <svg className="h-8 w-8" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                </div>
                <div className="text-left">
                  <div className="text-lg font-bold">Leave a Google Review</div>
                  <div className="text-sm opacity-90">Share on Google Business</div>
                </div>
              </div>
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </motion.button>
          </div>

          <p className="mt-6 text-center text-sm text-gray-500">
            Your review helps others discover great hibachi experiences! 🌟
          </p>
        </motion.div>

        {/* Additional Benefits */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="rounded-2xl bg-gradient-to-r from-purple-100 to-pink-100 p-6 text-center"
        >
          <h3 className="mb-2 text-lg font-semibold text-gray-800">Already left a review?</h3>
          <p className="mb-4 text-gray-600">
            Join our VIP list for exclusive offers and early access to special events!
          </p>
          <a
            href="/newsletter-signup"
            className="inline-block rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 px-8 py-3 font-semibold text-white transition hover:from-purple-700 hover:to-pink-700"
          >
            Join VIP List
          </a>
        </motion.div>

        {/* Skip Option */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-gray-500 underline hover:text-gray-700">
            Skip for now
          </Link>
        </div>
      </div>
    </div>
  );
}
