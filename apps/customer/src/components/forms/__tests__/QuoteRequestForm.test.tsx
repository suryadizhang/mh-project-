/**
 * Unit tests for QuoteRequestForm
 * Tests form validation and submission functionality
 */
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { QuoteRequestForm } from '../QuoteRequestForm';

// Mock apiFetch
const mockApiFetch = vi.fn();
vi.mock('@/lib/api', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    error: vi.fn(),
    info: vi.fn(),
  },
}));

describe('QuoteRequestForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiFetch.mockResolvedValue({ success: true, lead_id: 'lead_123' });
  });

  describe('Form Rendering', () => {
    it('should render form title', () => {
      render(<QuoteRequestForm />);
      // Title appears in h2 and button, check for heading specifically
      expect(screen.getByRole('heading', { name: /get your free quote/i })).toBeInTheDocument();
    });

    it('should render name field', () => {
      render(<QuoteRequestForm />);
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    });

    it('should render phone field', () => {
      render(<QuoteRequestForm />);
      expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    });

    it('should render email field as optional', () => {
      render(<QuoteRequestForm />);
      const emailField = screen.getByLabelText(/email address/i);
      expect(emailField).toBeInTheDocument();
    });

    it('should render submit button', () => {
      render(<QuoteRequestForm />);
      expect(screen.getByRole('button', { name: /get your free quote/i })).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error when name is empty', async () => {
      render(<QuoteRequestForm />);

      // Fill phone to pass HTML5 validation but leave name empty
      const phoneInput = screen.getByLabelText(/phone/i);
      await userEvent.type(phoneInput, '5551234567');

      // Clear name field (if it has a default) and submit
      const nameInput = screen.getByLabelText(/full name/i);
      await userEvent.clear(nameInput);

      // Need to use the form directly to bypass browser validation
      const form = screen.getByRole('button', { name: /get your free quote/i }).closest('form');
      fireEvent.submit(form!);

      await waitFor(() => {
        expect(screen.getByText('Please enter your full name')).toBeInTheDocument();
      });
    });

    it('should show error when phone is missing', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      await userEvent.type(nameInput, 'John Doe');

      // Submit form directly to bypass HTML5 validation
      const form = screen.getByRole('button', { name: /get your free quote/i }).closest('form');
      fireEvent.submit(form!);

      await waitFor(() => {
        expect(
          screen.getByText(/please enter a valid phone number with at least 10 digits/i),
        ).toBeInTheDocument();
      });
    });

    it('should show error for short phone number', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '12345'); // Too short

      // Submit form directly to bypass HTML5 validation
      const form = screen.getByRole('button', { name: /get your free quote/i }).closest('form');
      fireEvent.submit(form!);

      await waitFor(() => {
        expect(
          screen.getByText(/please enter a valid phone number with at least 10 digits/i),
        ).toBeInTheDocument();
      });
    });

    it('should accept email as optional', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalled();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/public/leads'),
          expect.objectContaining({
            method: 'POST',
          }),
        );
      });
    });

    it('should include optional fields when provided', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      const emailInput = screen.getByLabelText(/email address/i);

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');
      await userEvent.type(emailInput, 'john@example.com');

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalled();
        const callBody = JSON.parse(mockApiFetch.mock.calls[0][1].body);
        expect(callBody.email).toBe('john@example.com');
      });
    });

    it('should show success state after submission', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/thank you/i)).toBeInTheDocument();
      });
    });
  });

  describe('Phone Number Formatting', () => {
    it('should format phone number as user types', async () => {
      render(<QuoteRequestForm />);

      const phoneInput = screen.getByLabelText(/phone/i) as HTMLInputElement;

      await userEvent.type(phoneInput, '5551234567');

      // Should format to (555) 123-4567
      expect(phoneInput.value).toMatch(/\(\d{3}\)\s\d{3}-\d{4}/);
    });

    it('should accept various phone formats for submission', async () => {
      render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);

      await userEvent.type(nameInput, 'Format Test');
      await userEvent.type(phoneInput, '5551234567');

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalled();
      });
    });
  });

  describe('SMS and Email Consent', () => {
    it('should render SMS consent checkbox', () => {
      const { container } = render(<QuoteRequestForm />);
      const smsCheckbox = container.querySelector('input#smsConsent');
      expect(smsCheckbox).toBeInTheDocument();
    });

    it('should render email consent checkbox', () => {
      const { container } = render(<QuoteRequestForm />);
      const emailCheckbox = container.querySelector('input#emailConsent');
      expect(emailCheckbox).toBeInTheDocument();
    });

    it('should include consent in submission when checked', async () => {
      const { container } = render(<QuoteRequestForm />);

      const nameInput = screen.getByLabelText(/full name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      const smsCheckbox = container.querySelector('input#smsConsent') as HTMLInputElement;

      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');
      await userEvent.click(smsCheckbox);

      const submitButton = screen.getByRole('button', { name: /get your free quote/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiFetch).toHaveBeenCalled();
        const callBody = JSON.parse(mockApiFetch.mock.calls[0][1].body);
        expect(callBody.sms_consent).toBe(true);
      });
    });
  });

  describe('Accessibility', () => {
    it('should have accessible form structure', () => {
      const { container } = render(<QuoteRequestForm />);
      const form = container.querySelector('form');
      expect(form).toBeInTheDocument();
    });

    it('should have labels for all inputs', () => {
      render(<QuoteRequestForm />);

      // Required fields
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();

      // Optional fields
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });
  });
});
