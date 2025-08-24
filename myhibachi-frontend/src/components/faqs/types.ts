import type { FaqItem } from '@/data/faqsData'

export interface FAQsPageProps {
  faqs: FaqItem[]
}

export interface FAQsHeroProps {
  title: string
  description: string
}

export interface FAQsContentProps {
  children: React.ReactNode
}

export interface FAQsListContainerProps {
  faqs: FaqItem[]
}

export interface JSONLDSchemaProps {
  faqs: FaqItem[]
  url?: string
  name?: string
}
