"""
Agent Namespace Service
Implements proper agent isolation to prevent prompt bleed while allowing general reasoning.
Manages context namespacing, conversation separation, and agent-specific response filtering.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class ConversationContext:
    """Manages conversation context with agent isolation."""
    
    def __init__(self, conversation_id: str, agent: str):
        self.conversation_id = conversation_id
        self.agent = agent
        self.created_at = datetime.utcnow()
        self.messages = []
        self.agent_capabilities = set()
        self.escalation_history = []
        self.sensitive_topics = set()
        self._namespace_boundaries = {}
    
    def add_message(
        self,
        message_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add message to conversation with namespace validation."""
        message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "agent": self.agent,
            "metadata": metadata or {}
        }
        
        # Apply namespace filtering
        filtered_content = self._filter_content_for_namespace(content)
        message["filtered_content"] = filtered_content
        
        self.messages.append(message)
    
    def _filter_content_for_namespace(self, content: str) -> str:
        """Filter content to respect agent namespace boundaries."""
        # Implement agent-specific content filtering
        if self.agent == "customer":
            # Remove admin-specific content
            admin_patterns = [
                "admin dashboard", "user management", "financial reports",
                "system configuration", "staff management"
            ]
            filtered_content = content
            for pattern in admin_patterns:
                if pattern.lower() in content.lower():
                    filtered_content = filtered_content.replace(
                        pattern, "[content not available for customer agent]"
                    )
            return filtered_content
        
        return content
    
    def get_conversation_history(
        self,
        include_system: bool = False,
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history with namespace filtering."""
        filtered_messages = []
        
        for message in self.messages[-max_messages:]:
            if message["role"] == "system" and not include_system:
                continue
            
            # Use filtered content for namespace isolation
            filtered_message = {
                "role": message["role"],
                "content": message["filtered_content"],
                "timestamp": message["timestamp"],
                "message_id": message["message_id"]
            }
            
            filtered_messages.append(filtered_message)
        
        return filtered_messages


class AgentNamespaceService:
    """Service for managing agent namespaces and isolation."""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
        self.agent_boundaries = self._initialize_agent_boundaries()
        self.cross_agent_restrictions = self._initialize_cross_agent_restrictions()
        self.namespace_rules = self._initialize_namespace_rules()
    
    def _initialize_agent_boundaries(self) -> Dict[str, Dict[str, Any]]:
        """Initialize agent namespace boundaries."""
        return {
            "customer": {
                "allowed_topics": [
                    "booking", "menu", "restaurant_info", "pricing",
                    "availability", "cancellation", "modification"
                ],
                "forbidden_topics": [
                    "admin_functions", "user_management", "staff_management",
                    "financial_data", "system_configuration", "analytics"
                ],
                "data_access": {
                    "own_bookings": True,
                    "own_profile": True,
                    "all_bookings": False,
                    "user_data": False,
                    "financial_reports": False
                },
                "escalation_triggers": [
                    "admin_request", "complex_issue", "complaint",
                    "refund_request", "legal_concern"
                ]
            },
            "admin": {
                "allowed_topics": [
                    "user_management", "staff_management", "booking_management",
                    "financial_oversight", "system_configuration", "analytics",
                    "restaurant_operations", "customer_service"
                ],
                "forbidden_topics": [],  # Admin has access to all topics
                "data_access": {
                    "own_bookings": True,
                    "own_profile": True,
                    "all_bookings": True,
                    "user_data": True,
                    "financial_reports": True,
                    "system_logs": True,
                    "staff_data": True
                },
                "escalation_triggers": [
                    "security_breach", "legal_issue", "data_privacy_concern"
                ]
            },
            "staff": {
                "allowed_topics": [
                    "operational_guidance", "customer_service", "booking_support",
                    "workflow_assistance", "training_materials"
                ],
                "forbidden_topics": [
                    "financial_data", "user_management", "system_configuration",
                    "admin_functions"
                ],
                "data_access": {
                    "own_bookings": True,
                    "own_profile": True,
                    "assigned_bookings": True,
                    "customer_lookup": True,
                    "all_bookings": False,
                    "financial_reports": False
                },
                "escalation_triggers": [
                    "admin_needed", "complex_customer_issue", "system_problem"
                ]
            },
            "support": {
                "allowed_topics": [
                    "customer_issues", "complaint_resolution", "refund_processing",
                    "escalation_management", "service_recovery"
                ],
                "forbidden_topics": [
                    "system_configuration", "staff_management", "financial_oversight"
                ],
                "data_access": {
                    "own_bookings": True,
                    "own_profile": True,
                    "customer_bookings": True,
                    "customer_history": True,
                    "support_tickets": True,
                    "financial_reports": False
                },
                "escalation_triggers": [
                    "legal_threat", "media_attention", "safety_concern"
                ]
            },
            "analytics": {
                "allowed_topics": [
                    "data_analysis", "reporting", "business_intelligence",
                    "performance_metrics", "trend_analysis"
                ],
                "forbidden_topics": [
                    "customer_service", "booking_operations", "staff_management"
                ],
                "data_access": {
                    "aggregated_data": True,
                    "anonymized_data": True,
                    "individual_customer_data": False,
                    "financial_reports": True,
                    "operational_metrics": True
                },
                "escalation_triggers": [
                    "data_privacy_request", "complex_analysis_needed"
                ]
            }
        }
    
    def _initialize_cross_agent_restrictions(self) -> Dict[str, List[str]]:
        """Initialize restrictions for cross-agent interactions."""
        return {
            "customer_to_admin": [
                "Cannot access admin functions",
                "Cannot view other customer data",
                "Cannot modify system settings"
            ],
            "staff_to_admin": [
                "Cannot access financial reports",
                "Cannot modify user accounts",
                "Cannot change system configuration"
            ],
            "support_to_admin": [
                "Cannot access system configuration",
                "Cannot view financial oversight data"
            ],
            "analytics_to_operational": [
                "Cannot perform operational actions",
                "Cannot modify customer data",
                "Read-only access to most data"
            ]
        }
    
    def _initialize_namespace_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize namespace isolation rules."""
        return {
            "conversation_isolation": {
                "cross_agent_context": False,  # Conversations don't cross agent boundaries
                "history_sharing": False,      # Agent conversations are isolated
                "context_bleeding": False      # No context bleed between agents
            },
            "data_isolation": {
                "agent_specific_filtering": True,
                "capability_enforcement": True,
                "access_control_validation": True
            },
            "response_filtering": {
                "agent_appropriate_content": True,
                "sensitive_data_masking": True,
                "capability_aligned_responses": True
            }
        }
    
    async def create_agent_context(
        self,
        conversation_id: str,
        agent: str,
        user_id: Optional[str] = None
    ) -> ConversationContext:
        """
        Create isolated context for agent conversation.
        
        Args:
            conversation_id: Conversation identifier
            agent: Agent type
            user_id: Optional user identifier
            
        Returns:
            Isolated conversation context
        """
        try:
            # Validate agent
            if agent not in self.agent_boundaries:
                raise ValueError(f"Unknown agent: {agent}")
            
            # Create conversation context
            context = ConversationContext(conversation_id, agent)
            
            # Set agent capabilities
            agent_config = self.agent_boundaries[agent]
            context.agent_capabilities = set(agent_config["allowed_topics"])
            
            # Store context
            self.conversations[conversation_id] = context
            
            logger.info(f"Created agent context for {agent} - conversation {conversation_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error creating agent context: {e}")
            raise
    
    async def validate_agent_action(
        self,
        agent: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate if an agent can perform a specific action.
        
        Args:
            agent: Agent type
            action: Action to validate
            context: Optional context for validation
            
        Returns:
            Validation result
        """
        try:
            if agent not in self.agent_boundaries:
                return {
                    "valid": False,
                    "reason": f"Unknown agent: {agent}",
                    "alternatives": []
                }
            
            agent_config = self.agent_boundaries[agent]
            
            # Check allowed topics
            if action in agent_config["allowed_topics"]:
                return {
                    "valid": True,
                    "reason": "Action within agent capabilities",
                    "restrictions": []
                }
            
            # Check forbidden topics
            if action in agent_config["forbidden_topics"]:
                return {
                    "valid": False,
                    "reason": f"Action '{action}' is forbidden for {agent} agent",
                    "alternatives": self._suggest_alternatives(agent, action)
                }
            
            # Check escalation triggers
            if action in agent_config["escalation_triggers"]:
                return {
                    "valid": False,
                    "reason": f"Action '{action}' requires escalation",
                    "escalation_required": True,
                    "escalation_target": self._get_escalation_target(agent, action)
                }
            
            # Default: allow but log
            logger.warning(f"Uncategorized action '{action}' for agent '{agent}'")
            return {
                "valid": True,
                "reason": "Action not explicitly restricted",
                "warning": "Uncategorized action - review needed"
            }
            
        except Exception as e:
            logger.error(f"Error validating agent action: {e}")
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "alternatives": []
            }
    
    def _suggest_alternatives(self, agent: str, forbidden_action: str) -> List[str]:
        """Suggest alternative actions for forbidden ones."""
        agent_config = self.agent_boundaries[agent]
        allowed_actions = agent_config["allowed_topics"]
        
        # Simple keyword matching for suggestions
        suggestions = []
        forbidden_lower = forbidden_action.lower()
        
        for allowed in allowed_actions:
            if any(word in allowed.lower() for word in forbidden_lower.split("_")):
                suggestions.append(allowed)
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _get_escalation_target(self, agent: str, action: str) -> str:
        """Determine escalation target for an action."""
        escalation_map = {
            "customer": "support",
            "staff": "admin",
            "support": "admin",
            "analytics": "admin"
        }
        
        # Special cases
        if "legal" in action.lower():
            return "human_legal"
        elif "security" in action.lower():
            return "human_security"
        elif "financial" in action.lower() and agent != "admin":
            return "admin"
        
        return escalation_map.get(agent, "admin")
    
    async def filter_response_for_agent(
        self,
        agent: str,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Filter response content to be appropriate for agent namespace.
        
        Args:
            agent: Agent type
            response: Original response
            context: Optional context
            
        Returns:
            Filtered response appropriate for agent
        """
        try:
            if agent not in self.agent_boundaries:
                return response
            
            agent_config = self.agent_boundaries[agent]
            filtered_response = response
            
            # Remove forbidden topic content
            for forbidden_topic in agent_config["forbidden_topics"]:
                topic_keywords = forbidden_topic.replace("_", " ").split()
                for keyword in topic_keywords:
                    if keyword.lower() in filtered_response.lower():
                        # Replace with agent-appropriate message
                        replacement = self._get_topic_replacement_message(agent, forbidden_topic)
                        filtered_response = self._replace_topic_content(
                            filtered_response, keyword, replacement
                        )
            
            # Apply agent-specific formatting
            filtered_response = self._apply_agent_formatting(agent, filtered_response)
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"Error filtering response for agent: {e}")
            return response  # Return original on error
    
    def _get_topic_replacement_message(self, agent: str, forbidden_topic: str) -> str:
        """Get replacement message for forbidden topics."""
        messages = {
            "customer": {
                "admin_functions": "For administrative assistance, please contact our staff.",
                "user_management": "For account-related issues, please contact our support team.",
                "financial_data": "For billing inquiries, please contact our accounts team.",
                "system_configuration": "For technical issues, please contact our support team."
            },
            "staff": {
                "financial_data": "Financial information requires manager approval.",
                "user_management": "User account changes require admin access.",
                "system_configuration": "System changes require admin authorization."
            },
            "support": {
                "system_configuration": "System changes require technical team approval.",
                "staff_management": "Staff issues should be escalated to management."
            }
        }
        
        agent_messages = messages.get(agent, {})
        return agent_messages.get(
            forbidden_topic,
            f"This information requires different authorization level."
        )
    
    def _replace_topic_content(
        self,
        response: str,
        keyword: str,
        replacement: str
    ) -> str:
        """Replace topic-specific content with appropriate message."""
        # Simple replacement - could be enhanced with more sophisticated NLP
        response_lower = response.lower()
        keyword_lower = keyword.lower()
        
        if keyword_lower in response_lower:
            # Find sentences containing the keyword and replace them
            sentences = response.split('. ')
            filtered_sentences = []
            
            for sentence in sentences:
                if keyword_lower in sentence.lower():
                    filtered_sentences.append(replacement)
                else:
                    filtered_sentences.append(sentence)
            
            return '. '.join(filtered_sentences)
        
        return response
    
    def _apply_agent_formatting(self, agent: str, response: str) -> str:
        """Apply agent-specific formatting to response."""
        formatting_rules = {
            "customer": {
                "tone": "friendly and helpful",
                "prefix": "",
                "suffix": "\n\nHow else can I help you today?"
            },
            "admin": {
                "tone": "professional and comprehensive",
                "prefix": "",
                "suffix": "\n\nIs there anything else you need assistance with?"
            },
            "staff": {
                "tone": "supportive and instructional",
                "prefix": "",
                "suffix": "\n\nLet me know if you need additional guidance!"
            },
            "support": {
                "tone": "empathetic and solution-focused",
                "prefix": "",
                "suffix": "\n\nI'm here to help resolve this for you."
            },
            "analytics": {
                "tone": "analytical and data-driven",
                "prefix": "",
                "suffix": "\n\nWould you like me to analyze this data further?"
            }
        }
        
        rules = formatting_rules.get(agent, {})
        formatted_response = response
        
        if rules.get("prefix"):
            formatted_response = rules["prefix"] + formatted_response
        
        if rules.get("suffix"):
            formatted_response = formatted_response + rules["suffix"]
        
        return formatted_response
    
    async def get_namespace_status(self, agent: str) -> Dict[str, Any]:
        """Get namespace status and configuration for an agent."""
        try:
            if agent not in self.agent_boundaries:
                return {
                    "agent": agent,
                    "valid": False,
                    "error": f"Unknown agent: {agent}"
                }
            
            agent_config = self.agent_boundaries[agent]
            active_conversations = [
                conv_id for conv_id, context in self.conversations.items()
                if context.agent == agent
            ]
            
            return {
                "agent": agent,
                "valid": True,
                "namespace_boundaries": agent_config,
                "active_conversations": len(active_conversations),
                "isolation_rules": self.namespace_rules,
                "cross_agent_restrictions": [
                    restriction for key, restriction in self.cross_agent_restrictions.items()
                    if key.startswith(agent)
                ]
            }
            
        except Exception as e:
            return {
                "agent": agent,
                "valid": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on namespace service."""
        try:
            total_agents = len(self.agent_boundaries)
            total_conversations = len(self.conversations)
            
            # Check for any namespace violations
            violations = []
            for conv_id, context in self.conversations.items():
                if context.agent not in self.agent_boundaries:
                    violations.append(f"Invalid agent in conversation {conv_id}")
            
            return {
                "healthy": len(violations) == 0,
                "total_agents": total_agents,
                "total_conversations": total_conversations,
                "namespace_violations": violations,
                "isolation_enabled": self.namespace_rules["conversation_isolation"]["cross_agent_context"] == False,
                "last_check": datetime.utcnow()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow()
            }