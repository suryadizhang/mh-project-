'use client'

import React, { useEffect, useRef } from 'react'

import { homeData } from '@/data/home'
import styles from '@/styles/home/features.module.css'
import type { HomeFeature } from '@/types/data'

export function FeaturesGrid() {
  const sectionRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animateIn)
            // Animate individual cards with stagger
            const cards = entry.target.querySelectorAll(`.${styles.featureCard}`)
            cards.forEach((card, index) => {
              setTimeout(() => {
                card.classList.add(styles.cardAnimateIn)
              }, index * 100)
            })
          }
        })
      },
      { threshold: 0.1 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <section className={styles.featuresSection} ref={sectionRef}>
      <div className="container">
        <div className="row">
          <div className="col-12 text-center">
            <h2 className={styles.sectionTitle}>Why Choose My Hibachi?</h2>
            <p className={styles.sectionSubtitle}>
              Experience the difference of authentic Japanese hibachi dining at home
            </p>
          </div>
        </div>

        <div className="row">
          <div className="col-12">
            <div className={styles.featuresGrid}>
              {homeData.features.map((feature: HomeFeature, index: number) => (
                <div key={index} className={styles.featureCard}>
                  <div className={styles.cardContent}>
                    <div className={styles.featureIcon}>{feature.icon}</div>
                    <h3 className={styles.featureTitle}>{feature.title}</h3>
                    <p className={styles.featureDescription}>{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
