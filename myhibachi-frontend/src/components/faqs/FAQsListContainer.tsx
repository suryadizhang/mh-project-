'use client'

import type { FAQsListContainerProps } from './types'
import { FaqList } from '@/components/faq/FaqList'
import styles from './styles/FAQsListContainer.module.css'

export function FAQsListContainer({ faqs }: FAQsListContainerProps) {
  return (
    <div className={styles.faqsListContainer}>
      <FaqList items={faqs} />
    </div>
  )
}
