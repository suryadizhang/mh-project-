"""
Customer Lookup for Payment Processing
======================================

Endpoints for looking up customers by phone/email and retrieving
their balance information with tax calculations and tip suggestions.

Tax Rules:
- Tax is calculated on (balance_due - travel_fee)
- Travel fee is NOT taxable (gas reimbursement for chef)
- Tips are NOT taxable (added after tax calculation)
"""

import logging
import re
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from db.models.core import Booking, Customer
from db.models.stripe import PaymentStatus, StripePayment

from .schemas import (
    BookingBalanceInfo,
    CustomerBalanceResponse,
    CustomerLookupRequest,
    LoyaltyTier,
    SuggestedTips,
    TaxBreakdownResponse,
)
from .utils import (
    DEFAULT_TAX_RATE,
    calculate_suggested_tips,
    calculate_tax_breakdown,
    determine_loyalty_status,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-customer-lookup"])


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format (+1XXXXXXXXXX).

    Args:
        phone: Raw phone number input

    Returns:
        Normalized phone number in +1XXXXXXXXXX format
    """
    if not phone:
        return ""

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Handle various formats
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 11:
        return f"+{digits}"

    return phone  # Return as-is if format unclear


async def get_customer_paid_amount(db: AsyncSession, customer_id: UUID) -> int:
    """Get total amount paid by customer (in cents)."""
    result = await db.execute(
        select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(
            and_(
                StripePayment.customer_id == customer_id,
                StripePayment.status == PaymentStatus.SUCCEEDED,
            )
        )
    )
    return result.scalar() or 0


async def get_customer_bookings_with_balance(
    db: AsyncSession,
    customer_id: UUID,
) -> list[Booking]:
    """
    Get customer's bookings that have outstanding balance.

    Returns bookings with: confirmed status and balance_due > 0
    """
    # Get all confirmed/pending bookings for the customer
    result = await db.execute(
        select(Booking)
        .where(
            and_(
                Booking.customer_id == customer_id,
                Booking.status.in_(["pending", "confirmed", "deposit_paid"]),
            )
        )
        .order_by(Booking.event_date.desc())
    )
    return list(result.scalars().all())


@router.post("/lookup", response_model=CustomerBalanceResponse)
async def lookup_customer_balance(
    request: CustomerLookupRequest,
    db: AsyncSession = Depends(get_db),
    tax_rate: float = Query(
        default=0.0825, ge=0, le=0.2, description="Tax rate (default 8.25%)"
    ),
):
    """
    Look up customer by phone or email and get balance information.

    Returns:
    - Customer info
    - Active bookings with balances
    - Tax calculation (travel fee excluded from taxable amount)
    - Suggested tip amounts
    - Loyalty tier

    Tax Rules:
    - Taxable amount = balance_due - travel_fee
    - Travel fee is NOT taxed (gas reimbursement for chef)
    - Tips are NOT taxed (calculated separately)
    """
    if not request.phone and not request.email:
        raise HTTPException(
            status_code=400, detail="Either phone or email is required for lookup"
        )

    try:
        # Build query conditions
        conditions = []

        if request.phone:
            normalized_phone = normalize_phone(request.phone)
            # Try both encrypted and plain phone fields
            conditions.append(Customer.phone == normalized_phone)
            if hasattr(Customer, "phone_encrypted"):
                conditions.append(Customer.phone_encrypted == normalized_phone)

        if request.email:
            email_lower = request.email.lower().strip()
            conditions.append(Customer.email == email_lower)
            if hasattr(Customer, "email_encrypted"):
                conditions.append(Customer.email_encrypted == email_lower)

        # Execute query
        result = await db.execute(select(Customer).where(or_(*conditions)).limit(1))
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer not found with provided phone or email",
            )

        # Get active bookings with balance
        bookings = await get_customer_bookings_with_balance(db, customer.id)

        # Calculate totals across all bookings
        total_balance_due = 0
        total_travel_fee = 0
        booking_infos = []

        for booking in bookings:
            # Calculate balance for this booking
            total_due = booking.total_due_cents or 0
            deposit_paid = (
                booking.deposit_due_cents or 0
            )  # This is deposit AMOUNT, not paid

            # Get actual paid amount for this booking
            paid_result = await db.execute(
                select(func.coalesce(func.sum(StripePayment.amount_cents), 0)).where(
                    and_(
                        StripePayment.booking_id == booking.id,
                        StripePayment.status == PaymentStatus.SUCCEEDED,
                    )
                )
            )
            paid_amount = paid_result.scalar() or 0

            balance_due = max(0, total_due - paid_amount)

            # Get travel fee (estimate based on zone if available)
            # Travel fee is typically included in total_due, estimate as 0 for now
            # unless we can calculate it from the booking's travel_zone
            travel_fee = 0
            if hasattr(booking, "travel_fee_cents") and booking.travel_fee_cents:
                travel_fee = booking.travel_fee_cents

            if balance_due > 0:
                total_balance_due += balance_due
                total_travel_fee += travel_fee

                booking_infos.append(
                    BookingBalanceInfo(
                        booking_id=booking.id,
                        event_date=booking.event_date,
                        total_due_cents=total_due,
                        deposit_paid_cents=paid_amount,
                        balance_due_cents=balance_due,
                        travel_fee_cents=travel_fee,
                        status=booking.status,
                    )
                )

        # Calculate tax breakdown (travel fee excluded from taxable amount)
        tax_breakdown = calculate_tax_breakdown(
            balance_due_cents=total_balance_due,
            travel_fee_cents=total_travel_fee,
            tip_cents=0,  # No tip yet - just showing base calculation
            tax_rate=Decimal(str(tax_rate)),
        )

        # Calculate suggested tips (on taxable amount, not travel fee)
        tips = calculate_suggested_tips(tax_breakdown["taxable_amount_cents"])

        # Get total spent for loyalty tier
        total_spent = await get_customer_paid_amount(db, customer.id)
        loyalty_tier = determine_loyalty_status(Decimal(total_spent) / 100)

        # Get customer contact info (handle encrypted fields)
        customer_email = getattr(customer, "email", None) or getattr(
            customer, "email_encrypted", None
        )
        customer_phone = getattr(customer, "phone", None) or getattr(
            customer, "phone_encrypted", None
        )
        customer_name = (
            getattr(customer, "name", None)
            or f"{getattr(customer, 'first_name', '')} {getattr(customer, 'last_name', '')}".strip()
            or "Customer"
        )

        return CustomerBalanceResponse(
            customer_id=customer.id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            bookings=booking_infos,
            total_balance_due_cents=total_balance_due,
            total_travel_fee_cents=total_travel_fee,
            tax_breakdown=TaxBreakdownResponse(
                taxable_amount_cents=tax_breakdown["taxable_amount_cents"],
                tax_amount_cents=tax_breakdown["tax_amount_cents"],
                travel_fee_cents=tax_breakdown["travel_fee_cents"],
                tip_cents=0,
                subtotal_cents=tax_breakdown["subtotal_cents"],
                total_cents=tax_breakdown["total_cents"],
                tax_rate=float(tax_rate),
            ),
            suggested_tips=SuggestedTips(
                tip_20_percent=tips["20%"],
                tip_25_percent=tips["25%"],
                tip_30_percent=tips["30%"],
                tip_35_percent=tips["35%"],
            ),
            loyalty_tier=loyalty_tier,
            total_spent_cents=total_spent,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error looking up customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to look up customer")


@router.get("/calculate-total")
async def calculate_payment_total(
    balance_cents: int = Query(..., ge=0, description="Balance due in cents"),
    travel_fee_cents: int = Query(default=0, ge=0, description="Travel fee in cents"),
    tip_cents: int = Query(default=0, ge=0, description="Tip amount in cents"),
    tax_rate: float = Query(
        default=0.0825, ge=0, le=0.2, description="Tax rate (default 8.25%)"
    ),
) -> TaxBreakdownResponse:
    """
    Calculate total payment amount with tax.

    Tax Rules:
    - Taxable amount = balance - travel_fee
    - Travel fee is NOT taxed (gas reimbursement for chef)
    - Tips are NOT taxed

    Example:
        balance=50000 (&#36;500), travel_fee=2000 (&#36;20), tip=5000 (&#36;50)
        taxable = 48000 (&#36;480)
        tax = 3960 (&#36;39.60 at 8.25%)
        total = 58960 (&#36;589.60 = &#36;500 + &#36;39.60 + &#36;50)
    """
    breakdown = calculate_tax_breakdown(
        balance_due_cents=balance_cents,
        travel_fee_cents=travel_fee_cents,
        tip_cents=tip_cents,
        tax_rate=Decimal(str(tax_rate)),
    )

    return TaxBreakdownResponse(
        taxable_amount_cents=breakdown["taxable_amount_cents"],
        tax_amount_cents=breakdown["tax_amount_cents"],
        travel_fee_cents=breakdown["travel_fee_cents"],
        tip_cents=breakdown["tip_cents"],
        subtotal_cents=breakdown["subtotal_cents"],
        total_cents=breakdown["total_cents"],
        tax_rate=tax_rate,
    )


@router.get("/suggested-tips")
async def get_suggested_tips(
    amount_cents: int = Query(..., ge=0, description="Base amount in cents"),
) -> SuggestedTips:
    """
    Get suggested tip amounts for a given base amount.

    Suggested tips: 20%, 25%, 30%, 35% (industry standard for catering)
    """
    tips = calculate_suggested_tips(amount_cents)

    return SuggestedTips(
        tip_20_percent=tips["20%"],
        tip_25_percent=tips["25%"],
        tip_30_percent=tips["30%"],
        tip_35_percent=tips["35%"],
    )
