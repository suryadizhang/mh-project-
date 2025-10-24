"""Create tables for core and identity schemas based on models."""
import asyncio
from sqlalchemy import text
from api.app.database import engine
from api.app.models.core import Base as CoreBase

async def setup_schemas():
    """Create necessary schemas and tables."""
    async with engine.begin() as conn:
        # Create schemas
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
        await conn.execute(text("GRANT ALL ON SCHEMA core TO PUBLIC"))
        await conn.execute(text("GRANT ALL ON SCHEMA identity TO PUBLIC"))
        
        # Drop existing core tables if they exist (to recreate with correct schema)
        await conn.execute(text("DROP TABLE IF EXISTS core.payments CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS core.bookings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS core.customers CASCADE"))
        
        # Create identity.stations table (minimal version for FK constraints)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS identity.stations (
                id UUID PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL UNIQUE,
                display_name VARCHAR(200) NOT NULL,
                timezone VARCHAR(50) NOT NULL DEFAULT 'America/New_York',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        print("✅ Schemas and stations table created")
        
    # Now create core tables using SQLAlchemy models
    async with engine.begin() as conn:
        await conn.run_sync(CoreBase.metadata.create_all)
        print("✅ Core tables created from models")
    
    print("\n[SUCCESS] Database schema setup complete!")

if __name__ == "__main__":
    asyncio.run(setup_schemas())
