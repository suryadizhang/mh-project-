"""
Stripe Service - Leveraging Stripe's Built-in Features

ARCHITECTURE DECISION (November 23, 2025):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
We leverage Stripe's comprehensive built-in capabilities instead of
building custom implementations:

✅ STRIPE NATIVE FEATURES WE USE:
1. Stripe Dashboard Analytics (https://dashboard.stripe.com/analytics)
   - Revenue reports, trends, forecasts
   - Customer lifetime value
   - Payment success rates
   - Real-time metrics

2. Stripe Reporting API (stripe.reporting.report_run)
   - Automated report generation
   - Custom date ranges
   - CSV/JSON exports

3. Stripe Webhooks (stripe.WebhookEndpoint)
   - Real-time payment notifications
   - Automatic retry logic
   - Event delivery guarantees

4. Stripe Customer Portal (stripe.billing_portal.Session)
   - Self-service payment method management
   - Invoice history
   - Subscription management

5. Stripe Checkout (stripe.checkout.Session)
   - PCI-compliant payment forms
   - Multi-currency support
   - Mobile-optimized UX

❌ REMOVED CUSTOM IMPLEMENTATIONS:
- Custom payment analytics (use Stripe Dashboard)
- Custom customer management (use Stripe API)
- Custom dispute tracking (use Stripe Dashboard)
- Custom invoice generation (use Stripe Invoicing)

💡 BENEFITS:
- Reduced code complexity (500+ lines removed)
- Better security (PCI compliance handled by Stripe)
- Free updates (new features added by Stripe)
- Lower maintenance burden
- Enterprise-grade reliability

📚 DOCUMENTATION:
- Stripe Dashboard: https://dashboard.stripe.com
- API Docs: https://stripe.com/docs/api
- Webhooks Guide: https://stripe.com/docs/webhooks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings

settings = get_settings()
# MIGRATED: from models.booking → db.models.core
from db.models.core import Customer, Payment

# MIGRATED: Stripe models from db.models.stripe
from db.models.stripe import Invoice, StripeCustomer, StripePayment
from schemas.stripe_schemas import PaymentAnalytics

logger = logging.getLogger(__name__)


class StripeService:
    """
    Stripe Service - Minimal wrapper around Stripe API.

    Most functionality delegated to Stripe's native features.
    This service only handles:
    1. Webhook event processing
    2. Database synchronization
    3. Business logic integration
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        stripe.api_key = settings.stripe_secret_key

    async def get_or_create_customer(
        self, user_id: str, email: str, name: str | None = None
    ) -> StripeCustomer:
        """Get existing StripeCustomer or create new one."""
        # Check if StripeCustomer exists
        result = await self.db.execute(
            select(StripeCustomer).where(StripeCustomer.customer_id == user_id)
        )
        existing_customer = result.scalar_one_or_none()

        if existing_customer:
            return existing_customer

        # Create new Stripe customer via API
        stripe_customer_data = stripe.Customer.create(
            email=email,
            name=name,
            description=f"My Hibachi Customer - {email}",
            metadata={
                "user_id": user_id,
                "source": "api",
                "preferred_payment": "zelle",
            },
        )

        # Create StripeCustomer record in our database
        new_customer = StripeCustomer(
            customer_id=user_id,
            stripe_customer_id=stripe_customer_data.id,
            preferred_payment_method="zelle",
        )

        self.db.add(new_customer)
        await self.db.commit()
        await self.db.refresh(new_customer)

        return new_customer

    async def get_customer_by_user_id(self, user_id: str) -> StripeCustomer | None:
        """Get StripeCustomer by user ID."""
        result = await self.db.execute(
            select(StripeCustomer).where(StripeCustomer.customer_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_customer(
        self, user_id: str, email: str, name: str | None = None
    ) -> StripeCustomer:
        """Create or update a Stripe customer record."""
        # Try to find existing
        existing = await self.get_customer_by_user_id(user_id)
        if existing:
            # Update Stripe customer if email/name changed
            if existing.stripe_customer_id:
                try:
                    stripe.Customer.modify(
                        existing.stripe_customer_id,
                        email=email,
                        name=name,
                    )
                except stripe.error.StripeError as e:
                    logger.warning(f"Failed to update Stripe customer: {e}")
            return existing

        # Create new
        return await self.get_or_create_customer(user_id, email, name)

    async def get_customer_analytics(self, customer_id: str | UUID) -> dict[str, Any]:
        """Get analytics for a specific customer."""
        result = await self.db.execute(
            select(StripeCustomer).where(StripeCustomer.id == str(customer_id))
        )
        customer = result.scalar_one_or_none()

        if not customer:
            return {
                "total_spent": 0,
                "total_bookings": 0,
                "loyalty_tier": "bronze",
                "zelle_savings": 0,
            }

        return {
            "total_spent": float(customer.total_spent or 0),
            "total_bookings": customer.total_bookings or 0,
            "loyalty_tier": customer.loyalty_tier or "bronze",
            "zelle_savings": float(customer.zelle_savings or 0),
        }

    async def track_payment_preference(self, customer_id: str | UUID, payment_type: str) -> None:
        """Track customer payment preference for analytics."""
        result = await self.db.execute(
            select(StripeCustomer).where(StripeCustomer.id == str(customer_id))
        )
        customer = result.scalar_one_or_none()

        if customer:
            customer.preferred_payment_method = payment_type
            customer.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def update_payment_preferences(
        self, customer_id: str | UUID, preferences: dict[str, Any]
    ) -> None:
        """Update customer payment preferences."""
        result = await self.db.execute(
            select(StripeCustomer).where(StripeCustomer.id == str(customer_id))
        )
        customer = result.scalar_one_or_none()

        if customer:
            if "preferred_payment_method" in preferences:
                customer.preferred_payment_method = preferences["preferred_payment_method"]
            customer.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def process_webhook_event(self, event: dict[str, Any]) -> None:
        """Process Stripe webhook events."""
        event_type = event["type"]
        data_object = event["data"]["object"]

        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(data_object)

            elif event_type == "payment_intent.succeeded":
                await self._handle_payment_succeeded(data_object)

            elif event_type == "payment_intent.payment_failed":
                await self._handle_payment_failed(data_object)

            elif event_type == "payment_intent.canceled":
                await self._handle_payment_canceled(data_object)

            elif event_type == "invoice.payment_succeeded":
                await self._handle_invoice_payment_succeeded(data_object)

            elif event_type == "invoice.payment_failed":
                await self._handle_invoice_payment_failed(data_object)

            elif event_type == "customer.created":
                await self._handle_StripeCustomer_created(data_object)

            elif event_type == "charge.dispute.created":
                await self._handle_dispute_created(data_object)

            elif event_type.startswith("customer.subscription."):
                await self._handle_subscription_event(data_object, event_type)

            else:
                logger.info(f"Unhandled webhook event: {event_type}")

        except Exception as e:
            logger.exception(f"Error processing webhook {event_type}: {e}")
            raise

    async def _handle_checkout_completed(self, session: dict[str, Any]) -> None:
        """Handle completed checkout session."""
        metadata = session.get("metadata", {})
        booking_id = metadata.get("booking_id")
        user_id = metadata.get("user_id")

        if not booking_id or not user_id:
            logger.warning("Missing booking_id or user_id in checkout session")
            return

        # Get payment intent if available
        payment_intent_id = session.get("payment_intent")
        if payment_intent_id:
            # Retrieve payment intent for more details
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            await self._create_payment_record(payment_intent, "checkout")

        logger.info(f"Checkout completed: {session['id']}, booking: {booking_id}")

    async def _handle_payment_succeeded(self, payment_intent: dict[str, Any]) -> None:
        """Handle successful payment."""
        await self._create_payment_record(payment_intent, "succeeded")
        await self._update_StripeCustomer_analytics(payment_intent)

        logger.info(f"Payment succeeded: {payment_intent['id']}")

    async def _handle_payment_failed(self, payment_intent: dict[str, Any]) -> None:
        """Handle failed payment."""
        metadata = payment_intent.get("metadata", {})

        # Log failed payment
        logger.warning(
            f"Payment failed: {payment_intent['id']}, " f"booking: {metadata.get('booking_id')}"
        )

        # Update payment record if exists
        await self._update_payment_status(payment_intent["id"], "failed")

    async def _handle_payment_canceled(self, payment_intent: dict[str, Any]) -> None:
        """Handle canceled payment."""
        logger.info(f"Payment canceled: {payment_intent['id']}")
        await self._update_payment_status(payment_intent["id"], "canceled")

    async def _handle_invoice_payment_succeeded(self, invoice: dict[str, Any]) -> None:
        """Handle successful invoice payment."""
        # Update invoice record
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == invoice["id"])
        )
        invoice_record = result.scalar_one_or_none()

        if invoice_record:
            invoice_record.status = "paid"
            invoice_record.amount_paid = Decimal(str(invoice["amount_paid"] / 100))
            invoice_record.paid_at = datetime.now(timezone.utc)
            await self.db.commit()

        logger.info(f"Invoice payment succeeded: {invoice['id']}")

    async def _handle_invoice_payment_failed(self, invoice: dict[str, Any]) -> None:
        """Handle failed invoice payment."""
        # Update invoice record
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == invoice["id"])
        )
        invoice_record = result.scalar_one_or_none()

        if invoice_record:
            invoice_record.status = "payment_failed"
            await self.db.commit()

        logger.warning(f"Invoice payment failed: {invoice['id']}")

    async def _handle_StripeCustomer_created(self, StripeCustomer: dict[str, Any]) -> None:
        """Handle StripeCustomer creation."""
        metadata = StripeCustomer.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            logger.warning(f"StripeCustomer created without user_id: {StripeCustomer['id']}")
            return

        # Check if we already have this StripeCustomer
        result = await self.db.execute(
            select(StripeCustomer).where(Customer.stripe_StripeCustomer_id == StripeCustomer["id"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            # Create StripeCustomer record
            StripeCustomer_record = StripeCustomer(
                user_id=user_id,
                email=StripeCustomer["email"],
                name=StripeCustomer.get("name"),
                stripe_StripeCustomer_id=StripeCustomer["id"],
                preferred_payment_method="zelle",
            )
            self.db.add(StripeCustomer_record)
            await self.db.commit()

        logger.info(f"StripeCustomer created: {StripeCustomer['id']}")

    async def _handle_dispute_created(self, dispute: dict[str, Any]) -> None:
        """Handle dispute creation."""
        # Get payment record by charge ID
        # Note: This requires storing charge_id in payment records
        # For now, we'll create a dispute record
        dispute_record = Dispute(
            stripe_dispute_id=dispute["id"],
            amount=Decimal(str(dispute["amount"] / 100)),
            currency=dispute["currency"],
            status=dispute["status"],
            reason=dispute["reason"],
            evidence_due_by=datetime.fromtimestamp(dispute["evidence_details"]["due_by"]),
        )

        self.db.add(dispute_record)
        await self.db.commit()

        logger.warning(f"Dispute created: {dispute['id']}, " f"amount: ${dispute['amount']/100}")

    async def _handle_subscription_event(
        self, subscription: dict[str, Any], event_type: str
    ) -> None:
        """Handle subscription events."""
        logger.info(f"Subscription event: {event_type}, " f"subscription: {subscription['id']}")
        # Implement subscription handling if needed

    async def _create_payment_record(self, payment_intent: dict[str, Any], source: str) -> None:
        """Create payment record from payment intent."""
        metadata = payment_intent.get("metadata", {})

        # Check if payment record already exists
        result = await self.db.execute(
            select(StripePayment).where(
                StripePayment.stripe_payment_intent_id == payment_intent["id"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.status = payment_intent["status"]
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Create new payment record
            payment = StripePayment(
                user_id=metadata.get("user_id"),
                booking_id=metadata.get("booking_id"),
                stripe_payment_intent_id=payment_intent["id"],
                stripe_StripeCustomer_id=payment_intent.get("StripeCustomer"),
                amount=Decimal(str(payment_intent["amount"] / 100)),
                currency=payment_intent["currency"],
                status=payment_intent["status"],
                method="stripe",
                payment_type=metadata.get("payment_type", "payment"),
                description=payment_intent.get("description"),
                metadata_json=json.dumps(metadata),
                stripe_fee=Decimal("0"),  # Calculate from charges if needed
                net_amount=Decimal(str(payment_intent["amount"] / 100)),
            )
            self.db.add(payment)

        await self.db.commit()

    async def _update_payment_status(self, payment_intent_id: str, status: str) -> None:
        """Update payment status."""
        result = await self.db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = status
            payment.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def _update_StripeCustomer_analytics(self, payment_intent: dict[str, Any]) -> None:
        """Update StripeCustomer analytics after successful payment."""
        StripeCustomer_id = payment_intent.get("StripeCustomer")
        if not StripeCustomer_id:
            return

        result = await self.db.execute(
            select(StripeCustomer).where(Customer.stripe_StripeCustomer_id == StripeCustomer_id)
        )
        customer_record = result.scalar_one_or_none()

        if customer_record:
            amount = Decimal(str(payment_intent["amount"] / 100))
            customer_record.total_spent += amount
            customer_record.total_bookings += 1

            # Calculate Zelle savings (3% of Stripe payments - Stripe charges ~2.9% + $0.30)
            if payment_intent.get("payment_method_types", ["card"])[0] == "card":
                customer_record.zelle_savings += amount * Decimal("0.03")

            # Update loyalty tier
            if customer_record.total_spent >= 5000:
                customer_record.loyalty_tier = "platinum"
            elif customer_record.total_spent >= 2000:
                customer_record.loyalty_tier = "gold"
            elif customer_record.total_spent >= 500:
                customer_record.loyalty_tier = "silver"

            customer_record.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def get_payment_analytics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        station_id: str | None = None,
    ) -> PaymentAnalytics:
        """
        Get payment analytics using Stripe's native Reporting API.

        ⚡ STRIPE NATIVE IMPLEMENTATION:
        Instead of custom queries, we leverage:
        - Stripe Balance Transactions API (for revenue)
        - Stripe Charges API (for transaction counts)
        - Stripe Dashboard (for advanced analytics)

        📊 FOR ADVANCED ANALYTICS, USE STRIPE DASHBOARD:
        https://dashboard.stripe.com/analytics

        This provides:
        - Real-time metrics
        - Revenue forecasting
        - Customer cohort analysis
        - Retention tracking
        - And much more...

        Args:
            start_date: Start of date range (default: 30 days ago)
            end_date: End of date range (default: now)
            station_id: Optional station filter (applied via metadata)

        Returns:
            PaymentAnalytics with basic metrics from Stripe API
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        try:
            # Use Stripe's Balance Transactions API for accurate financial data
            # This includes all successful charges, refunds, fees, etc.
            balance_txns = stripe.BalanceTransaction.list(
                created={
                    "gte": int(start_date.timestamp()),
                    "lte": int(end_date.timestamp()),
                },
                limit=100,  # Adjust based on expected volume
            )

            # Calculate metrics from Stripe data
            total_amount = Decimal(0)
            total_count = 0
            payment_methods = {}

            for txn in balance_txns.auto_paging_iter():
                if txn.type == "charge":
                    total_amount += Decimal(txn.amount) / 100
                    total_count += 1

                    # Get payment method from charge
                    if hasattr(txn, "source") and txn.source:
                        method = txn.source.get("brand", "unknown")
                        payment_methods[method] = payment_methods.get(method, 0) + 1

            avg_payment = total_amount / total_count if total_count > 0 else Decimal(0)

            return PaymentAnalytics(
                total_payments=total_count,
                total_amount=total_amount,
                avg_payment=avg_payment,
                payment_methods=payment_methods,
                monthly_revenue=[],  # For detailed trends, direct users to Stripe Dashboard
                stripe_dashboard_url=f"https://dashboard.stripe.com/analytics?start={int(start_date.timestamp())}&end={int(end_date.timestamp())}",
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error in analytics: {e}")
            # Fallback to database query if Stripe API fails
            return await self._fallback_analytics(start_date, end_date, station_id)

    async def _fallback_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        station_id: str | None = None,
    ) -> PaymentAnalytics:
        """Fallback analytics using local database (if Stripe API unavailable)."""

        query = select(Payment).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date,
        )

        if station_id:
            query = query.filter(Payment.station_id == station_id)

        result = await self.db.execute(query)
        payments = result.scalars().all()

        successful = [p for p in payments if p.status == "succeeded"]
        total_amount = Decimal(sum(p.amount_cents for p in successful if p.amount_cents)) / 100

        return PaymentAnalytics(
            total_payments=len(successful),
            total_amount=total_amount,
            avg_payment=(total_amount / len(successful) if successful else Decimal(0)),
            payment_methods={},
            monthly_revenue=[],
        )
