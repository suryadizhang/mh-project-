"""
Plaid RTP (Real-Time Payments) Service

Handles bank account verification and RTP payment processing through Plaid API.
Enables instant bank-to-bank transfers with lower fees (~1%) compared to credit cards (8%).

Features:
- Bank account linking via Plaid Link
- Identity verification ($0.05 per verification)
- Balance checks before payment ($0.05 per check)
- RTP payment initiation (~1% fee)
- Transaction tracking and webhooks

Cost Structure:
- Auth (verify bank): $0.05/verification
- Balance check: $0.05/check
- RTP transfer: ~1% of transaction amount
- Example: $500 order = $0.05 + $0.05 + $5.00 = $5.10 total fees
- Savings vs Stripe: $40 - $5.10 = $34.90 saved (8% vs 1%)
"""

from datetime import datetime
from decimal import Decimal
import logging
import os

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import (
    LinkTokenCreateRequestUser,
)
from plaid.model.payment_amount import PaymentAmount
from plaid.model.payment_amount_currency import PaymentAmountCurrency
from plaid.model.payment_initiation_payment_create_request import (
    PaymentInitiationPaymentCreateRequest,
)
from plaid.model.payment_initiation_payment_get_request import (
    PaymentInitiationPaymentGetRequest,
)
from plaid.model.products import Products

logger = logging.getLogger(__name__)


