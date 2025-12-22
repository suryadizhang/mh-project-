"""
Vendor Sync Service
===================
Syncs MyHibachi chefs to Akaunting vendors for payroll tracking.

Chefs are tracked as vendors because we pay them (1099 contractors).

Batch 7E: Chef Payroll System
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.accounting.akaunting_client import (
    AkauntingClient,
    AkauntingContact,
    get_akaunting_client,
)

logger = logging.getLogger(__name__)


class VendorSyncService:
    """
    Service for synchronizing chefs to Akaunting vendors.

    This enables:
    - Tracking payments to chefs (bills in Akaunting)
    - 1099 reporting at year end
    - Expense categorization by chef
    """

    def __init__(
        self,
        db: AsyncSession,
        client: Optional[AkauntingClient] = None,
    ):
        """Initialize the vendor sync service."""
        self.db = db
        self.client = client or get_akaunting_client()

    async def sync_chef_as_vendor(
        self,
        chef_id: UUID,
        company_id: Optional[int] = None,
    ) -> Optional[AkauntingContact]:
        """
        Sync a chef to Akaunting as a vendor.

        Args:
            chef_id: MyHibachi chef ID
            company_id: Akaunting company ID (uses parent company if not specified)

        Returns:
            Created/updated AkauntingContact or None
        """
        try:
            # 1. Get chef details
            chef = await self._get_chef(chef_id)
            if not chef:
                logger.error(f"Chef {chef_id} not found")
                return None

            # 2. Check if already mapped
            existing_mapping = await self._get_vendor_mapping(chef_id, company_id)
            if existing_mapping:
                # Update existing vendor
                vendor = await self.client.update_contact(
                    company_id=existing_mapping["akaunting_company_id"],
                    contact_id=existing_mapping["akaunting_vendor_id"],
                    name=chef["full_name"],
                    email=chef.get("email"),
                    phone=chef.get("phone"),
                )
                await self._update_mapping_sync_status(chef_id, company_id, "synced")
                return vendor

            # 3. Get company ID (parent company if not specified)
            if not company_id:
                company_id = await self._get_parent_company_id()

            # 4. Create vendor in Akaunting
            vendor = await self.client.create_contact(
                company_id=company_id,
                name=chef["full_name"],
                email=chef.get("email", f"chef_{chef_id}@myhibachi.internal"),
                contact_type="vendor",
                phone=chef.get("phone"),
                address=chef.get("address"),
            )

            # 5. Save mapping
            await self._save_vendor_mapping(
                chef_id=chef_id,
                akaunting_company_id=company_id,
                akaunting_vendor_id=vendor.id,
            )

            logger.info(f"Synced chef {chef_id} as vendor {vendor.id}")
            return vendor

        except Exception as e:
            logger.exception(f"Failed to sync chef {chef_id} as vendor: {e}")
            return None

    async def sync_all_chefs(self, company_id: Optional[int] = None) -> dict:
        """
        Sync all active chefs to Akaunting as vendors.

        Returns:
            Summary dict with success/failed counts
        """
        # Get all active chefs
        chefs = await self._get_all_active_chefs()

        results = {"synced": 0, "failed": 0, "skipped": 0}

        for chef in chefs:
            try:
                vendor = await self.sync_chef_as_vendor(
                    chef_id=chef["id"],
                    company_id=company_id,
                )
                if vendor:
                    results["synced"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to sync chef {chef['id']}: {e}")
                results["failed"] += 1

        logger.info(
            f"Chef sync complete: {results['synced']} synced, " f"{results['failed']} failed"
        )
        return results

    async def update_chef_tax_info(
        self,
        chef_id: UUID,
        tax_id_encrypted: bytes,
        payment_method: str = "cash",
        zelle_email: Optional[str] = None,
        zelle_phone: Optional[str] = None,
    ) -> bool:
        """
        Update chef's tax and payment information.

        This is sensitive data - tax_id should already be encrypted.

        Args:
            chef_id: Chef ID
            tax_id_encrypted: Encrypted SSN/EIN
            payment_method: 'cash', 'zelle', 'check', 'direct_deposit'
            zelle_email: Email for Zelle payments
            zelle_phone: Phone for Zelle payments
        """
        try:
            # Update in our mapping table
            # TODO: Update accounting.chef_vendor_mappings
            logger.warning("update_chef_tax_info not fully implemented")
            return True
        except Exception as e:
            logger.exception(f"Failed to update tax info for chef {chef_id}: {e}")
            return False

    async def get_vendors_needing_1099(
        self,
        tax_year: int,
        threshold: float = 600.0,
    ) -> list[dict]:
        """
        Get vendors (chefs) who need 1099 forms for a tax year.

        IRS Rule: 1099-NEC required if paid $600+ in a calendar year.

        Args:
            tax_year: The tax year to check
            threshold: Payment threshold (default $600)

        Returns:
            List of chef/vendor info needing 1099
        """
        # TODO: Query accounting.chef_1099_summary view
        logger.warning("get_vendors_needing_1099 not fully implemented")
        return []

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_chef(self, chef_id: UUID) -> Optional[dict]:
        """Get chef by ID."""
        # TODO: Query ops.chefs
        logger.warning("_get_chef not fully implemented")
        return None

    async def _get_all_active_chefs(self) -> list[dict]:
        """Get all active chefs."""
        # TODO: Query ops.chefs WHERE is_active = true
        logger.warning("_get_all_active_chefs not fully implemented")
        return []

    async def _get_vendor_mapping(
        self,
        chef_id: UUID,
        company_id: Optional[int],
    ) -> Optional[dict]:
        """Get vendor mapping for a chef."""
        # TODO: Query accounting.chef_vendor_mappings
        return None

    async def _get_parent_company_id(self) -> int:
        """Get the parent company ID (My Hibachi main)."""
        # TODO: Get from config or query
        return 1

    async def _save_vendor_mapping(
        self,
        chef_id: UUID,
        akaunting_company_id: int,
        akaunting_vendor_id: int,
    ) -> None:
        """Save vendor mapping to database."""
        # TODO: Insert into accounting.chef_vendor_mappings
        logger.warning("_save_vendor_mapping not fully implemented")

    async def _update_mapping_sync_status(
        self,
        chef_id: UUID,
        company_id: Optional[int],
        status: str,
    ) -> None:
        """Update vendor mapping sync status."""
        # TODO: Update accounting.chef_vendor_mappings
        logger.warning("_update_mapping_sync_status not fully implemented")
