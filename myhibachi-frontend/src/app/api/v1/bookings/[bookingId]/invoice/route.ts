import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import jsPDF from 'jspdf'
import fs from 'fs'
import path from 'path'

const invoiceSchema = z.object({
  bookingId: z.string().min(1, 'Booking ID is required')
})

// Interfaces for future use
/*
interface MenuService {
  name: string
  description: string
  basePrice: number
  priceType: 'per_person' | 'flat_rate'
  category: 'hibachi_experience' | 'equipment' | 'service_fees' | 'travel' | 'add_ons'
  required?: boolean
}
*/

/*
interface DiscountPromotion {
  id: string
  name: string
  type: 'percentage' | 'fixed_amount'
  value: number
  description: string
  code?: string
  minOrderAmount?: number
  maxDiscount?: number
  validFrom?: string
  validTo?: string
  isActive: boolean
}
*/

interface BookingInvoiceData {
  bookingId: string
  confirmationNumber: string
  customerName: string
  customerEmail: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: {
    street: string
    city: string
    state: string
    zipcode: string
  }
  services: Array<{
    name: string
    description: string
    price: number
    quantity: number
    category: string
  }>
  subtotal: number
  tax: number
  totalAmount: number
  appliedDiscounts?: Array<{
    name: string
    type: 'percentage' | 'fixed_amount'
    value: number
    amount: number
  }>
  paymentStatus: 'paid' | 'pending' | 'overdue'
  paymentMethod?: string
  notes?: string
  // Deposit fields
  depositAmount?: number
  depositPaid?: boolean
  additionalNotes?: string
  paymentTerms?: string
  // New fields for travel and discount
  travelMiles?: number
  travelFee?: number
  discountAmount?: number
  discountDescription?: string
  adjustedTotal?: number
}

// MyHibachi menu services with real pricing - Available for future use
/* 
const MYHIBACHI_MENU_SERVICES: MenuService[] = [
  // Core Hibachi Experience
  {
    name: 'Adult Hibachi Experience',
    description: 'Full hibachi dining experience with chef performance, includes protein, vegetables, and rice',
    basePrice: 55,
    priceType: 'per_person',
    category: 'hibachi_experience',
    required: true
  },
  {
    name: 'Child Hibachi Experience (12 & Under)',
    description: 'Kids hibachi meal with smaller portions and chef entertainment',
    basePrice: 30,
    priceType: 'per_person',
    category: 'hibachi_experience'
  },
  
  // Premium Protein Upgrades
  {
    name: 'Premium Steak Upgrade',
    description: 'Upgrade to premium filet mignon',
    basePrice: 15,
    priceType: 'per_person',
    category: 'add_ons'
  },
  {
    name: 'Lobster Tail Addition',
    description: 'Fresh lobster tail grilled hibachi style',
    basePrice: 12,
    priceType: 'per_person',
    category: 'add_ons'
  },
  {
    name: 'Scallops Addition',
    description: 'Pan-seared scallops with garlic butter',
    basePrice: 8,
    priceType: 'per_person',
    category: 'add_ons'
  },
  {
    name: 'Extra Shrimp',
    description: 'Additional hibachi-style shrimp',
    basePrice: 5,
    priceType: 'per_person',
    category: 'add_ons'
  },

  // Equipment & Setup
  {
    name: 'Hibachi Grill & Equipment',
    description: 'Professional hibachi grill, utensils, and cooking equipment',
    basePrice: 0,
    priceType: 'flat_rate',
    category: 'equipment',
    required: true
  },
  {
    name: 'Table & Chairs Setup',
    description: 'Complete dining setup with tables and chairs for your party',
    basePrice: 0,
    priceType: 'flat_rate',
    category: 'equipment'
  },

  // Travel Fees (calculated based on distance from Fremont, CA)
  {
    name: 'Travel Fee',
    description: 'Travel fee calculated based on distance from our Fremont location',
    basePrice: 0, // This will be calculated dynamically
    priceType: 'flat_rate',
    category: 'travel'
  }
]
*/

