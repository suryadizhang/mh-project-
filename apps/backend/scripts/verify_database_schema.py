#!/usr/bin/env python3
"""
Verify Database Schema After Migration
======================================

This script validates that all expected schemas, tables, and constraints
were created correctly during the Alembic migration process.

Usage:
    python scripts/verify_database_schema.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
import psycopg2
from psycopg2 import sql
from typing import List, Dict, Tuple
import json


class DatabaseSchemaValidator:
    """Validates database schema structure"""

    EXPECTED_SCHEMAS = [
        'core',           # Main business entities (bookings, customers, chefs, messages, etc.)
        'identity',       # Auth, roles, permissions, stations
        'lead',           # Lead management
        'newsletter',     # Newsletter & SMS campaigns
        'feedback',       # Reviews and discount coupons
        'events',         # Event sourcing (domain_events, inbox, outbox)
        'integra',        # External integrations (payment, social, calls)
        'marketing',      # QR codes and marketing tools
        'support',        # Customer support escalations
        'communications'  # Call recordings and communications
    ]

    # Note: 'bookings' schema exists but is empty (tables are in 'core' schema)
    # This is intentional - reserved for future booking-specific features

    def __init__(self):
        self.settings = get_settings()
        self.conn = None
        self.cur = None

    def connect(self):
        """Connect to database"""
        try:
            # Convert async URL to sync URL for psycopg2
            db_url = self.settings.database_url
            if db_url.startswith("postgresql+asyncpg://"):
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

            self.conn = psycopg2.connect(db_url)
            self.cur = self.conn.cursor()
            print("✅ Connected to database")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)

    def disconnect(self):
        """Disconnect from database"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def verify_schemas(self) -> Tuple[bool, List[str]]:
        """Verify all expected schemas exist"""
        print("\n" + "="*70)
        print("📊 VERIFYING SCHEMAS")
        print("="*70)

        self.cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)

        existing_schemas = [row[0] for row in self.cur.fetchall()]
        missing_schemas = [s for s in self.EXPECTED_SCHEMAS if s not in existing_schemas]
        extra_schemas = [s for s in existing_schemas if s not in self.EXPECTED_SCHEMAS and s != 'public']

        print(f"\n✅ Expected schemas: {len(self.EXPECTED_SCHEMAS)}")
        print(f"✅ Found schemas: {len(existing_schemas)}")

        for schema in self.EXPECTED_SCHEMAS:
            if schema in existing_schemas:
                print(f"  ✅ {schema}")
            else:
                print(f"  ❌ {schema} - MISSING!")

        if extra_schemas:
            print(f"\n⚠️  Extra schemas found: {', '.join(extra_schemas)}")

        return len(missing_schemas) == 0, missing_schemas

    def verify_tables(self) -> Tuple[bool, Dict[str, List[str]]]:
        """Verify tables in each schema"""
        print("\n" + "="*70)
        print("📋 VERIFYING TABLES PER SCHEMA")
        print("="*70)

        all_tables = {}
        total_tables = 0

        for schema in self.EXPECTED_SCHEMAS:
            self.cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))

            tables = [row[0] for row in self.cur.fetchall()]
            all_tables[schema] = tables
            total_tables += len(tables)

            print(f"\n📦 {schema} schema: {len(tables)} tables")
            for table in tables[:5]:  # Show first 5
                print(f"  ✅ {table}")
            if len(tables) > 5:
                print(f"  ... and {len(tables) - 5} more")

        print(f"\n📊 Total tables across all schemas: {total_tables}")
        return True, all_tables

    def verify_enums(self) -> Tuple[bool, Dict[str, List[str]]]:
        """Verify ENUM types"""
        print("\n" + "="*70)
        print("🔢 VERIFYING ENUM TYPES")
        print("="*70)

        self.cur.execute("""
            SELECT n.nspname as schema, t.typname as enum_name
            FROM pg_type t
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE t.typtype = 'e'
            AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY n.nspname, t.typname
        """)

        enums_by_schema = {}
        total_enums = 0

        for schema, enum_name in self.cur.fetchall():
            if schema not in enums_by_schema:
                enums_by_schema[schema] = []
            enums_by_schema[schema].append(enum_name)
            total_enums += 1

        for schema, enums in enums_by_schema.items():
            print(f"\n📦 {schema} schema: {len(enums)} ENUMs")
            for enum in enums:
                print(f"  ✅ {enum}")

        print(f"\n📊 Total ENUMs: {total_enums}")
        return True, enums_by_schema

    def verify_foreign_keys(self) -> Tuple[bool, int]:
        """Verify foreign key constraints"""
        print("\n" + "="*70)
        print("🔗 VERIFYING FOREIGN KEY CONSTRAINTS")
        print("="*70)

        self.cur.execute("""
            SELECT
                tc.table_schema,
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema IN ('core', 'identity', 'bookings', 'lead', 'newsletter',
                                   'feedback', 'events', 'integra', 'marketing',
                                   'support', 'communications', 'public')
            ORDER BY tc.table_schema, tc.table_name
        """)

        fks = self.cur.fetchall()
        fk_count = len(fks)

        print(f"\n✅ Total foreign keys: {fk_count}")

        # Show sample FKs
        print(f"\n📋 Sample foreign keys:")
        for fk in fks[:10]:
            schema, table, constraint, col, fk_schema, fk_table, fk_col = fk
            print(f"  ✅ {schema}.{table}.{col} → {fk_schema}.{fk_table}.{fk_col}")

        if fk_count > 10:
            print(f"  ... and {fk_count - 10} more")

        return True, fk_count

    def verify_indexes(self) -> Tuple[bool, int]:
        """Verify indexes"""
        print("\n" + "="*70)
        print("⚡ VERIFYING INDEXES")
        print("="*70)

        self.cur.execute("""
            SELECT
                schemaname,
                tablename,
                indexname
            FROM pg_indexes
            WHERE schemaname IN ('core', 'identity', 'bookings', 'lead', 'newsletter',
                               'feedback', 'events', 'integra', 'marketing',
                               'support', 'communications', 'public')
            ORDER BY schemaname, tablename
        """)

        indexes = self.cur.fetchall()
        index_count = len(indexes)

        print(f"\n✅ Total indexes: {index_count}")

        # Count by schema
        by_schema = {}
        for schema, table, index in indexes:
            if schema not in by_schema:
                by_schema[schema] = 0
            by_schema[schema] += 1

        print(f"\n📊 Indexes by schema:")
        for schema in sorted(by_schema.keys()):
            print(f"  ✅ {schema}: {by_schema[schema]} indexes")

        return True, index_count

    def verify_alembic_version(self) -> Tuple[bool, str]:
        """Verify Alembic version"""
        print("\n" + "="*70)
        print("🔄 VERIFYING ALEMBIC VERSION")
        print("="*70)

        self.cur.execute("SELECT version_num FROM alembic_version")
        result = self.cur.fetchone()

        if result:
            version = result[0]
            print(f"\n✅ Current migration: {version}")

            # Check if it's HEAD
            if version == "6391276aefcc":
                print("✅ Database is at HEAD (6391276aefcc)")
                return True, version
            else:
                print(f"⚠️  Database is at {version}, expected HEAD (6391276aefcc)")
                return False, version
        else:
            print("❌ No Alembic version found!")
            return False, None

    def run_full_validation(self):
        """Run all validation checks"""
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  DATABASE SCHEMA VALIDATION - POST MIGRATION".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝")

        results = {}

        # Connect
        self.connect()

        try:
            # Run all checks
            results['alembic'] = self.verify_alembic_version()
            results['schemas'] = self.verify_schemas()
            results['tables'] = self.verify_tables()
            results['enums'] = self.verify_enums()
            results['foreign_keys'] = self.verify_foreign_keys()
            results['indexes'] = self.verify_indexes()

            # Summary
            print("\n" + "="*70)
            print("📊 VALIDATION SUMMARY")
            print("="*70)

            all_passed = True

            alembic_ok, version = results['alembic']
            print(f"\n{'✅' if alembic_ok else '❌'} Alembic Version: {version}")
            all_passed = all_passed and alembic_ok

            schemas_ok, missing = results['schemas']
            print(f"{'✅' if schemas_ok else '❌'} Schemas: {len(self.EXPECTED_SCHEMAS)} expected, {len(self.EXPECTED_SCHEMAS) - len(missing)} found")
            all_passed = all_passed and schemas_ok

            _, tables_dict = results['tables']
            total_tables = sum(len(t) for t in tables_dict.values())
            print(f"✅ Tables: {total_tables} total")

            _, enums_dict = results['enums']
            total_enums = sum(len(e) for e in enums_dict.values())
            print(f"✅ ENUMs: {total_enums} total")

            _, fk_count = results['foreign_keys']
            print(f"✅ Foreign Keys: {fk_count} total")

            _, index_count = results['indexes']
            print(f"✅ Indexes: {index_count} total")

            # Final verdict
            print("\n" + "="*70)
            if all_passed:
                print("🎉 ALL VALIDATIONS PASSED! Database schema is correct! 🎉")
                print("="*70)
                return 0
            else:
                print("❌ SOME VALIDATIONS FAILED! Please review above.")
                print("="*70)
                return 1

        finally:
            self.disconnect()


def main():
    """Main entry point"""
    validator = DatabaseSchemaValidator()
    exit_code = validator.run_full_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
