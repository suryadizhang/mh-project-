/**
 * BookingForm Component Tests
 * 
 * Tests the critical booking flow component including:
 * - Form rendering and initial state
 * - User input handling and validation
 * - Form submission (success and error cases)
 * - Loading states and disabled buttons
 * - Required field validation
 */

import React from 'react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import BookingForm from '../BookingForm'

// Mock dependencies
vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn()
}))

vi.mock('@/lib/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn()
  }
}))

import { apiFetch } from '@/lib/api'
import { logger } from '@/lib/logger'

describe('BookingForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Form Rendering', () => {
    it('should render all form fields', () => {
      render(<BookingForm />)

      // Check labels and inputs
      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/phone/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/event date/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/guest count/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/event location/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/special requests/i)).toBeInTheDocument()
    })

    it('should render submit button with correct initial text', () => {
      render(<BookingForm />)

      const submitButton = screen.getByRole('button', { name: /book my hibachi experience/i })
      expect(submitButton).toBeInTheDocument()
      expect(submitButton).toBeEnabled()
    })

    it('should render with custom className', () => {
      const { container } = render(<BookingForm className="custom-class" />)

      const formContainer = container.firstChild as HTMLElement
      expect(formContainer.className).toContain('custom-class')
    })

    it('should render form title', () => {
      render(<BookingForm />)

      expect(screen.getByText(/book your hibachi experience/i)).toBeInTheDocument()
    })

    it('should mark required fields with asterisks', () => {
      render(<BookingForm />)

      // Required fields should have * in their labels
      expect(screen.getByText(/name \*/i)).toBeInTheDocument()
      expect(screen.getByText(/email \*/i)).toBeInTheDocument()
      expect(screen.getByText(/phone \*/i)).toBeInTheDocument()
      expect(screen.getByText(/event date \*/i)).toBeInTheDocument()
      expect(screen.getByText(/guest count \*/i)).toBeInTheDocument()
      expect(screen.getByText(/event location \*/i)).toBeInTheDocument()
    })
  })

  describe('Form Input Handling', () => {
    it('should update name field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement

      await user.type(nameInput, 'John Doe')

      expect(nameInput.value).toBe('John Doe')
    })

    it('should update email field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement

      await user.type(emailInput, 'john@example.com')

      expect(emailInput.value).toBe('john@example.com')
    })

    it('should update phone field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const phoneInput = screen.getByLabelText(/phone/i) as HTMLInputElement

      await user.type(phoneInput, '555-1234')

      expect(phoneInput.value).toBe('555-1234')
    })

    it('should update event date field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const dateInput = screen.getByLabelText(/event date/i) as HTMLInputElement

      await user.type(dateInput, '2025-12-31')

      expect(dateInput.value).toBe('2025-12-31')
    })

    it('should update guest count field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const guestInput = screen.getByLabelText(/guest count/i) as HTMLInputElement

      await user.clear(guestInput)
      await user.type(guestInput, '10')

      expect(guestInput.value).toBe('10')
    })

    it('should update location field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const locationInput = screen.getByLabelText(/event location/i) as HTMLInputElement

      await user.type(locationInput, '123 Main St, City, State 12345')

      expect(locationInput.value).toBe('123 Main St, City, State 12345')
    })

    it('should update special requests field on user input', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const requestsInput = screen.getByLabelText(/special requests/i) as HTMLTextAreaElement

      await user.type(requestsInput, 'Vegetarian menu please')

      expect(requestsInput.value).toBe('Vegetarian menu please')
    })

    it('should handle multiple field updates', async () => {
      const user = userEvent.setup()
      render(<BookingForm />)

      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
      const phoneInput = screen.getByLabelText(/phone/i) as HTMLInputElement

      await user.type(nameInput, 'Jane Smith')
      await user.type(emailInput, 'jane@example.com')
      await user.type(phoneInput, '555-5678')

      expect(nameInput.value).toBe('Jane Smith')
      expect(emailInput.value).toBe('jane@example.com')
      expect(phoneInput.value).toBe('555-5678')
    })
  })

  describe('Form Validation', () => {
    it('should have required attribute on name field', () => {
      render(<BookingForm />)

      const nameInput = screen.getByLabelText(/name/i)
      expect(nameInput).toHaveAttribute('required')
    })

    it('should have required attribute on email field', () => {
      render(<BookingForm />)

      const emailInput = screen.getByLabelText(/email/i)
      expect(emailInput).toHaveAttribute('required')
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should have required attribute on phone field', () => {
      render(<BookingForm />)

      const phoneInput = screen.getByLabelText(/phone/i)
      expect(phoneInput).toHaveAttribute('required')
      expect(phoneInput).toHaveAttribute('type', 'tel')
    })

    it('should have min and max constraints on guest count', () => {
      render(<BookingForm />)

      const guestInput = screen.getByLabelText(/guest count/i)
      expect(guestInput).toHaveAttribute('type', 'number')
      expect(guestInput).toHaveAttribute('min', '1')
      expect(guestInput).toHaveAttribute('max', '50')
      expect(guestInput).toHaveAttribute('required')
    })

    it('should have date type on event date field', () => {
      render(<BookingForm />)

      const dateInput = screen.getByLabelText(/event date/i)
      expect(dateInput).toHaveAttribute('type', 'date')
      expect(dateInput).toHaveAttribute('required')
    })

    it('should have required attribute on location field', () => {
      render(<BookingForm />)

      const locationInput = screen.getByLabelText(/event location/i)
      expect(locationInput).toHaveAttribute('required')
    })

    it('should NOT have required attribute on special requests', () => {
      render(<BookingForm />)

      const requestsInput = screen.getByLabelText(/special requests/i)
      expect(requestsInput).not.toHaveAttribute('required')
    })
  })

  describe('Form Submission - Success', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      mockApiFetch.mockResolvedValue({ success: true, data: { id: '123' } })

      render(<BookingForm />)

      // Fill out form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.clear(screen.getByLabelText(/guest count/i))
      await user.type(screen.getByLabelText(/guest count/i), '10')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')

      // Submit form
      await user.click(screen.getByRole('button', { name: /book my hibachi experience/i }))

      // Verify API call
      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalledWith(
          '/api/v1/bookings',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('John Doe')
          })
        )
      })
    })

    it('should show loading state during submission', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      
      // Mock API with delay to capture loading state
      mockApiFetch.mockImplementation(() => 
        new Promise(resolve => {
          setTimeout(() => resolve({ success: true, data: { id: '123' } }), 100)
        })
      )

      render(<BookingForm />)

      // Fill out form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')

      // Submit form
      const submitButton = screen.getByRole('button')
      await user.click(submitButton)

      // Should show loading state
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
        expect(submitButton).toHaveTextContent(/submitting/i)
      })

      // Wait for submission to complete
      await waitFor(() => {
        expect(submitButton).toBeEnabled()
        expect(submitButton).toHaveTextContent(/book my hibachi experience/i)
      })
    })

    it('should disable submit button during submission', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      mockApiFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true, data: {} }), 100))
      )

      render(<BookingForm />)

      // Fill minimum required fields
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')

      const submitButton = screen.getByRole('button')
      await user.click(submitButton)

      // Button should be disabled
      expect(submitButton).toBeDisabled()

      // Wait for completion
      await waitFor(() => {
        expect(submitButton).toBeEnabled()
      })
    })

    it('should log success message on successful submission', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      const mockLogger = vi.mocked(logger)
      mockApiFetch.mockResolvedValue({ success: true, data: { id: '123' } })

      render(<BookingForm />)

      // Fill and submit form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')
      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(mockLogger.info).toHaveBeenCalledWith('Booking created')
      })
    })

    it('should include special requests in submission if provided', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      mockApiFetch.mockResolvedValue({ success: true, data: {} })

      render(<BookingForm />)

      // Fill form including special requests
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')
      await user.type(screen.getByLabelText(/special requests/i), 'Gluten-free menu')
      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalledWith(
          '/api/v1/bookings',
          expect.objectContaining({
            body: expect.stringContaining('Gluten-free menu')
          })
        )
      })
    })
  })

  describe('Form Submission - Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      const mockLogger = vi.mocked(logger)
      mockApiFetch.mockRejectedValue(new Error('API Error'))

      render(<BookingForm />)

      // Fill and submit form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')
      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(mockLogger.error).toHaveBeenCalledWith(
          'Error creating booking',
          expect.any(Error)
        )
      })
    })

    it('should re-enable submit button after error', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      mockApiFetch.mockImplementation(() =>
        new Promise((_, reject) => setTimeout(() => reject(new Error('API Error')), 50))
      )

      render(<BookingForm />)

      // Fill and submit form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')

      const submitButton = screen.getByRole('button')
      await user.click(submitButton)

      // Should be disabled during submission
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })

      // Should be re-enabled after error
      await waitFor(() => {
        expect(submitButton).toBeEnabled()
      }, { timeout: 3000 })
    })

    it('should allow retry after failed submission', async () => {
      const user = userEvent.setup()
      const mockApiFetch = vi.mocked(apiFetch)
      
      // First call fails, second succeeds
      mockApiFetch
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce({ success: true, data: { id: '123' } })

      render(<BookingForm />)

      // Fill form
      await user.type(screen.getByLabelText(/name/i), 'John Doe')
      await user.type(screen.getByLabelText(/email/i), 'john@example.com')
      await user.type(screen.getByLabelText(/phone/i), '555-1234')
      await user.type(screen.getByLabelText(/event date/i), '2025-12-31')
      await user.type(screen.getByLabelText(/event location/i), '123 Main St')

      const submitButton = screen.getByRole('button')

      // First submission fails
      await user.click(submitButton)
      await waitFor(() => {
        expect(submitButton).toBeEnabled()
      })

      // Retry submission
      await user.click(submitButton)
      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Initial State', () => {
    it('should have empty string initial values for text fields', () => {
      render(<BookingForm />)

      expect(screen.getByLabelText(/name/i)).toHaveValue('')
      expect(screen.getByLabelText(/email/i)).toHaveValue('')
      expect(screen.getByLabelText(/phone/i)).toHaveValue('')
      expect(screen.getByLabelText(/event date/i)).toHaveValue('')
      expect(screen.getByLabelText(/event location/i)).toHaveValue('')
      expect(screen.getByLabelText(/special requests/i)).toHaveValue('')
    })

    it('should have initial guest count of 1', () => {
      render(<BookingForm />)

      expect(screen.getByLabelText(/guest count/i)).toHaveValue(1)
    })

    it('should have submit button enabled initially', () => {
      render(<BookingForm />)

      expect(screen.getByRole('button')).toBeEnabled()
    })
  })
})
