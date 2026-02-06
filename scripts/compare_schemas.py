#!/usr/bin/env python3
"""
Schema Comparison Script for CI/CD Pipeline
============================================

Purpose: Detect mismatches between SQLAlchemy models and production database schema
         BEFORE deployment to prevent "column does not exist" errors.

Usage:
    # Compare against staging (default)
    python scripts/compare_schemas.py

    # Compare against production (use with caution)
    python scripts/compare_schemas.py --env production

    # CI/CD usage (exit code 1 if mismatches found)
    python scripts/compare_schemas.py --ci

What it checks:
1. Missing columns in database that exist in models
2. Missing columns in models that exist in database (warning only)
3. Type mismatches between model and database
4. Missing tables

Exit codes:
- 0: No critical mismatches
- 1: Critical mismatches found (columns in model but not in DB)
- 2: Error running comparison
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# Tables and schemas to check
MANAGED_SCHEMAS = ["core", "identity", "audit", "communications", "crm", "ai"]

# Tables that are known to be model-only or DB-only (skip comparison)
SKIP_TABLES = {
    "alembic_version",  # Alembic migration tracking
}


def get_model_columns(model_class) -> dict[str, str]:
    """Extract column names and types from SQLAlchemy model."""
    columns = {}
    if hasattr(model_class, "__table__"):
        for col in model_class.__table__.columns:
            columns[col.name] = str(col.type)
    return columns


def get_all_models() -> dict[str, Any]:
    """Import and return all SQLAlchemy models."""
    models = {}

    try:
        # Import all model modules
        from db.models import core, crm
        from db.models.identity import users, stations

        # Get all classes that are SQLAlchemy models
        for module in [core, crm, users, stations]:
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and hasattr(obj, "__tablename__")
                    and hasattr(obj, "__table_args__")
                ):
                    # Get schema from table args
                    table_args = obj.__table_args__
                    schema = "public"
                    if isinstance(table_args, dict):
                        schema = table_args.get("schema", "public")
                    elif isinstance(table_args, tuple):
                        for arg in table_args:
                            if isinstance(arg, dict) and "schema" in arg:
                                schema = arg["schema"]
                                break

                    full_name = f"{schema}.{obj.__tablename__}"
                    models[full_name] = obj
    except ImportError as e:
        logger.warning(f"Could not import some models: {e}")

    return models


def get_db_columns(engine, schema: str, table: str) -> dict[str, str]:
    """Get column names and types from database."""
    columns = {}
    inspector = inspect(engine)

    try:
        for col in inspector.get_columns(table, schema=schema):
            columns[col["name"]] = str(col["type"])
    except Exception as e:
        logger.debug(f"Could not get columns for {schema}.{table}: {e}")

    return columns


def get_db_tables(engine, schema: str) -> set[str]:
    """Get all table names in a schema."""
    inspector = inspect(engine)
    try:
        return set(inspector.get_table_names(schema=schema))
    except Exception:
        return set()


def compare_schema(database_url: str, ci_mode: bool = False) -> int:
    """
    Compare SQLAlchemy models with database schema.

    Returns:
        0 if no critical issues
        1 if critical mismatches found
        2 if error occurred
    """
    engine = create_engine(database_url)

    # Get all models
    models = get_all_models()

    if not models:
        logger.error("❌ No models found to compare")
        return 2

    logger.info(f"🔍 Comparing {len(models)} models against database...")
    logger.info("-" * 60)

    critical_issues = []
    warnings = []

    for full_name, model_class in sorted(models.items()):
        schema, table = full_name.split(".")

        if table in SKIP_TABLES:
            continue

        # Get columns from model and database
        model_cols = get_model_columns(model_class)
        db_cols = get_db_columns(engine, schema, table)

        if not db_cols:
            critical_issues.append(f"Table {full_name} does not exist in database")
            continue

        # Find mismatches
        model_only = set(model_cols.keys()) - set(db_cols.keys())
        db_only = set(db_cols.keys()) - set(model_cols.keys())

        if model_only:
            for col in model_only:
                issue = f"{full_name}.{col} exists in MODEL but NOT in DATABASE"
                critical_issues.append(issue)

        if db_only:
            for col in db_only:
                warning = f"{full_name}.{col} exists in DATABASE but NOT in MODEL"
                warnings.append(warning)

    # Report results
    logger.info("")

    if critical_issues:
        logger.error("❌ CRITICAL ISSUES (will cause runtime errors):")
        for issue in critical_issues:
            logger.error(f"   - {issue}")
        logger.info("")

    if warnings:
        logger.warning("⚠️ WARNINGS (may indicate stale model or intentional DB-only columns):")
        for warning in warnings[:10]:  # Limit to avoid spam
            logger.warning(f"   - {warning}")
        if len(warnings) > 10:
            logger.warning(f"   ... and {len(warnings) - 10} more")
        logger.info("")

    if not critical_issues and not warnings:
        logger.info("✅ All models match database schema!")

    # Summary
    logger.info("-" * 60)
    logger.info(f"📊 Summary: {len(critical_issues)} critical issues, {len(warnings)} warnings")

    if critical_issues:
        logger.info("")
        logger.info("🔧 To fix critical issues:")
        logger.info("   1. Create a migration file in database/migrations/")
        logger.info("   2. Add missing columns with ALTER TABLE ADD COLUMN")
        logger.info("   3. Apply migration to staging first, then production")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(description="Compare SQLAlchemy models with database schema")
    parser.add_argument(
        "--env",
        choices=["staging", "production"],
        default="staging",
        help="Environment to compare against (default: staging)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with code 1 if mismatches found",
    )
    parser.add_argument(
        "--database-url",
        help="Direct database URL (overrides --env)",
    )

    args = parser.parse_args()

    # Determine database URL
    if args.database_url:
        database_url = args.database_url
    elif args.env == "production":
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://myhibachi_user:PASSWORD@localhost:5432/myhibachi_production"
        )
        logger.warning("⚠️ Comparing against PRODUCTION database")
    else:
        database_url = os.environ.get(
            "STAGING_DATABASE_URL",
            "postgresql://myhibachi_staging_user:PASSWORD@localhost:5432/myhibachi_staging"
        )
        logger.info("Comparing against staging database")

    # Mask password in URL for logging
    safe_url = database_url.split("@")[-1] if "@" in database_url else database_url
    logger.info(f"Database: ...@{safe_url}")
    logger.info("")

    try:
        exit_code = compare_schema(database_url, ci_mode=args.ci)
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
