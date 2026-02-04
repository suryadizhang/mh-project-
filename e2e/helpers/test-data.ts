/**
 * Test Data Helpers
 * Centralized test data for consistent E2E testing
 */

export const testCustomer = {
  name: 'John Doe',
  email: `test-${Date.now()}@example.com`, // Unique email per test run
  phone: '555-0123',
  address: '123 Test St',
  city: 'Test City',
  state: 'CA',
  zipCode: '90210',
};

export const testBooking = {
  eventDate: getTestDate(30), // 30 days from now
  guestCount: 20,
  eventType: 'Birthday Party',
  menuItems: ['Hibachi Chicken', 'Fried Rice', 'Vegetables'],
  specialRequests: 'Please arrive 30 minutes early',
};

export const testPayment = {
  // Stripe test cards
  cards: {
    visa: {
      number: '4242424242424242',
      expiry: '12/25',
      cvc: '123',
      zip: '90210',
    },
    visaDebit: {
      number: '4000056655665556',
      expiry: '12/25',
      cvc: '123',
      zip: '90210',
    },
    mastercard: {
      number: '5555555555554444',
      expiry: '12/25',
      cvc: '123',
      zip: '90210',
    },
    declined: {
      number: '4000000000000002',
      expiry: '12/25',
      cvc: '123',
      zip: '90210',
    },
    insufficientFunds: {
      number: '4000000000009995',
      expiry: '12/25',
      cvc: '123',
      zip: '90210',
    },
  },
  amounts: {
    deposit: 100,
    balance: 500,
    tip: 50,
  },
};

export const testAdmin = {
  // NEVER hardcode credentials - use environment variables
  // Set TEST_ADMIN_EMAIL and TEST_ADMIN_PASSWORD in your .env file
  email: process.env.TEST_ADMIN_EMAIL || '',
  password: process.env.TEST_ADMIN_PASSWORD || '',
};

/**
 * Get a test date N days from now
 */
export function getTestDate(daysFromNow: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().split('T')[0]; // YYYY-MM-DD
}

/**
 * Generate unique booking ID
 */
export function generateBookingId(): string {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
  const random = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `MH-${dateStr}-${random}`;
}

/**
 * Calculate expected totals with fees
 */
export function calculateTotal(
  subtotal: number,
  paymentMethod: 'stripe' | 'venmo' | 'zelle'
) {
  const fees = {
    stripe: 0.08, // 8%
    venmo: 0.03, // 3%
    zelle: 0, // 0%
  };

  const fee = subtotal * fees[paymentMethod];
  const total = subtotal + fee;

  return {
    subtotal,
    fee: Math.round(fee * 100) / 100,
    total: Math.round(total * 100) / 100,
  };
}

/**
 * Wait helper
 */
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
