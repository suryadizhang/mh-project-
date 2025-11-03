"""
Agent Gateway Service with Station-Aware RBAC Integration
Central orchestration layer for agent-aware AI interactions with multi-tenant permissions.
Handles agent validation, request routing, and response coordination with station context.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from api.ai.endpoints.services.agent_namespace import AgentNamespaceService
from api.ai.endpoints.services.model_ladder import ModelLadderService
from api.ai.endpoints.services.openai_service import OpenAIService
from api.ai.endpoints.services.prompt_registry import PromptRegistryService
from api.ai.endpoints.services.role_based_ai import UserRole, role_based_ai
from api.ai.endpoints.services.tool_registry import ToolRegistryService

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agent types with specific capabilities."""

    CUSTOMER = "customer"
    ADMIN = "admin"
    STAFF = "staff"
    SUPPORT = "support"
    ANALYTICS = "analytics"


class StationAwareAgentGatewayService:
    """Central gateway for agent-aware AI interactions with station-scoped permissions."""

    def __init__(self):
        self.prompt_registry = PromptRegistryService()
        self.tool_registry = ToolRegistryService()
        self.model_ladder = ModelLadderService()
        self.namespace_service = AgentNamespaceService()
        self.openai_service = OpenAIService()

        # Agent configurations with station-aware permissions
        self.agent_configs = {
            AgentType.CUSTOMER: {
                "display_name": "Customer Service Agent",
                "description": "Handles booking inquiries and customer service within station scope",
                "capabilities": [
                    "booking_management",
                    "menu_inquiry",
                    "restaurant_info",
                    "customer_support",
                ],
                "tools": [
                    "booking_search",
                    "booking_create",
                    "booking_modify",
                    "booking_cancel",
                    "menu_query",
                    "restaurant_info",
                ],
                "required_station_permissions": [
                    "booking.read",
                    "booking.create",
                    "customer.read",
                    "ai.chat",
                    "ai.booking_assist",
                ],
                "max_model": "gpt-4-mini",
                "station_data_access": "current_station_only",
                "escalation_triggers": [
                    "complex_booking",
                    "payment_issue",
                    "complaint",
                    "allergy_concern",
                ],
            },
            AgentType.ADMIN: {
                "display_name": "Administrative Management Agent",
                "description": "Full system management and operations with cross-station access",
                "capabilities": [
                    "user_management",
                    "staff_management",
                    "booking_management",
                    "financial_oversight",
                    "system_configuration",
                    "analytics_access",
                    "restaurant_operations",
                    "cross_station_access",
                ],
                "tools": [
                    "user_create",
                    "user_modify",
                    "staff_manage",
                    "booking_admin",
                    "analytics_query",
                    "system_config",
                    "financial_reports",
                    "cross_station_reports",
                ],
                "required_station_permissions": [
                    "booking.read",
                    "booking.create",
                    "booking.update",
                    "booking.cancel",
                    "customer.read",
                    "customer.update",
                    "user.manage",
                    "system.config",
                    "reports.advanced",
                    "ai.analytics",
                    "cross_station.read",
                ],
                "max_model": "gpt-4",
                "station_data_access": "cross_station_allowed",
                "escalation_triggers": ["security_concern", "data_breach", "legal_issue"],
            },
            AgentType.STAFF: {
                "display_name": "Staff Operations Agent",
                "description": "Operational guidance and workflow assistance within station",
                "capabilities": [
                    "operational_guidance",
                    "workflow_assistance",
                    "booking_support",
                    "customer_service_help",
                ],
                "tools": ["booking_view", "customer_lookup", "workflow_guide", "shift_management"],
                "required_station_permissions": [
                    "booking.read",
                    "booking.update",
                    "customer.read",
                    "ai.chat",
                    "reports.basic",
                ],
                "max_model": "gpt-4-mini",
                "station_data_access": "current_station_only",
                "escalation_triggers": ["admin_required", "system_issue", "complex_problem"],
            },
            AgentType.SUPPORT: {
                "display_name": "Customer Support Agent",
                "description": "Specialized customer support and escalation handling within station",
                "capabilities": [
                    "advanced_customer_service",
                    "issue_resolution",
                    "escalation_management",
                    "complaint_handling",
                ],
                "tools": [
                    "ticket_create",
                    "customer_history",
                    "escalation_route",
                    "issue_tracking",
                ],
                "required_station_permissions": [
                    "booking.read",
                    "booking.update",
                    "customer.read",
                    "customer.update",
                    "message.read",
                    "message.send",
                    "ai.chat",
                    "ai.booking_assist",
                ],
                "max_model": "gpt-4",
                "station_data_access": "current_station_only",
                "escalation_triggers": ["legal_threat", "refund_request", "service_failure"],
            },
            AgentType.ANALYTICS: {
                "display_name": "Analytics and Reporting Agent",
                "description": "Data analysis and business intelligence with station-scoped access",
                "capabilities": [
                    "data_analysis",
                    "report_generation",
                    "business_intelligence",
                    "performance_metrics",
                ],
                "tools": ["query_builder", "report_generator", "chart_creator", "data_export"],
                "required_station_permissions": [
                    "booking.read",
                    "customer.read",
                    "reports.basic",
                    "reports.advanced",
                    "reports.export",
                    "ai.analytics",
                ],
                "max_model": "gpt-4",
                "station_data_access": "depends_on_user_permissions",
                "escalation_triggers": ["data_privacy_concern", "complex_analysis"],
            },
        }

    async def validate_agent_for_station_user(
        self, agent: str, user_station_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Validate agent type and check station permissions.

        Args:
            agent: Agent identifier string
            user_station_context: User's station context with permissions

        Returns:
            Validation result with agent configuration and permission check
        """
        try:
            agent_type = AgentType(agent.lower())
            config = self.agent_configs[agent_type]

            # Check if user has required station permissions for this agent
            permission_check = {"granted": True, "missing_permissions": []}

            if user_station_context:
                user_permissions = set(user_station_context.get("station_permissions", []))
                required_permissions = set(config["required_station_permissions"])
                missing_permissions = required_permissions - user_permissions

                if missing_permissions:
                    permission_check = {
                        "granted": False,
                        "missing_permissions": list(missing_permissions),
                        "user_role": user_station_context.get("station_role"),
                        "station_id": user_station_context.get("current_station_id"),
                    }

            return {
                "valid": True,
                "agent": agent_type.value,
                "capabilities": self._get_agent_capabilities(agent_type),
                "config": config,
                "permission_check": permission_check,
                "station_access_level": config["station_data_access"],
            }

        except ValueError:
            return {
                "valid": False,
                "error": f"Unknown agent type: {agent}",
                "available_agents": [a.value for a in AgentType],
            }

    def _get_agent_capabilities(self, agent_type: AgentType) -> dict[str, bool]:
        """Get boolean capability map for agent."""
        config = self.agent_configs[agent_type]
        all_capabilities = [
            "booking_management",
            "user_management",
            "staff_management",
            "financial_oversight",
            "system_configuration",
            "analytics_access",
            "restaurant_operations",
            "customer_support",
            "escalation_management",
            "cross_station_access",
        ]

        return {cap: cap in config["capabilities"] for cap in all_capabilities}

    async def process_station_aware_request(
        self,
        agent: str,
        message: str,
        conversation_id: str,
        user_station_context: dict[str, Any],
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        """
        Process chat request through agent-aware pipeline with station permissions.

        Args:
            agent: Agent type
            message: User message
            conversation_id: Conversation identifier
            user_station_context: User's station context with permissions
            user_id: Optional user identifier
            context: Additional context
            model_override: Optional model selection override

        Returns:
            Processed response with metadata and permission-filtered content
        """
        try:
            agent_type = AgentType(agent.lower())
            agent_config = self.agent_configs[agent_type]
            context = context or {}

            # Validate agent permissions for station user
            validation = await self.validate_agent_for_station_user(agent, user_station_context)
            if not validation["permission_check"]["granted"]:
                return await self._handle_permission_denied_error(
                    agent_type, validation["permission_check"], message
                )

            # Extract station context
            current_station_id = user_station_context.get("current_station_id")
            station_role = user_station_context.get("station_role")
            accessible_stations = user_station_context.get(
                "accessible_stations", [current_station_id]
            )

            # Create agent namespace context with station isolation
            namespace_context = await self.namespace_service.create_agent_context(
                conversation_id=conversation_id, agent=agent, user_id=user_id
            )

            # Build station-aware agent context
            agent_context = {
                "agent": agent,
                "agent_type": agent_type.value,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "capabilities": agent_config["capabilities"],
                "available_tools": agent_config["tools"],
                "namespace_context": namespace_context,
                # Station context
                "station_context": {
                    "current_station_id": current_station_id,
                    "station_role": station_role,
                    "accessible_stations": accessible_stations,
                    "station_permissions": user_station_context.get("station_permissions", []),
                    "data_access_level": agent_config["station_data_access"],
                    "is_super_admin": user_station_context.get("is_super_admin", False),
                    "is_admin": user_station_context.get("is_admin", False),
                },
                **context,
            }

            # Get agent-specific prompt with station context
            system_prompt = await self.prompt_registry.get_agent_prompt(
                agent_type.value, context=agent_context
            )

            # Validate tool permissions with station context
            requested_tools = self._extract_tool_requests(message)
            tool_validation = await self.tool_registry.validate_tools_with_station_context(
                agent_type.value, requested_tools, user_station_context
            )

            if not tool_validation["valid"]:
                return await self._handle_tool_permission_error(
                    agent_type, tool_validation, message
                )

            # Select model based on complexity, agent limits, and station permissions
            selected_model = await self.model_ladder.select_model(
                message=message,
                agent=agent_type.value,
                max_model=agent_config["max_model"],
                override=model_override,
            )

            # Check for escalation triggers
            escalation_check = await self._check_escalation_triggers(
                message, agent_type, agent_config["escalation_triggers"]
            )

            if escalation_check["should_escalate"]:
                return await self._handle_escalation(
                    agent_type, message, escalation_check, agent_context
                )

            # Generate AI response
            response_data = await self.openai_service.generate_response(
                message=message, context=system_prompt, force_model=selected_model
            )

            # Apply agent-specific filtering with namespace isolation and station scoping
            filtered_content = await self.namespace_service.filter_response_for_agent_with_station(
                agent=agent_type.value,
                response=response_data[0],  # response content
                context=agent_context,
                station_context=agent_context["station_context"],
            )

            # Get agent-specific suggestions with station context
            suggestions = await self._generate_agent_suggestions_with_station(
                agent_type, message, filtered_content, user_station_context
            )

            # Build response with station metadata
            return {
                "content": filtered_content,
                "confidence": response_data[1],
                "intent": response_data[2],
                "model_used": selected_model,
                "suggestions": suggestions,
                "actions": await self._get_available_actions_with_station(
                    agent_type, filtered_content, user_station_context
                ),
                "tools_used": tool_validation.get("used_tools", []),
                "station_context": {
                    "current_station": current_station_id,
                    "agent_permissions": validation["permission_check"],
                    "data_scope": agent_config["station_data_access"],
                },
                "cost": {
                    "input_tokens": response_data[3] * 0.00001,  # Simplified cost calc
                    "output_tokens": response_data[4] * 0.00002,
                },
            }

        except Exception as e:
            logger.exception(f"Station-aware agent gateway processing error: {e}")
            return await self._handle_processing_error(agent, message, str(e))

    async def _handle_permission_denied_error(
        self, agent_type: AgentType, permission_check: dict[str, Any], message: str
    ) -> dict[str, Any]:
        """Handle permission denied errors for station access."""
        missing_perms = ", ".join(permission_check["missing_permissions"])
        user_role = permission_check.get("user_role", "unknown")

        return {
            "content": f"I'm sorry, but your current role ({user_role}) doesn't have the required permissions "
            f"to use the {agent_type.value} agent. Missing permissions: {missing_perms}. "
            f"Please contact your station administrator to request access.",
            "confidence": 0.95,
            "intent": "permission_denied",
            "model_used": "rule_based",
            "suggestions": [
                "Contact station administrator",
                "Try a different agent",
                "Request permission upgrade",
            ],
            "actions": [
                {
                    "type": "permission_request",
                    "label": "Request Permissions",
                    "url": "/admin/permissions/request",
                }
            ],
            "tools_used": [],
            "station_context": {
                "permission_denied": True,
                "required_permissions": permission_check["missing_permissions"],
                "current_role": user_role,
            },
            "escalation": {
                "required": True,
                "reason": "insufficient_station_permissions",
                "target_role": "station_admin",
            },
        }

    async def _generate_agent_suggestions_with_station(
        self,
        agent_type: AgentType,
        message: str,
        response: str,
        user_station_context: dict[str, Any],
    ) -> list[str]:
        """Generate agent-specific follow-up suggestions with station context."""
        user_station_context.get("station_role", "customer_support")
        is_cross_station = user_station_context.get("is_admin", False)

        suggestions_map = {
            AgentType.CUSTOMER: [
                "Tell me about pricing for this station",
                "Check availability at this location",
                "What's included in our service?",
                "How do I book at this station?",
                "What are this station's service areas?",
            ],
            AgentType.ADMIN: [
                "Show analytics for current station",
                "Generate station financial report",
                "View this station's status",
                "Manage station staff schedules",
                "Configure station settings",
            ]
            + (
                ["View cross-station analytics", "Compare station performance"]
                if is_cross_station
                else []
            ),
            AgentType.STAFF: [
                "Help with station booking process",
                "Show today's station schedule",
                "Customer service guidelines for this station",
                "Handle special requests",
                "Escalate to station manager",
            ],
            AgentType.SUPPORT: [
                "Create support ticket for this station",
                "Check customer history in station",
                "Process refund request",
                "Escalate to station management",
                "Review station-specific complaint details",
            ],
            AgentType.ANALYTICS: [
                "Generate station performance report",
                "Show station booking trends",
                "Station revenue analysis",
                "Customer satisfaction metrics for this station",
                "Export station data to CSV",
            ]
            + (
                ["Compare with other stations", "Cross-station analysis"]
                if is_cross_station
                else []
            ),
        }

        return suggestions_map.get(agent_type, [])

    async def _get_available_actions_with_station(
        self, agent_type: AgentType, response: str, user_station_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get available actions based on agent and station permissions."""
        actions = []
        station_id = user_station_context.get("current_station_id")
        station_permissions = set(user_station_context.get("station_permissions", []))

        if agent_type == AgentType.CUSTOMER:
            if "book" in response.lower() and "booking.create" in station_permissions:
                actions.append(
                    {
                        "type": "booking_form",
                        "label": "Start Booking Process",
                        "url": f"/booking/new?station={station_id}",
                        "requires_permission": "booking.create",
                    }
                )
            if "menu" in response.lower():
                actions.append(
                    {
                        "type": "menu_view",
                        "label": "View Station Menu",
                        "url": f"/menu?station={station_id}",
                    }
                )

        elif agent_type == AgentType.ADMIN:
            if "system.config" in station_permissions:
                actions.append(
                    {
                        "type": "admin_dashboard",
                        "label": "Open Station Dashboard",
                        "url": f"/admin/dashboard?station={station_id}",
                        "requires_permission": "system.config",
                    }
                )
            if "user.manage" in station_permissions:
                actions.append(
                    {
                        "type": "user_management",
                        "label": "Manage Station Users",
                        "url": f"/admin/users?station={station_id}",
                        "requires_permission": "user.manage",
                    }
                )
            if "cross_station.read" in station_permissions:
                actions.append(
                    {
                        "type": "cross_station_view",
                        "label": "View All Stations",
                        "url": "/admin/stations",
                        "requires_permission": "cross_station.read",
                    }
                )

        elif agent_type == AgentType.ANALYTICS:
            if "reports.basic" in station_permissions:
                actions.append(
                    {
                        "type": "station_reports",
                        "label": "Station Reports",
                        "url": f"/analytics/station/{station_id}",
                        "requires_permission": "reports.basic",
                    }
                )
            if "reports.export" in station_permissions:
                actions.append(
                    {
                        "type": "data_export",
                        "label": "Export Station Data",
                        "url": f"/analytics/export?station={station_id}",
                        "requires_permission": "reports.export",
                    }
                )

        return actions

    async def stream_response(
        self,
        agent: str,
        message: str,
        conversation_id: str,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream response generation for real-time interactions.

        Args:
            agent: Agent type
            message: User message
            conversation_id: Conversation identifier
            user_id: Optional user identifier
            context: Additional context

        Yields:
            Response chunks with metadata
        """
        try:
            # Validate agent
            validation = await self.validate_agent(agent)
            if not validation["valid"]:
                yield {
                    "content": f"Error: {validation['error']}",
                    "is_final": True,
                    "metadata": {"error": True},
                }
                return

            # For now, process normally and stream the result
            # In production, this would integrate with streaming LLM APIs
            response = await self.process_request(
                agent=agent,
                message=message,
                conversation_id=conversation_id,
                user_id=user_id,
                context=context,
            )

            # Simulate streaming by chunking the response
            content = response["content"]
            chunk_size = 50  # Characters per chunk

            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                is_final = i + chunk_size >= len(content)

                yield {
                    "content": chunk,
                    "is_final": is_final,
                    "metadata": {
                        "chunk_index": i // chunk_size,
                        "total_chunks": (len(content) + chunk_size - 1) // chunk_size,
                        "agent": agent,
                    },
                }

                if is_final:
                    # Send final metadata
                    yield {
                        "content": "",
                        "is_final": True,
                        "metadata": {
                            "response_complete": True,
                            "confidence": response["confidence"],
                            "model_used": response["model_used"],
                            "suggestions": response["suggestions"],
                        },
                    }

        except Exception as e:
            logger.exception(f"Streaming error: {e}")
            yield {
                "content": f"Error during streaming: {e!s}",
                "is_final": True,
                "metadata": {"error": True},
            }

    def _extract_tool_requests(self, message: str) -> list[str]:
        """Extract potential tool requests from message."""
        # Simplified tool extraction - in production, this would be more sophisticated
        tool_keywords = {
            "book": ["booking_create"],
            "cancel": ["booking_cancel"],
            "modify": ["booking_modify"],
            "search": ["booking_search"],
            "user": ["user_lookup"],
            "report": ["report_generator"],
            "analytics": ["analytics_query"],
        }

        message_lower = message.lower()
        requested_tools = []

        for keyword, tools in tool_keywords.items():
            if keyword in message_lower:
                requested_tools.extend(tools)

        return requested_tools

    async def _check_escalation_triggers(
        self, message: str, agent_type: AgentType, triggers: list[str]
    ) -> dict[str, Any]:
        """Check if message contains escalation triggers."""
        message_lower = message.lower()

        escalation_keywords = {
            "complex_booking": ["multiple", "corporate", "large group", "special requirements"],
            "payment_issue": ["refund", "charge", "payment", "billing"],
            "complaint": ["terrible", "awful", "disappointed", "angry", "complaint"],
            "allergy_concern": ["allergy", "allergic", "dietary restriction", "gluten"],
            "legal_threat": ["lawyer", "legal", "sue", "lawsuit"],
            "security_concern": ["hack", "breach", "security", "unauthorized"],
        }

        triggered = []
        for trigger in triggers:
            if trigger in escalation_keywords:
                keywords = escalation_keywords[trigger]
                if any(keyword in message_lower for keyword in keywords):
                    triggered.append(trigger)

        return {
            "should_escalate": len(triggered) > 0,
            "triggers": triggered,
            "escalation_type": "human" if triggered else None,
        }

    async def _apply_agent_filtering(
        self, agent_type: AgentType, content: str, context: dict[str, Any]
    ) -> str:
        """Apply agent-specific content filtering."""
        # Use existing role-based filtering
        if agent_type == AgentType.CUSTOMER:
            user_role = UserRole.CUSTOMER
        elif agent_type == AgentType.ADMIN:
            user_role = UserRole.ADMIN
        elif agent_type == AgentType.STAFF:
            user_role = UserRole.STAFF
        else:
            user_role = UserRole.CUSTOMER  # Default

        return role_based_ai.filter_ai_response(user_role, content, context)

    async def _generate_agent_suggestions(
        self, agent_type: AgentType, message: str, response: str
    ) -> list[str]:
        """Generate agent-specific follow-up suggestions."""
        suggestions_map = {
            AgentType.CUSTOMER: [
                "Tell me about pricing",
                "Check availability",
                "What's included in the service?",
                "How do I book?",
                "What are your service areas?",
            ],
            AgentType.ADMIN: [
                "Show user analytics",
                "Generate financial report",
                "View system status",
                "Manage staff schedules",
                "Configure system settings",
            ],
            AgentType.STAFF: [
                "Help with booking process",
                "Show today's schedule",
                "Customer service guidelines",
                "Handle special requests",
                "Escalate to manager",
            ],
            AgentType.SUPPORT: [
                "Create support ticket",
                "Check customer history",
                "Process refund request",
                "Escalate to management",
                "Review complaint details",
            ],
            AgentType.ANALYTICS: [
                "Generate performance report",
                "Show booking trends",
                "Revenue analysis",
                "Customer satisfaction metrics",
                "Export data to CSV",
            ],
        }

        return suggestions_map.get(agent_type, [])

    async def _get_available_actions(
        self, agent_type: AgentType, response: str
    ) -> list[dict[str, Any]]:
        """Get available actions based on agent and response."""
        actions = []

        if agent_type == AgentType.CUSTOMER:
            if "book" in response.lower():
                actions.append(
                    {
                        "type": "booking_form",
                        "label": "Start Booking Process",
                        "url": "/booking/new",
                    }
                )
            if "menu" in response.lower():
                actions.append({"type": "menu_view", "label": "View Full Menu", "url": "/menu"})

        elif agent_type == AgentType.ADMIN:
            actions.extend(
                [
                    {
                        "type": "admin_dashboard",
                        "label": "Open Admin Dashboard",
                        "url": "/admin/dashboard",
                    },
                    {"type": "user_management", "label": "Manage Users", "url": "/admin/users"},
                ]
            )

        return actions

    async def _handle_tool_permission_error(
        self, agent_type: AgentType, validation: dict[str, Any], message: str
    ) -> dict[str, Any]:
        """Handle tool permission errors."""
        return {
            "content": f"I don't have permission to perform that action as a {agent_type.value} agent. "
            f"Available tools: {', '.join(validation.get('allowed_tools', []))}",
            "confidence": 0.95,
            "intent": "permission_error",
            "model_used": "rule_based",
            "suggestions": ["Try a different request", "Contact an admin"],
            "actions": [],
            "tools_used": [],
            "escalation": {
                "required": True,
                "reason": "insufficient_permissions",
                "target_agent": "admin",
            },
        }

    async def _handle_escalation(
        self,
        agent_type: AgentType,
        message: str,
        escalation_check: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle escalation scenarios."""
        return {
            "content": "I understand your concern. Let me connect you with a team member who can provide specialized assistance.",
            "confidence": 0.95,
            "intent": "escalation",
            "model_used": "rule_based",
            "suggestions": ["Speak with manager", "Get immediate help"],
            "actions": [
                {
                    "type": "escalation",
                    "label": "Connect with Human Agent",
                    "url": "/support/escalate",
                }
            ],
            "tools_used": [],
            "escalation": {
                "required": True,
                "triggers": escalation_check["triggers"],
                "type": escalation_check["escalation_type"],
                "priority": "high" if "legal" in escalation_check["triggers"] else "normal",
            },
        }

    async def _handle_processing_error(
        self, agent: str, message: str, error: str
    ) -> dict[str, Any]:
        """Handle processing errors gracefully."""
        return {
            "content": "I'm sorry, I'm experiencing technical difficulties. Please try again or contact our support team.",
            "confidence": 0.0,
            "intent": "error",
            "model_used": "error_handler",
            "suggestions": ["Try again", "Contact support", "Use different wording"],
            "actions": [{"type": "support", "label": "Contact Support", "url": "/support"}],
            "tools_used": [],
            "error_details": {"agent": agent, "message_preview": message[:50], "error": error},
        }

    async def list_agents(self) -> list[dict[str, Any]]:
        """List all available agents with their configurations."""
        agents = []

        for agent_type, config in self.agent_configs.items():
            agents.append(
                {
                    "agent": agent_type.value,
                    "display_name": config["display_name"],
                    "description": config["description"],
                    "capabilities": config["capabilities"],
                    "tools_count": len(config["tools"]),
                    "max_model": config["max_model"],
                    "status": "active",
                }
            )

        return agents

    async def get_agent_details(self, agent_name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific agent."""
        try:
            agent_type = AgentType(agent_name.lower())
            config = self.agent_configs[agent_type]

            return {
                "agent": agent_type.value,
                "display_name": config["display_name"],
                "description": config["description"],
                "capabilities": config["capabilities"],
                "tools": config["tools"],
                "max_model": config["max_model"],
                "escalation_triggers": config["escalation_triggers"],
                "status": "active",
                "prompt_template": await self.prompt_registry.get_agent_prompt_template(
                    agent_type.value
                ),
                "tool_permissions": await self.tool_registry.get_agent_permissions(
                    agent_type.value
                ),
            }

        except ValueError:
            return None

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on agent gateway."""
        try:
            # Test agent validation
            test_validation = await self.validate_agent("customer")

            return {
                "healthy": test_validation["valid"],
                "agent_count": len(self.agent_configs),
                "available_agents": [a.value for a in AgentType],
                "station_aware": True,
                "rbac_enabled": True,
                "last_check": datetime.utcnow(),
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "last_check": datetime.utcnow()}

    # Legacy compatibility methods (for backward compatibility)
    async def validate_agent(self, agent: str) -> dict[str, Any]:
        """Legacy method - use validate_agent_for_station_user for new implementations."""
        return await self.validate_agent_for_station_user(agent, None)

    async def process_request(
        self,
        agent: str,
        message: str,
        conversation_id: str,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        """Legacy method - use process_station_aware_request for new implementations."""
        # Create minimal station context for backward compatibility
        minimal_station_context = {
            "current_station_id": "default",
            "station_role": "customer_support",
            "station_permissions": ["booking.read", "customer.read", "ai.chat"],
            "accessible_stations": ["default"],
            "is_super_admin": False,
            "is_admin": False,
        }

        return await self.process_station_aware_request(
            agent=agent,
            message=message,
            conversation_id=conversation_id,
            user_station_context=minimal_station_context,
            user_id=user_id,
            context=context,
            model_override=model_override,
        )


# For backward compatibility - alias the station-aware version as the main class
AgentGatewayService = StationAwareAgentGatewayService
