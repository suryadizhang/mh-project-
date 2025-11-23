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
      // Prepare form data
      const submitData = new FormData();
      submitData.append('customer_id', '1'); // TODO: Get from auth
      submitData.append('customer_name', formData.customerName || '');
      submitData.append('customer_email', formData.customerEmail || '');
      submitData.append('customer_phone', formData.customerPhone || '');
      submitData.append('show_initials_only', String(formData.showInitialsOnly || false));
      submitData.append('title', formData.title || '');
      submitData.append('content', formData.content || '');
      submitData.append('rating', String(formData.rating || 0));

      if (formData.googleReviewUrl) {
        submitData.append('reviewed_on_google', 'true');
        submitData.append('google_review_link', formData.googleReviewUrl);
      }
      if (formData.yelpReviewUrl) {
        submitData.append('reviewed_on_yelp', 'true');
        submitData.append('yelp_review_link', formData.yelpReviewUrl);
      }

      // Add media files
      mediaFiles.forEach((media) => {
        submitData.append('media_files', media.file);
      });

      // Submit to backend
      const response = await fetch('http://localhost:8000/api/customer-reviews/submit-review', {
        method: 'POST',
        body: submitData,
      });

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      const result = await response.json();

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
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-green-800 mb-4">
            Thank You for Your Review!
          </h2>
          <p className="text-lg text-green-700 mb-6">
            Your review has been submitted and is pending approval by our team.
            {"We'll"} review it shortly and it will appear on our website once approved.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => {
                setSubmitted(false);
                setCurrentStep(1);
                setFormData({});
                setMediaFiles([]);
              }}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              Submit Another Review
            </button>
            <Link
              href="/"
              className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
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
      <div className="max-w-4xl mx-auto p-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold mb-6">Preview Your Review</h2>

          <div className="border-2 border-gray-200 rounded-lg p-6 mb-6">
            {/* Rating Stars */}
            <div className="flex items-center gap-2 mb-4">
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
            <h3 className="text-2xl font-bold mb-4">{formData.title}</h3>

            {/* Content */}
            <p className="text-gray-700 whitespace-pre-wrap mb-6">{formData.content}</p>

            {/* Media Gallery */}
            {mediaFiles.length > 0 && (
              <div className="mb-6">
                <h4 className="font-semibold mb-3">Media ({mediaFiles.length})</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {mediaFiles.map((media, index) => (
                    <div key={index} className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                      {media.type === 'image' ? (
                        <img
                          src={media.preview}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <video
                          src={media.preview}
                          className="w-full h-full object-cover"
                          controls
                        />
                      )}
                      <div className="absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs">
                        {media.type}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Customer Info */}
            <div className="border-t pt-4 mt-4">
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
              <p className="text-xs text-gray-500 italic mt-1">
                {formData.showInitialsOnly ? (
                  '✓ Showing initials only (full name kept private)'
                ) : (
                  '✓ Your email and phone are private (not shown publicly)'
                )}
              </p>
            </div>

            {/* External Links */}
            {(formData.googleReviewUrl || formData.yelpReviewUrl) && (
              <div className="border-t pt-4 mt-4">
                <p className="text-sm font-semibold mb-2">Also reviewed on:</p>
                <div className="flex gap-3">
                  {formData.googleReviewUrl && (
                    <a
                      href={formData.googleReviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm"
                    >
                      Google Reviews →
                    </a>
                  )}
                  {formData.yelpReviewUrl && (
                    <a
                      href={formData.yelpReviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm"
                    >
                      Yelp →
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-between">
            <button
              onClick={() => setShowPreview(false)}
              className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
            >
              ← Edit Review
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
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
    <div className="max-w-3xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            {[1, 2, 3, 4].map((step) => (
              <div
                key={step}
                className={`flex items-center ${step < 4 ? 'flex-1' : ''}`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                    step <= currentStep
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {step}
                </div>
                {step < 4 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
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
            <h2 className="text-2xl font-bold mb-6">How would you rate your experience?</h2>
            <div className="flex justify-center gap-4 mb-8">
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
            {errors.rating && <p className="text-red-600 text-center mb-4">{errors.rating}</p>}
            <div className="flex justify-end">
              <button
                onClick={handleNext}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Content */}
        {currentStep === 2 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Tell us about your experience</h2>

            {/* Privacy Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🔒</span>
                <div>
                  <p className="font-semibold text-blue-900 mb-1">Your Privacy Matters</p>
                  <p className="text-sm text-blue-800">
                    By default, your <strong>full name</strong> will be shown publicly with your review.
                    You can choose to show only your <strong>initials</strong> instead (e.g., &ldquo;JD&rdquo; for &ldquo;John Doe&rdquo;).
                    Your email and phone number are always kept private and used only for verification
                    and communication.
                  </p>
                </div>
              </div>
            </div>

            {/* Customer Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Your Name *</label>
                <input
                  type="text"
                  value={formData.customerName || ''}
                  onChange={(e) => handleInputChange('customerName', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="John Doe"
                />
                {errors.customerName && <p className="text-red-600 text-sm mt-1">{errors.customerName}</p>}
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Email *</label>
                <input
                  type="email"
                  value={formData.customerEmail || ''}
                  onChange={(e) => handleInputChange('customerEmail', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="john@example.com"
                />
                {errors.customerEmail && <p className="text-red-600 text-sm mt-1">{errors.customerEmail}</p>}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold mb-2">Phone (Optional)</label>
              <input
                type="tel"
                value={formData.customerPhone || ''}
                onChange={(e) => handleInputChange('customerPhone', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="(555) 123-4567"
              />
            </div>

            {/* Privacy Option - Show Initials Only */}
            <div className="mb-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.showInitialsOnly || false}
                  onChange={(e) => handleInputChange('showInitialsOnly', e.target.checked)}
                  className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Show only my initials publicly</span>
                  <p className="text-sm text-gray-600 mt-1">
                    {formData.customerName ? (
                      <>
                        Instead of showing &ldquo;<strong>{formData.customerName}</strong>&rdquo;,
                        your review will display &ldquo;<strong>{
                          (() => {
                            const words = formData.customerName.trim().split(' ');
                            if (words.length === 1) return words[0][0]?.toUpperCase() || '?';
                            return (words[0][0] + words[words.length - 1][0]).toUpperCase();
                          })()
                        }</strong>&rdquo;
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
              <label className="block text-sm font-semibold mb-2">Review Title *</label>
              <input
                type="text"
                value={formData.title || ''}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Amazing food and service!"
                maxLength={200}
              />
              {errors.title && <p className="text-red-600 text-sm mt-1">{errors.title}</p>}
            </div>

            {/* Review Content */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">Your Review *</label>
              <textarea
                value={formData.content || ''}
                onChange={(e) => handleInputChange('content', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none h-40 resize-none"
                placeholder="Share your experience with us... (minimum 20 characters)"
                maxLength={5000}
              />
              <div className="text-sm text-gray-600 mt-1">
                {(formData.content || '').length} / 5000 characters
              </div>
              {errors.content && <p className="text-red-600 text-sm mt-1">{errors.content}</p>}
            </div>

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Media Upload */}
        {currentStep === 3 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Add Photos or Videos (Optional)</h2>
            <p className="text-gray-600 mb-6">
              Upload up to 10 images or videos to showcase your experience
            </p>

            {/* Upload Area */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center mb-6 transition ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              }`}
            >
              <div className="text-6xl mb-4">📸🎥</div>
              <p className="text-lg font-semibold mb-2">
                Drag & Drop or Click to Upload
              </p>
              <p className="text-sm text-gray-600 mb-4">
                Images: JPG, PNG, WEBP, GIF (10MB max)<br />
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
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition cursor-pointer"
              >
                Choose Files
              </label>
            </div>

            {/* Media Preview Grid */}
            {mediaFiles.length > 0 && (
              <div className="mb-6">
                <h3 className="font-semibold mb-3">
                  Uploaded Media ({mediaFiles.length}/10)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {mediaFiles.map((media, index) => (
                    <div
                      key={index}
                      className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden group"
                    >
                      {media.type === 'image' ? (
                        <img
                          src={media.preview}
                          alt={`Upload ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="relative w-full h-full">
                          <video
                            src={media.preview}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                            <span className="text-white text-4xl">▶</span>
                          </div>
                        </div>
                      )}
                      <div className="absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs">
                        {media.type}
                      </div>
                      <button
                        onClick={() => removeMedia(index)}
                        className="absolute top-2 left-2 bg-red-600 text-white w-8 h-8 rounded-full opacity-0 group-hover:opacity-100 transition"
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
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Step 4: External Links */}
        {currentStep === 4 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Add External Review Links (Optional)</h2>
            <p className="text-gray-600 mb-6">
              Have you also reviewed us on Google or Yelp? Share the links!
            </p>

            <div className="mb-4">
              <label className="block text-sm font-semibold mb-2">
                Google Review URL
              </label>
              <input
                type="url"
                value={formData.googleReviewUrl || ''}
                onChange={(e) => handleInputChange('googleReviewUrl', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="https://g.page/..."
              />
              {errors.googleReviewUrl && <p className="text-red-600 text-sm mt-1">{errors.googleReviewUrl}</p>}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2">
                Yelp Review URL
              </label>
              <input
                type="url"
                value={formData.yelpReviewUrl || ''}
                onChange={(e) => handleInputChange('yelpReviewUrl', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="https://yelp.com/biz/..."
              />
              {errors.yelpReviewUrl && <p className="text-red-600 text-sm mt-1">{errors.yelpReviewUrl}</p>}
            </div>

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
              >
                ← Back
              </button>
              <button
                onClick={handlePreview}
                className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-semibold"
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
