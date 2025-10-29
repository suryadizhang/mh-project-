"""Promote OAuth user to super admin and activate account"""
import asyncio
import asyncpg
import sys
sys.path.insert(0, 'src')
from src.core.config import get_settings

async def promote_user(email: str):
    settings = get_settings()
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Update user to super admin and active status
        result = await conn.execute('''
            UPDATE identity.users 
            SET is_super_admin = true, 
                status = 'active',
                updated_at = NOW()
            WHERE email = $1
        ''', email)
        
        # Fetch updated user details
        user = await conn.fetchrow('''
            SELECT id, email, full_name, status, is_super_admin, 
                   is_email_verified, created_at, updated_at
            FROM identity.users 
            WHERE email = $1
        ''', email)
        
        if user:
            print(f"✅ User promoted successfully!")
            print(f"  Email: {user['email']}")
            print(f"  Full Name: {user['full_name']}")
            print(f"  Status: {user['status']} (was: pending)")
            print(f"  Super Admin: {user['is_super_admin']} (was: False)")
            print(f"  Email Verified: {user['is_email_verified']}")
            print(f"  Created: {user['created_at']}")
            print(f"  Updated: {user['updated_at']}")
        else:
            print(f"❌ User not found: {email}")
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    email = 'myhibachichef@gmail.com'
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"Promoting {email} to super admin...")
    asyncio.run(promote_user(email))
