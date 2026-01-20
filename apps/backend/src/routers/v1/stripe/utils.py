"""
Stripe Router Utilities
=======================

Helper functions and constants for Stripe operations.

Tax Rules (per business requirements):
- Tax is calculated on (balance_due - travel_fee)
- Travel fee is NOT taxable (gas reimbursement for chef)
- Tips are NOT taxable (added after tax calculation)
- Default tax rate: 8.25% (California)
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional, TypedDict

from .schemas import LoyaltyTier

# Tax configuration
DEFAULT_TAX_RATE = Decimal("0.0825")  # 8.25% California sales tax


class TaxBreakdown(TypedDict):
    """Tax calculation breakdown."""

    taxable_amount_cents: int
    tax_amount_cents: int
    travel_fee_cents: int
    tip_cents: int
    subtotal_cents: int  # balance_due before tax
    total_cents: int  # final amount including tax and tip


def calculate_tax_breakdown(
    balance_due_cents: int,
    travel_fee_cents: int = 0,
    tip_cents: int = 0,
    tax_rate: Decimal = DEFAULT_TAX_RATE,
) -> TaxBreakdown:
    """
    Calculate tax breakdown for payment.

    Tax Rules (per business requirements):
    - Tax is calculated on (balance_due - travel_fee)
    - Travel fee is NOT taxable (gas reimbursement for chef)
    - Tips are NOT taxable (added after tax calculation)

    Args:
        balance_due_cents: Total balance due in cents (includes travel_fee)
        travel_fee_cents: Travel fee portion in cents (NOT taxable)
        tip_cents: Tip amount in cents (NOT taxable)
        tax_rate: Tax rate as Decimal (default 8.25%)

    Returns:
        TaxBreakdown with all amounts in cents

    Example:
        >>> calculate_tax_breakdown(50000, 2000, 1000)  # $500 balance, $20 travel, $10 tip
        {
            'taxable_amount_cents': 48000,  # $480 (balance - travel)
            'tax_amount_cents': 3960,       # $39.60 (8.25% of $480)
            'travel_fee_cents': 2000,       # $20 (NOT taxed)
            'tip_cents': 1000,              # $10 (NOT taxed)
            'subtotal_cents': 50000,        # $500 (original balance)
            'total_cents': 54960            # $549.60 (balance + tax + tip)
        }
    """
    # Taxable amount = balance - travel fee (travel fee is gas reimbursement)
    taxable_amount = max(0, balance_due_cents - travel_fee_cents)

    # Calculate tax (round half up for fairness)
    tax_decimal = Decimal(taxable_amount) * tax_rate
    tax_amount = int(tax_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    # Final total = balance + tax + tip (travel fee already in balance)
    total = balance_due_cents + tax_amount + tip_cents

    return TaxBreakdown(
        taxable_amount_cents=taxable_amount,
        tax_amount_cents=tax_amount,
        travel_fee_cents=travel_fee_cents,
        tip_cents=tip_cents,
        subtotal_cents=balance_due_cents,
        total_cents=total,
    )


def calculate_suggested_tips(amount_cents: int) -> Dict[str, int]:
    """
    Calculate suggested tip amounts for common tip percentages.

    Suggested tips: 20%, 25%, 30%, 35% (industry standard for catering)

    Args:
        amount_cents: Base amount in cents to calculate tips on

    Returns:
        Dictionary with tip percentages and amounts in cents

    Example:
        >>> calculate_suggested_tips(50000)  # $500
        {'20%': 10000, '25%': 12500, '30%': 15000, '35%': 17500}
    """
    tips = {}
    for pct in [20, 25, 30, 35]:
        tip = int(Decimal(amount_cents) * Decimal(pct) / Decimal(100))
        tips[f"{pct}%"] = tip
    return tips


# Loyalty tier thresholds (in dollars)
LOYALTY_THRESHOLDS = {
    LoyaltyTier.VIP: 5000,  # $5,000+ total spent
    LoyaltyTier.GOLD: 2000,  # $2,000+ total spent
    LoyaltyTier.SILVER: 500,  # $500+ total spent
    LoyaltyTier.NEW: 0,  # New customer
}

# Stripe fee rate for savings calculations (Zelle saves ~3%)
STRIPE_FEE_RATE = Decimal("0.03")


def determine_loyalty_status(total_spent: Decimal) -> LoyaltyTier:
    """
    Determine customer loyalty tier based on total spending.

    Args:
        total_spent: Total amount spent in dollars

    Returns:
        LoyaltyTier enum value
    """
    total_float = float(total_spent)

    if total_float >= LOYALTY_THRESHOLDS[LoyaltyTier.VIP]:
        return LoyaltyTier.VIP
    elif total_float >= LOYALTY_THRESHOLDS[LoyaltyTier.GOLD]:
        return LoyaltyTier.GOLD
    elif total_float >= LOYALTY_THRESHOLDS[LoyaltyTier.SILVER]:
        return LoyaltyTier.SILVER
    else:
        return LoyaltyTier.NEW


def calculate_zelle_savings(total_spent: Decimal) -> Decimal:
    """
    Calculate how much a customer could save by using Zelle instead of card.

    Stripe charges approximately 3% in processing fees.
    Zelle is free, so customers save the full 3%.

    Args:
        total_spent: Total amount spent via card in dollars

    Returns:
        Potential savings in dollars
    """
    return total_spent * STRIPE_FEE_RATE


def format_payment_for_response(
    payment: Any, include_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Format a payment record for API response.

    Args:
        payment: Payment database model
        include_sensitive: Whether to include sensitive fields

    Returns:
        Dictionary representation of payment
    """
    result = {
        "id": str(payment.id),
        "amount_cents": payment.amount_cents,
        "amount": float(payment.amount_cents) / 100 if payment.amount_cents else 0,
        "currency": payment.currency or "usd",
        "status": payment.status.value
        if hasattr(payment.status, "value")
        else payment.status,
        "payment_method": payment.payment_method.value
        if hasattr(payment.payment_method, "value")
        else payment.payment_method,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "description": payment.description,
    }

    if hasattr(payment, "booking_id") and payment.booking_id:
        result["booking_id"] = str(payment.booking_id)

    if include_sensitive:
        if hasattr(payment, "stripe_payment_intent_id"):
            result["stripe_payment_intent_id"] = payment.stripe_payment_intent_id
        if hasattr(payment, "stripe_customer_id"):
            result["stripe_customer_id"] = payment.stripe_customer_id

    return result


def format_invoice_for_response(invoice: Any) -> Dict[str, Any]:
    """
    Format an invoice record for API response.

    Args:
        invoice: Invoice database model

    Returns:
        Dictionary representation of invoice
    """
    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "amount_cents": invoice.amount_cents,
        "amount": float(invoice.amount_cents) / 100 if invoice.amount_cents else 0,
        "currency": invoice.currency or "usd",
        "status": invoice.status.value
        if hasattr(invoice.status, "value")
        else invoice.status,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "booking_id": str(invoice.booking_id) if invoice.booking_id else None,
    }