class PlaidService:
    """
    Service for Plaid RTP payment processing

    Handles:
    1. Link Token creation (for bank account linking UI)
    2. Public token exchange (convert temporary token to permanent access token)
    3. Bank account verification (Auth product)
    4. Balance checking (before payment processing)
    5. RTP payment initiation and tracking
    """

    def __init__(self):
        """Initialize Plaid client with credentials from environment"""
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.env = os.getenv("PLAID_ENV", "sandbox")

        # Map environment name to Plaid host (newer SDK uses string values)
        env_hosts = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }

        if not self.client_id or not self.secret:
            logger.error("Plaid credentials not configured - using mock mode")
            # Set mock mode flag instead of raising error
            self.mock_mode = True
            self.client = None
            return

        self.mock_mode = False

        # Initialize Plaid API client
        configuration = plaid.Configuration(
            host=env_hosts.get(self.env, "https://sandbox.plaid.com"),
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            },
        )

        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

        # Business account details for receiving payments
        self.business_name = os.getenv("BUSINESS_NAME", "My Hibachi LLC")
        self.business_account_id = os.getenv("PLAID_BUSINESS_ACCOUNT_ID")

        logger.info(
            f"Plaid service initialized in {self.env} mode {'(MOCK)' if self.mock_mode else ''}"
        )

    async def create_link_token(
        self, user_id: str, user_email: str, user_name: str | None = None
    ) -> dict:
        """
        Create a Link token for Plaid Link UI

        This token is used to initialize Plaid Link on the frontend,
        allowing customers to securely connect their bank account.

        Args:
            user_id: Unique user identifier
            user_email: User's email address
            user_name: User's full name (optional)

        Returns:
            {
                "link_token": "link-sandbox-xxx",
                "expiration": "2025-10-30T12:00:00Z",
                "request_id": "abc123"
            }

        Cost: FREE (no charge for creating link tokens)
        """
        # Return mock data if in mock mode
        if self.mock_mode:
            logger.warning("Plaid in mock mode - returning fake link token")
            return {
                "link_token": "link-sandbox-mock-" + user_id[:8],
                "expiration": "2025-10-30T12:00:00Z",
                "request_id": "mock-request-" + user_id[:8],
            }

        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(
                    client_user_id=user_id, email_address=user_email, name=user_name
                ),
                client_name=self.business_name,
                products=[Products("auth"), Products("identity"), Products("balance")],
                country_codes=[CountryCode("US")],
                language="en",
                webhook="https://api.myhibachichef.com/webhooks/plaid",
                redirect_uri=os.getenv("FRONTEND_URL", "http://localhost:3001"),
            )

            response = self.client.link_token_create(request)

            logger.info(f"Created Plaid Link token for user {user_id}")

            return {
                "link_token": response.link_token,
                "expiration": response.expiration,
                "request_id": response.request_id,
            }

        except plaid.ApiException as e:
            logger.exception(f"Error creating Plaid link token: {e}")
            raise

    async def exchange_public_token(self, public_token: str) -> dict:
        """
        Exchange a public token for an access token

        After user completes Plaid Link, frontend receives a temporary
        public_token. This function exchanges it for a permanent access_token
        that can be used for API calls.

        Args:
            public_token: Temporary token from Plaid Link completion

        Returns:
            {
                "access_token": "access-sandbox-xxx",
                "item_id": "item-xxx",
                "request_id": "abc123"
            }

        Cost: FREE (no charge for token exchange)
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)

            response = self.client.item_public_token_exchange(request)

            logger.info(f"Exchanged public token for item {response.item_id}")

            return {
                "access_token": response.access_token,
                "item_id": response.item_id,
                "request_id": response.request_id,
            }

        except plaid.ApiException as e:
            logger.exception(f"Error exchanging public token: {e}")
            raise

    async def verify_bank_account(self, access_token: str) -> dict:
        """
        Verify bank account and get account details

        Uses Plaid Auth to verify account ownership and retrieve
        account/routing numbers for ACH transfers.

        Args:
            access_token: Plaid access token for the linked account

        Returns:
            {
                "accounts": [
                    {
                        "account_id": "xxx",
                        "name": "Checking",
                        "type": "depository",
                        "subtype": "checking",
                        "mask": "0000",
                        "verification_status": "verified"
                    }
                ],
                "numbers": {
                    "ach": [
                        {
                            "account": "1234567890",
                            "routing": "011000015",
                            "account_id": "xxx"
                        }
                    ]
                }
            }

        Cost: $0.05 per verification
        """
        try:
            request = AuthGetRequest(access_token=access_token)

            response = self.client.auth_get(request)

            logger.info(f"Verified {len(response.accounts)} bank accounts")

            # Format account data
            accounts = []
            for account in response.accounts:
                accounts.append(
                    {
                        "account_id": account.account_id,
                        "name": account.name,
                        "type": account.type,
                        "subtype": account.subtype,
                        "mask": account.mask,
                        "verification_status": "verified",
                    }
                )

            # Format ACH numbers (if available)
            ach_numbers = []
            if hasattr(response, "numbers") and hasattr(response.numbers, "ach"):
                for ach in response.numbers.ach:
                    ach_numbers.append(
                        {
                            "account": ach.account,
                            "routing": ach.routing,
                            "account_id": ach.account_id,
                        }
                    )

            return {"accounts": accounts, "numbers": {"ach": ach_numbers}}

        except plaid.ApiException as e:
            logger.exception(f"Error verifying bank account: {e}")
            raise

    async def check_balance(self, access_token: str, account_id: str) -> dict:
        """
        Check real-time account balance

        Prevents insufficient funds errors by checking balance
        before initiating payment.

        Args:
            access_token: Plaid access token
            account_id: Specific account to check

        Returns:
            {
                "available": 1250.50,
                "current": 1500.00,
                "currency": "USD",
                "account_id": "xxx"
            }

        Cost: $0.05 per balance check
        """
        try:
            request = AccountsBalanceGetRequest(
                access_token=access_token, options={"account_ids": [account_id]}
            )

            response = self.client.accounts_balance_get(request)

            if response.accounts:
                account = response.accounts[0]
                balances = account.balances

                logger.info(f"Retrieved balance for account {account_id}")

                return {
                    "available": float(balances.available or 0),
                    "current": float(balances.current or 0),
                    "currency": balances.iso_currency_code or "USD",
                    "account_id": account.account_id,
                    "name": account.name,
                    "mask": account.mask,
                }

            raise ValueError("Account not found")

        except plaid.ApiException as e:
            logger.exception(f"Error checking balance: {e}")
            raise

    async def initiate_payment(
        self,
        access_token: str,
        account_id: str,
        amount: Decimal,
        reference: str,
        description: str | None = None,
    ) -> dict:
        """
        Initiate RTP payment from customer to business

        Creates a payment initiation request through Plaid's Payment
        Initiation API for instant bank-to-bank transfer.

        Args:
            access_token: Customer's Plaid access token
            account_id: Customer's bank account ID
            amount: Payment amount in dollars (e.g., 500.00)
            reference: Unique reference (booking ID, invoice #, etc.)
            description: Payment description

        Returns:
            {
                "payment_id": "payment-xxx",
                "status": "initiated",
                "amount": 500.00,
                "currency": "USD",
                "reference": "BOOKING-123",
                "created_at": "2025-10-29T12:00:00Z"
            }

        Cost: ~1% of transaction amount (e.g., $5.00 for $500 payment)
        """
        try:
            # Step 1: Create recipient (business account)
            if not self.business_account_id:
                raise ValueError("Business Plaid account not configured")

            # Step 2: Create payment amount
            payment_amount = PaymentAmount(
                value=float(amount), currency=PaymentAmountCurrency("USD")
            )

            # Step 3: Create payment request
            request = PaymentInitiationPaymentCreateRequest(
                recipient_id=self.business_account_id,
                reference=reference,
                amount=payment_amount,
                schedule=None,  # Immediate payment
                options={"request_refund_details": False, "iban": None},
            )

            response = self.client.payment_initiation_payment_create(request)

            logger.info(f"Initiated RTP payment {response.payment_id} for ${amount}")

            return {
                "payment_id": response.payment_id,
                "status": response.status,
                "amount": float(amount),
                "currency": "USD",
                "reference": reference,
                "description": description,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

        except plaid.ApiException as e:
            logger.exception(f"Error initiating payment: {e}")
            raise

    async def get_payment_status(self, payment_id: str) -> dict:
        """
        Get current status of RTP payment

        Track payment through its lifecycle:
        - initiated: Payment request created
        - pending: Being processed
        - executed: Successfully completed
        - failed: Payment failed

        Args:
            payment_id: Plaid payment ID

        Returns:
            {
                "payment_id": "payment-xxx",
                "status": "executed",
                "amount": 500.00,
                "currency": "USD",
                "last_status_update": "2025-10-29T12:05:00Z"
            }

        Cost: FREE (status checks included with payment)
        """
        try:
            request = PaymentInitiationPaymentGetRequest(payment_id=payment_id)

            response = self.client.payment_initiation_payment_get(request)

            logger.info(f"Retrieved payment status for {payment_id}: {response.status}")

            return {
                "payment_id": response.payment_id,
                "status": response.status,
                "amount": float(response.amount.value),
                "currency": response.amount.currency,
                "reference": response.reference,
                "last_status_update": (
                    response.last_status_update.isoformat() + "Z"
                    if hasattr(response, "last_status_update")
                    else None
                ),
            }

        except plaid.ApiException as e:
            logger.exception(f"Error getting payment status: {e}")
            raise

    def calculate_fees(self, amount: Decimal) -> dict:
        """
        Calculate Plaid RTP fees for transparency

        Args:
            amount: Payment amount in dollars

        Returns:
            {
                "transfer_fee": 0.00,
                "total_fees": 0.00,
                "net_amount": 500.00,
                "savings_vs_stripe": 15.00
            }
        """
        # Plaid RTP is FREE for us (0% processing fee)
        transfer_fee = Decimal("0.00")
        total_fees = Decimal("0.00")
        net_amount = amount

        # Compare to Stripe (3% fee)
        stripe_fee = amount * Decimal("0.03")
        savings = stripe_fee - total_fees

        return {
            "transfer_fee": float(transfer_fee),
            "total_fees": float(total_fees),
            "net_amount": float(net_amount),
            "savings_vs_stripe": float(savings),
            "percentage_fee": "0.00%",  # FREE!
            "stripe_percentage": "3.00%",
        }


# Singleton instance
plaid_service = PlaidService()
