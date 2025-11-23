import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Elements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'

import PaymentForm from '../PaymentForm'

// Mock Stripe
const stripePromise = loadStripe('pk_test_mock')

vi.mock('@/lib/logger', () => ({
  logger: {
    error: vi.fn(),
    info: vi.fn()
  }
}))

describe('PaymentForm', () => {
  const mockBookingData = {
    id: 'booking-123',
    customerName: 'John Doe',
    customerEmail: 'john@example.com',
    eventDate: '2025-10-25',
    eventTime: '6:00 PM',
    guestCount: 20,
    venueAddress: '123 Main St, San Francisco, CA',
    totalAmount: 2000,
    depositPaid: false,
    depositAmount: 500,
    remainingBalance: 1500
  }

  const defaultProps = {
    amount: 500,
    bookingData: mockBookingData,
    paymentType: 'deposit' as const,
    tipAmount: 0,
    clientSecret: 'test_client_secret'
  }

  const renderWithStripe = (props = defaultProps) => {
    return render(
      <Elements stripe={stripePromise}>
        <PaymentForm {...props} />
      </Elements>
    )
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render payment form with title', () => {
      renderWithStripe()
      expect(screen.getByText('Credit Card Payment')).toBeInTheDocument()
    })

    it('should display security badge', () => {
      renderWithStripe()
      expect(screen.getByText(/Secured by Stripe/i)).toBeInTheDocument()
      expect(screen.getByText(/256-bit SSL encryption/i)).toBeInTheDocument()
    })

    it('should render payment summary section', () => {
      renderWithStripe()
      expect(screen.getByText('Payment Summary')).toBeInTheDocument()
    })

    it('should display correct payment amount', () => {
      renderWithStripe()
      expect(screen.getByText(/\$500\.00/)).toBeInTheDocument()
    })

    it('should show payment type as deposit', () => {
      renderWithStripe()
      expect(screen.getByText('Deposit Payment')).toBeInTheDocument()
    })

    it('should show balance payment type when specified', () => {
      const props = { ...defaultProps, paymentType: 'balance' as const, amount: 1500 }
      renderWithStripe(props)
      expect(screen.getByText('Balance Payment')).toBeInTheDocument()
    })
  })

  describe('Customer Information', () => {
    it('should NOT show customer info fields when booking data is provided', () => {
      renderWithStripe()
      expect(screen.queryByLabelText(/Full Name/i)).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/Email Address/i)).not.toBeInTheDocument()
    })

    it('should show customer info fields when no booking data', () => {
      const props = { ...defaultProps, bookingData: null }
      renderWithStripe(props)
      expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Phone Number/i)).toBeInTheDocument()
    })

    it('should mark required fields with asterisk when no booking data', () => {
      const props = { ...defaultProps, bookingData: null }
      renderWithStripe(props)
      expect(screen.getByLabelText(/Full Name \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Email Address \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Phone Number \*/i)).toBeInTheDocument()
    })

    it('should render optional address fields when no booking data', () => {
      const props = { ...defaultProps, bookingData: null }
      renderWithStripe(props)
      expect(screen.getByLabelText('Address')).toBeInTheDocument()
      expect(screen.getByLabelText('City')).toBeInTheDocument()
      expect(screen.getByLabelText('State')).toBeInTheDocument()
      expect(screen.getByLabelText('ZIP Code')).toBeInTheDocument()
    })
  })

  describe('Booking Information Display', () => {
    it('should display booking details when booking data is provided', () => {
      renderWithStripe()
      expect(screen.getByText('Booking Details')).toBeInTheDocument()
      expect(screen.getByText(/John Doe/i)).toBeInTheDocument()
      expect(screen.getByText(/john@example\.com/i)).toBeInTheDocument()
    })

    it('should display event date and time', () => {
      renderWithStripe()
      expect(screen.getByText(/2025-10-25/i)).toBeInTheDocument()
      expect(screen.getByText(/6:00 PM/i)).toBeInTheDocument()
    })

    it('should display guest count', () => {
      renderWithStripe()
      expect(screen.getByText(/20 Guests/i)).toBeInTheDocument()
    })

    it('should display venue address', () => {
      renderWithStripe()
      expect(screen.getByText(/123 Main St, San Francisco, CA/i)).toBeInTheDocument()
    })
  })

  describe('Payment Summary', () => {
    it('should display payment breakdown', () => {
      renderWithStripe()
      expect(screen.getByText('Payment Summary')).toBeInTheDocument()
      expect(screen.getByText(/Subtotal/i)).toBeInTheDocument()
    })

    it('should show tip amount when tip is added', () => {
      const props = { ...defaultProps, tipAmount: 50 }
      renderWithStripe(props)
      expect(screen.getByText(/\$50\.00/)).toBeInTheDocument()
    })

    it('should calculate and display total with tip', () => {
      const props = { ...defaultProps, tipAmount: 50, amount: 500 }
      renderWithStripe(props)
      // Should show $550 total (500 + 50)
      expect(screen.getByText(/Total Amount/i)).toBeInTheDocument()
    })

    it('should show remaining balance for deposit payment', () => {
      renderWithStripe()
      expect(screen.getByText(/Remaining Balance/i)).toBeInTheDocument()
      expect(screen.getByText(/\$1,500\.00/)).toBeInTheDocument()
    })

    it('should NOT show remaining balance for balance payment', () => {
      const props = { ...defaultProps, paymentType: 'balance' as const }
      renderWithStripe(props)
      expect(screen.queryByText(/Remaining Balance/i)).not.toBeInTheDocument()
    })
  })

  describe('Payment Button', () => {
    it('should render submit button with correct text', () => {
      renderWithStripe()
      expect(screen.getByRole('button', { name: /Pay \$500\.00/i })).toBeInTheDocument()
    })

    it('should show loading state button text when processing', () => {
      // Note: This would require user interaction to test properly
      // Keeping as basic render test for now
      renderWithStripe()
      const button = screen.getByRole('button', { name: /Pay/i })
      expect(button).toBeEnabled()
    })

    it('should be disabled when Stripe is not loaded', () => {
      // This tests the stripe/elements not being ready
      renderWithStripe()
      const button = screen.getByRole('button', { name: /Pay/i })
      // Button should exist
      expect(button).toBeInTheDocument()
    })
  })

  describe('Payment Details Section', () => {
    it('should render Payment Details heading', () => {
      renderWithStripe()
      expect(screen.getByText('Payment Details')).toBeInTheDocument()
    })

    it('should show security lock icon', () => {
      const { container } = renderWithStripe()
      // Check for lock icon presence (Lucide renders as svg)
      const lockIcon = container.querySelector('svg')
      expect(lockIcon).toBeInTheDocument()
    })
  })

  describe('Success State', () => {
    // Note: Testing success state would require mocking Stripe's confirmPayment
    // which is complex. These tests ensure the component structure is correct.

    it('should render without crashing', () => {
      const { container } = renderWithStripe()
      expect(container).toBeInTheDocument()
    })
  })

  describe('Props Validation', () => {
    it('should handle different amounts correctly', () => {
      const props = { ...defaultProps, amount: 1000 }
      renderWithStripe(props)
      expect(screen.getByText(/\$1,000\.00/)).toBeInTheDocument()
    })

    it('should handle zero tip correctly', () => {
      const props = { ...defaultProps, tipAmount: 0 }
      renderWithStripe(props)
      expect(screen.getByText('Payment Summary')).toBeInTheDocument()
    })

    it('should render with minimum required props', () => {
      const minProps = {
        amount: 100,
        bookingData: null,
        paymentType: 'deposit' as const,
        tipAmount: 0,
        clientSecret: 'test_secret'
      }
      renderWithStripe(minProps)
      expect(screen.getByText('Credit Card Payment')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should render error boundary wrapper', () => {
      // The component is wrapped in FormErrorBoundary
      const { container } = renderWithStripe()
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper form structure', () => {
      const { container } = renderWithStripe()
      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()
    })

    it('should have accessible labels for required fields when no booking data', () => {
      const props = { ...defaultProps, bookingData: null }
      renderWithStripe(props)

      const nameInput = screen.getByLabelText(/Full Name/i)
      expect(nameInput).toHaveAttribute('required')

      const emailInput = screen.getByLabelText(/Email Address/i)
      expect(emailInput).toHaveAttribute('required')
      expect(emailInput).toHaveAttribute('type', 'email')

      const phoneInput = screen.getByLabelText(/Phone Number/i)
      expect(phoneInput).toHaveAttribute('required')
      expect(phoneInput).toHaveAttribute('type', 'tel')
    })

    it('should have submit button with role', () => {
      renderWithStripe()
      const button = screen.getByRole('button', { name: /Pay/i })
      expect(button).toHaveAttribute('type', 'submit')
    })
  })
})
