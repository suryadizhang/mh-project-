import { NextRequest, NextResponse } from 'next/server'
import { emailService } from '@/lib/email-service'

interface InvoiceEmailData {
  to: string
  subject: string
  bookingId: string
  customerName: string
  total: number
  eventDate: string
  eventTime: string
  invoiceData: {
    guestCount: number
    selectedUpgrades: string[]
    travelFee: number
    adminNotes: string
    basePrice: number
    upgradesTotal: number
  }
}

// Menu upgrades lookup (same as admin page)
const MENU_UPGRADES = [
  { id: 'premium_steak', name: 'Premium Wagyu Steak Upgrade', price: 25.00 },
  { id: 'lobster_tail', name: 'Lobster Tail Addition', price: 30.00 },
  { id: 'premium_sake', name: 'Premium Sake Pairing', price: 20.00 },
  { id: 'dessert_tempura', name: 'Tempura Ice Cream Dessert', price: 12.00 },
  { id: 'extra_chef_show', name: 'Extended Chef Performance', price: 50.00 },
  { id: 'party_decorations', name: 'Birthday/Anniversary Decorations', price: 35.00 },
  { id: 'premium_vegetables', name: 'Organic Vegetable Upgrade', price: 15.00 },
  { id: 'sushi_appetizers', name: 'Fresh Sushi Appetizer Platter', price: 40.00 }
]

export async function POST(request: NextRequest) {
  try {
    const emailData: InvoiceEmailData = await request.json()
    
    // Generate HTML email template for invoice
    const invoiceEmailHtml = generateInvoiceEmailTemplate(emailData)
    const invoiceEmailText = generateInvoiceEmailText(emailData)
    
    // Send email using existing email service
    const emailSent = await emailService.sendCustomEmail({
      to: emailData.to,
      subject: emailData.subject,
      html: invoiceEmailHtml,
      text: invoiceEmailText
    })
    
    if (emailSent) {
      return NextResponse.json({ 
        success: true, 
        message: 'Invoice sent successfully' 
      })
    } else {
      return NextResponse.json({ 
        success: false, 
        error: 'Failed to send invoice email' 
      }, { status: 500 })
    }
    
  } catch (error) {
    console.error('Invoice email error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Internal server error' 
    }, { status: 500 })
  }
}

