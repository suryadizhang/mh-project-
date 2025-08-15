import { NextRequest, NextResponse } from 'next/server'
import { cosineSearch } from '../../../lib/vectorSearch'

interface AssistantRequest {
  message: string
  page: string
}

interface AssistantResponse {
  answer: string
  citations: Array<{ title: string; href: string }>
  confidence: 'high' | 'medium' | 'low'
}

export async function POST(request: NextRequest): Promise<NextResponse<AssistantResponse | { error: string }>> {
  try {
    const { message, page }: AssistantRequest = await request.json()

    if (!message || !page) {
      return NextResponse.json({ error: 'Missing message or page' }, { status: 400 })
    }

    // Check for human contact requests first (before search)
    const contactKeywords = ['contact a person', 'talk to human', 'speak to someone', 'contact person', 'human support', 'live chat', 'real person', 'customer service', 'talk to a human', 'speak to a person']
    const isContactRequest = contactKeywords.some(keyword =>
      message.toLowerCase().includes(keyword)
    )

    if (isContactRequest) {
      return NextResponse.json({
        answer: "👋 I'd be happy to connect you with our team! You can chat with us on Facebook Messenger or Instagram DM. Would you like me to show you the options?",
        citations: [{ title: 'Contact Our Team', href: '/contact' }],
        confidence: 'high'
      })
    }

    // Search for relevant content
    const searchResults = await cosineSearch(message, page)

    if (searchResults.length === 0 || searchResults[0].score < 0.3) {
      return NextResponse.json({
        answer: "I don't have specific information about that in my knowledge base. For the most accurate answer, I'd recommend talking to our team directly!",
        citations: [{ title: 'Contact Us', href: '/contact' }],
        confidence: 'low'
      })
    }

    // Build answer from search results
    const topResult = searchResults[0]
    const confidence: 'high' | 'medium' | 'low' = topResult.score > 0.7 ? 'high' : topResult.score > 0.5 ? 'medium' : 'low'

    let answer = topResult.content
    let citations = [{ title: topResult.title, href: topResult.href }]

    // Add context-aware suggestions
    if (page === '/BookUs' && (message.toLowerCase().includes('book') || message.toLowerCase().includes('reserve'))) {
      answer += "\n\n📞 Ready to book? Use our booking form on this page or call (916) 740-8768!"
    } else if (page === '/menu' && message.toLowerCase().includes('price')) {
      citations.push({ title: 'Get a Quote', href: '/quote' })
    }

    // Handle specific common questions (after search results)
    if (message.toLowerCase().includes('travel') || message.toLowerCase().includes('distance')) {
      answer = "🚚 We serve the Bay Area & Sacramento region! First 30 miles are FREE, then $2/mile after that. We travel up to 150 miles total."
      citations = [{ title: 'Service Areas & Travel', href: '/faqs' }]
    }

    if (message.toLowerCase().includes('deposit')) {
      answer = "💳 We require a 50% deposit to secure your booking. The remaining balance is due on the day of service. No surprise fees!"
      citations = [{ title: 'Booking & Payment', href: '/faqs' }]
    }

    if (message.toLowerCase().includes('time') && message.toLowerCase().includes('slot')) {
      answer = "🕐 Our popular time slots are:\n• 12PM (Lunch)\n• 3PM (Afternoon) \n• 6PM (Dinner)\n• 9PM (Late dinner)\n\nWe need 48 hours advance notice for booking."
      citations = [{ title: 'Booking Times', href: '/BookUs' }]
    }

    return NextResponse.json({
      answer: answer.trim(),
      citations,
      confidence
    })

  } catch (error) {
    console.error('Assistant API error:', error)
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    )
  }
}