// Function to get mock booking data
async function getMockBookingData(bookingId: string): Promise<BookingInvoiceData> {
  // Mock data - replace with actual database call
  const mockBooking: BookingInvoiceData = {
    bookingId: bookingId,
    confirmationNumber: bookingId === 'MHNZ2FCPP6' ? bookingId : `MH${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
    customerName: 'Sarah Johnson',
    customerEmail: 'sarah.johnson@email.com',
    eventDate: '2025-08-14',
    eventTime: '6:00 PM',
    guestCount: 8,
    venueAddress: {
      street: '123 Oak Street',
      city: 'San Jose',
      state: 'CA',
      zipcode: '95123'
    },
    services: [
      {
        name: 'Adult Hibachi Experience',
        description: 'Full hibachi dining experience with chef performance',
        price: 55,
        quantity: 6,
        category: 'hibachi_experience'
      },
      {
        name: 'Child Hibachi Experience (12 & Under)',
        description: 'Kids hibachi meal with smaller portions',
        price: 30,
        quantity: 2,
        category: 'hibachi_experience'
      },
      {
        name: 'Premium Steak Upgrade',
        description: 'Upgrade to premium filet mignon',
        price: 15,
        quantity: 2,
        category: 'add_ons'
      },
      {
        name: 'Lobster Tail Addition',
        description: 'Fresh lobster tail grilled hibachi style',
        price: 12,
        quantity: 4,
        category: 'add_ons'
      }
    ],
    subtotal: 468, // (6 * $55) + (2 * $30) + (2 * $15) + (4 * $12) = $330 + $60 + $30 + $48 = $468
    tax: 0, // Tax will be calculated properly on final total
    totalAmount: 468, // Will be recalculated with travel fees and tax
    appliedDiscounts: [
      // No automatic discounts - discounts are only applied through admin function
    ],
    paymentStatus: 'pending',
    notes: 'Customer requested extra ginger sauce'
  }

  // Travel fee will be calculated separately in the admin panel
  // Don't add travel fee as a service - it's handled as a separate line item
  
  // Calculate totals without travel fee in services (travel fee is separate)
  const servicesTotal = mockBooking.services.reduce((sum, service) => sum + (service.price * service.quantity), 0)
  const discountAmount = mockBooking.appliedDiscounts?.reduce((sum, discount) => sum + discount.amount, 0) || 0
  const subtotalAfterDiscount = servicesTotal - discountAmount
  
  // Tax will be calculated on the final total including travel fees in the main calculation logic
  mockBooking.subtotal = servicesTotal
  mockBooking.tax = 0 // Will be calculated properly on the final total later
  mockBooking.totalAmount = subtotalAfterDiscount

  return mockBooking
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ bookingId: string }> }
) {
  try {
    const { bookingId } = await context.params

    // Validate booking ID
    const validation = invoiceSchema.safeParse({ bookingId })
    if (!validation.success) {
      return NextResponse.json(
        { error: 'Invalid booking ID', details: validation.error.issues },
        { status: 400 }
      )
    }

    // Get URL parameters for deposit and other settings
    const url = new URL(request.url)
    const format = url.searchParams.get('format')
    const depositAmount = parseFloat(url.searchParams.get('depositAmount') || '0')
    const depositPaid = url.searchParams.get('depositPaid') === 'true'
    const additionalNotes = url.searchParams.get('additionalNotes') || ''
    const paymentTerms = url.searchParams.get('paymentTerms') || 'Due upon service completion'
    const urlTravelMiles = parseFloat(url.searchParams.get('travelMiles') || '0')
    const discountAmount = parseFloat(url.searchParams.get('discountAmount') || '0')
    const discountDescription = url.searchParams.get('discountDescription') || ''

    // Get booking data
    const booking = await getMockBookingData(bookingId)
    
    // Calculate travel fee - use URL parameter (admin panel handles travel fee calculation)
    const travelMiles = urlTravelMiles
    const travelFee = travelMiles * 2 // $2 per mile
    
    // Calculate services subtotal (same as admin panel)
    const servicesSubtotal = booking.services.reduce((sum, service) => sum + (service.price * service.quantity), 0)
    
    // Calculate subtotal with travel fee and after admin discount
    const subtotalWithTravel = servicesSubtotal + travelFee
    const subtotalAfterDiscount = subtotalWithTravel - discountAmount
    
    // Calculate tax on the final subtotal (8% tax rate)
    const taxAmount = Math.max(subtotalAfterDiscount, 0) * 0.08
    
    // Final total including tax
    const adjustedTotal = Math.max(subtotalAfterDiscount + taxAmount, 0)
    
    // Add all calculations to booking
    booking.depositAmount = depositAmount > 0 ? depositAmount : undefined
    booking.depositPaid = depositPaid
    booking.additionalNotes = additionalNotes
    booking.paymentTerms = paymentTerms
    booking.travelMiles = travelMiles
    booking.travelFee = travelFee
    booking.discountAmount = discountAmount
    booking.discountDescription = discountDescription
    booking.subtotal = servicesSubtotal // Use calculated services subtotal
    booking.tax = taxAmount // Update tax to be calculated on final total
    booking.adjustedTotal = adjustedTotal
    
    // Check if PDF is requested
    if (format === 'pdf') {
      // Generate PDF
      const pdfBuffer = await generateInvoicePDF(booking)
      
      return new NextResponse(new Uint8Array(pdfBuffer), {
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': `attachment; filename="MyHibachi-Invoice-${booking.confirmationNumber}.pdf"`
        }
      })
    }
    
    // Return HTML invoice
    const htmlInvoice = generateInvoiceHTML(booking)
    
    return new NextResponse(htmlInvoice, {
      headers: {
        'Content-Type': 'text/html'
      }
    })
    
  } catch (error) {
    console.error('Invoice generation error:', error)
    return NextResponse.json(
      { error: 'Failed to generate invoice' },
      { status: 500 }
    )
  }
}

function generateInvoiceHTML(booking: BookingInvoiceData): string {
  // Use the actual MyHibachi logo from public/images
  const logoPath = '/images/myhibachi-logo.png'

  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>MyHibachi Invoice - ${booking.confirmationNumber}</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        
        @media print {
            body { margin: 0; }
            .no-print { display: none; }
        }
        
        body {
            font-family: 'Poppins', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #4a2d13;
            background: linear-gradient(135deg, #f9e8d0 0%, rgba(249, 232, 208, 0.9) 50%, #ffb997 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .invoice-container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            box-shadow: 0 15px 40px rgba(74, 45, 19, 0.15);
            overflow: hidden;
            border: 2px solid rgba(219, 43, 40, 0.1);
        }
        
        .header {
            background: #f9e8d0;
            color: #4a2d13;
            padding: 30px;
            position: relative;
            min-height: 120px;
            border-bottom: 2px solid rgba(219, 43, 40, 0.1);
            box-shadow: 0 4px 20px rgba(74, 45, 19, 0.15);
        }
        
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 800;
            color: #db2b28;
            text-shadow: 2px 2px 4px rgba(219, 43, 40, 0.2);
            letter-spacing: 0.5px;
        }
        
        .header .business-info {
            margin-top: 15px;
            font-size: 14px;
            color: #6b4019;
            font-weight: 500;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-image {
            width: 100px;
            height: 100px;
            object-fit: contain;
            background: transparent;
            border-radius: 12px;
            border: none;
            padding: 8px;
        }
        
        .invoice-number {
            position: absolute;
            top: 30px;
            right: 30px;
            text-align: right;
            background: none;
            padding: 0;
            border-radius: 0;
            border: none;
            box-shadow: none;
        }
        
        .invoice-number h2 {
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 700;
            color: #4a2d13;
            text-shadow: none;
        }
        
        .invoice-meta {
            font-size: 14px;
            margin-top: 0;
            color: #4a2d13;
            font-weight: 500;
            line-height: 1.4;
        }
        
        .content {
            padding: 30px;
            background: #fff;
        }
        
        .billing-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .billing-info {
            background: #f9f4ec;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(219, 43, 40, 0.1);
        }
        
        .billing-info h3 {
            color: #db2b28;
            font-size: 16px;
            font-weight: 700;
            margin: 0 0 15px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #db2b28;
            padding-bottom: 8px;
        }
        
        .services-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(74, 45, 19, 0.08);
            border: 1px solid rgba(219, 43, 40, 0.1);
        }
        
        .services-table th {
            background: linear-gradient(135deg, #ff7b00, #ffb800);
            color: white;
            font-weight: 700;
            padding: 15px 12px;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 12px;
        }
        
        .services-table td {
            padding: 15px 12px;
            border-bottom: 1px solid rgba(219, 43, 40, 0.05);
            background: rgba(249, 244, 236, 0.3);
        }
        
        .services-table tbody tr:hover {
            background: rgba(249, 244, 236, 0.6);
            transform: translateY(-1px);
        }
        
        .services-table .description {
            font-size: 13px;
            color: #6b4019;
            margin-top: 4px;
            font-style: italic;
        }
        
        .amount-cell {
            text-align: right;
            font-weight: 700;
            color: #db2b28;
        }
        
        .totals-section {
            max-width: 350px;
            margin-left: auto;
            background: linear-gradient(135deg, #f9f4ec, rgba(249, 244, 236, 0.8));
            border-radius: 15px;
            padding: 25px;
            border: 2px solid rgba(219, 43, 40, 0.1);
            box-shadow: 0 10px 30px rgba(74, 45, 19, 0.1);
        }
        
        .total-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-weight: 500;
            color: #4a2d13;
        }
        
        .total-row.final {
            font-size: 20px;
            font-weight: 800;
            color: #db2b28;
            border-top: 3px solid #db2b28;
            padding-top: 15px;
            margin-top: 15px;
            text-shadow: 1px 1px 2px rgba(219, 43, 40, 0.1);
        }
        
        .discount-row {
            color: #16a34a;
            background: rgba(34, 197, 94, 0.1);
            padding: 8px 12px;
            border-radius: 8px;
            margin: 4px 0;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }
        
        .deposit-row {
            background-color: #f8f9fa;
            padding: 8px 12px;
            margin: 8px -12px 0;
            border-radius: 6px;
            border-left: 4px solid #6c757d;
        }
        
        .paid-deposit {
            color: #28a745;
            font-weight: 600;
        }
        
        .required-deposit {
            color: #dc3545;
            font-weight: 600;
        }
        
        .balance-due {
            font-weight: 700;
            font-size: 18px;
            background-color: #fff3cd;
            padding: 10px 12px;
            margin: 8px -12px 0;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            color: #856404;
        }
        
        .balance-paid {
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        .travel-fee {
            background-color: #e3f2fd;
            padding: 8px 12px;
            margin: 8px -12px 0;
            border-radius: 6px;
            border-left: 4px solid #2196f3;
        }
        
        .travel-amount {
            color: #1976d2;
            font-weight: 600;
        }
        
        .admin-discount {
            background-color: #f3e5f5;
            padding: 8px 12px;
            margin: 8px -12px 0;
            border-radius: 6px;
            border-left: 4px solid #9c27b0;
        }
        
        .discount-amount {
            color: #7b1fa2;
            font-weight: 600;
        }
        
        .adjusted-total {
            font-weight: 700;
            font-size: 16px;
            background-color: #fff8e1;
            padding: 10px 12px;
            margin: 8px -12px 0;
            border-radius: 6px;
            border-left: 4px solid #ff9800;
            color: #e65100;
        }
        
        .payment-info {
            background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
            border: 2px solid #86efac;
            border-radius: 15px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 10px 30px rgba(34, 197, 94, 0.1);
        }
        
        .payment-info h3 {
            color: #166534;
            margin: 0 0 15px 0;
            font-weight: 700;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .payment-info p {
            color: #15803d;
            margin: 8px 0;
            font-weight: 500;
        }
        
        .footer {
            background: linear-gradient(135deg, #ffb800, #db2b28);
            color: white;
            padding: 25px 30px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
        }
        
        .footer p {
            margin: 8px 0;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        .footer strong {
            font-weight: 700;
            font-size: 16px;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .billing-section {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .invoice-number {
                position: static;
                text-align: left;
                margin-top: 20px;
                background: none;
                padding: 0;
                border: none;
                box-shadow: none;
            }
            
            .header {
                padding: 20px;
                min-height: auto;
            }
            
            .content {
                padding: 20px;
            }
            
            .logo-container {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            
            .services-table th,
            .services-table td {
                padding: 10px 8px;
                font-size: 12px;
            }
        }
      </style>
    </head>
    <body>
      <div class="invoice-container">
        <div class="header">
          <div class="logo-container">
            <img src="${logoPath}" alt="MyHibachi Logo" class="logo-image" />
            <div>
              <h1>MyHibachi</h1>
              <div class="business-info">
                Professional Hibachi Catering Service<br>
                Email: cs@myhibachichef.com<br>
                Phone: +1 (916) 740-8768
              </div>
            </div>
          </div>
          
          <div class="invoice-number">
            <h2>INVOICE</h2>
            <div class="invoice-meta">
              <strong>#${booking.confirmationNumber}</strong><br>
              Date: ${new Date().toLocaleDateString()}<br>
              Due: ${booking.paymentStatus === 'paid' ? 'PAID' : 'Upon Service'}
            </div>
          </div>
        </div>

        <div class="content">
          <div class="billing-section">
            <div class="billing-info">
              <h3>Bill To</h3>
              <p><strong>${booking.customerName}</strong></p>
              <p>${booking.customerEmail}</p>
              <p>${booking.venueAddress.street}<br>
                 ${booking.venueAddress.city}, ${booking.venueAddress.state} ${booking.venueAddress.zipcode}
              </p>
            </div>
            
            <div class="billing-info">
              <h3>Event Details</h3>
              <p><strong>Date:</strong> ${new Date(booking.eventDate).toLocaleDateString()}</p>
              <p><strong>Time:</strong> ${booking.eventTime}</p>
              <p><strong>Guests:</strong> ${booking.guestCount} people</p>
              <p><strong>Status:</strong> ${booking.paymentStatus.toUpperCase()}</p>
            </div>
          </div>

          <table class="services-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              ${booking.services.map(service => `
                <tr>
                  <td>
                    <strong>${service.name}</strong>
                    ${service.description ? `<div class="description">${service.description}</div>` : ''}
                  </td>
                  <td>${service.quantity}</td>
                  <td class="amount-cell">$${service.price.toFixed(2)}</td>
                  <td class="amount-cell">$${(service.price * service.quantity).toFixed(2)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="totals-section">
            <h3 style="color: #333; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #dc2626; padding-bottom: 8px;">Payment Summary</h3>
            
            <div class="total-row">
              <span>Services Subtotal:</span>
              <span>$${booking.subtotal.toFixed(2)}</span>
            </div>
            
            ${booking.travelFee && booking.travelFee > 0 ? `
              <div class="total-row travel-fee">
                <span>Travel Fee (${booking.travelMiles} mi × $2):</span>
                <span class="travel-amount">+$${booking.travelFee.toFixed(2)}</span>
              </div>
            ` : ''}
            
            ${booking.discountAmount && booking.discountAmount > 0 ? `
              <div class="total-row admin-discount">
                <span>Discount (${booking.discountDescription || 'Applied'}):</span>
                <span class="discount-amount">-$${booking.discountAmount.toFixed(2)}</span>
              </div>
            ` : ''}
            
            <div class="total-row">
              <span>Tax and Processing Fee (8%):</span>
              <span class="travel-amount">+$${booking.tax.toFixed(2)}</span>
            </div>
            
            <!-- Subtotal line separator -->
            <div style="border-top: 1px solid #e5e7eb; margin: 10px 0;"></div>
            
            <div class="total-row final" style="font-weight: bold; font-size: 14px;">
              <span>Total Amount:</span>
              <span>$${booking.adjustedTotal?.toFixed(2)}</span>
            </div>
            
            ${booking.depositAmount && booking.depositAmount > 0 ? `
              <div class="total-row deposit-row" style="background-color: ${booking.depositPaid ? '#f0f9ff' : '#fef2f2'}; padding: 8px; border-radius: 4px; margin: 8px 0;">
                <span style="font-weight: 500;">Deposit ${booking.depositPaid ? 'Paid' : 'Required'}:</span>
                <span class="${booking.depositPaid ? 'paid-deposit' : 'required-deposit'}" style="font-weight: bold;">${booking.depositPaid ? '-' : ''}$${booking.depositAmount.toFixed(2)}</span>
              </div>
              
              <!-- Final balance separator -->
              <div style="border-top: 2px solid #dc2626; margin: 12px 0;"></div>
              
              <div class="total-row balance-summary" style="font-weight: bold; font-size: 16px; color: #dc2626;">
                <span>Amount Due:</span>
                <span>$${Math.max((booking.adjustedTotal || booking.totalAmount) - (booking.depositPaid ? booking.depositAmount : 0), 0).toFixed(2)}</span>
              </div>
              
              <!-- Payment method comparison at the bottom -->
              <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 12px;">
                ${(() => {
                  const subtotalBeforeTax = booking.subtotal + (booking.travelFee || 0) - (booking.discountAmount || 0)
                  const cardVenmoTotal = subtotalBeforeTax + (subtotalBeforeTax * 0.08)
                  const cashZelleTotal = subtotalBeforeTax
                  const depositAmount = booking.depositPaid && booking.depositAmount ? booking.depositAmount : 0
                  const cardVenmoAmountDue = Math.max(cardVenmoTotal - depositAmount, 0)
                  const cashZelleAmountDue = Math.max(cashZelleTotal - depositAmount, 0)
                  
                  return `
                    <div style="color: #e65100; margin-bottom: 4px;">For Card/Venmo Payments: $${cardVenmoAmountDue.toFixed(2)}</div>
                    <div style="color: #2e7d32;">For Cash/Zelle Payments: $${cashZelleAmountDue.toFixed(2)} (after processing fee discount)</div>
                  `
                })()}
              </div>
            ` : ''}
          </div>

          ${booking.paymentStatus === 'paid' ? `
            <div class="payment-info">
              <h3>💳 Payment Information</h3>
              <p><strong>Status:</strong> Paid in Full</p>
              <p><strong>Payment Method:</strong> ${booking.paymentMethod || 'Credit Card'}</p>
              <p><strong>Transaction Date:</strong> ${new Date().toLocaleDateString()}</p>
            </div>
          ` : `
            <div class="payment-info">
              <h3>💰 Payment Instructions</h3>
              <p><strong>Amount Due:</strong> $${Math.max((booking.adjustedTotal || booking.totalAmount) - (booking.depositPaid && booking.depositAmount ? booking.depositAmount : 0), 0).toFixed(2)}</p>
              <p><strong>Payment Terms:</strong> Due upon service completion</p>
              <p><strong>Accepted Methods:</strong> Cash, Credit Card, Zelle</p>
            </div>
          `}

          ${booking.notes ? `
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #dc2626;">
              <strong>Special Notes:</strong><br>
              ${booking.notes}
            </div>
          ` : ''}
        </div>

        <div class="footer">
          <p><strong>Thank you for choosing MyHibachi!</strong></p>
          <p>Questions? Contact us at cs@myhibachichef.com or +1 (916) 740-8768</p>
          <p>Follow us for more delicious hibachi experiences!</p>
        </div>
      </div>
      
      <div class="no-print" style="text-align: center; margin: 20px;">
        <a href="?format=pdf" style="background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600;">Download PDF</a>
      </div>
    </body>
    </html>
  `
}

async function generateInvoicePDF(booking: BookingInvoiceData): Promise<Buffer> {
  const pdf = new jsPDF()
  const pageWidth = pdf.internal.pageSize.getWidth()
  
  // Colors (available for future styling)
  // const primaryColor = '#dc2626' // Red-600
  // const secondaryColor = '#374151' // Gray-700
  
  let yPosition = 20

  // Header section matching navbar design - compressed
  // Top header bar with navbar background color (light tan) - made shorter
  pdf.setFillColor(245, 245, 220) // Light tan navbar background
  pdf.rect(0, 0, pageWidth, 32, 'F') // Reduced from 40 to 32 for shorter header
  
  // Invoice section (top right, no container)
  pdf.setFontSize(16) // Reduced from 18
  pdf.setFont('helvetica', 'bold')
  pdf.setTextColor(220, 38, 40) // MyHibachi red text on tan background
  pdf.text('INVOICE', pageWidth - 20, 10, { align: 'right' }) // Adjusted position
  
  pdf.setFontSize(10) // Reduced from 11
  pdf.setFont('helvetica', 'bold')
  pdf.setTextColor(75, 85, 99) // Dark gray for details
  pdf.text(`#${booking.confirmationNumber}`, pageWidth - 20, 18, { align: 'right' })
  
  pdf.setFontSize(9) // Reduced from 10
  pdf.setFont('helvetica', 'normal')
  pdf.text(`Date: ${new Date().toLocaleDateString()}`, pageWidth - 20, 26, { align: 'right' })
  
  try {
    // Load and embed the actual MyHibachi logo (navbar dimensions) - compressed
    const logoPath = path.join(process.cwd(), 'public', 'images', 'myhibachi-logo.png')
    const logoBase64 = fs.readFileSync(logoPath, 'base64')
    const logoDataUrl = `data:image/png;base64,${logoBase64}`
    
    // Add logo image with better proportional dimensions (left side)
    pdf.addImage(logoDataUrl, 'PNG', 15, 4, 30, 18) // Adjusted y position for shorter header
    
    // Company text in center between logo and invoice info
    const centerX = pageWidth / 2
    pdf.setFontSize(10) // Reduced from 11
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(75, 85, 99) // Dark gray text on tan background
    pdf.text('My hibachi chef professional catering', centerX, 12, { align: 'center' })
    
    // Contact details centered below company name
    pdf.setFontSize(8) // Reduced from 9
    pdf.setFont('helvetica', 'normal')
    pdf.setTextColor(75, 85, 99) // Dark gray text
    pdf.text('cs@myhibachichef.com | +1 (916) 740-8768', centerX, 20, { align: 'center' })
    
  } catch {
    // Fallback to text if logo loading fails - compressed with center layout
    pdf.setFontSize(16) // Reduced from 18
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(220, 38, 40) // MyHibachi red
    pdf.text('MyHibachi', 15, 14)
    
    // Center company text even in fallback
    const centerX = pageWidth / 2
    pdf.setFontSize(10) // Reduced from 11
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(75, 85, 99) // Dark gray text
    pdf.text('My hibachi chef professional catering', centerX, 12, { align: 'center' })
    
    pdf.setFontSize(8) // Reduced from 9
    pdf.setFont('helvetica', 'normal')
    pdf.setTextColor(75, 85, 99) // Dark gray text
    pdf.text('cs@myhibachichef.com | +1 (916) 740-8768', centerX, 20, { align: 'center' })
  }
  
  yPosition = 40 // Reduced from 50 due to shorter header
  
  // Reset text color for content
  pdf.setTextColor(0, 0, 0)
  
  // Billing and Event Details section - side by side for better space usage - compressed
  const leftColumnX = 15
  const rightColumnX = pageWidth / 2 + 10
  
  // Bill To section (left column)
  pdf.setFontSize(11) // Reduced from 12
  pdf.setFont('helvetica', 'bold')
  pdf.text('Bill To:', leftColumnX, yPosition)
  
  pdf.setFontSize(9) // Reduced from 10
  pdf.setFont('helvetica', 'normal')
  pdf.text(booking.customerName, leftColumnX, yPosition + 10) // Reduced spacing
  pdf.text(booking.customerEmail, leftColumnX, yPosition + 18)
  pdf.text(`${booking.venueAddress.street}`, leftColumnX, yPosition + 26)
  pdf.text(`${booking.venueAddress.city}, ${booking.venueAddress.state} ${booking.venueAddress.zipcode}`, leftColumnX, yPosition + 34)
  
  // Event Details (right column)
  pdf.setFontSize(11) // Reduced from 12
  pdf.setFont('helvetica', 'bold')
  pdf.text('Event Details:', rightColumnX, yPosition)
  
  pdf.setFontSize(9) // Reduced from 10
  pdf.setFont('helvetica', 'normal')
  pdf.text(`Date: ${new Date(booking.eventDate).toLocaleDateString()}`, rightColumnX, yPosition + 10)
  pdf.text(`Time: ${booking.eventTime}`, rightColumnX, yPosition + 18)
  pdf.text(`Guests: ${booking.guestCount} people`, rightColumnX, yPosition + 26)
  pdf.text(`Status: ${booking.paymentStatus.toUpperCase()}`, rightColumnX, yPosition + 34)
  
  yPosition += 45 // Reduced from 50
  
  // Services Table Header - more compact
  pdf.setFillColor(245, 245, 245)
  pdf.rect(15, yPosition - 3, pageWidth - 30, 10, 'F') // Reduced height from 12 to 10
  
  pdf.setFontSize(9) // Reduced from 10
  pdf.setFont('helvetica', 'bold')
  pdf.text('Service', 20, yPosition + 3) // Adjusted positioning
  pdf.text('Qty', pageWidth - 100, yPosition + 3, { align: 'center' })
  pdf.text('Unit Price', pageWidth - 65, yPosition + 3, { align: 'center' })
  pdf.text('Total', pageWidth - 20, yPosition + 3, { align: 'right' })
  
  yPosition += 15 // Reduced from 18
  
  // Services with improved spacing and text wrapping - more compact
  pdf.setFont('helvetica', 'normal')
  pdf.setFontSize(9) // Reduced from 10
  
  booking.services.forEach(service => {
    const total = service.price * service.quantity
    
    // Service name with proper text wrapping - more compact
    const maxServiceWidth = pageWidth - 130
    const serviceNameLines = pdf.splitTextToSize(service.name, maxServiceWidth)
    
    // Main service info
    pdf.text(serviceNameLines[0], 20, yPosition)
    pdf.text(service.quantity.toString(), pageWidth - 100, yPosition, { align: 'center' })
    pdf.text(`$${service.price.toFixed(2)}`, pageWidth - 65, yPosition, { align: 'center' })
    pdf.text(`$${total.toFixed(2)}`, pageWidth - 20, yPosition, { align: 'right' })
    
    let currentY = yPosition
    
    // Handle multi-line service names
    if (serviceNameLines.length > 1) {
      for (let i = 1; i < serviceNameLines.length; i++) {
        currentY += 6 // Reduced from 8
        pdf.text(serviceNameLines[i], 20, currentY)
      }
    }
    
    // Description with proper spacing and wrapping - more compact
    if (service.description) {
      pdf.setFontSize(7) // Reduced from 8
      pdf.setTextColor(120, 120, 120)
      currentY += 6 // Reduced from 8
      
      const descLines = pdf.splitTextToSize(service.description, maxServiceWidth)
      descLines.forEach((line: string, index: number) => {
        if (index > 0) currentY += 5 // Reduced from 6
        pdf.text(line, 25, currentY)
      })
      
      pdf.setFontSize(9) // Reduced from 10
      pdf.setTextColor(0, 0, 0)
    }
    
    yPosition = currentY + 8 // Reduced from 12
    
    // Remove the page break check here since we want to fit on one page
  })
  
  // Payment Summary section - moved to left side for better space usage
  yPosition += 5
  const leftSummaryX = 15 // Left aligned for better space usage
  
  // Payment Summary header with underline - left aligned
  pdf.setFontSize(11)
  pdf.setFont('helvetica', 'bold')
  pdf.text('Payment Summary', leftSummaryX, yPosition)
  
  // Draw underline for Payment Summary header
  pdf.setLineWidth(1)
  pdf.setDrawColor(220, 38, 40) // MyHibachi red
  pdf.line(leftSummaryX, yPosition + 2, 140, yPosition + 2) // Underline width
  yPosition += 8
  
  // Services Subtotal
  pdf.setFontSize(9)
  pdf.setFont('helvetica', 'normal')
  pdf.setDrawColor(0, 0, 0) // Reset line color
  pdf.text('Services Subtotal:', leftSummaryX, yPosition)
  pdf.text(`$${booking.subtotal.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
  yPosition += 10
  
  // Travel fee (if applicable)
  if (booking.travelFee && booking.travelFee > 0) {
    pdf.setTextColor(25, 118, 210) // Blue for travel fee
    pdf.text(`Travel Fee (${booking.travelMiles} mi × $2):`, leftSummaryX, yPosition)
    pdf.text(`+$${booking.travelFee.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
    pdf.setTextColor(0, 0, 0) // Reset color
    yPosition += 10
  }
  
  // Admin discount (if applicable)
  if (booking.discountAmount && booking.discountAmount > 0) {
    pdf.setTextColor(0, 150, 0) // Green for discount
    const discountText = booking.discountDescription ? 
      `Discount (${booking.discountDescription}):` : 
      'Discount (Applied):'
    pdf.text(discountText, leftSummaryX, yPosition)
    pdf.text(`-$${booking.discountAmount.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
    pdf.setTextColor(0, 0, 0) // Reset color
    yPosition += 10
  }
  
  // Calculate subtotal before tax (for cash/Zelle discount calculation)
  const subtotalBeforeTax = booking.subtotal + (booking.travelFee || 0) - (booking.discountAmount || 0)
  
  // Tax line - show the 8% tax calculation
  pdf.setTextColor(229, 81, 0) // Orange for tax
  pdf.text('Tax and Processing Fee (8%):', leftSummaryX, yPosition)
  pdf.text(`+$${booking.tax.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
  pdf.setTextColor(0, 0, 0) // Reset color
  yPosition += 10
  
  // Subtotal separator line
  pdf.setLineWidth(0.3)
  pdf.setDrawColor(200, 200, 200)
  pdf.line(leftSummaryX, yPosition + 1, leftSummaryX + 125, yPosition + 1)
  yPosition += 6
  
  // Total Amount - use the adjusted total from booking
  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(10)
  pdf.text('Total Amount:', leftSummaryX, yPosition)
  pdf.text(`$${booking.adjustedTotal?.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
  yPosition += 12
  
  // Deposit information (if applicable) - compact
  if (booking.depositAmount && booking.depositAmount > 0) {
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(9)
    pdf.setTextColor(102, 0, 204) // Purple for deposit
    pdf.text(`Deposit ${booking.depositPaid ? 'Paid' : 'Required'}:`, leftSummaryX, yPosition)
    if (booking.depositPaid) {
      pdf.text(`-$${booking.depositAmount.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
    } else {
      pdf.text(`$${booking.depositAmount.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
    }
    pdf.setTextColor(0, 0, 0) // Reset color
    yPosition += 8
    
    // Final separator
    pdf.setLineWidth(0.5)
    pdf.setDrawColor(220, 38, 40)
    pdf.line(leftSummaryX, yPosition, leftSummaryX + 125, yPosition)
    yPosition += 6
    
    // Amount Due - simplified calculation
    pdf.setFont('helvetica', 'bold')
    pdf.setFontSize(10)
    pdf.text('Amount Due:', leftSummaryX, yPosition)
    
    // Use the booking's adjusted total minus deposit
    const amountDue = Math.max((booking.adjustedTotal || booking.totalAmount) - (booking.depositPaid ? booking.depositAmount : 0), 0)
    
    pdf.text(`$${amountDue.toFixed(2)}`, leftSummaryX + 120, yPosition, { align: 'right' })
    yPosition += 15
    
    // Payment method comparison - at the bottom
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(8)
    
    // Calculate amounts for both payment methods after deposit
    const cardVenmoTotal = subtotalBeforeTax + (subtotalBeforeTax * 0.08)
    const cashZelleTotal = subtotalBeforeTax
    const cardVenmoAmountDue = Math.max(cardVenmoTotal - booking.depositAmount, 0)
    const cashZelleAmountDue = Math.max(cashZelleTotal - booking.depositAmount, 0)
    
    pdf.setTextColor(229, 81, 0) // Orange for card/venmo
    pdf.text(`For Card/Venmo Payments: $${cardVenmoAmountDue.toFixed(2)}`, leftSummaryX, yPosition)
    yPosition += 8
    
    pdf.setTextColor(0, 150, 0) // Green for cash/zelle
    pdf.text(`For Cash/Zelle Payments: $${cashZelleAmountDue.toFixed(2)} (after processing fee discount)`, leftSummaryX, yPosition)
    pdf.setTextColor(0, 0, 0) // Reset color
    yPosition += 10
  }
  
  // Compact footer - positioned at bottom of content
  yPosition += 15
  
  // Footer - very compact, no payment terms
  pdf.setDrawColor(220, 38, 40)
  pdf.setLineWidth(0.5)
  pdf.line(15, yPosition, pageWidth - 15, yPosition)
  yPosition += 5
  
  pdf.setFontSize(7)
  pdf.setFont('helvetica', 'normal')
  pdf.setTextColor(85, 85, 85)
  
  // Contact info only - compact
  pdf.text('Questions? Call +1 (916) 740-8768 | Email: cs@myhibachichef.com | www.myhibachichef.com', 15, yPosition)
  yPosition += 8
  
  // Thank you - compact
  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(8)
  pdf.text('Thank you for choosing MyHibachi Catering!', 15, yPosition)
  
  return Buffer.from(pdf.output('arraybuffer'))
}
