'use client';

import Image from 'next/image';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';

import { blogPosts, type BlogPost } from '@/data/blogPosts';

interface FeaturedPostsCarouselProps {
  maxPosts?: number;
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showDots?: boolean;
  showArrows?: boolean;
  height?: 'sm' | 'md' | 'lg' | 'xl';
}

const FeaturedPostsCarousel: React.FC<FeaturedPostsCarouselProps> = ({
  maxPosts = 5,
  autoPlay = true,
  autoPlayInterval = 5000,
  showDots = true,
  showArrows = true,
  height = 'lg',
}) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  // Get featured posts or top posts
  const featuredPosts = blogPosts.filter((post: BlogPost) => post.featured).slice(0, maxPosts);

  // If not enough featured posts, get top posts by ID (simulating popularity)
  const displayPosts = featuredPosts.length >= 3 ? featuredPosts : blogPosts.slice(0, maxPosts);

  // Auto-play functionality
  useEffect(() => {
    if (!autoPlay || isHovered || displayPosts.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % displayPosts.length);
    }, autoPlayInterval);

    return () => clearInterval(interval);
  }, [autoPlay, autoPlayInterval, isHovered, displayPosts.length]);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + displayPosts.length) % displayPosts.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % displayPosts.length);
  };

  const getHeightClass = () => {
    switch (height) {
      case 'sm':
        return 'h-64';
      case 'md':
        return 'h-80';
      case 'lg':
        return 'h-96';
      case 'xl':
        return 'h-[32rem]';
    }
  };

  if (displayPosts.length === 0) {
    return null;
  }

  return (
    <div className="relative w-full overflow-hidden rounded-xl bg-gray-100 shadow-lg">
      {/* Carousel Container */}
      <div
        className={`relative ${getHeightClass()} overflow-hidden`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Slides */}
        {displayPosts.map((post, index) => (
          <div
            key={post.id}
            className={`absolute inset-0 transition-opacity duration-700 ease-in-out ${
              index === currentSlide ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {/* Background Image/Gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-orange-600 via-red-600 to-purple-700">
              {post.image && (
                <Image
                  src={post.image}
                  alt={post.imageAlt || post.title}
                  fill
                  className="object-cover mix-blend-overlay"
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                />
              )}
              {/* Overlay */}
              <div className="bg-opacity-40 absolute inset-0 bg-black"></div>
            </div>

            {/* Content */}
            <div className="relative z-10 flex h-full items-center justify-center p-8">
              <div className="mx-auto max-w-4xl text-center text-white">
                {/* Category Badge */}
                <div className="bg-opacity-20 mb-4 inline-flex items-center rounded-full bg-white px-3 py-1 text-sm font-medium text-white backdrop-blur-sm">
                  <span className="mr-2">🎯</span>
                  {post.category}
                </div>

                {/* Title */}
                <h2 className="mb-6 text-3xl leading-tight font-bold md:text-4xl lg:text-5xl">
                  {post.title}
                </h2>

                {/* Excerpt */}
                <p className="mx-auto mb-8 line-clamp-3 max-w-3xl text-lg text-gray-100 md:text-xl">
                  {post.excerpt}
                </p>

                {/* Meta Info */}
                <div className="mb-8 flex items-center justify-center space-x-6 text-sm text-gray-200">
                  <div className="flex items-center space-x-2">
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>{post.author}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>{post.date}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>{post.readTime}</span>
                  </div>
                </div>

                {/* CTA Button */}
                <Link
                  href={`/blog/${post.slug}`}
                  className="inline-flex transform items-center rounded-full bg-white px-8 py-3 font-semibold text-gray-900 shadow-lg transition-colors duration-200 hover:scale-105 hover:bg-gray-100 hover:shadow-xl"
                >
                  Read Full Article
                  <svg className="ml-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Featured Badge */}
            {post.featured && (
              <div className="absolute top-4 left-4 z-20">
                <div className="flex items-center rounded-full bg-yellow-400 px-3 py-1 text-sm font-bold text-yellow-900">
                  <span className="mr-1">⭐</span>
                  Featured
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Navigation Arrows */}
        {showArrows && displayPosts.length > 1 && (
          <>
            <button
              onClick={goToPrevious}
              className="bg-opacity-20 hover:bg-opacity-30 absolute top-1/2 left-4 z-20 -translate-y-1/2 transform rounded-full bg-white p-3 text-white backdrop-blur-sm transition-all duration-200 hover:scale-110"
              aria-label="Previous slide"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            <button
              onClick={goToNext}
              className="bg-opacity-20 hover:bg-opacity-30 absolute top-1/2 right-4 z-20 -translate-y-1/2 transform rounded-full bg-white p-3 text-white backdrop-blur-sm transition-all duration-200 hover:scale-110"
              aria-label="Next slide"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </>
        )}
      </div>

      {/* Dots Indicator */}
      {showDots && displayPosts.length > 1 && (
        <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2 transform">
          <div className="flex space-x-2">
            {displayPosts.map((_: BlogPost, index: number) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`h-3 w-3 rounded-full transition-all duration-200 ${
                  index === currentSlide
                    ? 'scale-125 bg-white'
                    : 'bg-opacity-50 hover:bg-opacity-75 bg-white'
                }`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {autoPlay && !isHovered && displayPosts.length > 1 && (
        <div className="bg-opacity-20 absolute bottom-0 left-0 h-1 w-full bg-white">
          <div
            className="h-full bg-white transition-all duration-100 ease-linear"
            style={{
              width: `${((currentSlide + 1) / displayPosts.length) * 100}%`,
            }}
          />
        </div>
      )}

      {/* Mini Thumbnails */}
      <div className="absolute right-4 bottom-4 z-20 hidden space-x-2 lg:flex">
        {displayPosts.map((post, index) => (
          <button
            key={post.id}
            onClick={() => goToSlide(index)}
            className={`bg-opacity-20 h-12 w-16 overflow-hidden rounded border-2 bg-white backdrop-blur-sm transition-all duration-200 ${
              index === currentSlide
                ? 'scale-110 border-white'
                : 'border-transparent hover:scale-105 hover:border-white'
            }`}
            title={post.title}
          >
            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-orange-400 to-red-500 text-xs font-bold text-white">
              {index + 1}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default FeaturedPostsCarousel;
