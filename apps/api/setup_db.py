#!/usr/bin/env python3
"""Database setup script for MyHibachi API"""

import asyncio
import asyncpg
import sys
from pathlib import Path

async def setup_database():
    """Create the development database if it doesn't exist"""
    try:
        # Connect to postgres default database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        
        # Check if myhibachi_dev database exists
        result = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datname = 'myhibachi_dev'"
        )
        
        if not result:
            print("Creating myhibachi_dev database...")
            await conn.execute("CREATE DATABASE myhibachi_dev")
            print("✅ Database created successfully!")
        else:
            print("✅ Database myhibachi_dev already exists")
            
        await conn.close()
        
        # Test connection to the new database
        print("Testing connection to myhibachi_dev...")
        test_conn = await asyncpg.connect(
            'postgresql://postgres:postgres@localhost:5432/myhibachi_dev'
        )
        await test_conn.close()
        print("✅ Database connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)