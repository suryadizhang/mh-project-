'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Star, ExternalLink, CheckCircle, MessageSquare, ThumbsUp, Users, Calendar, Trophy } from 'lucide-react'

interface Review {
  id: string
  customerName: string
  rating: number
  comment: string
  eventDate: string
  verified: boolean
  helpful: number
  createdAt: string
  bookingId?: string
}

const REVIEW_PLATFORMS = [
  {
    name: 'Google Reviews',
    icon: '🔍',
    url: 'https://g.page/r/YOUR_GOOGLE_BUSINESS_ID/review',
    color: 'bg-blue-500 hover:bg-blue-600',
    description: 'Help others discover our authentic hibachi experience',
    incentive: 'Get 5% off your next booking!'
  },
  {
    name: 'Yelp',
    icon: '🌟',
    url: 'https://www.yelp.com/writeareview/biz/YOUR_YELP_BUSINESS_ID',
    color: 'bg-red-500 hover:bg-red-600',
    description: 'Share your hibachi story with the foodie community',
    incentive: 'Enter monthly drawing for free hibachi!'
  },
  {
    name: 'Facebook',
    icon: '📘',
    url: 'https://www.facebook.com/people/My-hibachi/61577483702847/',
    color: 'bg-blue-600 hover:bg-blue-700',
    description: 'Tell your friends about your hibachi adventure',
    incentive: 'Share with friends for bonus discount!'
  },
  {
    name: 'TripAdvisor',
    icon: '🗺️',
    url: 'https://www.tripadvisor.com/UserReviewEdit-YOUR_TRIPADVISOR_ID',
    color: 'bg-green-600 hover:bg-green-700',
    description: 'Help travelers find the best hibachi experience',
    incentive: 'VIP status for future bookings!'
  }
]

const INITIAL_REVIEWS: Review[] = [
  {
    id: '1',
    customerName: 'Sarah M.',
    rating: 5,
    comment: 'Chef Kevin was absolutely incredible! The hibachi show was entertaining and the food was fresh and delicious. My kids loved the volcano onion and the shrimp was perfectly cooked. Will definitely book again for my husband\'s birthday!',
    eventDate: '2025-07-15',
    verified: true,
    helpful: 24,
    createdAt: '2025-07-16T10:30:00Z',
    bookingId: 'MH-20250715-A1B2'
  },
  {
    id: '2',
    customerName: 'Michael R.',
    rating: 5,
    comment: 'MyHibachi made our anniversary unforgettable! The chef arrived on time, was professional, and created an amazing atmosphere in our backyard. The steak was restaurant-quality and the fried rice was the best I\'ve ever had. Highly recommend!',
    eventDate: '2025-07-20',
    verified: true,
    helpful: 18,
    createdAt: '2025-07-21T14:15:00Z',
    bookingId: 'MH-20250720-C3D4'
  },
  {
    id: '3',
    customerName: 'Jennifer L.',
    rating: 5,
    comment: 'Booked MyHibachi for my daughter\'s sweet 16 and it was perfect! The chef was engaging with all the teenagers, the food was amazing, and cleanup was hassle-free. Worth every penny for such a unique experience.',
    eventDate: '2025-07-28',
    verified: true,
    helpful: 31,
    createdAt: '2025-07-29T09:45:00Z',
    bookingId: 'MH-20250728-E5F6'
  },
  {
    id: '4',
    customerName: 'David K.',
    rating: 5,
    comment: 'Outstanding service from start to finish! The booking process was seamless, the chef was punctual and professional, and the food exceeded our expectations. Our corporate event was a huge success thanks to MyHibachi.',
    eventDate: '2025-07-10',
    verified: true,
    helpful: 15,
    createdAt: '2025-07-11T16:20:00Z',
    bookingId: 'MH-20250710-G7H8'
  }
]

