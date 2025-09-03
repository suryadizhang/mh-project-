'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Play, Pause, Volume2, VolumeX } from 'lucide-react'

interface HeroVideoProps {
  videoSrc?: string
  fallbackImage?: string
  title?: string
  subtitle?: string
  showControls?: boolean
}

export default function HeroVideo({
  videoSrc = '/videos/hero_video.mp4',
  fallbackImage = '/images/background.jpg',
  title = 'Authentic Hibachi Experience',
  subtitle = 'Bringing the restaurant experience to your home with skilled chefs, premium ingredients, and unforgettable dining entertainment.',
  showControls = false
}: HeroVideoProps) {
  const [isPlaying, setIsPlaying] = useState(true)
  const [isMuted, setIsMuted] = useState(true)
  const [videoLoaded, setVideoLoaded] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (video) {
      video.addEventListener('loadeddata', () => setVideoLoaded(true))
      video.addEventListener('error', () => setVideoLoaded(false))
    }
  }, [])

  const togglePlay = () => {
    const video = videoRef.current
    if (video) {
      if (isPlaying) {
        video.pause()
      } else {
        video.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (video) {
      video.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  return (
    <section className="relative home-hero overflow-hidden">
      {/* Background Video or Fallback Image */}
      {videoLoaded ? (
        <video
          ref={videoRef}
          autoPlay
          muted={isMuted}
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover z-0"
          poster={fallbackImage}
        >
          <source src={videoSrc} type="video/mp4" />
          {/* Fallback for browsers that don't support video */}
          <div
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${fallbackImage})` }}
          ></div>
        </video>
      ) : (
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6)), url(${fallbackImage})`
          }}
        ></div>
      )}

      {/* Dark overlay for better text readability */}
      <div className="absolute inset-0 bg-black bg-opacity-40 z-10"></div>

      {/* Video Controls (optional) */}
      {showControls && videoLoaded && (
        <div className="absolute top-4 right-4 z-30 flex gap-2">
          <button
            onClick={togglePlay}
            className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70 transition-all"
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
          <button
            onClick={toggleMute}
            className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70 transition-all"
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>
        </div>
      )}

      {/* Content */}
      <div className="relative z-20 max-w-4xl mx-auto px-4 text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6 text-white drop-shadow-lg fade-in">
          {title}
        </h1>
        <p className="text-lg md:text-xl mb-8 text-white drop-shadow-md max-w-3xl mx-auto slide-in-left">
          {subtitle}
        </p>
        <div className="space-x-4 zoom-in">
          <Button asChild size="lg" className="shadow-strong">
            <Link href="/contact">Book Your Event</Link>
          </Button>
          <Button
            variant="outline"
            asChild
            size="lg"
            className="bg-black bg-opacity-30 backdrop-blur-sm border-white text-white hover:bg-white hover:text-gray-900"
          >
            <Link href="/menu">View Menu</Link>
          </Button>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20">
        <div className="w-6 h-10 border-2 border-white border-opacity-50 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-white bg-opacity-70 rounded-full mt-2 animate-bounce"></div>
        </div>
      </div>
    </section>
  )
}
