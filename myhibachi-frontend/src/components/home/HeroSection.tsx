'use client';

import React, { useRef, useEffect } from 'react';
import Image from 'next/image';
import HeroVideo from '../HeroVideo';
import { homeData } from '@/data/home';
import styles from '@/styles/home/hero.module.css';

export function HeroSection() {
  const heroRef = useRef<HTMLElement>(null);

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

    if (heroRef.current) {
      observer.observe(heroRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section className={styles.aboutSection} ref={heroRef}>
      {/* Hero Video */}
      <div className={styles.heroMediaContainer}>
        <HeroVideo
          videoSrc={homeData.hero.videoSrc}
          title={homeData.hero.title}
          subtitle={homeData.hero.subtitle}
          showControls={false}
        />
      </div>

      {/* Hero Content */}
      <div className={`container ${styles.heroContent}`}>
        <div className="row justify-content-center">
          <div className="col-lg-8 text-center">
            <div className={styles.qualityBadge}>
              {homeData.hero.qualityBadge}
            </div>
          </div>
        </div>

        {/* Logo Section */}
        <div className={`row justify-content-center mt-5 ${styles.logoSection}`}>
          <div className="col-md-6 text-center">
            <div className={styles.logoContainer}>
              <Image
                src="/images/myhibachi-logo.png"
                alt="My Hibachi Logo"
                width={200}
                height={100}
                className={styles.logoImage}
                priority
              />
              <h2 className={styles.logoText}>
                My Hibachi
              </h2>
              <p className={styles.logoDescription}>
                Bringing the restaurant experience to your home
              </p>
            </div>
          </div>
        </div>

        {/* About Content */}
        <div className="row justify-content-center mt-5">
          <div className="col-lg-10">
            <div className={styles.aboutContent}>
              <p className={styles.aboutParagraph}>
                Welcome to My Hibachi, where we bring the authentic Japanese hibachi experience directly to your home. Our skilled chefs combine traditional cooking techniques with premium ingredients to create an unforgettable dining experience for you and your guests.
              </p>
              <p className={styles.aboutParagraph}>
                From the theatrical presentation to the perfectly grilled proteins and vegetables, every aspect of our service is designed to transport you to a traditional hibachi restaurant without leaving the comfort of your own space.
              </p>
              <p className={styles.aboutParagraph}>
                Whether you&apos;re celebrating a special occasion, hosting a dinner party, or simply want to enjoy restaurant-quality hibachi at home, My Hibachi delivers an experience that goes beyond just a meal – it&apos;s entertainment, cuisine, and memories all rolled into one spectacular event.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
