"""
Feature Flags Configuration for My Hibachi
All new features are behind flags - default OFF in production
Enable flags in dev/staging immediately, gradual rollout in production
"""

from enum import Enum

from pydantic_settings import BaseSettings


class FeatureFlag(str, Enum):
    """Feature flag enumeration for type safety"""

    # ============================================================================
    # BOOKING SYSTEM FLAGS (5 features)
    # ============================================================================
    BOOKING_REMINDERS = "booking_reminders"  # P0 - Booking reminder system
    MULTI_LOCATION = "multi_location"  # P0 - Multi-location support
    RECURRING_BOOKINGS = "recurring_bookings"  # P1 - Recurring events
    BOOKING_WAITLIST = "booking_waitlist"  # P2 - Waitlist management
    GROUP_RESERVATIONS = "group_reservations"  # P2 - Group reservation enhancements

    # ============================================================================
    # CUSTOMER MANAGEMENT FLAGS (6 features)
    # ============================================================================
    CUSTOMER_MERGE = "customer_merge"  # P2 - Customer merge system
    CUSTOMER_EXPORT = "customer_export"  # P1 - Data export (GDPR)
    CUSTOMER_PREFERENCES = "customer_preferences"  # P1 - Communication preferences
    LOYALTY_POINTS = "loyalty_points"  # P1 - Loyalty points system
    REFERRAL_TRACKING = "referral_tracking"  # P2 - Referral tracking
    CUSTOMER_FEEDBACK_HISTORY = "customer_feedback_history"  # P3 - Feedback history

    # ============================================================================
    # AI SERVICES FLAGS (20 features)
    # ============================================================================
    # Voice AI (5 features)
    VOICE_AI = "voice_ai"  # P2 - Voice AI call handling
    VOICE_TRANSCRIPTION = "voice_transcription"  # P2 - Real-time transcription
    VOICE_SENTIMENT = "voice_sentiment"  # P2 - Live sentiment analysis
    VOICE_TRANSFER = "voice_transfer"  # P2 - Call transfer to human
    VOICE_IVR = "voice_ivr"  # P2 - Interactive Voice Response

    # Embeddings & Vector Search (4 features)
    AI_EMBEDDINGS = "ai_embeddings"  # P3 - Generate embeddings
    EMBEDDINGS_SEARCH = "embeddings_search"  # P3 - Semantic search
    EMBEDDINGS_SIMILARITY = "embeddings_similarity"  # P3 - Find similar queries
    EMBEDDINGS_CLUSTERING = "embeddings_clustering"  # P3 - Conversation clustering

    # ML Training & Model Management (11 features)
    ML_TRAINING = "ml_training"  # P3 - Train custom models
    ML_FINE_TUNING = "ml_fine_tuning"  # P3 - Fine-tune GPT models
    ML_EVALUATION = "ml_evaluation"  # P3 - Model evaluation
    ML_BATCH_PROCESSING = "ml_batch_processing"  # P3 - Batch message processing
    AI_CACHING = "ai_caching"  # P3 - Enhanced AI response caching
    AI_RATE_LIMITING = "ai_rate_limiting"  # P3 - Enhanced rate limiting
    AI_COST_TRACKING = "ai_cost_tracking"  # P3 - OpenAI cost tracking
    AI_MODEL_SWITCHING = "ai_model_switching"  # P3 - Switch between models
    AI_FALLBACK = "ai_fallback"  # P3 - Fallback to simpler models
    AI_CONTEXT_MANAGEMENT = "ai_context_management"  # P3 - Context management
    AI_PROMPT_TEMPLATES = "ai_prompt_templates"  # P3 - Prompt template management

    # ============================================================================
    # ADMIN OPERATIONS FLAGS (22 features)
    # ============================================================================
    # User & Role Management (2 features)
    ADMIN_USERS = "admin_users"  # P0 - Admin user management
    ADMIN_ROLES = "admin_roles"  # P0 - Role-based access control

    # System Configuration (2 features)
    ADMIN_CONFIG = "admin_config"  # P1 - System configuration
    ADMIN_FEATURE_FLAGS = "admin_feature_flags"  # P1 - Feature flag UI control

    # Audit & Logging (1 feature)
    AUDIT_LOGS = "audit_logs"  # P1 - Audit log system

    # Admin Overrides & Operations (5 features)
    ADMIN_BOOKING_OVERRIDE = "admin_booking_override"  # P1 - Override booking rules
    ADMIN_CUSTOMER_MERGE = "admin_customer_merge"  # P1 - Merge customers (admin)
    ADMIN_BULK_OPERATIONS = "admin_bulk_operations"  # P1 - Bulk operations
    ADMIN_REPORTS = "admin_reports"  # P1 - Report generation
    ADMIN_NOTIFICATIONS = "admin_notifications"  # P1 - Notification settings

    # Template & Integration Management (6 features)
    ADMIN_EMAIL_TEMPLATES = "admin_email_templates"  # P2 - Email template management
    ADMIN_SMS_TEMPLATES = "admin_sms_templates"  # P2 - SMS template management
    ADMIN_INTEGRATION_STATUS = "admin_integration_status"  # P2 - Integration health
    ADMIN_API_KEYS = "admin_api_keys"  # P2 - API key management
    ADMIN_RATE_LIMITS = "admin_rate_limits"  # P2 - Rate limit configuration
    ADMIN_CACHE = "admin_cache"  # P2 - Cache management

    # System Maintenance & Security (6 features)
    ADMIN_DB_MAINTENANCE = "admin_db_maintenance"  # P2 - Database maintenance
    ADMIN_BACKUP_RESTORE = "admin_backup_restore"  # P2 - Backup/restore
    ADMIN_SECURITY = "admin_security"  # P2 - Security settings
    ADMIN_COMPLIANCE = "admin_compliance"  # P2 - Compliance reports
    ADMIN_DATA_EXPORT = "admin_data_export"  # P2 - Data export
    ADMIN_DASHBOARD = "admin_dashboard"  # P2 - Dashboard widgets API

    # ============================================================================
    # PAYMENT PROCESSING FLAGS (14 features)
    # ============================================================================
    # Deposit API (5 features)
    DEPOSIT_API = "deposit_api"  # P0 - Deposit CRUD REST API
    DEPOSIT_CREATE = "deposit_create"  # P0 - Create deposits
    DEPOSIT_LIST = "deposit_list"  # P0 - List deposits
    DEPOSIT_CONFIRM = "deposit_confirm"  # P0 - Confirm deposits
    DEPOSIT_CANCEL = "deposit_cancel"  # P0 - Cancel/refund deposits

    # Payment History & Reports (2 features)
    PAYMENT_HISTORY = "payment_history"  # P1 - Payment history
    PAYMENT_REPORTS = "payment_reports"  # P1 - Payment reports

    # Payment Disputes & Reconciliation (3 features)
    PAYMENT_DISPUTES = "payment_disputes"  # P2 - Stripe dispute handling
    PAYMENT_RECONCILIATION = "payment_reconciliation"  # P2 - Payment reconciliation
    PAYMENT_BULK = "payment_bulk"  # P2 - Bulk payment operations

    # Advanced Payment Features (3 features)
    PAYMENT_SUBSCRIPTIONS = "payment_subscriptions"  # P3 - Recurring subscriptions
    PAYMENT_INSTALLMENTS = "payment_installments"  # P3 - Payment plans
    PAYMENT_WEBHOOKS_ENHANCED = "payment_webhooks_enhanced"  # P3 - Enhanced webhooks

    # ============================================================================
    # COMMUNICATIONS FLAGS (9 features)
    # ============================================================================
    # Direct Communications (2 features)
    DIRECT_SMS = "direct_sms"  # P0 - Direct SMS API
    DIRECT_EMAIL = "direct_email"  # P0 - Direct email API

    # Template Management (1 feature)
    COMMUNICATION_TEMPLATES = "communication_templates"  # P1 - Template management

    # Contact List & Opt-Out (2 features)
    CONTACT_LISTS = "contact_lists"  # P1 - Contact list management
    OPT_OUT_MANAGEMENT = "opt_out_management"  # P1 - Opt-out management

    # Advanced Communication Features (4 features)
    COMMUNICATION_SCHEDULING = "communication_scheduling"  # P2 - Schedule messages
    COMMUNICATION_PERSONALIZATION = (
        "communication_personalization"  # P2 - Dynamic personalization
    )
    COMMUNICATION_AB_TESTING = "communication_ab_testing"  # P2 - A/B testing
    COMMUNICATION_ANALYTICS = "communication_analytics"  # P2 - Advanced analytics


