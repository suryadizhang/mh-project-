#!/usr/bin/env python3
"""Simple production deployment verification script."""

import sys


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking Python dependencies...")

    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'alembic',
        'psycopg2',
        'asyncpg',
        'jose',
        'passlib',
        'slowapi',
        'google.auth',
        'google.cloud.pubsub',
        'openai',
        'jwt'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package} - {e}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required dependencies are installed!")
        return True


def check_database():
    """Test database connectivity."""
    print("\n🔍 Testing database connectivity...")

    try:
        import asyncio

        from sqlalchemy import text

        from app.database import get_db_context

        async def test_db():
            async with get_db_context() as db:
                result = await db.execute(text("SELECT version()"))
                version = result.scalar()
                print("  ✅ PostgreSQL connection successful")
                print(f"  📊 Version: {version}")

                # Check schemas
                result = await db.execute(text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name IN ('core', 'events', 'read', 'integra')
                    ORDER BY schema_name
                """))
                schemas = [row[0] for row in result.fetchall()]
                print(f"  📋 Schemas: {', '.join(schemas)}")

                return True

        return asyncio.run(test_db())

    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False


def check_environment():
    """Check environment configuration."""
    print("\n🔍 Checking environment configuration...")

    try:
        from app.config import settings
        print(f"  ✅ Environment: {settings.environment}")
        print(f"  ✅ Debug mode: {settings.debug}")
        print(f"  ✅ Database URL configured: {'postgresql' in settings.database_url}")

        # Check API keys are configured (placeholder check)
        env_vars = [
            'META_APP_SECRET',
            'GOOGLE_SERVICE_ACCOUNT_KEY',
            'YELP_API_KEY',
            'OPENAI_API_KEY'
        ]

        import os
        configured_keys = []
        placeholder_keys = []

        for var in env_vars:
            value = os.getenv(var, '')
            if value and 'your_' not in value.lower() and 'placeholder' not in value.lower():
                configured_keys.append(var)
            else:
                placeholder_keys.append(var)

        if configured_keys:
            print(f"  ✅ Configured API keys: {', '.join(configured_keys)}")

        if placeholder_keys:
            print(f"  ⚠️  Placeholder API keys: {', '.join(placeholder_keys)}")

        return True

    except Exception as e:
        print(f"  ❌ Environment check failed: {e}")
        return False


def main():
    """Run all production deployment checks."""
    print("🚀 My Hibachi Production Deployment Verification")
    print("=" * 50)

    checks_passed = 0
    total_checks = 3

    # Check dependencies
    if check_dependencies():
        checks_passed += 1

    # Check database
    if check_database():
        checks_passed += 1

    # Check environment
    if check_environment():
        checks_passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Deployment Readiness: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("🎉 System is ready for production deployment!")
        print("\n📋 Next steps:")
        print("  1. Configure production API keys in environment variables")
        print("  2. Set up webhook endpoints with SSL certificates")
        print("  3. Register webhooks with social media platforms")
        print("  4. Start the application: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(0)
    else:
        print("⚠️  System needs configuration before production deployment")
        print("See PRODUCTION_DEPLOYMENT_GUIDE.md for detailed instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
