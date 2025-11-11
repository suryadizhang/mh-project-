# 📝 Customer Review Blog System - Implementation Guide

## Overview
Enterprise-grade customer review blog system with image upload, admin approval, and integration with Google/Yelp review flow.

**Pattern:** Like Facebook newsfeed + Yelp reviews + Instagram stories

---

## Database Schema

### New Tables

```sql
-- Customer review blog posts
CREATE TABLE customer_review_blog_posts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    booking_id INTEGER REFERENCES bookings(id),
    
    -- Content
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    -- Images
    images JSONB DEFAULT '[]', -- Array of image URLs
    
    -- Status (admin approval workflow)
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    
    -- External reviews (track if they also reviewed on Google/Yelp)
    reviewed_on_google BOOLEAN DEFAULT FALSE,
    reviewed_on_yelp BOOLEAN DEFAULT FALSE,
    google_review_link TEXT,
    yelp_review_link TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- SEO
    slug VARCHAR(255) UNIQUE,
    keywords TEXT[],
    
    -- Engagement
    likes_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    
    INDEX idx_status (status),
    INDEX idx_customer (customer_id),
    INDEX idx_created (created_at DESC),
    INDEX idx_rating (rating)
);

-- Image uploads (temporary storage before approval)
CREATE TABLE customer_review_images (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES customer_review_blog_posts(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    original_filename VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(50),
    width INTEGER,
    height INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin approval log (audit trail)
CREATE TABLE review_approval_log (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES customer_review_blog_posts(id),
    admin_id INTEGER REFERENCES users(id),
    action VARCHAR(20), -- approved, rejected, pending_review
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Backend API

### 1. Customer Review Submission Endpoint

```python
# apps/backend/src/api/customer_reviews/router.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from PIL import Image
import io

from ..dependencies import get_db, get_current_customer
from ..services.image_service import ImageService
from ..services.email_service import EmailService
from ..models import CustomerReviewBlogPost, Customer

router = APIRouter(prefix="/api/customer-reviews", tags=["customer-reviews"])

@router.post("/submit-review")
async def submit_customer_review(
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(..., ge=1, le=5),
    booking_id: Optional[int] = Form(None),
    reviewed_on_google: bool = Form(False),
    reviewed_on_yelp: bool = Form(False),
    google_review_link: Optional[str] = Form(None),
    yelp_review_link: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer)
):
    """
    Submit a customer review with optional images
    
    Enterprise Features:
    - Image upload with validation
    - Thumbnail generation
    - Admin approval workflow
    - Email notifications
    - Integration with Google/Yelp reviews
    """
    
    # Validate image count
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    
    # Create review post (pending approval)
    review = CustomerReviewBlogPost(
        customer_id=customer.id,
        booking_id=booking_id,
        title=title,
        content=content,
        rating=rating,
        status='pending',
        reviewed_on_google=reviewed_on_google,
        reviewed_on_yelp=reviewed_on_yelp,
        google_review_link=google_review_link,
        yelp_review_link=yelp_review_link,
        slug=f"{uuid.uuid4()}-{title.lower().replace(' ', '-')[:50]}"
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Process and upload images
    image_service = ImageService()
    uploaded_images = []
    
    for image_file in images:
        # Validate image
        if not image_file.content_type.startswith('image/'):
            continue
        
        # Read image
        contents = await image_file.read()
        
        # Validate size (max 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Image {image_file.filename} exceeds 10MB")
        
        # Process image
        image = Image.open(io.BytesIO(contents))
        
        # Generate optimized version
        optimized = image_service.optimize_image(image, max_width=1920, quality=85)
        
        # Generate thumbnail
        thumbnail = image_service.generate_thumbnail(image, size=(400, 300))
        
        # Upload to storage (S3, Cloudinary, etc.)
        image_url = await image_service.upload_image(
            optimized,
            f"reviews/{review.id}/{uuid.uuid4()}.jpg"
        )
        
        thumbnail_url = await image_service.upload_image(
            thumbnail,
            f"reviews/{review.id}/thumb_{uuid.uuid4()}.jpg"
        )
        
        # Store image metadata
        uploaded_images.append({
            'url': image_url,
            'thumbnail': thumbnail_url,
            'width': image.width,
            'height': image.height,
            'filename': image_file.filename
        })
    
    # Update review with images
    review.images = uploaded_images
    db.commit()
    
    # Send email notification to admin
    email_service = EmailService()
    await email_service.notify_admin_new_review(review)
    
    # Log submission
    from ..models import ReviewApprovalLog
    log = ReviewApprovalLog(
        review_id=review.id,
        action='pending_review',
        comment='New review submitted by customer'
    )
    db.add(log)
    db.commit()
    
    return JSONResponse(
        status_code=201,
        content={
            'success': True,
            'message': 'Review submitted successfully! It will appear after admin approval.',
            'review_id': review.id,
            'status': 'pending'
        }
    )

@router.get("/my-reviews")
async def get_my_reviews(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer)
):
    """Get customer's own reviews"""
    reviews = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.customer_id == customer.id
    ).order_by(CustomerReviewBlogPost.created_at.desc()).all()
    
    return {
        'reviews': [
            {
                'id': r.id,
                'title': r.title,
                'content': r.content,
                'rating': r.rating,
                'images': r.images,
                'status': r.status,
                'created_at': r.created_at.isoformat(),
                'rejection_reason': r.rejection_reason if r.status == 'rejected' else None
            }
            for r in reviews
        ]
    }

