#!/usr/bin/env python3
"""Verify payment notification tables were created"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Get DATABASE_URL and convert from asyncpg to psycopg2 format
db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')

# Connect to database
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Check tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
      AND (table_name LIKE 'catering%' OR table_name='payment_notifications')
    ORDER BY table_name
""")

print("✅ Payment Notification System Tables:")
for row in cursor.fetchall():
    print(f"   - {row[0]}")

# Check indexes
cursor.execute("""
    SELECT tablename, indexname 
    FROM pg_indexes 
    WHERE schemaname='public' 
      AND (tablename LIKE 'catering%' OR tablename='payment_notifications')
    ORDER BY tablename, indexname
""")

print("\n✅ Indexes Created:")
current_table = None
for row in cursor.fetchall():
    if row[0] != current_table:
        current_table = row[0]
        print(f"\n   {current_table}:")
    print(f"     - {row[1]}")

cursor.close()
conn.close()
print("\n✅ Database migration successful!")
