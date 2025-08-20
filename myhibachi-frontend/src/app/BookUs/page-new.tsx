import './datepicker.css'
import { Metadata } from 'next'
import BookUsPageClient from './BookUsPageClient'

export const metadata: Metadata = {
  title: "Book Hibachi Chef Online | Schedule Private Catering | Bay Area & Sacramento",
  description: "Book your private hibachi chef experience online. Available dates and times for Bay Area, Sacramento, San Jose hibachi catering. Professional mobile chef service booking.",
  keywords: "book hibachi chef, schedule hibachi catering, hibachi booking online, bay area hibachi booking, sacramento hibachi schedule, private chef booking, mobile hibachi reservation",
  openGraph: {
    title: "Book Hibachi Chef Online | Schedule Private Catering",
    description: "Book your private hibachi chef experience online across Northern California.",
    type: 'website'
  }
}

export default function BookUsPage() {
  return <BookUsPageClient />
}
