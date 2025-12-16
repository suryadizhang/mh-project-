'use client'

import React, { useEffect, useRef } from 'react'

import { homeData } from '@/data/home'
import styles from '@/styles/home/services.module.css'
import type { HomeService } from '@/types/data'

export function ServicesSection() {
  const sectionRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animateIn)
            // Animate individual service cards with stagger
            const cards = entry.target.querySelectorAll(`.${styles.serviceCard}`)
            cards.forEach((card, index) => {
              setTimeout(() => {
                card.classList.add(styles.cardAnimateIn)
              }, index * 150)
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
    <section className={styles.servicesSection} ref={sectionRef}>
      <div className="container">
        <div className="row">
          <div className="col-12 text-center">
            <h2 className={styles.sectionTitle}>{homeData.services.title}</h2>
            <p className={styles.sectionSubtitle}>
              Perfect for any occasion, bringing people together through exceptional food and
              entertainment
            </p>
          </div>
        </div>

        <div className="row">
          <div className="col-12">
            <div className={styles.servicesGrid}>
              {homeData.services.items.map((service: HomeService, index: number) => (
                <div key={index} className={styles.serviceCard}>
                  <div className={styles.cardContent}>
                    <div className={styles.serviceIcon}>{service.icon}</div>
                    <h3 className={styles.serviceTitle}>{service.title}</h3>
                    <p className={styles.serviceDescription}>{service.description}</p>
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
