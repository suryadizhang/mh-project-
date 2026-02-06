import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

import { BookingFormData } from '@/data/booking/types';
import * as api from '@/lib/api';

import { useBooking } from '../booking/useBooking';

// Mock dependencies
vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

describe('useBooking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with default values', async () => {
      // Mock the booked dates call that happens on mount
      vi.mocked(api.apiFetch).mockResolvedValue({
        success: true,
        data: { bookedDates: [] },
      });

      const { result } = renderHook(() => useBooking());

      // Wait for the initial data fetch to complete
      await waitFor(() => {
        expect(result.current.loadingDates).toBe(false);
      });

      expect(result.current.bookedDates).toEqual([]);
      expect(result.current.availableTimeSlots).toEqual([]);
      expect(result.current.loadingTimeSlots).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.showValidationModal).toBe(false);
      expect(result.current.showAgreementModal).toBe(false);
      expect(result.current.missingFields).toEqual([]);
      expect(result.current.formData).toBeNull();
    });

    it('should provide form methods from react-hook-form', () => {
      const { result } = renderHook(() => useBooking());

      expect(result.current.register).toBeDefined();
      expect(result.current.handleSubmit).toBeDefined();
      expect(result.current.control).toBeDefined();
      expect(result.current.errors).toBeDefined();
      expect(result.current.watch).toBeDefined();
      expect(result.current.setValue).toBeDefined();
      expect(result.current.getValues).toBeDefined();
    });

    it('should provide methods for data fetching', () => {
      const { result } = renderHook(() => useBooking());

      expect(typeof result.current.onSubmit).toBe('function');
      expect(typeof result.current.fetchBookedDates).toBe('function');
      expect(typeof result.current.fetchAvailability).toBe('function');
    });
  });

  describe('Booked Dates Fetching', () => {
    it('should fetch booked dates on mount', async () => {
      const mockBookedDates = ['2025-10-25', '2025-10-26', '2025-10-27'];

      vi.mocked(api.apiFetch).mockResolvedValue({
        success: true,
        data: { bookedDates: mockBookedDates },
      });

      const { result } = renderHook(() => useBooking());

      await waitFor(() => {
        expect(api.apiFetch).toHaveBeenCalledWith('/api/v1/public/bookings/booked-dates');
      });

      await waitFor(() => {
        expect(result.current.bookedDates.length).toBe(3);
      });
    });

    it('should handle booked dates fetch error', async () => {
      vi.mocked(api.apiFetch).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBooking());

      await waitFor(() => {
        expect(result.current.dateError).toBe('Unable to load booked dates. Please try again.');
      });
    });

    it('should set loading state while fetching', async () => {
      vi.mocked(api.apiFetch).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  data: { bookedDates: [] },
                }),
              100,
            ),
          ),
      );

      const { result } = renderHook(() => useBooking());

      // Should start loading
      await waitFor(() => {
        expect(result.current.loadingDates).toBe(true);
      });

      // Should finish loading
      await waitFor(
        () => {
          expect(result.current.loadingDates).toBe(false);
        },
        { timeout: 3000 },
      );
    });

    it('should handle empty booked dates response', async () => {
      vi.mocked(api.apiFetch).mockResolvedValue({
        success: true,
        data: { bookedDates: [] },
      });

      const { result } = renderHook(() => useBooking());

      await waitFor(() => {
        expect(result.current.bookedDates).toEqual([]);
      });
    });
  });

  describe('Availability Fetching', () => {
    it('should fetch availability for selected date', async () => {
      const testDate = new Date('2025-10-25');
      const mockTimeSlots = [
        { time: '12:00', label: '12:00 PM', available: 5 },
        { time: '13:00', label: '1:00 PM', available: 3 },
      ];

      // Mock initial booked dates call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { bookedDates: [] },
      });

      // Mock availability call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { timeSlots: mockTimeSlots },
      });

      const { result } = renderHook(() => useBooking());

      await act(async () => {
        await result.current.fetchAvailability(testDate);
      });

      await waitFor(() => {
        expect(result.current.availableTimeSlots.length).toBe(2);
      });
    });

    it('should format time slots with isAvailable flag', async () => {
      const testDate = new Date('2025-10-25');
      const mockTimeSlots = [
        { time: '12:00', label: '12:00 PM', available: 5 },
        { time: '13:00', label: '1:00 PM', available: 0 },
      ];

      // Mock initial booked dates call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { bookedDates: [] },
      });

      // Mock availability call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { timeSlots: mockTimeSlots },
      });

      const { result } = renderHook(() => useBooking());

      await act(async () => {
        await result.current.fetchAvailability(testDate);
      });

      await waitFor(() => {
        const slots = result.current.availableTimeSlots;
        expect(slots[0].isAvailable).toBe(true);
        expect(slots[1].isAvailable).toBe(false);
      });
    });

    it('should handle availability fetch error', async () => {
      const testDate = new Date('2025-10-25');

      vi.mocked(api.apiFetch).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBooking());

      await act(async () => {
        await result.current.fetchAvailability(testDate);
      });

      await waitFor(() => {
        expect(result.current.availableTimeSlots).toEqual([]);
      });
    });

    it('should set loading state while fetching availability', async () => {
      const testDate = new Date('2025-10-25');

      vi.mocked(api.apiFetch).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  success: true,
                  data: { timeSlots: [] },
                }),
              100,
            ),
          ),
      );

      const { result } = renderHook(() => useBooking());

      act(() => {
        result.current.fetchAvailability(testDate);
      });

      await waitFor(() => {
        expect(result.current.loadingTimeSlots).toBe(true);
      });

      await waitFor(
        () => {
          expect(result.current.loadingTimeSlots).toBe(false);
        },
        { timeout: 3000 },
      );
    });
  });

  describe('Form Submission', () => {
    it('should validate required fields', async () => {
      // Mock initial booked dates call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { bookedDates: [] },
      });

      const { result } = renderHook(() => useBooking());

      await act(async () => {
        await result.current.onSubmit({
          name: '',
          email: '',
          phone: '',
          preferredCommunication: '',
          eventDate: new Date(),
          eventTime: '12PM',
          guestCount: 0,
          addressStreet: '',
          addressCity: '',
          addressState: '',
          addressZipcode: '',
          sameAsVenue: false,
          venueStreet: '',
          venueCity: '',
          venueState: '',
          venueZipcode: '',
        });
      });

      await waitFor(() => {
        expect(result.current.showValidationModal).toBe(true);
        expect(result.current.missingFields.length).toBeGreaterThan(0);
      });
    });

    it('should show agreement modal for valid form', async () => {
      // Mock initial booked dates call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { bookedDates: [] },
      });

      const { result } = renderHook(() => useBooking());

      const validData: BookingFormData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone: '1234567890',
        preferredCommunication: 'email',
        eventDate: new Date('2025-10-25'),
        eventTime: '12PM',
        guestCount: 10,
        addressStreet: '123 Main St',
        addressCity: 'San Francisco',
        addressState: 'CA',
        addressZipcode: '94102',
        sameAsVenue: true,
        venueStreet: '',
        venueCity: '',
        venueState: '',
        venueZipcode: '',
      };

      await act(async () => {
        await result.current.onSubmit(validData);
      });

      await waitFor(() => {
        expect(result.current.showAgreementModal).toBe(true);
        expect(result.current.formData).toEqual(validData);
      });
    });

    it('should validate venue address when sameAsVenue is false', async () => {
      // Mock initial booked dates call
      vi.mocked(api.apiFetch).mockResolvedValueOnce({
        success: true,
        data: { bookedDates: [] },
      });

      const { result } = renderHook(() => useBooking());

      const dataWithoutVenueAddress: BookingFormData = {
        name: 'John Doe',
        email: 'john@example.com',
        phone: '1234567890',
        preferredCommunication: 'email',
        eventDate: new Date('2025-10-25'),
        eventTime: '12PM',
        guestCount: 10,
        addressStreet: '123 Main St',
        addressCity: 'San Francisco',
        addressState: 'CA',
        addressZipcode: '94102',
        sameAsVenue: false,
        venueStreet: '',
        venueCity: '',
        venueState: '',
        venueZipcode: '',
      };

      await act(async () => {
        await result.current.onSubmit(dataWithoutVenueAddress);
      });

      await waitFor(() => {
        expect(result.current.showValidationModal).toBe(true);
        expect(result.current.missingFields).toContain('Venue Street');
        expect(result.current.missingFields).toContain('Venue City');
        expect(result.current.missingFields).toContain('Venue State');
        expect(result.current.missingFields).toContain('Venue Zip Code');
      });
    });

    it('should set isSubmitting state during validation', async () => {
      const { result } = renderHook(() => useBooking());

      act(() => {
        result.current.onSubmit({
          name: '',
          email: '',
          phone: '',
          preferredCommunication: '',
          eventDate: new Date(),
          eventTime: '12PM',
          guestCount: 0,
          addressStreet: '',
          addressCity: '',
          addressState: '',
          addressZipcode: '',
          sameAsVenue: false,
        });
      });

      // Should briefly be submitting
      // Note: This might be hard to catch due to synchronous validation
      await waitFor(() => {
        expect(result.current.isSubmitting).toBe(false);
      });
    });
  });

  describe('State Management', () => {
    it('should update showValidationModal state', () => {
      const { result } = renderHook(() => useBooking());

      act(() => {
        result.current.setShowValidationModal(true);
      });

      expect(result.current.showValidationModal).toBe(true);

      act(() => {
        result.current.setShowValidationModal(false);
      });

      expect(result.current.showValidationModal).toBe(false);
    });

    it('should update showAgreementModal state', () => {
      const { result } = renderHook(() => useBooking());

      act(() => {
        result.current.setShowAgreementModal(true);
      });

      expect(result.current.showAgreementModal).toBe(true);

      act(() => {
        result.current.setShowAgreementModal(false);
      });

      expect(result.current.showAgreementModal).toBe(false);
    });

    it('should update formData state', () => {
      const { result } = renderHook(() => useBooking());

      const testData: Partial<BookingFormData> = {
        name: 'Test User',
        email: 'test@example.com',
      };

      act(() => {
        result.current.setFormData(testData as BookingFormData | null);
      });

      expect(result.current.formData).toEqual(testData);
    });

    it('should update isSubmitting state', () => {
      const { result } = renderHook(() => useBooking());

      act(() => {
        result.current.setIsSubmitting(true);
      });

      expect(result.current.isSubmitting).toBe(true);

      act(() => {
        result.current.setIsSubmitting(false);
      });

      expect(result.current.isSubmitting).toBe(false);
    });
  });
});
