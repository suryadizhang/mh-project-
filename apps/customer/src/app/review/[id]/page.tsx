"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";

interface ReviewData {
  id: string;
  status: string;
  rating?: string;
  submitted: boolean;
  booking_date?: string;
  customer_name?: string;
  coupon_issued?: boolean;
  coupon_code?: string;
}

const ratings = [
  { value: "great", label: "Great! 🌟", emoji: "😊", color: "green" },
  { value: "good", label: "Good 👍", emoji: "🙂", color: "blue" },
  { value: "okay", label: "Okay 😐", emoji: "😐", color: "yellow" },
  { value: "could_be_better", label: "Could be better", emoji: "😕", color: "orange" },
];

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const reviewId = params.id as string;

  const [review, setReview] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedRating, setSelectedRating] = useState<string | null>(null);
  const [complaintText, setComplaintText] = useState("");
  const [improvementSuggestions, setImprovementSuggestions] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReview();
  }, [reviewId]);

  const fetchReview = async () => {
    try {
      const response = await fetch(`/api/reviews/${reviewId}`);
      if (!response.ok) throw new Error("Review not found");

      const data = await response.json();
      setReview(data);

      // If already submitted, redirect appropriately
      if (data.submitted && data.rating) {
        if (["great", "good"].includes(data.rating)) {
          router.push(`/review/${reviewId}/external-reviews`);
        } else {
          router.push(`/review/${reviewId}/thank-you`);
        }
      }
    } catch (err) {
      setError("Unable to load review. Please check your link.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedRating) {
      setError("Please select a rating");
      return;
    }

    // Validate negative reviews have complaint text
    if (["okay", "could_be_better"].includes(selectedRating) && !complaintText.trim()) {
      setError("Please tell us what went wrong");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/reviews/${reviewId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating: selectedRating,
          complaint_text: complaintText || undefined,
          improvement_suggestions: improvementSuggestions || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to submit review");
      }

      const result = await response.json();

      // Redirect based on rating
      if (result.is_positive) {
        router.push(`/review/${reviewId}/external-reviews`);
      } else if (selectedRating === "okay") {
        // "Okay" rating - AI will follow up, show acknowledgment
        router.push(`/review/${reviewId}/acknowledged`);
      } else if (selectedRating === "could_be_better") {
        // "Could be better" - Redirect to AI chat for immediate assistance
        router.push(`/review/${reviewId}/ai-assistance`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to submit review";
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your review...</p>
        </div>
      </div>
    );
  }

  if (error && !review) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">😕</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Oops!</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            href="/"
            className="inline-block bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition"
          >
            Go to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="text-6xl mb-4">🍱</div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            How was your hibachi experience?
          </h1>
          <p className="text-gray-600">
            Hi {review?.customer_name}! Your feedback helps us serve you better.
          </p>
        </motion.div>

        {/* Rating Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-xl p-8 mb-6"
        >
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
            Rate Your Experience
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {ratings.map((rating) => (
              <motion.button
                key={rating.value}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedRating(rating.value)}
                className={`
                  p-6 rounded-xl border-2 transition-all
                  ${selectedRating === rating.value
                    ? `border-${rating.color}-500 bg-${rating.color}-50 ring-4 ring-${rating.color}-200`
                    : "border-gray-200 hover:border-gray-300"
                  }
                `}
              >
                <div className="text-5xl mb-2">{rating.emoji}</div>
                <div className="font-semibold text-lg">{rating.label}</div>
              </motion.button>
            ))}
          </div>

          {/* Complaint Form (for negative reviews) */}
          {selectedRating && ["okay", "could_be_better"].includes(selectedRating) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="space-y-4 mt-6 pt-6 border-t"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  What went wrong? <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={complaintText}
                  onChange={(e) => setComplaintText(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Please tell us about your concerns..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  How can we improve?
                </label>
                <textarea
                  value={improvementSuggestions}
                  onChange={(e) => setImprovementSuggestions(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Your suggestions help us do better..."
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>We appreciate your feedback!</strong> Our team will review your
                  concerns and reach out to make things right. Plus, {"you'll"} receive a
                  special discount coupon for your next booking. 🎁
                </p>
              </div>
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSubmit}
            disabled={!selectedRating || submitting}
            className={`
              w-full mt-6 py-4 rounded-xl font-semibold text-lg transition-all
              ${selectedRating && !submitting
                ? "bg-red-600 text-white hover:bg-red-700 shadow-lg"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }
            `}
          >
            {submitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </span>
            ) : (
              "Submit Feedback"
            )}
          </motion.button>
        </motion.div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500">
          Your privacy is important to us. This feedback is confidential and used only to improve our service.
        </p>
      </div>
    </div>
  );
}
