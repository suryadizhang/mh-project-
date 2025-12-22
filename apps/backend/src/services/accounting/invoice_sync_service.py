"""
Invoice Sync Service
====================
Syncs MyHibachi bookings to Akaunting invoices.

Workflow:
1. Booking created → Create draft invoice
2. Deposit paid → Update invoice with partial payment
3. Event completed → Finalize and send invoice
4. Full payment → Mark invoice as paid

Batch 7C: Booking → Invoice Automation
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.booking import Booking
from services.accounting.akaunting_client import (
    AkauntingClient,
    AkauntingInvoice,
    get_akaunting_client,
)

logger = logging.getLogger(__name__)


class InvoiceSyncService:
    """
    Service for synchronizing bookings to Akaunting invoices.

    Usage:
        service = InvoiceSyncService(db_session)
        invoice = await service.create_invoice_for_booking(booking_id)
        await service.record_deposit_payment(booking_id, amount)
    """

    def __init__(
        self,
        db: AsyncSession,
        client: Optional[AkauntingClient] = None,
    ):
        """Initialize the invoice sync service."""
        self.db = db
        self.client = client or get_akaunting_client()

    # =========================================================================
    # Invoice Creation
    # =========================================================================

    async def create_invoice_for_booking(
        self,
        booking_id: UUID,
        auto_send: bool = False,
    ) -> Optional[AkauntingInvoice]:
        """
        Create an Akaunting invoice for a booking.

        Args:
            booking_id: MyHibachi booking ID
            auto_send: Whether to automatically send the invoice email

        Returns:
            Created AkauntingInvoice or None if failed
        """
        try:
            # 1. Get booking with related data
            booking = await self._get_booking(booking_id)
            if not booking:
                logger.error(f"Booking {booking_id} not found")
                return None

            # 2. Get or create customer contact in Akaunting
            akaunting_contact_id = await self._ensure_customer_contact(booking)
            if not akaunting_contact_id:
                logger.error(f"Failed to get/create contact for booking {booking_id}")
                return None

            # 3. Get company mapping for station
            company_mapping = await self._get_company_mapping(booking.station_id)
            if not company_mapping:
                logger.error(f"No company mapping for station {booking.station_id}")
                return None

            # 4. Build invoice line items
            items = self._build_invoice_items(booking, company_mapping)

            # 5. Calculate dates
            issued_at = date.today()
            due_at = booking.event_date or (issued_at + timedelta(days=14))

            # 6. Create invoice in Akaunting
            invoice = await self.client.create_invoice(
                company_id=company_mapping["akaunting_company_id"],
                contact_id=akaunting_contact_id,
                items=items,
                issued_at=issued_at,
                due_at=due_at,
                notes=self._build_invoice_notes(booking),
            )

            # 7. Save mapping to our database
            await self._save_invoice_mapping(
                booking_id=booking_id,
                akaunting_company_id=company_mapping["akaunting_company_id"],
                akaunting_invoice_id=invoice.id,
                akaunting_invoice_number=invoice.invoice_number,
                invoice_amount=invoice.amount,
            )

            # 8. Optionally send the invoice
            if auto_send:
                await self.client.send_invoice(
                    company_id=company_mapping["akaunting_company_id"],
                    invoice_id=invoice.id,
                )
                await self._update_invoice_mapping_status(booking_id, "sent")

            logger.info(f"Created invoice {invoice.invoice_number} for booking {booking_id}")
            return invoice

        except Exception as e:
            logger.exception(f"Failed to create invoice for booking {booking_id}: {e}")
            await self._log_sync_failure("invoice", booking_id, str(e))
            return None

    # =========================================================================
    # Payment Recording
    # =========================================================================

    async def record_deposit_payment(
        self,
        booking_id: UUID,
        amount: Decimal,
        stripe_payment_id: Optional[str] = None,
    ) -> bool:
        """
        Record a deposit payment against the booking's invoice.

        Args:
            booking_id: MyHibachi booking ID
            amount: Payment amount
            stripe_payment_id: Optional Stripe payment intent ID for reference

        Returns:
            True if successful
        """
        try:
            # Get invoice mapping
            mapping = await self._get_invoice_mapping(booking_id)
            if not mapping:
                logger.warning(f"No invoice mapping for booking {booking_id}")
                return False

            # Get the Stripe account ID in Akaunting
            account_id = await self._get_stripe_account_id(mapping["akaunting_company_id"])

            # Record payment
            await self.client.record_invoice_payment(
                company_id=mapping["akaunting_company_id"],
                invoice_id=mapping["akaunting_invoice_id"],
                account_id=account_id,
                amount=amount,
                paid_at=date.today(),
                description=(
                    f"Deposit - Stripe: {stripe_payment_id}" if stripe_payment_id else "Deposit"
                ),
            )

            # Update our mapping
            await self._update_invoice_mapping_status(booking_id, "partial", amount_paid=amount)

            logger.info(f"Recorded deposit ${amount} for booking {booking_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to record deposit for {booking_id}: {e}")
            return False

    async def record_final_payment(
        self,
        booking_id: UUID,
        amount: Decimal,
        payment_method: str = "stripe",
        reference: Optional[str] = None,
    ) -> bool:
        """
        Record the final payment for a booking.

        Args:
            booking_id: MyHibachi booking ID
            amount: Final payment amount
            payment_method: 'stripe', 'cash', 'zelle', etc.
            reference: External reference (Stripe ID, Zelle confirmation, etc.)

        Returns:
            True if successful
        """
        try:
            mapping = await self._get_invoice_mapping(booking_id)
            if not mapping:
                return False

            account_id = await self._get_payment_account_id(
                mapping["akaunting_company_id"],
                payment_method,
            )

            await self.client.record_invoice_payment(
                company_id=mapping["akaunting_company_id"],
                invoice_id=mapping["akaunting_invoice_id"],
                account_id=account_id,
                amount=amount,
                paid_at=date.today(),
                description=(
                    f"Final payment - {payment_method}: {reference}"
                    if reference
                    else "Final payment"
                ),
            )

            # Check if fully paid
            invoice = await self.client.get_invoice(
                mapping["akaunting_company_id"],
                mapping["akaunting_invoice_id"],
            )

            new_status = "paid" if invoice.amount_due <= 0 else "partial"
            await self._update_invoice_mapping_status(
                booking_id,
                new_status,
                amount_paid=mapping.get("amount_paid", Decimal("0")) + amount,
            )

            logger.info(
                f"Recorded final payment ${amount} for booking {booking_id}, status: {new_status}"
            )
            return True

        except Exception as e:
            logger.exception(f"Failed to record final payment for {booking_id}: {e}")
            return False

    # =========================================================================
    # Invoice Status Management
    # =========================================================================

    async def send_invoice(self, booking_id: UUID) -> bool:
        """Send the invoice email to the customer."""
        try:
            mapping = await self._get_invoice_mapping(booking_id)
            if not mapping:
                return False

            success = await self.client.send_invoice(
                mapping["akaunting_company_id"],
                mapping["akaunting_invoice_id"],
            )

            if success:
                await self._update_invoice_mapping_status(booking_id, "sent")

            return success
        except Exception as e:
            logger.exception(f"Failed to send invoice for {booking_id}: {e}")
            return False

    async def cancel_invoice(self, booking_id: UUID) -> bool:
        """Cancel an invoice (for cancelled bookings)."""
        try:
            mapping = await self._get_invoice_mapping(booking_id)
            if not mapping:
                return False

            await self.client.update_invoice_status(
                mapping["akaunting_company_id"],
                mapping["akaunting_invoice_id"],
                "cancelled",
            )

            await self._update_invoice_mapping_status(booking_id, "cancelled")
            return True

        except Exception as e:
            logger.exception(f"Failed to cancel invoice for {booking_id}: {e}")
            return False

    async def get_invoice_pdf_url(self, booking_id: UUID) -> Optional[str]:
        """Get the PDF download URL for a booking's invoice."""
        mapping = await self._get_invoice_mapping(booking_id)
        if not mapping:
            return None

        return await self.client.get_invoice_pdf_url(
            mapping["akaunting_company_id"],
            mapping["akaunting_invoice_id"],
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_booking(self, booking_id: UUID) -> Optional[Booking]:
        """Get booking by ID."""
        result = await self.db.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def _ensure_customer_contact(self, booking: Booking) -> Optional[int]:
        """
        Get or create the customer as a contact in Akaunting.
        Returns the Akaunting contact ID.
        """
        # TODO: Implement customer mapping lookup and creation
        # This will check accounting.customer_mappings first
        # If not found, create in Akaunting and save mapping
        logger.warning("_ensure_customer_contact not fully implemented")
        return None

    async def _get_company_mapping(self, station_id: UUID) -> Optional[dict]:
        """Get the Akaunting company mapping for a station."""
        # TODO: Query accounting.company_mappings
        logger.warning("_get_company_mapping not fully implemented")
        return None

    def _build_invoice_items(self, booking: Booking, company_mapping: dict) -> list[dict]:
        """Build invoice line items from booking details."""
        items = []

        # Main service (per-person pricing)
        items.append(
            {
                "name": f"Hibachi Catering - {booking.guest_count} guests",
                "quantity": booking.guest_count,
                "price": str(booking.price_per_person or Decimal("0")),
                "tax_id": company_mapping.get("tax_id"),
            }
        )

        # Travel fee if applicable
        if booking.travel_fee and booking.travel_fee > 0:
            items.append(
                {
                    "name": "Travel Fee",
                    "quantity": 1,
                    "price": str(booking.travel_fee),
                    "tax_id": None,  # Travel usually not taxed
                }
            )

        # Add-ons if any
        # TODO: Query booking add-ons and add as line items

        return items

    def _build_invoice_notes(self, booking: Booking) -> str:
        """Build invoice notes from booking details."""
        notes = []

        if booking.event_date:
            notes.append(f"Event Date: {booking.event_date.strftime('%B %d, %Y')}")

        if booking.event_time:
            notes.append(f"Event Time: {booking.event_time}")

        if booking.venue_address:
            notes.append(f"Venue: {booking.venue_address}")

        if booking.special_requests:
            notes.append(f"Special Requests: {booking.special_requests}")

        return "\n".join(notes)

    async def _save_invoice_mapping(
        self,
        booking_id: UUID,
        akaunting_company_id: int,
        akaunting_invoice_id: int,
        akaunting_invoice_number: str,
        invoice_amount: Decimal,
    ) -> None:
        """Save invoice mapping to database."""
        # TODO: Insert into accounting.invoice_mappings
        logger.warning("_save_invoice_mapping not fully implemented")

    async def _get_invoice_mapping(self, booking_id: UUID) -> Optional[dict]:
        """Get invoice mapping by booking ID."""
        # TODO: Query accounting.invoice_mappings
        logger.warning("_get_invoice_mapping not fully implemented")
        return None

    async def _update_invoice_mapping_status(
        self,
        booking_id: UUID,
        status: str,
        amount_paid: Optional[Decimal] = None,
    ) -> None:
        """Update invoice mapping status."""
        # TODO: Update accounting.invoice_mappings
        logger.warning("_update_invoice_mapping_status not fully implemented")

    async def _get_stripe_account_id(self, company_id: int) -> int:
        """Get the Stripe account ID for a company in Akaunting."""
        # TODO: Query Akaunting accounts and find Stripe
        logger.warning("_get_stripe_account_id not fully implemented")
        return 1  # Default placeholder

    async def _get_payment_account_id(
        self,
        company_id: int,
        payment_method: str,
    ) -> int:
        """Get the appropriate account ID for a payment method."""
        # TODO: Map payment methods to Akaunting accounts
        logger.warning("_get_payment_account_id not fully implemented")
        return 1  # Default placeholder

    async def _log_sync_failure(
        self,
        entity_type: str,
        entity_id: UUID,
        error_message: str,
    ) -> None:
        """Log a sync failure to accounting.sync_history."""
        # TODO: Insert into accounting.sync_history
        logger.warning("_log_sync_failure not fully implemented")
