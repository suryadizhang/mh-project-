"""
Admin Management AI Functions
Handles all admin management AI interactions with full system access
"""

from enum import Enum
import logging
from typing import Any

from api.ai.endpoints.services.openai_service import openai_service
from api.ai.endpoints.services.role_based_ai import UserRole

logger = logging.getLogger(__name__)


class AdminFunction(Enum):
    """Available admin management functions"""

    USER_MANAGEMENT = "user_management"
    BOOKING_MANAGEMENT = "booking_management"
    STAFF_MANAGEMENT = "staff_management"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"
    SYSTEM_CONFIG = "system_config"
    TRAINING = "training"
    SUPPORT = "support"


class AdminManagementAI:
    """AI service for admin management operations with full system access"""

    def __init__(self):
        self.admin_capabilities = {
            AdminFunction.USER_MANAGEMENT: [
                "view_all_users",
                "create_user",
                "update_user",
                "deactivate_user",
                "reset_password",
                "view_user_activity",
                "manage_permissions",
            ],
            AdminFunction.BOOKING_MANAGEMENT: [
                "view_all_bookings",
                "create_booking",
                "modify_any_booking",
                "cancel_any_booking",
                "view_booking_analytics",
                "manage_availability",
                "blacklist_management",
                "waitlist_management",
            ],
            AdminFunction.STAFF_MANAGEMENT: [
                "view_staff",
                "add_staff",
                "update_staff",
                "staff_schedules",
                "staff_performance",
                "staff_training",
                "access_control",
            ],
            AdminFunction.OPERATIONS: [
                "kitchen_management",
                "table_management",
                "inventory_control",
                "vendor_management",
                "equipment_monitoring",
                "maintenance_logs",
            ],
            AdminFunction.ANALYTICS: [
                "revenue_reports",
                "customer_analytics",
                "staff_analytics",
                "operational_metrics",
                "trend_analysis",
                "forecasting",
            ],
            AdminFunction.SYSTEM_CONFIG: [
                "restaurant_settings",
                "menu_management",
                "pricing_control",
                "business_hours",
                "holiday_management",
                "notification_settings",
            ],
        }

    async def process_admin_message(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process admin message using OpenAI for natural admin assistance"""
        try:
            logger.info(f"Admin AI processing message: {message[:50]}...")

            user_role = context.get("user_role", UserRole.ADMIN)

            # Verify admin access
            if not self._verify_admin_access(user_role):
                return self._create_access_denied_response()

            # Use OpenAI for natural admin conversation
            if openai_service.client:
                logger.info("Admin AI using OpenAI service")

                # Create context for OpenAI
                system_prompt = """You are a helpful AI assistant for MyHibachi restaurant admin users. You can answer any questions naturally and conversationally, including general knowledge, math, or any topic the user asks about.

When asked about MyHibachi-specific tasks, I can help with:

🏢 **Admin Functions**:
• User & Staff Management
• Booking Operations
• Analytics & Reports
• System Configuration
• Operations Support

📊 **Quick Actions**:
• View booking statistics
• Manage customer accounts
• Staff scheduling assistance
• Generate reports
• System settings help

**Guidelines**:
- Answer all questions naturally and helpfully
- Be professional but conversational
- For MyHibachi tasks, be security-conscious with sensitive data
- Provide clear, accurate information
- Use emojis sparingly for visual appeal

You should respond to ANY question the user asks, not just MyHibachi-related ones."""

                ai_response = await openai_service.generate_response(
                    message=message,
                    context={
                        "system_prompt": system_prompt,
                        "user_role": "admin",
                        "service_type": "admin_management",
                        **context,
                    },
                )

                logger.info(f"Admin AI received OpenAI response: {type(ai_response)}")
                logger.info(
                    f"🔧 Admin AI response content: {ai_response[:2] if isinstance(ai_response, tuple) else str(ai_response)[:100]}"
                )

                # Handle tuple response format from OpenAI service
                if isinstance(ai_response, tuple):
                    response_text = ai_response[0]
                    confidence = ai_response[1] if len(ai_response) > 1 else 0.9
                    logger.info(f"🔧 Admin AI final response: {response_text[:100]}...")
                else:
                    response_text = ai_response
                    confidence = 0.9

                return {
                    "response": response_text,
                    "intent": "admin_management",
                    "confidence": confidence,
                }
            else:
                logger.warning("Admin AI OpenAI service not available, using fallback")
                # Fallback to simple responses if OpenAI not available
                return self._get_admin_fallback_response(message, context)

        except Exception as e:
            logger.exception(f"Error processing admin message: {e}")
            return {
                "response": "I'm experiencing technical difficulties. Please contact our team directly for help.",
                "intent": "error",
                "confidence": 0.0,
            }

    def _get_admin_fallback_response(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Provide fallback response for admin when OpenAI is not available"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["booking", "reservation"]):
            return {
                "response": """Hello! I'm your AI management assistant.

I can help you with:

• **User & Staff Management** - Manage accounts and permissions
• **Booking Operations** - Handle reservations and scheduling
• **Analytics & Reports** - View performance metrics
• **System Configuration** - Manage settings and preferences
• **Operations Support** - Kitchen, inventory, and maintenance

How can I assist you with managing MyHibachi today?""",
                "intent": "booking_management",
                "confidence": 0.8,
            }
        elif any(word in message_lower for word in ["user", "customer", "staff"]):
            return {
                "response": """I can help you manage users and staff.

What would you like to do?

• **View user accounts** - See all customer profiles
• **Manage staff schedules** - Create and modify work schedules
• **Update permissions** - Modify user access levels
• **Review user activity** - Check account usage and behavior

Please let me know which option interests you!""",
                "intent": "user_management",
                "confidence": 0.8,
            }
        else:
            return {
                "response": """Hello! I'm your AI management assistant.

I can help you with:

• **User & Staff Management** - Manage accounts and permissions
• **Booking Operations** - Handle reservations and scheduling
• **Analytics & Reports** - View performance metrics
• **System Configuration** - Manage settings and preferences
• **Operations Support** - Kitchen, inventory, and maintenance

How can I assist you with managing MyHibachi today?""",
                "intent": "general_admin",
                "confidence": 0.7,
            }

    def _verify_admin_access(self, user_role: UserRole) -> bool:
        """Verify user has admin access"""
        admin_roles = {UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF}
        return user_role in admin_roles

    def _identify_admin_function(self, message: str) -> AdminFunction | None:
        """Identify the admin function from the message"""
        function_keywords = {
            AdminFunction.USER_MANAGEMENT: [
                "user",
                "customer",
                "account",
                "profile",
                "permission",
                "access",
            ],
            AdminFunction.BOOKING_MANAGEMENT: [
                "booking",
                "reservation",
                "table",
                "availability",
                "waitlist",
            ],
            AdminFunction.STAFF_MANAGEMENT: [
                "staff",
                "employee",
                "team",
                "schedule",
                "shift",
                "training",
            ],
            AdminFunction.OPERATIONS: [
                "kitchen",
                "inventory",
                "equipment",
                "maintenance",
                "vendor",
            ],
            AdminFunction.ANALYTICS: [
                "report",
                "analytics",
                "metric",
                "revenue",
                "performance",
                "trend",
            ],
            AdminFunction.SYSTEM_CONFIG: ["setting", "config", "menu", "price", "hours", "holiday"],
        }

        for function, keywords in function_keywords.items():
            if any(keyword in message for keyword in keywords):
                return function

        return None

    async def _handle_admin_function(
        self, function: AdminFunction, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle specific admin function requests"""
        handlers = {
            AdminFunction.USER_MANAGEMENT: self._handle_user_management,
            AdminFunction.BOOKING_MANAGEMENT: self._handle_booking_management,
            AdminFunction.STAFF_MANAGEMENT: self._handle_staff_management,
            AdminFunction.OPERATIONS: self._handle_operations,
            AdminFunction.ANALYTICS: self._handle_analytics,
            AdminFunction.SYSTEM_CONFIG: self._handle_system_config,
        }

        handler = handlers.get(function)
        if handler:
            return await handler(message, context)
        else:
            return self._create_function_not_implemented_response(function)

    async def _handle_user_management(
        self, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle user management requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["view", "show", "list", "all users"]):
            return await self._show_user_overview()
        elif any(word in message_lower for word in ["create", "add", "new user"]):
            return await self._create_user_assistant(message, context)
        elif any(word in message_lower for word in ["update", "modify", "edit"]):
            return await self._update_user_assistant(message, context)
        elif any(word in message_lower for word in ["deactivate", "disable", "block"]):
            return await self._deactivate_user_assistant(message, context)
        elif any(word in message_lower for word in ["reset password", "password reset"]):
            return await self._reset_password_assistant(message, context)
        else:
            return self._create_user_management_menu()

    async def _handle_booking_management(
        self, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle booking management requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["view", "show", "list", "all bookings"]):
            return await self._show_booking_overview()
        elif any(word in message_lower for word in ["create", "add", "new booking"]):
            return await self._create_admin_booking(message, context)
        elif any(word in message_lower for word in ["modify", "update", "change"]):
            return await self._modify_booking_admin(message, context)
        elif any(word in message_lower for word in ["cancel", "delete", "remove"]):
            return await self._cancel_booking_admin(message, context)
        elif any(word in message_lower for word in ["analytics", "report", "stats"]):
            return await self._booking_analytics()
        elif any(word in message_lower for word in ["availability", "schedule", "calendar"]):
            return await self._manage_availability()
        else:
            return self._create_booking_management_menu()

    async def _handle_staff_management(
        self, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle staff management requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["view", "show", "list", "all staff"]):
            return await self._show_staff_overview()
        elif any(word in message_lower for word in ["add", "create", "new staff"]):
            return await self._add_staff_assistant(message, context)
        elif any(word in message_lower for word in ["schedule", "shift", "roster"]):
            return await self._manage_staff_schedules()
        elif any(word in message_lower for word in ["performance", "review", "evaluation"]):
            return await self._staff_performance_review()
        elif any(word in message_lower for word in ["training", "onboard", "education"]):
            return await self._staff_training_assistant()
        else:
            return self._create_staff_management_menu()

    async def _handle_operations(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Handle operations management requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["kitchen", "food", "prep"]):
            return await self._kitchen_management()
        elif any(word in message_lower for word in ["inventory", "stock", "supplies"]):
            return await self._inventory_management()
        elif any(word in message_lower for word in ["equipment", "maintenance", "repair"]):
            return await self._equipment_management()
        elif any(word in message_lower for word in ["vendor", "supplier", "order"]):
            return await self._vendor_management()
        else:
            return self._create_operations_menu()

    async def _handle_analytics(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Handle analytics and reporting requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["revenue", "sales", "financial"]):
            return await self._revenue_analytics()
        elif any(word in message_lower for word in ["customer", "guest", "patron"]):
            return await self._customer_analytics()
        elif any(word in message_lower for word in ["staff", "employee", "team"]):
            return await self._staff_analytics()
        elif any(word in message_lower for word in ["operational", "operation", "efficiency"]):
            return await self._operational_metrics()
        else:
            return self._create_analytics_menu()

    async def _handle_system_config(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Handle system configuration requests"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["menu", "dish", "food"]):
            return await self._menu_management()
        elif any(word in message_lower for word in ["price", "pricing", "cost"]):
            return await self._pricing_management()
        elif any(word in message_lower for word in ["hours", "schedule", "operating"]):
            return await self._business_hours_management()
        elif any(word in message_lower for word in ["setting", "config", "preference"]):
            return await self._general_settings()
        else:
            return self._create_system_config_menu()

    # User Management Functions
    async def _show_user_overview(self) -> dict[str, Any]:
        """Show user overview with statistics"""
        mock_stats = {
            "total_users": 1247,
            "active_users": 1156,
            "new_this_month": 89,
            "vip_customers": 156,
        }

        response = f"""👥 **User Management Overview**

**User Statistics**:
• Total Users: {mock_stats['total_users']}
• Active Users: {mock_stats['active_users']}
• New This Month: {mock_stats['new_this_month']}
• VIP Customers: {mock_stats['vip_customers']}

**Recent Activity**:
• 23 new registrations this week
• 156 active bookings today
• 5 users requiring attention

**Quick Actions**:
• Create new user account
• View user details
• Reset user password
• Generate user report

What would you like to do?"""

        return {
            "function": "user_management",
            "action": "overview",
            "response": response,
            "data": mock_stats,
        }

    async def _create_user_assistant(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Assistant for creating new users"""
        response = """➕ **Create New User Account**

I can help you create a new user account. Please provide:

**Required Information**:
• Full Name
• Email Address
• Phone Number
• User Role (Customer, Staff, Admin)

**Optional Information**:
• Date of Birth
• Dietary Preferences
• VIP Status
• Special Notes

Please provide the user details, or I can guide you through step by step."""

        return {
            "function": "user_management",
            "action": "create_user",
            "response": response,
            "next_step": "collect_user_info",
        }

    # Booking Management Functions
    async def _show_booking_overview(self) -> dict[str, Any]:
        """Show booking overview with current status"""
        mock_data = {
            "today_bookings": 87,
            "pending_bookings": 12,
            "cancelled_today": 5,
            "no_shows": 2,
            "revenue_today": 12450.00,
        }

        response = f"""📅 **Booking Management Overview**

**Today's Statistics**:
• Total Bookings: {mock_data['today_bookings']}
• Pending Confirmations: {mock_data['pending_bookings']}
• Cancelled Today: {mock_data['cancelled_today']}
• No-Shows: {mock_data['no_shows']}
• Revenue Today: ${mock_data['revenue_today']:,.2f}

**Upcoming Highlights**:
• Next 2 hours: 23 reservations
• Peak time (7-8 PM): 34 bookings
• Large parties (8+): 6 bookings

**Quick Actions**:
• View live booking status
• Modify reservation
• Check availability
• Generate booking report

What would you like to manage?"""

        return {
            "function": "booking_management",
            "action": "overview",
            "response": response,
            "data": mock_data,
        }

    # Staff Management Functions
    async def _show_staff_overview(self) -> dict[str, Any]:
        """Show staff overview and management options"""
        mock_data = {"total_staff": 23, "on_duty": 12, "scheduled_today": 18, "on_leave": 2}

        response = f"""👨‍💼 **Staff Management Overview**

**Staff Statistics**:
• Total Staff: {mock_data['total_staff']}
• Currently On Duty: {mock_data['on_duty']}
• Scheduled Today: {mock_data['scheduled_today']}
• On Leave: {mock_data['on_leave']}

**Today's Schedule**:
• Morning Shift: 8 staff members
• Evening Shift: 10 staff members
• Kitchen Staff: 6 active
• Front of House: 6 active

**Quick Actions**:
• View staff schedules
• Add new staff member
• Manage shifts
• Performance reviews
• Training assignments

What would you like to manage?"""

        return {
            "function": "staff_management",
            "action": "overview",
            "response": response,
            "data": mock_data,
        }

    # Analytics Functions
    async def _revenue_analytics(self) -> dict[str, Any]:
        """Show revenue analytics and insights"""
        mock_data = {
            "daily_revenue": 12450.00,
            "monthly_revenue": 287500.00,
            "growth_rate": 15.2,
            "avg_order_value": 65.50,
        }

        response = f"""💰 **Revenue Analytics**

**Current Performance**:
• Today's Revenue: ${mock_data['daily_revenue']:,.2f}
• Monthly Revenue: ${mock_data['monthly_revenue']:,.2f}
• Growth Rate: +{mock_data['growth_rate']}%
• Average Order Value: ${mock_data['avg_order_value']:.2f}

**Insights**:
• Peak revenue time: 7-8 PM (31% of daily revenue)
• Best performing day: Saturday (+28% above average)
• Top revenue source: Hibachi dinners (45% of revenue)
• Reservation vs. Walk-in: 70% / 30%

**Recommendations**:
• Increase marketing for Tuesday/Wednesday
• Consider premium menu options
• Optimize table turnover during peak hours

Would you like detailed reports or specific analytics?"""

        return {
            "function": "analytics",
            "action": "revenue",
            "response": response,
            "data": mock_data,
        }

    async def _handle_general_admin_inquiry(
        self, message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle general admin inquiries"""
        return {
            "function": "general_admin",
            "response": """🎛️ **Admin Management Dashboard**

I can help you manage all aspects of MyHibachi:

**👥 User Management**
• View/create/modify customer accounts
• Manage user permissions and access
• Handle password resets and account issues

**📅 Booking Management**
• View all reservations and availability
• Create/modify/cancel any booking
• Manage waitlists and special requests

**👨‍💼 Staff Management**
• Manage staff schedules and shifts
• Track performance and training
• Handle staff onboarding and access

**🏪 Operations**
• Kitchen and inventory management
• Equipment monitoring and maintenance
• Vendor and supplier coordination

**📊 Analytics & Reports**
• Revenue and financial reporting
• Customer and operational analytics
• Performance metrics and insights

**⚙️ System Configuration**
• Menu and pricing management
• Business hours and holiday settings
• System preferences and notifications

What would you like to manage today?""",
            "next_action": "await_admin_selection",
        }

    # Menu Creation Helpers
    def _create_user_management_menu(self) -> dict[str, Any]:
        """Create user management menu"""
        return {
            "function": "user_management",
            "response": """👥 **User Management Options**

• **View Users** - Show all user accounts and statistics
• **Create User** - Add new customer or staff account
• **Update User** - Modify user information and preferences
• **Deactivate User** - Disable problematic accounts
• **Reset Password** - Help users with login issues
• **User Analytics** - View user behavior and engagement

What would you like to do?""",
            "menu_type": "user_management",
        }

    def _create_booking_management_menu(self) -> dict[str, Any]:
        """Create booking management menu"""
        return {
            "function": "booking_management",
            "response": """📅 **Booking Management Options**

• **View All Bookings** - See current reservations and status
• **Create Booking** - Make reservation for customer
• **Modify Booking** - Change any reservation details
• **Cancel Booking** - Cancel reservations with proper handling
• **Manage Availability** - Control table and time slot availability
• **Booking Analytics** - View reservation patterns and insights
• **Waitlist Management** - Handle waiting lists and notifications

What would you like to manage?""",
            "menu_type": "booking_management",
        }

    def _create_staff_management_menu(self) -> dict[str, Any]:
        """Create staff management menu"""
        return {
            "function": "staff_management",
            "response": """👨‍💼 **Staff Management Options**

• **View Staff** - See all staff members and current status
• **Add Staff** - Onboard new team members
• **Manage Schedules** - Create and modify work schedules
• **Performance Reviews** - Track and evaluate staff performance
• **Training Programs** - Assign and track training progress
• **Access Control** - Manage staff system permissions

What would you like to handle?""",
            "menu_type": "staff_management",
        }

    def _create_operations_menu(self) -> dict[str, Any]:
        """Create operations management menu"""
        return {
            "function": "operations",
            "response": """🏪 **Operations Management Options**

• **Kitchen Management** - Monitor food prep and cooking operations
• **Inventory Control** - Track stock levels and ordering
• **Equipment Monitoring** - Check equipment status and maintenance
• **Vendor Management** - Manage supplier relationships and orders
• **Table Management** - Optimize seating and table assignments
• **Quality Control** - Monitor service and food quality

What operational area needs attention?""",
            "menu_type": "operations",
        }

    def _create_analytics_menu(self) -> dict[str, Any]:
        """Create analytics menu"""
        return {
            "function": "analytics",
            "response": """📊 **Analytics & Reporting Options**

• **Revenue Reports** - Financial performance and trends
• **Customer Analytics** - Guest behavior and preferences
• **Staff Analytics** - Employee performance metrics
• **Operational Metrics** - Efficiency and quality measurements
• **Trend Analysis** - Identify patterns and opportunities
• **Forecasting** - Predict future performance and needs

Which analytics would you like to review?""",
            "menu_type": "analytics",
        }

    def _create_system_config_menu(self) -> dict[str, Any]:
        """Create system configuration menu"""
        return {
            "function": "system_config",
            "response": """⚙️ **System Configuration Options**

• **Menu Management** - Update dishes, descriptions, and categories
• **Pricing Control** - Manage prices and special offers
• **Business Hours** - Set operating hours and break times
• **Holiday Management** - Configure holiday hours and closures
• **Notification Settings** - Manage automated messages and alerts
• **General Settings** - System preferences and configurations

What would you like to configure?""",
            "menu_type": "system_config",
        }

    def _create_access_denied_response(self) -> dict[str, Any]:
        """Create access denied response"""
        return {
            "error": "access_denied",
            "response": "🚫 **Access Denied**\n\nYou don't have sufficient permissions to access admin management functions. Please contact your system administrator if you believe this is an error.",
            "required_role": "admin",
        }

    def _create_function_not_implemented_response(self, function: AdminFunction) -> dict[str, Any]:
        """Create response for not implemented functions"""
        return {
            "function": function.value,
            "response": f"⚠️ **Function Under Development**\n\nThe {function.value.replace('_', ' ').title()} function is currently being developed. Please check back soon or contact support for assistance.",
            "status": "not_implemented",
        }


# Global instance for admin management AI
admin_management_ai = AdminManagementAI()
