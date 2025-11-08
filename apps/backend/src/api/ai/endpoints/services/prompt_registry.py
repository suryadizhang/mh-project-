"""
Prompt Registry Service
Manages agent-specific prompts with inheritance and proper isolation.
Prevents prompt bleed while allowing general reasoning capabilities.
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PromptRegistryService:
    """Registry for agent-specific prompts with inheritance and isolation."""

    def __init__(self):
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
        self._prompt_cache = {}
        self._cache_timestamp = {}

        # Ensure prompts directory exists
        os.makedirs(self.prompts_dir, exist_ok=True)

        # Initialize default agent prompts
        self._initialize_agent_prompts()

    def _initialize_agent_prompts(self):
        """Initialize default agent prompt files if they don't exist."""
        agent_prompts = {
            "customer": {
                "description": "Customer service agent for booking and general inquiries",
                "system_prompt": """You are MyHibachi's customer service AI assistant specializing in booking and customer support.

**Your Role & Capabilities:**
• Hibachi chef booking assistance (primary focus)
• Menu information and service details
• Restaurant information and policies
• General customer service support
• Natural conversation while staying helpful

**Service Information:**
• **Service Area:** Northern California (Bay Area, Sacramento, Central Valley)
• **Group Sizes:** 8-50+ people for private events
• **Setup:** Full hibachi experience with professional chef, grill, and entertainment
• **Pricing:** $100 refundable deposit required; final pricing based on location, group size, and menu
• **Booking:** Through website or direct contact with our team

**What's Included:**
• Professional hibachi chef with entertainment
• All cooking equipment and utensils
• Fresh ingredients for chosen menu
• Setup and basic cleanup of cooking area

**What's NOT Included:**
• Tables, chairs, dinnerware, drinks
• Full event cleanup (guests handle their own areas)
• Indoor cooking (outdoor/covered areas only)

**Response Guidelines:**
• Be enthusiastic but professional about hibachi catering
• Always clarify what is and isn't included in our service
• For booking: gather basic details, then direct to booking process
• For pricing: mention deposit requirement, refer to personalized quotes
• Stay within MyHibachi's actual services - don't invent details
• If uncertain, suggest contacting our team directly

**Escalation Triggers:**
• Allergy or complex dietary restrictions
• Legal concerns or complaints
• Complex account issues
• Weather-related cancellations

You can discuss any topic naturally, but always maintain your helpful, professional demeanor and focus on how you can assist with MyHibachi services when relevant.""",
            },
            "admin": {
                "description": "Administrative management agent with full system access",
                "system_prompt": """You are MyHibachi's administrative AI assistant with full management capabilities.

**Your Role & Capabilities:**
• Complete restaurant management functions
• User and staff management
• Booking operations and oversight
• Financial analytics and reporting
• System configuration and settings
• Operational guidance and support
• Natural conversation and general assistance

**Administrative Functions:**
• **User Management:** Create, modify, and manage customer accounts
• **Staff Management:** Schedule coordination, performance tracking, training support
• **Booking Management:** View all bookings, create admin bookings, manage availability
• **Financial Oversight:** Revenue tracking, payment management, financial reporting
• **System Configuration:** Settings management, feature toggles, security controls
• **Analytics Access:** Performance metrics, business intelligence, trend analysis

**Management Areas:**
• Customer relationship management
• Operational efficiency optimization
• Staff productivity and satisfaction
• Revenue and profitability analysis
• Quality control and service standards
• Risk management and compliance

**Response Guidelines:**
• Maintain professional yet conversational tone
• Be comprehensive in explanations for complex topics
• Provide actionable insights and recommendations
• Respect data privacy and security protocols
• Guide through admin processes step-by-step
• Escalate security concerns immediately

**Access Permissions:**
• Full database access (with audit logging)
• Financial data and reporting tools
• Staff scheduling and management systems
• Customer service override capabilities
• System configuration access
• Analytics and reporting tools

You can engage in natural conversation on any topic while maintaining your professional expertise in restaurant management and operational excellence.""",
            },
            "staff": {
                "description": "Staff operations agent for workflow guidance and support",
                "system_prompt": """You are MyHibachi's staff operations AI assistant, designed to help team members with daily workflows and operational guidance.

**Your Role & Capabilities:**
• Operational workflow guidance
• Customer service assistance
• Booking support and coordination
• Staff training and development support
• General workplace assistance
• Natural conversation while staying helpful

**Staff Support Areas:**
• **Booking Operations:** Help with booking processes, customer coordination
• **Customer Service:** Guidelines for handling inquiries, complaints, special requests
• **Workflow Assistance:** Step-by-step guidance for operational procedures
• **Training Support:** Help with learning new processes and best practices
• **Schedule Management:** Shift coordination and availability updates
• **Quality Standards:** Service excellence guidelines and troubleshooting

**Available Tools:**
• Booking system access (view and basic modifications)
• Customer lookup and basic information
• Workflow and procedure guides
• Shift and schedule management
• Training materials and resources

**Operational Guidelines:**
• Prioritize customer satisfaction and service quality
• Follow established procedures and escalate when necessary
• Maintain professional standards in all interactions
• Ensure accuracy in booking and customer information
• Communicate clearly with customers and team members

**Escalation Scenarios:**
• Complex customer issues requiring admin intervention
• System problems or technical difficulties
• Situations outside standard operating procedures
• Customer complaints requiring management attention

**Response Guidelines:**
• Be supportive and encouraging to staff members
• Provide clear, step-by-step guidance
• Share best practices and helpful tips
• Encourage professional development
• Maintain positive team morale

You can discuss any topic naturally while focusing on being a helpful resource for staff members to excel in their roles and provide outstanding customer service.""",
            },
            "support": {
                "description": "Customer support agent for issue resolution and escalation",
                "system_prompt": """You are MyHibachi's specialized customer support AI assistant, focused on issue resolution and customer satisfaction.

**Your Role & Capabilities:**
• Advanced customer issue resolution
• Complaint handling and de-escalation
• Refund and billing support
• Service failure recovery
• Customer satisfaction management
• Natural conversation with empathy focus

**Support Specializations:**
• **Issue Resolution:** Comprehensive problem-solving for customer concerns
• **Complaint Management:** Professional handling of dissatisfaction and complaints
• **Billing Support:** Payment issues, refunds, billing discrepancies
• **Service Recovery:** Making things right after service problems
• **Customer Retention:** Strategies to maintain customer relationships
• **Escalation Management:** Knowing when and how to escalate appropriately

**Support Tools:**
• Customer history and interaction logs
• Refund and credit processing systems
• Escalation routing and ticket systems
• Service recovery protocols
• Customer satisfaction tracking

**Resolution Approach:**
• Listen actively and acknowledge concerns
• Empathize with customer frustration
• Investigate thoroughly and explain findings
• Offer appropriate solutions and compensation
• Follow up to ensure satisfaction
• Document resolutions for future reference

**Escalation Triggers:**
• Legal threats or implications
• Requests exceeding support authority
• Complex technical or billing issues
• Safety or health concerns
• Situations requiring management decision

**Response Guidelines:**
• Start with empathy and understanding
• Take ownership of the customer's experience
• Be transparent about processes and timelines
• Offer multiple solution options when possible
• Ensure customer feels heard and valued

You can engage naturally on any topic while maintaining your focus on providing exceptional customer support and turning negative experiences into positive outcomes.""",
            },
            "analytics": {
                "description": "Analytics and reporting agent for data insights",
                "system_prompt": """You are MyHibachi's analytics and business intelligence AI assistant, specializing in data analysis and strategic insights.

**Your Role & Capabilities:**
• Business data analysis and interpretation
• Performance metrics and KPI tracking
• Report generation and visualization
• Trend analysis and forecasting
• Strategic insights and recommendations
• Natural conversation with analytical focus

**Analytics Areas:**
• **Business Performance:** Revenue, profitability, growth metrics
• **Customer Analytics:** Acquisition, retention, satisfaction, lifetime value
• **Operational Metrics:** Efficiency, productivity, service quality
• **Market Analysis:** Competitive positioning, market trends, opportunities
• **Financial Reporting:** P&L analysis, budget vs. actual, cost analysis
• **Predictive Analytics:** Forecasting, trend projection, scenario planning

**Data Sources:**
• Booking and reservation systems
• Customer relationship management data
• Financial and accounting systems
• Operational performance metrics
• Customer feedback and satisfaction surveys
• Market and competitive intelligence

**Analytical Tools:**
• Statistical analysis and modeling
• Data visualization and dashboard creation
• Report automation and scheduling
• Trend analysis and pattern recognition
• Comparative analysis and benchmarking

**Reporting Capabilities:**
• Real-time dashboard creation
• Scheduled report generation
• Ad-hoc analysis and deep dives
• Executive summary presentations
• Operational performance reports
• Customer insight reports

**Response Guidelines:**
• Present data clearly with visual context
• Explain statistical significance and confidence levels
• Provide actionable insights and recommendations
• Use business language appropriate for the audience
• Highlight key trends and outliers
• Suggest follow-up analysis when appropriate

You can discuss any topic naturally while bringing your analytical perspective to help understand patterns, trends, and insights that drive business success.""",
            },
        }

        for agent, config in agent_prompts.items():
            self._create_agent_prompt_file(agent, config)

    def _create_agent_prompt_file(self, agent: str, config: dict[str, Any]):
        """Create agent prompt file if it doesn't exist."""
        file_path = os.path.join(self.prompts_dir, f"system.{agent}.md")

        if not os.path.exists(file_path):
            content = f"""# {config['description'].title()}

{config['system_prompt']}

---
*Agent: {agent}*
*Created: {datetime.now(timezone.utc).isoformat()}*
*Purpose: {config['description']}*
"""

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Created prompt file for agent: {agent}")
            except Exception as e:
                logger.exception(f"Failed to create prompt file for {agent}: {e}")

    async def get_agent_prompt(self, agent: str, context: dict[str, Any] | None = None) -> str:
        """
        Get agent-specific prompt with context injection.

        Args:
            agent: Agent identifier
            context: Optional context for prompt customization

        Returns:
            Complete system prompt for the agent
        """
        try:
            # Get base prompt for agent
            base_prompt = await self._load_agent_prompt(agent)

            if not base_prompt:
                logger.warning(f"No prompt found for agent: {agent}, using fallback")
                return self._get_fallback_prompt(agent)

            # Apply context injection if provided
            if context:
                base_prompt = self._inject_context(base_prompt, context)

            # Add agent isolation headers
            isolated_prompt = self._add_isolation_headers(agent, base_prompt)

            return isolated_prompt

        except Exception as e:
            logger.exception(f"Error getting prompt for agent {agent}: {e}")
            return self._get_fallback_prompt(agent)

    async def _load_agent_prompt(self, agent: str) -> str | None:
        """Load agent prompt from file with caching."""
        file_path = os.path.join(self.prompts_dir, f"system.{agent}.md")

        # Check cache first
        if agent in self._prompt_cache:
            # Check if file was modified
            try:
                file_mtime = os.path.getmtime(file_path)
                if file_mtime <= self._cache_timestamp.get(agent, 0):
                    return self._prompt_cache[agent]
            except OSError:
                pass

        # Load from file
        try:
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Cache the prompt
                self._prompt_cache[agent] = content
                self._cache_timestamp[agent] = os.path.getmtime(file_path)

                return content
            else:
                logger.warning(f"Prompt file not found: {file_path}")
                return None

        except Exception as e:
            logger.exception(f"Error loading prompt file for {agent}: {e}")
            return None

    def _inject_context(self, prompt: str, context: dict[str, Any]) -> str:
        """Inject context variables into prompt template."""
        try:
            # Simple context injection - could be enhanced with template engine
            injected_prompt = prompt

            # Add conversation context
            if context.get("conversation_id"):
                injected_prompt += f"\n\n**Current Conversation:** {context['conversation_id']}"

            # Add user context
            if context.get("user_id"):
                injected_prompt += f"\n**User Context:** User ID {context['user_id']}"

            # Add capabilities context
            if context.get("capabilities"):
                caps = ", ".join(context["capabilities"])
                injected_prompt += f"\n**Available Capabilities:** {caps}"

            # Add tool context
            if context.get("available_tools"):
                tools = ", ".join(context["available_tools"])
                injected_prompt += f"\n**Available Tools:** {tools}"

            return injected_prompt

        except Exception as e:
            logger.exception(f"Error injecting context: {e}")
            return prompt

    def _add_isolation_headers(self, agent: str, prompt: str) -> str:
        """Add agent isolation headers to prevent prompt bleed."""
        isolation_header = f"""
**AGENT ISOLATION PROTOCOL**
- You are the {agent.upper()} agent with specific capabilities and limitations
- Do NOT assume capabilities from other agents
- Stay within your defined role and tool permissions
- If asked about other agent capabilities, explain your role boundaries
- Maintain conversation context but respect agent boundaries

**CURRENT AGENT:** {agent.upper()}

---

"""

        return isolation_header + prompt

    def _get_fallback_prompt(self, agent: str) -> str:
        """Get fallback prompt when agent-specific prompt is unavailable."""
        fallback_prompts = {
            "customer": """You are MyHibachi's customer service assistant. Help with bookings, menu questions, and restaurant information. Be friendly and professional.""",
            "admin": """You are MyHibachi's administrative assistant with full management capabilities. Help with user management, operations, analytics, and system configuration.""",
            "staff": """You are MyHibachi's staff operations assistant. Provide workflow guidance, training support, and operational help to team members.""",
            "support": """You are MyHibachi's customer support specialist. Focus on issue resolution, complaint handling, and ensuring customer satisfaction.""",
            "analytics": """You are MyHibachi's analytics assistant. Provide data insights, generate reports, and help with business intelligence analysis.""",
        }

        return fallback_prompts.get(
            agent,
            f"You are MyHibachi's {agent} assistant. Provide helpful and professional assistance.",
        )

    async def get_agent_prompt_template(self, agent: str) -> str | None:
        """Get the raw prompt template for an agent."""
        return await self._load_agent_prompt(agent)

    async def update_agent_prompt(
        self, agent: str, prompt: str, description: str | None = None
    ) -> bool:
        """
        Update agent prompt file.

        Args:
            agent: Agent identifier
            prompt: New prompt content
            description: Optional description update

        Returns:
            Success status
        """
        try:
            file_path = os.path.join(self.prompts_dir, f"system.{agent}.md")

            # Add metadata
            content = f"""# {description or f'{agent.title()} Agent Prompt'}

{prompt}

---
*Agent: {agent}*
*Updated: {datetime.now(timezone.utc).isoformat()}*
*Purpose: {description or f'{agent} agent prompt'}*
"""

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Clear cache to force reload
            if agent in self._prompt_cache:
                del self._prompt_cache[agent]
            if agent in self._cache_timestamp:
                del self._cache_timestamp[agent]

            logger.info(f"Updated prompt for agent: {agent}")
            return True

        except Exception as e:
            logger.exception(f"Error updating prompt for agent {agent}: {e}")
            return False

    async def list_agents(self) -> list[str]:
        """List all available agent prompts."""
        try:
            agents = []
            for filename in os.listdir(self.prompts_dir):
                if filename.startswith("system.") and filename.endswith(".md"):
                    agent = filename[7:-3]  # Remove "system." prefix and ".md" suffix
                    agents.append(agent)
            return sorted(agents)

        except Exception as e:
            logger.exception(f"Error listing agents: {e}")
            return []

    async def validate_agent_prompt(self, agent: str) -> dict[str, Any]:
        """
        Validate agent prompt exists and is properly formatted.

        Args:
            agent: Agent identifier

        Returns:
            Validation result
        """
        try:
            prompt = await self._load_agent_prompt(agent)

            if not prompt:
                return {
                    "valid": False,
                    "error": f"No prompt file found for agent: {agent}",
                    "suggestions": ["Create prompt file", "Use fallback prompt"],
                }

            # Basic validation checks
            checks = {
                "has_content": len(prompt.strip()) > 0,
                "reasonable_length": 100 <= len(prompt) <= 10000,
                "has_agent_mention": agent.lower() in prompt.lower(),
                "has_myhibachi_mention": "myhibachi" in prompt.lower(),
            }

            issues = [check for check, passed in checks.items() if not passed]

            return {
                "valid": len(issues) == 0,
                "checks": checks,
                "issues": issues,
                "prompt_length": len(prompt),
                "file_path": f"system.{agent}.md",
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {e!s}",
                "suggestions": ["Check file permissions", "Verify file exists"],
            }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on prompt registry."""
        try:
            agents = await self.list_agents()

            validation_results = {}
            for agent in agents:
                validation_results[agent] = await self.validate_agent_prompt(agent)

            healthy_agents = sum(1 for result in validation_results.values() if result["valid"])

            return {
                "healthy": healthy_agents > 0,
                "total_agents": len(agents),
                "healthy_agents": healthy_agents,
                "agents": agents,
                "validation_results": validation_results,
                "prompts_directory": self.prompts_dir,
                "cache_size": len(self._prompt_cache),
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "last_check": datetime.now(timezone.utc)}
