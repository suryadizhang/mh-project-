'use client';

import Image from 'next/image';
import React, { useEffect, useRef } from 'react';

import { homeData } from '@/data/home';
import styles from '@/styles/home/hero.module.css';

import HeroVideo from '../HeroVideo';

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
      { threshold: 0.1 },
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
      <div className={`container mx-auto px-4 ${styles.heroContent}`}>
        <div className="flex justify-center">
          <div className="w-full text-center lg:w-2/3">
            <div className={styles.qualityBadge}>{homeData.hero.qualityBadge}</div>
          </div>
        </div>

        {/* Logo Section */}
        <div className={`mt-8 flex justify-center ${styles.logoSection}`}>
          <div className="w-full text-center md:w-1/2">
            <div className={styles.logoContainer}>
              <Image
                src="/images/myhibachi-logo-small.webp"
                alt="My Hibachi Logo"
                width={200}
                height={100}
                className={styles.logoImage}
                priority
              />
              <h2 className={styles.logoText}>My Hibachi</h2>
              <p className={styles.logoDescription}>
                Bringing the restaurant experience to your home
              </p>
            </div>
          </div>
        </div>

        {/* About Content */}
        <div className="mt-8 flex justify-center">
          <div className="w-full lg:w-5/6">
            <div className={styles.aboutContent}>
              <p className={styles.aboutParagraph}>
                Welcome to My Hibachi, where we bring the authentic Japanese hibachi experience
                directly to your home. Our skilled chefs combine traditional cooking techniques with
                premium ingredients to create an unforgettable dining experience for you and your
                guests.
              </p>
              <p className={styles.aboutParagraph}>
                From the theatrical presentation to the perfectly grilled proteins and vegetables,
                every aspect of our service is designed to transport you to a traditional hibachi
                restaurant without leaving the comfort of your own space.
              </p>
              <p className={styles.aboutParagraph}>
                Whether you&apos;re celebrating a special occasion, hosting a dinner party, or
                simply want to enjoy restaurant-quality hibachi at home, My Hibachi delivers an
                experience that goes beyond just a meal – it&apos;s entertainment, cuisine, and
                memories all rolled into one spectacular event.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
