#!/usr/bin/env python3
"""Test database connectivity for My Hibachi API."""

import asyncio

from sqlalchemy import text

from app.database import get_db_context


async def test_database_connection():
    """Test the database connection."""
    try:
        async with get_db_context() as db:
            # Test basic connectivity
            result = await db.execute(text("SELECT version()"))
            version = result.scalar()
            print("✅ Database connection successful!")
            print(f"📊 PostgreSQL version: {version}")

            # Test schema access
            result = await db.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('core', 'events', 'read', 'integra')
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result.fetchall()]
            print(f"📋 Available schemas: {', '.join(schemas)}")

            # Test table count per schema
            for schema in schemas:
                result = await db.execute(text(f"""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                """))
                count = result.scalar()
                print(f"📊 {schema} schema: {count} tables")

            # Test social media tables specifically
            result = await db.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'core'
                AND table_name LIKE 'social_%'
                ORDER BY table_name
            """))
            social_tables = [row[0] for row in result.fetchall()]
            print(f"🔗 Social media tables: {', '.join(social_tables)}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_database_connection())
