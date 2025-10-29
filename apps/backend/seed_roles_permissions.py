"""Seed default roles and permissions"""
import asyncio
import asyncpg
import sys
import uuid
sys.path.insert(0, 'src')
from src.core.config import get_settings
from src.models.role import DEFAULT_ROLES, RoleType, PermissionType

async def seed_roles_permissions():
    settings = get_settings()
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🌱 Seeding permissions...")
        
        # Create all permissions first
        permission_ids = {}
        for perm in PermissionType:
            resource, action = perm.value.split(':')
            display_name = f"{action.title()} {resource.title()}"
            description = f"Permission to {action} {resource}"
            
            # Check if permission exists
            existing = await conn.fetchrow(
                'SELECT id FROM identity.permissions WHERE name = $1',
                perm.value
            )
            
            if existing:
                permission_ids[perm.value] = existing['id']
                print(f"  ✓ Permission exists: {perm.value}")
            else:
                perm_id = uuid.uuid4()
                await conn.execute('''
                    INSERT INTO identity.permissions (id, name, display_name, description, resource, action)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', perm_id, perm.value, display_name, description, resource, action)
                permission_ids[perm.value] = perm_id
                print(f"  ✅ Created permission: {perm.value}")
        
        print(f"\n🌱 Seeding roles...")
        
        # Create roles with their permissions
        for role_type, role_config in DEFAULT_ROLES.items():
            # Check if role exists
            existing_role = await conn.fetchrow(
                'SELECT id FROM identity.roles WHERE name = $1',
                role_type.value
            )
            
            if existing_role:
                role_id = existing_role['id']
                print(f"  ✓ Role exists: {role_config['display_name']}")
            else:
                role_id = uuid.uuid4()
                await conn.execute('''
                    INSERT INTO identity.roles (id, name, display_name, description, is_system_role, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', role_id, role_type.value, role_config['display_name'], 
                   role_config['description'], role_config['is_system_role'], True)
                print(f"  ✅ Created role: {role_config['display_name']}")
            
            # Assign permissions to role
            for perm in role_config['permissions']:
                perm_value = perm.value if hasattr(perm, 'value') else perm
                perm_id = permission_ids.get(perm_value)
                
                if perm_id:
                    # Check if permission already assigned
                    existing_assignment = await conn.fetchrow(
                        'SELECT 1 FROM identity.role_permissions WHERE role_id = $1 AND permission_id = $2',
                        role_id, perm_id
                    )
                    
                    if not existing_assignment:
                        await conn.execute('''
                            INSERT INTO identity.role_permissions (role_id, permission_id)
                            VALUES ($1, $2)
                        ''', role_id, perm_id)
        
        print(f"\n✅ Successfully seeded {len(PermissionType)} permissions and {len(DEFAULT_ROLES)} roles!")
        
        # Show summary
        print(f"\n📊 Summary:")
        role_counts = await conn.fetch('''
            SELECT r.display_name, COUNT(rp.permission_id) as perm_count
            FROM identity.roles r
            LEFT JOIN identity.role_permissions rp ON r.id = rp.role_id
            GROUP BY r.id, r.display_name
            ORDER BY r.display_name
        ''')
        
        for row in role_counts:
            print(f"  • {row['display_name']}: {row['perm_count']} permissions")
            
    except Exception as e:
        print(f"❌ Error seeding roles/permissions: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Starting role and permission seeding...")
    asyncio.run(seed_roles_permissions())
