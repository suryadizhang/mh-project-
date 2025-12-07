-- Support schema enums
CREATE TYPE support.escalation_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE support.escalation_method AS ENUM ('email', 'sms', 'phone', 'dashboard');
CREATE TYPE support.escalation_status AS ENUM ('pending', 'escalated', 'resolved', 'expired');
CREATE TYPE support.ticket_status AS ENUM ('open', 'in_progress', 'resolved', 'closed', 'escalated');
CREATE TYPE support.ticket_priority AS ENUM ('low', 'medium', 'high', 'urgent');

-- Ops schema enums
CREATE TYPE ops.chef_status AS ENUM ('active', 'inactive', 'suspended', 'on_leave');
CREATE TYPE ops.chef_specialty AS ENUM ('hibachi', 'sushi', 'teppanyaki', 'general');
CREATE TYPE ops.day_of_week AS ENUM ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday');
CREATE TYPE ops.timeoff_type AS ENUM ('vacation', 'sick', 'personal', 'unpaid');
CREATE TYPE ops.timeoff_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');
CREATE TYPE ops.equipment_type AS ENUM ('grill', 'knife_set', 'cooking_utensils', 'serving_ware', 'safety_equipment', 'transport', 'other');
CREATE TYPE ops.equipment_status AS ENUM ('available', 'in_use', 'maintenance', 'retired');
CREATE TYPE ops.maintenance_type AS ENUM ('routine', 'repair', 'inspection', 'emergency');
CREATE TYPE ops.inventory_category AS ENUM ('ingredients', 'supplies', 'equipment', 'packaging');

-- Communications schema enums
CREATE TYPE communications.sms_queue_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'cancelled');
CREATE TYPE communications.sms_delivery_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'undelivered');
CREATE TYPE communications.recording_type AS ENUM ('inbound', 'outbound', 'conference', 'voicemail');
CREATE TYPE communications.recording_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE communications.template_status AS ENUM ('active', 'inactive', 'draft', 'archived');
CREATE TYPE communications.template_source AS ENUM ('system', 'custom', 'imported');
CREATE TYPE communications.tone_type AS ENUM ('formal', 'casual', 'friendly', 'professional', 'urgent');

-- Integra schema enums
CREATE TYPE integra.sync_type AS ENUM ('full', 'incremental', 'delta');
CREATE TYPE integra.sync_status AS ENUM ('pending', 'running', 'completed', 'failed');
CREATE TYPE integra.sync_source_type AS ENUM ('api', 'webhook', 'manual', 'scheduled');

-- Feedback schema enums
CREATE TYPE feedback.coupon_status AS ENUM ('active', 'inactive', 'expired', 'redeemed');
CREATE TYPE feedback.feedback_status AS ENUM ('pending', 'reviewed', 'resolved', 'archived');
CREATE TYPE feedback.feedback_type AS ENUM ('suggestion', 'complaint', 'compliment', 'question', 'other');
CREATE TYPE feedback.survey_status AS ENUM ('draft', 'active', 'closed', 'archived');
CREATE TYPE feedback.upsell_trigger_type AS ENUM ('post_booking', 'pre_event', 'post_event', 'anniversary', 'birthday');
CREATE TYPE feedback.offer_status AS ENUM ('active', 'inactive', 'expired', 'redeemed');

-- Identity schema enums
CREATE TYPE identity.user_role AS ENUM ('super_admin', 'admin', 'station_admin', 'customer_support', 'customer');
CREATE TYPE identity.user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');
CREATE TYPE identity.permissiontype AS ENUM ('read', 'write', 'delete', 'admin');
CREATE TYPE identity.roletype AS ENUM ('super_admin', 'admin', 'station_admin', 'customer_support', 'chef', 'customer');

-- AI schema enums
CREATE TYPE ai.ai_model_type AS ENUM ('gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3', 'claude-2', 'gemini');
CREATE TYPE ai.conversation_status AS ENUM ('active', 'ended', 'abandoned', 'escalated');
CREATE TYPE ai.escalation_status AS ENUM ('pending', 'escalated', 'resolved', 'expired');
CREATE TYPE ai.escalation_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE ai.escalation_method AS ENUM ('email', 'sms', 'phone', 'dashboard');
CREATE TYPE ai.rule_category AS ENUM ('booking', 'payment', 'customer_service', 'complaint', 'feedback', 'technical');

-- Newsletter schema enums
CREATE TYPE newsletter.template_source AS ENUM ('system', 'custom', 'imported');
CREATE TYPE newsletter.template_status AS ENUM ('active', 'inactive', 'draft', 'archived');
