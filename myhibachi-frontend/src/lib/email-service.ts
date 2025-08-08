import { Resend } from 'resend'

// Lazy initialization of Resend to prevent build errors
let resend: Resend | null = null
function getResendClient(): Resend {
  if (!resend) {
    const apiKey = process.env.RESEND_API_KEY || 'fallback_key_for_build'
    resend = new Resend(apiKey)
  }
  return resend
}

// Email templates and automation system
interface EmailTemplate {
  subject: string
  html: string
  text: string
}

interface BookingEmailData {
  customerName: string
  customerEmail: string
  bookingId: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: {
    street: string
    city: string
    state: string
    zipcode: string
  }
  confirmationNumber: string
}

// Email sending history for audit and rate limiting
interface EmailLog {
  bookingId: string
  emailType: 'confirmation' | 'review_request' | 'upsell'
  recipientEmail: string
  sentAt: string
  status: 'sent' | 'failed' | 'queued'
  resendMessageId?: string
  error?: string
}

// In-memory email log storage (replace with database in production)
const emailLogs: EmailLog[] = []

// Rate limiting for email sending
const emailRateLimit = new Map<string, { count: number; resetTime: number }>()
const EMAIL_RATE_LIMIT = 5 // Max 5 emails per hour per recipient
const EMAIL_RATE_WINDOW = 3600000 // 1 hour

class MyHibachiEmailService {
  
  // Check email rate limiting
  private checkEmailRateLimit(email: string): boolean {
    const now = Date.now()
    const userRecord = emailRateLimit.get(email)
    
    if (!userRecord || now > userRecord.resetTime) {
      emailRateLimit.set(email, { count: 1, resetTime: now + EMAIL_RATE_WINDOW })
      return true
    }
    
    if (userRecord.count >= EMAIL_RATE_LIMIT) {
      return false
    }
    
    userRecord.count++
    return true
  }

  // Generate calendar links
  private generateCalendarLinks(bookingData: BookingEmailData): { google: string; apple: string; ics: string } {
    const { customerName, eventDate, eventTime, venueAddress } = bookingData
    
    // Convert event time to 24-hour format and create full datetime
    const timeMap: { [key: string]: string } = {
      '12PM': '12:00',
      '3PM': '15:00', 
      '6PM': '18:00',
      '9PM': '21:00'
    }
    
    const eventStartTime = timeMap[eventTime]
    const startDate = `${eventDate}T${eventStartTime}:00`
    const endDate = `${eventDate}T${parseInt(eventStartTime.split(':')[0]) + 2}:00:00` // 2-hour duration
    
    const title = `MyHibachi Experience - ${customerName}`
    const description = `Private hibachi cooking experience with MyHibachi. Enjoy fresh, premium ingredients prepared right at your venue!`
    const location = `${venueAddress.street}, ${venueAddress.city}, ${venueAddress.state} ${venueAddress.zipcode}`
    
    // Google Calendar link
    const googleStartTime = startDate.replace(/[-:]/g, '').replace('T', 'T')
    const googleEndTime = endDate.replace(/[-:]/g, '').replace('T', 'T')
    const googleUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${googleStartTime}/${googleEndTime}&details=${encodeURIComponent(description)}&location=${encodeURIComponent(location)}`
    
    // Apple Calendar (webcal) link - simplified
    const appleUrl = `data:text/calendar;charset=utf8,BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
URL:https://myhibachi.com
DTSTART:${googleStartTime}
DTEND:${googleEndTime}
SUMMARY:${title}
DESCRIPTION:${description}
LOCATION:${location}
END:VEVENT
END:VCALENDAR`
    
    // ICS file content
    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyHibachi//Booking System//EN
BEGIN:VEVENT
UID:${bookingData.bookingId}@myhibachi.com
DTSTART:${googleStartTime}
DTEND:${googleEndTime}
SUMMARY:${title}
DESCRIPTION:${description}
LOCATION:${location}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`
    
    return {
      google: googleUrl,
      apple: appleUrl,
      ics: icsContent
    }
  }

