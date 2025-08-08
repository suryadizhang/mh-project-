import { NextRequest, NextResponse } from 'next/server'
import { emailService } from '@/lib/email-service'
import { emailScheduler } from '@/lib/email-scheduler'

// Email management and monitoring endpoints
// GET /api/v1/bookings/emails - Get email logs and statistics
// POST /api/v1/bookings/emails - Admin actions (resend, cancel, trigger)

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const action = url.searchParams.get('action')
    const bookingId = url.searchParams.get('bookingId')
    const page = parseInt(url.searchParams.get('page') || '1')
    const limit = parseInt(url.searchParams.get('limit') || '50')

    switch (action) {
      case 'history':
        if (!bookingId) {
          return NextResponse.json(
            { detail: 'bookingId parameter required for history action' },
            { status: 400 }
          )
        }
        
        const history = emailService.getEmailHistory(bookingId)
        return NextResponse.json({
          bookingId,
          emails: history,
          total: history.length
        })

      case 'scheduled':
        const scheduled = emailScheduler.getScheduledEmails()
        const status = url.searchParams.get('status') as 'pending' | 'sent' | 'failed' | 'cancelled' | undefined
        const filtered = status ? scheduled.filter(email => email.status === status) : scheduled
        
        return NextResponse.json({
          scheduledEmails: filtered,
          total: filtered.length,
          statistics: emailScheduler.getSchedulerStats()
        })

      case 'stats':
        const schedulerStats = emailScheduler.getSchedulerStats()
        const { logs: allLogs, total: totalLogs } = emailService.getAllEmailLogs(1, 1000)
        
        const emailStats = {
          sent: allLogs.filter(log => log.status === 'sent').length,
          failed: allLogs.filter(log => log.status === 'failed').length,
          total: totalLogs,
          byType: {
            confirmation: allLogs.filter(log => log.emailType === 'confirmation').length,
            review_request: allLogs.filter(log => log.emailType === 'review_request').length,
            upsell: allLogs.filter(log => log.emailType === 'upsell').length
          }
        }

        return NextResponse.json({
          emailStats,
          schedulerStats,
          status: 'EMAIL_SYSTEM_OPERATIONAL'
        })

      default:
        // Default: Get all email logs with pagination
        const { logs, total } = emailService.getAllEmailLogs(page, limit)
        return NextResponse.json({
          emails: logs,
          pagination: {
            page,
            limit,
            total,
            totalPages: Math.ceil(total / limit)
          }
        })
    }

  } catch (error) {
    console.error('[EMAIL API ERROR]', error)
    return NextResponse.json(
      { detail: 'Failed to retrieve email information' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, bookingId, emailType, emailId, bookingData } = body

    if (!action) {
      return NextResponse.json(
        { detail: 'Action parameter required' },
        { status: 400 }
      )
    }

    switch (action) {
      case 'resend':
        if (!bookingId || !emailType || !bookingData) {
          return NextResponse.json(
            { detail: 'bookingId, emailType, and bookingData required for resend action' },
            { status: 400 }
          )
        }

        const validEmailTypes = ['confirmation', 'review_request', 'upsell']
        if (!validEmailTypes.includes(emailType)) {
          return NextResponse.json(
            { detail: `Invalid email type. Must be one of: ${validEmailTypes.join(', ')}` },
            { status: 400 }
          )
        }

        console.log(`[EMAIL ADMIN] Manual resend requested: ${emailType} for booking ${bookingId}`)
        
        const resendSuccess = await emailService.resendEmail(bookingId, emailType, bookingData)
        
        return NextResponse.json({
          success: resendSuccess,
          message: resendSuccess 
            ? `${emailType} email resent successfully` 
            : `Failed to resend ${emailType} email`,
          bookingId,
          emailType,
          timestamp: new Date().toISOString()
        })

      case 'cancel_scheduled':
        if (!emailId) {
          return NextResponse.json(
            { detail: 'emailId required for cancel_scheduled action' },
            { status: 400 }
          )
        }

        const cancelSuccess = emailScheduler.cancelScheduledEmail(emailId)
        
        return NextResponse.json({
          success: cancelSuccess,
          message: cancelSuccess 
            ? 'Scheduled email cancelled successfully' 
            : 'Failed to cancel scheduled email (not found or already processed)',
          emailId,
          timestamp: new Date().toISOString()
        })

      case 'trigger_scheduled':
        if (!emailId) {
          return NextResponse.json(
            { detail: 'emailId required for trigger_scheduled action' },
            { status: 400 }
          )
        }

        console.log(`[EMAIL ADMIN] Manual trigger requested for scheduled email ${emailId}`)
        
        const triggerSuccess = await emailScheduler.triggerScheduledEmail(emailId)
        
        return NextResponse.json({
          success: triggerSuccess,
          message: triggerSuccess 
            ? 'Scheduled email sent successfully' 
            : 'Failed to send scheduled email',
          emailId,
          timestamp: new Date().toISOString()
        })

      case 'start_scheduler':
        emailScheduler.startScheduler()
        
        return NextResponse.json({
          success: true,
          message: 'Email scheduler started',
          timestamp: new Date().toISOString()
        })

      case 'stop_scheduler':
        emailScheduler.stopScheduler()
        
        return NextResponse.json({
          success: true,
          message: 'Email scheduler stopped',
          timestamp: new Date().toISOString()
        })

      default:
        return NextResponse.json(
          { 
            detail: 'Invalid action. Supported actions: resend, cancel_scheduled, trigger_scheduled, start_scheduler, stop_scheduler' 
          },
          { status: 400 }
        )
    }

  } catch (error) {
    console.error('[EMAIL API ERROR]', error)
    return NextResponse.json(
      { detail: 'Email operation failed' },
      { status: 500 }
    )
  }
}

