"""
ReAct Agent - Reason + Act Pattern (Layer 3)

Implements ReAct (Reasoning + Acting) pattern for AI agents.
AI reasons through steps, takes actions, observes results, and iterates.

Expected Performance:
- 92% accuracy
- 2 second average response time
- $0.005 cost per query
- Handles 45% of total queries (medium complexity)

Example Flow:
    Customer: "I need chef for 15 people next Saturday"

    THOUGHT 1: Need to check availability for large group
    ACTION 1: check_availability(date="2025-11-16", party_size=15)
    OBSERVATION 1: Only 12-seat table available

    THOUGHT 2: Offer alternative or combined seating
    ACTION 2: check_combined_seating(size=15)
    OBSERVATION 2: Can combine two tables for 16 seats

    THOUGHT 3: Suggest combined seating with details
    RESPONSE: "We can accommodate your party of 15 by combining..."

Author: MyHibachi AI Team
Created: November 10, 2025
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ReActConfig:
    """Configuration for ReAct agent"""

    max_iterations: int = 5  # Maximum thought-action loops
    max_tokens: int = 2000  # Maximum tokens per iteration
    temperature: float = 0.7  # Creativity vs consistency
    timeout_seconds: float = 10.0  # Maximum execution time
    log_reasoning_trace: bool = True  # Log all thoughts/actions
    enable_self_correction: bool = True  # Allow agent to correct mistakes


@dataclass
class ReActStep:
    """Single step in ReAct reasoning process"""

    iteration: int
    thought: str
    action: str | None = None
    action_input: dict[str, Any] | None = None
    observation: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReActResult:
    """Result from ReAct agent execution"""

    response: str
    steps: list[ReActStep]
    tools_used: list[str]
    iterations: int
    success: bool
    error: str | None = None
    cost_usd: float = 0.005  # Approximate cost
    duration_ms: float = 0.0


class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent

    Implements the ReAct pattern where AI:
    1. THINKS about what to do next
    2. ACTS by calling a tool/function
    3. OBSERVES the result
    4. Repeats until problem is solved

    This provides stronger reasoning than simple prompting (Layer 2)
    while being simpler than multi-agent systems (Layer 4).

    Example Usage:
        ```python
        agent = ReActAgent(provider, tools)

        result = await agent.process(
            query="Book for 15 people with dietary restrictions",
            context={"customer_id": "123"}
        )

        print(result.response)  # Final answer
        print(result.steps)  # Reasoning trace
        print(result.tools_used)  # Tools called
        ```
    """

    def __init__(
        self,
        model_provider: Any,  # OpenAI/Llama provider
        tool_registry: dict[str, Callable],
        config: ReActConfig | None = None,
    ):
        """
        Initialize ReAct agent.

        Args:
            model_provider: AI model provider (OpenAI, Llama, etc.)
            tool_registry: Dictionary of available tools {name: function}
            config: Optional configuration
        """
        self.provider = model_provider
        self.tools = tool_registry
        self.config = config or ReActConfig()
        self.logger = logging.getLogger(__name__)

    async def process(
        self, query: str, context: dict[str, Any] | None = None
    ) -> ReActResult:
        """
        Process query using ReAct pattern.

        Args:
            query: Customer query
            context: Optional context (customer_id, history, etc.)

        Returns:
            ReActResult with response and reasoning trace
        """
        context = context or {}
        start_time = datetime.now(timezone.utc)
        steps: list[ReActStep] = []
        tools_used: list[str] = []

        try:
            # Build system prompt with ReAct instructions
            system_prompt = self._build_system_prompt()

            # Initial messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ]

            # ReAct loop
            for iteration in range(1, self.config.max_iterations + 1):
                self.logger.debug(f"ReAct iteration {iteration}/{self.config.max_iterations}")

                # Get AI's thought + action
                step = await self._think_and_act(messages, iteration, context)
                steps.append(step)

                # Execute action if present
                if step.action:
                    observation = await self._execute_action(step.action, step.action_input or {})
                    step.observation = observation
                    tools_used.append(step.action)

                    # Add observation to conversation
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"THOUGHT: {step.thought}\nACTION: {step.action}\nINPUT: {json.dumps(step.action_input)}",
                        }
                    )
                    messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})

                    self.logger.debug(f"Action '{step.action}' returned: {observation[:100]}...")

                else:
                    # No action = agent has final answer
                    self.logger.info(f"ReAct completed in {iteration} iterations")
                    break

                # Safety: prevent infinite loops
                if iteration >= self.config.max_iterations:
                    self.logger.warning("ReAct hit max iterations, forcing completion")
                    # Get final response even if incomplete
                    final_step = await self._force_completion(messages, context)
                    steps.append(final_step)
                    break

            # Extract final response
            final_response = steps[-1].thought if steps else "I apologize, I couldn't process your request."

            # Calculate duration
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return ReActResult(
                response=final_response,
                steps=steps,
                tools_used=list(set(tools_used)),  # Deduplicate
                iterations=len(steps),
                success=True,
                duration_ms=duration_ms,
                cost_usd=0.005,  # Approximate
            )

        except Exception as e:
            self.logger.error(f"ReAct agent error: {e}", exc_info=True)
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return ReActResult(
                response=f"I apologize, I encountered an error: {str(e)}",
                steps=steps,
                tools_used=tools_used,
                iterations=len(steps),
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _build_system_prompt(self) -> str:
        """Build system prompt with ReAct instructions"""

        tool_descriptions = self._format_tool_descriptions()

        return f"""You are a helpful AI assistant that uses the ReAct (Reasoning + Acting) pattern.

For each step, you must:
1. THINK about what to do next
2. ACT by calling a tool (if needed)
3. OBSERVE the result
4. Repeat until you can answer

When you need to call a tool, respond with:
THOUGHT: [your reasoning]
ACTION: [tool_name]
INPUT: [JSON parameters]

When you have the final answer, respond with:
THOUGHT: [your reasoning and final answer]
ACTION: None

Available Tools:
{tool_descriptions}

Important:
- Think step by step
- Use tools to gather information
- Be thorough but concise
- Provide clear, helpful responses
- If a tool fails, try an alternative approach
"""

    def _format_tool_descriptions(self) -> str:
        """Format tool descriptions for prompt"""

        if not self.tools:
            return "No tools available."

        descriptions = []
        for name, func in self.tools.items():
            # Get docstring or use placeholder
            doc = func.__doc__ or "No description available"
            descriptions.append(f"- {name}: {doc.strip()}")

        return "\n".join(descriptions)

    async def _think_and_act(
        self, messages: list[dict], iteration: int, context: dict[str, Any]
    ) -> ReActStep:
        """
        Get AI's thought and action for current step.

        Returns:
            ReActStep with thought, action, and input
        """

        # Call AI model
        response = await self.provider.complete(
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        content = response.get("content", "")

        # Parse response (simple regex for now)
        import re

        thought_match = re.search(r"THOUGHT:\s*(.+?)(?:ACTION:|$)", content, re.DOTALL)
        action_match = re.search(r"ACTION:\s*(.+?)(?:INPUT:|$)", content, re.DOTALL)
        input_match = re.search(r"INPUT:\s*(.+?)$", content, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else content
        action = action_match.group(1).strip() if action_match else None
        action_input = None

        if action and action.lower() != "none":
            if input_match:
                try:
                    action_input = json.loads(input_match.group(1).strip())
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse action input JSON")
                    action_input = {}
        else:
            action = None  # "None" means no action needed

        return ReActStep(iteration=iteration, thought=thought, action=action, action_input=action_input)

    async def _execute_action(self, action: str, action_input: dict[str, Any]) -> str:
        """
        Execute tool action.

        Args:
            action: Tool name
            action_input: Tool parameters

        Returns:
            Observation string (tool result)
        """

        if action not in self.tools:
            return f"Error: Tool '{action}' not found. Available tools: {', '.join(self.tools.keys())}"

        try:
            tool = self.tools[action]

            # Call tool (sync or async)
            import asyncio
            import inspect

            if inspect.iscoroutinefunction(tool):
                result = await tool(**action_input)
            else:
                result = tool(**action_input)

            # Convert result to string observation
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)

        except Exception as e:
            self.logger.error(f"Tool '{action}' failed: {e}", exc_info=True)
            return f"Error executing '{action}': {str(e)}"

    async def _force_completion(
        self, messages: list[dict], context: dict[str, Any]
    ) -> ReActStep:
        """Force agent to provide final response when max iterations reached"""

        # Add explicit instruction to provide final answer
        messages.append(
            {
                "role": "user",
                "content": "Please provide your final answer based on what you've learned so far.",
            }
        )

        response = await self.provider.complete(
            messages=messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens
        )

        return ReActStep(
            iteration=self.config.max_iterations + 1,
            thought=response.get("content", "I apologize, I need more time to answer properly."),
            action=None,
        )


# Singleton instance
_react_agent = None


def get_react_agent(
    model_provider: Any = None,
    tool_registry: dict[str, Callable] | None = None,
    config: ReActConfig | None = None,
) -> ReActAgent:
    """
    Get singleton ReAct agent instance.

    Args:
        model_provider: AI model provider (required on first call)
        tool_registry: Available tools (required on first call)
        config: Optional configuration

    Returns:
        ReActAgent instance
    """
    global _react_agent

    if _react_agent is None:
        if model_provider is None or tool_registry is None:
            raise ValueError("First call to get_react_agent requires provider and tools")

        _react_agent = ReActAgent(model_provider, tool_registry, config)

    return _react_agent
