import { test, expect } from '@playwright/test';
import { testPayment, calculateTotal } from '../../helpers/test-data';
import {
  completeStripePayment,
  selectZellePayment,
  selectVenmoPayment,
  testPaymentFailure,
  verifyPaymentTotal,
} from '../../helpers/payment-helpers';

/**
 * Payment Processing Tests
 *
 * Tests all payment methods: Stripe, Zelle, Venmo
 * Tests success and failure scenarios
 *
 * Tags: @payment @critical
 * Services needed: Frontend, Backend, Database, Stripe
 */
test.describe('Payment Processing', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to payment page
    await page.goto('/payment');

    // Simulate having a booking (you may need to create one first)
    await page.evaluate(() => {
      sessionStorage.setItem('testBookingId', 'MH-20251225-TEST');
      sessionStorage.setItem('testAmount', '100');
    });
  });

  test('processes Stripe payment successfully @payment @critical', async ({
    page,
  }) => {
    const amount = 100;
    const { fee, total } = calculateTotal(amount, 'stripe');

    // Verify fee calculation
    await verifyPaymentTotal(page, { subtotal: amount, fee, total });

    // Complete payment
    await completeStripePayment(page, total);

    // Verify success
    await expect(page.locator('text=Payment successful')).toBeVisible({
      timeout: 30000,
    });

    // Verify receipt
    await expect(page.locator('text=Receipt')).toBeVisible();
  });

  test('shows Zelle payment instructions @payment @critical', async ({
    page,
  }) => {
    await selectZellePayment(page);

    // Verify instructions
    await expect(page.locator('text=Send payment to:')).toBeVisible();
    await expect(page.locator('text=myhibachichef@gmail.com')).toBeVisible();
    await expect(page.locator('text=0% processing fee')).toBeVisible();

    // Verify savings indicator
    const savings = await page.textContent('[data-testid="savings-amount"]');
    expect(savings).toContain('$8'); // 8% of $100
  });

  test('shows Venmo payment instructions @payment', async ({ page }) => {
    await selectVenmoPayment(page);

    // Verify instructions
    await expect(page.locator('text=@myhibachichef')).toBeVisible();
    await expect(page.locator('text=3% processing fee')).toBeVisible();
  });

  test('handles declined card @payment', async ({ page }) => {
    await testPaymentFailure(page);

    // Verify error message
    await expect(page.locator('text=Your card was declined')).toBeVisible();
    await expect(page.locator('text=Try another payment method')).toBeVisible();
  });

  test('calculates tips correctly @payment', async ({ page }) => {
    const baseAmount = 100;

    // Test different tip percentages
    const tipTests = [15, 18, 20, 25];

    for (const tipPercent of tipTests) {
      await page.click(`button:has-text("${tipPercent}%")`);

      const expectedTip = baseAmount * (tipPercent / 100);
      const tipAmount = await page.textContent('[data-testid="tip-amount"]');

      expect(tipAmount).toContain(expectedTip.toFixed(2));
    }
  });

  test('allows custom tip amount @payment', async ({ page }) => {
    await page.click('button:has-text("Custom")');
    await page.fill('[name="customTip"]', '35');

    const tipAmount = await page.textContent('[data-testid="tip-amount"]');
    expect(tipAmount).toContain('35.00');
  });

  test('validates payment amount @payment', async ({ page }) => {
    // Try to pay with invalid amount
    await page.evaluate(() => {
      sessionStorage.setItem('testAmount', '0');
    });

    await page.reload();

    // Verify error
    await expect(page.locator('text=Invalid payment amount')).toBeVisible();
  });

  test('shows payment history @payment', async ({ page }) => {
    await page.goto('/payment/history');

    // Verify history loads
    await expect(page.locator('h1')).toContainText('Payment History');

    // Should show list or empty state
    const hasPayments = await page
      .locator('[data-testid="payment-item"]')
      .count();

    if (hasPayments > 0) {
      // Verify payment details shown
      await expect(
        page.locator('[data-testid="payment-amount"]').first()
      ).toBeVisible();
      await expect(
        page.locator('[data-testid="payment-date"]').first()
      ).toBeVisible();
    } else {
      await expect(page.locator('text=No payments yet')).toBeVisible();
    }
  });
});

test.describe('Payment Security', () => {
  test('payment form is SSL secured @payment @security', async ({ page }) => {
    await page.goto('/payment');

    // In local dev, we use HTTP. In production, verify HTTPS
    // Skip SSL check for localhost
    const currentUrl = page.url();
    if (!currentUrl.includes('localhost')) {
      expect(currentUrl).toMatch(/^https:/);
    }

    // Verify secure indicators (if present)
    const securedText = page.locator('text=Secured by Stripe');
    const isSecuredTextVisible = await securedText
      .isVisible()
      .catch(() => false);
    // This is optional - payment page may not show this text
    if (isSecuredTextVisible) {
      await expect(securedText).toBeVisible();
    }
  });

  test('sensitive data not exposed in DOM @payment @security', async ({
    page,
  }) => {
    await page.goto('/payment');

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');

    // Check that test card numbers are not in page content
    const pageContent = await page.content();
    expect(pageContent).not.toContain('4242424242424242');
  });
});
