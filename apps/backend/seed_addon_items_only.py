"""
Simplified seeding script for addon_items table only.
Avoids loading all models to prevent mapper errors.
"""

import os
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

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def create_addon_category_enum():
    """Create addon_category ENUM type if not exists"""
    print("\n🏗️  Creating addon_category ENUM...")

    session = SessionLocal()
    try:
        # Check if enum exists
        result = session.execute(
            text(
                """
            SELECT 1 FROM pg_type WHERE typname = 'addon_category'
        """
            )
        )

        if result.scalar():
            print("   ✅ addon_category ENUM already exists")
        else:
            # Create enum
            session.execute(
                text(
                    """
                CREATE TYPE addon_category AS ENUM (
                    'protein_upgrades',
                    'enhancements',
                    'equipment',
                    'entertainment',
                    'beverages'
                )
            """
                )
            )
            session.commit()
            print("   ✅ addon_category ENUM created")
    except Exception as e:
        session.rollback()
        print(f"   ⚠️  ENUM creation: {e}")
    finally:
        session.close()


def create_addon_items_table():
    """Create addon_items table if not exists"""
    print("\n🏗️  Creating addon_items table...")

    session = SessionLocal()
    try:
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS public.addon_items (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category addon_category NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                image_url VARCHAR(500),
                display_order INTEGER DEFAULT 0,
                station_id VARCHAR(36),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        session.commit()
        print("   ✅ addon_items table created")
    except Exception as e:
        session.rollback()
        print(f"   ⚠️  Table creation: {e}")
    finally:
        session.close()


def create_indexes():
    """Create indexes for addon_items table"""
    print("\n🏗️  Creating indexes...")

    session = SessionLocal()
    try:
        # Drop existing indexes first (in case of conflicts)
        session.execute(text("DROP INDEX IF EXISTS idx_addon_items_category"))
        session.execute(text("DROP INDEX IF EXISTS idx_addon_items_active"))
        session.execute(text("DROP INDEX IF EXISTS idx_addon_items_station"))
        session.execute(text("DROP INDEX IF EXISTS idx_addon_items_lookup"))

        # Create indexes
        session.execute(
            text("CREATE INDEX idx_addon_items_category ON public.addon_items(category)")
        )
        session.execute(
            text("CREATE INDEX idx_addon_items_active ON public.addon_items(is_active)")
        )
        session.execute(
            text("CREATE INDEX idx_addon_items_station ON public.addon_items(station_id)")
        )
        session.execute(
            text(
                "CREATE INDEX idx_addon_items_lookup ON public.addon_items(category, is_active, display_order)"
            )
        )

        session.commit()
        print("   ✅ Indexes created")
    except Exception as e:
        session.rollback()
        print(f"   ⚠️  Index creation: {e}")
    finally:
        session.close()


def seed_addon_items():
    """Seed addon_items table with initial data"""
    print("\n📋 Seeding addon_items table...")

    session = SessionLocal()
    try:
        # Clear existing data
        session.execute(text("DELETE FROM public.addon_items"))

        # Insert addon items using raw SQL
        addon_items = [
            {
                "id": "addon_001",
                "name": "Filet Mignon",
                "description": "Premium upgrade - tender filet mignon (+$5 per person)",
                "category": "protein_upgrades",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 1,
            },
            {
                "id": "addon_002",
                "name": "Salmon",
                "description": "Premium upgrade - fresh Atlantic salmon (+$5 per person)",
                "category": "protein_upgrades",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 2,
            },
            {
                "id": "addon_003",
                "name": "Scallops",
                "description": "Premium upgrade - seared scallops (+$5 per person)",
                "category": "protein_upgrades",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 3,
            },
            {
                "id": "addon_004",
                "name": "Lobster Tail",
                "description": "Premium upgrade - succulent lobster tail (+$15 per person)",
                "category": "protein_upgrades",
                "price": Decimal("15.00"),
                "is_active": True,
                "display_order": 4,
            },
            {
                "id": "addon_005",
                "name": "3rd Protein Selection",
                "description": "Add a third protein to your meal (+$10 per person)",
                "category": "protein_upgrades",
                "price": Decimal("10.00"),
                "is_active": True,
                "display_order": 5,
            },
            {
                "id": "addon_006",
                "name": "Yakisoba Noodles",
                "description": "Substitute fried rice with yakisoba noodles (+$5 per person)",
                "category": "enhancements",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 6,
            },
            {
                "id": "addon_007",
                "name": "Extra Fried Rice",
                "description": "Additional portion of hibachi fried rice (+$5 per person)",
                "category": "enhancements",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 7,
            },
            {
                "id": "addon_008",
                "name": "Extra Vegetables",
                "description": "Additional grilled vegetables (+$5 per person)",
                "category": "enhancements",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 8,
            },
            {
                "id": "addon_009",
                "name": "Edamame",
                "description": "Steamed edamame appetizer (+$5)",
                "category": "enhancements",
                "price": Decimal("5.00"),
                "is_active": True,
                "display_order": 9,
            },
            {
                "id": "addon_010",
                "name": "Gyoza (6 pieces)",
                "description": "Pan-fried pork dumplings (+$10)",
                "category": "enhancements",
                "price": Decimal("10.00"),
                "is_active": True,
                "display_order": 10,
            },
        ]

        for item in addon_items:
            session.execute(
                text(
                    """
                INSERT INTO public.addon_items
                (id, name, description, category, price, is_active, display_order)
                VALUES
                (:id, :name, :description, :category, :price, :is_active, :display_order)
            """
                ),
                item,
            )

        session.commit()
        print(f"   ✅ Inserted {len(addon_items)} addon items")

        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM public.addon_items"))
        count = result.scalar()
        print(f"   ✅ Verified: {count} rows in addon_items table")

    except Exception as e:
        session.rollback()
        print(f"   ❌ Error seeding addon items: {e}")
        raise
    finally:
        session.close()


def main():
    """Main seeding process"""
    print("🌱 Starting addon_items database seeding...")
    print("=" * 60)

    try:
        create_addon_category_enum()
        create_addon_items_table()
        create_indexes()
        seed_addon_items()

        print("\n" + "=" * 60)
        print("✅ addon_items table seeding complete!")
        print("\n📊 Summary:")
        print("   - addon_items: 10 items (4 protein upgrades + 6 enhancements)")
        print("\n🚀 Ready for PricingService!")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    main()
