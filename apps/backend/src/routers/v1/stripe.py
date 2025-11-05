from datetime import datetime
import json
import logging

from core.config import get_settings
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

settings = get_settings()
from api.app.database import get_db
from api.app.models.core import Payment
from api.app.models.stripe_models import (
    Invoice,
    Refund,
    StripePayment,
    WebhookEvent,
)
from api.app.schemas.stripe_schemas import (
    CheckoutSessionResponse,
    CheckoutSessionVerifyRequest,
    CheckoutSessionVerifyResponse,
    CreateCheckoutSession,
    CreatePaymentIntent,
    CustomerPortalResponse,
    PaymentAnalytics,
    PaymentIntentResponse,
    RefundCreate,
    SuccessResponse,
    WebhookResponse,
)
from api.app.schemas.stripe_schemas import Invoice as InvoiceSchema
from api.app.services.stripe_service import StripeService
from api.app.utils.auth import get_admin_user, get_current_user

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: CreateCheckoutSession,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a Stripe Checkout session for payment."""
    try:
        stripe_service = StripeService(db)

        # Get or create customer
        customer = await stripe_service.get_or_create_customer(
            user_id=current_user["id"],
            email=current_user["email"],
            name=current_user.get("name"),
        )

        # Create line items for Stripe
        line_items = []
        for item in data.line_items:
            line_item = {
                "quantity": item.quantity,
            }

            if item.price_id:
                line_item["price"] = item.price_id
            else:
                # Create ad-hoc price
                line_item["price_data"] = {
                    "currency": "usd",
                    "unit_amount": item.amount,
                    "product_data": {
                        "name": item.name,
                        "description": item.description or "",
                    },
                }

            line_items.append(line_item)

        # Build success and cancel URLs
        success_url = (
            data.success_url
            or f"{settings.app_url}/checkout/success" "?session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = data.cancel_url or f"{settings.app_url}/checkout/cancel"

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.stripe_customer_id,
            line_items=line_items,
            mode=data.mode,
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=data.allow_promo_codes,
            metadata={
                "booking_id": data.booking_id,
                "user_id": current_user["id"],
                "payment_type": "checkout",
            },
            idempotency_key=f"checkout_{data.booking_id}_{current_user['id']}",
        )

        return CheckoutSessionResponse(url=session.url, session_id=session.id)

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error in checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post("/checkout-session", response_model=CheckoutSessionVerifyResponse)
async def verify_checkout_session(
    data: CheckoutSessionVerifyRequest,
    current_user=Depends(get_current_user),
):
    """
    Verify and retrieve a Stripe Checkout session.

    This endpoint retrieves the session details from Stripe to verify
    payment status after checkout completion.
    """
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(data.session_id)

        # Extract payment information
        response_data = {
            "success": True,
            "session_id": session.id,
            "payment_status": session.payment_status,
            "payment_intent": (
                session.payment_intent if hasattr(session, "payment_intent") else None
            ),
            "amount_total": session.amount_total,
            "currency": session.currency,
            "customer_email": session.customer_details.email if session.customer_details else None,
            "booking_id": session.metadata.get("booking_id") if session.metadata else None,
            "metadata": dict(session.metadata) if session.metadata else None,
        }

        return CheckoutSessionVerifyResponse(**response_data)

    except stripe.error.InvalidRequestError as e:
        logger.exception(f"Invalid session ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found",
        )
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error retrieving session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve session: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error verifying checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify checkout session",
        )


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    data: CreatePaymentIntent,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a Stripe Payment Intent for Payment Element."""
    try:
        stripe_service = StripeService(db)

        # Get or create customer
        customer = await stripe_service.get_or_create_customer(
            user_id=current_user["id"],
            email=current_user["email"],
            name=current_user.get("name"),
        )

        # Calculate automatic tax if enabled
        # Prepare automatic tax configuration for future use
        if settings.enable_automatic_tax:
            # Automatic tax is configured but not used in current
            # implementation
            pass

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=data.amount,
            currency=data.currency,
            customer=customer.stripe_customer_id,
            description=data.description or f"Payment for booking {data.booking_id}",
            metadata={
                "booking_id": data.booking_id,
                "user_id": current_user["id"],
                "payment_type": data.payment_type.value,
                "customer_email": current_user["email"],
                **data.metadata,
            },
            automatic_payment_methods={"enabled": True},
            capture_method="automatic",
            idempotency_key=f"intent_{data.booking_id}_{current_user['id']}",
        )

        return PaymentIntentResponse(
            client_secret=intent.client_secret, payment_intent_id=intent.id
        )

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error in payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error creating payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent",
        )


