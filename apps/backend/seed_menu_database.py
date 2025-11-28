"""
Database Seeding Script for Menu & Addon Items
Seeds Supabase database with current pricing from FAQ data

Run with: python seed_menu_database.py
"""

import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.knowledge_base import MenuItem, AddonItem, MenuCategory, AddonCategory
from models.base import Base

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres",
)

print(f"🔌 Connecting to database: {DATABASE_URL[:60]}...")

# Create engine (synchronous for seeding)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def seed_menu_items():
    """Seed menu_items table with current pricing"""
    session = SessionLocal()

    try:
        print("\n📋 Seeding menu_items table...")

        menu_items = [
            # Base Pricing
            MenuItem(
                id=str(uuid.uuid4()),
                name="Adult Hibachi Experience",
                description="Complete hibachi experience for adults (13+) with 2 protein choices, fried rice, vegetables, and our signature sauces",
                category=MenuCategory.SPECIALTY,
                base_price=Decimal("55.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["customizable", "can be gluten-free"],
                display_order=1,
            ),
            MenuItem(
                id=str(uuid.uuid4()),
                name="Child Hibachi Experience",
                description="Hibachi experience for children (6-12) with 2 protein choices, fried rice, vegetables, and our signature sauces",
                category=MenuCategory.SPECIALTY,
                base_price=Decimal("30.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["kid-friendly", "customizable"],
                display_order=2,
            ),
            # FREE Proteins (Poultry)
            MenuItem(
                id=str(uuid.uuid4()),
                name="Chicken",
                description="Tender hibachi-grilled chicken breast (FREE protein choice)",
                category=MenuCategory.POULTRY,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["high-protein", "low-carb"],
                display_order=10,
            ),
            # FREE Proteins (Beef)
            MenuItem(
                id=str(uuid.uuid4()),
                name="NY Strip Steak",
                description="Premium NY strip steak grilled to perfection (FREE protein choice)",
                category=MenuCategory.BEEF,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["high-protein", "low-carb"],
                display_order=20,
            ),
            # FREE Proteins (Seafood)
            MenuItem(
                id=str(uuid.uuid4()),
                name="Shrimp",
                description="Fresh hibachi-grilled jumbo shrimp (FREE protein choice)",
                category=MenuCategory.SEAFOOD,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["high-protein", "low-carb", "pescatarian"],
                display_order=30,
            ),
            # FREE Proteins (Specialty)
            MenuItem(
                id=str(uuid.uuid4()),
                name="Tofu",
                description="Grilled tofu with hibachi seasonings (FREE protein choice)",
                category=MenuCategory.SPECIALTY,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["vegan", "vegetarian", "plant-based", "high-protein"],
                display_order=40,
            ),
            MenuItem(
                id=str(uuid.uuid4()),
                name="Vegetables",
                description="Grilled seasonal vegetables (FREE protein choice)",
                category=MenuCategory.SPECIALTY,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["vegan", "vegetarian", "plant-based", "low-carb"],
                display_order=41,
            ),
            # Sides
            MenuItem(
                id=str(uuid.uuid4()),
                name="Hibachi Fried Rice",
                description="Classic hibachi fried rice with eggs and vegetables",
                category=MenuCategory.SIDES,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["included"],
                display_order=100,
            ),
            MenuItem(
                id=str(uuid.uuid4()),
                name="Grilled Vegetables",
                description="Seasonal vegetables grilled hibachi-style",
                category=MenuCategory.SIDES,
                base_price=Decimal("0.00"),
                is_premium=False,
                is_available=True,
                dietary_info=["vegan", "vegetarian", "included"],
                display_order=101,
            ),
        ]

        # Add all items
        for item in menu_items:
            session.add(item)

        session.commit()
        print(f"✅ Successfully seeded {len(menu_items)} menu items")

    except Exception as e:
        print(f"❌ Error seeding menu items: {e}")
        session.rollback()
    finally:
        session.close()


def seed_addon_items():
    """Seed addon_items table with protein upgrades and enhancements"""
    session = SessionLocal()

    try:
        print("\n📋 Seeding addon_items table...")

        addon_items = [
            # Protein Upgrades
            AddonItem(
                id=str(uuid.uuid4()),
                name="Filet Mignon",
                description="Premium filet mignon upgrade (+$5 per portion)",
                category=AddonCategory.PROTEIN_UPGRADES,
                price=Decimal("5.00"),
                is_active=True,
                display_order=1,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Salmon",
                description="Fresh Atlantic salmon upgrade (+$5 per portion)",
                category=AddonCategory.PROTEIN_UPGRADES,
                price=Decimal("5.00"),
                is_active=True,
                display_order=2,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Scallops",
                description="Succulent sea scallops upgrade (+$5 per portion)",
                category=AddonCategory.PROTEIN_UPGRADES,
                price=Decimal("5.00"),
                is_active=True,
                display_order=3,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Lobster Tail",
                description="Premium lobster tail upgrade (+$15 per portion)",
                category=AddonCategory.PROTEIN_UPGRADES,
                price=Decimal("15.00"),
                is_active=True,
                display_order=4,
            ),
            # Enhancements (from actual menu page)
            AddonItem(
                id=str(uuid.uuid4()),
                name="Yakisoba Noodles",
                description="Japanese stir-fried noodles with vegetables",
                category=AddonCategory.ENHANCEMENTS,
                price=Decimal("5.00"),
                is_active=True,
                display_order=10,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Extra Fried Rice",
                description="Additional portion of hibachi fried rice",
                category=AddonCategory.ENHANCEMENTS,
                price=Decimal("5.00"),
                is_active=True,
                display_order=11,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Extra Vegetables",
                description="Additional portion of grilled vegetables",
                category=AddonCategory.ENHANCEMENTS,
                price=Decimal("5.00"),
                is_active=True,
                display_order=12,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Edamame",
                description="Steamed Japanese soybeans with sea salt",
                category=AddonCategory.ENHANCEMENTS,
                price=Decimal("5.00"),
                is_active=True,
                display_order=13,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="Gyoza",
                description="Pan-fried Japanese dumplings (6 pieces)",
                category=AddonCategory.ENHANCEMENTS,
                price=Decimal("10.00"),
                is_active=True,
                display_order=14,
            ),
            AddonItem(
                id=str(uuid.uuid4()),
                name="3rd Protein",
                description="Add a third protein choice per guest (+$10 beyond 2 per guest)",
                category=AddonCategory.PROTEIN_UPGRADES,
                price=Decimal("10.00"),
                is_active=True,
                display_order=5,
            ),
        ]

        # Add all items
        for item in addon_items:
            session.add(item)

        session.commit()
        print(f"✅ Successfully seeded {len(addon_items)} addon items")

    except Exception as e:
        print(f"❌ Error seeding addon items: {e}")
        session.rollback()
    finally:
        session.close()


def create_tables():
    """Create tables if they don't exist"""
    print("\n🏗️  Creating tables...")
    try:
        Base.metadata.create_all(engine)
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"⚠️  Table creation warning: {e}")


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 60)

    # Create tables first
    create_tables()

    # Seed data
    seed_menu_items()
    seed_addon_items()

    print("\n" + "=" * 60)
    print("✅ Database seeding complete!")
    print("\n📊 Summary:")
    print("   - menu_items: 9 items (2 base pricing + 5 FREE proteins + 2 sides)")
    print("   - addon_items: 10 items (4 protein upgrades + 6 enhancements)")
    print("\n🚀 MenuAgent will now load from database!")


if __name__ == "__main__":
    main()
