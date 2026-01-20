"""
Stripe Refund Endpoints
=======================

Endpoints for processing refunds (admin only).
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from db.models.stripe import PaymentStatus, StripePayment
from services.stripe_service import StripeService
from utils.auth import Permission, get_current_user, require_permissions

from .schemas import RefundRequest, RefundResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-refunds"])


def get_stripe_service(db: AsyncSession = Depends(get_db)) -> StripeService:
    """Dependency to get StripeService instance."""
    return StripeService(db)


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    request: RefundRequest,
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Process a refund for a payment.

    Admin only. Supports full or partial refunds.
    """
    try:
        # Find the payment record
        payment = await db.get(StripePayment, request.payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Validate payment can be refunded
        if payment.status not in [
            PaymentStatus.SUCCEEDED,
            PaymentStatus.PARTIALLY_REFUNDED,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Payment cannot be refunded. Current status: {payment.status}",
            )

        if not payment.stripe_payment_intent_id:
            raise HTTPException(
                status_code=400,
                detail="Payment does not have a Stripe payment intent ID",
            )

        # Calculate refund amount
        refund_amount = request.amount or payment.amount
        already_refunded = payment.refunded_amount or 0
        max_refundable = payment.amount - already_refunded

        if refund_amount > max_refundable:
            raise HTTPException(
                status_code=400,
                detail=f"Refund amount exceeds available amount. Max refundable: ${max_refundable / 100:.2f}",
            )

        # Process refund via Stripe
        refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id,
            amount=refund_amount,
            reason=request.reason or "requested_by_customer",
            metadata={
                "admin_user_id": str(current_user.id),
                "internal_payment_id": str(payment.id),
            },
        )

        # Update payment record
        new_refunded_amount = already_refunded + refund_amount
        if new_refunded_amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        payment.refunded_amount = new_refunded_amount
        payment.refunded_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(
            f"Processed refund {refund.id} for ${refund_amount / 100:.2f} "
            f"on payment {payment.id} by admin {current_user.id}"
        )

        return RefundResponse(
            refund_id=refund.id,
            payment_id=str(payment.id),
            amount=refund.amount,
            currency=refund.currency,
            status=refund.status,
            reason=refund.reason,
            created=refund.created,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error processing refund: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing refund: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process refund")


@router.get("/refund/{refund_id}")
async def get_refund(
    refund_id: str,
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
):
    """
    Retrieve details of a specific refund.

    Admin only.
    """
    try:
        refund = stripe.Refund.retrieve(refund_id)

        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "currency": refund.currency,
            "status": refund.status,
            "reason": refund.reason,
            "created": refund.created,
            "payment_intent_id": refund.payment_intent,
            "metadata": refund.metadata,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving refund: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving refund: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve refund")


@router.get("/payment/{payment_id}/refunds")
async def list_refunds_for_payment(
    payment_id: UUID,
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
):
    """
    List all refunds for a specific payment.

    Admin only.
    """
    try:
        # Find the payment
        payment = await db.get(Payment, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if not payment.stripe_payment_intent_id:
            return {"refunds": [], "total": 0}

        # Get refunds from Stripe
        refunds = stripe.Refund.list(
            payment_intent=payment.stripe_payment_intent_id,
            limit=100,
        )

        return {
            "refunds": [
                {
                    "refund_id": r.id,
                    "amount": r.amount,
                    "currency": r.currency,
                    "status": r.status,
                    "reason": r.reason,
                    "created": r.created,
                }
                for r in refunds.data
            ],
            "total": len(refunds.data),
            "payment_id": str(payment.id),
            "total_refunded": sum(r.amount for r in refunds.data),
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error listing refunds: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing refunds: {e}")
        raise HTTPException(status_code=500, detail="Failed to list refunds")
