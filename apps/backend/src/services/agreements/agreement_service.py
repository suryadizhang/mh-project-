"""
Agreement Service
=================

Core CRUD operations for legal agreements:
- Fetch active agreement templates
- Create signed agreements (immutable)
- Query agreement status by booking/customer
- Allergen disclosure management

IMPORTANT: signed_agreements are IMMUTABLE after creation.
All agreement text is frozen at signing time with values baked in.

Usage:
    service = AgreementService(db)

    # Get current template
    template = await service.get_active_template('liability_waiver')

    # Create signed agreement
    signed = await service.create_signed_agreement(
        booking_id=booking_id,
        customer_id=customer_id,
        agreement_type='liability_waiver',
        rendered_text=rendered_markdown,
        signature_image=signature_bytes,
        signer_info=signer_data
    )

    # Check if booking has signed agreement
    is_signed = await service.has_signed_agreement(booking_id, 'liability_waiver')

See: database/migrations/008_legal_agreements_system.sql
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from services.business_config_service import get_business_config

logger = logging.getLogger(__name__)


class AgreementService:
    """
    Service for managing legal agreements.

    Handles:
    - Agreement template retrieval with dynamic value injection
    - Signed agreement creation (immutable records)
    - Agreement status queries
    - Allergen disclosure management
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize agreement service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_active_template(self, agreement_type: str) -> dict[str, Any] | None:
        """
        Get the current active template for an agreement type.

        Args:
            agreement_type: Type of agreement ('liability_waiver', 'allergen_disclosure')

        Returns:
            Template dict with id, version, title, content_markdown, variable_refs
            None if no active template found
        """
        result = await self.db.execute(
            select("*")
            .select_from(self.db.bind.dialect.identifier_preparer.quote("core.agreement_templates"))
            .where(
                and_(
                    # Using text for raw SQL since we might not have the model yet
                )
            )
        )

        # Use raw SQL for now until SQLAlchemy models are created
        from sqlalchemy import text

        result = await self.db.execute(
            text(
                """
                SELECT id, agreement_type, version, title, content_markdown,
                       effective_date, variable_refs
                FROM core.agreement_templates
                WHERE agreement_type = :agreement_type
                AND is_active = true
                ORDER BY effective_date DESC
                LIMIT 1
            """
            ),
            {"agreement_type": agreement_type},
        )
        row = result.fetchone()

        if not row:
            logger.warning(f"No active template found for agreement_type: {agreement_type}")
            return None

        return {
            "id": row.id,
            "agreement_type": row.agreement_type,
            "version": row.version,
            "title": row.title,
            "content_markdown": row.content_markdown,
            "effective_date": row.effective_date,
            "variable_refs": row.variable_refs or [],
        }

    async def render_template(
        self, template: dict[str, Any], additional_vars: dict[str, str] | None = None
    ) -> str:
        """
        Render a template with current business config values.

        Replaces {{PLACEHOLDER}} syntax with actual values.

        Args:
            template: Template dict from get_active_template()
            additional_vars: Extra variables (e.g., customer-specific data)

        Returns:
            Rendered markdown text with all placeholders replaced
        """
        # Get current business config for dynamic values
        config = await get_business_config(self.db)

        # Build variable map
        variables = {
            # Pricing (convert cents to dollars)
            "ADULT_PRICE": str(config.adult_price_cents // 100),
            "CHILD_PRICE": str(config.child_price_cents // 100),
            "CHILD_FREE_AGE": str(config.child_free_under_age),
            "PARTY_MINIMUM": str(config.party_minimum_cents // 100),
            "DEPOSIT_AMOUNT": str(config.deposit_amount_cents // 100),
            # Dates
            "EFFECTIVE_DATE": datetime.now().strftime("%B %d, %Y"),
            "SIGNATURE_DATE": datetime.now().strftime("%B %d, %Y"),
            # Travel
            "FREE_TRAVEL_MILES": str(config.travel_free_miles),
            "COST_PER_MILE": str(config.travel_per_mile_cents // 100),
        }

        # Add any additional variables
        if additional_vars:
            variables.update(additional_vars)

        # Replace placeholders
        content = template["content_markdown"]
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", var_value)

        return content

    async def create_signed_agreement(
        self,
        booking_id: UUID | None,
        customer_id: UUID,
        agreement_type: str,
        agreement_version: str,
        rendered_text: str,
        signature_image: bytes | None,
        signature_typed_name: str | None,
        signer_info: dict[str, Any],
        signing_method: str = "online",
    ) -> dict[str, Any]:
        """
        Create an immutable signed agreement record.

        IMPORTANT: Once created, signed agreements CANNOT be modified.

        Args:
            booking_id: Associated booking (can be None for pre-booking)
            customer_id: Customer who signed
            agreement_type: Type of agreement
            agreement_version: Version of template used
            rendered_text: Full text with all values baked in
            signature_image: PNG bytes of signature canvas
            signature_typed_name: Typed name if not drawn
            signer_info: Dict with name, email, ip_address, user_agent, device_fingerprint
            signing_method: How it was signed ('online', 'sms_link', 'phone', 'ai_chat')

        Returns:
            Dict with id, signed_at, and confirmation details

        Raises:
            ValueError: If neither signature_image nor signature_typed_name provided
        """
        if not signature_image and not signature_typed_name:
            raise ValueError("Either signature_image or signature_typed_name is required")

        from sqlalchemy import text

        # Insert signed agreement (immutable)
        result = await self.db.execute(
            text(
                """
                INSERT INTO core.signed_agreements (
                    booking_id, customer_id, agreement_type, agreement_version,
                    agreement_text, signature_image, signature_typed_name,
                    signer_name, signer_email, signer_ip_address, signer_user_agent,
                    signer_device_fingerprint, signing_method
                ) VALUES (
                    :booking_id, :customer_id, :agreement_type, :agreement_version,
                    :agreement_text, :signature_image, :signature_typed_name,
                    :signer_name, :signer_email, :signer_ip_address, :signer_user_agent,
                    :signer_device_fingerprint, :signing_method
                )
                RETURNING id, signed_at, retention_expires_at
            """
            ),
            {
                "booking_id": str(booking_id) if booking_id else None,
                "customer_id": str(customer_id),
                "agreement_type": agreement_type,
                "agreement_version": agreement_version,
                "agreement_text": rendered_text,
                "signature_image": signature_image,
                "signature_typed_name": signature_typed_name,
                "signer_name": signer_info.get("name"),
                "signer_email": signer_info.get("email"),
                "signer_ip_address": signer_info.get("ip_address"),
                "signer_user_agent": signer_info.get("user_agent"),
                "signer_device_fingerprint": signer_info.get("device_fingerprint"),
                "signing_method": signing_method,
            },
        )

        row = result.fetchone()
        await self.db.commit()

        logger.info(
            f"Created signed agreement: type={agreement_type}, "
            f"booking={booking_id}, customer={customer_id}"
        )

        return {
            "id": row.id,
            "signed_at": row.signed_at,
            "retention_expires_at": row.retention_expires_at,
            "agreement_type": agreement_type,
        }

    async def has_signed_agreement(self, booking_id: UUID, agreement_type: str) -> bool:
        """
        Check if a booking has a signed agreement of given type.

        Args:
            booking_id: Booking to check
            agreement_type: Type of agreement to look for

        Returns:
            True if signed agreement exists
        """
        from sqlalchemy import text

        result = await self.db.execute(
            text(
                """
                SELECT 1 FROM core.signed_agreements
                WHERE booking_id = :booking_id
                AND agreement_type = :agreement_type
                LIMIT 1
            """
            ),
            {"booking_id": str(booking_id), "agreement_type": agreement_type},
        )

        return result.fetchone() is not None

    async def get_signed_agreement(self, agreement_id: UUID) -> dict[str, Any] | None:
        """
        Get a signed agreement by ID.

        Args:
            agreement_id: Agreement ID

        Returns:
            Agreement dict or None
        """
        from sqlalchemy import text

        result = await self.db.execute(
            text(
                """
                SELECT id, booking_id, customer_id, agreement_type, agreement_version,
                       agreement_text, signed_at, signer_name, signer_email,
                       signing_method, confirmation_pdf_url, retention_expires_at
                FROM core.signed_agreements
                WHERE id = :agreement_id
            """
            ),
            {"agreement_id": str(agreement_id)},
        )

        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row.id,
            "booking_id": row.booking_id,
            "customer_id": row.customer_id,
            "agreement_type": row.agreement_type,
            "agreement_version": row.agreement_version,
            "agreement_text": row.agreement_text,
            "signed_at": row.signed_at,
            "signer_name": row.signer_name,
            "signer_email": row.signer_email,
            "signing_method": row.signing_method,
            "confirmation_pdf_url": row.confirmation_pdf_url,
            "retention_expires_at": row.retention_expires_at,
        }

    async def get_agreements_for_booking(self, booking_id: UUID) -> list[dict[str, Any]]:
        """
        Get all signed agreements for a booking.

        Args:
            booking_id: Booking ID

        Returns:
            List of agreement dicts
        """
        from sqlalchemy import text

        result = await self.db.execute(
            text(
                """
                SELECT id, agreement_type, agreement_version, signed_at,
                       signer_name, signing_method, confirmation_pdf_url
                FROM core.signed_agreements
                WHERE booking_id = :booking_id
                ORDER BY signed_at DESC
            """
            ),
            {"booking_id": str(booking_id)},
        )

        return [
            {
                "id": row.id,
                "agreement_type": row.agreement_type,
                "agreement_version": row.agreement_version,
                "signed_at": row.signed_at,
                "signer_name": row.signer_name,
                "signing_method": row.signing_method,
                "confirmation_pdf_url": row.confirmation_pdf_url,
            }
            for row in result.fetchall()
        ]

    async def update_pdf_url(self, agreement_id: UUID, pdf_url: str) -> None:
        """
        Update the PDF URL for a signed agreement.

        NOTE: This is the ONLY allowed update to signed_agreements table.
        It adds the PDF URL after generation, not modifying the agreement itself.

        Args:
            agreement_id: Agreement ID
            pdf_url: R2/S3 URL to the generated PDF
        """

        # We need a special bypass for this one field
        # The trigger blocks updates, so we'll use a different approach:
        # Store the PDF URL in a separate table or disable trigger temporarily

        # For now, let's use a separate approach - store in a related table
        # or update the signed agreement before the immutability trigger
        logger.info(f"PDF URL for agreement {agreement_id}: {pdf_url}")

        # TODO: Consider storing PDF URLs in a separate table
        # to maintain true immutability of signed_agreements


# Convenience function for dependency injection
def get_agreement_service(db: AsyncSession) -> AgreementService:
    """FastAPI dependency injection helper."""
    return AgreementService(db)