function generateInvoiceEmailTemplate(data: InvoiceEmailData): string {
  const { customerName, bookingId, total, eventDate, eventTime, invoiceData } = data
  
  const eventDateFormatted = new Date(eventDate).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
  
  // Generate upgrade items HTML
  const upgradesHtml = invoiceData.selectedUpgrades.map(upgradeId => {
    const upgrade = MENU_UPGRADES.find(u => u.id === upgradeId)
    if (upgrade) {
      return `
        <tr>
          <td style="padding: 8px 0; border-bottom: 1px solid #eee;">
            ${upgrade.name}
          </td>
          <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">
            +$${upgrade.price.toFixed(2)}
          </td>
        </tr>
      `
    }
    return ''
  }).join('')
  
  return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MyHibachi Invoice</title>
    <style>
        body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #dc2626, #ea580c); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .header p { margin: 5px 0 0; opacity: 0.9; }
        .content { padding: 35px 30px; }
        .invoice-info { background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px; }
        .invoice-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .invoice-table th { background: #f1f5f9; padding: 12px; text-align: left; font-weight: 600; }
        .invoice-table td { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }
        .total-row { background: #fef7ed; font-weight: 600; font-size: 16px; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6b7280; font-size: 14px; }
        .btn { display: inline-block; background: #dc2626; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 10px 5px; }
        @media (max-width: 600px) {
            .container { margin: 10px; }
            .content, .header { padding: 25px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍤 MyHibachi Invoice</h1>
            <p>Premium Mobile Hibachi Experience</p>
        </div>
        
        <div class="content">
            <h2>Hello ${customerName},</h2>
            <p>Thank you for choosing MyHibachi! Please find your invoice details below.</p>
            
            <div class="invoice-info">
                <h3 style="margin-top: 0;">📋 Booking Details</h3>
                <p><strong>Booking ID:</strong> ${bookingId}</p>
                <p><strong>Event Date:</strong> ${eventDateFormatted} at ${eventTime}</p>
                <p><strong>Guests:</strong> ${invoiceData.guestCount} people</p>
            </div>
            
            <h3>💰 Invoice Breakdown</h3>
            <table class="invoice-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Hibachi Experience (${invoiceData.guestCount} guests × $85.00)</td>
                        <td style="text-align: right;">$${invoiceData.basePrice.toFixed(2)}</td>
                    </tr>
                    ${upgradesHtml}
                    ${invoiceData.travelFee > 0 ? `
                    <tr>
                        <td>Travel/Setup Fee</td>
                        <td style="text-align: right;">+$${invoiceData.travelFee.toFixed(2)}</td>
                    </tr>
                    ` : ''}
                    <tr class="total-row">
                        <td><strong>TOTAL</strong></td>
                        <td style="text-align: right;"><strong>$${total.toFixed(2)}</strong></td>
                    </tr>
                </tbody>
            </table>
            
            ${invoiceData.adminNotes ? `
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #92400e;">📝 Special Notes:</h4>
                <p style="margin-bottom: 0; color: #92400e;">${invoiceData.adminNotes}</p>
            </div>
            ` : ''}
            
            <p><strong>Payment Information:</strong></p>
            <p>We accept payment via cash, check, or electronic transfer. Payment is typically due on the day of service unless other arrangements have been made.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://myhibachi.com/contact" class="btn">Contact Us</a>
                <a href="https://myhibachi.com/book" class="btn" style="background: #059669;">Book Again</a>
            </div>
            
            <p>We're excited to create an unforgettable hibachi experience for you!</p>
            
            <p>Best regards,<br><strong>The MyHibachi Team</strong></p>
        </div>
        
        <div class="footer">
            <p>MyHibachi - Premium Mobile Hibachi Experience<br>
            <a href="https://myhibachi.com">myhibachi.com</a> | +1 (916) 740-8768 | cs@myhibachichef.com</p>
            <p style="font-size: 12px; color: #9ca3af;">
                This invoice was generated automatically. If you have any questions, please contact us.
            </p>
        </div>
    </div>
</body>
</html>`
}

function generateInvoiceEmailText(data: InvoiceEmailData): string {
  const { customerName, bookingId, total, eventDate, eventTime, invoiceData } = data
  
  const eventDateFormatted = new Date(eventDate).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
  
  // Generate upgrade items text
  const upgradesText = invoiceData.selectedUpgrades.map(upgradeId => {
    const upgrade = MENU_UPGRADES.find(u => u.id === upgradeId)
    return upgrade ? `- ${upgrade.name}: +$${upgrade.price.toFixed(2)}` : ''
  }).join('\n')
  
  return `
🍤 MyHibachi Invoice

Hello ${customerName},

Thank you for choosing MyHibachi! Please find your invoice details below.

BOOKING DETAILS:
Booking ID: ${bookingId}
Event Date: ${eventDateFormatted} at ${eventTime}
Guests: ${invoiceData.guestCount} people

INVOICE BREAKDOWN:
- Hibachi Experience (${invoiceData.guestCount} guests × $85.00): $${invoiceData.basePrice.toFixed(2)}
${upgradesText}
${invoiceData.travelFee > 0 ? `- Travel/Setup Fee: +$${invoiceData.travelFee.toFixed(2)}` : ''}

TOTAL: $${total.toFixed(2)}

${invoiceData.adminNotes ? `
SPECIAL NOTES:
${invoiceData.adminNotes}
` : ''}

PAYMENT INFORMATION:
We accept payment via cash, check, or electronic transfer. Payment is typically due on the day of service unless other arrangements have been made.

We're excited to create an unforgettable hibachi experience for you!

Best regards,
The MyHibachi Team

MyHibachi - Premium Mobile Hibachi Experience
myhibachi.com | +1 (916) 740-8768 | cs@myhibachichef.com`
}
