'use client'

import { useEffect } from 'react'

export const useScrollAnimation = () => {
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in')
        }
      })
    }, observerOptions)

    // Observe all elements with animate-on-scroll class
    const animatedElements = document.querySelectorAll('.animate-on-scroll')
    animatedElements.forEach((el) => observer.observe(el))

    // Counter animation for statistics
    const animateCounters = () => {
      const counters = document.querySelectorAll('.stat-number')
      counters.forEach((counter) => {
        const target = counter.textContent?.replace(/\D/g, '') || '0'
        const targetNumber = parseInt(target)
        let current = 0
        const increment = targetNumber / 60 // 60 frames for smooth animation
        
        const updateCounter = () => {
          if (current < targetNumber) {
            current += increment
            const displayValue = Math.ceil(current)
            if (counter.textContent?.includes('★')) {
              counter.textContent = `${displayValue}★`
            } else if (counter.textContent?.includes('+')) {
              counter.textContent = `${displayValue}+`
            } else {
              counter.textContent = displayValue.toString()
            }
            requestAnimationFrame(updateCounter)
          } else {
            // Restore original text
            if (targetNumber === 5) counter.textContent = '5★'
            else if (targetNumber === 500) counter.textContent = '500+'
            else if (targetNumber === 50) counter.textContent = '50+'
          }
        }
        
        // Only animate if element is visible
        const rect = counter.getBoundingClientRect()
        if (rect.top < window.innerHeight && rect.bottom > 0) {
          updateCounter()
        }
      })
    }

    // Trigger counter animation when statistics section comes into view
    const statisticsSection = document.querySelector('.statistics-section')
    if (statisticsSection) {
      const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounters()
            statsObserver.unobserve(entry.target) // Only animate once
          }
        })
      }, { threshold: 0.5 })
      
      statsObserver.observe(statisticsSection)
    }

    // Cleanup
    return () => {
      observer.disconnect()
    }
  }, [])
}
