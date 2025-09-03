import logging
from typing import Any

import stripe

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


async def setup_stripe_products() -> None:
    """Setup default Stripe products and prices."""
    try:
        logger.info("Setting up Stripe products and prices...")

        # Define products to create
        products_to_create = [
            {
                "name": "Adult Hibachi Menu",
                "description": "Full hibachi experience for adults",
                "category": "menu",
                "prices": [
                    {"amount": 4500, "nickname": "Adult Menu - Standard"},  # $45
                    {"amount": 5500, "nickname": "Adult Menu - Premium"},  # $55
                ],
            },
            {
                "name": "Kids Hibachi Menu",
                "description": "Kid-friendly hibachi menu",
                "category": "menu",
                "prices": [
                    {"amount": 2500, "nickname": "Kids Menu"},  # $25
                ],
            },
            {
                "name": "Booking Deposit",
                "description": "Required deposit for booking confirmation",
                "category": "deposit",
                "prices": [
                    {"amount": 10000, "nickname": "Standard Deposit"},  # $100
                    {"amount": 15000, "nickname": "Premium Deposit"},  # $150
                ],
            },
            {
                "name": "Travel Fee",
                "description": "Travel fee per mile",
                "category": "fee",
                "prices": [
                    {"amount": 200, "nickname": "Per Mile"},  # $2 per mile
                ],
            },
            {
                "name": "Protein Upgrade",
                "description": "Premium protein upgrade",
                "category": "addon",
                "prices": [
                    {"amount": 500, "nickname": "Filet Mignon Upgrade"},  # $5
                    {"amount": 800, "nickname": "Lobster Upgrade"},  # $8
                    {"amount": 1000, "nickname": "Wagyu Upgrade"},  # $10
                ],
            },
            {
                "name": "Gratuity",
                "description": "Chef gratuity",
                "category": "gratuity",
                "prices": [
                    {"amount": 1000, "nickname": "Standard Tip 15%"},  # $10 (example)
                    {"amount": 1500, "nickname": "Premium Tip 20%"},  # $15 (example)
                ],
            },
        ]

        created_count = 0

        for product_data in products_to_create:
            # Check if product already exists
            existing_products = stripe.Product.list(limit=100, active=True)

            existing_product = None
            for existing in existing_products.data:
                if existing.name == product_data["name"]:
                    existing_product = existing
                    break

            if existing_product:
                logger.info(f"Product '{product_data['name']}' already exists")
                product = existing_product
            else:
                # Create product
                product = stripe.Product.create(
                    name=product_data["name"],
                    description=product_data["description"],
                    metadata={"category": product_data["category"], "created_by": "setup_script"},
                )
                logger.info(f"Created product: {product.name}")
                created_count += 1

            # Create prices for this product
            for price_data in product_data["prices"]:
                # Check if price already exists
                existing_prices = stripe.Price.list(product=product.id, limit=100, active=True)

                price_exists = False
                for existing_price in existing_prices.data:
                    if (
                        existing_price.unit_amount == price_data["amount"]
                        and existing_price.nickname == price_data["nickname"]
                    ):
                        price_exists = True
                        break

                if not price_exists:
                    price = stripe.Price.create(
                        product=product.id,
                        unit_amount=price_data["amount"],
                        currency="usd",
                        nickname=price_data["nickname"],
                        metadata={"category": product_data["category"]},
                    )
                    logger.info(f"Created price: {price.nickname} - ${price.unit_amount/100}")
                else:
                    logger.info(f"Price '{price_data['nickname']}' already exists")

        # Setup tax settings if enabled
        if settings.enable_automatic_tax:
            await setup_tax_settings()

        logger.info(f"Stripe setup completed. Created {created_count} new products.")

    except Exception as e:
        logger.error(f"Error setting up Stripe products: {e}")
        raise


async def setup_tax_settings() -> None:
    """Setup automatic tax collection."""
    try:
        logger.info("Setting up automatic tax collection...")

        # This would typically involve:
        # 1. Setting up tax registrations
        # 2. Configuring tax rates
        # 3. Enabling automatic tax calculation

        # For now, just log that we would do this
        logger.info("Tax settings configured (placeholder)")

    except Exception as e:
        logger.error(f"Error setting up tax settings: {e}")


def get_default_prices() -> dict[str, str]:
    """Get default price IDs for common items."""
    try:
        # In a real implementation, you'd cache these or store in config
        prices = {}

        # Get all products and their prices
        products = stripe.Product.list(limit=100, active=True)

        for product in products.data:
            product_prices = stripe.Price.list(product=product.id, limit=100, active=True)

            for price in product_prices.data:
                key = f"{product.name}_{price.nickname}".lower().replace(" ", "_")
                prices[key] = price.id

        return prices

    except Exception as e:
        logger.error(f"Error getting default prices: {e}")
        return {}


def create_test_data() -> dict[str, Any]:
    """Create test data for development."""
    if settings.environment != "development":
        logger.warning("Test data creation only available in development")
        return {}

    try:
        logger.info("Creating test data...")

        # Create test customer
        test_customer = stripe.Customer.create(
            email="test@myhibachi.com",
            name="Test Customer",
            description="Test customer for development",
            metadata={"user_id": "test-user-123", "source": "test_data"},
        )

        # Create test payment intent
        test_intent = stripe.PaymentIntent.create(
            amount=10000,  # $100
            currency="usd",
            customer=test_customer.id,
            description="Test booking deposit",
            metadata={
                "booking_id": "test-booking-123",
                "user_id": "test-user-123",
                "payment_type": "deposit",
            },
        )

        logger.info("Test data created successfully")

        return {
            "customer_id": test_customer.id,
            "payment_intent_id": test_intent.id,
            "client_secret": test_intent.client_secret,
        }

    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        return {}
