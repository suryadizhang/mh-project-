'use client';

import Link from 'next/link';
import React, { useEffect, useRef } from 'react';

import { homeData } from '@/data/home';
import styles from '@/styles/home/service-areas.module.css';
import type { CTAButton } from '@/types/data';

export function ServiceAreas() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.animateIn);
          }
        });
      },
      { threshold: 0.1 },
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section className={styles.serviceAreasSection} ref={sectionRef}>
      <div className="container mx-auto px-4">
        <div className="mb-6">
          <div className="text-center">
            <h2 className={styles.sectionTitle}>{homeData.serviceAreas.title}</h2>
            <p className={styles.sectionSubtitle}>{homeData.serviceAreas.subtitle}</p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="mb-8 flex justify-center">
          <div className="w-full text-center md:w-2/3">
            <div className={styles.ctaButtons}>
              {homeData.serviceAreas.ctaButtons.map((button: CTAButton, index: number) => (
                <Link
                  key={index}
                  href={button.href}
                  className={`${styles.ctaButton} ${
                    button.primary ? styles.primaryButton : styles.secondaryButton
                  }`}
                >
                  {button.text}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Service Areas Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Primary Areas */}
          <div className="mb-4">
            <div className={styles.areaCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.areaTitle}>{homeData.serviceAreas.areas.primary.title}</h3>
                <p className={styles.areaSubtitle}>
                  {homeData.serviceAreas.areas.primary.subtitle}
                </p>
              </div>
              <div className={styles.locationsList}>
                {homeData.serviceAreas.areas.primary.locations.map(
                  (location: string, index: number) => (
                    <div key={index} className={styles.locationItem}>
                      {location}
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>

          {/* Extended Areas */}
          <div className="mb-4">
            <div className={styles.areaCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.areaTitle}>{homeData.serviceAreas.areas.extended.title}</h3>
                <p className={styles.areaSubtitle}>
                  {homeData.serviceAreas.areas.extended.subtitle}
                </p>
              </div>
              <div className={styles.locationsList}>
                {homeData.serviceAreas.areas.extended.locations.map(
                  (location: string, index: number) => (
                    <div key={index} className={styles.locationItem}>
                      {location}
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
