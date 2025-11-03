"""
Plaid RTP Payment API Router

Provides endpoints for Real-Time Payment processing via Plaid:
- Bank account linking
- Payment verification
- RTP payment initiation
- Payment status tracking

Cost Breakdown:
- RTP Transfer: 0% (FREE!)
- Total: 0% (no fees)

Savings Example (vs Stripe 3%):
- $100 order: Save $3.00
- $500 order: Save $15.00
- $1000 order: Save $30.00
"""

from decimal import Decimal
import logging

from api.app.database import get_db
from api.app.utils.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from services.plaid_service import plaid_service
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas
class LinkTokenRequest(BaseModel):
    """Request to create Plaid Link token"""

    user_name: str | None = Field(None, description="User's full name")


class LinkTokenResponse(BaseModel):
    """Plaid Link token for initializing frontend"""

    link_token: str
    expiration: str
    request_id: str


class ExchangeTokenRequest(BaseModel):
    """Exchange public token for access token"""

    public_token: str = Field(..., description="Public token from Plaid Link completion")


class ExchangeTokenResponse(BaseModel):
    """Access token and item ID"""

    access_token: str
    item_id: str
    message: str = "Bank account linked successfully"


class VerifyAccountRequest(BaseModel):
    """Verify bank account"""

    access_token: str = Field(..., description="Plaid access token")


class BankAccount(BaseModel):
    """Bank account details"""

    account_id: str
    name: str
    type: str
    subtype: str
    mask: str
    verification_status: str


class VerifyAccountResponse(BaseModel):
    """Verified bank account details"""

    accounts: list[BankAccount]
    message: str = "Bank account verified successfully"
    cost: float = Field(0.00, description="Verification fee (FREE)")


class BalanceCheckRequest(BaseModel):
    """Check account balance"""

    access_token: str
    account_id: str


class BalanceCheckResponse(BaseModel):
    """Account balance information"""

    available: float
    current: float
    currency: str
    account_id: str
    name: str
    mask: str
    cost: float = Field(0.00, description="Balance check fee (FREE)")


class InitiatePaymentRequest(BaseModel):
    """Initiate RTP payment"""

    access_token: str
    account_id: str
    amount: Decimal = Field(..., gt=0, description="Payment amount in dollars")
    booking_id: str = Field(..., description="Booking ID for reference")
    description: str | None = Field(None, description="Payment description")


class InitiatePaymentResponse(BaseModel):
    """Payment initiation confirmation"""

    payment_id: str
    status: str
    amount: float
    currency: str
    reference: str
    created_at: str
    fees: dict
    savings_vs_stripe: float


class PaymentStatusRequest(BaseModel):
    """Get payment status"""

    payment_id: str


class PaymentStatusResponse(BaseModel):
    """Current payment status"""

    payment_id: str
    status: str
    amount: float
    currency: str
    reference: str
    last_status_update: str | None


class CalculateFeesRequest(BaseModel):
    """Calculate Plaid fees"""

    amount: Decimal = Field(..., gt=0)


class CalculateFeesResponse(BaseModel):
    """Fee calculation breakdown"""

    amount: float
    transfer_fee: float
    total_fees: float
    net_amount: float
    savings_vs_stripe: float
    percentage_fee: str
    stripe_percentage: str
    recommendation: str


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    request: LinkTokenRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create Plaid Link token for bank account linking

    **Step 1** of Plaid RTP flow. Returns a link_token to initialize
    Plaid Link on the frontend. User will select their bank and log in.

    **Cost**: FREE (no charge for creating link tokens)

    **Frontend Usage**:
    ```javascript
    const { link_token } = await fetch('/api/v1/plaid/link-token', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Initialize Plaid Link
    const handler = Plaid.create({
        token: link_token,
        onSuccess: (public_token) => {
            // Exchange public token (Step 2)
        }
    });
    handler.open();
    ```

    Returns:
    - link_token: Token to initialize Plaid Link
    - expiration: Token expiration time
    - request_id: Plaid request ID for debugging
    """
    try:
        result = await plaid_service.create_link_token(
            user_id=current_user.id,
            user_email=current_user.email,
            user_name=request.user_name or current_user.full_name,
        )

        logger.info(f"Created Plaid link token for user {current_user.id}")

        return LinkTokenResponse(**result)

    except Exception as e:
        logger.exception(f"Error creating link token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bank link token",
        )


@router.post("/exchange-token", response_model=ExchangeTokenResponse)
async def exchange_public_token(
    request: ExchangeTokenRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange public token for access token

    **Step 2** of Plaid RTP flow. After user completes Plaid Link,
    exchange the temporary public_token for a permanent access_token.
    Store this access_token securely for future API calls.

    **Cost**: FREE (no charge for token exchange)

    **Security**: Store access_token encrypted in database. Never expose
    to frontend. Use for server-side API calls only.

    Returns:
    - access_token: Permanent token for API calls (store securely!)
    - item_id: Plaid item ID for this bank connection
    """
    try:
        result = await plaid_service.exchange_public_token(request.public_token)

        logger.info(f"Exchanged public token for user {current_user.id}, item {result['item_id']}")

        # TODO: Store access_token encrypted in database
        # await db.execute(
        #     "INSERT INTO plaid_accounts (user_id, access_token, item_id) VALUES (?, ?, ?)",
        #     (current_user.id, encrypt(result['access_token']), result['item_id'])
        # )

        return ExchangeTokenResponse(**result)

    except Exception as e:
        logger.exception(f"Error exchanging public token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to link bank account"
        )


