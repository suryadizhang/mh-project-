"""
Stripe Checkout Endpoints
=========================

Endpoints for Stripe Checkout Sessions and verification.
"""

import logging
from typing import Optional
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from services.stripe_service import StripeService
from utils.auth import get_current_user

from .schemas import CheckoutSessionRequest, CheckoutSessionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-checkout"])


def get_stripe_service(db: AsyncSession = Depends(get_db)) -> StripeService:
    """Dependency to get StripeService instance."""
    return StripeService(db)


@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user=Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Create a Stripe Checkout Session for payment collection.

    This creates a hosted checkout page where customers can securely
    enter payment information.
    """
    try:
        # Build success and cancel URLs
        success_url = (
            request.success_url
            or f"{settings.FRONTEND_URL}/booking/success?session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = request.cancel_url or f"{settings.FRONTEND_URL}/booking/cancel"

        # Determine customer email for receipt
        customer_email = request.customer_email or current_user.email

        # Create checkout session via Stripe API
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": request.currency,
                        "unit_amount": request.amount,
                        "product_data": {
                            "name": request.description or "My Hibachi Booking",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            # Enable Stripe-managed receipt emails
            payment_intent_data={
                "receipt_email": customer_email,
            },
            metadata={
                "booking_id": str(request.booking_id) if request.booking_id else None,
                "user_id": str(current_user.id),
                **(request.metadata or {}),
            },
        )

        logger.info(f"Created checkout session {session.id} for user {current_user.id}")

        return CheckoutSessionResponse(
            session_id=session.id,
            checkout_url=session.url,
            expires_at=None,  # Stripe sessions expire after 24 hours
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/checkout/session/{session_id}")
async def verify_checkout_session(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """
    Verify the status of a Checkout Session.

    Used to confirm payment completion after redirect from Stripe.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        # Verify the session belongs to this user (via metadata)
        session_user_id = session.metadata.get("user_id")
        if session_user_id and session_user_id != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Session does not belong to this user"
            )

        return {
            "session_id": session.id,
            "payment_status": session.payment_status,
            "status": session.status,
            "amount_total": session.amount_total,
            "currency": session.currency,
            "customer_email": session.customer_email,
            "booking_id": session.metadata.get("booking_id"),
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error verifying checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify session")
