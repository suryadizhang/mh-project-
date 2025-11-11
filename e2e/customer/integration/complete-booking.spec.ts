import { test, expect } from '@playwright/test';
import { 
  testCustomer, 
  testBooking, 
  testPayment, 
  calculateTotal 
} from '../../helpers/test-data';
import { createBooking } from '../../helpers/booking-helpers';
import { completeStripePayment, addTip } from '../../helpers/payment-helpers';

/**
 * Complete End-to-End Booking with Payment
 * 
 * This test simulates the entire customer journey:
 * 1. Create a booking
 * 2. Navigate to payment
 * 3. Complete Stripe payment
 * 4. Verify confirmation
 * 
 * Tags: @e2e @critical @slow
 * Services needed: Frontend, Backend, Database, Stripe
 */
test.describe('Complete Booking Flow', () => {
  test('customer can create booking and complete payment @e2e @critical', async ({ page }) => {
    // Step 1: Create booking
    test.step('Create booking', async () => {
      const bookingId = await createBooking(page);
      expect(bookingId).toBeTruthy();
      
      // Store booking ID for next steps
      test.info().annotations.push({ type: 'bookingId', description: bookingId! });
    });
    
    // Step 2: Navigate to payment
    test.step('Navigate to payment', async () => {
      await page.click('text=Proceed to Payment');
      await expect(page).toHaveURL(/.*payment/);
    });
    
    // Step 3: Select deposit payment
    test.step('Select deposit payment', async () => {
      await page.click('text=Deposit');
      await expect(page.locator('[data-testid="amount"]')).toContainText('$100');
    });
    
    // Step 4: Add tip
    test.step('Add 20% tip', async () => {
      await addTip(page, 20);
      
      // Verify tip calculation
      const tipAmount = await page.textContent('[data-testid="tip-amount"]');
      expect(tipAmount).toContain('$20');
    });
    
    // Step 5: Complete payment
    test.step('Complete Stripe payment', async () => {
      const total = 100 + 20; // deposit + tip
      const { total: totalWithFee } = calculateTotal(total, 'stripe');
      
      await completeStripePayment(page, totalWithFee);
    });
    
    // Step 6: Verify confirmation
    test.step('Verify payment confirmation', async () => {
      await expect(page.locator('h1')).toContainText('Payment Successful');
      await expect(page.locator('text=Confirmation email sent')).toBeVisible();
      
      // Screenshot for proof
      await page.screenshot({ path: 'test-results/booking-success.png' });
    });
  });
  
  test('customer can see booking history @e2e', async ({ page }) => {
    // Create booking first
    const bookingId = await createBooking(page);
    
    // Navigate to booking history
    await page.goto('/my-bookings');
    
    // Verify booking appears
    await expect(page.locator(`[data-booking-id="${bookingId}"]`)).toBeVisible();
  });
  
  test('handles invalid booking data gracefully @e2e', async ({ page }) => {
    await page.goto('/booking');
    
    // Try to submit without required fields
    await page.click('button:has-text("Submit Booking")');
    
    // Verify error messages
    await expect(page.locator('text=Name is required')).toBeVisible();
    await expect(page.locator('text=Email is required')).toBeVisible();
  });
});
