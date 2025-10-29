"""Check if OAuth user was created"""
import asyncio
import asyncpg
import sys
sys.path.insert(0, 'src')
from src.core.config import get_settings

async def check_user():
    settings = get_settings()
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    result = await conn.fetch('''
        SELECT id, email, full_name, google_id, status, is_super_admin, 
               is_email_verified, created_at 
        FROM identity.users 
        WHERE email = 'myhibachichef@gmail.com'
    ''')
    
    if result:
        print("✅ User found in database!")
        for row in result:
            print(f"  Email: {row['email']}")
            print(f"  Full Name: {row['full_name']}")
            print(f"  Google ID: {row['google_id']}")
            print(f"  Status: {row['status']}")
            print(f"  Super Admin: {row['is_super_admin']}")
            print(f"  Email Verified: {row['is_email_verified']}")
            print(f"  Created: {row['created_at']}")
    else:
        print("❌ No user found")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_user())
