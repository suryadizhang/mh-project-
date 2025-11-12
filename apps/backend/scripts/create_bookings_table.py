#!/usr/bin/env python3
"""
Create bookings table for availability checking
This is a mock/development table that will be replaced with real data in production
"""
import asyncio
import asyncpg
from datetime import date, time


async def create_bookings_table():
    """Create bookings table for AI availability checks"""

    conn = await asyncpg.connect(
        "postgresql://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres"
    )

    try:
        print("\n📅 Creating bookings table for availability checks...")

        # Check if table exists in public schema
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'bookings'
            )
        """
        )

        if table_exists:
            print("   ℹ️  Table 'bookings' exists")

            try:
                # Check if it has data
                count = await conn.fetchval("SELECT COUNT(*) FROM public.bookings")
                print(f"   📊 Current bookings: {count}")

                if count == 0:
                    print("   📝 Table empty, adding mock bookings...")
                    # Continue to add mock data (skip table creation)
                    pass  # Will fall through to mock data section
                else:
                    print("   ✅ Table already has data")
                    return
            except Exception as e:
                print(f"   ⚠️  Error accessing table: {e}")
                print("   🔄 Attempting to recreate table...")
                await conn.execute("DROP TABLE IF EXISTS public.bookings CASCADE")
                table_exists = False

        # Create bookings table in public schema (only if doesn't exist)
        if not table_exists:
            await conn.execute(
                """
                CREATE TABLE public.bookings (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                customer_name VARCHAR(255) NOT NULL,
                customer_email VARCHAR(255),
                customer_phone VARCHAR(50),
                
                event_date DATE NOT NULL,
                event_time TIME NOT NULL,
                event_address TEXT NOT NULL,
                
                guest_count INTEGER NOT NULL,
                adult_count INTEGER,
                child_count INTEGER,
                
                proteins JSONB,  -- Array of selected proteins
                add_ons JSONB,   -- Array of selected add-ons
                
                subtotal DECIMAL(10, 2),
                travel_fee DECIMAL(10, 2) DEFAULT 0,
                total_amount DECIMAL(10, 2) NOT NULL,
                
                deposit_amount DECIMAL(10, 2) DEFAULT 100,
                deposit_paid BOOLEAN DEFAULT FALSE,
                balance_paid BOOLEAN DEFAULT FALSE,
                
                status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, completed, cancelled
                
                chef_assigned VARCHAR(255),
                special_requests TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT valid_guest_count CHECK (guest_count > 0),
                CONSTRAINT valid_amounts CHECK (total_amount >= 550)  -- Minimum order
            )
        """
            )

            # Create indexes for availability queries
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_event_date 
                ON public.bookings(event_date)
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_status 
                ON public.bookings(status)
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_date_status 
                ON public.bookings(event_date, status)
            """
            )

            print("   ✅ Created 'bookings' table with indexes")

        # Add some mock data for testing
        print("\n📝 Adding mock bookings for testing...")

        mock_bookings = [
            # Past booking
            (
                date(2025, 11, 1),
                time(18, 0),
                "John Smith",
                "john@example.com",
                "(916) 555-0101",
                "123 Main St, Sacramento, CA",
                25,
                20,
                5,
                2750.00,
                "confirmed",
            ),
            # Upcoming bookings
            (
                date(2025, 11, 15),
                time(19, 0),
                "Sarah Johnson",
                "sarah@example.com",
                "(916) 555-0102",
                "456 Oak Ave, Sacramento, CA",
                30,
                25,
                5,
                3250.00,
                "confirmed",
            ),
            (
                date(2025, 11, 20),
                time(18, 30),
                "Mike Davis",
                "mike@example.com",
                "(916) 555-0103",
                "789 Pine Rd, Folsom, CA",
                15,
                12,
                3,
                1650.00,
                "confirmed",
            ),
            (
                date(2025, 12, 1),
                time(17, 0),
                "Lisa Anderson",
                "lisa@example.com",
                "(916) 555-0104",
                "321 Elm St, Roseville, CA",
                50,
                45,
                5,
                5500.00,
                "pending",
            ),
            # Holiday season bookings
            (
                date(2025, 12, 15),
                time(19, 0),
                "Corporate Event - TechCo",
                "events@techco.com",
                "(916) 555-0105",
                "555 Business Park Dr, Sacramento, CA",
                60,
                60,
                0,
                6600.00,
                "confirmed",
            ),
            (
                date(2025, 12, 31),
                time(20, 0),
                "New Year's Eve Party",
                "party@example.com",
                "(916) 555-0106",
                "999 Celebration Ln, Sacramento, CA",
                40,
                35,
                5,
                4400.00,
                "pending",
            ),
        ]

        for (
            event_date,
            event_time,
            name,
            email,
            phone,
            address,
            guests,
            adults,
            children,
            total,
            status,
        ) in mock_bookings:
            await conn.execute(
                """
                INSERT INTO public.bookings (
                    event_date, event_time, customer_name, customer_email, customer_phone,
                    event_address, guest_count, adult_count, child_count,
                    total_amount, status, deposit_paid
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true)
            """,
                event_date,
                event_time,
                name,
                email,
                phone,
                address,
                guests,
                adults,
                children,
                total,
                status,
            )

        count = await conn.fetchval("SELECT COUNT(*) FROM public.bookings")
        print(f"   ✅ Added {count} mock bookings for testing")

        print("\n" + "=" * 60)
        print("✅ Bookings table ready for AI availability checks!")
        print("=" * 60)
        print("\n⚠️  PRODUCTION NOTE:")
        print("   When deploying to production, clear mock data:")
        print("   DELETE FROM bookings WHERE customer_email LIKE '%example.com';")
        print("   Then populate with real booking data from your booking system.")
        print("=" * 60)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_bookings_table())
