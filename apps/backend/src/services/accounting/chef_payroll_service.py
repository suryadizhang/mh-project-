"""
Chef Payroll Service
====================
Tracks payments to chefs (Cash/Zelle) for payroll and 1099 reporting.

This is the CUSTOM payroll solution since:
- Chefs are paid cash or Zelle (not direct deposit)
- We need 1099-NEC tracking for $600+ annual payments
- Akaunting's payroll plugin doesn't support cash payments

Batch 7E: Chef Payroll System
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


class ChefPayrollService:
    """
    Service for tracking chef payments (Cash/Zelle).

    Features:
    - Record cash and Zelle payments to chefs
    - Track year-to-date totals for 1099 reporting
    - Sync to Akaunting as vendor bills/payments
    - Generate 1099 eligibility reports
    """

    def __init__(
        self,
        db: AsyncSession,
        client: Optional[AkauntingClient] = None,
    ):
        """Initialize the chef payroll service."""
        self.db = db
        self.client = client or get_akaunting_client()

    # =========================================================================
    # Payment Recording
    # =========================================================================

    async def record_chef_payment(
        self,
        chef_id: UUID,
        amount: Decimal,
        payment_method: str,
        booking_id: Optional[UUID] = None,
        payment_date: Optional[date] = None,
        zelle_confirmation: Optional[str] = None,
        cash_receipt_signed: bool = False,
        notes: Optional[str] = None,
        paid_by: Optional[UUID] = None,
    ) -> dict:
        """
        Record a payment to a chef.

        Args:
            chef_id: Chef to pay
            amount: Payment amount
            payment_method: 'cash' or 'zelle'
            booking_id: Optional booking this payment is for
            payment_date: Payment date (defaults to today)
            zelle_confirmation: Zelle transaction confirmation number
            cash_receipt_signed: Whether chef signed cash receipt
            notes: Optional notes
            paid_by: User ID who made the payment

        Returns:
            Payment record dict
        """
        try:
            if payment_date is None:
                payment_date = date.today()

            # 1. Get chef vendor mapping
            vendor_mapping = await self._get_vendor_mapping(chef_id)
            if not vendor_mapping:
                raise ValueError(f"Chef {chef_id} not set up as vendor. Run vendor sync first.")

            # 2. Calculate YTD before this payment
            year = payment_date.year
            ytd_before = await self._get_chef_ytd(chef_id, year)
            ytd_after = ytd_before + amount

            # 3. Check 1099 threshold crossing
            threshold_crossed = ytd_before < 600 and ytd_after >= 600
            if threshold_crossed:
                logger.info(
                    f"Chef {chef_id} crossed $600 threshold for {year}. "
                    f"YTD: ${ytd_after}. 1099 required."
                )

            # 4. Save payment record
            payment_record = await self._save_chef_payment(
                chef_vendor_mapping_id=vendor_mapping["id"],
                booking_id=booking_id,
                akaunting_company_id=vendor_mapping["akaunting_company_id"],
                payment_date=payment_date,
                amount=amount,
                payment_method=payment_method,
                zelle_confirmation=zelle_confirmation,
                cash_receipt_signed=cash_receipt_signed,
                year_to_date_total=ytd_after,
                notes=notes,
                paid_by=paid_by,
            )

            # 5. Sync to Akaunting (as vendor bill payment)
            await self._sync_payment_to_akaunting(payment_record, vendor_mapping)

            logger.info(
                f"Recorded {payment_method} payment ${amount} to chef {chef_id}. "
                f"YTD: ${ytd_after}"
            )

            return {
                "id": payment_record["id"],
                "chef_id": chef_id,
                "amount": amount,
                "payment_method": payment_method,
                "payment_date": payment_date,
                "year_to_date": ytd_after,
                "requires_1099": ytd_after >= 600,
                "threshold_crossed": threshold_crossed,
            }

        except Exception as e:
            logger.exception(f"Failed to record chef payment: {e}")
            raise

    async def record_batch_payments(
        self,
        payments: list[dict],
        paid_by: Optional[UUID] = None,
    ) -> dict:
        """
        Record multiple chef payments at once (e.g., end of day payout).

        Args:
            payments: List of payment dicts with chef_id, amount, payment_method, etc.
            paid_by: User making the payments

        Returns:
            Summary dict
        """
        results = {"success": 0, "failed": 0, "errors": []}

        for payment in payments:
            try:
                await self.record_chef_payment(
                    chef_id=payment["chef_id"],
                    amount=Decimal(str(payment["amount"])),
                    payment_method=payment["payment_method"],
                    booking_id=payment.get("booking_id"),
                    zelle_confirmation=payment.get("zelle_confirmation"),
                    cash_receipt_signed=payment.get("cash_receipt_signed", False),
                    notes=payment.get("notes"),
                    paid_by=paid_by,
                )
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "chef_id": str(payment["chef_id"]),
                        "error": str(e),
                    }
                )

        logger.info(
            f"Batch payment complete: {results['success']} success, " f"{results['failed']} failed"
        )
        return results

    # =========================================================================
    # YTD and 1099 Reporting
    # =========================================================================

    async def get_chef_ytd_summary(
        self,
        chef_id: UUID,
        year: Optional[int] = None,
    ) -> dict:
        """
        Get year-to-date payment summary for a chef.

        Args:
            chef_id: Chef ID
            year: Tax year (defaults to current year)

        Returns:
            Summary dict with YTD total, payment count, 1099 status
        """
        if year is None:
            year = date.today().year

        ytd = await self._get_chef_ytd(chef_id, year)
        payment_count = await self._get_chef_payment_count(chef_id, year)
        has_tax_id = await self._chef_has_tax_id(chef_id)

        return {
            "chef_id": chef_id,
            "year": year,
            "year_to_date": ytd,
            "payment_count": payment_count,
            "requires_1099": ytd >= 600,
            "has_tax_id_on_file": has_tax_id,
            "action_needed": ytd >= 600 and not has_tax_id,
        }

    async def get_1099_report(
        self,
        year: Optional[int] = None,
        threshold: Decimal = Decimal("600"),
    ) -> list[dict]:
        """
        Generate 1099-NEC eligibility report for all chefs.

        Args:
            year: Tax year (defaults to current year)
            threshold: 1099 threshold (IRS requires $600+)

        Returns:
            List of chefs needing 1099 with details
        """
        if year is None:
            year = date.today().year

        # Query the chef_1099_summary view
        # TODO: Implement actual query
        logger.warning("get_1099_report not fully implemented")
        return []

    async def get_payment_history(
        self,
        chef_id: UUID,
        year: Optional[int] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get payment history for a chef.

        Args:
            chef_id: Chef ID
            year: Filter by year (optional)
            limit: Max records to return

        Returns:
            List of payment records
        """
        # TODO: Query accounting.chef_payment_mappings
        logger.warning("get_payment_history not fully implemented")
        return []

    # =========================================================================
    # Cash Receipt Management
    # =========================================================================

    async def mark_cash_receipt_signed(
        self,
        payment_id: UUID,
    ) -> bool:
        """
        Mark a cash payment as having a signed receipt.

        This is important for audit purposes.
        """
        try:
            # TODO: Update accounting.chef_payment_mappings
            logger.warning("mark_cash_receipt_signed not fully implemented")
            return True
        except Exception as e:
            logger.exception(f"Failed to mark receipt signed: {e}")
            return False

    async def get_unsigned_cash_payments(
        self,
        days_back: int = 30,
    ) -> list[dict]:
        """
        Get cash payments missing signed receipts.

        Used for follow-up to ensure proper documentation.
        """
        # TODO: Query payments where payment_method='cash' AND cash_receipt_signed=false
        logger.warning("get_unsigned_cash_payments not fully implemented")
        return []

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_vendor_mapping(self, chef_id: UUID) -> Optional[dict]:
        """Get chef vendor mapping."""
        # TODO: Query accounting.chef_vendor_mappings
        logger.warning("_get_vendor_mapping not fully implemented")
        return None

    async def _get_chef_ytd(self, chef_id: UUID, year: int) -> Decimal:
        """Get chef's year-to-date payments."""
        # TODO: Use accounting.calculate_chef_ytd function
        logger.warning("_get_chef_ytd not fully implemented")
        return Decimal("0")

    async def _get_chef_payment_count(self, chef_id: UUID, year: int) -> int:
        """Get count of payments to chef in a year."""
        # TODO: Query accounting.chef_payment_mappings
        return 0

    async def _chef_has_tax_id(self, chef_id: UUID) -> bool:
        """Check if chef has tax ID on file."""
        # TODO: Query accounting.chef_vendor_mappings
        return False

    async def _save_chef_payment(
        self,
        chef_vendor_mapping_id: UUID,
        booking_id: Optional[UUID],
        akaunting_company_id: int,
        payment_date: date,
        amount: Decimal,
        payment_method: str,
        zelle_confirmation: Optional[str],
        cash_receipt_signed: bool,
        year_to_date_total: Decimal,
        notes: Optional[str],
        paid_by: Optional[UUID],
    ) -> dict:
        """Save chef payment record."""
        # TODO: Insert into accounting.chef_payment_mappings
        logger.warning("_save_chef_payment not fully implemented")
        return {"id": None}

    async def _sync_payment_to_akaunting(
        self,
        payment_record: dict,
        vendor_mapping: dict,
    ) -> None:
        """Sync chef payment to Akaunting as vendor bill/payment."""
        try:
            # Option 1: Create a bill and immediately pay it
            # Option 2: Just create an expense transaction
            # Using Option 2 for simplicity with cash payments

            company_id = vendor_mapping["akaunting_company_id"]
            vendor_id = vendor_mapping["akaunting_vendor_id"]

            # Get cash/bank account
            accounts = await self.client.list_accounts(company_id)
            cash_account = next(
                (a for a in accounts if "cash" in a.get("name", "").lower()),
                accounts[0] if accounts else None,
            )

            if not cash_account:
                logger.warning("No cash account found in Akaunting")
                return

            # Create expense transaction
            await self.client.create_transaction(
                company_id=company_id,
                account_id=cash_account["id"],
                amount=payment_record.get("amount", Decimal("0")),
                paid_at=payment_record.get("payment_date", date.today()),
                transaction_type="expense",
                contact_id=vendor_id,
                description=f"Chef payment - {payment_record.get('payment_method', 'cash')}",
                reference=payment_record.get("zelle_confirmation"),
            )

            # Update sync status
            # TODO: Update accounting.chef_payment_mappings SET sync_status='synced'

        except Exception as e:
            logger.exception(f"Failed to sync chef payment to Akaunting: {e}")
            # TODO: Update sync_status='failed'
