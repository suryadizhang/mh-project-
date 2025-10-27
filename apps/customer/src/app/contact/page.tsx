import '@/styles/contact.css'
import '@/styles/base.css'

import { Metadata } from 'next'

import Assistant from '@/components/chat/Assistant'
import MetaMessenger from '@/components/chat/MetaMessenger'
import ConsentBar from '@/components/consent/ConsentBar'

import ContactPageClient from './ContactPageClient'

// Force dynamic rendering to prevent conflicts with contact.html redirect page
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Book Private Hibachi Chef | Bay Area & Sacramento Catering Contact',
  description:
    'Contact MyHibachi for premium private hibachi chef services. Serving San Francisco, San Jose, Oakland, Sacramento. Professional hibachi catering for all events. Get your free quote!',
  keywords:
    'book hibachi chef, contact hibachi catering, bay area private chef, sacramento hibachi service, san jose hibachi catering, hibachi chef booking, private hibachi contact',
  openGraph: {
    title: 'Book Private Hibachi Chef | Bay Area & Sacramento Catering',
    description:
      'Contact MyHibachi for premium private hibachi chef services across Northern California.',
    type: 'website'
  }
}

export default function ContactPage() {
  return (
    <>
      <ContactPageClient />
      <Assistant page="/contact" />
      <ConsentBar />
      <MetaMessenger />
    </>
  )
}
