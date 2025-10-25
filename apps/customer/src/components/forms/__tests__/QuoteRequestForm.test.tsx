/**
 * Unit tests for QuoteRequestForm
 * Tests newsletter auto-subscribe functionality
 */
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { QuoteRequestForm } from '../QuoteRequestForm';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch as unknown as typeof fetch;

describe('QuoteRequestForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, lead_id: 'lead_123' }),
    } as Response);
  });

  describe('Auto-Subscribe Notice Display', () => {
    it('should display auto-subscribe notice', () => {
      render(<QuoteRequestForm />);
      
      const notice = screen.getByText(/submitting this form, you'll be automatically subscribed/i);
      expect(notice).toBeInTheDocument();
    });

    it('should not display consent checkboxes', () => {
      render(<QuoteRequestForm />);
      
      // Old consent checkboxes should not exist
      expect(screen.queryByText(/I consent to receive SMS/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/I consent to receive email/i)).not.toBeInTheDocument();
    });

    it('should display STOP instructions', () => {
      render(<QuoteRequestForm />);
      
      const stopInstructions = screen.getByText(/Reply STOP to unsubscribe/i);
      expect(stopInstructions).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should require name field', async () => {
      render(<QuoteRequestForm />);
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });

    it('should require phone field', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      await userEvent.type(nameInput, 'John Doe');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/phone is required/i)).toBeInTheDocument();
      });
    });

    it('should accept email as optional', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/public/leads'),
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });

    it('should validate phone format', async () => {
      render(<QuoteRequestForm />);
      
      const phoneInput = screen.getByLabelText(/phone/i);
      await userEvent.type(phoneInput, '123'); // Too short
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/phone number is invalid/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      const emailInput = screen.getByLabelText(/email/i);
      
      await userEvent.type(nameInput, 'John Doe');
      await userEvent.type(phoneInput, '5551234567');
      await userEvent.type(emailInput, 'john@example.com');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/public/leads'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
            }),
            body: expect.stringContaining('John Doe'),
          })
        );
      });
    });

    it('should submit with phone-only (no email)', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Jane Smith');
      await userEvent.type(phoneInput, '5559876543');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        const fetchCall = mockFetch.mock.calls[0];
        const body = JSON.parse(fetchCall[1].body as string);
        
        expect(body.name).toBe('Jane Smith');
        expect(body.phone).toBe('5559876543');
        expect(body.email).toBeUndefined();
      });
    });

    it('should include source field in payload', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Test User');
      await userEvent.type(phoneInput, '5551111111');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        const fetchCall = mockFetch.mock.calls[0];
        const body = JSON.parse(fetchCall[1].body as string);
        
        expect(body.source).toBe('quote');
      });
    });

    it('should display success message after submission', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Success Test');
      await userEvent.type(phoneInput, '5551234567');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/thank you for your request/i)).toBeInTheDocument();
      });
    });

    it('should display error message on submission failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error' }),
      } as Response);
      
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Error Test');
      await userEvent.type(phoneInput, '5551234567');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/error.*submitting/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during submission', async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );
      
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Loading Test');
      await userEvent.type(phoneInput, '5551234567');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      expect(screen.getByRole('button', { name: /submitting/i })).toBeDisabled();
    });

    it('should disable form during submission', async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );
      
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      
      await userEvent.type(nameInput, 'Disable Test');
      await userEvent.type(phoneInput, '5551234567');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      expect(nameInput).toBeDisabled();
      expect(phoneInput).toBeDisabled();
    });
  });

  describe('Honeypot Protection', () => {
    it('should include hidden honeypot field', () => {
      const { container } = render(<QuoteRequestForm />);
      
      const honeypot = container.querySelector('input[name="honeypot"]');
      expect(honeypot).toBeInTheDocument();
      expect(honeypot).toHaveAttribute('type', 'text');
      expect(honeypot).toHaveStyle({ display: 'none' });
    });

    it('should not submit if honeypot is filled', async () => {
      render(<QuoteRequestForm />);
      
      const nameInput = screen.getByLabelText(/name/i);
      const phoneInput = screen.getByLabelText(/phone/i);
      const honeypot = document.querySelector('input[name="honeypot"]') as HTMLInputElement;
      
      await userEvent.type(nameInput, 'Bot Test');
      await userEvent.type(phoneInput, '5551234567');
      
      // Simulate bot filling honeypot
      fireEvent.change(honeypot, { target: { value: 'I am a bot' } });
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      // Should not call fetch if honeypot is filled
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('Phone Number Formatting', () => {
    it('should accept various phone formats', async () => {
      const phoneFormats = [
        '5551234567',
        '(555) 123-4567',
        '555-123-4567',
        '1-555-123-4567',
      ];
      
      for (const format of phoneFormats) {
        vi.clearAllMocks();
        
        const { unmount } = render(<QuoteRequestForm />);
        
        const nameInput = screen.getByLabelText(/name/i);
        const phoneInput = screen.getByLabelText(/phone/i);
        
        await userEvent.type(nameInput, 'Format Test');
        await userEvent.type(phoneInput, format);
        
        const submitButton = screen.getByRole('button', { name: /submit/i });
        fireEvent.click(submitButton);
        
        await waitFor(() => {
          expect(global.fetch).toHaveBeenCalled();
        });
        
        unmount();
      }
    });
  });
});
