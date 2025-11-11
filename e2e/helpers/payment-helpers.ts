import { Page, expect } from '@playwright/test';
import { testPayment } from './test-data';

/**
 * Payment Flow Helpers
 */

/**
 * Complete Stripe payment
 */
export async function completeStripePayment(page: Page, amount: number) {
  // Select Stripe payment method
  await page.click('text=Credit Card');
  
  // Wait for Stripe Elements to load
  await page.waitForSelector('[data-testid="stripe-payment-element"]', { timeout: 10000 });
  
  // Fill card details in Stripe iframe
  const stripeFrame = page.frameLocator('iframe[name*="__privateStripeFrame"]').first();
  
  await stripeFrame.locator('[name="cardnumber"]').fill(testPayment.cards.visa.number);
  await stripeFrame.locator('[name="exp-date"]').fill(testPayment.cards.visa.expiry);
  await stripeFrame.locator('[name="cvc"]').fill(testPayment.cards.visa.cvc);
  await stripeFrame.locator('[name="postal"]').fill(testPayment.cards.visa.zip);
  
  // Submit payment
  await page.click('button:has-text("Pay")');
  
  // Wait for success
  await page.waitForSelector('text=Payment successful', { timeout: 30000 });
}

/**
 * Select Zelle payment method
 */
export async function selectZellePayment(page: Page) {
  await page.click('text=Zelle');
  
  // Verify Zelle instructions are shown
  await expect(page.locator('text=myhibachichef@gmail.com')).toBeVisible();
  
  // Click confirm
  await page.click('button:has-text("I will pay with Zelle")');
}

/**
 * Select Venmo payment method
 */
export async function selectVenmoPayment(page: Page) {
  await page.click('text=Venmo');
  
  // Verify Venmo instructions are shown
  await expect(page.locator('text=@myhibachichef')).toBeVisible();
  
  // Click confirm
  await page.click('button:has-text("I will pay with Venmo")');
}

/**
 * Add tip
 */
export async function addTip(page: Page, tipPercentage: number) {
  await page.click(`button:has-text("${tipPercentage}%")`);
}

/**
 * Verify payment total
 */
export async function verifyPaymentTotal(
  page: Page, 
  expected: { subtotal: number; fee: number; total: number }
) {
  const subtotal = await page.textContent('[data-testid="subtotal"]');
  const fee = await page.textContent('[data-testid="processing-fee"]');
  const total = await page.textContent('[data-testid="total"]');
  
  expect(subtotal).toContain(expected.subtotal.toFixed(2));
  expect(fee).toContain(expected.fee.toFixed(2));
  expect(total).toContain(expected.total.toFixed(2));
}

/**
 * Test payment failure scenario
 */
export async function testPaymentFailure(page: Page) {
  // Use declined card
  const stripeFrame = page.frameLocator('iframe[name*="__privateStripeFrame"]').first();
  
  await stripeFrame.locator('[name="cardnumber"]').fill(testPayment.cards.declined.number);
  await stripeFrame.locator('[name="exp-date"]').fill(testPayment.cards.declined.expiry);
  await stripeFrame.locator('[name="cvc"]').fill(testPayment.cards.declined.cvc);
  await stripeFrame.locator('[name="postal"]').fill(testPayment.cards.declined.zip);
  
  // Submit payment
  await page.click('button:has-text("Pay")');
  
  // Wait for error message
  await page.waitForSelector('text=Your card was declined', { timeout: 10000 });
}