export default function ReviewPage() {
  const [reviews, setReviews] = useState<Review[]>(INITIAL_REVIEWS)
  const [newReview, setNewReview] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [selectedRating, setSelectedRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [showThankYou, setShowThankYou] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [reviewStats, setReviewStats] = useState({
    totalReviews: 0,
    averageRating: 0,
    fiveStarCount: 0,
    recommendationRate: 0,
    verifiedReviews: 0
  })

  useEffect(() => {
    // Calculate review statistics
    if (reviews.length > 0) {
      const totalReviews = reviews.length
      const totalRating = reviews.reduce((sum, review) => sum + review.rating, 0)
      const averageRating = totalRating / totalReviews
      const fiveStarCount = reviews.filter(review => review.rating === 5).length
      const recommendationRate = (fiveStarCount / totalReviews) * 100
      const verifiedReviews = reviews.filter(review => review.verified).length

      setReviewStats({
        totalReviews,
        averageRating: Math.round(averageRating * 10) / 10,
        fiveStarCount,
        recommendationRate: Math.round(recommendationRate),
        verifiedReviews
      })
    }
  }, [reviews])

  const handleInternalReviewSubmit = async () => {
    if (selectedRating > 0 && newReview.trim() && customerName.trim()) {
      setIsSubmitting(true)

      try {
        // In production, this would call your API
        const review: Review = {
          id: Date.now().toString(),
          customerName: customerName.trim(),
          rating: selectedRating,
          comment: newReview.trim(),
          eventDate: new Date().toISOString().split('T')[0],
          verified: false, // Would be verified after admin approval
          helpful: 0,
          createdAt: new Date().toISOString()
        }

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000))

        setReviews([review, ...reviews])
        setNewReview('')
        setCustomerName('')
        setSelectedRating(0)
        setShowThankYou(true)

        // Hide thank you message after 4 seconds
        setTimeout(() => setShowThankYou(false), 4000)
      } catch (error) {
        console.error('Failed to submit review:', error)
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const handleHelpfulClick = (reviewId: string) => {
    setReviews(reviews.map(review => 
      review.id === reviewId 
        ? { ...review, helpful: review.helpful + 1 }
        : review
    ))
  }

  const renderStars = (rating: number, interactive = false, size = 'w-5 h-5') => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`${size} ${
              star <= (interactive ? hoveredRating || selectedRating : rating)
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300'
            } ${interactive ? 'cursor-pointer hover:scale-110 transition-transform' : ''}`}
            onClick={interactive ? () => setSelectedRating(star) : undefined}
            onMouseEnter={interactive ? () => setHoveredRating(star) : undefined}
            onMouseLeave={interactive ? () => setHoveredRating(0) : undefined}
          />
        ))}
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50">
      <div className="container mx-auto px-4 py-12">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Share Your MyHibachi Experience
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Help others discover the authentic hibachi experience that brings restaurant-quality Japanese cuisine directly to their home.
          </p>
        </div>

        {/* Review Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="flex justify-center mb-4">
                <Trophy className="w-8 h-8 text-orange-600" />
              </div>
              <div className="text-3xl font-bold text-orange-600 mb-2">
                {reviewStats.averageRating}
              </div>
              <div className="flex justify-center mb-2">
                {renderStars(Math.round(reviewStats.averageRating))}
              </div>
              <p className="text-sm text-gray-600">Average Rating</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="flex justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-blue-600" />
              </div>
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {reviewStats.totalReviews}
              </div>
              <p className="text-sm text-gray-600">Total Reviews</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="flex justify-center mb-4">
                <ThumbsUp className="w-8 h-8 text-green-600" />
              </div>
              <div className="text-3xl font-bold text-green-600 mb-2">
                {reviewStats.recommendationRate}%
              </div>
              <p className="text-sm text-gray-600">Recommend Us</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="flex justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-purple-600" />
              </div>
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {reviewStats.verifiedReviews}
              </div>
              <p className="text-sm text-gray-600">Verified Reviews</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="flex justify-center mb-4">
                <Users className="w-8 h-8 text-indigo-600" />
              </div>
              <div className="text-3xl font-bold text-indigo-600 mb-2">
                {reviewStats.fiveStarCount}
              </div>
              <p className="text-sm text-gray-600">Five Star Reviews</p>
            </CardContent>
          </Card>
        </div>

        {/* Review Platforms with Incentives */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Leave a Review & Get Rewarded!</CardTitle>
            <CardDescription className="text-center">
              Share your experience on these platforms and enjoy exclusive benefits
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {REVIEW_PLATFORMS.map((platform) => (
                <Button
                  key={platform.name}
                  variant="outline"
                  className={`h-auto p-6 flex flex-col items-center gap-3 border-2 hover:border-transparent transition-all ${platform.color} hover:text-white group`}
                  onClick={() => window.open(platform.url, '_blank')}
                >
                  <div className="text-3xl">{platform.icon}</div>
                  <div className="font-semibold">{platform.name}</div>
                  <div className="text-xs text-center opacity-80 group-hover:opacity-100">
                    {platform.description}
                  </div>
                  <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">
                    🎁 {platform.incentive}
                  </Badge>
                  <ExternalLink className="w-4 h-4 opacity-60 group-hover:opacity-100" />
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Internal Review Form */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle>Share Your Feedback</CardTitle>
            <CardDescription>
              Leave a review that will be displayed on our website after verification
            </CardDescription>
          </CardHeader>
          <CardContent>
            {showThankYou ? (
              <div className="text-center py-8">
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-2xl font-semibold text-green-700 mb-2">
                  Thank You!
                </h3>
                <p className="text-gray-600 mb-4">
                  Your review has been submitted and will be displayed after verification.
                </p>
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  Review pending approval
                </Badge>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Your Name
                    </label>
                    <Input
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      placeholder="Enter your name"
                      maxLength={50}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Rate Your Experience
                    </label>
                    {renderStars(selectedRating, true, 'w-8 h-8')}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tell Us About Your Experience
                  </label>
                  <Textarea
                    value={newReview}
                    onChange={(e) => setNewReview(e.target.value)}
                    placeholder="What did you love about your MyHibachi experience? How was the food, service, and overall experience?"
                    rows={4}
                    className="resize-none"
                    maxLength={500}
                  />
                  <div className="text-right text-xs text-gray-500 mt-1">
                    {newReview.length}/500 characters
                  </div>
                </div>

                <Button
                  onClick={handleInternalReviewSubmit}
                  disabled={selectedRating === 0 || newReview.trim() === '' || customerName.trim() === '' || isSubmitting}
                  className="w-full bg-orange-600 hover:bg-orange-700"
                >
                  {isSubmitting ? 'Submitting Review...' : 'Submit Review'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Existing Reviews */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            What Our Customers Say
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {reviews.map((review) => (
              <Card key={review.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold">{review.customerName}</h4>
                        {review.verified && (
                          <Badge variant="secondary" className="text-xs">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Verified
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mb-2">
                        {renderStars(review.rating)}
                        <span className="text-sm text-gray-500">
                          {formatDate(review.createdAt)}
                        </span>
                      </div>
                      {review.bookingId && (
                        <Badge variant="outline" className="text-xs mb-2">
                          <Calendar className="w-3 h-3 mr-1" />
                          {review.bookingId}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-4 leading-relaxed">
                    {review.comment}
                  </p>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Event: {formatDate(review.eventDate)}</span>
                    <button
                      onClick={() => handleHelpfulClick(review.id)}
                      className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                    >
                      <ThumbsUp className="w-3 h-3" />
                      {review.helpful}
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-12">
          <Card className="bg-gradient-to-r from-orange-500 to-red-500 text-white border-0">
            <CardContent className="pt-8 pb-8">
              <h3 className="text-2xl font-bold mb-4">
                Ready for Your Own Hibachi Experience?
              </h3>
              <p className="text-lg mb-6 opacity-90">
                Book your personalized hibachi experience today and create unforgettable memories
              </p>
              <Button
                variant="secondary"
                size="lg"
                className="bg-white text-orange-600 hover:bg-gray-100"
                onClick={() => window.location.href = '/BookUs'}
              >
                Book Your Event Now
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