  // Generate booking confirmation email template
  private generateConfirmationEmail(bookingData: BookingEmailData): EmailTemplate {
    const { customerName, eventDate, eventTime, guestCount, venueAddress, confirmationNumber } = bookingData
    const calendarLinks = this.generateCalendarLinks(bookingData)
    
    // Format date for display
    const displayDate = new Date(eventDate).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
    
    const subject = "🎉 Your MyHibachi Experience is Confirmed!"
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #ff6b35, #f7931e); color: white; padding: 40px 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .header p { margin: 10px 0 0; opacity: 0.9; font-size: 16px; }
        .content { padding: 40px 30px; }
        .booking-details { background: #f8f9fa; border-radius: 8px; padding: 25px; margin: 25px 0; }
        .booking-details h3 { margin: 0 0 20px; color: #ff6b35; font-size: 20px; }
        .detail-row { display: flex; justify-content: space-between; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e9ecef; }
        .detail-label { font-weight: 600; color: #495057; }
        .detail-value { color: #6c757d; text-align: right; }
        .cta-section { text-align: center; margin: 35px 0; }
        .cta-button { display: inline-block; background: #ff6b35; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 0 10px 10px; transition: background 0.3s; }
        .cta-button:hover { background: #e5552a; }
        .cta-button.secondary { background: #6c757d; }
        .cta-button.secondary:hover { background: #545b62; }
        .footer { background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px; }
        .confirmation-number { background: #e7f3ff; border: 2px dashed #007bff; border-radius: 8px; padding: 15px; text-align: center; margin: 20px 0; }
        .confirmation-number strong { font-size: 18px; color: #007bff; }
        @media (max-width: 600px) {
            .container { margin: 10px; }
            .content, .header { padding: 25px 20px; }
            .cta-button { display: block; margin: 10px 0; }
            .detail-row { flex-direction: column; text-align: left; }
            .detail-value { text-align: left; margin-top: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Booking Confirmed!</h1>
            <p>Get ready for an amazing hibachi experience</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>${customerName}</strong>,</p>
            
            <p>Great news! Your MyHibachi experience has been confirmed. Our talented chef will bring the authentic hibachi experience right to your location with fresh, premium ingredients and exciting table-side cooking.</p>
            
            <div class="confirmation-number">
                <p style="margin: 0;">Your confirmation number:</p>
                <strong>${confirmationNumber}</strong>
            </div>
            
            <div class="booking-details">
                <h3>📅 Your Booking Details</h3>
                <div class="detail-row">
                    <span class="detail-label">Date & Time:</span>
                    <span class="detail-value">${displayDate} at ${eventTime}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Guests:</span>
                    <span class="detail-value">${guestCount} people</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span class="detail-value">${venueAddress.street}<br>${venueAddress.city}, ${venueAddress.state} ${venueAddress.zipcode}</span>
                </div>
            </div>
            
            <div class="cta-section">
                <p><strong>Add this event to your calendar:</strong></p>
                <a href="${calendarLinks.google}" class="cta-button" target="_blank">📅 Add to Google Calendar</a>
                <a href="${calendarLinks.apple}" class="cta-button secondary" download="hibachi-booking.ics">🍎 Add to Apple Calendar</a>
            </div>
            
            <h3>🍤 What to Expect</h3>
            <ul>
                <li><strong>Fresh Ingredients:</strong> Premium meats, seafood, and vegetables</li>
                <li><strong>Professional Chef:</strong> Skilled hibachi cooking with entertainment</li>
                <li><strong>Complete Setup:</strong> We bring all equipment and cleanup afterward</li>
                <li><strong>Memorable Experience:</strong> Perfect for celebrations and special occasions</li>
            </ul>
            
            <p><strong>Questions or need to make changes?</strong><br>
            Call us at <a href="tel:+1234567890">(123) 456-7890</a> or email <a href="mailto:bookings@myhibachi.com">bookings@myhibachi.com</a></p>
        </div>
        
        <div class="footer">
            <p>Thank you for choosing MyHibachi!<br>
            <a href="https://myhibachi.com">myhibachi.com</a> | Follow us on social media @MyHibachi</p>
        </div>
    </div>
</body>
</html>`

    const text = `
🎉 Your MyHibachi Experience is Confirmed!

Hi ${customerName},

Great news! Your MyHibachi experience has been confirmed.

BOOKING DETAILS:
Confirmation Number: ${confirmationNumber}
Date & Time: ${displayDate} at ${eventTime}
Guests: ${guestCount} people
Location: ${venueAddress.street}, ${venueAddress.city}, ${venueAddress.state} ${venueAddress.zipcode}

Add to calendar:
Google Calendar: ${calendarLinks.google}

Questions? Contact us:
Phone: (123) 456-7890
Email: bookings@myhibachi.com

Thank you for choosing MyHibachi!
myhibachi.com`

    return { subject, html, text }
  }

  // Generate review request email template
  private generateReviewEmail(bookingData: BookingEmailData): EmailTemplate {
    const { customerName } = bookingData
    
    const subject = "How Was Your Hibachi Experience? 🌟"
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Request</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 26px; font-weight: 600; }
        .content { padding: 35px 30px; }
        .review-buttons { text-align: center; margin: 30px 0; }
        .review-button { display: inline-block; background: #ff6b35; color: white; padding: 12px 25px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 5px 8px; }
        .review-button:hover { background: #e5552a; }
        .review-button.google { background: #4285f4; }
        .review-button.yelp { background: #d32323; }
        .review-button.facebook { background: #1877f2; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; }
        @media (max-width: 600px) {
            .container { margin: 10px; }
            .content, .header { padding: 25px 20px; }
            .review-button { display: block; margin: 10px 0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 How Was Your Experience?</h1>
        </div>
        
        <div class="content">
            <p>Hi <strong>${customerName}</strong>,</p>
            
            <p>We hope you had an amazing hibachi experience! Your feedback means the world to us and helps other families discover the joy of authentic hibachi cooking.</p>
            
            <p><strong>Would you mind taking a moment to share your experience?</strong></p>
            
            <div class="review-buttons">
                <a href="https://g.page/r/your-google-business-id/review" class="review-button google" target="_blank">⭐ Review on Google</a>
                <a href="https://www.yelp.com/writeareview/biz/your-yelp-business-id" class="review-button yelp" target="_blank">🍽️ Review on Yelp</a>
                <a href="https://www.facebook.com/your-facebook-page/reviews" class="review-button facebook" target="_blank">👍 Review on Facebook</a>
            </div>
            
            <p>Your honest review helps us improve and lets other families know what to expect. We truly appreciate your time!</p>
            
            <p><strong>Planning another event?</strong> We'd love to cook for you again! Visit <a href="https://myhibachi.com">myhibachi.com</a> to book your next experience.</p>
            
            <p>With gratitude,<br><strong>The MyHibachi Team</strong></p>
        </div>
        
        <div class="footer">
            <p>MyHibachi - Bringing Authentic Hibachi to You<br>
            <a href="https://myhibachi.com">myhibachi.com</a> | (123) 456-7890</p>
        </div>
    </div>
</body>
</html>`

    const text = `
🌟 How Was Your Hibachi Experience?

Hi ${customerName},

We hope you had an amazing hibachi experience! Would you mind taking a moment to share your experience?

Leave a review:
- Google: https://g.page/r/your-google-business-id/review
- Yelp: https://www.yelp.com/writeareview/biz/your-yelp-business-id
- Facebook: https://www.facebook.com/your-facebook-page/reviews

Planning another event? Visit myhibachi.com to book again!

With gratitude,
The MyHibachi Team
myhibachi.com | (123) 456-7890`

    return { subject, html, text }
  }

  // Generate upsell email template
  private generateUpsellEmail(bookingData: BookingEmailData): EmailTemplate {
    const { customerName } = bookingData
    const promoCode = `WELCOME10-${bookingData.bookingId.slice(-6)}`
    
    const subject = "Miss the Hibachi Magic? 🍤 Get 10% Off Your Next Experience!"
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Special Offer</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #6f42c1, #e83e8c); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 26px; font-weight: 600; }
        .content { padding: 35px 30px; }
        .promo-code { background: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 20px; text-align: center; margin: 25px 0; }
        .promo-code strong { font-size: 24px; color: #856404; letter-spacing: 2px; }
        .cta-button { display: inline-block; background: #ff6b35; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }
        .occasions { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; }
        @media (max-width: 600px) {
            .container { margin: 10px; }
            .content, .header { padding: 25px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍤 Miss the Hibachi Magic?</h1>
            <p>Special offer just for you!</p>
        </div>
        
        <div class="content">
            <p>Hi <strong>${customerName}</strong>,</p>
            
            <p>It's been a month since your last hibachi experience, and we've been thinking about you! We hope you're still savoring those delicious memories.</p>
            
            <p><strong>Ready for another unforgettable evening?</strong> We're offering you an exclusive 10% discount on your next booking!</p>
            
            <div class="promo-code">
                <p style="margin: 0 0 10px;">Your exclusive promo code:</p>
                <strong>${promoCode}</strong>
                <p style="margin: 10px 0 0; font-size: 14px;">Valid for 30 days</p>
            </div>
            
            <div style="text-align: center;">
                <a href="https://myhibachi.com/book?promo=${promoCode}" class="cta-button">🎉 Book Now & Save 10%</a>
            </div>
            
            <div class="occasions">
                <h3 style="margin: 0 0 15px; color: #ff6b35;">🎊 Perfect Occasions for Hibachi:</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Birthday celebrations</li>
                    <li>Anniversary dinners</li>
                    <li>Holiday gatherings</li>
                    <li>Date nights</li>
                    <li>Family reunions</li>
                    <li>Just because you deserve it!</li>
                </ul>
            </div>
            
            <p>Don't wait – this exclusive offer expires in 30 days, and our calendar fills up quickly!</p>
            
            <p>Can't wait to cook for you again,<br><strong>The MyHibachi Team</strong></p>
        </div>
        
        <div class="footer">
            <p>MyHibachi - Premium Hibachi Experiences<br>
            <a href="https://myhibachi.com">myhibachi.com</a> | (123) 456-7890</p>
            <p style="font-size: 12px; margin-top: 10px;">
                <a href="mailto:unsubscribe@myhibachi.com">Unsubscribe</a> from promotional emails
            </p>
        </div>
    </div>
</body>
</html>`

    const text = `
🍤 Miss the Hibachi Magic?

Hi ${customerName},

Ready for another unforgettable hibachi evening? We're offering you an exclusive 10% discount!

Your promo code: ${promoCode}
Valid for 30 days

Book now: https://myhibachi.com/book?promo=${promoCode}

Perfect occasions for hibachi:
- Birthday celebrations
- Anniversary dinners  
- Holiday gatherings
- Date nights
- Family reunions
- Just because you deserve it!

Can't wait to cook for you again,
The MyHibachi Team
myhibachi.com | (123) 456-7890`

    return { subject, html, text }
  }

  // Send email with error handling and logging
  private async sendEmail(
    to: string, 
    template: EmailTemplate, 
    bookingId: string, 
    emailType: 'confirmation' | 'review_request' | 'upsell'
  ): Promise<{ success: boolean; messageId?: string; error?: string }> {
    
    // Check rate limiting
    if (!this.checkEmailRateLimit(to)) {
      console.log(`[EMAIL RATE LIMITED] ${emailType} email to ${to} blocked due to rate limiting`)
      return { success: false, error: 'Rate limited' }
    }

    try {
      const result = await getResendClient().emails.send({
        from: 'MyHibachi <bookings@myhibachi.com>',
        to: [to],
        subject: template.subject,
        html: template.html,
        text: template.text,
        tags: [
          { name: 'type', value: emailType },
          { name: 'booking_id', value: bookingId }
        ]
      })

      // Log successful email
      const emailLog: EmailLog = {
        bookingId,
        emailType,
        recipientEmail: to,
        sentAt: new Date().toISOString(),
        status: 'sent',
        resendMessageId: result.data?.id
      }
      emailLogs.push(emailLog)

      console.log(`[EMAIL SENT] ${emailType} email sent to ${to} for booking ${bookingId}`)
      return { success: true, messageId: result.data?.id }

    } catch (error) {
      // Log failed email
      const emailLog: EmailLog = {
        bookingId,
        emailType,
        recipientEmail: to,
        sentAt: new Date().toISOString(),
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      emailLogs.push(emailLog)

      console.error(`[EMAIL ERROR] Failed to send ${emailType} email to ${to}:`, error)
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  // Send booking confirmation email immediately
  async sendBookingConfirmation(bookingData: BookingEmailData): Promise<boolean> {
    const template = this.generateConfirmationEmail(bookingData)
    const result = await this.sendEmail(
      bookingData.customerEmail, 
      template, 
      bookingData.bookingId, 
      'confirmation'
    )
    return result.success
  }

  // Send review request email (called by cron job)
  async sendReviewRequest(bookingData: BookingEmailData): Promise<boolean> {
    const template = this.generateReviewEmail(bookingData)
    const result = await this.sendEmail(
      bookingData.customerEmail, 
      template, 
      bookingData.bookingId, 
      'review_request'
    )
    return result.success
  }

  // Send upsell email (called by cron job)
  async sendUpsellEmail(bookingData: BookingEmailData): Promise<boolean> {
    const template = this.generateUpsellEmail(bookingData)
    const result = await this.sendEmail(
      bookingData.customerEmail, 
      template, 
      bookingData.bookingId, 
      'upsell'
    )
    return result.success
  }

  // Get email history for a booking
  getEmailHistory(bookingId: string): EmailLog[] {
    return emailLogs.filter(log => log.bookingId === bookingId)
  }

  // Get all email logs with pagination
  getAllEmailLogs(page: number = 1, limit: number = 50): { logs: EmailLog[], total: number } {
    const startIndex = (page - 1) * limit
    const endIndex = startIndex + limit
    return {
      logs: emailLogs.slice(startIndex, endIndex),
      total: emailLogs.length
    }
  }

  // Admin function to manually resend email
  async resendEmail(bookingId: string, emailType: 'confirmation' | 'review_request' | 'upsell', bookingData: BookingEmailData): Promise<boolean> {
    console.log(`[EMAIL ADMIN] Manual resend requested for booking ${bookingId}, type: ${emailType}`)
    
    switch (emailType) {
      case 'confirmation':
        return await this.sendBookingConfirmation(bookingData)
      case 'review_request':
        return await this.sendReviewRequest(bookingData)
      case 'upsell':
        return await this.sendUpsellEmail(bookingData)
      default:
        return false
    }
  }

  // Send custom email (for admin-generated emails like invoices)
  async sendCustomEmail(emailData: { to: string; subject: string; html: string; text: string }): Promise<boolean> {
    try {
      // Check rate limiting
      if (!this.checkEmailRateLimit(emailData.to)) {
        console.log(`[EMAIL RATE LIMITED] Custom email to ${emailData.to}`)
        return false
      }

      const { to, subject, html, text } = emailData

      const result = await getResendClient().emails.send({
        from: 'MyHibachi <noreply@myhibachi.com>',
        to: [to],
        subject,
        html,
        text,
      })

      // Log email
      const emailLog: EmailLog = {
        bookingId: 'custom',
        emailType: 'confirmation', // Using existing type for now
        recipientEmail: to,
        sentAt: new Date().toISOString(),
        status: 'sent',
        resendMessageId: result.data?.id
      }
      emailLogs.push(emailLog)

      console.log(`[EMAIL SENT] Custom email sent to ${to}, Message ID: ${result.data?.id}`)
      return true

    } catch (error) {
      console.error(`[EMAIL ERROR] Failed to send custom email:`, error)
      
      // Log failed email
      const emailLog: EmailLog = {
        bookingId: 'custom',
        emailType: 'confirmation',
        recipientEmail: emailData.to,
        sentAt: new Date().toISOString(),
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      emailLogs.push(emailLog)
      
      return false
    }
  }
}

// Export singleton instance
export const emailService = new MyHibachiEmailService()
export type { BookingEmailData, EmailLog }
