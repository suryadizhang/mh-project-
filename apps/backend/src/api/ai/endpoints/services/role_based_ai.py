"""
Role-Based AI Service for MyHibachi
Implements scope separation between customer and admin AI functionality
"""

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles for AI scope separation"""

    CUSTOMER = "customer"
    ADMIN = "admin"
    STAFF = "staff"
    SUPER_ADMIN = "super_admin"


class AICapability(str, Enum):
    """AI capabilities that can be granted to different roles"""

    # Customer capabilities (booking-only)
    VIEW_BOOKING = "view_booking"
    CREATE_BOOKING = "create_booking"
    MODIFY_BOOKING = "modify_booking"
    CANCEL_BOOKING = "cancel_booking"
    MENU_INQUIRY = "menu_inquiry"
    RESTAURANT_INFO = "restaurant_info"

    # Admin capabilities (full management)
    USER_MANAGEMENT = "user_management"
    STAFF_MANAGEMENT = "staff_management"
    BOOKING_MANAGEMENT = "booking_management"
    MENU_MANAGEMENT = "menu_management"
    RESTAURANT_OPERATIONS = "restaurant_operations"
    FINANCIAL_OVERSIGHT = "financial_oversight"
    SYSTEM_CONFIGURATION = "system_configuration"
    ANALYTICS_ACCESS = "analytics_access"

    # Staff guidance capabilities
    STAFF_GUIDANCE = "staff_guidance"
    OPERATIONAL_ASSISTANCE = "operational_assistance"
    WORKFLOW_HELP = "workflow_help"


class RoleBasedAIService:
    """AI service with role-based access control"""

    def __init__(self):
        # Define capabilities for each role
        self.role_capabilities = {
            UserRole.CUSTOMER: [
                AICapability.VIEW_BOOKING,
                AICapability.CREATE_BOOKING,
                AICapability.MODIFY_BOOKING,
                AICapability.CANCEL_BOOKING,
                AICapability.MENU_INQUIRY,
                AICapability.RESTAURANT_INFO,
            ],
            UserRole.ADMIN: [
                # Admin has all capabilities
                *list(AICapability),
            ],
            UserRole.STAFF: [
                AICapability.VIEW_BOOKING,
                AICapability.BOOKING_MANAGEMENT,
                AICapability.MENU_INQUIRY,
                AICapability.RESTAURANT_INFO,
                AICapability.STAFF_GUIDANCE,
                AICapability.OPERATIONAL_ASSISTANCE,
                AICapability.WORKFLOW_HELP,
            ],
            UserRole.SUPER_ADMIN: [
                # Super admin has all capabilities
                *list(AICapability),
            ],
        }

        # Define restricted admin functions for customer
        self.customer_restrictions = [
            "admin",
            "management",
            "staff",
            "employee",
            "configure",
            "settings",
            "analytics",
            "financial",
            "revenue",
            "profit",
            "user_data",
            "private",
            "internal",
            "backend",
            "database",
        ]

    def get_user_capabilities(self, role: UserRole) -> list[AICapability]:
        """Get list of capabilities for a given role"""
        return self.role_capabilities.get(role, [])

    def can_perform_action(self, role: UserRole, capability: AICapability) -> bool:
        """Check if a role can perform a specific action"""
        user_capabilities = self.get_user_capabilities(role)
        return capability in user_capabilities

    def filter_ai_response(self, role: UserRole, response: str, context: dict[str, Any]) -> str:
        """Filter AI response based on user role to prevent information leakage"""
        if role == UserRole.CUSTOMER:
            return self._filter_customer_response(response)
        elif role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            return response  # Admin gets full response
        else:
            return self._filter_staff_response(response)

    def _filter_customer_response(self, response: str) -> str:
        """Filter response for customer to remove admin-only information"""
        response_lower = response.lower()

        # Check for restricted admin content
        for restriction in self.customer_restrictions:
            if restriction in response_lower:
                logger.warning(f"Filtered admin content from customer response: {restriction}")
                # Replace with customer-appropriate message
                response = "I can help you with bookings and restaurant information. For other inquiries, please contact our staff directly."
                break

        return response

    def _filter_staff_response(self, response: str) -> str:
        """Filter response for staff to remove super-admin content"""
        # Staff can see most content except financial and system configuration
        sensitive_admin_content = [
            "financial",
            "profit",
            "revenue",
            "system_configuration",
            "database",
        ]
        response_lower = response.lower()

        for content in sensitive_admin_content:
            if content in response_lower:
                response = "This information requires admin access. Please contact your manager."
                break

        return response

    def get_context_prompt(self, role: UserRole, conversation_context: dict[str, Any]) -> str:
        """Generate role-specific context prompt for AI"""
        base_context = f"You are MyHibachi's AI assistant. The user role is: {role.value}."

        if role == UserRole.CUSTOMER:
            return (
                base_context
                + """

You can ONLY help with:
- Viewing, creating, modifying, and canceling bookings
- Menu inquiries and restaurant information
- General customer service questions