class FeatureFlagConfig(BaseSettings):
    """
    Feature flag configuration with environment variable support
    All flags default to False in production
    Override via environment variables: FEATURE_FLAG_<NAME>=true
    """

    # ============================================================================
    # BOOKING SYSTEM FLAGS
    # ============================================================================
    FEATURE_FLAG_BOOKING_REMINDERS: bool = False
    FEATURE_FLAG_MULTI_LOCATION: bool = False
    FEATURE_FLAG_RECURRING_BOOKINGS: bool = False
    FEATURE_FLAG_BOOKING_WAITLIST: bool = False
    FEATURE_FLAG_GROUP_RESERVATIONS: bool = False

    # ============================================================================
    # CUSTOMER MANAGEMENT FLAGS
    # ============================================================================
    FEATURE_FLAG_CUSTOMER_MERGE: bool = False
    FEATURE_FLAG_CUSTOMER_EXPORT: bool = False
    FEATURE_FLAG_CUSTOMER_PREFERENCES: bool = False
    FEATURE_FLAG_LOYALTY_POINTS: bool = False
    FEATURE_FLAG_REFERRAL_TRACKING: bool = False
    FEATURE_FLAG_CUSTOMER_FEEDBACK_HISTORY: bool = False

    # ============================================================================
    # AI SERVICES FLAGS
    # ============================================================================
    FEATURE_FLAG_VOICE_AI: bool = False
    FEATURE_FLAG_VOICE_TRANSCRIPTION: bool = False
    FEATURE_FLAG_VOICE_SENTIMENT: bool = False
    FEATURE_FLAG_VOICE_TRANSFER: bool = False
    FEATURE_FLAG_VOICE_IVR: bool = False
    FEATURE_FLAG_AI_EMBEDDINGS: bool = False
    FEATURE_FLAG_EMBEDDINGS_SEARCH: bool = False
    FEATURE_FLAG_EMBEDDINGS_SIMILARITY: bool = False
    FEATURE_FLAG_EMBEDDINGS_CLUSTERING: bool = False
    FEATURE_FLAG_ML_TRAINING: bool = False
    FEATURE_FLAG_ML_FINE_TUNING: bool = False
    FEATURE_FLAG_ML_EVALUATION: bool = False
    FEATURE_FLAG_ML_BATCH_PROCESSING: bool = False
    FEATURE_FLAG_AI_CACHING: bool = False
    FEATURE_FLAG_AI_RATE_LIMITING: bool = False
    FEATURE_FLAG_AI_COST_TRACKING: bool = False
    FEATURE_FLAG_AI_MODEL_SWITCHING: bool = False
    FEATURE_FLAG_AI_FALLBACK: bool = False
    FEATURE_FLAG_AI_CONTEXT_MANAGEMENT: bool = False
    FEATURE_FLAG_AI_PROMPT_TEMPLATES: bool = False

    # ============================================================================
    # ADMIN OPERATIONS FLAGS
    # ============================================================================
    FEATURE_FLAG_ADMIN_USERS: bool = False
    FEATURE_FLAG_ADMIN_ROLES: bool = False
    FEATURE_FLAG_ADMIN_CONFIG: bool = False
    FEATURE_FLAG_ADMIN_FEATURE_FLAGS: bool = False
    FEATURE_FLAG_AUDIT_LOGS: bool = False
    FEATURE_FLAG_ADMIN_BOOKING_OVERRIDE: bool = False
    FEATURE_FLAG_ADMIN_CUSTOMER_MERGE: bool = False
    FEATURE_FLAG_ADMIN_BULK_OPERATIONS: bool = False
    FEATURE_FLAG_ADMIN_REPORTS: bool = False
    FEATURE_FLAG_ADMIN_NOTIFICATIONS: bool = False
    FEATURE_FLAG_ADMIN_EMAIL_TEMPLATES: bool = False
    FEATURE_FLAG_ADMIN_SMS_TEMPLATES: bool = False
    FEATURE_FLAG_ADMIN_INTEGRATION_STATUS: bool = False
    FEATURE_FLAG_ADMIN_API_KEYS: bool = False
    FEATURE_FLAG_ADMIN_RATE_LIMITS: bool = False
    FEATURE_FLAG_ADMIN_CACHE: bool = False
    FEATURE_FLAG_ADMIN_DB_MAINTENANCE: bool = False
    FEATURE_FLAG_ADMIN_BACKUP_RESTORE: bool = False
    FEATURE_FLAG_ADMIN_SECURITY: bool = False
    FEATURE_FLAG_ADMIN_COMPLIANCE: bool = False
    FEATURE_FLAG_ADMIN_DATA_EXPORT: bool = False
    FEATURE_FLAG_ADMIN_DASHBOARD: bool = False

    # ============================================================================
    # PAYMENT PROCESSING FLAGS
    # ============================================================================
    FEATURE_FLAG_DEPOSIT_API: bool = False
    FEATURE_FLAG_DEPOSIT_CREATE: bool = False
    FEATURE_FLAG_DEPOSIT_LIST: bool = False
    FEATURE_FLAG_DEPOSIT_CONFIRM: bool = False
    FEATURE_FLAG_DEPOSIT_CANCEL: bool = False
    FEATURE_FLAG_PAYMENT_HISTORY: bool = False
    FEATURE_FLAG_PAYMENT_REPORTS: bool = False
    FEATURE_FLAG_PLAID_INTEGRATION: bool = False
    FEATURE_FLAG_PAYMENT_DISPUTES: bool = False
    FEATURE_FLAG_PAYMENT_RECONCILIATION: bool = False
    FEATURE_FLAG_PAYMENT_BULK: bool = False
    FEATURE_FLAG_PAYMENT_SUBSCRIPTIONS: bool = False
    FEATURE_FLAG_PAYMENT_INSTALLMENTS: bool = False
    FEATURE_FLAG_PAYMENT_WEBHOOKS_ENHANCED: bool = False

    # ============================================================================
    # COMMUNICATIONS FLAGS
    # ============================================================================
    FEATURE_FLAG_DIRECT_SMS: bool = False
    FEATURE_FLAG_DIRECT_EMAIL: bool = False
    FEATURE_FLAG_COMMUNICATION_TEMPLATES: bool = False
    FEATURE_FLAG_CONTACT_LISTS: bool = False
    FEATURE_FLAG_OPT_OUT_MANAGEMENT: bool = False
    FEATURE_FLAG_COMMUNICATION_SCHEDULING: bool = False
    FEATURE_FLAG_COMMUNICATION_PERSONALIZATION: bool = False
    FEATURE_FLAG_COMMUNICATION_AB_TESTING: bool = False
    FEATURE_FLAG_COMMUNICATION_ANALYTICS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global feature flag instance