@router.get("/approved-reviews")
async def get_approved_reviews(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get approved customer reviews (public endpoint)
    
    Features:
    - Pagination
    - Newest first (like Facebook newsfeed)
    - Only approved reviews
    """
    offset = (page - 1) * per_page
    
    reviews = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.status == 'approved'
    ).order_by(
        CustomerReviewBlogPost.approved_at.desc()
    ).offset(offset).limit(per_page).all()
    
    total = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.status == 'approved'
    ).count()
    
    return {
        'reviews': [
            {
                'id': r.id,
                'title': r.title,
                'content': r.content,
                'rating': r.rating,
                'images': r.images,
                'customer_name': f"{r.customer.first_name} {r.customer.last_name[0]}.",
                'created_at': r.created_at.isoformat(),
                'likes_count': r.likes_count,
                'helpful_count': r.helpful_count
            }
            for r in reviews
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }
```

---

### 2. Admin Approval Endpoints

```python
# apps/backend/src/api/admin/review_moderation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..dependencies import get_db, get_current_admin_user
from ..models import CustomerReviewBlogPost, ReviewApprovalLog, User

router = APIRouter(prefix="/api/admin/review-moderation", tags=["admin"])

@router.get("/pending-reviews")
async def get_pending_reviews(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get all pending reviews for admin approval
    
    Features:
    - Pagination
    - Oldest first (FIFO queue)
    - Full customer details for context
    """
    offset = (page - 1) * per_page
    
    reviews = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.status == 'pending'
    ).order_by(
        CustomerReviewBlogPost.created_at.asc()  # Oldest first (queue)
    ).offset(offset).limit(per_page).all()
    
    total = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.status == 'pending'
    ).count()
    
    return {
        'reviews': [
            {
                'id': r.id,
                'title': r.title,
                'content': r.content,
                'rating': r.rating,
                'images': r.images,
                'customer': {
                    'id': r.customer.id,
                    'name': f"{r.customer.first_name} {r.customer.last_name}",
                    'email': r.customer.email,
                    'phone': r.customer.phone
                },
                'booking_id': r.booking_id,
                'reviewed_on_google': r.reviewed_on_google,
                'reviewed_on_yelp': r.reviewed_on_yelp,
                'google_review_link': r.google_review_link,
                'yelp_review_link': r.yelp_review_link,
                'created_at': r.created_at.isoformat()
            }
            for r in reviews
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }

@router.post("/approve-review/{review_id}")
async def approve_review(
    review_id: int,
    admin_comment: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Approve a customer review"""
    review = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.id == review_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.status != 'pending':
        raise HTTPException(status_code=400, detail="Review already processed")
    
    # Approve review
    review.status = 'approved'
    review.approved_by = admin.id
    review.approved_at = datetime.utcnow()
    
    # Log approval
    log = ReviewApprovalLog(
        review_id=review.id,
        admin_id=admin.id,
        action='approved',
        comment=admin_comment or 'Approved by admin'
    )
    db.add(log)
    db.commit()
    
    # Send email to customer
    from ..services.email_service import EmailService
    email_service = EmailService()
    await email_service.notify_customer_review_approved(review)
    
    return {
        'success': True,
        'message': 'Review approved successfully',
        'review_id': review_id
    }

@router.post("/reject-review/{review_id}")
async def reject_review(
    review_id: int,
    rejection_reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Reject a customer review with reason"""
    review = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.id == review_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.status != 'pending':
        raise HTTPException(status_code=400, detail="Review already processed")
    
    # Reject review
    review.status = 'rejected'
    review.rejection_reason = rejection_reason
    
    # Log rejection
    log = ReviewApprovalLog(
        review_id=review.id,
        admin_id=admin.id,
        action='rejected',
        comment=rejection_reason
    )
    db.add(log)
    db.commit()
    
    # Send email to customer with reason
    from ..services.email_service import EmailService
    email_service = EmailService()
    await email_service.notify_customer_review_rejected(review, rejection_reason)
    
    return {
        'success': True,
        'message': 'Review rejected',
        'review_id': review_id
    }

@router.post("/bulk-action")
async def bulk_review_action(
    action: str,  # approve or reject
    review_ids: List[int],
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Bulk approve/reject reviews"""
    if action not in ['approve', 'reject']:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    reviews = db.query(CustomerReviewBlogPost).filter(
        CustomerReviewBlogPost.id.in_(review_ids),
        CustomerReviewBlogPost.status == 'pending'
    ).all()
    
    processed = []
    for review in reviews:
        if action == 'approve':
            review.status = 'approved'
            review.approved_by = admin.id
            review.approved_at = datetime.utcnow()
        else:
            review.status = 'rejected'
            review.rejection_reason = reason or 'Rejected by admin'
        
        # Log action
        log = ReviewApprovalLog(
            review_id=review.id,
            admin_id=admin.id,
            action=action + 'd',
            comment=reason or f'Bulk {action} by admin'
        )
        db.add(log)
        processed.append(review.id)
    
    db.commit()
    
    return {
        'success': True,
        'message': f'Bulk {action} completed',
        'processed_count': len(processed),
        'processed_ids': processed
    }
```

---

## Frontend Components

### 1. Customer Review Submission Form

```typescript
// apps/customer/src/components/reviews/CustomerReviewForm.tsx
'use client'

import { useState } from 'react'
import { Upload, Star, Check, AlertCircle, X, Image as ImageIcon } from 'lucide-react'
import Image from 'next/image'

interface CustomerReviewFormProps {
  bookingId?: number
  onSuccess?: () => void
}

export default function CustomerReviewForm({ bookingId, onSuccess }: CustomerReviewFormProps) {
  const [step, setStep] = useState<'rating' | 'content' | 'images' | 'external'>('rating')
  const [rating, setRating] = useState(0)
  const [hoverRating, setHoverRating] = useState(0)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [images, setImages] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [reviewedOnGoogle, setReviewedOnGoogle] = useState(false)
  const [reviewedOnYelp, setReviewedOnYelp] = useState(false)
  const [googleLink, setGoogleLink] = useState('')
  const [yelpLink, setYelpLink] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    
    if (images.length + files.length > 10) {
      setError('Maximum 10 images allowed')
      return
    }
    
    // Validate file size (10MB max per image)
    const invalidFiles = files.filter(f => f.size > 10 * 1024 * 1024)
    if (invalidFiles.length > 0) {
      setError('Each image must be under 10MB')
      return
    }
    
    setImages([...images, ...files])
    
    // Generate previews
    files.forEach(file => {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviews(prev => [...prev, reader.result as string])
      }
      reader.readAsDataURL(file)
    })
    
    setError('')
  }
  
  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index))
    setPreviews(previews.filter((_, i) => i !== index))
  }
  
  const handleSubmit = async () => {
    setIsSubmitting(true)
    setError('')
    
    try {
      const formData = new FormData()
      formData.append('title', title)
      formData.append('content', content)
      formData.append('rating', rating.toString())
      if (bookingId) formData.append('booking_id', bookingId.toString())
      formData.append('reviewed_on_google', reviewedOnGoogle.toString())
      formData.append('reviewed_on_yelp', reviewedOnYelp.toString())
      if (googleLink) formData.append('google_review_link', googleLink)
      if (yelpLink) formData.append('yelp_review_link', yelpLink)
      
      images.forEach(image => {
        formData.append('images', image)
      })
      
      const response = await fetch('/api/customer-reviews/submit-review', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit review')
      }
      
      setSuccess(true)
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review')
    } finally {
      setIsSubmitting(false)
    }
  }
  
  if (success) {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-white rounded-lg shadow-lg text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Thank You!</h2>
        <p className="text-gray-600 mb-6">
          Your review has been submitted and will appear on our blog after admin approval.
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => window.location.href = '/'}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Back to Home
          </button>
          <button
            onClick={() => window.location.href = '/my-reviews'}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            View My Reviews
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded-lg shadow-lg">
      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {['Rating', 'Content', 'Images', 'External Reviews'].map((stepName, index) => (
          <div key={stepName} className="flex-1 flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              ['rating', 'content', 'images', 'external'].indexOf(step) >= index
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 text-gray-500'
            }`}>
              {index + 1}
            </div>
            {index < 3 && (
              <div className={`flex-1 h-1 mx-2 ${
                ['rating', 'content', 'images', 'external'].indexOf(step) > index
                  ? 'bg-red-600'
                  : 'bg-gray-200'
              }`} />
            )}
          </div>
        ))}
      </div>
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
          <p className="text-red-600">{error}</p>
        </div>
      )}
      
      {/* Step 1: Rating */}
      {step === 'rating' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">How was your experience?</h2>
          <div className="flex items-center gap-2 mb-8 justify-center">
            {[1, 2, 3, 4, 5].map(value => (
              <button
                key={value}
                onMouseEnter={() => setHoverRating(value)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(value)}
                className="transition-transform hover:scale-110"
              >
                <Star
                  className={`w-12 h-12 ${
                    (hoverRating || rating) >= value
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
          <div className="text-center mb-6">
            {rating > 0 && (
              <p className="text-gray-600">
                {rating === 1 && 'We\'re sorry to hear that'}
                {rating === 2 && 'We can do better'}
                {rating === 3 && 'Good experience'}
                {rating === 4 && 'Great experience!'}
                {rating === 5 && 'Excellent! Thank you!'}
              </p>
            )}
          </div>
          <button
            onClick={() => setStep('content')}
            disabled={rating === 0}
            className="w-full py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      )}
      
      {/* Step 2: Content */}
      {step === 'content' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Tell us about your experience</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Title</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g., Amazing hibachi experience for my birthday!"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
                maxLength={100}
              />
              <p className="text-sm text-gray-500 mt-1">{title.length}/100</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Your Story</label>
              <textarea
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Share the details of your experience with us..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 h-40"
                maxLength={2000}
              />
              <p className="text-sm text-gray-500 mt-1">{content.length}/2000</p>
            </div>
          </div>
          <div className="flex gap-4 mt-6">
            <button
              onClick={() => setStep('rating')}
              className="flex-1 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={() => setStep('images')}
              disabled={!title || !content || content.length < 50}
              className="flex-1 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Continue
            </button>
          </div>
        </div>
      )}
      
      {/* Step 3: Images */}
      {step === 'images' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Add Photos (Optional)</h2>
          <p className="text-gray-600 mb-6">Share your favorite moments! Up to 10 images, max 10MB each.</p>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
              id="image-upload"
            />
            <label
              htmlFor="image-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-12 h-12 text-gray-400 mb-2" />
              <p className="text-gray-600 mb-1">Click to upload images</p>
              <p className="text-sm text-gray-400">PNG, JPG, WEBP up to 10MB each</p>
            </label>
          </div>
          
          {/* Image Previews */}
          {previews.length > 0 && (
            <div className="grid grid-cols-3 gap-4 mb-6">
              {previews.map((preview, index) => (
                <div key={index} className="relative aspect-square">
                  <Image
                    src={preview}
                    alt={`Preview ${index + 1}`}
                    fill
                    className="object-cover rounded-lg"
                  />
                  <button
                    onClick={() => removeImage(index)}
                    className="absolute top-2 right-2 p-1 bg-red-600 text-white rounded-full hover:bg-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex gap-4">
            <button
              onClick={() => setStep('content')}
              className="flex-1 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={() => setStep('external')}
              className="flex-1 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Continue
            </button>
          </div>
        </div>
      )}
      
      {/* Step 4: External Reviews */}
      {step === 'external' && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Also review us on Google & Yelp?</h2>
          <p className="text-gray-600 mb-6">
            Help us grow by sharing your experience on Google and Yelp! It takes just a minute.
          </p>
          
          <div className="space-y-4 mb-6">
            <div className="p-4 border border-gray-200 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reviewedOnGoogle}
                  onChange={e => setReviewedOnGoogle(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Google Business</span>
                    <span className="text-sm bg-blue-100 text-blue-600 px-2 py-0.5 rounded">Recommended</span>
                  </div>
                  <p className="text-sm text-gray-500">Review us on Google</p>
                </div>
              </label>
              {reviewedOnGoogle && (
                <div className="mt-3">
                  <input
                    type="url"
                    value={googleLink}
                    onChange={e => setGoogleLink(e.target.value)}
                    placeholder="Paste your Google review link (optional)"
                    className="w-full p-2 border border-gray-300 rounded text-sm"
                  />
                  <a
                    href="https://g.page/r/YOUR_GOOGLE_PLACE_ID/review"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 text-sm text-blue-600 hover:underline"
                  >
                    Open Google Review Page →
                  </a>
                </div>
              )}
            </div>
            
            <div className="p-4 border border-gray-200 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reviewedOnYelp}
                  onChange={e => setReviewedOnYelp(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Yelp</span>
                  </div>
                  <p className="text-sm text-gray-500">Review us on Yelp</p>
                </div>
              </label>
              {reviewedOnYelp && (
                <div className="mt-3">
                  <input
                    type="url"
                    value={yelpLink}
                    onChange={e => setYelpLink(e.target.value)}
                    placeholder="Paste your Yelp review link (optional)"
                    className="w-full p-2 border border-gray-300 rounded text-sm"
                  />
                  <a
                    href="https://www.yelp.com/writeareview/biz/YOUR_YELP_ID"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 text-sm text-red-600 hover:underline"
                  >
                    Open Yelp Review Page →
                  </a>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex gap-4">
            <button
              onClick={() => setStep('images')}
              className="flex-1 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex-1 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

This is getting very long. Let me create a summary document instead with all the implementation details:
