import { Page, expect } from '@playwright/test';
import { testCustomer, testBooking } from './test-data';

/**
 * Booking Flow Helpers
 */

/**
 * Complete entire booking flow
 */
export async function createBooking(page: Page) {
  // Go to booking page
  await page.goto('/booking');
  
  // Fill customer info
  await page.fill('[name="name"]', testCustomer.name);
  await page.fill('[name="email"]', testCustomer.email);
  await page.fill('[name="phone"]', testCustomer.phone);
  
  // Select event date
  await page.click('[name="eventDate"]');
  await page.fill('[name="eventDate"]', testBooking.eventDate);
  
  // Select guest count
  await page.fill('[name="guestCount"]', testBooking.guestCount.toString());
  
  // Select menu items
  for (const item of testBooking.menuItems) {
    await page.click(`text=${item}`);
  }
  
  // Add special requests
  await page.fill('[name="specialRequests"]', testBooking.specialRequests);
  
  // Submit booking
  await page.click('button:has-text("Submit Booking")');
  
  // Wait for success message
  await page.waitForSelector('text=Booking created successfully', { timeout: 10000 });
  
  // Extract booking ID from success message
  const bookingId = await page.textContent('[data-testid="booking-id"]');
  
  return bookingId;
}

/**
 * Search for booking by ID
 */
export async function searchBooking(page: Page, bookingId: string) {
  await page.goto('/payment');
  
  // Enter booking ID
  await page.fill('[name="bookingId"]', bookingId);
  await page.click('button:has-text("Search")');
  
  // Wait for booking details to load
  await page.waitForSelector('[data-testid="booking-details"]', { timeout: 5000 });
}

/**
 * Verify booking details
 */
export async function verifyBookingDetails(page: Page, expectedDetails: any) {
  const name = await page.textContent('[data-testid="customer-name"]');
  const email = await page.textContent('[data-testid="customer-email"]');
  const eventDate = await page.textContent('[data-testid="event-date"]');
  
  expect(name).toContain(expectedDetails.name);
  expect(email).toContain(expectedDetails.email);
  expect(eventDate).toContain(expectedDetails.eventDate);
}
