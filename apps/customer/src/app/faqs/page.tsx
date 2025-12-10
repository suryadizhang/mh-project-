import '@/styles/base.css';
import '@/styles/faqs/faqs-base.css';
import '@/styles/faqs/faqs-items.css';

import { Metadata } from 'next';

import { FAQsPageContainer } from '@/components/faq';
import { getFaqsWithPricing } from '@/lib/faqDataProvider';

export const metadata: Metadata = {
  title: 'Hibachi Catering FAQs | Private Chef Questions | Bay Area & Sacramento',
  description:
    'Get answers to common hibachi catering questions. Pricing, booking, menu options, service areas for Bay Area, Sacramento, San Jose private hibachi chef services.',
  keywords:
    'hibachi catering faq, private chef questions, hibachi booking questions, bay area hibachi faq, sacramento hibachi questions, hibachi pricing faq, mobile chef questions',
  openGraph: {
    title: 'Hibachi Catering FAQs | Private Chef Questions',
    description:
      'Get answers to common hibachi catering questions about pricing, booking, and service areas.',
    type: 'website',
  },
};

export default async function FAQsPage() {
  // Fetch FAQs with dynamic pricing from database (server-side)
  const { faqs } = await getFaqsWithPricing();

  return <FAQsPageContainer faqs={faqs} />;
}
