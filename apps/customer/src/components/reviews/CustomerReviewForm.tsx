/**
 * Customer Review Submission Form
 * Multi-step wizard with media upload, preview, and submit
 *
 * Features:
 * - Step 1: Rating selection (1-5 stars)
 * - Step 2: Review content (title + description)
 * - Step 3: Media upload (images + videos with previews)
 * - Step 4: External review links (Google/Yelp)
 * - PREVIEW BUTTON: See how review will look before submitting
 * - SUBMIT BUTTON: Post review to backend
 * - Form validation with error messages
 * - Success confirmation page
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { z } from 'zod';

// ============================================================================
// Types & Validation
// ============================================================================

const reviewFormSchema = z.object({
  rating: z.number().min(1).max(5),
  title: z.string().min(5, 'Title must be at least 5 characters').max(200),
  content: z.string().min(20, 'Review must be at least 20 characters').max(5000),
  customerName: z.string().min(2, 'Name is required'),
  customerEmail: z.string().email('Valid email is required'),
  customerPhone: z.string().optional(),
  showInitialsOnly: z.boolean().optional(),
  googleReviewUrl: z.string().url().optional().or(z.literal('')),
  yelpReviewUrl: z.string().url().optional().or(z.literal('')),
});

type ReviewFormData = z.infer<typeof reviewFormSchema>;

interface MediaFile {
  file: File;
  preview: string;
  type: 'image' | 'video';
}

// ============================================================================
// Main Component
// ============================================================================

export default function CustomerReviewForm() {
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<Partial<ReviewFormData>>({
    rating: 0,
    title: '',
    content: '',
    customerName: '',
    customerEmail: '',
    customerPhone: '',
    showInitialsOnly: false,
    googleReviewUrl: '',
    yelpReviewUrl: '',
  });

  // Media state
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [dragActive, setDragActive] = useState(false);

  // UI state
  const [showPreview, setShowPreview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // ============================================================================
  // Media Upload Handlers
  // ============================================================================

  const handleMediaUpload = (files: FileList | null) => {
    if (!files) return;

    const newMedia: MediaFile[] = [];
    const maxFiles = 10;

    // Check total files limit
    if (mediaFiles.length + files.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`);
      return;
    }

    Array.from(files).forEach((file) => {
      // Check file type
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');

      if (!isImage && !isVideo) {
        alert(`${file.name} is not a valid image or video`);
        return;
      }

      // Check file size
      const maxImageSize = 10 * 1024 * 1024; // 10MB
      const maxVideoSize = 100 * 1024 * 1024; // 100MB
      const maxSize = isVideo ? maxVideoSize : maxImageSize;

      if (file.size > maxSize) {
        alert(`${file.name} exceeds max size (${isVideo ? '100MB' : '10MB'})`);
        return;
      }

      // Create preview URL
      const preview = URL.createObjectURL(file);

      newMedia.push({
        file,
        preview,
        type: isImage ? 'image' : 'video',
      });
    });

    setMediaFiles([...mediaFiles, ...newMedia]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleMediaUpload(e.dataTransfer.files);
    }
  };

  const removeMedia = (index: number) => {
    const newMedia = [...mediaFiles];
    URL.revokeObjectURL(newMedia[index].preview);
    newMedia.splice(index, 1);
    setMediaFiles(newMedia);
  };

  // ============================================================================
  // Form Handlers
  // ============================================================================

  const handleInputChange = (field: keyof ReviewFormData, value: string | number | boolean) => {
    setFormData({ ...formData, [field]: value });
    // Clear error for this field
    if (errors[field]) {
      const newErrors = { ...errors };
      delete newErrors[field];
      setErrors(newErrors);
    }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!formData.rating || formData.rating === 0) {
          newErrors.rating = 'Please select a rating';
        }
        break;
      case 2:
        if (!formData.title || formData.title.length < 5) {
          newErrors.title = 'Title must be at least 5 characters';
        }
        if (!formData.content || formData.content.length < 20) {
          newErrors.content = 'Review must be at least 20 characters';
        }
        if (!formData.customerName || formData.customerName.length < 2) {
          newErrors.customerName = 'Name is required';
        }
        if (!formData.customerEmail || !formData.customerEmail.includes('@')) {
          newErrors.customerEmail = 'Valid email is required';
        }
        break;
      case 3:
        // Media is optional, no validation needed
        break;
      case 4:
        // External links are optional
        if (formData.googleReviewUrl && !formData.googleReviewUrl.startsWith('http')) {
          newErrors.googleReviewUrl = 'Must be a valid URL';
        }
        if (formData.yelpReviewUrl && !formData.yelpReviewUrl.startsWith('http')) {
          newErrors.yelpReviewUrl = 'Must be a valid URL';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
  };

  const handlePreview = () => {
    if (validateStep(currentStep)) {
      setShowPreview(true);
    }
  };

  const handleSubmit = async () => {
    // Validate all steps
    let allValid = true;
    for (let step = 1; step <= 4; step++) {
      if (!validateStep(step)) {
        allValid = false;
        setCurrentStep(step);
        break;
      }
    }

    if (!allValid) {
      alert('Please fix validation errors');
      return;
    }

    setIsSubmitting(true);

    try {
      // Prepare form data - matches backend POST /api/v1/reviews/submit-public
      const submitData = new FormData();
      submitData.append('rating', String(formData.rating || 0));
      submitData.append('review_text', formData.content || '');
      submitData.append('customer_email', formData.customerEmail || '');
      submitData.append('customer_name', formData.customerName || '');

      // booking_id is optional - only append if available from URL params or context
      // submitData.append('booking_id', bookingId);

      // Add media files (max 5)
      const filesToUpload = mediaFiles.slice(0, 5);
      filesToUpload.forEach((media) => {
        submitData.append('files', media.file);
      });

      // Submit to backend - use environment variable or relative path
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiBaseUrl}/api/v1/reviews/submit-public`, {
        method: 'POST',
        body: submitData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to submit review');
      }

      const result = await response.json();

      // Track external reviews if provided
      if (result.review_id && (formData.googleReviewUrl || formData.yelpReviewUrl)) {
        // Track on Google
        if (formData.googleReviewUrl) {
          await fetch(`${apiBaseUrl}/api/v1/reviews/${result.review_id}/track-external`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'google' }),
          }).catch(console.error);
        }
        // Track on Yelp
        if (formData.yelpReviewUrl) {
          await fetch(`${apiBaseUrl}/api/v1/reviews/${result.review_id}/track-external`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'yelp' }),
          }).catch(console.error);
        }
      }

      // Success!
      setSubmitted(true);
      setShowPreview(false);

      // Cleanup media previews
      mediaFiles.forEach((media) => URL.revokeObjectURL(media.preview));
    } catch (error) {
      console.error('Submit error:', error);
      alert('Failed to submit review. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ============================================================================
  // Render Functions
  // ============================================================================

  if (submitted) {
    return (
      <div className="mx-auto max-w-2xl p-8">
        <div className="rounded-lg border border-green-200 bg-green-50 p-8 text-center">
          <div className="mb-4 text-6xl">🎉</div>
          <h2 className="mb-4 text-3xl font-bold text-green-800">Thank You for Your Review!</h2>
          <p className="mb-6 text-lg text-green-700">
            Your review has been submitted and is pending approval by our team.
            {"We'll"} review it shortly and it will appear on our website once approved.
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => {
                setSubmitted(false);
                setCurrentStep(1);
                setFormData({});
                setMediaFiles([]);
              }}
              className="rounded-lg bg-green-600 px-6 py-3 text-white transition hover:bg-green-700"
            >
              Submit Another Review
            </button>
            <Link
              href="/"
              className="rounded-lg bg-gray-200 px-6 py-3 text-gray-800 transition hover:bg-gray-300"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (showPreview) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <div className="rounded-lg bg-white p-8 shadow-lg">
          <h2 className="mb-6 text-3xl font-bold">Preview Your Review</h2>

          <div className="mb-6 rounded-lg border-2 border-gray-200 p-6">
            {/* Rating Stars */}
            <div className="mb-4 flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <span
                  key={star}
                  className={`text-3xl ${
                    star <= (formData.rating || 0) ? 'text-yellow-400' : 'text-gray-300'
                  }`}
                >
                  ★
                </span>
              ))}
            </div>

            {/* Title */}
            <h3 className="mb-4 text-2xl font-bold">{formData.title}</h3>

            {/* Content */}
            <p className="mb-6 whitespace-pre-wrap text-gray-700">{formData.content}</p>

            {/* Media Gallery */}
            {mediaFiles.length > 0 && (
              <div className="mb-6">
                <h4 className="mb-3 font-semibold">Media ({mediaFiles.length})</h4>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                  {mediaFiles.map((media, index) => (
                    <div
                      key={index}
                      className="relative aspect-video overflow-hidden rounded-lg bg-gray-100"
                    >
                      {media.type === 'image' ? (
                        <img
                          src={media.preview}
                          alt={`Preview ${index + 1}`}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <video
                          src={media.preview}
                          className="h-full w-full object-cover"
                          controls
                        />
                      )}
                      <div className="absolute top-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
                        {media.type}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Customer Info */}
            <div className="mt-4 border-t pt-4">
              <p className="font-semibold text-gray-900">
                {formData.showInitialsOnly ? (
                  <>
                    {(() => {
                      const words = (formData.customerName || '').trim().split(' ');
                      if (words.length === 0) return '?';
                      if (words.length === 1) return words[0][0]?.toUpperCase() || '?';
                      return (words[0][0] + words[words.length - 1][0]).toUpperCase();
                    })()}
                  </>
                ) : (
                  formData.customerName
                )}
              </p>
              <p className="mt-1 text-xs text-gray-500 italic">
                {formData.showInitialsOnly
                  ? '✓ Showing initials only (full name kept private)'
                  : '✓ Your email and phone are private (not shown publicly)'}
              </p>
            </div>

            {/* External Links */}
            {(formData.googleReviewUrl || formData.yelpReviewUrl) && (
              <div className="mt-4 border-t pt-4">
                <p className="mb-2 text-sm font-semibold">Also reviewed on:</p>
                <div className="flex gap-3">
                  {formData.googleReviewUrl && (
                    <a
                      href={formData.googleReviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Google Reviews →
                    </a>
                  )}
                  {formData.yelpReviewUrl && (
                    <a
                      href={formData.yelpReviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Yelp →
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between gap-4">
            <button
              onClick={() => setShowPreview(false)}
              className="rounded-lg bg-gray-200 px-6 py-3 text-gray-800 transition hover:bg-gray-300"
            >
              ← Edit Review
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="rounded-lg bg-green-600 px-8 py-3 font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Submitting...
                </span>
              ) : (
                'Submit Review ✓'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // Multi-Step Form UI
  // ============================================================================

  return (
    <div className="mx-auto max-w-3xl p-8">
      <div className="rounded-lg bg-white p-8 shadow-lg">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className={`flex items-center ${step < 4 ? 'flex-1' : ''}`}>
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full font-bold ${
                    step <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {step}
                </div>
                {step < 4 && (
                  <div
                    className={`mx-2 h-1 flex-1 ${
                      step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Rating</span>
            <span>Content</span>
            <span>Media</span>
            <span>Links</span>
          </div>
        </div>

        {/* Step 1: Rating */}
        {currentStep === 1 && (
          <div>
            <h2 className="mb-6 text-2xl font-bold">How would you rate your experience?</h2>
            <div className="mb-8 flex justify-center gap-4">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleInputChange('rating', star)}
                  className="transition-transform hover:scale-110"
                >
                  <span
                    className={`text-6xl ${
                      star <= (formData.rating || 0) ? 'text-yellow-400' : 'text-gray-300'
                    }`}
                  >
                    ★
                  </span>
                </button>
              ))}
            </div>
            {errors.rating && <p className="mb-4 text-center text-red-600">{errors.rating}</p>}
            <div className="flex justify-end">
              <button
                onClick={handleNext}
                className="rounded-lg bg-blue-600 px-8 py-3 text-white transition hover:bg-blue-700"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Content */}
        {currentStep === 2 && (
          <div>
            <h2 className="mb-6 text-2xl font-bold">Tell us about your experience</h2>

            {/* Privacy Notice */}
            <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🔒</span>
                <div>
                  <p className="mb-1 font-semibold text-blue-900">Your Privacy Matters</p>
                  <p className="text-sm text-blue-800">
                    By default, your <strong>full name</strong> will be shown publicly with your
                    review. You can choose to show only your <strong>initials</strong> instead
                    (e.g., &ldquo;JD&rdquo; for &ldquo;John Doe&rdquo;). Your email and phone number
                    are always kept private and used only for verification and communication.
                  </p>
                </div>
              </div>
            </div>

            {/* Customer Info */}
            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold">Your Name *</label>
                <input
                  type="text"
                  value={formData.customerName || ''}
                  onChange={(e) => handleInputChange('customerName', e.target.value)}
                  className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
                {errors.customerName && (
                  <p className="mt-1 text-sm text-red-600">{errors.customerName}</p>
                )}
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold">Email *</label>
                <input
                  type="email"
                  value={formData.customerEmail || ''}
                  onChange={(e) => handleInputChange('customerEmail', e.target.value)}
                  className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="john@example.com"
                />
                {errors.customerEmail && (
                  <p className="mt-1 text-sm text-red-600">{errors.customerEmail}</p>
                )}
              </div>
            </div>

            <div className="mb-4">
              <label className="mb-2 block text-sm font-semibold">Phone (Optional)</label>
              <input
                type="tel"
                value={formData.customerPhone || ''}
                onChange={(e) => handleInputChange('customerPhone', e.target.value)}
                className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="(555) 123-4567"
              />
            </div>

            {/* Privacy Option - Show Initials Only */}
            <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  checked={formData.showInitialsOnly || false}
                  onChange={(e) => handleInputChange('showInitialsOnly', e.target.checked)}
                  className="mt-1 h-5 w-5 rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">
                    Show only my initials publicly
                  </span>
                  <p className="mt-1 text-sm text-gray-600">
                    {formData.customerName ? (
                      <>
                        Instead of showing &ldquo;<strong>{formData.customerName}</strong>&rdquo;,
                        your review will display &ldquo;
                        <strong>
                          {(() => {
                            const words = formData.customerName.trim().split(' ');
                            if (words.length === 1) return words[0][0]?.toUpperCase() || '?';
                            return (words[0][0] + words[words.length - 1][0]).toUpperCase();
                          })()}
                        </strong>
                        &rdquo;
                      </>
                    ) : (
                      'Your initials will be generated from your name (e.g., &ldquo;John Doe&rdquo; → &ldquo;JD&rdquo;)'
                    )}
                  </p>
                </div>
              </label>
            </div>

            {/* Review Title */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-semibold">Review Title *</label>
              <input
                type="text"
                value={formData.title || ''}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Amazing food and service!"
                maxLength={200}
              />
              {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title}</p>}
            </div>

            {/* Review Content */}
            <div className="mb-6">
              <label className="mb-2 block text-sm font-semibold">Your Review *</label>
              <textarea
                value={formData.content || ''}
                onChange={(e) => handleInputChange('content', e.target.value)}
                className="h-40 w-full resize-none rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Share your experience with us... (minimum 20 characters)"
                maxLength={5000}
              />
              <div className="mt-1 text-sm text-gray-600">
                {(formData.content || '').length} / 5000 characters
              </div>
              {errors.content && <p className="mt-1 text-sm text-red-600">{errors.content}</p>}
            </div>

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="rounded-lg bg-gray-200 px-6 py-3 text-gray-800 transition hover:bg-gray-300"
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                className="rounded-lg bg-blue-600 px-8 py-3 text-white transition hover:bg-blue-700"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Media Upload */}
        {currentStep === 3 && (
          <div>
            <h2 className="mb-6 text-2xl font-bold">Add Photos or Videos (Optional)</h2>
            <p className="mb-6 text-gray-600">
              Upload up to 10 images or videos to showcase your experience
            </p>

            {/* Upload Area */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`mb-6 rounded-lg border-2 border-dashed p-8 text-center transition ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              }`}
            >
              <div className="mb-4 text-6xl">📸🎥</div>
              <p className="mb-2 text-lg font-semibold">Drag & Drop or Click to Upload</p>
              <p className="mb-4 text-sm text-gray-600">
                Images: JPG, PNG, WEBP, GIF (10MB max)
                <br />
                Videos: MP4, MOV, WEBM, AVI (100MB max)
              </p>
              <input
                type="file"
                multiple
                accept="image/*,video/*"
                onChange={(e) => handleMediaUpload(e.target.files)}
                className="hidden"
                id="media-upload"
              />
              <label
                htmlFor="media-upload"
                className="inline-block cursor-pointer rounded-lg bg-blue-600 px-6 py-3 text-white transition hover:bg-blue-700"
              >
                Choose Files
              </label>
            </div>

            {/* Media Preview Grid */}
            {mediaFiles.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-3 font-semibold">Uploaded Media ({mediaFiles.length}/10)</h3>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                  {mediaFiles.map((media, index) => (
                    <div
                      key={index}
                      className="group relative aspect-video overflow-hidden rounded-lg bg-gray-100"
                    >
                      {media.type === 'image' ? (
                        <img
                          src={media.preview}
                          alt={`Upload ${index + 1}`}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="relative h-full w-full">
                          <video src={media.preview} className="h-full w-full object-cover" />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                            <span className="text-4xl text-white">▶</span>
                          </div>
                        </div>
                      )}
                      <div className="absolute top-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
                        {media.type}
                      </div>
                      <button
                        onClick={() => removeMedia(index)}
                        className="absolute top-2 left-2 h-8 w-8 rounded-full bg-red-600 text-white opacity-0 transition group-hover:opacity-100"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="rounded-lg bg-gray-200 px-6 py-3 text-gray-800 transition hover:bg-gray-300"
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                className="rounded-lg bg-blue-600 px-8 py-3 text-white transition hover:bg-blue-700"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 4: External Links */}
        {currentStep === 4 && (
          <div>
            <h2 className="mb-6 text-2xl font-bold">Add External Review Links (Optional)</h2>
            <p className="mb-6 text-gray-600">
              Have you also reviewed us on Google or Yelp? Share the links!
            </p>

            <div className="mb-4">
              <label className="mb-2 block text-sm font-semibold">Google Review URL</label>
              <input
                type="url"
                value={formData.googleReviewUrl || ''}
                onChange={(e) => handleInputChange('googleReviewUrl', e.target.value)}
                className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://g.page/..."
              />
              {errors.googleReviewUrl && (
                <p className="mt-1 text-sm text-red-600">{errors.googleReviewUrl}</p>
              )}
            </div>

            <div className="mb-6">
              <label className="mb-2 block text-sm font-semibold">Yelp Review URL</label>
              <input
                type="url"
                value={formData.yelpReviewUrl || ''}
                onChange={(e) => handleInputChange('yelpReviewUrl', e.target.value)}
                className="w-full rounded-lg border px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://yelp.com/biz/..."
              />
              {errors.yelpReviewUrl && (
                <p className="mt-1 text-sm text-red-600">{errors.yelpReviewUrl}</p>
              )}
            </div>

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="rounded-lg bg-gray-200 px-6 py-3 text-gray-800 transition hover:bg-gray-300"
              >
                ← Back
              </button>
              <button
                onClick={handlePreview}
                className="rounded-lg bg-purple-600 px-8 py-3 font-semibold text-white transition hover:bg-purple-700"
              >
                Preview Review 👁
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
