"""create_alert_rules_table

Revision ID: 573ac0543ebb
Revises: 5f6cb2dfed84
Create Date: 2025-11-10 21:17:37.459040

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '573ac0543ebb'
down_revision = '5f6cb2dfed84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE thresholdoperator AS ENUM (
                'gt', 'gte', 'lt', 'lte', 'eq', 'neq'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ruleseverity AS ENUM (
                'critical', 'high', 'medium', 'low', 'info'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create alert_rules table
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('operator', sa.String(length=10), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_title_template', sa.String(length=500), nullable=True),
        sa.Column('alert_message_template', sa.String(length=2000), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_alert_rules_name', 'alert_rules', ['name'], unique=True)
    op.create_index('ix_alert_rules_metric_name', 'alert_rules', ['metric_name'], unique=False)
    op.create_index('ix_alert_rules_enabled', 'alert_rules', ['enabled'], unique=False)
    op.create_index('ix_alert_rules_id', 'alert_rules', ['id'], unique=False)
    
    # Insert some example rules
    op.execute("""
        INSERT INTO alert_rules 
        (name, description, metric_name, operator, threshold_value, duration_seconds, cooldown_seconds, severity, enabled, alert_title_template, alert_message_template)
        VALUES
        ('High CPU Usage', 'Alert when CPU usage exceeds 80% for 2 minutes', 'cpu_percent', 'gt', 80.0, 120, 300, 'high', true, 
         '{rule_name}: CPU at {current_value}%', 'CPU usage is {current_value}% (threshold: > {threshold_value}%) for {duration}s'),
        
        ('Critical CPU Usage', 'Alert when CPU usage exceeds 95% for 1 minute', 'cpu_percent', 'gte', 95.0, 60, 180, 'critical', true,
         '{rule_name}: CRITICAL CPU at {current_value}%', 'CRITICAL: CPU usage is {current_value}% (threshold: >= {threshold_value}%) for {duration}s'),
        
        ('High Memory Usage', 'Alert when memory usage exceeds 85% for 3 minutes', 'memory_percent', 'gt', 85.0, 180, 300, 'high', true,
         '{rule_name}: Memory at {current_value}%', 'Memory usage is {current_value}% (threshold: > {threshold_value}%) for {duration}s'),
        
        ('Database Unavailable', 'Alert immediately when database is unavailable', 'database_available', 'lt', 1.0, 0, 60, 'critical', true,
         '{rule_name}: Database DOWN', 'Database is unavailable! Immediate attention required.'),
        
        ('High Error Rate', 'Alert when API error rate exceeds 5% for 2 minutes', 'api_error_rate_percent', 'gt', 5.0, 120, 300, 'high', true,
         '{rule_name}: Error rate at {current_value}%', 'API error rate is {current_value}% (threshold: > {threshold_value}%) for {duration}s'),
        
        ('Slow API Response', 'Alert when P95 response time exceeds 1000ms for 3 minutes', 'api_response_time_p95_ms', 'gt', 1000.0, 180, 300, 'medium', true,
         '{rule_name}: P95 latency at {current_value}ms', 'API P95 response time is {current_value}ms (threshold: > {threshold_value}ms) for {duration}s'),
        
        ('High Disk Usage', 'Alert when disk usage exceeds 90%', 'disk_percent', 'gt', 90.0, 300, 600, 'high', true,
         '{rule_name}: Disk at {current_value}%', 'Disk usage is {current_value}% (threshold: > {threshold_value}%)'),
        
        ('Low Cache Hit Rate', 'Alert when cache hit rate drops below 70% for 5 minutes', 'cache_hit_rate_percent', 'lt', 70.0, 300, 600, 'medium', true,
         '{rule_name}: Cache hits at {current_value}%', 'Cache hit rate is {current_value}% (threshold: < {threshold_value}%) for {duration}s')
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_alert_rules_id', table_name='alert_rules')
    op.drop_index('ix_alert_rules_enabled', table_name='alert_rules')
    op.drop_index('ix_alert_rules_metric_name', table_name='alert_rules')
    op.drop_index('ix_alert_rules_name', table_name='alert_rules')
    
    # Drop table
    op.drop_table('alert_rules')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS ruleseverity')
    op.execute('DROP TYPE IF EXISTS thresholdoperator')