feature_flags = FeatureFlagConfig()


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """
    Check if a feature flag is enabled

    Args:
        flag: FeatureFlag enum value

    Returns:
        bool: True if feature is enabled, False otherwise

    Example:
        if is_feature_enabled(FeatureFlag.BOOKING_REMINDERS):
            # Use new reminder system
        else:
            # Fall back to legacy behavior
    """
    flag_name = f"FEATURE_FLAG_{flag.value.upper()}"
    return getattr(feature_flags, flag_name, False)


def get_enabled_features() -> dict[str, bool]:
    """
    Get all feature flags and their current status

    Returns:
        dict: Dictionary of all feature flags and their enabled state

    Example:
        {
            "BOOKING_REMINDERS": False,
            "MULTI_LOCATION": True,
            ...
        }
    """
    return {flag.value: is_feature_enabled(flag) for flag in FeatureFlag}


def require_feature(flag: FeatureFlag):
    """
    Decorator to require a feature flag to be enabled
    Raises HTTP 501 Not Implemented if flag is disabled

    Args:
        flag: FeatureFlag enum value

    Example:
        @router.post("/reminders")
        @require_feature(FeatureFlag.BOOKING_REMINDERS)
        async def create_reminder(...):
            # This endpoint only works if BOOKING_REMINDERS flag is ON
    """
    from functools import wraps

    from fastapi import HTTPException, status

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_feature_enabled(flag):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=f"Feature '{flag.value}' is not enabled. "
                    f"Contact administrator to enable this feature.",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
