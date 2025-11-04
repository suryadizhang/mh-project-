"""
Payment Calculation API Router

Calculates payment totals with processing fees for different payment methods.
Helps customers see the exact cost before selecting a payment method.

Payment Methods & Fees:
- Zelle: 0% (FREE)
- Venmo: 0% (standard transfer)
- Stripe: 2.9% + $0.30 processing fee
"""

from decimal import Decimal
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas
class CalculatePaymentRequest(BaseModel):
    """Request to calculate payment with fees"""

    base_amount: Decimal = Field(..., gt=0, description="Base payment amount (before fees)")
    tip_amount: Decimal = Field(0, ge=0, description="Tip amount")
    payment_method: str = Field(..., description="Payment method: zelle, venmo, or stripe")


class PaymentMethodBreakdown(BaseModel):
    """Payment breakdown for a specific method"""

    method: str
    method_display_name: str
    base_amount: float
    tip_amount: float
    subtotal: float
    processing_fee: float
    processing_fee_percentage: str
    total_amount: float
    savings_vs_stripe: float
    is_free: bool
    is_instant: bool
    confirmation_time: str


class CalculatePaymentResponse(BaseModel):
    """Payment calculation with all fees"""

    base_amount: float
    tip_amount: float
    subtotal: float
    selected_method: PaymentMethodBreakdown
    all_methods: list[PaymentMethodBreakdown]
    recommendation: str


class CompareAllMethodsRequest(BaseModel):
    """Request to compare all payment methods"""

    base_amount: Decimal = Field(..., gt=0)
    tip_amount: Decimal = Field(0, ge=0)


class CompareAllMethodsResponse(BaseModel):
    """Comparison of all 4 payment methods"""

    base_amount: float
    tip_amount: float
    subtotal: float
    methods: list[PaymentMethodBreakdown]
    best_value: str
    fastest: str
    recommendation: str


def calculate_payment_breakdown(
    base_amount: Decimal, tip_amount: Decimal, payment_method: str
) -> PaymentMethodBreakdown:
    """
    Calculate payment breakdown for a specific method

    Fee Structure:
    - Zelle: 0%
    - Venmo: 0%
    - Stripe: 2.9% + $0.30
    """
    # Define fee percentages
    fee_rates = {
        "zelle": Decimal("0.00"),
        "venmo": Decimal("0.00"),
        "stripe": Decimal("0.029"),
    }

    # Stripe fixed fee
    stripe_fixed_fee = Decimal("0.30")

    # Display names
    display_names = {
        "zelle": "Zelle",
        "venmo": "Venmo",
        "stripe": "Credit Card (Stripe)",
    }

    # Method characteristics
    instant_methods = ["stripe"]
    confirmation_times = {
        "zelle": "1-2 hours (manual confirmation)",
        "venmo": "1-2 hours (manual confirmation)",
        "stripe": "Instant (automated)",
    }

    method = payment_method.lower()
    fee_rate = fee_rates.get(method, Decimal("0.029"))  # Default to Stripe rate

    subtotal = base_amount + tip_amount

    # Calculate processing fee (Stripe has fixed + percentage)
    if method == "stripe":
        processing_fee = (subtotal * fee_rate) + stripe_fixed_fee
    else:
        processing_fee = subtotal * fee_rate

    total = subtotal + processing_fee

    # Calculate savings vs Stripe (2.9% + $0.30)
    stripe_fee = (subtotal * Decimal("0.029")) + Decimal("0.30")
    savings = float(stripe_fee - processing_fee)

    return PaymentMethodBreakdown(
        method=method,
        method_display_name=display_names.get(method, method.title()),
        base_amount=float(base_amount),
        tip_amount=float(tip_amount),
        subtotal=float(subtotal),
        processing_fee=float(processing_fee),
        processing_fee_percentage=(
            f"{float(fee_rate * 100):.2f}%" if method != "stripe" else "2.9% + $0.30"
        ),
        total_amount=float(total),
        savings_vs_stripe=savings,
        is_free=(fee_rate == 0),
        is_instant=(method in instant_methods),
        confirmation_time=confirmation_times.get(method, "Varies"),
    )


@router.post("/calculate", response_model=CalculatePaymentResponse)
async def calculate_payment_with_fees(request: CalculatePaymentRequest):
    """
    Calculate payment total with processing fees

    Shows customer the exact amount they'll pay including processing fees
    for their selected payment method.

    **Example Request**:
    ```json
    {
      "base_amount": 500.00,
      "tip_amount": 50.00,
      "payment_method": "stripe"
    }
    ```

    **Example Response**:
    ```json
    {
      "base_amount": 500.00,
      "tip_amount": 50.00,
      "subtotal": 550.00,
      "selected_method": {
        "method": "stripe",
        "method_display_name": "Credit Card (Stripe)",
        "processing_fee": 16.50,
        "total_amount": 566.50
      },
      "all_methods": [...],
      "recommendation": "💡 Save $16.50! Use Zelle or Bank Transfer (FREE)"
    }
    ```
    """
    # Calculate for selected method
    selected = calculate_payment_breakdown(
        request.base_amount, request.tip_amount, request.payment_method
    )

    # Calculate for all methods for comparison
    all_methods = [
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "zelle"),
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "venmo"),
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "stripe"),
    ]

    # Generate recommendation
    if request.payment_method in ["zelle", "venmo"]:
        recommendation = "✅ Great choice! No processing fees with this payment method."
    else:  # stripe
        recommendation = f"💡 Save ${selected.processing_fee:.2f}! Use Zelle or Venmo (FREE)"

    return CalculatePaymentResponse(
        base_amount=float(request.base_amount),
        tip_amount=float(request.tip_amount),
        subtotal=float(request.base_amount + request.tip_amount),
        selected_method=selected,
        all_methods=all_methods,
        recommendation=recommendation,
    )


