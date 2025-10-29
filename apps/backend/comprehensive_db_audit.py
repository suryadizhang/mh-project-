"""
Comprehensive Database Audit Script
Checks for errors, conflicts, mismatches, and potential bugs in the database schema
"""

import asyncio
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import reflection
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL_SYNC = os.getenv('DATABASE_URL_SYNC')

def run_audit():
    """Run comprehensive database audit"""
    
    engine = create_engine(DATABASE_URL_SYNC)
    inspector = inspect(engine)
    
    print("="*80)
    print("COMPREHENSIVE DATABASE AUDIT")
    print("="*80)
    print()
    
    issues = []
    warnings = []
    
    # 1. CHECK SCHEMAS
    print("1. SCHEMA VALIDATION")
    print("-" * 80)
    schemas = inspector.get_schema_names()
    expected_schemas = ['core', 'events', 'feedback', 'identity', 'integra', 'lead', 'marketing', 'newsletter', 'public', 'read']
    
    for schema in expected_schemas:
        if schema in schemas:
            print(f"   ✓ Schema '{schema}' exists")
        else:
            issues.append(f"MISSING SCHEMA: '{schema}'")
            print(f"   ✗ Schema '{schema}' MISSING")
    print()
    
    # 2. CHECK CRITICAL TABLES
    print("2. CRITICAL TABLES VALIDATION")
    print("-" * 80)
    
    critical_tables = {
        'public': ['users', 'alembic_version', 'audit_logs'],
        'core': ['customers', 'bookings', 'messages', 'message_threads', 'chefs'],
        'identity': ['stations', 'station_users', 'station_audit_logs', 'station_access_tokens'],
        'feedback': ['customer_reviews', 'discount_coupons', 'review_escalations'],
        'events': ['domain_events', 'outbox', 'inbox'],
        'integra': ['payment_events', 'payment_matches', 'call_sessions'],
        'lead': ['leads', 'lead_scores'],
        'marketing': ['qr_codes', 'qr_scans'],
        'newsletter': ['campaigns', 'subscribers']
    }
    
    for schema, tables in critical_tables.items():
        if schema not in schemas:
            continue
        
        schema_tables = inspector.get_table_names(schema=schema)
        
        for table in tables:
            if table in schema_tables:
                print(f"   ✓ {schema}.{table} exists")
            else:
                warnings.append(f"Missing table: {schema}.{table}")
                print(f"   ⚠ {schema}.{table} MISSING")
    print()
    
    # 3. CHECK USERS TABLE STRUCTURE
    print("3. USERS TABLE VALIDATION")
    print("-" * 80)
    
    users_columns = {col['name']: col for col in inspector.get_columns('users', schema='public')}
    
    required_user_columns = {
        'id': 'UUID',
        'email': 'VARCHAR',
        'password_hash': 'VARCHAR',
        'first_name': 'VARCHAR',
        'last_name': 'VARCHAR',
        'phone': 'VARCHAR',
        'role': 'VARCHAR',
        'is_active': 'BOOLEAN',
        'is_verified': 'BOOLEAN',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP',
        'assigned_station_id': 'UUID'
    }
    
    for col_name, expected_type in required_user_columns.items():
        if col_name in users_columns:
            actual_type = str(users_columns[col_name]['type']).upper()
            if expected_type in actual_type:
                print(f"   ✓ Column '{col_name}' exists ({actual_type})")
            else:
                warnings.append(f"users.{col_name} type mismatch: expected {expected_type}, got {actual_type}")
                print(f"   ⚠ Column '{col_name}' type mismatch: expected {expected_type}, got {actual_type}")
        else:
            issues.append(f"MISSING COLUMN: users.{col_name}")
            print(f"   ✗ Column '{col_name}' MISSING")
    print()
    
    # 4. CHECK FOREIGN KEY INTEGRITY
    print("4. FOREIGN KEY VALIDATION")
    print("-" * 80)
    
    fk_checks = [
        ('core', 'bookings', 'customer_id', 'core', 'customers', 'id'),
        ('core', 'bookings', 'chef_id', 'core', 'chefs', 'id'),
        ('core', 'messages', 'thread_id', 'core', 'message_threads', 'id'),
        ('core', 'message_threads', 'customer_id', 'core', 'customers', 'id'),
        ('identity', 'station_users', 'user_id', 'public', 'users', 'id'),
        ('identity', 'station_users', 'station_id', 'identity', 'stations', 'id'),
        ('feedback', 'customer_reviews', 'station_id', 'identity', 'stations', 'id'),
        ('feedback', 'customer_reviews', 'booking_id', 'core', 'bookings', 'id'),
        ('feedback', 'customer_reviews', 'customer_id', 'core', 'customers', 'id'),
    ]
    
    for source_schema, source_table, source_col, target_schema, target_table, target_col in fk_checks:
        if source_schema not in schemas or target_schema not in schemas:
            continue
            
        source_tables = inspector.get_table_names(schema=source_schema)
        target_tables = inspector.get_table_names(schema=target_schema)
        
        if source_table not in source_tables or target_table not in target_tables:
            continue
        
        fks = inspector.get_foreign_keys(source_table, schema=source_schema)
        fk_exists = False
        
        for fk in fks:
            if (source_col in fk['constrained_columns'] and 
                fk['referred_table'] == target_table and
                target_col in fk['referred_columns']):
                fk_exists = True
                break
        
        if fk_exists:
            print(f"   ✓ FK: {source_schema}.{source_table}.{source_col} → {target_schema}.{target_table}.{target_col}")
        else:
            warnings.append(f"Missing FK: {source_schema}.{source_table}.{source_col} → {target_schema}.{target_table}.{target_col}")
            print(f"   ⚠ FK MISSING: {source_schema}.{source_table}.{source_col} → {target_schema}.{target_table}.{target_col}")
    print()
    
    # 5. CHECK INDEXES
    print("5. INDEX VALIDATION")
    print("-" * 80)
    
    critical_indexes = [
        ('public', 'users', 'email'),
        ('public', 'users', 'role'),
        ('core', 'bookings', 'customer_id'),
        ('core', 'bookings', 'date'),
        ('core', 'customers', 'email_encrypted'),
        ('identity', 'stations', 'code'),
        ('identity', 'stations', 'status'),
    ]
    
    for schema, table, column in critical_indexes:
        if schema not in schemas:
            continue
            
        schema_tables = inspector.get_table_names(schema=schema)
        if table not in schema_tables:
            continue
        
        indexes = inspector.get_indexes(table, schema=schema)
        index_exists = any(column in idx['column_names'] for idx in indexes)
        
        if index_exists:
            print(f"   ✓ Index on {schema}.{table}({column})")
        else:
            warnings.append(f"Missing index: {schema}.{table}({column})")
            print(f"   ⚠ Index MISSING: {schema}.{table}({column})")
    print()
    
    # 6. CHECK ENUMS
    print("6. ENUM TYPE VALIDATION")
    print("-" * 80)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT n.nspname AS schema, t.typname AS enum_name, e.enumlabel AS enum_value
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE n.nspname IN ('public', 'feedback')
            ORDER BY schema, enum_name, e.enumsortorder
        """))
        
        enums = {}
        for row in result:
            schema = row[0]
            enum_name = row[1]
            enum_value = row[2]
            key = f"{schema}.{enum_name}"
            if key not in enums:
                enums[key] = []
            enums[key].append(enum_value)
        
        expected_enums = {
            'public.audit_action': ['VIEW', 'CREATE', 'UPDATE', 'DELETE'],
            'public.user_role': ['SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER'],
            'feedback.review_rating': ['great', 'good', 'okay', 'could_be_better'],
            'feedback.review_status': ['pending', 'submitted', 'escalated', 'resolved', 'archived'],
        }
        
        for enum_key, expected_values in expected_enums.items():
            if enum_key in enums:
                actual_values = enums[enum_key]
                if set(expected_values) == set(actual_values):
                    print(f"   ✓ Enum {enum_key}: {actual_values}")
                else:
                    warnings.append(f"Enum mismatch: {enum_key} - expected {expected_values}, got {actual_values}")
                    print(f"   ⚠ Enum {enum_key} mismatch: expected {expected_values}, got {actual_values}")
            else:
                warnings.append(f"Missing enum: {enum_key}")
                print(f"   ⚠ Enum MISSING: {enum_key}")
    print()
    
    # 7. CHECK CONSTRAINTS
    print("7. CONSTRAINT VALIDATION")
    print("-" * 80)
    
    constraint_checks = [
        ('public', 'users', 'email', 'UNIQUE'),
        ('identity', 'stations', 'code', 'UNIQUE'),
        ('core', 'bookings', 'party_adults', 'CHECK'),
        ('core', 'bookings', 'deposit_due_cents', 'CHECK'),
    ]
    
    for schema, table, column, constraint_type in constraint_checks:
        if schema not in schemas:
            continue
            
        schema_tables = inspector.get_table_names(schema=schema)
        if table not in schema_tables:
            continue
        
        if constraint_type == 'UNIQUE':
            constraints = inspector.get_unique_constraints(table, schema=schema)
            constraint_exists = any(column in c['column_names'] for c in constraints)
        else:  # CHECK
            constraints = inspector.get_check_constraints(table, schema=schema)
            constraint_exists = any(column.lower() in c['sqltext'].lower() for c in constraints)
        
        if constraint_exists:
            print(f"   ✓ {constraint_type} constraint on {schema}.{table}.{column}")
        else:
            warnings.append(f"Missing {constraint_type} constraint: {schema}.{table}.{column}")
            print(f"   ⚠ {constraint_type} constraint MISSING: {schema}.{table}.{column}")
    print()
    
    # 8. CHECK MIGRATION VERSION
    print("8. MIGRATION VERSION CHECK")
    print("-" * 80)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        versions = [row[0] for row in result]
        
        if len(versions) == 1:
            print(f"   ✓ Single migration head: {versions[0]}")
        elif len(versions) == 0:
            issues.append("No migration version found!")
            print("   ✗ No migration version found!")
        else:
            issues.append(f"Multiple migration heads detected: {versions}")
            print(f"   ✗ Multiple migration heads: {versions}")
    print()
    
    # 9. CHECK FOR ORPHANED RECORDS
    print("9. DATA INTEGRITY CHECKS")
    print("-" * 80)
    
    integrity_checks = [
        ("Bookings without customers", "SELECT COUNT(*) FROM core.bookings b LEFT JOIN core.customers c ON b.customer_id = c.id WHERE c.id IS NULL"),
        ("Messages without threads", "SELECT COUNT(*) FROM core.messages m LEFT JOIN core.message_threads mt ON m.thread_id = mt.id WHERE mt.id IS NULL"),
        ("Station users without users", "SELECT COUNT(*) FROM identity.station_users su LEFT JOIN users u ON su.user_id = u.id WHERE u.id IS NULL"),
    ]
    
    with engine.connect() as conn:
        for check_name, query in integrity_checks:
            try:
                result = conn.execute(text(query))
                count = result.scalar()
                if count == 0:
                    print(f"   ✓ {check_name}: 0 orphaned records")
                else:
                    issues.append(f"Data integrity issue: {check_name} found {count} orphaned records")
                    print(f"   ✗ {check_name}: {count} orphaned records")
            except Exception as e:
                warnings.append(f"Could not check {check_name}: {str(e)}")
                print(f"   ⚠ {check_name}: Could not check ({str(e)[:50]})")
    print()
    
    # 10. CHECK FOR POTENTIAL PERFORMANCE ISSUES
    print("10. PERFORMANCE CHECKS")
    print("-" * 80)
    
    with engine.connect() as conn:
        # Check table sizes
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS bytes
            FROM pg_tables
            WHERE schemaname IN ('core', 'public', 'identity', 'feedback', 'events')
            ORDER BY bytes DESC
            LIMIT 10
        """))
        
        print("   Top 10 largest tables:")
        for row in result:
            print(f"      - {row[0]}.{row[1]}: {row[2]}")
        
        # Check for tables without primary keys
        result = conn.execute(text("""
            SELECT 
                n.nspname AS schema,
                c.relname AS table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_constraint cn ON cn.conrelid = c.oid AND cn.contype = 'p'
            WHERE c.relkind = 'r'
            AND n.nspname IN ('core', 'public', 'identity', 'feedback', 'events', 'integra', 'lead', 'marketing', 'newsletter')
            AND cn.conname IS NULL
            ORDER BY n.nspname, c.relname
        """))
        
        tables_without_pk = list(result)
        if tables_without_pk:
            print("\n   ⚠ Tables without primary keys:")
            for row in tables_without_pk:
                warnings.append(f"Table without PK: {row[0]}.{row[1]}")
                print(f"      - {row[0]}.{row[1]}")
        else:
            print("\n   ✓ All tables have primary keys")
    print()
    
    # SUMMARY
    print("="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    if not issues and not warnings:
        print("\n✅ DATABASE IS HEALTHY!")
        print("   No critical issues or warnings detected.")
    else:
        if issues:
            print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
    
    print("\n" + "="*80)
    
    return len(issues), len(warnings)

if __name__ == "__main__":
    critical_count, warning_count = run_audit()
    
    # Exit with appropriate code
    if critical_count > 0:
        exit(1)  # Critical issues found
    elif warning_count > 0:
        exit(2)  # Warnings found
    else:
        exit(0)  # All good
cd apps/backend
python seed_first_station.py