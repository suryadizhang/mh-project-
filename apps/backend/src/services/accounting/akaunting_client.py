"""
Akaunting REST API Client
=========================
HTTP client for communicating with Akaunting's REST API.

API Documentation: https://akaunting.com/docs/api
Authentication: Bearer token (created in Akaunting Settings → API)

Batch 7A: Foundation
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class AkauntingConfig(BaseModel):
    """Akaunting API configuration."""

    base_url: str = Field(
        default="http://localhost:9000", description="Akaunting base URL (internal Docker network)"
    )
    api_token: str = Field(default="", description="API token from Akaunting Settings → API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    company_id: Optional[int] = Field(
        default=None, description="Default company ID for single-company operations"
    )


# =============================================================================
# Response Models
# =============================================================================


class AkauntingCompany(BaseModel):
    """Akaunting company representation."""

    id: int
    name: str
    email: Optional[str] = None
    tax_number: Optional[str] = None
    currency_code: str = "USD"
    enabled: bool = True


class AkauntingContact(BaseModel):
    """Akaunting contact (customer/vendor) representation."""

    id: int
    company_id: int
    type: str  # "customer" or "vendor"
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    currency_code: str = "USD"
    enabled: bool = True


class AkauntingInvoice(BaseModel):
    """Akaunting invoice representation."""

    id: int
    company_id: int
    contact_id: int
    contact_name: str
    invoice_number: str
    status: str  # draft, sent, viewed, partial, paid, cancelled, overdue
    issued_at: date
    due_at: date
    amount: Decimal
    amount_due: Decimal
    currency_code: str = "USD"
    notes: Optional[str] = None


class AkauntingTransaction(BaseModel):
    """Akaunting transaction representation."""

    id: int
    company_id: int
    type: str  # income, expense, transfer
    account_id: int
    category_id: Optional[int] = None
    contact_id: Optional[int] = None
    amount: Decimal
    currency_code: str = "USD"
    paid_at: date
    description: Optional[str] = None
    reference: Optional[str] = None  # Stripe payment ID, etc.


# =============================================================================
# Akaunting API Client
# =============================================================================


class AkauntingClient:
    """
    HTTP client for Akaunting REST API.

    Usage:
        client = AkauntingClient(config)
        companies = await client.list_companies()
        invoice = await client.create_invoice(company_id, invoice_data)
    """

    def __init__(self, config: Optional[AkauntingConfig] = None):
        """Initialize the Akaunting client."""
        self.config = config or AkauntingConfig(
            base_url=getattr(settings, "AKAUNTING_URL", "http://localhost:9000"),
            api_token=getattr(settings, "AKAUNTING_API_TOKEN", ""),
        )
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"{self.config.base_url}/api",
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Company": str(self.config.company_id) if self.config.company_id else "",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "AkauntingClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:
        """Context manager exit."""
        await self.close()

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> bool:
        """Check if Akaunting API is accessible."""
        try:
            response = await self.client.get("/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Akaunting health check failed: {e}")
            return False

    # =========================================================================
    # Companies
    # =========================================================================

    async def list_companies(self) -> list[AkauntingCompany]:
        """List all companies in Akaunting."""
        try:
            response = await self.client.get("/companies")
            response.raise_for_status()
            data = response.json()
            return [AkauntingCompany(**c) for c in data.get("data", [])]
        except httpx.HTTPError as e:
            logger.error(f"Failed to list companies: {e}")
            raise

    async def get_company(self, company_id: int) -> AkauntingCompany:
        """Get a specific company by ID."""
        try:
            response = await self.client.get(f"/companies/{company_id}")
            response.raise_for_status()
            data = response.json()
            return AkauntingCompany(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to get company {company_id}: {e}")
            raise

    async def create_company(
        self,
        name: str,
        email: str,
        currency_code: str = "USD",
        tax_number: Optional[str] = None,
    ) -> AkauntingCompany:
        """Create a new company (for new station)."""
        try:
            payload = {
                "name": name,
                "email": email,
                "currency_code": currency_code,
                "enabled": True,
            }
            if tax_number:
                payload["tax_number"] = tax_number

            response = await self.client.post("/companies", json=payload)
            response.raise_for_status()
            data = response.json()
            return AkauntingCompany(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to create company: {e}")
            raise

    # =========================================================================
    # Contacts (Customers & Vendors)
    # =========================================================================

    async def list_contacts(
        self,
        company_id: int,
        contact_type: str = "customer",
        search: Optional[str] = None,
        limit: int = 25,
    ) -> list[AkauntingContact]:
        """List contacts for a company."""
        try:
            params = {
                "type": contact_type,
                "limit": limit,
            }
            if search:
                params["search"] = search

            response = await self.client.get(
                f"/companies/{company_id}/contacts",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [AkauntingContact(**c) for c in data.get("data", [])]
        except httpx.HTTPError as e:
            logger.error(f"Failed to list contacts: {e}")
            raise

    async def create_contact(
        self,
        company_id: int,
        name: str,
        email: str,
        contact_type: str = "customer",
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_number: Optional[str] = None,
    ) -> AkauntingContact:
        """Create a new contact (customer or vendor)."""
        try:
            payload = {
                "type": contact_type,
                "name": name,
                "email": email,
                "currency_code": "USD",
                "enabled": True,
            }
            if phone:
                payload["phone"] = phone
            if address:
                payload["address"] = address
            if tax_number:
                payload["tax_number"] = tax_number

            response = await self.client.post(
                f"/companies/{company_id}/contacts",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingContact(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to create contact: {e}")
            raise

    async def update_contact(
        self,
        company_id: int,
        contact_id: int,
        **updates,
    ) -> AkauntingContact:
        """Update an existing contact."""
        try:
            response = await self.client.patch(
                f"/companies/{company_id}/contacts/{contact_id}",
                json=updates,
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingContact(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to update contact {contact_id}: {e}")
            raise

    # =========================================================================
    # Invoices
    # =========================================================================

    async def list_invoices(
        self,
        company_id: int,
        status: Optional[str] = None,
        contact_id: Optional[int] = None,
        limit: int = 25,
    ) -> list[AkauntingInvoice]:
        """List invoices for a company."""
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            if contact_id:
                params["contact_id"] = contact_id

            response = await self.client.get(
                f"/companies/{company_id}/invoices",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [AkauntingInvoice(**i) for i in data.get("data", [])]
        except httpx.HTTPError as e:
            logger.error(f"Failed to list invoices: {e}")
            raise

    async def create_invoice(
        self,
        company_id: int,
        contact_id: int,
        items: list[dict],
        issued_at: date,
        due_at: date,
        invoice_number: Optional[str] = None,
        notes: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> AkauntingInvoice:
        """
        Create a new invoice.

        Args:
            company_id: Akaunting company ID
            contact_id: Customer contact ID
            items: List of line items, each with:
                - name: str
                - quantity: int
                - price: Decimal
                - tax_id: Optional[int]
            issued_at: Invoice date
            due_at: Payment due date
            invoice_number: Optional custom invoice number
            notes: Optional notes for invoice
            category_id: Optional income category ID
        """
        try:
            payload = {
                "contact_id": contact_id,
                "items": items,
                "issued_at": issued_at.isoformat(),
                "due_at": due_at.isoformat(),
                "currency_code": "USD",
                "status": "draft",
            }
            if invoice_number:
                payload["invoice_number"] = invoice_number
            if notes:
                payload["notes"] = notes
            if category_id:
                payload["category_id"] = category_id

            response = await self.client.post(
                f"/companies/{company_id}/invoices",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingInvoice(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to create invoice: {e}")
            raise

    async def get_invoice(
        self,
        company_id: int,
        invoice_id: int,
    ) -> AkauntingInvoice:
        """Get invoice details."""
        try:
            response = await self.client.get(f"/companies/{company_id}/invoices/{invoice_id}")
            response.raise_for_status()
            data = response.json()
            return AkauntingInvoice(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to get invoice {invoice_id}: {e}")
            raise

    async def update_invoice_status(
        self,
        company_id: int,
        invoice_id: int,
        status: str,
    ) -> AkauntingInvoice:
        """
        Update invoice status.

        Valid statuses: draft, sent, viewed, partial, paid, cancelled
        """
        try:
            response = await self.client.patch(
                f"/companies/{company_id}/invoices/{invoice_id}",
                json={"status": status},
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingInvoice(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to update invoice status: {e}")
            raise

    async def send_invoice(
        self,
        company_id: int,
        invoice_id: int,
    ) -> bool:
        """Send invoice email to customer."""
        try:
            response = await self.client.post(f"/companies/{company_id}/invoices/{invoice_id}/send")
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send invoice {invoice_id}: {e}")
            return False

    async def get_invoice_pdf_url(
        self,
        company_id: int,
        invoice_id: int,
    ) -> str:
        """Get the PDF download URL for an invoice."""
        return f"{self.config.base_url}/api/companies/{company_id}/invoices/{invoice_id}/pdf"

    # =========================================================================
    # Transactions (Payments)
    # =========================================================================

    async def create_transaction(
        self,
        company_id: int,
        account_id: int,
        amount: Decimal,
        paid_at: date,
        transaction_type: str = "income",
        contact_id: Optional[int] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> AkauntingTransaction:
        """
        Create a new transaction (income/expense).

        Args:
            company_id: Akaunting company ID
            account_id: Bank/payment account ID
            amount: Transaction amount
            paid_at: Payment date
            transaction_type: 'income', 'expense', or 'transfer'
            contact_id: Optional customer/vendor ID
            category_id: Optional category ID
            description: Optional description
            reference: Optional external reference (Stripe payment ID)
        """
        try:
            payload = {
                "type": transaction_type,
                "account_id": account_id,
                "amount": str(amount),
                "paid_at": paid_at.isoformat(),
                "currency_code": "USD",
            }
            if contact_id:
                payload["contact_id"] = contact_id
            if category_id:
                payload["category_id"] = category_id
            if description:
                payload["description"] = description
            if reference:
                payload["reference"] = reference

            response = await self.client.post(
                f"/companies/{company_id}/transactions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingTransaction(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to create transaction: {e}")
            raise

    async def record_invoice_payment(
        self,
        company_id: int,
        invoice_id: int,
        account_id: int,
        amount: Decimal,
        paid_at: date,
        description: Optional[str] = None,
    ) -> AkauntingTransaction:
        """
        Record a payment against an invoice.

        This updates the invoice status automatically.
        """
        try:
            payload = {
                "account_id": account_id,
                "amount": str(amount),
                "paid_at": paid_at.isoformat(),
                "currency_code": "USD",
            }
            if description:
                payload["description"] = description

            response = await self.client.post(
                f"/companies/{company_id}/invoices/{invoice_id}/transactions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return AkauntingTransaction(**data.get("data", {}))
        except httpx.HTTPError as e:
            logger.error(f"Failed to record invoice payment: {e}")
            raise

    # =========================================================================
    # Categories & Accounts
    # =========================================================================

    async def list_categories(
        self,
        company_id: int,
        category_type: str = "income",
    ) -> list[dict]:
        """List categories (income or expense)."""
        try:
            response = await self.client.get(
                f"/companies/{company_id}/categories",
                params={"type": category_type},
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list categories: {e}")
            raise

    async def list_accounts(self, company_id: int) -> list[dict]:
        """List bank/payment accounts."""
        try:
            response = await self.client.get(f"/companies/{company_id}/accounts")
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list accounts: {e}")
            raise

    # =========================================================================
    # Tax Rates
    # =========================================================================

    async def list_tax_rates(self, company_id: int) -> list[dict]:
        """List tax rates for a company."""
        try:
            response = await self.client.get(f"/companies/{company_id}/taxes")
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list tax rates: {e}")
            raise

    async def create_tax_rate(
        self,
        company_id: int,
        name: str,
        rate: Decimal,
        type: str = "normal",  # normal, inclusive, compound
    ) -> dict:
        """Create a new tax rate."""
        try:
            payload = {
                "name": name,
                "rate": str(rate),
                "type": type,
                "enabled": True,
            }
            response = await self.client.post(
                f"/companies/{company_id}/taxes",
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("data", {})
        except httpx.HTTPError as e:
            logger.error(f"Failed to create tax rate: {e}")
            raise


# =============================================================================
# Singleton Instance
# =============================================================================

_akaunting_client: Optional[AkauntingClient] = None


def get_akaunting_client() -> AkauntingClient:
    """Get or create the singleton Akaunting client."""
    global _akaunting_client
    if _akaunting_client is None:
        _akaunting_client = AkauntingClient()
    return _akaunting_client