@router.post("/compare", response_model=CompareAllMethodsResponse)
async def compare_all_payment_methods(request: CompareAllMethodsRequest):
    """
    Compare all 4 payment methods side-by-side

    Shows customer all options with fees, helping them make an informed decision.

    **Example Request**:
    ```json
    {
      "base_amount": 500.00,
      "tip_amount": 50.00
    }
    ```

    **Example Response**:
    ```json
    {
      "subtotal": 550.00,
      "methods": [
        {
          "method": "zelle",
          "total_amount": 550.00,
          "processing_fee": 0.00,
          "savings_vs_stripe": 16.25
        },
        {
          "method": "venmo",
          "total_amount": 550.00,
          "processing_fee": 0.00,
          "savings_vs_stripe": 16.25
        },
        {
          "method": "stripe",
          "total_amount": 566.25,
          "processing_fee": 16.25,
          "is_instant": true
        }
      ],
      "best_value": "zelle or venmo (FREE)",
      "fastest": "stripe (instant)",
      "recommendation": "💰 Best: Zelle or Venmo - FREE!"
    }
    ```
    """
    # Calculate for all methods
    methods = [
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "zelle"),
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "plaid"),
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "venmo"),
        calculate_payment_breakdown(request.base_amount, request.tip_amount, "stripe"),
    ]

    # Determine best options
    best_value = "Zelle or Bank Transfer (Plaid) - FREE"
    fastest = "Bank Transfer (Plaid) or Credit Card - Instant"

    # Smart recommendation based on amount
    subtotal = request.base_amount + request.tip_amount
    if subtotal >= 100:
        recommendation = (
            f"💰 Best: Bank Transfer (Plaid) - FREE + Instant! "
            f"Save ${float(subtotal * Decimal('0.03')):.2f} vs credit card."
        )
    else:
        recommendation = (
            "💡 For small amounts, any FREE method works! "
            "Bank Transfer (Plaid) is instant, Zelle requires confirmation."
        )

    return CompareAllMethodsResponse(
        base_amount=float(request.base_amount),
        tip_amount=float(request.tip_amount),
        subtotal=float(subtotal),
        methods=methods,
        best_value=best_value,
        fastest=fastest,
        recommendation=recommendation,
    )


@router.get("/methods", response_model=dict)
async def get_payment_methods_info():
    """
    Get information about all available payment methods

    Returns static information about payment methods, fees, and characteristics.
    Useful for building payment selection UI.

    **Response**:
    ```json
    {
      "methods": [
        {
          "id": "zelle",
          "name": "Zelle",
          "icon": "Z",
          "color": "purple",
          "fee_percentage": 0.00,
          "is_free": true,
          "is_instant": false,
          "confirmation_time": "1-2 hours",
          "qr_code_available": true,
          "description": "Free bank transfer with manual confirmation"
        },
        ...
      ]
    }
    ```
    """
    methods = [
        {
            "id": "zelle",
            "name": "Zelle",
            "icon": "Z",
            "color": "purple",
            "fee_percentage": 0.00,
            "is_free": True,
            "is_instant": False,
            "confirmation_time": "1-2 hours",
            "qr_code_available": True,
            "description": "Free bank transfer with manual confirmation",
            "recommended_for": "All orders (FREE!)",
            "email": "myhibachichef@gmail.com",
            "phone": "+19167408768",
        },
        {
            "id": "plaid",
            "name": "Bank Transfer",
            "display_name": "Bank Transfer (Plaid RTP)",
            "icon": "🏦",
            "color": "green",
            "fee_percentage": 0.00,
            "is_free": True,
            "is_instant": True,
            "confirmation_time": "Instant",
            "qr_code_available": False,
            "description": "Free instant bank transfer (automated)",
            "recommended_for": "All orders (FREE + Instant!)",
            "benefits": ["No fees", "Instant confirmation", "Automated", "Secure"],
        },
        {
            "id": "venmo",
            "name": "Venmo",
            "icon": "V",
            "color": "blue",
            "fee_percentage": 3.00,
            "is_free": False,
            "is_instant": False,
            "confirmation_time": "1-2 hours",
            "qr_code_available": True,
            "description": "Peer-to-peer payment with 3% processing fee",
            "recommended_for": "Small orders if you prefer Venmo",
            "username": "@myhibachichef",
        },
        {
            "id": "stripe",
            "name": "Credit Card",
            "display_name": "Credit Card (Stripe)",
            "icon": "💳",
            "color": "blue",
            "fee_percentage": 3.00,
            "is_free": False,
            "is_instant": True,
            "confirmation_time": "Instant",
            "qr_code_available": False,
            "description": "Credit/debit card with 3% processing fee",
            "recommended_for": "If you don't have a bank account linked",
            "accepted_cards": ["Visa", "Mastercard", "Amex", "Discover"],
        },
    ]

    return {
        "success": True,
        "methods": methods,
        "recommendation": "Bank Transfer (Plaid) offers the best value: FREE + Instant!",
        "total_methods": 4,
    }
