'use client'

import React, { useEffect, useRef } from 'react'

import { homeData } from '@/data/home'
import styles from '@/styles/home/experience.module.css'

export function ExperienceSection() {
  const sectionRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animateIn)
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
    <section className={styles.experienceSection} ref={sectionRef}>
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-10">
            <div className={styles.experienceGrid}>
              {/* Chef Experience */}
              <div className={styles.experienceCard}>
                <div className={styles.cardContent}>
                  <h3 className={styles.cardTitle}>{homeData.experience.chef.title}</h3>
                  <p className={styles.cardDescription}>{homeData.experience.chef.content}</p>
                </div>
              </div>

              {/* Entertainment Experience */}
              <div className={styles.experienceCard}>
                <div className={styles.cardContent}>
                  <h3 className={styles.cardTitle}>{homeData.experience.entertainment.title}</h3>
                  <p className={styles.cardDescription}>
                    {homeData.experience.entertainment.content}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
