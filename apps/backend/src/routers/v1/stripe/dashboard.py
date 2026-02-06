"""
Stripe Customer Dashboard Endpoint
===================================

Customer-facing dashboard with payment history, loyalty status, and savings.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from db.models.stripe import Invoice, InvoiceStatus, PaymentStatus, StripePayment
from services.stripe_service import StripeService
from utils.auth import get_current_user

from .schemas import (
    CustomerDashboardResponse,
    PortalSessionRequest,
    PortalSessionResponse,
)
from .utils import (
    calculate_zelle_savings,
    determine_loyalty_status,
    format_invoice_for_response,
    format_payment_for_response,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-dashboard"])


def get_stripe_service():
    """Dependency to get Stripe service instance."""
    return StripeService()


@router.get("/dashboard", response_model=CustomerDashboardResponse)
async def get_customer_dashboard(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive customer dashboard data.

    Includes:
    - Payment history (last 10)
    - Invoice history (last 10)
    - Total spent (all time)
    - Loyalty tier status
    - Zelle savings (3% of total)
    - Pending amounts
    """
    try:
        user_id = current_user.id

        # Get recent payments (last 10)
        payments_query = (
            select(StripePayment)
            .where(StripePayment.user_id == user_id)
            .order_by(StripePayment.created_at.desc())
            .limit(10)
        )
        payments_result = await db.execute(payments_query)
        recent_payments = payments_result.scalars().all()

        # Get recent invoices (last 10)
        invoices_query = (
            select(Invoice)
            .where(Invoice.user_id == user_id)
            .order_by(Invoice.created_at.desc())
            .limit(10)
        )
        invoices_result = await db.execute(invoices_query)
        recent_invoices = invoices_result.scalars().all()

        # Calculate total spent (successful payments only)
        total_result = await db.execute(
            select(func.sum(StripePayment.amount)).where(
                and_(
                    StripePayment.user_id == user_id,
                    StripePayment.status == PaymentStatus.SUCCEEDED,
                )
            )
        )
        total_spent = total_result.scalar() or Decimal("0")

        # Calculate pending amount
        pending_result = await db.execute(
            select(func.sum(StripePayment.amount)).where(
                and_(
                    StripePayment.user_id == user_id,
                    StripePayment.status == PaymentStatus.PENDING,
                )
            )
        )
        pending_amount = pending_result.scalar() or Decimal("0")

        # Get total payment count
        count_result = await db.execute(
            select(func.count(StripePayment.id)).where(
                and_(
                    StripePayment.user_id == user_id,
                    StripePayment.status == PaymentStatus.SUCCEEDED,
                )
            )
        )
        payment_count = count_result.scalar() or 0

        # Calculate loyalty status and Zelle savings
        loyalty_tier = determine_loyalty_status(total_spent)
        zelle_savings = calculate_zelle_savings(total_spent)

        # Format response
        return CustomerDashboardResponse(
            user_id=str(user_id),
            email=current_user.email,
            loyalty_tier=loyalty_tier.value,
            total_spent=float(total_spent),
            payment_count=payment_count,
            zelle_savings=float(zelle_savings),
            pending_amount=float(pending_amount),
            recent_payments=[
                format_payment_for_response(p, include_sensitive=False) for p in recent_payments
            ],
            recent_invoices=[format_invoice_for_response(inv) for inv in recent_invoices],
        )

    except Exception as e:
        logger.exception(f"Error fetching customer dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.post("/customer-portal", response_model=PortalSessionResponse)
async def create_customer_portal_session(
    request: PortalSessionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Create a Stripe Customer Portal session.

    Allows customers to:
    - View payment history
    - Update payment methods
    - Download invoices
    - Manage subscription (if applicable)
    """
    try:
        # Get or create Stripe customer ID for user
        stripe_customer_id = current_user.stripe_customer_id

        if not stripe_customer_id:
            # Create new Stripe customer
            customer = await stripe_service.create_customer(
                email=current_user.email,
                name=current_user.full_name or current_user.email,
                metadata={"user_id": str(current_user.id)},
            )
            stripe_customer_id = customer.id

            # Save to user record
            current_user.stripe_customer_id = stripe_customer_id
            await db.commit()

        # Create portal session
        return_url = request.return_url or f"{settings.FRONTEND_URL}/dashboard"

        portal_session = await stripe_service.create_portal_session(
            customer_id=stripe_customer_id,
            return_url=return_url,
        )

        return PortalSessionResponse(
            url=portal_session.url,
            return_url=return_url,
        )

    except Exception as e:
        logger.exception(f"Error creating customer portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


# Legacy compatibility function for main.py's /api/v1/customers/dashboard
# This uses Stripe customer_id directly instead of database user_id
async def get_customer_dashboard_by_stripe_id(
    customer_id: str | None = None,
    email: str | None = None,
    stripe_service: StripeService = None,
):
    """
    LEGACY: Get customer dashboard using Stripe customer ID or email.

    Used by compatibility endpoint at /api/v1/customers/dashboard.
    For new endpoints, use get_customer_dashboard() with authentication.
    """
    import stripe

    if stripe_service is None:
        stripe_service = StripeService()

    if not customer_id and not email:
        raise HTTPException(status_code=400, detail="Customer ID or email required")

    try:
        if customer_id:
            stripe_customer = stripe.Customer.retrieve(customer_id)
            customer_data = await stripe_service.get_customer_analytics(customer_id)
        else:
            customers = stripe.Customer.list(email=email, limit=1)
            if not customers.data:
                raise HTTPException(status_code=404, detail="Customer not found")
            stripe_customer = customers.data[0]
            customer_data = await stripe_service.get_customer_analytics(stripe_customer.id)

        if not customer_data:
            raise HTTPException(status_code=404, detail="Customer analytics not found")

        analytics = customer_data.get("analytics", {})
        total_spent = analytics.get("totalSpent", 0)

        # 3% Stripe fee savings calculation
        potential_savings = total_spent * 0.03

        return {
            "customer": {
                "id": stripe_customer.id,
                "email": stripe_customer.email,
                "name": stripe_customer.name,
            },
            "analytics": analytics,
            "insights": {
                "potentialZelleSavings": potential_savings,
                "savingsMessage": f"Switch to Zelle and save ${potential_savings:.2f} in processing fees!",
            },
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=404, detail="Customer not found")
    except Exception as e:
        logger.exception(f"Error fetching customer dashboard by Stripe ID: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.get("/loyalty-status")
async def get_loyalty_status(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed loyalty status for the current user.

    Returns:
    - Current tier
    - Total spent
    - Progress to next tier
    - Tier benefits
    """
    try:
        user_id = current_user.id

        # Calculate total spent
        total_result = await db.execute(
            select(func.sum(StripePayment.amount)).where(
                and_(
                    StripePayment.user_id == user_id,
                    StripePayment.status == PaymentStatus.SUCCEEDED,
                )
            )
        )
        total_spent = total_result.scalar() or Decimal("0")

        # Get loyalty tier
        tier = determine_loyalty_status(total_spent)

        # Calculate progress to next tier
        from .utils import LOYALTY_THRESHOLDS, LoyaltyTier

        current_threshold = LOYALTY_THRESHOLDS.get(tier, Decimal("0"))

        # Find next tier
        tier_order = [
            LoyaltyTier.NEW,
            LoyaltyTier.SILVER,
            LoyaltyTier.GOLD,
            LoyaltyTier.VIP,
        ]
        current_index = tier_order.index(tier)

        next_tier = None
        amount_to_next = Decimal("0")
        progress_percent = 100

        if current_index < len(tier_order) - 1:
            next_tier = tier_order[current_index + 1]
            next_threshold = LOYALTY_THRESHOLDS.get(next_tier, Decimal("0"))
            amount_to_next = max(Decimal("0"), next_threshold - total_spent)

            # Calculate progress percentage
            range_size = next_threshold - current_threshold
            if range_size > 0:
                progress = total_spent - current_threshold
                progress_percent = min(100, int((progress / range_size) * 100))

        # Define tier benefits
        tier_benefits = {
            LoyaltyTier.NEW: ["Welcome discount on first order"],
            LoyaltyTier.SILVER: ["5% priority booking", "Early access to new features"],
            LoyaltyTier.GOLD: [
                "10% priority booking",
                "Dedicated support",
                "Exclusive events",
            ],
            LoyaltyTier.VIP: [
                "15% priority booking",
                "VIP concierge",
                "Free upgrades",
                "Exclusive events",
            ],
        }

        return {
            "tier": tier.value,
            "total_spent": float(total_spent),
            "next_tier": next_tier.value if next_tier else None,
            "amount_to_next_tier": float(amount_to_next),
            "progress_percent": progress_percent,
            "benefits": tier_benefits.get(tier, []),
            "zelle_savings": float(calculate_zelle_savings(total_spent)),
        }

    except Exception as e:
        logger.exception(f"Error fetching loyalty status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch loyalty status")