@router.post("/verify-account", response_model=VerifyAccountResponse)
async def verify_bank_account(
    request: VerifyAccountRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify bank account and get details

    **Step 3** of Plaid RTP flow. Verify account ownership and retrieve
    account details for payment processing.

    **Cost**: FREE (no fees!)

    Returns:
    - accounts: List of verified bank accounts
    - cost: Verification fee (FREE)

    **Note**: No charges for bank verification with Plaid RTP.
    """
    try:
        result = await plaid_service.verify_bank_account(request.access_token)

        accounts = [BankAccount(**acc) for acc in result["accounts"]]

        logger.info(f"Verified {len(accounts)} accounts for user {current_user.id}")

        return VerifyAccountResponse(accounts=accounts)

    except Exception as e:
        logger.exception(f"Error verifying bank account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to verify bank account"
        )


@router.post("/check-balance", response_model=BalanceCheckResponse)
async def check_account_balance(
    request: BalanceCheckRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check real-time account balance

    **Optional** step before payment. Prevents insufficient funds errors
    by checking balance before initiating payment.

    **Cost**: FREE (no fees!)

    **Recommendation**: Check balance for large transactions ($500+)
    to prevent payment failures.

    Returns:
    - available: Available balance
    - current: Current balance
    - cost: Balance check fee (FREE)
    """
    try:
        result = await plaid_service.check_balance(request.access_token, request.account_id)

        logger.info(f"Checked balance for user {current_user.id}: ${result['available']}")

        return BalanceCheckResponse(**result)

    except Exception as e:
        logger.exception(f"Error checking balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to check account balance"
        )


@router.post("/initiate-payment", response_model=InitiatePaymentResponse)
async def initiate_rtp_payment(
    request: InitiatePaymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate RTP payment from customer to business

    **Step 4** of Plaid RTP flow. Process instant bank-to-bank payment.

    **Cost**: 0% (FREE!)
    - $100 payment = $0.00 fee
    - $500 payment = $0.00 fee
    - $1000 payment = $0.00 fee

    **Savings vs Stripe (3%)**:
    - $100: Save $3.00
    - $500: Save $15.00
    - $1000: Save $30.00

    **Processing Time**: Instant (Real-Time Payment)

    Returns:
    - payment_id: Plaid payment ID for tracking
    - status: Payment status (initiated, pending, executed)
    - fees: Detailed fee breakdown (all $0)
    - savings_vs_stripe: How much customer saved vs credit card
    """
    try:
        # Calculate fees
        fees = plaid_service.calculate_fees(request.amount)

        # Initiate payment
        result = await plaid_service.initiate_payment(
            access_token=request.access_token,
            account_id=request.account_id,
            amount=request.amount,
            reference=request.booking_id,
            description=request.description
            or f"My Hibachi payment for booking {request.booking_id}",
        )

        logger.info(
            f"Initiated RTP payment {result['payment_id']} "
            f"for ${request.amount} from user {current_user.id}"
        )

        # TODO: Record payment in database
        # await db.execute(
        #     "INSERT INTO payments (user_id, booking_id, plaid_payment_id, amount, method, status) "
        #     "VALUES (?, ?, ?, ?, 'plaid', 'pending')",
        #     (current_user.id, request.booking_id, result['payment_id'], request.amount)
        # )

        return InitiatePaymentResponse(
            **result, fees=fees, savings_vs_stripe=fees["savings_vs_stripe"]
        )

    except Exception as e:
        logger.exception(f"Error initiating payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to initiate payment"
        )


@router.post("/payment-status", response_model=PaymentStatusResponse)
async def get_payment_status(
    request: PaymentStatusRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current status of RTP payment

    Track payment through its lifecycle:
    - **initiated**: Payment request created
    - **pending**: Being processed by banks
    - **executed**: Successfully completed
    - **failed**: Payment failed (insufficient funds, etc.)

    **Cost**: FREE (included with payment)

    **Typical Timeline**:
    - initiated → pending: ~30 seconds
    - pending → executed: 1-5 minutes (instant for RTP)

    Returns:
    - status: Current payment status
    - last_status_update: When status was last updated
    """
    try:
        result = await plaid_service.get_payment_status(request.payment_id)

        logger.info(f"Retrieved payment status for {request.payment_id}: {result['status']}")

        return PaymentStatusResponse(**result)

    except Exception as e:
        logger.exception(f"Error getting payment status: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")


@router.post("/calculate-fees", response_model=CalculateFeesResponse)
async def calculate_plaid_fees(request: CalculateFeesRequest):
    """
    Calculate Plaid RTP fees (public endpoint, no auth required)

    Show customers exactly how much they'll save by using Plaid RTP
    instead of credit card.

    **Fee Structure**:
    - RTP Transfer: 0% (FREE!)
    - Total: 0% (no fees)

    **Compare to**:
    - Stripe (credit card): 3.00%
    - Zelle: 0% (but manual confirmation)
    - Venmo: 3.00%
    - Plaid RTP: 0% (instant + automated!)

    Returns detailed fee breakdown and savings calculation.
    """
    fees = plaid_service.calculate_fees(request.amount)

    # Add recommendation based on amount
    if request.amount >= 100:
        recommendation = (
            f"💰 Recommended! Save ${fees['savings_vs_stripe']:.2f} "
            f"compared to credit card. Instant bank transfer with Plaid RTP."
        )
    else:
        recommendation = (
            f"For payments under $100, consider Zelle (0% fees) if you don't "
            f"need instant confirmation. Plaid RTP still saves ${fees['savings_vs_stripe']:.2f} vs credit card."
        )

    return CalculateFeesResponse(
        amount=float(request.amount), **fees, recommendation=recommendation
    )
