"""
Stripe Webhook Endpoints & Handlers
====================================

CONSOLIDATED webhook endpoint (previously 3 duplicates).
Handles all Stripe webhook events with proper verification and processing.

Consolidation Notes:
- Previous: /webhook, /v1/payments/webhook, /v1/webhooks/stripe
- Now: Single /webhook endpoint with comprehensive handler routing
"""

import json
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status

from core.config import settings
from core.database import get_db
from db.models.stripe import (
    Invoice,
    InvoiceStatus,
    PaymentStatus,
    StripePayment,
    WebhookEvent,
)
from services.stripe_service import StripeService

from .schemas import WebhookEventResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-webhooks"])


def get_stripe_service():
    """Dependency to get Stripe service instance."""
    return StripeService()


# ============================================================================
# CONSOLIDATED WEBHOOK ENDPOINT
# ============================================================================


@router.post("/webhook", response_model=WebhookEventResponse)
async def webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Consolidated Stripe webhook handler.

    This is the SINGLE webhook endpoint for all Stripe events.
    Configure this URL in Stripe Dashboard: {API_URL}/api/v1/stripe/webhook

    Handles:
    - Payment intent events (succeeded, failed, canceled, processing)
    - Customer events (created, updated)
    - Invoice events (created, paid, failed)
    - Checkout session events
    - Refund and dispute events
    - Subscription events
    """
    try:
        # Get the webhook payload and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            logger.error("Missing stripe-signature header")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header",
            )

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except ValueError:
            logger.exception("Invalid webhook payload")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload",
            )
        except stripe.error.SignatureVerificationError:
            logger.exception("Invalid webhook signature")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            )

        # Store webhook event for audit trail
        webhook_event = await store_webhook_event(event, db)

        # Route event to appropriate handler
        processed = await route_event(event, stripe_service, db)

        # Mark as processed
        if webhook_event:
            webhook_event.processed = True
            webhook_event.processed_at = datetime.now(timezone.utc)
            await db.commit()

        return WebhookEventResponse(
            received=True,
            event_type=event["type"],
            event_id=event["id"],
            processed=processed,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Critical webhook processing error: {e}")
        # Return 200 to acknowledge receipt (prevent Stripe retries)
        return WebhookEventResponse(
            received=True,
            event_type="unknown",
            event_id="unknown",
            processed=False,
        )


async def store_webhook_event(event: dict, db: AsyncSession) -> WebhookEvent:
    """Store webhook event for audit trail and idempotency."""
    try:
        # Check for duplicate event (idempotency)
        existing = await db.execute(
            select(WebhookEvent).where(WebhookEvent.stripe_event_id == event["id"])
        )
        if existing.scalar_one_or_none():
            logger.info(f"Duplicate webhook event ignored: {event['id']}")
            return None

        webhook_event = WebhookEvent(
            type=event["type"],
            stripe_event_id=event["id"],
            payload_json=json.dumps(event),
            processed=False,
        )
        db.add(webhook_event)
        await db.commit()
        logger.info(f"[WEBHOOK STORED] {event['type']} - {event['id']}")
        return webhook_event

    except Exception as error:
        logger.exception(f"Error storing webhook event: {error}")
        return None


async def route_event(
    event: dict,
    stripe_service: StripeService,
    db: AsyncSession,
) -> bool:
    """Route webhook event to appropriate handler."""
    event_type = event["type"]
    event_data = event["data"]["object"]

    try:
        # Payment Intent events
        if event_type == "payment_intent.succeeded":
            await handle_payment_intent_succeeded(event_data, stripe_service, db)
        elif event_type == "payment_intent.payment_failed":
            await handle_payment_intent_failed(event_data, stripe_service, db)
        elif event_type == "payment_intent.canceled":
            await handle_payment_intent_canceled(event_data, stripe_service, db)
        elif event_type == "payment_intent.processing":
            await handle_payment_intent_processing(event_data, stripe_service, db)

        # Customer events
        elif event_type == "customer.created":
            await handle_customer_created(event_data, stripe_service, db)
        elif event_type == "customer.updated":
            await handle_customer_updated(event_data, stripe_service, db)

        # Invoice events
        elif event_type == "invoice.created":
            await handle_invoice_created(event_data, stripe_service, db)
        elif event_type == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(event_data, stripe_service, db)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(event_data, stripe_service, db)

        # Checkout events
        elif event_type == "checkout.session.completed":
            await handle_checkout_session_completed(event_data, stripe_service, db)

        # Refund and dispute events
        elif event_type == "charge.refunded":
            await handle_charge_refunded(event_data, stripe_service, db)
        elif event_type == "charge.dispute.created":
            await handle_dispute_created(event_data, stripe_service, db)

        # Subscription events
        elif event_type in [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ]:
            await handle_subscription_event(event_data, event_type, stripe_service, db)

        # Quote events
        elif event_type == "quote.accepted":
            await handle_quote_accepted(event_data, stripe_service, db)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        return True

    except Exception as e:
        logger.exception(f"Error handling {event_type}: {e}")
        return False


# ============================================================================
# PAYMENT INTENT HANDLERS
# ============================================================================


async def handle_payment_intent_succeeded(
    payment_intent: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle successful payment intent."""
    metadata = payment_intent.get("metadata", {})
    amount_cents = payment_intent["amount"]
    amount_dollars = amount_cents / 100

    logger.info(
        f"[PAYMENT SUCCESS] ID: {payment_intent['id']}, "
        f"Amount: ${amount_dollars:.2f}, "
        f"Customer: {metadata.get('customerName', 'Unknown')}, "
        f"Booking: {metadata.get('bookingId', 'N/A')}"
    )

    # Update payment record in database
    payment_intent_id = payment_intent["id"]
    result = await db.execute(
        select(StripePayment).where(StripePayment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.SUCCEEDED
        payment.stripe_charge_id = payment_intent.get("latest_charge")
        await db.commit()
        logger.info(f"Payment record updated: {payment.id}")

    # Update customer analytics
    customer_id = payment_intent.get("customer")
    if customer_id:
        try:
            await stripe_service.update_payment_preferences(
                customer_id,
                {
                    "preferredPaymentMethod": "stripe",
                    "lastPaymentAmount": amount_dollars,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to update customer preferences: {e}")

    # TODO: Update booking status if booking_id in metadata
    # TODO: Send confirmation email


async def handle_payment_intent_failed(
    payment_intent: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle failed payment intent."""
    metadata = payment_intent.get("metadata", {})
    last_error = payment_intent.get("last_payment_error", {})
    error_message = last_error.get("message", "Unknown error")
    error_code = last_error.get("code", "unknown")

    logger.warning(
        f"[PAYMENT FAILED] ID: {payment_intent['id']}, "
        f"Amount: ${(payment_intent['amount'] / 100):.2f}, "
        f"Error: {error_code} - {error_message}"
    )

    # Update payment record
    payment_intent_id = payment_intent["id"]
    result = await db.execute(
        select(StripePayment).where(StripePayment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.FAILED
        payment.failure_code = error_code
        payment.failure_message = error_message
        await db.commit()
        logger.info(f"Payment record marked as failed: {payment.id}")

    # TODO: Send failure notification to customer
    # TODO: Notify admin for manual follow-up if high value


async def handle_payment_intent_canceled(
    payment_intent: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle canceled payment intent."""
    metadata = payment_intent.get("metadata", {})

    logger.info(
        f"[PAYMENT CANCELED] ID: {payment_intent['id']}, "
        f"Amount: ${(payment_intent['amount'] / 100):.2f}, "
        f"Booking: {metadata.get('bookingId', 'N/A')}"
    )

    # Update payment record
    payment_intent_id = payment_intent["id"]
    result = await db.execute(
        select(StripePayment).where(StripePayment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.CANCELED
        await db.commit()

    # TODO: Update booking status if applicable


async def handle_payment_intent_processing(
    payment_intent: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle payment intent in processing state."""
    logger.info(
        f"[PAYMENT PROCESSING] ID: {payment_intent['id']}, "
        f"Amount: ${(payment_intent['amount'] / 100):.2f}"
    )

    # Update payment record
    payment_intent_id = payment_intent["id"]
    result = await db.execute(
        select(StripePayment).where(StripePayment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.PROCESSING
        await db.commit()


# ============================================================================
# CUSTOMER HANDLERS
# ============================================================================


async def handle_customer_created(
    customer: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle new Stripe customer creation."""
    logger.info(
        f"[CUSTOMER CREATED] ID: {customer['id']}, " f"Email: {customer.get('email', 'No email')}"
    )

    # TODO: Link Stripe customer to local user if email matches
    # TODO: Send welcome email with Zelle savings promotion


async def handle_customer_updated(
    customer: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle Stripe customer update."""
    logger.info(f"[CUSTOMER UPDATED] ID: {customer['id']}")

    # Check if they updated preferred payment to Zelle (smart choice!)
    metadata = customer.get("metadata", {})
    preferred_method = metadata.get("preferredPaymentMethod")
    if preferred_method == "zelle":
        logger.info(f"[SMART CHOICE] Customer {customer['id']} chose Zelle - 3% savings!")
        # TODO: Send congratulations email for choosing Zelle


# ============================================================================
# INVOICE HANDLERS
# ============================================================================


async def handle_invoice_created(
    invoice: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle invoice creation."""
    logger.info(
        f"[INVOICE CREATED] ID: {invoice['id']}, "
        f"Amount: ${(invoice.get('amount_due', 0) / 100):.2f}"
    )

    # TODO: Create local invoice record linked to booking


async def handle_invoice_payment_succeeded(
    invoice: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle successful invoice payment."""
    logger.info(
        f"[INVOICE PAID] ID: {invoice['id']}, "
        f"Amount: ${(invoice.get('amount_paid', 0) / 100):.2f}"
    )

    # Update local invoice record
    stripe_invoice_id = invoice["id"]
    result = await db.execute(select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id))
    local_invoice = result.scalar_one_or_none()

    if local_invoice:
        local_invoice.status = InvoiceStatus.PAID
        local_invoice.paid_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Invoice record updated: {local_invoice.id}")

    # TODO: Update booking payment status


async def handle_invoice_payment_failed(
    invoice: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle failed invoice payment."""
    logger.warning(
        f"[INVOICE FAILED] ID: {invoice['id']}, "
        f"Amount: ${(invoice.get('amount_due', 0) / 100):.2f}"
    )

    # Update local invoice record
    stripe_invoice_id = invoice["id"]
    result = await db.execute(select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id))
    local_invoice = result.scalar_one_or_none()

    if local_invoice:
        local_invoice.status = InvoiceStatus.PAYMENT_FAILED
        await db.commit()

    # TODO: Send payment failure notification


# ============================================================================
# CHECKOUT, REFUND, AND OTHER HANDLERS
# ============================================================================


async def handle_checkout_session_completed(
    session: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle checkout session completion."""
    metadata = session.get("metadata", {})
    payment_status = session.get("payment_status")

    logger.info(
        f"[CHECKOUT COMPLETED] ID: {session['id']}, "
        f"Status: {payment_status}, "
        f"Booking: {metadata.get('booking_id', 'N/A')}"
    )

    if payment_status == "paid":
        # Payment was successful
        booking_id = metadata.get("booking_id")
        if booking_id:
            # TODO: Update booking status to confirmed
            pass

        # Create payment record if not already created
        payment_intent_id = session.get("payment_intent")
        if payment_intent_id:
            existing = await db.execute(
                select(StripePayment).where(
                    StripePayment.stripe_payment_intent_id == payment_intent_id
                )
            )
            if not existing.scalar_one_or_none():
                # Create new payment record
                # This would be handled by payment_intent.succeeded handler
                pass


async def handle_charge_refunded(
    charge: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle charge refund."""
    refund_amount = charge.get("amount_refunded", 0)
    original_amount = charge.get("amount", 0)

    logger.info(
        f"[CHARGE REFUNDED] ID: {charge['id']}, "
        f"Refunded: ${(refund_amount / 100):.2f} of ${(original_amount / 100):.2f}"
    )

    # Update payment record
    payment_intent_id = charge.get("payment_intent")
    if payment_intent_id:
        result = await db.execute(
            select(StripePayment).where(StripePayment.stripe_payment_intent_id == payment_intent_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            if refund_amount >= original_amount:
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED
            payment.refunded_amount = refund_amount
            await db.commit()
            logger.info(f"Payment record updated for refund: {payment.id}")


async def handle_dispute_created(
    dispute: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle dispute creation - CRITICAL event requiring immediate attention."""
    charge_id = dispute.get("charge")
    amount = dispute.get("amount", 0)
    reason = dispute.get("reason", "unknown")

    logger.critical(
        f"[DISPUTE CREATED] ID: {dispute['id']}, "
        f"Charge: {charge_id}, "
        f"Amount: ${(amount / 100):.2f}, "
        f"Reason: {reason}"
    )

    # TODO: Send immediate notification to admin
    # TODO: Create dispute record in database for tracking
    # Disputes require response within 7-21 days depending on card network


async def handle_subscription_event(
    subscription: dict,
    event_type: str,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle subscription lifecycle events."""
    status = subscription.get("status")
    customer_id = subscription.get("customer")

    logger.info(
        f"[SUBSCRIPTION {event_type.split('.')[-1].upper()}] ID: {subscription['id']}, "
        f"Status: {status}, "
        f"Customer: {customer_id}"
    )

    # TODO: Update local subscription record
    # TODO: Send appropriate notification based on event type


async def handle_quote_accepted(
    quote: dict,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle quote acceptance."""
    logger.info(
        f"[QUOTE ACCEPTED] ID: {quote['id']}, "
        f"Amount: ${(quote.get('amount_total', 0) / 100):.2f}"
    )

    # TODO: Convert quote to invoice/booking
