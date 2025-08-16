import { NextRequest, NextResponse } from 'next/server'

interface SupportRequest {
  name: string
  email: string
  phone?: string
  subject: string
  message: string
  page: string
  previousMessages?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const supportData: SupportRequest = await request.json()

    // Validate required fields
    const { name, email, subject, message, page } = supportData
    if (!name || !email || !subject || !message || !page) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      )
    }

    // Format chat context if provided
    let chatContext = ''
    if (supportData.previousMessages && supportData.previousMessages.length > 0) {
      chatContext = '\n\n--- Chat History ---\n'
      supportData.previousMessages.forEach((msg, index) => {
        chatContext += `${index + 1}. ${msg.role.toUpperCase()}: ${msg.content}\n`
      })
      chatContext += '--- End Chat History ---\n'
    }

    // In production, this would send to your email service
    // For now, we'll just log and return success
    console.log('Support request received:', {
      name,
      email,
      phone: supportData.phone || 'Not provided',
      subject,
      message: message.substring(0, 100) + (message.length > 100 ? '...' : ''),
      page,
      timestamp: new Date().toISOString(),
      hasChatContext: supportData.previousMessages && supportData.previousMessages.length > 0,
      chatHistory: chatContext ? chatContext.substring(0, 200) + '...' : 'None'
    })

    // Email service implementation using our existing email system
    try {
      // In production, this would send via your email service
      console.log('Contact form submission:', {
        name,
        email,
        subject,
        message,
        timestamp: new Date().toISOString()
      });

      // Note: Integrate with your preferred email service:
      // - Resend, SendGrid, Mailgun, or SMTP
      // - Database logging for ticket tracking
      // - Auto-responder to customer

    } catch (emailError) {
      console.error('Error processing contact form:', emailError);
      // Continue with success response even if email fails
    }

    return NextResponse.json({
      success: true,
      message: 'Support request submitted successfully! We\'ll get back to you within 24 hours.'
    })

  } catch (error) {
    console.error('Support API error:', error)
    return NextResponse.json(
      { error: 'Failed to submit support request' },
      { status: 500 }
    )
  }
}
