import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import { headers } from 'next/headers'

// Initialize Stripe with secret key
const stripeSecretKey = process.env.STRIPE_SECRET_KEY
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET

if (!stripeSecretKey) {
  console.warn('⚠️ STRIPE_SECRET_KEY not found in environment variables')
}

if (!webhookSecret) {
  console.warn('⚠️ STRIPE_WEBHOOK_SECRET not found in environment variables')
}

const stripe = stripeSecretKey ? new Stripe(stripeSecretKey, {
  apiVersion: '2025-08-27.basil',
}) : null

export async function POST(request: NextRequest) {
  try {
    // Check if Stripe is configured
    if (!stripe || !webhookSecret) {
      return NextResponse.json(
        { error: 'Webhook processing is not configured' },
        { status: 503 }
      )
    }

    const body = await request.text()
    const headersList = headers()
    const signature = headersList.get('stripe-signature')

    if (!signature) {
      return NextResponse.json(
        { error: 'No signature found' },
        { status: 400 }
      )
    }

    let event: Stripe.Event

    try {
      // Verify webhook signature
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret)
    } catch (err) {
      console.error('⚠️ Webhook signature verification failed:', err)
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 400 }
      )
    }

    // Handle the event
    switch (event.type) {
      case 'payment_intent.succeeded':
        const paymentIntent = event.data.object as Stripe.PaymentIntent
        console.log('💰 Payment succeeded:', paymentIntent.id)
        
        // TODO: Update booking status in database
        // TODO: Send confirmation email to customer
        // TODO: Notify admin of successful payment
        await handlePaymentSuccess(paymentIntent)
        break

      case 'payment_intent.payment_failed':
        const failedPayment = event.data.object as Stripe.PaymentIntent
        console.log('❌ Payment failed:', failedPayment.id)
        
        // TODO: Log failed payment attempt
        // TODO: Notify admin of failed payment
        await handlePaymentFailure(failedPayment)
        break

      case 'payment_intent.canceled':
        const canceledPayment = event.data.object as Stripe.PaymentIntent
        console.log('🚫 Payment canceled:', canceledPayment.id)
        
        // TODO: Handle payment cancellation
        await handlePaymentCancellation(canceledPayment)
        break

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })

  } catch (error) {
    console.error('Error processing webhook:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    )
  }
}

async function handlePaymentSuccess(paymentIntent: Stripe.PaymentIntent) {
  try {
    const { metadata } = paymentIntent
    
    // Log successful payment
    console.log(`[PAYMENT SUCCESS] 
      ID: ${paymentIntent.id}
      Amount: $${(paymentIntent.amount / 100).toFixed(2)}
      Customer: ${metadata.customerName}
      Booking: ${metadata.bookingId}
      Type: ${metadata.paymentType}
    `)

    // TODO: Implement the following in production:
    
    // 1. Update booking status in database
    if (metadata.bookingId && metadata.bookingId !== 'manual-payment') {
      // await updateBookingPaymentStatus(metadata.bookingId, 'paid', paymentIntent.id)
    }

    // 2. Send confirmation email
    // await sendPaymentConfirmationEmail({
    //   email: paymentIntent.receipt_email,
    //   paymentId: paymentIntent.id,
    //   amount: paymentIntent.amount / 100,
    //   customerName: metadata.customerName,
    //   bookingId: metadata.bookingId
    // })

    // 3. Create payment record
    // await createPaymentRecord({
    //   stripePaymentId: paymentIntent.id,
    //   amount: paymentIntent.amount / 100,
    //   currency: paymentIntent.currency,
    //   status: 'completed',
    //   bookingId: metadata.bookingId,
    //   customerName: metadata.customerName,
    //   paymentType: metadata.paymentType,
    //   createdAt: new Date()
    // })

  } catch (error) {
    console.error('Error handling payment success:', error)
  }
}

async function handlePaymentFailure(paymentIntent: Stripe.PaymentIntent) {
  try {
    const { metadata } = paymentIntent
    
    // Log failed payment
    console.log(`[PAYMENT FAILED] 
      ID: ${paymentIntent.id}
      Amount: $${(paymentIntent.amount / 100).toFixed(2)}
      Customer: ${metadata.customerName}
      Booking: ${metadata.bookingId}
      Last Error: ${paymentIntent.last_payment_error?.message || 'Unknown'}
    `)

    // TODO: Implement the following in production:
    
    // 1. Log failed attempt
    // await logFailedPayment({
    //   stripePaymentId: paymentIntent.id,
    //   amount: paymentIntent.amount / 100,
    //   customerName: metadata.customerName,
    //   bookingId: metadata.bookingId,
    //   errorMessage: paymentIntent.last_payment_error?.message,
    //   failureCode: paymentIntent.last_payment_error?.code,
    //   attemptedAt: new Date()
    // })

    // 2. Send admin notification
    // await sendAdminNotification({
    //   type: 'payment_failed',
    //   paymentId: paymentIntent.id,
    //   amount: paymentIntent.amount / 100,
    //   customer: metadata.customerName,
    //   booking: metadata.bookingId
    // })

  } catch (error) {
    console.error('Error handling payment failure:', error)
  }
}

async function handlePaymentCancellation(paymentIntent: Stripe.PaymentIntent) {
  try {
    const { metadata } = paymentIntent
    
    // Log canceled payment
    console.log(`[PAYMENT CANCELED] 
      ID: ${paymentIntent.id}
      Amount: $${(paymentIntent.amount / 100).toFixed(2)}
      Customer: ${metadata.customerName}
      Booking: ${metadata.bookingId}
    `)

    // TODO: Implement the following in production:
    
    // 1. Update booking status if applicable
    // if (metadata.bookingId && metadata.bookingId !== 'manual-payment') {
    //   await updateBookingPaymentStatus(metadata.bookingId, 'payment_canceled', paymentIntent.id)
    // }

    // 2. Send cancellation notification
    // await sendAdminNotification({
    //   type: 'payment_canceled',
    //   paymentId: paymentIntent.id,
    //   amount: paymentIntent.amount / 100,
    //   customer: metadata.customerName,
    //   booking: metadata.bookingId
    // })

  } catch (error) {
    console.error('Error handling payment cancellation:', error)
  }
}
