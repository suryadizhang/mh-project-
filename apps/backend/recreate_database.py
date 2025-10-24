"""
Recreate database tables using unified Base.

This script drops all existing tables and recreates them using the unified
Base.metadata.create_all() to ensure perfect alignment between ORM models
and database schema.

WARNING: This will DELETE ALL DATA in the database!
"""
import asyncio
from sqlalchemy import text
from api.app.database import engine
from api.app.models import Base

# Import all models to register them with Base.metadata
# (models/__init__.py no longer auto-imports to avoid circular imports)
from api.app.auth.station_models import Station, StationUser, StationStatus, StationRole
from api.app.auth.models import User as IdentityUser, UserSession, AuditLog, PasswordResetToken
from api.app.models.booking_models import (
    AddonItem, LegacyBooking, BookingAddon, BookingAvailability, BookingMenuItem, 
    BookingStatus, MenuItem, PreferredCommunication, TimeSlotConfiguration, 
    TimeSlotEnum, LegacyUser, UserRole
)
from api.app.models.stripe_models import (
    StripeCustomer, Dispute, Invoice, StripePayment, Price, Product, Refund, WebhookEvent
)
from api.app.models.core import Customer as CoreCustomer, Booking as CoreBooking, Payment as CorePayment, MessageThread, Message, Event
from api.app.models.events import DomainEvent, OutboxEntry, Snapshot, ProjectionPosition, IdempotencyKey
from api.app.models.lead_newsletter import (
    Lead, LeadContact, LeadContext, LeadEvent, SocialThread,
    Subscriber, Campaign, CampaignEvent
)

async def recreate_database():
    """Drop all tables and recreate from unified Base."""
    
    print("=" * 80)
    print("DATABASE RECREATION SCRIPT")
    print("=" * 80)
    print("\n⚠️  WARNING: This will DELETE ALL DATA!")
    print("\nSchemas to be managed:")
    print("  - core (bookings, customers, payments, messages)")
    print("  - identity (stations, station_users, users)")
    print("  - public (legacy tables)")
    print("  - lead (leads, lead_contacts)")
    print("  - newsletter (subscribers, campaigns)")
    print("  - events (domain_events)")
    
    # Get all table names from unified Base
    all_tables = list(Base.metadata.tables.keys())
    print(f"\n📋 Total tables in unified Base: {len(all_tables)}")
    
    async with engine.begin() as conn:
        # Create all schemas first
        print("\n[STEP 1] Creating schemas...")
        schemas = ["core", "identity", "public", "lead", "newsletter", "events"]
        for schema in schemas:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            await conn.execute(text(f"GRANT ALL ON SCHEMA {schema} TO PUBLIC"))
            print(f"  ✅ {schema}")
        
        # Drop all tables in reverse order (to handle FK dependencies)
        print("\n[STEP 2] Dropping existing tables...")
        print("  (Using CASCADE to handle foreign key dependencies)")
        
        # Drop tables by schema (skip public - system owned)
        for schema in schemas:
            if schema == "public":
                # Can't drop public schema, drop tables individually
                result = await conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT LIKE 'pg_%' 
                    AND tablename NOT LIKE 'sql_%'
                """))
                public_tables = [row[0] for row in result]
                for table in public_tables:
                    await conn.execute(text(f"DROP TABLE IF EXISTS public.{table} CASCADE"))
                print(f"  ✅ Dropped {len(public_tables)} tables from public schema")
            else:
                await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                await conn.execute(text(f"GRANT ALL ON SCHEMA {schema} TO PUBLIC"))
                print(f"  ✅ Dropped and recreated {schema} schema")
        
        print("\n[STEP 3] Creating tables from unified Base...")
        
    # Create all tables using Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"  ✅ Created {len(all_tables)} tables")
    
    # Verify tables were created
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname IN ('core', 'identity', 'public', 'lead', 'newsletter', 'events')
            ORDER BY schemaname, tablename
        """))
        tables = result.fetchall()
        
        print("\n[VERIFICATION] Tables created:")
        current_schema = None
        for schema, table in tables:
            if schema != current_schema:
                print(f"\n  📁 {schema}:")
                current_schema = schema
            print(f"     - {table}")
    
    print("\n" + "=" * 80)
    print("✅ DATABASE RECREATION COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Seed initial data (stations, users)")
    print("  2. Run tests: pytest tests/test_api_performance.py -v")
    print("  3. Verify API endpoints are working")

if __name__ == "__main__":
    print("\n⚠️  This script will DELETE ALL DATA in the database!")
    response = input("\nType 'YES' to continue: ")
    if response == "YES":
        asyncio.run(recreate_database())
    else:
        print("\n❌ Operation cancelled")
