"""
Direct SQL script to create roles and permissions tables
Bypassing Alembic migration issues
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv()

async def create_tables():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    
    # Convert from SQLAlchemy format to asyncpg format
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        # Create roletype enum if not exists
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE roletype AS ENUM ('super_admin', 'admin', 'manager', 'staff', 'viewer');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✅ roletype enum ready")
        
        # Create permissiontype enum if not exists
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE permissiontype AS ENUM (
                    'user:create', 'user:read', 'user:update', 'user:delete', 'user:approve',
                    'station:create', 'station:read', 'station:update', 'station:delete',
                    'booking:create', 'booking:read', 'booking:update', 'booking:delete', 'booking:cancel',
                    'customer:create', 'customer:read', 'customer:update', 'customer:delete',
                    'payment:create', 'payment:read', 'payment:refund',
                    'review:read', 'review:moderate', 'review:respond',
                    'analytics:view', 'analytics:export',
                    'settings:read', 'settings:update'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✅ permissiontype enum ready")
        
        # Create permissions table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identity.permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name permissiontype UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                resource VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ permissions table ready")
        
        # Create roles table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identity.roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name roletype UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
                settings JSONB NOT NULL DEFAULT '{}'::jsonb
            );
        """)
        print("✅ roles table ready")
        
        # Create role_permissions junction table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identity.role_permissions (
                role_id UUID REFERENCES identity.roles(id) ON DELETE CASCADE,
                permission_id UUID REFERENCES identity.permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (role_id, permission_id)
            );
        """)
        print("✅ role_permissions table ready")
        
        # Create user_roles junction table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identity.user_roles (
                user_id UUID REFERENCES identity.users(id) ON DELETE CASCADE,
                role_id UUID REFERENCES identity.roles(id) ON DELETE CASCADE,
                assigned_at TIMESTAMPTZ DEFAULT NOW(),
                assigned_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
                PRIMARY KEY (user_id, role_id)
            );
        """)
        print("✅ user_roles table ready")
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_permissions_name ON identity.permissions(name);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_permissions_resource ON identity.permissions(resource);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_permissions_action ON identity.permissions(action);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_roles_name ON identity.roles(name);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_roles_created_at ON identity.roles(created_at);")
        print("✅ indexes created")
        
        print("\n✅ All tables and enums created successfully!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
