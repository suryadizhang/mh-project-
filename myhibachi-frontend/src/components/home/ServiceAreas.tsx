'use client';

import React, { useRef, useEffect } from 'react';
import Link from 'next/link';
import { homeData } from '@/data/home';
import styles from '@/styles/home/service-areas.module.css';

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
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section className={styles.serviceAreasSection} ref={sectionRef}>
      <div className="container">
        <div className="row">
          <div className="col-12 text-center">
            <h2 className={styles.sectionTitle}>
              {homeData.serviceAreas.title}
            </h2>
            <p className={styles.sectionSubtitle}>
              {homeData.serviceAreas.subtitle}
            </p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="row justify-content-center mb-5">
          <div className="col-md-8 text-center">
            <div className={styles.ctaButtons}>
              {homeData.serviceAreas.ctaButtons.map((button, index) => (
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
        <div className="row">
          {/* Primary Areas */}
          <div className="col-lg-6 mb-4">
            <div className={styles.areaCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.areaTitle}>
                  {homeData.serviceAreas.areas.primary.title}
                </h3>
                <p className={styles.areaSubtitle}>
                  {homeData.serviceAreas.areas.primary.subtitle}
                </p>
              </div>
              <div className={styles.locationsList}>
                {homeData.serviceAreas.areas.primary.locations.map((location, index) => (
                  <div key={index} className={styles.locationItem}>
                    {location}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Extended Areas */}
          <div className="col-lg-6 mb-4">
            <div className={styles.areaCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.areaTitle}>
                  {homeData.serviceAreas.areas.extended.title}
                </h3>
                <p className={styles.areaSubtitle}>
                  {homeData.serviceAreas.areas.extended.subtitle}
                </p>
              </div>
              <div className={styles.locationsList}>
                {homeData.serviceAreas.areas.extended.locations.map((location, index) => (
                  <div key={index} className={styles.locationItem}>
                    {location}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
