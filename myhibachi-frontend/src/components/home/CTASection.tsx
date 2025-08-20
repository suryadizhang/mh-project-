'use client';

import React, { useRef, useEffect } from 'react';
import Link from 'next/link';
import { homeData } from '@/data/home';
import styles from '@/styles/home/cta.module.css';

export function CTASection() {
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
    <section className={styles.ctaSection} ref={sectionRef}>
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8 text-center">
            <div className={styles.ctaContent}>
              <h2 className={styles.ctaTitle}>
                {homeData.cta.title}
              </h2>
              <p className={styles.ctaSubtitle}>
                {homeData.cta.subtitle}
              </p>

              <div className={styles.ctaButtons}>
                {homeData.cta.buttons.map((button, index) => (
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

              {/* Additional About Section */}
              <div className={styles.aboutSection}>
                <h3 className={styles.aboutTitle}>
                  {homeData.about.title}
                </h3>
                <p className={styles.aboutDescription}>
                  {homeData.about.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
