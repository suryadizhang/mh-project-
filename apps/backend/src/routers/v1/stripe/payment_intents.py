"""
Stripe Payment Intents Endpoints
================================

Endpoints for creating and managing Payment Intents.
"""

import logging
from typing import Optional
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from services.stripe_service import StripeService
from utils.auth import get_current_user

from .schemas import (
    PaymentIntentRequest,
    PaymentIntentResponse,
    PortalSessionRequest,
    PortalSessionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-payment-intents"])


def get_stripe_service(db: AsyncSession = Depends(get_db)) -> StripeService:
    """Dependency to get StripeService instance."""
    return StripeService(db)


@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user=Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Create a Payment Intent for client-side payment processing.

    Use this for custom payment forms with Stripe Elements.
    """
    try:
        # Build metadata
        metadata = {
            "user_id": str(current_user.id),
            **(request.metadata or {}),
        }
        if request.booking_id:
            metadata["booking_id"] = str(request.booking_id)

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            receipt_email=request.customer_email or current_user.email,
            description=request.description or "My Hibachi Payment",
            metadata=metadata,
            automatic_payment_methods={"enabled": True},
        )

        logger.info(f"Created payment intent {intent.id} for user {current_user.id}")

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment intent")


@router.get("/payment-intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    current_user=Depends(get_current_user),
):
    """
    Retrieve details of a Payment Intent.
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Verify ownership via metadata
        intent_user_id = intent.metadata.get("user_id")
        if intent_user_id and intent_user_id != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Payment intent does not belong to this user"
            )

        return {
            "payment_intent_id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
            "created": intent.created,
            "booking_id": intent.metadata.get("booking_id"),
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error retrieving payment intent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment intent")


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    current_user=Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Create a Stripe Customer Portal session.

    Allows customers to manage their payment methods and billing.
    """
    try:
        # Get or create Stripe customer for this user
        customer_id = await stripe_service.get_or_create_customer(
            email=current_user.email,
            user_id=str(current_user.id),
            name=getattr(current_user, "full_name", None),
        )

        # Create portal session
        return_url = request.return_url or f"{settings.FRONTEND_URL}/account"

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        logger.info(f"Created portal session for user {current_user.id}")

        return PortalSessionResponse(
            portal_url=session.url,
            expires_at=None,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


# V1 Migrated Endpoints


@router.post("/v1/payments/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent_v1(
    request: PaymentIntentRequest,
    current_user=Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    V1 API: Create a Payment Intent with enhanced customer management.
    """
    try:
        # Get or create Stripe customer
        customer_id = await stripe_service.get_or_create_customer(
            email=request.customer_email or current_user.email,
            user_id=str(current_user.id),
            name=getattr(current_user, "full_name", None),
        )

        # Build metadata
        metadata = {
            "user_id": str(current_user.id),
            "source": "v1_api",
            **(request.metadata or {}),
        }
        if request.booking_id:
            metadata["booking_id"] = str(request.booking_id)

        # Create payment intent with customer attached
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            customer=customer_id,
            receipt_email=request.customer_email or current_user.email,
            description=request.description or "My Hibachi Payment",
            metadata=metadata,
            automatic_payment_methods={"enabled": True},
        )

        logger.info(f"Created V1 payment intent {intent.id} for customer {customer_id}")

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in V1 create intent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in V1 create payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment intent")


@router.get("/v1/payments/create-intent/{payment_intent_id}")
async def get_payment_intent_v1(
    payment_intent_id: str,
    current_user=Depends(get_current_user),
):
    """
    V1 API: Retrieve Payment Intent details with enhanced response.
    """
    try:
        intent = stripe.PaymentIntent.retrieve(
            payment_intent_id,
            expand=["customer", "latest_charge"],
        )

        # Verify ownership
        intent_user_id = intent.metadata.get("user_id")
        if intent_user_id and intent_user_id != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Payment intent does not belong to this user"
            )

        response = {
            "payment_intent_id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
            "created": intent.created,
            "booking_id": intent.metadata.get("booking_id"),
            "customer_id": intent.customer.id if intent.customer else None,
        }

        # Include charge details if available
        if intent.latest_charge:
            response["charge"] = {
                "id": intent.latest_charge.id,
                "paid": intent.latest_charge.paid,
                "refunded": intent.latest_charge.refunded,
                "receipt_url": intent.latest_charge.receipt_url,
            }

        return response

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in V1 get intent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in V1 get payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment intent")
