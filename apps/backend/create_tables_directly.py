"""
Create database tables directly using SQLAlchemy models.
This bypasses Alembic migration issues.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.app.database import Base, engine
from api.app.models import booking_models, stripe_models, core


async def create_all_tables():
    """Create all database tables."""
    print("Creating database tables...")
    print(f"Using database: {engine.url}")
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("[SUCCESS] Successfully created all tables!")
            
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_all_tables())
    print("\n[COMPLETE] Database setup complete!")
