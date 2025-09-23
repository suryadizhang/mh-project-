'use client'

import { useRouter } from 'next/navigation'

interface FreeQuoteButtonProps {
  variant?: 'primary' | 'secondary' | 'floating'
  text?: string
  className?: string
}

export function FreeQuoteButton({
  variant = 'primary',
  text = 'Get Free Quote',
  className = ''
}: FreeQuoteButtonProps) {
  const router = useRouter()

  const buttonClasses = {
    primary: 'free-quote-btn free-quote-primary',
    secondary: 'free-quote-btn free-quote-secondary',
    floating: 'free-quote-btn free-quote-floating'
  }

  const handleClick = () => {
    router.push('/quote')
  }

  return (
    <button
      onClick={handleClick}
      className={`${buttonClasses[variant]} ${className}`}
      aria-label="Go to quote calculator page"
    >
      <span className="quote-icon">💰</span>
      {text}
    </button>
  )
}
