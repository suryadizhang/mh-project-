import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { 
      method, 
      amount, 
      bookingId, 
      paymentType, 
      tipAmount, 
      customerInfo, 
      memo, 
      timestamp 
    } = body

    // Validate required fields
    if (!method || !amount || !customerInfo?.name || !customerInfo?.email) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // In a real implementation, you would:
    // 1. Save to database
    // 2. Send notification to admin
    // 3. Send confirmation email to customer
    // 4. Update booking status if applicable

    const paymentRecord = {
      id: `ALT-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      method,
      amount,
      bookingId: bookingId || null,
      paymentType: paymentType || 'manual',
      tipAmount: tipAmount || 0,
      customer: {
        name: customerInfo.name,
        email: customerInfo.email,
        phone: customerInfo.phone
      },
      memo,
      status: 'pending_verification',
      createdAt: timestamp || new Date().toISOString(),
      verifiedAt: null
    }

    // Log the payment record for audit trail
    console.log('[ALTERNATIVE PAYMENT RECORDED]', {
      id: paymentRecord.id,
      method,
      amount: `$${amount.toFixed(2)}`,
      customer: customerInfo.email,
      bookingId: bookingId || 'manual-payment'
    })

    // In production, you would:
    // 1. Save to your database
    // await savePaymentRecord(paymentRecord)
    
    // 2. Send admin notification
    // await sendAdminNotification(paymentRecord)
    
    // 3. Send customer confirmation
    // await sendCustomerConfirmation(paymentRecord)

    // 4. Update booking if applicable
    // if (bookingId) {
    //   await updateBookingPaymentStatus(bookingId, paymentType, 'pending_verification')
    // }

    return NextResponse.json({
      success: true,
      paymentId: paymentRecord.id,
      status: 'pending_verification',
      message: 'Payment instruction recorded. We will verify and confirm receipt within 1-2 business hours.'
    })

  } catch (error) {
    console.error('Error recording alternative payment:', error)
    
    return NextResponse.json(
      { error: 'Failed to record payment. Please try again.' },
      { status: 500 }
    )
  }
}

// GET endpoint to check payment status
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const paymentId = searchParams.get('payment_id')

    if (!paymentId) {
      return NextResponse.json(
        { error: 'Payment ID required' },
        { status: 400 }
      )
    }

    // In production, you would fetch from database
    // const payment = await getPaymentRecord(paymentId)
    
    // Mock response for demo
    const mockPayment = {
      id: paymentId,
      status: 'pending_verification',
      method: 'zelle',
      amount: 100.00,
      createdAt: new Date().toISOString(),
      verifiedAt: null,
      estimatedVerificationTime: '1-2 business hours'
    }

    return NextResponse.json(mockPayment)

  } catch (error) {
    console.error('Error retrieving payment status:', error)
    
    return NextResponse.json(
      { error: 'Failed to retrieve payment status' },
      { status: 500 }
    )
  }
}
