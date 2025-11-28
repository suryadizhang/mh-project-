"""
Simplified seeding script for menu_items table only.
Avoids loading all models to prevent mapper errors.
"""

import os
import uuid
from decimal import Decimal
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database connection (synchronous)
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)
print(f"🔌 Connecting to database: {DATABASE_URL[:60]}...")

engine = create_engine(DATABASE_URL, echo=False)  # Disable echo for cleaner output
SessionLocal = sessionmaker(bind=engine)


def seed_menu_items():
    """Seed menu_items table with initial data"""
    print("\n📋 Seeding menu_items table...")

    session = SessionLocal()
    try:
        # Clear existing data
        session.execute(text("DELETE FROM public.menu_items"))

        # Insert menu items using raw SQL
        menu_items = [
            # Base pricing (2 items)
            {
                "id": str(uuid.uuid4()),
                "name": "Adult Hibachi Experience",
                "description": "Complete hibachi experience for adults (13+). Includes 2 proteins, hibachi fried rice, grilled vegetables, and chef show.",
                "category": "specialty",
                "base_price": Decimal("55.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["customizable", "can be gluten-free"],
                "display_order": 1,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Child Hibachi Experience",
                "description": "Complete hibachi experience for children (12 and under). Includes 1 protein, hibachi fried rice, grilled vegetables, and chef show.",
                "category": "specialty",
                "base_price": Decimal("30.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["customizable", "kid-friendly"],
                "display_order": 2,
            },
            # FREE proteins (5 items)
            {
                "id": str(uuid.uuid4()),
                "name": "Chicken",
                "description": "Tender grilled chicken breast",
                "category": "poultry",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["gluten-free", "high-protein"],
                "display_order": 3,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "NY Strip Steak",
                "description": "Premium NY Strip steak",
                "category": "beef",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["gluten-free", "high-protein"],
                "display_order": 4,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Shrimp",
                "description": "Fresh grilled shrimp",
                "category": "seafood",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["gluten-free", "high-protein", "seafood"],
                "display_order": 5,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Tofu",
                "description": "Grilled tofu (vegetarian option)",
                "category": "specialty",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["vegetarian", "vegan", "gluten-free", "high-protein"],
                "display_order": 6,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Vegetables",
                "description": "Assorted grilled vegetables (vegan option)",
                "category": "specialty",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["vegetarian", "vegan", "gluten-free"],
                "display_order": 7,
            },
            # Included sides (2 items)
            {
                "id": str(uuid.uuid4()),
                "name": "Hibachi Fried Rice",
                "description": "Classic hibachi-style fried rice (included with meal)",
                "category": "sides",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["vegetarian"],
                "display_order": 8,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Grilled Vegetables",
                "description": "Mixed grilled vegetables (included with meal)",
                "category": "sides",
                "base_price": Decimal("0.00"),
                "is_premium": False,
                "is_available": True,
                "dietary_info": ["vegetarian", "vegan", "gluten-free"],
                "display_order": 9,
            },
        ]

        for item in menu_items:
            session.execute(
                text(
                    """
                INSERT INTO public.menu_items
                (id, name, description, category, base_price, is_premium, is_available, dietary_info, display_order)
                VALUES
                (:id, :name, :description, :category, :base_price, :is_premium, :is_available, :dietary_info, :display_order)
            """
                ),
                item,
            )

        session.commit()
        print(f"   ✅ Inserted {len(menu_items)} menu items")

        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM public.menu_items"))
        count = result.scalar()
        print(f"   ✅ Verified: {count} rows in menu_items table")

        # Show breakdown
        print("\n   📊 Menu breakdown:")
        print("      - Base pricing: 2 items (Adult $55, Child $30)")
        print("      - FREE proteins: 5 items (Chicken, Steak, Shrimp, Tofu, Vegetables)")
        print("      - Included sides: 2 items (Fried Rice, Grilled Vegetables)")

    except Exception as e:
        session.rollback()
        print(f"   ❌ Error seeding menu items: {e}")
        raise
    finally:
        session.close()


def main():
    """Main seeding process"""
    print("🌱 Starting menu_items database seeding...")
    print("=" * 60)

    try:
        seed_menu_items()

        print("\n" + "=" * 60)
        print("✅ menu_items table seeding complete!")
        print("\n🚀 MenuAgent will now load from database!")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    main()
