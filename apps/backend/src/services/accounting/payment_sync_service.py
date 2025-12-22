"""
Payment Sync Service
====================
Syncs Stripe payments to Akaunting transactions.

Triggered by:
- Stripe webhook: payment_intent.succeeded
- Manual payment recording

Batch 7D: Payment Sync Integration
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.accounting.akaunting_client import (
    AkauntingClient,
    get_akaunting_client,
)

logger = logging.getLogger(__name__)


class PaymentSyncService:
    """
    Service for synchronizing payments to Akaunting.

    Handles:
    - Stripe payments (deposits, final payments)
    - Cash payments
    - Zelle payments
    - Refunds
    """

    def __init__(
        self,
        db: AsyncSession,
        client: Optional[AkauntingClient] = None,
    ):
        """Initialize the payment sync service."""
        self.db = db
        self.client = client or get_akaunting_client()

    async def sync_stripe_payment(
        self,
        payment_id: UUID,
        stripe_payment_intent_id: str,
        amount: Decimal,
        booking_id: Optional[UUID] = None,
    ) -> bool:
        """
        Sync a Stripe payment to Akaunting.

        Args:
            payment_id: MyHibachi payment ID
            stripe_payment_intent_id: Stripe payment intent ID
            amount: Payment amount
            booking_id: Optional associated booking ID

        Returns:
            True if synced successfully
        """
        try:
            # 1. Get company from booking or default
            company_id = await self._get_company_for_payment(booking_id)

            # 2. Get Stripe account in Akaunting
            account_id = await self._get_stripe_account_id(company_id)

            # 3. Get category (Income → Catering Services)
            category_id = await self._get_income_category_id(company_id)

            # 4. Get customer contact if booking exists
            contact_id = None
            if booking_id:
                contact_id = await self._get_contact_for_booking(booking_id)

            # 5. Create transaction in Akaunting
            transaction = await self.client.create_transaction(
                company_id=company_id,
                account_id=account_id,
                amount=amount,
                paid_at=date.today(),
                transaction_type="income",
                contact_id=contact_id,
                category_id=category_id,
                description="Stripe payment for booking",
                reference=stripe_payment_intent_id,
            )

            # 6. Save mapping
            await self._save_payment_mapping(
                payment_id=payment_id,
                akaunting_company_id=company_id,
                akaunting_transaction_id=transaction.id,
                akaunting_account_id=account_id,
            )

            # 7. If booking has invoice, record payment against it
            if booking_id:
                await self._apply_payment_to_invoice(booking_id, amount, account_id)

            logger.info(
                f"Synced Stripe payment {payment_id} to Akaunting transaction {transaction.id}"
            )
            return True

        except Exception as e:
            logger.exception(f"Failed to sync Stripe payment {payment_id}: {e}")
            return False

    async def sync_manual_payment(
        self,
        payment_id: UUID,
        amount: Decimal,
        payment_method: str,  # 'cash', 'zelle', 'check'
        booking_id: Optional[UUID] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Sync a manual payment (cash/Zelle/check) to Akaunting.
        """
        try:
            company_id = await self._get_company_for_payment(booking_id)
            account_id = await self._get_account_for_method(company_id, payment_method)
            category_id = await self._get_income_category_id(company_id)

            contact_id = None
            if booking_id:
                contact_id = await self._get_contact_for_booking(booking_id)

            description = f"{payment_method.title()} payment"
            if notes:
                description += f" - {notes}"

            transaction = await self.client.create_transaction(
                company_id=company_id,
                account_id=account_id,
                amount=amount,
                paid_at=date.today(),
                transaction_type="income",
                contact_id=contact_id,
                category_id=category_id,
                description=description,
                reference=reference,
            )

            await self._save_payment_mapping(
                payment_id=payment_id,
                akaunting_company_id=company_id,
                akaunting_transaction_id=transaction.id,
                akaunting_account_id=account_id,
            )

            if booking_id:
                await self._apply_payment_to_invoice(booking_id, amount, account_id)

            logger.info(f"Synced {payment_method} payment {payment_id} to Akaunting")
            return True

        except Exception as e:
            logger.exception(f"Failed to sync manual payment {payment_id}: {e}")
            return False

    async def sync_refund(
        self,
        original_payment_id: UUID,
        refund_amount: Decimal,
        stripe_refund_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Sync a refund to Akaunting.

        Creates a negative income transaction linked to the original payment.
        """
        try:
            # Get original payment mapping
            original_mapping = await self._get_payment_mapping(original_payment_id)
            if not original_mapping:
                logger.warning(f"No mapping for original payment {original_payment_id}")
                return False

            description = "Refund"
            if reason:
                description += f": {reason}"
            if stripe_refund_id:
                description += f" (Stripe: {stripe_refund_id})"

            # Create negative transaction (expense or negative income)
            # Akaunting handles refunds as expenses against the same account
            transaction = await self.client.create_transaction(
                company_id=original_mapping["akaunting_company_id"],
                account_id=original_mapping["akaunting_account_id"],
                amount=refund_amount,
                paid_at=date.today(),
                transaction_type="expense",  # Refunds are expenses
                description=description,
                reference=stripe_refund_id or f"Refund for {original_payment_id}",
            )

            logger.info(f"Synced refund for payment {original_payment_id}: ${refund_amount}")
            return True

        except Exception as e:
            logger.exception(f"Failed to sync refund: {e}")
            return False

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_company_for_payment(
        self,
        booking_id: Optional[UUID],
    ) -> int:
        """Get Akaunting company ID for a payment."""
        if booking_id:
            # Get station from booking, then get company mapping
            # TODO: Implement
            pass
        # Return default company
        # TODO: Get from config or first company
        return 1

    async def _get_stripe_account_id(self, company_id: int) -> int:
        """Get the Stripe bank account ID in Akaunting."""
        accounts = await self.client.list_accounts(company_id)
        for account in accounts:
            if "stripe" in account.get("name", "").lower():
                return account["id"]
        # Return first account as fallback
        return accounts[0]["id"] if accounts else 1

    async def _get_account_for_method(
        self,
        company_id: int,
        payment_method: str,
    ) -> int:
        """Get the appropriate account ID for a payment method."""
        accounts = await self.client.list_accounts(company_id)

        method_keywords = {
            "cash": ["cash", "petty"],
            "zelle": ["zelle", "bank", "checking"],
            "check": ["bank", "checking"],
        }

        keywords = method_keywords.get(payment_method.lower(), [])
        for account in accounts:
            name = account.get("name", "").lower()
            if any(kw in name for kw in keywords):
                return account["id"]

        # Fallback to first account
        return accounts[0]["id"] if accounts else 1

    async def _get_income_category_id(self, company_id: int) -> Optional[int]:
        """Get the income category for catering services."""
        categories = await self.client.list_categories(company_id, "income")
        for cat in categories:
            name = cat.get("name", "").lower()
            if any(kw in name for kw in ["catering", "service", "sales"]):
                return cat["id"]
        return categories[0]["id"] if categories else None

    async def _get_contact_for_booking(self, booking_id: UUID) -> Optional[int]:
        """Get Akaunting contact ID for a booking's customer."""
        # TODO: Query accounting.customer_mappings via invoice mapping
        return None

    async def _save_payment_mapping(
        self,
        payment_id: UUID,
        akaunting_company_id: int,
        akaunting_transaction_id: int,
        akaunting_account_id: int,
    ) -> None:
        """Save payment mapping to database."""
        # TODO: Insert into accounting.payment_mappings
        logger.warning("_save_payment_mapping not fully implemented")

    async def _get_payment_mapping(self, payment_id: UUID) -> Optional[dict]:
        """Get payment mapping by payment ID."""
        # TODO: Query accounting.payment_mappings
        return None

    async def _apply_payment_to_invoice(
        self,
        booking_id: UUID,
        amount: Decimal,
        account_id: int,
    ) -> None:
        """Apply payment to the booking's invoice in Akaunting."""
        # TODO: Get invoice mapping, call record_invoice_payment
        # This keeps the invoice status in sync
        logger.warning("_apply_payment_to_invoice not fully implemented")
