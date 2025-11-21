"""
Model Ladder Service
Implements confidence-based model selection and escalation routing.
Provides intelligent routing: retrieval → GPT-5 nano → GPT-4.1 mini → human escalation.
"""

from datetime import UTC, datetime
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tiers in ascending order of capability and cost."""

    RETRIEVAL = "retrieval"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    HUMAN = "human"


class ConfidenceThreshold(str, Enum):
    """Confidence thresholds for model selection."""

    LOW = "low"  # 0.0 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.7
    HIGH = "high"  # 0.7 - 0.9
    VERY_HIGH = "very_high"  # 0.9 - 1.0


class ModelLadderService:
    """Service for intelligent model selection and escalation routing."""

    def __init__(self):
        # Model configurations
        self.model_configs = {
            ModelTier.RETRIEVAL: {
                "display_name": "Knowledge Base Retrieval",
                "description": "Fast retrieval from pre-indexed knowledge base",
                "cost_per_1k_tokens": 0.0,
                "average_latency_ms": 50,
                "max_tokens": 0,
                "confidence_range": (0.8, 1.0),
                "use_cases": ["faq_lookup", "exact_match", "simple_queries"],
                "fallback_to": ModelTier.GPT_4O_MINI,
            },
            ModelTier.GPT_4O_MINI: {
                "display_name": "GPT-4o Mini",
                "description": "Fast, efficient model for routine interactions",
                "cost_per_1k_tokens": 0.0001,
                "average_latency_ms": 800,
                "max_tokens": 4096,
                "confidence_range": (0.7, 0.95),
                "use_cases": [
                    "customer_service",
                    "simple_bookings",
                    "general_qa",
                ],
                "fallback_to": ModelTier.GPT_4O,
            },
            ModelTier.GPT_4O: {
                "display_name": "GPT-4o",
                "description": "Balanced model for complex reasoning",
                "cost_per_1k_tokens": 0.001,
                "average_latency_ms": 1500,
                "max_tokens": 8192,
                "confidence_range": (0.8, 0.98),
                "use_cases": [
                    "complex_bookings",
                    "admin_tasks",
                    "detailed_analysis",
                ],
                "fallback_to": ModelTier.GPT_4,
            },
            ModelTier.GPT_4: {
                "display_name": "GPT-4",
                "description": "Most capable model for complex reasoning",
                "cost_per_1k_tokens": 0.01,
                "average_latency_ms": 3000,
                "max_tokens": 8192,
                "confidence_range": (0.85, 0.99),
                "use_cases": [
                    "complex_analysis",
                    "strategic_decisions",
                    "error_resolution",
                ],
                "fallback_to": ModelTier.HUMAN,
            },
            ModelTier.HUMAN: {
                "display_name": "Human Agent",
                "description": "Human agent for complex or sensitive issues",
                "cost_per_1k_tokens": 1.0,  # Symbolic cost
                "average_latency_ms": 300000,  # 5 minutes
                "max_tokens": float("inf"),
                "confidence_range": (0.95, 1.0),
                "use_cases": ["escalations", "complaints", "legal_issues"],
                "fallback_to": None,
            },
        }

        # Agent-specific model limits
        self.agent_model_limits = {
            "customer": ModelTier.GPT_4O_MINI,
            "admin": ModelTier.GPT_4,
            "staff": ModelTier.GPT_4O_MINI,
            "support": ModelTier.GPT_4,
            "analytics": ModelTier.GPT_4,
        }

        # Complexity detection patterns
        self.complexity_patterns = {
            "simple": [
                "hello",
                "hi",
                "thanks",
                "yes",
                "no",
                "okay",
                "hours",
                "location",
                "phone",
                "email",
            ],
            "medium": [
                "booking",
                "reservation",
                "availability",
                "menu",
                "pricing",
                "group",
                "event",
                "party",
            ],
            "complex": [
                "cancel",
                "refund",
                "problem",
                "issue",
                "complaint",
                "allergy",
                "dietary",
                "special",
                "requirement",
            ],
            "escalation": [
                "legal",
                "lawyer",
                "sue",
                "terrible",
                "awful",
                "manager",
                "supervisor",
                "corporate",
            ],
        }

    async def select_model(
        self,
        message: str,
        agent: str,
        max_model: str | None = None,
        override: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Select appropriate model based on message complexity and agent limitations.

        Args:
            message: User message to analyze
            agent: Agent type making the request
            max_model: Maximum model tier allowed for agent
            override: Optional model override
            context: Additional context for selection

        Returns:
            Selected model identifier
        """
        try:
            # Handle explicit override
            if override:
                if self._validate_model_override(override, agent):
                    logger.info(
                        f"Using model override: {override} for agent: {agent}"
                    )
                    return override
                else:
                    logger.warning(
                        f"Invalid model override {override} for agent {agent}"
                    )

            # Determine maximum allowed model for agent
            agent_max = self.agent_model_limits.get(
                agent, ModelTier.GPT_4O_MINI
            )
            if max_model:
                try:
                    explicit_max = ModelTier(max_model)
                    # Use the more restrictive limit
                    if self._compare_model_tiers(explicit_max, agent_max) < 0:
                        agent_max = explicit_max
                except ValueError:
                    logger.warning(f"Invalid max_model: {max_model}")

            # Analyze message complexity
            complexity = await self._analyze_complexity(message, context)

            # Check for immediate escalation triggers
            if await self._should_escalate_immediately(message, agent):
                return self._get_highest_available_model(agent_max)

            # Select model based on complexity
            selected_model = await self._select_by_complexity(
                complexity, agent_max
            )

            logger.info(
                f"Selected model {selected_model} for agent {agent} (complexity: {complexity})"
            )
            return selected_model

        except Exception as e:
            logger.exception(f"Model selection error: {e}")
            # Fallback to safe default
            return "gpt-4o-mini"

    async def _analyze_complexity(
        self, message: str, context: dict[str, Any] | None = None
    ) -> str:
        """Analyze message complexity."""
        try:
            message_lower = message.lower()
            word_count = len(message.split())

            # Check for escalation triggers first
            if any(
                pattern in message_lower
                for pattern in self.complexity_patterns["escalation"]
            ):
                return "escalation"

            # Check for complex patterns
            complex_score = sum(
                1
                for pattern in self.complexity_patterns["complex"]
                if pattern in message_lower
            )

            # Check for medium patterns
            medium_score = sum(
                1
                for pattern in self.complexity_patterns["medium"]
                if pattern in message_lower
            )

            # Check for simple patterns
            simple_score = sum(
                1
                for pattern in self.complexity_patterns["simple"]
                if pattern in message_lower
            )

            # Consider message length
            length_factor = min(word_count / 20, 2.0)  # Cap at 2x multiplier

            # Calculate weighted scores
            complexity_score = (
                complex_score * 3 + medium_score * 2 + simple_score * 1
            ) * length_factor

            # Add context-based scoring
            if context:
                if context.get("conversation_length", 0) > 5:
                    complexity_score += (
                        1  # Longer conversations tend to be more complex
                    )

                if context.get("previous_escalation"):
                    complexity_score += (
                        2  # Previous escalation suggests complexity
                    )

            # Determine complexity level
            if complexity_score >= 8:
                return "escalation"
            elif complexity_score >= 5:
                return "complex"
            elif complexity_score >= 2:
                return "medium"
            else:
                return "simple"

        except Exception as e:
            logger.exception(f"Complexity analysis error: {e}")
            return "medium"  # Safe default

    async def _should_escalate_immediately(
        self, message: str, agent: str
    ) -> bool:
        """Check if message should immediately escalate to highest model."""
        message_lower = message.lower()

        # Critical escalation keywords
        critical_keywords = [
            "emergency",
            "urgent",
            "legal",
            "lawsuit",
            "sue",
            "discrimination",
            "harassment",
            "safety",
            "injury",
            "food poisoning",
            "allergic reaction",
        ]

        # Admin agents have different escalation rules
        if agent == "admin":
            admin_escalation_keywords = [
                "security breach",
                "hack",
                "data loss",
                "system down",
                "payment failure",
                "fraud",
            ]
            return any(
                keyword in message_lower
                for keyword in admin_escalation_keywords
            )

        return any(keyword in message_lower for keyword in critical_keywords)

    async def _select_by_complexity(
        self, complexity: str, max_model: ModelTier
    ) -> str:
        """Select model based on complexity level."""
        complexity_model_map = {
            "simple": ModelTier.RETRIEVAL,
            "medium": ModelTier.GPT_4O_MINI,
            "complex": ModelTier.GPT_4O,
            "escalation": ModelTier.GPT_4,
        }

        suggested_model = complexity_model_map.get(
            complexity, ModelTier.GPT_4O_MINI
        )

        # Ensure we don't exceed agent's maximum allowed model
        if self._compare_model_tiers(suggested_model, max_model) > 0:
            suggested_model = max_model

        return suggested_model.value

    def _compare_model_tiers(
        self, model1: ModelTier, model2: ModelTier
    ) -> int:
        """Compare model tiers. Returns: -1 if model1 < model2, 0 if equal, 1 if model1 > model2."""
        tier_order = [
            ModelTier.RETRIEVAL,
            ModelTier.GPT_4O_MINI,
            ModelTier.GPT_4O,
            ModelTier.GPT_4,
            ModelTier.HUMAN,
        ]

        try:
            index1 = tier_order.index(model1)
            index2 = tier_order.index(model2)

            if index1 < index2:
                return -1
            elif index1 > index2:
                return 1
            else:
                return 0
        except ValueError:
            return 0

    def _get_highest_available_model(self, max_model: ModelTier) -> str:
        """Get the highest available model within agent limits."""
        return max_model.value

    def _validate_model_override(self, override: str, agent: str) -> bool:
        """Validate if model override is allowed for agent."""
        try:
            override_tier = ModelTier(override)
            agent_max = self.agent_model_limits.get(
                agent, ModelTier.GPT_4O_MINI
            )

            return self._compare_model_tiers(override_tier, agent_max) <= 0

        except ValueError:
            return False

    async def get_model_info(self, model: str) -> dict[str, Any] | None:
        """Get information about a specific model."""
        try:
            model_tier = ModelTier(model)
            return self.model_configs.get(model_tier)
        except ValueError:
            return None

    async def estimate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> dict[str, float]:
        """
        Estimate cost for a model interaction.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost breakdown
        """
        try:
            model_info = await self.get_model_info(model)
            if not model_info:
                return {"total": 0.0, "input": 0.0, "output": 0.0}

            cost_per_1k = model_info["cost_per_1k_tokens"]

            # Different pricing for input/output (simplified)
            input_cost = (
                (input_tokens / 1000) * cost_per_1k * 0.5
            )  # Input is typically cheaper
            output_cost = (
                (output_tokens / 1000) * cost_per_1k * 1.5
            )  # Output is more expensive

            return {
                "total": input_cost + output_cost,
                "input": input_cost,
                "output": output_cost,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        except Exception as e:
            logger.exception(f"Cost estimation error: {e}")
            return {"total": 0.0, "input": 0.0, "output": 0.0}

    async def should_retry_with_higher_model(
        self,
        current_model: str,
        confidence: float,
        agent: str,
        error_type: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Determine if request should be retried with a higher-tier model.

        Args:
            current_model: Currently used model
            confidence: Confidence score of current response
            agent: Agent making the request
            error_type: Type of error encountered

        Returns:
            Tuple of (should_retry, suggested_model)
        """
        try:
            current_tier = ModelTier(current_model)
            agent_max = self.agent_model_limits.get(
                agent, ModelTier.GPT_4O_MINI
            )

            # Don't retry if already at maximum
            if current_tier == agent_max:
                return False, None

            # Don't retry if at human level
            if current_tier == ModelTier.HUMAN:
                return False, None

            # Retry conditions
            should_retry = False

            # Low confidence threshold
            if confidence < 0.6:
                should_retry = True

            # Specific error types that warrant retry
            if error_type in ["context_limit", "rate_limit", "model_error"]:
                should_retry = True

            if should_retry:
                # Get next tier model
                next_model = self._get_next_tier_model(current_tier, agent_max)
                return True, next_model.value if next_model else None

            return False, None

        except Exception as e:
            logger.exception(f"Retry evaluation error: {e}")
            return False, None

    def _get_next_tier_model(
        self, current: ModelTier, max_allowed: ModelTier
    ) -> ModelTier | None:
        """Get the next tier model within agent limits."""
        tier_order = [
            ModelTier.RETRIEVAL,
            ModelTier.GPT_4O_MINI,
            ModelTier.GPT_4O,
            ModelTier.GPT_4,
            ModelTier.HUMAN,
        ]

        try:
            current_index = tier_order.index(current)
            max_index = tier_order.index(max_allowed)

            next_index = current_index + 1
            if next_index <= max_index and next_index < len(tier_order):
                return tier_order[next_index]

            return None

        except ValueError:
            return None

    async def get_agent_model_limits(self, agent: str) -> dict[str, Any]:
        """Get model limits and recommendations for an agent."""
        try:
            max_model = self.agent_model_limits.get(
                agent, ModelTier.GPT_4O_MINI
            )

            # Get available models for agent
            available_models = []
            for tier in ModelTier:
                if self._compare_model_tiers(tier, max_model) <= 0:
                    model_info = self.model_configs[tier]
                    available_models.append(
                        {
                            "model": tier.value,
                            "display_name": model_info["display_name"],
                            "description": model_info["description"],
                            "cost_per_1k_tokens": model_info[
                                "cost_per_1k_tokens"
                            ],
                            "average_latency_ms": model_info[
                                "average_latency_ms"
                            ],
                        }
                    )

            return {
                "agent": agent,
                "max_model": max_model.value,
                "available_models": available_models,
                "total_models": len(available_models),
            }

        except Exception as e:
            logger.exception(f"Error getting agent model limits: {e}")
            return {
                "agent": agent,
                "max_model": "gpt-4o-mini",
                "available_models": [],
                "total_models": 0,
            }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on model ladder service."""
        try:
            total_models = len(self.model_configs)
            total_agents = len(self.agent_model_limits)

            # Test model selection
            test_selection = await self.select_model(
                message="test message", agent="customer"
            )

            return {
                "healthy": test_selection is not None,
                "total_models": total_models,
                "total_agents": total_agents,
                "available_tiers": [tier.value for tier in ModelTier],
                "test_selection": test_selection,
                "last_check": datetime.now(UTC),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now(UTC),
            }
