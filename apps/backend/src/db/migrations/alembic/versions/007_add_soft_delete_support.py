"""add soft delete support

Revision ID: 007_add_soft_delete_support
Revises: 006_create_audit_logs_system
Create Date: 2025-10-28 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007_add_soft_delete_support'
down_revision: Union[str, None] = '006_create_audit_logs_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add soft delete columns to critical tables.
    Allows deletion tracking and 30-day restore window.
    """
    
    tables_to_update = [
        ('bookings', 'core', 'Booking records'),
        ('customers', 'core', 'Customer profiles'),
        ('leads', 'core', 'Sales leads'),
        ('reviews', 'feedback', 'Customer reviews'),
    ]
    
    for table_name, schema_name, description in tables_to_update:
        # Check if table exists
        conn = op.get_bind()
        table_check = conn.execute(sa.text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}' 
            AND table_name = '{table_name}'
        """))
        
        if table_check.fetchone() is None:
            print(f"[SKIP] {table_name} - table does not exist in schema {schema_name}")
            continue
        
        # Check if deleted_at column already exists
        result = conn.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema_name}' 
            AND table_name = '{table_name}' 
            AND column_name = 'deleted_at'
        """))
        
        if result.fetchone() is not None:
            print(f"[SKIP] {table_name} - soft delete columns already exist")
            continue
            
        # Add soft delete columns
        op.add_column(table_name, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of deletion (NULL = not deleted)'), schema=schema_name)
        op.add_column(table_name, sa.Column('deleted_by', sa.UUID(), nullable=True, comment='User who deleted this record'), schema=schema_name)
        op.add_column(table_name, sa.Column('delete_reason', sa.Text(), nullable=True, comment='Reason for deletion'), schema=schema_name)
        
        # Create partial index for active (non-deleted) records
        # This makes queries filtering WHERE deleted_at IS NULL extremely fast
        op.create_index(
            f'idx_{table_name}_deleted_at',
            table_name,
            ['deleted_at'],
            postgresql_where=sa.text('deleted_at IS NULL'),
            schema=schema_name
        )
        
        # Create index for deleted records (for trash/archive view)
        op.create_index(
            f'idx_{table_name}_deleted_by',
            table_name,
            ['deleted_by', 'deleted_at'],
            postgresql_where=sa.text('deleted_at IS NOT NULL'),
            schema=schema_name
        )
        
        print(f"[SUCCESS] Added soft delete support to {table_name} ({description})")
    
    print("\n[SOFT DELETE SUMMARY]")
    print("   - Added 3 columns per table: deleted_at, deleted_by, delete_reason")
    print("   - Created 2 indexes per table for performance")
    print(f"   - Total: {len(tables_to_update)} tables updated")
    print("\n[USAGE]")
    print("   - Filter active records: WHERE deleted_at IS NULL")
    print("   - Filter deleted records: WHERE deleted_at IS NOT NULL")
    print("   - Restore: SET deleted_at = NULL, deleted_by = NULL, delete_reason = NULL")


def downgrade() -> None:
    """Remove soft delete support"""
    
    tables_to_update = [
        ('bookings', 'core'),
        ('customers', 'core'),
        ('leads', 'core'),
        ('reviews', 'feedback')
    ]
    
    for table_name, schema_name in tables_to_update:
        # Drop indexes
        op.drop_index(f'idx_{table_name}_deleted_by', table_name, schema=schema_name)
        op.drop_index(f'idx_{table_name}_deleted_at', table_name, schema=schema_name)
        
        # Drop columns
        op.drop_column(table_name, 'delete_reason', schema=schema_name)
        op.drop_column(table_name, 'deleted_by', schema=schema_name)
        op.drop_column(table_name, 'deleted_at', schema=schema_name)
        
        print(f"[ROLLBACK] Removed soft delete support from {table_name}")
