import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Log the contact form submission for now
    console.log('Contact Form Submission:', {
      name: body.name,
      email: body.email,
      phone: body.phone,
      eventType: body.eventType,
      eventDate: body.eventDate,
      guestCount: body.guestCount,
      location: body.location,
      message: body.message,
      timestamp: new Date().toISOString()
    })

    // In a real application, you would:
    // 1. Validate the data with a schema
    // 2. Save to a database
    // 3. Send an email notification
    // 4. Maybe integrate with a CRM
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return NextResponse.json({
      success: true,
      message: 'Thank you for your inquiry! We will contact you within 1-2 hours.',
      data: {
        submittedAt: new Date().toISOString(),
        confirmationId: `MH-${Date.now()}`
      }
    })
    
  } catch (error) {
    console.error('Contact form error:', error)
    
    return NextResponse.json({
      success: false,
      message: 'There was an error processing your request. Please try again.',
      error: process.env.NODE_ENV === 'development' ? error : undefined
    }, { status: 500 })
  }
}