You CANNOT:
- Access admin functions
- Manage users or staff
- View internal operations
- Access financial information
- Modify system settings
- Provide admin guidance

Always focus on booking and customer service. If asked about admin functions, politely redirect to contacting staff.
"""
            )

        elif role == UserRole.ADMIN:
            return (
                base_context
                + """

As an admin, you have access to:
- Complete restaurant management functions
- User and staff management
- Booking management and operations
- Financial oversight and analytics
- System configuration
- Staff guidance and operational assistance

Your primary role is to help manage the restaurant efficiently and guide staff operations.
"""
            )

        elif role == UserRole.STAFF:
            return (
                base_context
                + """

As staff, you can access:
- Booking management and customer service
- Operational guidance and workflow help
- Menu information and restaurant details
- Staff-level assistance

You cannot access financial information or system configuration.
"""
            )

        else:
            return base_context + " You have full system access."

    def validate_request(self, role: UserRole, request_data: dict[str, Any]) -> dict[str, Any]:
        """Validate and filter request data based on role"""
        validation_result = {
            "valid": True,
            "filtered_data": request_data.copy(),
            "warnings": [],
            "errors": [],
        }

        # Check for unauthorized access attempts
        if role == UserRole.CUSTOMER:
            unauthorized_keywords = ["admin", "manage_users", "financial", "analytics", "system"]

            message = request_data.get("message", "").lower()
            for keyword in unauthorized_keywords:
                if keyword in message:
                    validation_result["warnings"].append(
                        f"Customer attempted to access admin function: {keyword}"
                    )
                    # Still allow the request but will be filtered in response

        return validation_result

    def get_booking_capabilities(self, role: UserRole) -> dict[str, bool]:
        """Get specific booking capabilities for a role"""
        capabilities = {
            "can_view_booking": self.can_perform_action(role, AICapability.VIEW_BOOKING),
            "can_create_booking": self.can_perform_action(role, AICapability.CREATE_BOOKING),
            "can_modify_booking": self.can_perform_action(role, AICapability.MODIFY_BOOKING),
            "can_cancel_booking": self.can_perform_action(role, AICapability.CANCEL_BOOKING),
            "can_manage_all_bookings": self.can_perform_action(
                role, AICapability.BOOKING_MANAGEMENT
            ),
        }

        return capabilities

    def get_management_capabilities(self, role: UserRole) -> dict[str, bool]:
        """Get specific management capabilities for a role"""
        capabilities = {
            "can_manage_users": self.can_perform_action(role, AICapability.USER_MANAGEMENT),
            "can_manage_staff": self.can_perform_action(role, AICapability.STAFF_MANAGEMENT),
            "can_manage_menu": self.can_perform_action(role, AICapability.MENU_MANAGEMENT),
            "can_view_analytics": self.can_perform_action(role, AICapability.ANALYTICS_ACCESS),
            "can_manage_operations": self.can_perform_action(
                role, AICapability.RESTAURANT_OPERATIONS
            ),
            "can_configure_system": self.can_perform_action(
                role, AICapability.SYSTEM_CONFIGURATION
            ),
        }

        return capabilities

    def log_ai_interaction(self, role: UserRole, request: dict[str, Any], response: str):
        """Log AI interactions for security auditing"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role.value,
            "request_message": request.get("message", "")[:100],  # Truncate for privacy
            "response_length": len(response),
            "conversation_id": request.get("conversation_id"),
            "user_id": request.get("user_id"),
        }

        logger.info(f"AI Interaction: {log_data}")

        # Additional security logging for sensitive operations
        if role == UserRole.CUSTOMER and any(
            word in request.get("message", "").lower() for word in self.customer_restrictions
        ):
            logger.warning(
                f"Customer attempted restricted access: {request.get('message', '')[:50]}"
            )


# Global instance
role_based_ai = RoleBasedAIService()


def get_role_from_context(context: dict[str, Any]) -> UserRole:
    """Extract user role from request context"""
    # Default logic - you can enhance based on authentication
    channel = context.get("channel", "web")
    user_type = context.get("user_type", "customer")

    if channel == "admin" or user_type == "admin":
        return UserRole.ADMIN
    elif user_type == "staff":
        return UserRole.STAFF
    else:
        return UserRole.CUSTOMER


def create_role_aware_response(
    role: UserRole, original_response: str, context: dict[str, Any]
) -> dict[str, Any]:
    """Create a role-aware AI response with appropriate filtering"""
    filtered_response = role_based_ai.filter_ai_response(role, original_response, context)

    # Add role-specific capabilities to response metadata
    booking_caps = role_based_ai.get_booking_capabilities(role)
    management_caps = (
        role_based_ai.get_management_capabilities(role) if role != UserRole.CUSTOMER else {}
    )

    return {
        "content": filtered_response,
        "role": role.value,
        "capabilities": {"booking": booking_caps, "management": management_caps},
        "metadata": {
            "filtered": filtered_response != original_response,
            "role_restricted": role == UserRole.CUSTOMER,
        },
    }
