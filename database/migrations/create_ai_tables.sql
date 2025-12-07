-- ===========================================================================
-- AI Schema Tables Creation Script
-- MyHibachi Backend - Production Database
-- ===========================================================================
-- This script creates all tables in the 'ai' schema for the AI subsystem
-- Run after all enums have been created
-- ===========================================================================

-- Ensure ai schema exists
CREATE SCHEMA IF NOT EXISTS ai;

-- ===========================================================================
-- 1. UNIFIED CONVERSATIONS TABLE
-- ===========================================================================
-- Main conversation model for all communication channels
-- Supports: web, SMS, voice, Facebook, Instagram, email, WhatsApp

CREATE TABLE IF NOT EXISTS ai.conversations (
    -- Primary Key
    id VARCHAR(100) PRIMARY KEY,

    -- User & Channel Identification
    user_id VARCHAR(255),
    customer_id VARCHAR(36) REFERENCES core.customers(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    thread_id VARCHAR(255),
    channel_metadata JSONB NOT NULL DEFAULT '{}',

    -- Conversation Status & Lifecycle
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,
    closed_reason VARCHAR(100),

    -- Conversation Context
    message_count INTEGER NOT NULL DEFAULT 0,
    context JSONB NOT NULL DEFAULT '{}',

    -- Emotion Tracking
    average_emotion_score FLOAT,
    emotion_trend VARCHAR(20),

    -- Human Escalation
    escalated BOOLEAN NOT NULL DEFAULT FALSE,
    escalated_at TIMESTAMP,
    assigned_agent_id VARCHAR(255),
    escalation_reason TEXT,

    -- Shadow Learning
    confidence_score FLOAT DEFAULT 1.0,
    route_decision VARCHAR(50) DEFAULT 'teacher',
    student_response TEXT,
    teacher_response TEXT,
    reward_score FLOAT
);

-- Conversations Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_active ON ai.conversations(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_conversations_user_channel ON ai.conversations(user_id, channel);
CREATE INDEX IF NOT EXISTS idx_conversations_channel_status ON ai.conversations(channel, status);
CREATE INDEX IF NOT EXISTS idx_conversations_status_updated ON ai.conversations(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_conversations_emotion_trend ON ai.conversations(average_emotion_score, emotion_trend);
CREATE INDEX IF NOT EXISTS idx_conversations_emotion_active ON ai.conversations(average_emotion_score, is_active);
CREATE INDEX IF NOT EXISTS idx_conversations_escalated ON ai.conversations(escalated, escalated_at);
CREATE INDEX IF NOT EXISTS idx_conversations_assigned_agent ON ai.conversations(assigned_agent_id, status);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON ai.conversations(last_message_at);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON ai.conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_closed ON ai.conversations(closed_at);
CREATE INDEX IF NOT EXISTS idx_conversations_context ON ai.conversations USING gin(context);
CREATE INDEX IF NOT EXISTS idx_conversations_channel_metadata ON ai.conversations USING gin(channel_metadata);
CREATE INDEX IF NOT EXISTS idx_conversations_route_decision ON ai.conversations(route_decision, confidence_score);
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id ON ai.conversations(customer_id);

COMMENT ON TABLE ai.conversations IS 'Unified conversation model for all communication channels (web, SMS, voice, social media)';

-- ===========================================================================
-- 2. UNIFIED MESSAGES TABLE
-- ===========================================================================
-- Messages within conversations with emotion tracking, token usage, tool calls

CREATE TABLE IF NOT EXISTS ai.messages (
    -- Primary Key
    id VARCHAR(100) PRIMARY KEY,

    -- Conversation Relationship
    conversation_id VARCHAR(100) NOT NULL REFERENCES ai.conversations(id) ON DELETE CASCADE,

    -- Message Content
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    text TEXT,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',

    -- Timestamps
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMP,

    -- Metadata
    message_metadata JSONB NOT NULL DEFAULT '{}',

    -- Emotion Tracking
    emotion_score FLOAT,
    emotion_label VARCHAR(20),
    detected_emotions JSONB,

    -- AI Performance Tracking
    model_used VARCHAR(50),
    confidence FLOAT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd FLOAT,
    processing_time_ms INTEGER,

    -- Knowledge Base & Intent
    intent_classification VARCHAR(50),
    kb_sources_used JSONB DEFAULT '[]',

    -- Tool Use
    tool_calls JSONB,
    tool_results JSONB,

    -- Human Feedback
    human_feedback VARCHAR(20),
    human_correction TEXT,
    is_training_data BOOLEAN NOT NULL DEFAULT FALSE
);

-- Messages Indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp ON ai.messages(conversation_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_role ON ai.messages(conversation_id, role);
CREATE INDEX IF NOT EXISTS idx_messages_emotion_history ON ai.messages(conversation_id, emotion_score, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_emotion_label ON ai.messages(emotion_label);
CREATE INDEX IF NOT EXISTS idx_messages_role_created ON ai.messages(role, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_model_used ON ai.messages(model_used, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON ai.messages(channel);
CREATE INDEX IF NOT EXISTS idx_messages_training_data ON ai.messages(is_training_data, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_human_feedback ON ai.messages(human_feedback, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_metadata ON ai.messages USING gin(message_metadata);
CREATE INDEX IF NOT EXISTS idx_messages_kb_sources ON ai.messages USING gin(kb_sources_used);
CREATE INDEX IF NOT EXISTS idx_messages_tool_calls ON ai.messages USING gin(tool_calls);
CREATE INDEX IF NOT EXISTS idx_messages_detected_emotions ON ai.messages USING gin(detected_emotions);

COMMENT ON TABLE ai.messages IS 'Unified message model with emotion tracking, AI performance metrics, and training data collection';

-- ===========================================================================
-- 3. CUSTOMER ENGAGEMENT FOLLOWUPS TABLE
-- ===========================================================================
-- Scheduled customer engagement and automated follow-ups

CREATE TABLE IF NOT EXISTS ai.customer_engagement_followups (
    -- Primary Key
    id VARCHAR(255) PRIMARY KEY,

    -- Relationship Identifiers
    conversation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Trigger Information
    trigger_type VARCHAR(50) NOT NULL,
    trigger_data JSONB NOT NULL DEFAULT '{}',

    -- Scheduling
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Message Content
    template_id VARCHAR(50),
    message_content TEXT,

    -- Metadata & Error Tracking
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
);

-- Followups Indexes
CREATE INDEX IF NOT EXISTS idx_followups_status_scheduled ON ai.customer_engagement_followups(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_followups_user_status ON ai.customer_engagement_followups(user_id, status);
CREATE INDEX IF NOT EXISTS idx_followups_duplicate_check ON ai.customer_engagement_followups(user_id, trigger_type, status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_followups_conversation ON ai.customer_engagement_followups(conversation_id);
CREATE INDEX IF NOT EXISTS idx_followups_trigger_type ON ai.customer_engagement_followups(trigger_type, status);
CREATE INDEX IF NOT EXISTS idx_followups_created ON ai.customer_engagement_followups(created_at);
CREATE INDEX IF NOT EXISTS idx_followups_executed ON ai.customer_engagement_followups(executed_at);

COMMENT ON TABLE ai.customer_engagement_followups IS 'Scheduled customer engagement follow-ups (post-event, re-engagement, emotion-based)';

-- ===========================================================================
-- 4. KNOWLEDGE BASE CHUNKS TABLE
-- ===========================================================================
-- RAG knowledge base for AI responses

CREATE TABLE IF NOT EXISTS ai.kb_chunks (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,

    -- Content
    title VARCHAR(500) NOT NULL,
    text TEXT NOT NULL,
    vector JSON,  -- Will be VECTOR(384) when pgvector is enabled

    -- Categorization
    tags JSONB NOT NULL DEFAULT '[]',
    category VARCHAR(100),
    source_type VARCHAR(50),

    -- Quality & Usage Tracking
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_rate FLOAT NOT NULL DEFAULT 0.0,

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Source Tracking
    source_message_id VARCHAR(36),
    created_by_agent_id VARCHAR(255)
);

-- KB Chunks Indexes
CREATE INDEX IF NOT EXISTS idx_kb_category ON ai.kb_chunks(category);
CREATE INDEX IF NOT EXISTS idx_kb_source_type ON ai.kb_chunks(source_type);
CREATE INDEX IF NOT EXISTS idx_kb_usage_success ON ai.kb_chunks(usage_count, success_rate);
CREATE INDEX IF NOT EXISTS idx_kb_updated ON ai.kb_chunks(updated_at);
CREATE INDEX IF NOT EXISTS idx_kb_tags ON ai.kb_chunks USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_kb_source_message ON ai.kb_chunks(source_message_id);

COMMENT ON TABLE ai.kb_chunks IS 'Knowledge base chunks for RAG (Retrieval-Augmented Generation)';

-- ===========================================================================
-- 5. ESCALATION RULES TABLE
-- ===========================================================================
-- Rules for automatic escalation to human agents

CREATE TABLE IF NOT EXISTS ai.escalation_rules (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,

    -- Rule Definition
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,

    -- Trigger Conditions
    keywords JSONB NOT NULL DEFAULT '[]',
    confidence_threshold FLOAT,
    sentiment_threshold FLOAT,

    -- Rule Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 1,

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Escalation Rules Indexes
CREATE INDEX IF NOT EXISTS idx_escalation_active_priority ON ai.escalation_rules(is_active, priority);
CREATE INDEX IF NOT EXISTS idx_escalation_updated ON ai.escalation_rules(updated_at);

COMMENT ON TABLE ai.escalation_rules IS 'Rules for automatic escalation to human agents (keywords, confidence, sentiment thresholds)';

-- ===========================================================================
-- 6. CONVERSATION ANALYTICS TABLE
-- ===========================================================================
-- Analytics and metrics for conversation quality

CREATE TABLE IF NOT EXISTS ai.conversation_analytics (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL UNIQUE REFERENCES ai.conversations(id) ON DELETE CASCADE,

    -- Message Counts
    total_messages INTEGER NOT NULL DEFAULT 0,
    ai_messages INTEGER NOT NULL DEFAULT 0,
    human_messages INTEGER NOT NULL DEFAULT 0,

    -- Quality Scores
    avg_confidence FLOAT,
    resolution_status VARCHAR(20),
    customer_satisfaction INTEGER,

    -- Timing Metrics
    first_response_time_seconds INTEGER,
    resolution_time_seconds INTEGER,

    -- Cost Tracking
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost_usd FLOAT NOT NULL DEFAULT 0.0,

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_analytics_conversation ON ai.conversation_analytics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_analytics_resolution ON ai.conversation_analytics(resolution_status, created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_satisfaction ON ai.conversation_analytics(customer_satisfaction, created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_cost ON ai.conversation_analytics(total_cost_usd, created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_response_time ON ai.conversation_analytics(first_response_time_seconds);
CREATE INDEX IF NOT EXISTS idx_analytics_resolution_time ON ai.conversation_analytics(resolution_time_seconds);
CREATE INDEX IF NOT EXISTS idx_analytics_confidence ON ai.conversation_analytics(avg_confidence);

COMMENT ON TABLE ai.conversation_analytics IS 'Conversation quality metrics, cost tracking, and performance analytics';

-- ===========================================================================
-- 7. AI USAGE TABLE
-- ===========================================================================
-- Detailed AI usage tracking per conversation

CREATE TABLE IF NOT EXISTS ai.ai_usage (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL REFERENCES ai.conversations(id) ON DELETE CASCADE,

    -- Model Information
    model_name VARCHAR(50) NOT NULL,

    -- Token Usage
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,

    -- Cost Tracking
    cost_usd FLOAT NOT NULL DEFAULT 0.0,

    -- Performance Metrics
    response_time_ms INTEGER,

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- AI Usage Indexes
CREATE INDEX IF NOT EXISTS idx_usage_conversation ON ai.ai_usage(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_model ON ai.ai_usage(model_name, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_cost ON ai.ai_usage(cost_usd, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_performance ON ai.ai_usage(response_time_ms);

COMMENT ON TABLE ai.ai_usage IS 'Detailed AI model usage tracking (tokens, cost, response time)';

-- ===========================================================================
-- 8. TRAINING DATA TABLE
-- ===========================================================================
-- High-quality training data collection for model improvement

CREATE TABLE IF NOT EXISTS ai.training_data (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,

    -- Source Tracking
    conversation_id VARCHAR(100) REFERENCES ai.conversations(id) ON DELETE SET NULL,
    message_id VARCHAR(100) REFERENCES ai.messages(id) ON DELETE SET NULL,

    -- Training Content
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    human_correction TEXT,

    -- Quality Indicators
    quality_score FLOAT NOT NULL DEFAULT 0.0,
    category VARCHAR(100),

    -- Approval & Metadata
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    training_metadata JSONB NOT NULL DEFAULT '{}',

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(255)
);

-- Training Data Indexes
CREATE INDEX IF NOT EXISTS idx_training_approved ON ai.training_data(is_approved, created_at);
CREATE INDEX IF NOT EXISTS idx_training_category ON ai.training_data(category, is_approved);
CREATE INDEX IF NOT EXISTS idx_training_quality ON ai.training_data(quality_score, is_approved);
CREATE INDEX IF NOT EXISTS idx_training_conversation ON ai.training_data(conversation_id);
CREATE INDEX IF NOT EXISTS idx_training_message ON ai.training_data(message_id);

COMMENT ON TABLE ai.training_data IS 'High-quality training data collection for model fine-tuning';

-- ===========================================================================
-- 9. AI TUTOR PAIRS TABLE
-- ===========================================================================
-- Teacher-Student Response Pairs for Shadow Learning

CREATE TABLE IF NOT EXISTS ai.ai_tutor_pairs (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Request Context
    prompt TEXT NOT NULL,
    context TEXT,
    agent_type VARCHAR(50),

    -- Teacher Response (OpenAI)
    teacher_model VARCHAR(50) NOT NULL,
    teacher_response TEXT NOT NULL,
    teacher_tokens INTEGER,
    teacher_cost_usd FLOAT,
    teacher_response_time_ms INTEGER,

    -- Student Response (Local Llama)
    student_model VARCHAR(50) NOT NULL,
    student_response TEXT NOT NULL,
    student_tokens INTEGER,
    student_response_time_ms INTEGER,

    -- Similarity Metrics
    similarity_score FLOAT,
    quality_score FLOAT,

    -- Customer Impact
    used_in_production BOOLEAN NOT NULL DEFAULT FALSE,
    customer_feedback VARCHAR(20),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- AI Tutor Pairs Indexes
CREATE INDEX IF NOT EXISTS idx_tutor_created ON ai.ai_tutor_pairs(created_at);
CREATE INDEX IF NOT EXISTS idx_tutor_similarity ON ai.ai_tutor_pairs(similarity_score, created_at);
CREATE INDEX IF NOT EXISTS idx_tutor_quality ON ai.ai_tutor_pairs(quality_score, created_at);
CREATE INDEX IF NOT EXISTS idx_tutor_agent ON ai.ai_tutor_pairs(agent_type, created_at);
CREATE INDEX IF NOT EXISTS idx_tutor_production ON ai.ai_tutor_pairs(used_in_production, created_at);
CREATE INDEX IF NOT EXISTS idx_tutor_feedback ON ai.ai_tutor_pairs(customer_feedback, created_at);

COMMENT ON TABLE ai.ai_tutor_pairs IS 'Teacher-Student response pairs for shadow learning (OpenAI vs Local model)';

-- ===========================================================================
-- 10. AI RLHF SCORES TABLE
-- ===========================================================================
-- Reinforcement Learning from Human Feedback Scores

CREATE TABLE IF NOT EXISTS ai.ai_rlhf_scores (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Reference to Tutor Pair
    tutor_pair_id INTEGER NOT NULL REFERENCES ai.ai_tutor_pairs(id) ON DELETE CASCADE,

    -- Human Feedback
    reviewer_id INTEGER,

    -- Scoring Dimensions (1-5 scale)
    accuracy_score INTEGER NOT NULL,
    helpfulness_score INTEGER NOT NULL,
    tone_score INTEGER NOT NULL,
    completeness_score INTEGER NOT NULL,

    -- Overall Assessment
    overall_score FLOAT NOT NULL,
    would_use_in_production BOOLEAN NOT NULL,

    -- Comments
    feedback_notes TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- RLHF Scores Indexes
CREATE INDEX IF NOT EXISTS idx_rlhf_tutor ON ai.ai_rlhf_scores(tutor_pair_id);
CREATE INDEX IF NOT EXISTS idx_rlhf_overall ON ai.ai_rlhf_scores(overall_score, created_at);
CREATE INDEX IF NOT EXISTS idx_rlhf_production ON ai.ai_rlhf_scores(would_use_in_production, created_at);
CREATE INDEX IF NOT EXISTS idx_rlhf_reviewer ON ai.ai_rlhf_scores(reviewer_id, created_at);

COMMENT ON TABLE ai.ai_rlhf_scores IS 'RLHF scores for student model responses (accuracy, helpfulness, tone, completeness)';

-- ===========================================================================
-- 11. AI EXPORT JOBS TABLE
-- ===========================================================================
-- Training Data Export Jobs

CREATE TABLE IF NOT EXISTS ai.ai_export_jobs (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Job Details
    export_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Export Criteria
    min_similarity_score FLOAT NOT NULL DEFAULT 0.85,
    min_rlhf_score FLOAT,
    date_range_start TIMESTAMP,
    date_range_end TIMESTAMP,

    -- Results
    pairs_exported INTEGER NOT NULL DEFAULT 0,
    output_file_path VARCHAR(500),
    output_file_size_mb FLOAT,

    -- Error Handling
    error_message TEXT,

    -- Metadata
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by INTEGER
);

-- Export Jobs Indexes
CREATE INDEX IF NOT EXISTS idx_export_status ON ai.ai_export_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_export_type ON ai.ai_export_jobs(export_type, status);
CREATE INDEX IF NOT EXISTS idx_export_creator ON ai.ai_export_jobs(created_by, created_at);

COMMENT ON TABLE ai.ai_export_jobs IS 'Training data export jobs for fine-tuning pipelines';

-- ===========================================================================
-- FINAL: Verify Table Creation
-- ===========================================================================
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as size
FROM pg_tables
WHERE schemaname = 'ai'
ORDER BY tablename;
