"""
Tool Registry Service
Manages agent-specific tool permissions and validation.
Ensures agents can only access tools appropriate for their role.
"""

from datetime import datetime
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolPermissionLevel(str, Enum):
    """Tool permission levels."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    FORBIDDEN = "forbidden"


class ToolCategory(str, Enum):
    """Tool categories for organization."""

    BOOKING = "booking"
    USER_MANAGEMENT = "user_management"
    ANALYTICS = "analytics"
    SYSTEM = "system"
    COMMUNICATION = "communication"
    FINANCIAL = "financial"


class ToolRegistryService:
    """Registry for tool permissions and validation."""

    def __init__(self):
        # Initialize tool definitions
        self.tools = self._initialize_tools()

        # Initialize agent permissions
        self.agent_permissions = self._initialize_agent_permissions()

    def _initialize_tools(self) -> dict[str, dict[str, Any]]:
        """Initialize tool definitions with metadata."""
        return {
            # Booking Tools
            "booking_search": {
                "category": ToolCategory.BOOKING,
                "description": "Search for existing bookings",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["date_range", "customer_id", "status"],
                "output": "List of matching bookings",
            },
            "booking_create": {
                "category": ToolCategory.BOOKING,
                "description": "Create a new booking",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["customer_info", "event_details", "menu_selection"],
                "output": "Booking confirmation",
            },
            "booking_modify": {
                "category": ToolCategory.BOOKING,
                "description": "Modify existing booking",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["booking_id", "modifications"],
                "output": "Updated booking details",
            },
            "booking_cancel": {
                "category": ToolCategory.BOOKING,
                "description": "Cancel a booking",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["booking_id", "reason", "refund_amount"],
                "output": "Cancellation confirmation",
            },
            "booking_admin": {
                "category": ToolCategory.BOOKING,
                "description": "Administrative booking operations",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["action", "booking_data", "admin_notes"],
                "output": "Administrative action result",
            },
            # Menu and Info Tools
            "menu_query": {
                "category": ToolCategory.BOOKING,
                "description": "Query menu options and pricing",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["category", "dietary_restrictions"],
                "output": "Menu items and details",
            },
            "restaurant_info": {
                "category": ToolCategory.BOOKING,
                "description": "Get restaurant information",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["info_type"],
                "output": "Restaurant information",
            },
            # User Management Tools
            "user_create": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Create new user account",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["user_data", "initial_permissions"],
                "output": "User account details",
            },
            "user_modify": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Modify user account",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["user_id", "modifications"],
                "output": "Updated user details",
            },
            "user_lookup": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Look up user information",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["user_identifier"],
                "output": "User information",
            },
            "customer_lookup": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Look up customer information",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["customer_identifier"],
                "output": "Customer information",
            },
            "customer_history": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Get customer booking history",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["customer_id", "date_range"],
                "output": "Customer history",
            },
            # Staff Management Tools
            "staff_manage": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Staff management operations",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["action", "staff_data"],
                "output": "Staff management result",
            },
            "shift_management": {
                "category": ToolCategory.USER_MANAGEMENT,
                "description": "Manage staff shifts and schedules",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["staff_id", "schedule_data"],
                "output": "Schedule confirmation",
            },
            "workflow_guide": {
                "category": ToolCategory.SYSTEM,
                "description": "Provide workflow guidance",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["workflow_type", "context"],
                "output": "Workflow instructions",
            },
            # Analytics Tools
            "analytics_query": {
                "category": ToolCategory.ANALYTICS,
                "description": "Query analytics data",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["metric", "date_range", "filters"],
                "output": "Analytics data",
            },
            "report_generator": {
                "category": ToolCategory.ANALYTICS,
                "description": "Generate business reports",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["report_type", "parameters"],
                "output": "Generated report",
            },
            "chart_creator": {
                "category": ToolCategory.ANALYTICS,
                "description": "Create data visualizations",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["data", "chart_type", "styling"],
                "output": "Chart visualization",
            },
            "data_export": {
                "category": ToolCategory.ANALYTICS,
                "description": "Export data to various formats",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["data_source", "format", "filters"],
                "output": "Exported data file",
            },
            "query_builder": {
                "category": ToolCategory.ANALYTICS,
                "description": "Build custom database queries",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["tables", "conditions", "aggregations"],
                "output": "Query results",
            },
            # Financial Tools
            "financial_reports": {
                "category": ToolCategory.FINANCIAL,
                "description": "Generate financial reports",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["report_type", "period"],
                "output": "Financial report",
            },
            # System Tools
            "system_config": {
                "category": ToolCategory.SYSTEM,
                "description": "Configure system settings",
                "required_permission": ToolPermissionLevel.ADMIN,
                "parameters": ["setting_category", "configuration"],
                "output": "Configuration status",
            },
            # Communication/Support Tools
            "ticket_create": {
                "category": ToolCategory.COMMUNICATION,
                "description": "Create support ticket",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["customer_id", "issue_details", "priority"],
                "output": "Ticket confirmation",
            },
            "escalation_route": {
                "category": ToolCategory.COMMUNICATION,
                "description": "Route escalation to appropriate team",
                "required_permission": ToolPermissionLevel.WRITE,
                "parameters": ["issue_type", "escalation_data"],
                "output": "Escalation confirmation",
            },
            "issue_tracking": {
                "category": ToolCategory.COMMUNICATION,
                "description": "Track issue resolution status",
                "required_permission": ToolPermissionLevel.READ,
                "parameters": ["ticket_id", "status_update"],
                "output": "Issue status",
            },
        }

    def _initialize_agent_permissions(self) -> dict[str, dict[str, ToolPermissionLevel]]:
        """Initialize agent-specific tool permissions."""
        return {
            "customer": {
                # Booking tools - read/write access for customer bookings
                "booking_search": ToolPermissionLevel.READ,
                "booking_create": ToolPermissionLevel.WRITE,
                "booking_modify": ToolPermissionLevel.WRITE,
                "booking_cancel": ToolPermissionLevel.WRITE,
                "booking_admin": ToolPermissionLevel.FORBIDDEN,
                # Menu and info - read access
                "menu_query": ToolPermissionLevel.READ,
                "restaurant_info": ToolPermissionLevel.READ,
                # User management - forbidden except own lookup
                "user_create": ToolPermissionLevel.FORBIDDEN,
                "user_modify": ToolPermissionLevel.FORBIDDEN,
                "user_lookup": ToolPermissionLevel.READ,  # Own info only
                "customer_lookup": ToolPermissionLevel.READ,  # Own info only
                "customer_history": ToolPermissionLevel.READ,  # Own history only
                # Staff management - forbidden
                "staff_manage": ToolPermissionLevel.FORBIDDEN,
                "shift_management": ToolPermissionLevel.FORBIDDEN,
                "workflow_guide": ToolPermissionLevel.FORBIDDEN,
                # Analytics - forbidden
                "analytics_query": ToolPermissionLevel.FORBIDDEN,
                "report_generator": ToolPermissionLevel.FORBIDDEN,
                "chart_creator": ToolPermissionLevel.FORBIDDEN,
                "data_export": ToolPermissionLevel.FORBIDDEN,
                "query_builder": ToolPermissionLevel.FORBIDDEN,
                # Financial - forbidden
                "financial_reports": ToolPermissionLevel.FORBIDDEN,
                # System - forbidden
                "system_config": ToolPermissionLevel.FORBIDDEN,
                # Communication - basic support
                "ticket_create": ToolPermissionLevel.WRITE,
                "escalation_route": ToolPermissionLevel.FORBIDDEN,
                "issue_tracking": ToolPermissionLevel.READ,
            },
            "admin": {
                # Full access to all tools
                **dict.fromkeys(
                    [
                        "booking_search",
                        "booking_create",
                        "booking_modify",
                        "booking_cancel",
                        "booking_admin",
                        "menu_query",
                        "restaurant_info",
                        "user_create",
                        "user_modify",
                        "user_lookup",
                        "customer_lookup",
                        "customer_history",
                        "staff_manage",
                        "shift_management",
                        "workflow_guide",
                        "analytics_query",
                        "report_generator",
                        "chart_creator",
                        "data_export",
                        "query_builder",
                        "financial_reports",
                        "system_config",
                        "ticket_create",
                        "escalation_route",
                        "issue_tracking",
                    ],
                    ToolPermissionLevel.ADMIN,
                )
            },
            "staff": {
                # Booking tools - read and basic write
                "booking_search": ToolPermissionLevel.READ,
                "booking_create": ToolPermissionLevel.WRITE,
                "booking_modify": ToolPermissionLevel.WRITE,
                "booking_cancel": ToolPermissionLevel.WRITE,
                "booking_admin": ToolPermissionLevel.FORBIDDEN,
                # Menu and info - read access
                "menu_query": ToolPermissionLevel.READ,
                "restaurant_info": ToolPermissionLevel.READ,
                # User management - limited access
                "user_create": ToolPermissionLevel.FORBIDDEN,
                "user_modify": ToolPermissionLevel.FORBIDDEN,
                "user_lookup": ToolPermissionLevel.READ,
                "customer_lookup": ToolPermissionLevel.READ,
                "customer_history": ToolPermissionLevel.READ,
                # Staff management - basic access
                "staff_manage": ToolPermissionLevel.READ,
                "shift_management": ToolPermissionLevel.READ,
                "workflow_guide": ToolPermissionLevel.READ,
                # Analytics - basic read
                "analytics_query": ToolPermissionLevel.READ,
                "report_generator": ToolPermissionLevel.READ,
                "chart_creator": ToolPermissionLevel.FORBIDDEN,
                "data_export": ToolPermissionLevel.FORBIDDEN,
                "query_builder": ToolPermissionLevel.FORBIDDEN,
                # Financial - forbidden
                "financial_reports": ToolPermissionLevel.FORBIDDEN,
                # System - read only
                "system_config": ToolPermissionLevel.READ,
                # Communication - full access
                "ticket_create": ToolPermissionLevel.WRITE,
                "escalation_route": ToolPermissionLevel.WRITE,
                "issue_tracking": ToolPermissionLevel.READ,
            },
            "support": {
                # Booking tools - full access for support
                "booking_search": ToolPermissionLevel.READ,
                "booking_create": ToolPermissionLevel.WRITE,
                "booking_modify": ToolPermissionLevel.WRITE,
                "booking_cancel": ToolPermissionLevel.WRITE,
                "booking_admin": ToolPermissionLevel.WRITE,
                # Menu and info - read access
                "menu_query": ToolPermissionLevel.READ,
                "restaurant_info": ToolPermissionLevel.READ,
                # User management - read and limited write
                "user_create": ToolPermissionLevel.FORBIDDEN,
                "user_modify": ToolPermissionLevel.WRITE,  # For support modifications
                "user_lookup": ToolPermissionLevel.READ,
                "customer_lookup": ToolPermissionLevel.READ,
                "customer_history": ToolPermissionLevel.READ,
                # Staff management - read only
                "staff_manage": ToolPermissionLevel.READ,
                "shift_management": ToolPermissionLevel.READ,
                "workflow_guide": ToolPermissionLevel.READ,
                # Analytics - basic access for support metrics
                "analytics_query": ToolPermissionLevel.READ,
                "report_generator": ToolPermissionLevel.READ,
                "chart_creator": ToolPermissionLevel.READ,
                "data_export": ToolPermissionLevel.WRITE,
                "query_builder": ToolPermissionLevel.FORBIDDEN,
                # Financial - limited access for refunds
                "financial_reports": ToolPermissionLevel.READ,
                # System - read only
                "system_config": ToolPermissionLevel.READ,
                # Communication - full access
                "ticket_create": ToolPermissionLevel.WRITE,
                "escalation_route": ToolPermissionLevel.WRITE,
                "issue_tracking": ToolPermissionLevel.WRITE,
            },
            "analytics": {
                # Booking tools - read only for analysis
                "booking_search": ToolPermissionLevel.READ,
                "booking_create": ToolPermissionLevel.FORBIDDEN,
                "booking_modify": ToolPermissionLevel.FORBIDDEN,
                "booking_cancel": ToolPermissionLevel.FORBIDDEN,
                "booking_admin": ToolPermissionLevel.FORBIDDEN,
                # Menu and info - read access
                "menu_query": ToolPermissionLevel.READ,
                "restaurant_info": ToolPermissionLevel.READ,
                # User management - read only for analysis
                "user_create": ToolPermissionLevel.FORBIDDEN,
                "user_modify": ToolPermissionLevel.FORBIDDEN,
                "user_lookup": ToolPermissionLevel.READ,
                "customer_lookup": ToolPermissionLevel.READ,
                "customer_history": ToolPermissionLevel.READ,
                # Staff management - read for analysis
                "staff_manage": ToolPermissionLevel.READ,
                "shift_management": ToolPermissionLevel.READ,
                "workflow_guide": ToolPermissionLevel.FORBIDDEN,
                # Analytics - full access
                "analytics_query": ToolPermissionLevel.ADMIN,
                "report_generator": ToolPermissionLevel.ADMIN,
                "chart_creator": ToolPermissionLevel.ADMIN,
                "data_export": ToolPermissionLevel.ADMIN,
                "query_builder": ToolPermissionLevel.ADMIN,
                # Financial - read access for analysis
                "financial_reports": ToolPermissionLevel.READ,
                # System - read for configuration analysis
                "system_config": ToolPermissionLevel.READ,
                # Communication - read for support analysis
                "ticket_create": ToolPermissionLevel.FORBIDDEN,
                "escalation_route": ToolPermissionLevel.FORBIDDEN,
                "issue_tracking": ToolPermissionLevel.READ,
            },
        }

    async def validate_tools(self, agent: str, requested_tools: list[str]) -> dict[str, Any]:
        """
        Validate tool access permissions for an agent.

        Args:
            agent: Agent identifier
            requested_tools: List of requested tool names

        Returns:
            Validation result with permissions and errors
        """
        try:
            if agent not in self.agent_permissions:
                return {
                    "valid": False,
                    "error": f"Unknown agent: {agent}",
                    "allowed_tools": [],
                    "forbidden_tools": requested_tools,
                }

            agent_perms = self.agent_permissions[agent]
            allowed_tools = []
            forbidden_tools = []
            permission_errors = []

            for tool in requested_tools:
                if tool not in self.tools:
                    permission_errors.append(f"Unknown tool: {tool}")
                    forbidden_tools.append(tool)
                    continue

                tool_info = self.tools[tool]
                required_permission = tool_info["required_permission"]
                agent_permission = agent_perms.get(tool, ToolPermissionLevel.FORBIDDEN)

                # Check if agent has sufficient permission
                if self._has_sufficient_permission(agent_permission, required_permission):
                    allowed_tools.append(tool)
                else:
                    forbidden_tools.append(tool)
                    permission_errors.append(
                        f"Tool '{tool}' requires {required_permission.value} but agent has {agent_permission.value}"
                    )

            return {
                "valid": len(forbidden_tools) == 0,
                "allowed_tools": allowed_tools,
                "forbidden_tools": forbidden_tools,
                "permission_errors": permission_errors,
                "used_tools": allowed_tools,  # Tools that would be used
            }

        except Exception as e:
            logger.exception(f"Tool validation error: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {e!s}",
                "allowed_tools": [],
                "forbidden_tools": requested_tools,
            }

    def _has_sufficient_permission(
        self, agent_permission: ToolPermissionLevel, required_permission: ToolPermissionLevel
    ) -> bool:
        """Check if agent permission is sufficient for required permission."""
        permission_hierarchy = {
            ToolPermissionLevel.FORBIDDEN: 0,
            ToolPermissionLevel.READ: 1,
            ToolPermissionLevel.WRITE: 2,
            ToolPermissionLevel.ADMIN: 3,
        }

        agent_level = permission_hierarchy.get(agent_permission, 0)
        required_level = permission_hierarchy.get(required_permission, 3)

        return agent_level >= required_level

    async def get_agent_permissions(self, agent: str) -> dict[str, Any]:
        """
        Get all tool permissions for an agent.

        Args:
            agent: Agent identifier

        Returns:
            Agent permissions with tool details
        """
        try:
            if agent not in self.agent_permissions:
                return {
                    "agent": agent,
                    "valid": False,
                    "error": f"Unknown agent: {agent}",
                    "permissions": {},
                }

            agent_perms = self.agent_permissions[agent]
            permissions = {}

            for tool, permission in agent_perms.items():
                if tool in self.tools:
                    tool_info = self.tools[tool]
                    permissions[tool] = {
                        "permission": permission.value,
                        "category": tool_info["category"].value,
                        "description": tool_info["description"],
                        "can_use": permission != ToolPermissionLevel.FORBIDDEN,
                    }

            # Get statistics
            total_tools = len(permissions)
            allowed_tools = sum(1 for p in permissions.values() if p["can_use"])

            return {
                "agent": agent,
                "valid": True,
                "permissions": permissions,
                "statistics": {
                    "total_tools": total_tools,
                    "allowed_tools": allowed_tools,
                    "forbidden_tools": total_tools - allowed_tools,
                },
            }

        except Exception as e:
            logger.exception(f"Error getting agent permissions: {e}")
            return {"agent": agent, "valid": False, "error": str(e), "permissions": {}}

    async def list_tools(
        self,
        category: ToolCategory | None = None,
        permission_level: ToolPermissionLevel | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available tools with optional filtering.

        Args:
            category: Optional category filter
            permission_level: Optional permission level filter

        Returns:
            List of tool information
        """
        try:
            tools = []

            for tool_name, tool_info in self.tools.items():
                # Apply filters
                if category and tool_info["category"] != category:
                    continue

                if permission_level and tool_info["required_permission"] != permission_level:
                    continue

                tools.append(
                    {
                        "name": tool_name,
                        "category": tool_info["category"].value,
                        "description": tool_info["description"],
                        "required_permission": tool_info["required_permission"].value,
                        "parameters": tool_info["parameters"],
                        "output": tool_info["output"],
                    }
                )

            return sorted(tools, key=lambda x: (x["category"], x["name"]))

        except Exception as e:
            logger.exception(f"Error listing tools: {e}")
            return []

    async def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Tool identifier

        Returns:
            Tool information or None if not found
        """
        try:
            if tool_name not in self.tools:
                return None

            tool_info = self.tools[tool_name]

            # Get agents that can use this tool
            authorized_agents = []
            for agent, permissions in self.agent_permissions.items():
                agent_permission = permissions.get(tool_name, ToolPermissionLevel.FORBIDDEN)
                if agent_permission != ToolPermissionLevel.FORBIDDEN:
                    authorized_agents.append({"agent": agent, "permission": agent_permission.value})

            return {
                "name": tool_name,
                "category": tool_info["category"].value,
                "description": tool_info["description"],
                "required_permission": tool_info["required_permission"].value,
                "parameters": tool_info["parameters"],
                "output": tool_info["output"],
                "authorized_agents": authorized_agents,
            }

        except Exception as e:
            logger.exception(f"Error getting tool info: {e}")
            return None

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on tool registry."""
        try:
            total_tools = len(self.tools)
            total_agents = len(self.agent_permissions)

            # Check for orphaned permissions
            orphaned_tools = []
            for agent, permissions in self.agent_permissions.items():
                for tool in permissions:
                    if tool not in self.tools:
                        orphaned_tools.append(f"{agent}:{tool}")

            # Check coverage
            tools_with_permissions = set()
            for permissions in self.agent_permissions.values():
                tools_with_permissions.update(permissions.keys())

            uncovered_tools = set(self.tools.keys()) - tools_with_permissions

            return {
                "healthy": len(orphaned_tools) == 0,
                "total_tools": total_tools,
                "total_agents": total_agents,
                "orphaned_permissions": orphaned_tools,
                "uncovered_tools": list(uncovered_tools),
                "last_check": datetime.utcnow(),
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "last_check": datetime.utcnow()}
