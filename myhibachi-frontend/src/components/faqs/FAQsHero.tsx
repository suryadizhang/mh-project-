'use client'

import type { FAQsHeroProps } from './types'
import styles from './styles/FAQsHero.module.css'

export function FAQsHero({ title, description }: FAQsHeroProps) {
  return (
    <section className={`${styles.faqsHero} faqs-hero page-hero-background`}>
      <div className={`${styles.container} container`}>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.description}>{description}</p>
      </div>
    </section>
  )
}
