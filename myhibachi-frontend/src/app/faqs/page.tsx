'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function FAQsPage() {
  const [openFAQ, setOpenFAQ] = useState<number | null>(null)

  const faqs = [
    {
      question: 'What is included in your hibachi catering service?',
      answer: 'Our service includes a professional hibachi chef, all cooking equipment, fresh ingredients, setup and cleanup, and an entertaining cooking performance for your guests.'
    },
    {
      question: 'How many people can you serve?',
      answer: 'We can accommodate groups from 10 to 100+ guests. Our chefs can work with multiple grills for larger events.'
    },
    {
      question: 'How far in advance should I book?',
      answer: 'We recommend booking at least 2-3 weeks in advance, especially for weekend events. However, we may be able to accommodate shorter notice requests based on availability.'
    },
    {
      question: 'Do you provide tables and seating?',
      answer: 'We provide the hibachi grills and cooking equipment. Tables, chairs, and other furniture can be arranged upon request for an additional fee.'
    },
    {
      question: 'What areas do you serve?',
      answer: 'We currently serve the Greater Metro Area. Contact us to confirm if we can reach your location.'
    },
    {
      question: 'Can you accommodate dietary restrictions?',
      answer: 'Absolutely! We can accommodate vegetarian, gluten-free, and other dietary needs. Please let us know about any restrictions when booking.'
    },
    {
      question: 'What is your cancellation policy?',
      answer: 'We require 48 hours notice for cancellations. Cancellations within 48 hours may be subject to a cancellation fee.'
    },
    {
      question: 'Do you require a deposit?',
      answer: 'Yes, we require a 50% deposit to secure your booking, with the remaining balance due on the day of service.'
    }
  ]

  const toggleFAQ = (index: number) => {
    setOpenFAQ(openFAQ === index ? null : index)
  }

  return (
    <div className="py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h1>
          <p className="text-gray-600">Everything you need to know about our hibachi catering service</p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
              >
                <span className="font-semibold text-gray-900">{faq.question}</span>
                {openFAQ === index ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
              {openFAQ === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-700">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Still have questions?</h2>
          <p className="text-gray-600 mb-6">
            Contact us and we&apos;ll be happy to help you plan your perfect hibachi experience.
          </p>
          <a
            href="/contact"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Contact Us
          </a>
        </div>
      </div>
    </div>
  )
}
