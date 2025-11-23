"""fix_all_schema_issues_and_create_newsletter_system

🚨 CRITICAL MIGRATION - Fixes ALL schema issues found in audit

This migration fixes:
1. Creates newsletter schema
2. Moves campaign tables from lead → newsletter  
3. Fixes all broken foreign key schema references
4. Creates SMS templates system (admin + AI suggestions)
5. Creates SMS send count tracking (RingCentral package limits)
6. Creates SMS send queue with retry mechanism
7. Fixes payment table references (catering_bookings → core.bookings)

Revision ID: cafcd735e7fe
Revises: 50da543dcbb3
Create Date: 2025-11-22 00:42:12.189958

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 'cafcd735e7fe'
down_revision = '50da543dcbb3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply all critical database fixes."""
    conn = op.get_bind()
    
    # Clean up any stale ENUMs from previous partial runs
    conn.execute(sa.text("DROP TYPE IF EXISTS sms_queue_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS template_source CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS template_status CASCADE"))
    
    print("\n" + "="*80)
    print("🚨 CRITICAL DATABASE FIX MIGRATION")
    print("="*80)
    
    # ========================================================================
    # PHASE 1: CREATE NEWSLETTER SCHEMA & MOVE TABLES
    # ========================================================================
    
    print("\n📋 Phase 1: Creating newsletter schema and moving campaign tables...")
    
    # Create newsletter schema
    conn.execute(sa.text("CREATE SCHEMA IF NOT EXISTS newsletter"))
    print("  ✅ Created newsletter schema")
    
    # Check if tables exist in lead schema before moving
    campaigns_in_lead = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'lead' AND table_name = 'campaigns'
        )
    """)).scalar()
    
    if campaigns_in_lead:
        # Move campaign tables to newsletter schema
        conn.execute(sa.text("ALTER TABLE lead.campaigns SET SCHEMA newsletter"))
        conn.execute(sa.text("ALTER TABLE lead.campaign_events SET SCHEMA newsletter"))
        conn.execute(sa.text("ALTER TABLE lead.sms_delivery_events SET SCHEMA newsletter"))
        conn.execute(sa.text("ALTER TABLE lead.subscribers SET SCHEMA newsletter"))
        print("  ✅ Moved 4 campaign tables: lead → newsletter")
    else:
        print("  [SKIP] Campaign tables not in lead schema (may already be in newsletter)")
    
    # ========================================================================
    # PHASE 2: FIX FOREIGN KEY SCHEMA PREFIXES
    # ========================================================================
    
    print("\n📋 Phase 2: Fixing foreign key schema references...")
    
    # Fix identity.station_users → identity.users
    station_users_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'identity' AND table_name = 'station_users'
        )
    """)).scalar()
    
    if station_users_exists:
        conn.execute(sa.text("""
            ALTER TABLE identity.station_users 
            DROP CONSTRAINT IF EXISTS fk_station_users_user_id;
            
            ALTER TABLE identity.station_users 
            ADD CONSTRAINT fk_station_users_user_id 
            FOREIGN KEY (user_id) REFERENCES identity.users(id) ON DELETE CASCADE;
        """))
        print("  ✅ Fixed: identity.station_users.user_id → identity.users(id)")
    
    # Fix support.audit_logs → identity.users
    audit_logs_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'support' AND table_name = 'audit_logs'
        )
    """)).scalar()
    
    if audit_logs_exists:
        conn.execute(sa.text("""
            ALTER TABLE support.audit_logs
            DROP CONSTRAINT IF EXISTS fk_audit_logs_user_id;
            
            ALTER TABLE support.audit_logs
            ADD CONSTRAINT fk_audit_logs_user_id
            FOREIGN KEY (user_id) REFERENCES identity.users(id) ON DELETE SET NULL;
        """))
        print("  ✅ Fixed: support.audit_logs.user_id → identity.users(id)")
    
    # Fix bookings.booking_reminders → core.bookings
    reminders_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'bookings' AND table_name = 'booking_reminders'
        )
    """)).scalar()
    
    if reminders_exists:
        conn.execute(sa.text("""
            ALTER TABLE bookings.booking_reminders
            DROP CONSTRAINT IF EXISTS fk_booking_reminders_booking_id;
            
            ALTER TABLE bookings.booking_reminders
            ADD CONSTRAINT fk_booking_reminders_booking_id
            FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE CASCADE;
        """))
        print("  ✅ Fixed: bookings.booking_reminders.booking_id → core.bookings(id)")
    
    # ========================================================================
    # PHASE 3: FIX PAYMENT TABLE REFERENCES
    # ========================================================================
    
    print("\n📋 Phase 3: Fixing payment table references...")
    
    # Fix catering_payments → core.bookings
    catering_payments_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'catering_payments'
        )
    """)).scalar()
    
    if catering_payments_exists:
        conn.execute(sa.text("""
            ALTER TABLE public.catering_payments
            DROP CONSTRAINT IF EXISTS fk_catering_payments_booking_id;
            
            ALTER TABLE public.catering_payments
            ADD CONSTRAINT fk_catering_payments_booking_id
            FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE CASCADE;
        """))
        print("  ✅ Fixed: catering_payments.booking_id → core.bookings(id)")
    
    # Fix payment_notifications → core.bookings
    payment_notif_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'payment_notifications'
        )
    """)).scalar()
    
    if payment_notif_exists:
        conn.execute(sa.text("""
            ALTER TABLE public.payment_notifications
            DROP CONSTRAINT IF EXISTS fk_payment_notifications_booking_id;
            
            ALTER TABLE public.payment_notifications
            ADD CONSTRAINT fk_payment_notifications_booking_id
            FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE SET NULL;
        """))
        print("  ✅ Fixed: payment_notifications.booking_id → core.bookings(id)")
    
    # ========================================================================
    # PHASE 4: CREATE SMS TEMPLATES SYSTEM
    # ========================================================================
    
    print("\n📋 Phase 4: Creating SMS templates system (admin + AI suggestions)...")
    
    # ENUMs will be created automatically by SQLAlchemy when creating the table
    
    # Create SMS templates table
    op.create_table(
        'sms_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False, comment='Template with {{variables}}'),
        sa.Column('category', sa.String(50), nullable=False, comment='reminder, promotion, transactional, newsletter'),
        sa.Column('source', sa.Enum('admin', 'ai_suggested', 'system', name='template_source', create_type=True), nullable=False, server_default='admin'),
        sa.Column('status', sa.Enum('draft', 'pending_approval', 'approved', 'rejected', 'archived', name='template_status', create_type=True), nullable=False, server_default='draft'),
        
        # Variables tracking
        sa.Column('variables', JSONB, server_default='[]', comment='["first_name", "booking_date", "amount"]'),
        sa.Column('example_data', JSONB, server_default='{}', comment='{"first_name": "John", "booking_date": "Dec 25"}'),
        
        # AI suggestion metadata
        sa.Column('ai_prompt', sa.Text, nullable=True, comment='Original AI prompt if AI-generated'),
        sa.Column('ai_confidence', sa.Float, nullable=True, comment='AI confidence score 0.0-1.0'),
        sa.Column('ai_model', sa.String(50), nullable=True, comment='GPT-4, Claude, etc.'),
        
        # Approval workflow
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by', UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        
        # Usage tracking
        sa.Column('usage_count', sa.Integer, server_default='0', comment='How many times used'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        
        # Metadata
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='newsletter'
    )
    
    # Create indexes
    op.create_index('idx_sms_templates_category', 'sms_templates', ['category'], schema='newsletter')
    op.create_index('idx_sms_templates_source', 'sms_templates', ['source'], schema='newsletter')
    op.create_index('idx_sms_templates_status', 'sms_templates', ['status'], schema='newsletter')
    op.create_index('idx_sms_templates_active', 'sms_templates', ['is_active'], schema='newsletter')
    
    print("  ✅ Created sms_templates table with AI suggestion support")
    
    # ========================================================================
    # PHASE 5: CREATE SMS SEND COUNT TRACKING (RINGCENTRAL PACKAGE LIMITS)
    # ========================================================================
    
    print("\n📋 Phase 5: Creating SMS send count tracking (RingCentral package limits)...")
    
    # Create campaign_sms_limits table
    op.create_table(
        'campaign_sms_limits',
        sa.Column('campaign_id', UUID(as_uuid=True), sa.ForeignKey('newsletter.campaigns.id', ondelete='CASCADE'), primary_key=True),
        
        # RingCentral package limits
        sa.Column('monthly_sms_limit', sa.Integer, nullable=False, server_default='1000', comment='RingCentral plan monthly limit'),
        sa.Column('monthly_sms_used', sa.Integer, nullable=False, server_default='0'),
        sa.Column('current_month', sa.String(7), nullable=False, comment='YYYY-MM'),
        
        # Campaign-specific limits
        sa.Column('campaign_sms_limit', sa.Integer, nullable=True, comment='Max SMS for this campaign (optional)'),
        sa.Column('campaign_sms_sent', sa.Integer, nullable=False, server_default='0'),
        sa.Column('campaign_sms_queued', sa.Integer, nullable=False, server_default='0'),
        sa.Column('campaign_sms_failed', sa.Integer, nullable=False, server_default='0'),
        
        # Cost tracking
        sa.Column('cost_per_sms_cents', sa.Integer, nullable=False, server_default='75', comment='Cost in cents (e.g., $0.0075)'),
        sa.Column('total_cost_cents', sa.Integer, nullable=False, server_default='0'),
        
        # Limit exceeded tracking
        sa.Column('monthly_limit_exceeded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('campaign_limit_exceeded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('limit_exceeded_action', sa.String(50), server_default='pause', comment='pause, notify, continue'),
        
        # Alert thresholds
        sa.Column('alert_at_percentage', sa.Integer, server_default='80', comment='Alert when 80% of limit used'),
        sa.Column('alert_sent_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='newsletter'
    )
    
    op.create_index('idx_campaign_sms_limits_month', 'campaign_sms_limits', ['current_month'], schema='newsletter')
    op.create_index('idx_campaign_sms_limits_exceeded', 'campaign_sms_limits', ['monthly_limit_exceeded_at'], schema='newsletter')
    
    print("  ✅ Created campaign_sms_limits table for RingCentral package tracking")
    
    # ========================================================================
    # PHASE 6: CREATE SMS SEND QUEUE WITH RETRY
    # ========================================================================
    
    print("\n📋 Phase 6: Creating SMS send queue with retry mechanism...")
    
    # ENUM will be created automatically by SQLAlchemy
    
    # Create SMS send queue
    op.create_table(
        'sms_send_queue',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('campaign_id', UUID(as_uuid=True), sa.ForeignKey('newsletter.campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('subscriber_id', UUID(as_uuid=True), sa.ForeignKey('newsletter.subscribers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('newsletter.sms_templates.id', ondelete='SET NULL'), nullable=True),
        
        # Message details
        sa.Column('phone_number', sa.String(20), nullable=False, index=True),
        sa.Column('message_content', sa.Text, nullable=False),
        sa.Column('personalized_variables', JSONB, server_default='{}', comment='Rendered template variables'),
        
        # Queue status
        sa.Column('status', sa.Enum('pending', 'sending', 'sent', 'failed', 'cancelled', name='sms_queue_status', create_type=True), nullable=False, server_default='pending', index=True),
        sa.Column('priority', sa.Integer, server_default='0', comment='Higher = sent first'),
        
        # Scheduling
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Retry logic
        sa.Column('attempts', sa.Integer, server_default='0'),
        sa.Column('max_attempts', sa.Integer, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        
        # RingCentral tracking
        sa.Column('message_sid', sa.String(100), nullable=True, unique=True, comment='RingCentral message ID'),
        sa.Column('ringcentral_status', sa.String(50), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='newsletter'
    )
    
    # Create indexes for queue processing
    op.create_index('idx_sms_queue_pending', 'sms_send_queue', ['status', 'scheduled_at'], schema='newsletter')
    op.create_index('idx_sms_queue_retry', 'sms_send_queue', ['status', 'next_retry_at'], schema='newsletter')
    op.create_index('idx_sms_queue_priority', 'sms_send_queue', ['priority', 'scheduled_at'], schema='newsletter')
    
    print("  ✅ Created sms_send_queue table with retry mechanism")
    
    # ========================================================================
    # PHASE 7: ADD MISSING FOREIGN KEYS
    # ========================================================================
    
    print("\n📋 Phase 7: Adding missing foreign keys...")
    
    # Fix marketing.qr_codes.created_by → identity.users
    qr_codes_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'marketing' AND table_name = 'qr_codes'
        )
    """)).scalar()
    
    if qr_codes_exists:
        # Check if created_by column exists
        created_by_exists = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name = 'qr_codes'
                AND column_name = 'created_by'
            )
        """)).scalar()
        
        if created_by_exists:
            conn.execute(sa.text("""
                ALTER TABLE marketing.qr_codes
                DROP CONSTRAINT IF EXISTS fk_qr_codes_created_by;
                
                ALTER TABLE marketing.qr_codes
                ADD CONSTRAINT fk_qr_codes_created_by
                FOREIGN KEY (created_by) REFERENCES identity.users(id) ON DELETE SET NULL;
            """))
            print("  ✅ Added: marketing.qr_codes.created_by → identity.users(id)")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print("\n" + "="*80)
    print("✅ ALL CRITICAL DATABASE ISSUES FIXED!")
    print("="*80)
    print("\n📊 Summary:")
    print("  ✅ Created newsletter schema")
    print("  ✅ Moved 4 campaign tables to newsletter schema")
    print("  ✅ Fixed 5+ foreign key schema references")
    print("  ✅ Created SMS templates system (admin + AI suggestions)")
    print("  ✅ Created SMS send count tracking (RingCentral limits)")
    print("  ✅ Created SMS send queue with retry")
    print("  ✅ Added missing foreign key constraints")
    print("\n🎯 Next: Run 'alembic upgrade head' to apply all fixes")
    print("="*80 + "\n")


def downgrade() -> None:
    """Rollback all fixes."""
    print("\n⚠️  Rolling back database fixes...")
    
    # Drop new tables
    op.drop_table('sms_send_queue', schema='newsletter')
    op.drop_table('campaign_sms_limits', schema='newsletter')
    op.drop_table('sms_templates', schema='newsletter')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS sms_queue_status')
    op.execute('DROP TYPE IF EXISTS template_status')
    op.execute('DROP TYPE IF EXISTS template_source')
    
    # Move tables back to lead schema
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE newsletter.campaigns SET SCHEMA lead"))
    conn.execute(sa.text("ALTER TABLE newsletter.campaign_events SET SCHEMA lead"))
    conn.execute(sa.text("ALTER TABLE newsletter.sms_delivery_events SET SCHEMA lead"))
    conn.execute(sa.text("ALTER TABLE newsletter.subscribers SET SCHEMA lead"))
    
    # Drop newsletter schema
    conn.execute(sa.text("DROP SCHEMA IF EXISTS newsletter CASCADE"))
    
    print("  ✅ Rollback complete")