// Helper endpoint to test email templates (development only)
export async function PUT(request: NextRequest) {
  try {
    if (process.env.NODE_ENV === 'production') {
      return NextResponse.json(
        { detail: 'Template testing not available in production' },
        { status: 403 }
      )
    }

    const body = await request.json()
    const { emailType, testData } = body

    if (!emailType || !testData) {
      return NextResponse.json(
        { detail: 'emailType and testData required for template testing' },
        { status: 400 }
      )
    }

    // Test email data
    const mockBookingData = {
      customerName: testData.customerName || 'John Doe',
      customerEmail: testData.customerEmail || 'test@example.com',
      bookingId: testData.bookingId || 'test-123',
      eventDate: testData.eventDate || '2025-08-15',
      eventTime: testData.eventTime || '6PM',
      guestCount: testData.guestCount || 4,
      venueAddress: {
        street: testData.venueAddress?.street || '123 Test Street',
        city: testData.venueAddress?.city || 'Test City',
        state: testData.venueAddress?.state || 'CA',
        zipcode: testData.venueAddress?.zipcode || '90210'
      },
      confirmationNumber: `MH-TEST-${Date.now().toString().slice(-6)}`
    }

    let success = false
    let message = ''

    switch (emailType) {
      case 'confirmation':
        success = await emailService.sendBookingConfirmation(mockBookingData)
        message = success ? 'Test confirmation email sent' : 'Failed to send test confirmation email'
        break

      case 'review_request':
        success = await emailService.sendReviewRequest(mockBookingData)
        message = success ? 'Test review request email sent' : 'Failed to send test review request email'
        break

      case 'upsell':
        success = await emailService.sendUpsellEmail(mockBookingData)
        message = success ? 'Test upsell email sent' : 'Failed to send test upsell email'
        break

      default:
        return NextResponse.json(
          { detail: 'Invalid email type for testing. Use: confirmation, review_request, or upsell' },
          { status: 400 }
        )
    }

    return NextResponse.json({
      success,
      message,
      emailType,
      testData: mockBookingData,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('[EMAIL TEMPLATE TEST ERROR]', error)
    return NextResponse.json(
      { detail: 'Template testing failed' },
      { status: 500 }
    )
  }
}