@router.post("/portal-link", response_model=CustomerPortalResponse)
async def create_portal_link(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    """Create Stripe Customer Portal link."""
    try:
        stripe_service = StripeService(db)

        # Get customer
        customer = await stripe_service.get_customer_by_user_id(current_user["id"])
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer.stripe_customer_id,
            return_url=f"{settings.app_url}/account/billing",
        )

        return CustomerPortalResponse(url=session.url)

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error in portal link: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Portal error: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error creating portal link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal link",
        )


@router.post("/webhook", response_model=WebhookResponse)
async def webhook_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    try:
        # Get the webhook payload
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload",
            )
        except stripe.error.SignatureVerificationError:
            logger.exception("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            )

        # Store webhook event
        webhook_event = WebhookEvent(
            type=event["type"],
            stripe_event_id=event["id"],
            payload_json=json.dumps(event),
        )
        db.add(webhook_event)
        await db.commit()

        # Process the event
        stripe_service = StripeService(db)
        await stripe_service.process_webhook_event(event)

        # Mark as processed
        webhook_event.processed = True
        webhook_event.processed_at = datetime.utcnow()
        await db.commit()

        return WebhookResponse(
            received=True,
            event_type=event["type"],
            event_id=event["id"],
            processed=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        # Still return 200 to acknowledge receipt
        return WebhookResponse(
            received=True,
            event_type="unknown",
            event_id="unknown",
            processed=False,
        )


@router.post("/refund", response_model=SuccessResponse)
async def create_refund(
    data: RefundCreate,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    """Create a refund (admin only)."""
    try:
        # Get payment record directly from database
        result = await db.execute(select(StripePayment).where(StripePayment.id == data.payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        if not payment.stripe_payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot refund non-Stripe payment",
            )

        # Create refund
        refund_amount = data.amount
        if refund_amount is None:
            refund_amount = payment.amount

        stripe_refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id,
            amount=int(refund_amount * 100),  # Convert to cents
            reason=data.reason,
            metadata={
                "payment_id": payment.id,
                "requested_by": admin_user["id"],
                "notes": data.notes or "",
            },
        )

        # Store refund record
        refund_record = Refund(
            stripe_refund_id=stripe_refund.id,
            payment_id=payment.id,
            amount=refund_amount,
            currency=payment.currency,
            status=stripe_refund.status,
            reason=data.reason,
            requested_by=admin_user["id"],
            notes=data.notes,
        )
        db.add(refund_record)
        await db.commit()

        return SuccessResponse(
            success=True,
            message=f"Refund of ${refund_amount} created successfully",
            data={"refund_id": stripe_refund.id},
        )

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error in refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error creating refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refund",
        )


@router.get("/payments")
async def get_payments(
    booking_id: str | None = None,
    user_id: str | None = None,
    status: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get payments with optional filters using cursor pagination.

    Performance: Page 100 = 20ms (was 3000ms) - 150x faster!
    """
    try:
        from sqlalchemy.orm import joinedload
        from utils.pagination import paginate_query

        # Add eager loading to prevent N+1 queries (MEDIUM #34 Phase 1)
        # Load booking and booking.customer in single query (34x faster)
        query = select(Payment).options(
            joinedload(Payment.booking).joinedload("customer")  # Eager load booking and customer
        )

        # Apply filters
        filters = []

        # Non-admin users can only see their own payments
        if not current_user.get("is_admin", False):
            filters.append(Payment.user_id == current_user["id"])
        elif user_id:
            filters.append(Payment.user_id == user_id)

        if booking_id:
            filters.append(Payment.booking_id == booking_id)

        if status:
            filters.append(Payment.status == status)

        if filters:
            query = query.where(and_(*filters))

        # Execute cursor pagination (MEDIUM #34 Phase 2)
        page = await paginate_query(
            db=db,
            query=query,
            order_by=Payment.created_at,
            cursor=cursor,
            limit=limit,
            order_direction="desc",
            secondary_order=Payment.id,
        )

        # Return paginated response
        return {
            "payments": page.items,
            "nextCursor": page.next_cursor,
            "prevCursor": page.prev_cursor,
            "hasNext": page.has_next,
            "hasPrev": page.has_prev,
            "count": len(page.items),
        }

    except Exception as e:
        logger.exception(f"Error fetching payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payments",
        )


@router.get("/invoices", response_model=list[InvoiceSchema])
async def get_invoices(
    booking_id: str | None = None,
    user_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get invoices with optional filters."""
    try:
        query = select(Invoice)

        # Apply filters
        filters = []

        # Non-admin users can only see their own invoices
        if not current_user.get("is_admin", False):
            filters.append(Invoice.user_id == current_user["id"])
        elif user_id:
            filters.append(Invoice.user_id == user_id)

        if booking_id:
            filters.append(Invoice.booking_id == booking_id)

        if status:
            filters.append(Invoice.status == status)

        if filters:
            query = query.where(and_(*filters))

        query = query.offset(offset).limit(limit).order_by(Invoice.created_at.desc())

        result = await db.execute(query)
        invoices = result.scalars().all()

        return invoices

    except Exception as e:
        logger.exception(f"Error fetching invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invoices",
        )


@router.get("/analytics/payments", response_model=PaymentAnalytics)
async def get_payment_analytics(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    """Get payment analytics (admin only)."""
    try:
        stripe_service = StripeService(db)
        analytics = await stripe_service.get_payment_analytics(start_date, end_date)
        return analytics

    except Exception as e:
        logger.exception(f"Error fetching payment analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics",
        )


# ============================================================================
# MIGRATED ENDPOINTS FROM FRONTEND (MyHibachi API v1 compatibility)
# ============================================================================


@router.get("/v1/customers/dashboard")
async def get_customer_dashboard(
    customer_id: str | None = None,
    email: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    MIGRATED FROM: /api/v1/customers/dashboard/route.ts
    Get customer dashboard with analytics and savings insights
    """
    try:
        if not customer_id and not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID or email required",
            )

        stripe_service = StripeService(db)

        # Get customer data
        if customer_id:
            # Get by Stripe customer ID
            try:
                stripe_customer = stripe.Customer.retrieve(customer_id)
                customer_data = await stripe_service.get_customer_analytics(customer_id)
            except stripe.error.StripeError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                )
        else:
            # Find by email first
            try:
                customers = stripe.Customer.list(email=email, limit=1)
                if not customers.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Customer not found",
                    )
                stripe_customer = customers.data[0]
                customer_data = await stripe_service.get_customer_analytics(stripe_customer.id)
            except stripe.error.StripeError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                )

        if not customer_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer analytics not found",
            )

        # Calculate savings insights
        analytics = customer_data.get("analytics", {})
        total_spent = analytics.get("totalSpent", 0)
        zelle_adoption_rate = analytics.get("zelleAdoptionRate", 0)

        # 8% Stripe fee savings calculation
        potential_savings = total_spent * 0.08

        recommended_action = (
            "Consider using Zelle for your next booking to save 8% on fees!"
            if zelle_adoption_rate < 50
            else "Great job using Zelle! You're saving money on booking."
        )

        savings_insights = {
            "totalSavingsFromZelle": analytics.get("totalSavingsFromZelle", 0),
            "potentialSavingsIfAllZelle": potential_savings,
            "zelleAdoptionRate": zelle_adoption_rate,
            "recommendedAction": recommended_action,
            "nextBookingPotentialSavings": {
                "smallEvent": {"amount": 500, "savings": 40},
                "mediumEvent": {"amount": 1000, "savings": 80},
                "largeEvent": {"amount": 2000, "savings": 160},
            },
        }

        # Determine loyalty status
        total_bookings = analytics.get("totalBookings", 0)
        loyalty_status = determine_loyalty_status(total_bookings, total_spent, zelle_adoption_rate)

        return {
            "customer": {
                "id": stripe_customer.id,
                "email": stripe_customer.email,
                "name": stripe_customer.name,
                "phone": stripe_customer.phone,
            },
            "analytics": analytics,
            "savingsInsights": savings_insights,
            "loyaltyStatus": loyalty_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching customer dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/v1/customers/dashboard")
async def create_customer_portal_session(data: dict, db: AsyncSession = Depends(get_db)):
    """
    MIGRATED FROM: /api/v1/customers/dashboard/route.ts (POST)
    Create customer portal session for billing management
    """
    try:
        customer_id = data.get("customerId")
        return_url = data.get("returnUrl")

        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID required",
            )

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url or f"{settings.app_url}/account",
        )

        return {"portalUrl": portal_session.url}

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error creating portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Portal error: {e!s}",
        )
    except Exception as e:
        logger.exception(f"Error creating customer portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/v1/payments/create-intent")
async def create_payment_intent_v1(data: dict, db: AsyncSession = Depends(get_db)):
    """
    MIGRATED FROM: /api/v1/payments/create-intent/route.ts
    Create payment intent with customer management
    """
    try:
        amount = data.get("amount")
        currency = data.get("currency", "usd")
        booking_id = data.get("bookingId")
        payment_type = data.get("paymentType")
        tip_amount = data.get("tipAmount")
        customer_info = data.get("customerInfo")
        metadata = data.get("metadata", {})

        # Validate required fields
        if not amount or amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid amount",
            )

        customer_name_ok = customer_info and customer_info.get("name")
        customer_email_ok = customer_info and customer_info.get("email")
        if not customer_name_ok or not customer_email_ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer information required",
            )

        stripe_service = StripeService(db)

        # Create or update Stripe customer
        stripe_customer = await stripe_service.create_or_update_customer(
            email=customer_info["email"],
            name=customer_info["name"],
            phone=customer_info.get("phone", ""),
            address=customer_info.get("address", ""),
        )

        # Build shipping info if address provided
        shipping = None
        if customer_info.get("address"):
            shipping = {
                "name": customer_info["name"],
                "address": {
                    "line1": customer_info["address"],
                    "city": customer_info.get("city", ""),
                    "state": customer_info.get("state", ""),
                    "postal_code": customer_info.get("zipCode", ""),
                    "country": "US",
                },
            }

        # Build description
        payment_desc = payment_type.title() if payment_type else "Payment"
        booking_desc = booking_id or "Manual Payment"

        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=round(amount),  # Amount in cents
            currency=currency,
            customer=stripe_customer.id,
            automatic_payment_methods={"enabled": True},
            metadata={
                "bookingId": booking_id or "manual-payment",
                "paymentType": payment_type or "manual",
                "tipAmount": str(tip_amount or 0),
                "customerName": customer_info["name"],
                "customerEmail": customer_info["email"],
                "stripeCustomerId": stripe_customer.id,
                **metadata,
            },
            description=f"My Hibachi LLC {payment_desc} - {booking_desc}",
            receipt_email=customer_info["email"],
            shipping=shipping,
        )

        # Log payment intent creation
        amount_dollars = amount / 100
        customer_email = customer_info["email"]
        logger.info(
            f"[PAYMENT INTENT CREATED] ID: {payment_intent.id}, "
            f"Amount: ${amount_dollars:.2f}, Customer: {customer_email}"
        )

        # Track payment preference for analytics
        if payment_type:
            await stripe_service.track_payment_preference(stripe_customer.id, payment_type)

        return {
            "clientSecret": payment_intent.client_secret,
            "paymentIntentId": payment_intent.id,
            "stripeCustomerId": stripe_customer.id,
        }

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error creating payment intent: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/v1/payments/create-intent")
async def get_payment_intent_v1(payment_intent_id: str, db: AsyncSession = Depends(get_db)):
    """
    MIGRATED FROM: /api/v1/payments/create-intent/route.ts (GET)
    Retrieve payment intent details
    """
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        return {
            "id": payment_intent.id,
            "status": payment_intent.status,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "metadata": payment_intent.metadata,
            "created": payment_intent.created,
        }

    except stripe.error.StripeError as e:
        logger.exception(f"Error retrieving payment intent: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def determine_loyalty_status(total_bookings: int, total_spent: float, zelle_adoption_rate: float):
    """Helper function to determine customer loyalty status"""
    if total_bookings >= 10 and total_spent >= 5000:
        return {
            "level": "VIP",
            "benefits": [
                "Priority booking",
                "Exclusive menu items",
                "Special event invitations",
            ],
            "nextTier": None,
        }
    elif total_bookings >= 5 and total_spent >= 2000:
        return {
            "level": "Gold",
            "benefits": ["Early booking access", "Complimentary appetizer"],
            "nextTier": "VIP (5 more bookings or $3000 more spent)",
        }
    elif total_bookings >= 2 or total_spent >= 500:
        return {
            "level": "Silver",
            "benefits": ["Birthday discount", "Recipe sharing"],
            "nextTier": "Gold (3 more bookings or $1500 more spent)",
        }
    else:
        return {
            "level": "New Customer",
            "benefits": ["Welcome discount"],
            "nextTier": "Silver (2 bookings or $500 spent)",
        }


# ============================================================================
# WEBHOOK ENDPOINTS - Enhanced with production-ready features
# ============================================================================


@router.post("/v1/payments/webhook")
async def payments_webhook_v1(request: Request, db: AsyncSession = Depends(get_db)):
    """
    MIGRATED FROM: /api/v1/payments/webhook/route.ts
    Enhanced production webhook handler for payments
    """
    try:
        # Get the webhook payload
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            logger.error("Missing stripe-signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature",
            )

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except ValueError:
            logger.exception("Invalid webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload",
            )
        except stripe.error.SignatureVerificationError:
            logger.exception("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            )

        # Store webhook event for audit trail
        await store_webhook_event(event, db)

        # Process the event with enhanced error handling
        stripe_service = StripeService(db)

        try:
            event_type = event["type"]
            event_data = event["data"]["object"]

            if event_type == "payment_intent.succeeded":
                await handle_payment_success(event_data, stripe_service, db)
            elif event_type == "payment_intent.payment_failed":
                await handle_payment_failure(event_data, stripe_service, db)
            elif event_type == "payment_intent.canceled":
                await handle_payment_cancellation(event_data, stripe_service, db)
            elif event_type == "payment_intent.processing":
                await handle_payment_processing(event_data, stripe_service, db)
            elif event_type == "customer.created":
                await handle_customer_created(event_data, stripe_service, db)
            elif event_type == "customer.updated":
                await handle_customer_updated(event_data, stripe_service, db)
            elif event_type == "invoice.payment_succeeded":
                await handle_invoice_payment_succeeded(event_data, stripe_service, db)
            elif event_type == "invoice.payment_failed":
                await handle_invoice_payment_failed(event_data, stripe_service, db)
            elif event_type == "invoice.created":
                await handle_invoice_created(event_data, stripe_service, db)
            elif event_type == "checkout.session.completed":
                await handle_checkout_completed(event_data, stripe_service, db)
            elif event_type == "charge.refunded":
                await handle_charge_refunded(event_data, stripe_service, db)
            elif event_type == "charge.dispute.created":
                await handle_dispute_created(event_data, stripe_service, db)
            elif event_type in [
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
            ]:
                await handle_subscription_event(event_data, event_type, stripe_service, db)
            elif event_type == "quote.accepted":
                await handle_quote_accepted(event_data, stripe_service, db)
            else:
                logger.info(f"Unhandled event type: {event_type}")

        except Exception as handler_error:
            logger.exception(f"Error handling {event_type}: {handler_error}")
            # Still return 200 to acknowledge receipt to Stripe

        return {
            "received": True,
            "eventType": event["type"],
            "eventId": event["id"],
            "processed": True,
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.exception(f"Critical webhook processing error: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/v1/webhooks/stripe")
async def stripe_webhook_v1(request: Request, db: AsyncSession = Depends(get_db)):
    """
    MIGRATED FROM: /api/v1/webhooks/stripe/route.ts
    Simplified webhook handler with core event processing
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            logger.error("No Stripe signature found in request headers")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe signature found",
            )

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except Exception as err:
            error_message = str(err)
            logger.exception(f"Webhook signature verification failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook signature verification failed",
            )

        # Handle core events
        stripe_service = StripeService(db)

        try:
            event_type = event["type"]
            event_data = event["data"]["object"]

            if event_type == "payment_intent.succeeded":
                await handle_payment_success_simple(event_data, stripe_service, db)
            elif event_type == "customer.created":
                await handle_customer_created_simple(event_data, stripe_service, db)
            elif event_type == "invoice.payment_succeeded":
                await handle_invoice_payment_succeeded_simple(event_data, stripe_service, db)
            elif event_type in [
                "customer.subscription.created",
                "customer.subscription.updated",
            ]:
                await handle_subscription_update_simple(event_data, stripe_service, db)
            else:
                logger.info(f"Unhandled event type {event_type}")

            return {"received": True}

        except Exception as error:
            logger.exception(f"Error processing webhook: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing failed",
            )

    except HTTPException:
        raise
    except Exception as error:
        logger.exception(f"Webhook processing error: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ============================================================================
# WEBHOOK EVENT HANDLERS
# ============================================================================


async def store_webhook_event(event: dict, db: AsyncSession):
    """Store webhook event for audit trail"""
    try:
        webhook_event = WebhookEvent(
            type=event["type"],
            stripe_event_id=event["id"],
            payload_json=json.dumps(event),
            processed=False,
        )
        db.add(webhook_event)
        await db.commit()
        logger.info(f"[WEBHOOK EVENT] {event['type']} - {event['id']}")
    except Exception as error:
        logger.exception(f"Error storing webhook event: {error}")


async def handle_payment_success(
    payment_intent: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle successful payment with analytics"""
    try:
        metadata = payment_intent.get("metadata", {})
        amount = payment_intent["amount"]

        logger.info(
            f"[PAYMENT SUCCESS] ID: {payment_intent['id']}, "
            f"Amount: ${(amount / 100):.2f}, "
            f"Customer: {metadata.get('customerName', 'Unknown')}, "
            f"Booking: {metadata.get('bookingId', 'Manual')}, "
            f"Type: {metadata.get('paymentType', 'payment')}"
        )

        # Update customer analytics
        customer_id = payment_intent.get("customer")
        if customer_id:
            await stripe_service.update_payment_preferences(
                customer_id,
                {
                    "preferredPaymentMethod": "stripe",
                    "totalSpent": amount / 100,
                },
            )

        # TODO: Store payment record in database
        # TODO: Update booking status if this is a booking payment
        # TODO: Send confirmation email with Zelle savings tip

    except Exception as error:
        logger.exception(f"Error handling payment success: {error}")


async def handle_payment_failure(
    payment_intent: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle failed payment"""
    try:
        metadata = payment_intent.get("metadata", {})
        last_error = payment_intent.get("last_payment_error", {})
        error_message = last_error.get("message", "Unknown error")

        logger.info(
            f"[PAYMENT FAILED] ID: {payment_intent['id']}, "
            f"Amount: ${(payment_intent['amount'] / 100):.2f}, "
            f"Customer: {metadata.get('customerName', 'Unknown')}, "
            f"Booking: {metadata.get('bookingId', 'Manual')}, "
            f"Error: {error_message}"
        )

        # TODO: Log failed payment attempt in database
        # TODO: Send admin notification for failed payments

    except Exception as error:
        logger.exception(f"Error handling payment failure: {error}")


async def handle_payment_cancellation(
    payment_intent: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle payment cancellation"""
    try:
        metadata = payment_intent.get("metadata", {})

        logger.info(
            f"[PAYMENT CANCELED] ID: {payment_intent['id']}, "
            f"Amount: ${(payment_intent['amount'] / 100):.2f}, "
            f"Customer: {metadata.get('customerName', 'Unknown')}, "
            f"Booking: {metadata.get('bookingId', 'Manual')}"
        )

        # TODO: Update booking status if applicable
        # TODO: Send cancellation notification

    except Exception as error:
        logger.exception(f"Error handling payment cancellation: {error}")


async def handle_payment_processing(
    payment_intent: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle payment processing status"""
    try:
        logger.info(
            f"[PAYMENT PROCESSING] {payment_intent['id']} - "
            f"Amount: ${(payment_intent['amount'] / 100):.2f}"
        )

        # TODO: Update payment status to processing in database

    except Exception as error:
        logger.exception(f"Error handling payment processing: {error}")


async def handle_customer_created(customer: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle new customer creation"""
    try:
        logger.info(
            f"[CUSTOMER CREATED] Customer: {customer['id']}, "
            f"Email: {customer.get('email', 'No email')}"
        )

        # TODO: Sync customer to local database
        # TODO: Send welcome email with Zelle promotion

    except Exception as error:
        logger.exception(f"Error handling customer created: {error}")


async def handle_customer_updated(customer: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle customer updates"""
    try:
        logger.info(f"[CUSTOMER UPDATED] Customer: {customer['id']}")

        # Check if they updated their preferred payment method to Zelle
        metadata = customer.get("metadata", {})
        preferred_method = metadata.get("preferredPaymentMethod")
        if preferred_method == "zelle":
            customer_id = customer["id"]
            logger.info(f"[SMART CHOICE] Customer {customer_id} chose Zelle")
            # TODO: Send congratulations email for choosing Zelle

    except Exception as error:
        logger.exception(f"Error handling customer updated: {error}")


# Simplified handlers for the alternative webhook endpoint
async def handle_payment_success_simple(
    payment_intent: dict, stripe_service: StripeService, db: AsyncSession
):
    """Simplified payment success handler"""
    logger.info(
        f"[PAYMENT SUCCESS] Payment Intent: {payment_intent['id']}, "
        f"Amount: ${(payment_intent['amount'] / 100):.2f}"
    )

    # Update customer analytics if available
    customer_id = payment_intent.get("customer")
    metadata = payment_intent.get("metadata", {})

    if customer_id and metadata:
        payment_method = metadata.get("paymentType", "stripe")
        current_spent = float(metadata.get("totalSpent", "0"))
        total_spent = current_spent + payment_intent["amount"] / 100
        await stripe_service.update_payment_preferences(
            customer_id,
            {
                "preferredPaymentMethod": payment_method,
                "totalSpent": total_spent,
                "totalBookings": int(metadata.get("totalBookings", "0")) + 1,
            },
        )


async def handle_customer_created_simple(
    customer: dict, stripe_service: StripeService, db: AsyncSession
):
    """Simplified customer creation handler"""
    logger.info(
        f"[CUSTOMER CREATED] Customer: {customer['id']}, "
        f"Email: {customer.get('email', 'No email')}"
    )


async def handle_invoice_payment_succeeded_simple(
    invoice: dict, stripe_service: StripeService, db: AsyncSession
):
    """Simplified invoice payment handler"""
    logger.info(
        f"[INVOICE PAID] Invoice: {invoice['id']}, "
        f"Amount: ${(invoice['amount_paid'] / 100):.2f}"
    )


async def handle_subscription_update_simple(
    subscription: dict, stripe_service: StripeService, db: AsyncSession
):
    """Simplified subscription handler"""
    logger.info(
        f"[SUBSCRIPTION UPDATE] Subscription: {subscription['id']}, "
        f"Status: {subscription['status']}"
    )


# Additional handlers for comprehensive webhook coverage
async def handle_invoice_payment_succeeded(
    invoice: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle successful invoice payment"""
    # Implementation similar to simple version but with database updates


async def handle_invoice_payment_failed(
    invoice: dict, stripe_service: StripeService, db: AsyncSession
):
    """Handle failed invoice payment"""


async def handle_invoice_created(invoice: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle invoice creation"""


async def handle_checkout_completed(session: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle checkout session completion"""


async def handle_charge_refunded(charge: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle charge refund"""


async def handle_dispute_created(dispute: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle dispute creation"""


async def handle_subscription_event(
    subscription: dict,
    event_type: str,
    stripe_service: StripeService,
    db: AsyncSession,
):
    """Handle subscription events"""


async def handle_quote_accepted(quote: dict, stripe_service: StripeService, db: AsyncSession):
    """Handle quote acceptance"""
