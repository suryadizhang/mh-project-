// LEGACY FILE - REPLACED BY NEW STRIPE INTEGRATION
// See src/lib/server/stripeCustomerService.ts for working implementation

export function calculatePaymentSavings(amount: number, method: 'stripe' | 'zelle' | 'venmo') {
  const fees = {
    stripe: amount * 0.08, // 8% processing fee
    venmo: amount * 0.03, // 3% processing fee
    zelle: 0 // No fees
  }

  const savings = fees.stripe - fees[method]
  const stripeFeeSavings = fees.stripe

  // Customize message based on amount
  const savingsMessage =
    amount >= 100
      ? `Save $${stripeFeeSavings.toFixed(2)} compared to credit card!`
      : `Save $${stripeFeeSavings.toFixed(2)} - every dollar counts!`

  return {
    fees,
    savings,
    message: method === 'zelle' ? savingsMessage : null,
    recommendation:
      method !== 'zelle'
        ? {
            preferredMethod: 'zelle',
            potentialSavings: fees[method],
            message: `Switch to Zelle and save $${fees[method].toFixed(2)}`
          }
        : null
  }
}

/* 
// IMPLEMENTATION MOVED TO NEW STRIPE INTEGRATION
// See src/lib/server/stripeCustomerService.ts for working implementation
*/
