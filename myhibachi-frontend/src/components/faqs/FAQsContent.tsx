'use client'

import type { FAQsContentProps } from './types'
import styles from './styles/FAQsContent.module.css'

export function FAQsContent({ children }: FAQsContentProps) {
  return (
    <section className={`${styles.faqsContent} faqs-content section-background`}>
      <div className={`${styles.container} container`}>
        {children}
      </div>
    </section>
  )
}
