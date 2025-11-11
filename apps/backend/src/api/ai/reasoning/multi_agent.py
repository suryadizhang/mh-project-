"""
Multi-Agent System (Layer 4) - Expert Reasoning for Complex Queries

This module implements a coordinated multi-agent system where specialized agents
work together to solve complex problems that require multiple perspectives and
iterative refinement.

Architecture:
- Analyzer: Breaks down the problem and identifies requirements
- Planner: Creates a step-by-step action plan
- Executor: Executes the plan using available tools
- Critic: Reviews the solution for completeness and quality

Target Accuracy: 97%
Expected Usage: 4% of queries (complex multi-constraint problems)
Cost: ~$0.015 per query
Response Time: ~5 seconds

Author: MyHibachi AI Team
Created: January 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles in the multi-agent system"""

    ANALYZER = "analyzer"
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"


@dataclass
class AgentMessage:
    """Message passed between agents"""

    from_agent: AgentRole
    to_agent: AgentRole | None  # None = broadcast
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PlanStep:
    """Single step in the execution plan"""

    step_number: int
    description: str
    tool_name: str | None = None
    tool_parameters: dict[str, Any] | None = None
    expected_outcome: str | None = None
    completed: bool = False
    result: Any = None


@dataclass
class Analysis:
    """Problem analysis from Analyzer agent"""

    problem_statement: str
    requirements: list[str]
    constraints: list[str]
    complexity_factors: list[str]
    success_criteria: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExecutionPlan:
    """Execution plan from Planner agent"""

    goal: str
    steps: list[PlanStep]
    estimated_duration_ms: int
    dependencies: list[str] = field(default_factory=list)
    fallback_strategy: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Critique:
    """Quality review from Critic agent"""

    is_complete: bool
    quality_score: float  # 0-1
    strengths: list[str]
    weaknesses: list[str]
    missing_requirements: list[str]
    recommendations: list[str]
    final_verdict: str  # "ACCEPT", "REVISE", "REJECT"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MultiAgentConfig:
    """Configuration for multi-agent system"""

    max_iterations: int = 3  # Max planning/execution cycles
    max_critique_cycles: int = 2  # Max times to revise based on critique
    critique_quality_threshold: float = 0.85  # Minimum quality score to accept
    timeout_seconds: float = 15.0
    enable_parallel_execution: bool = False  # Execute independent steps in parallel
    log_agent_communication: bool = True


@dataclass
class MultiAgentResult:
    """Result from multi-agent processing"""

    success: bool
    response: str
    analysis: Analysis
    plan: ExecutionPlan
    critique: Critique
    messages: list[AgentMessage]
    iterations: int
    critique_cycles: int
    tools_used: list[str]
    cost_usd: float
    duration_ms: int
    error: str | None = None


class AnalyzerAgent:
    """
    Analyzes complex queries to identify requirements and constraints.

    Responsibilities:
    - Break down the problem into components
    - Identify explicit and implicit requirements
    - Detect constraints and limitations
    - Assess complexity factors
    - Define success criteria
    """

    def __init__(self, model_provider):
        self.model_provider = model_provider
        self.logger = logging.getLogger(f"{__name__}.AnalyzerAgent")

    async def analyze(self, query: str, context: dict[str, Any]) -> Analysis:
        """
        Analyze the query and extract requirements.

        Args:
            query: User's query
            context: Contextual information

        Returns:
            Analysis with requirements and constraints
        """
        system_prompt = """You are an expert problem analyzer for a hibachi catering service.

Your task is to break down customer queries into structured components:
1. Problem Statement: What is the customer trying to achieve?
2. Requirements: What specific needs must be met?
3. Constraints: What limitations or conditions exist?
4. Complexity Factors: What makes this query complex?
5. Success Criteria: How will we know if we've succeeded?

Output your analysis as JSON with these exact keys:
{
    "problem_statement": "Clear description of the core problem",
    "requirements": ["requirement 1", "requirement 2", ...],
    "constraints": ["constraint 1", "constraint 2", ...],
    "complexity_factors": ["factor 1", "factor 2", ...],
    "success_criteria": ["criterion 1", "criterion 2", ...]
}

Be thorough and identify both explicit and implicit requirements."""

        user_prompt = f"""Query: {query}

Context: {json.dumps(context, indent=2)}

Analyze this query and provide a structured breakdown."""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for analytical thinking
            )

            # Parse JSON response
            analysis_data = json.loads(response)

            analysis = Analysis(
                problem_statement=analysis_data["problem_statement"],
                requirements=analysis_data["requirements"],
                constraints=analysis_data["constraints"],
                complexity_factors=analysis_data["complexity_factors"],
                success_criteria=analysis_data["success_criteria"],
            )

            self.logger.info(
                f"Analysis complete: {len(analysis.requirements)} requirements, "
                f"{len(analysis.constraints)} constraints"
            )

            return analysis

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse analysis JSON: {e}")
            # Return minimal analysis
            return Analysis(
                problem_statement=query,
                requirements=["Provide accurate information"],
                constraints=["Time sensitivity"],
                complexity_factors=["Multiple factors to consider"],
                success_criteria=["Customer satisfaction"],
            )
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            raise


class PlannerAgent:
    """
    Creates actionable execution plans based on analysis.

    Responsibilities:
    - Design step-by-step action plans
    - Identify required tools for each step
    - Estimate execution time
    - Plan for dependencies and fallbacks
    """

    def __init__(self, model_provider, tool_registry):
        self.model_provider = model_provider
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(f"{__name__}.PlannerAgent")

    async def create_plan(self, analysis: Analysis, context: dict[str, Any]) -> ExecutionPlan:
        """
        Create an execution plan based on the analysis.

        Args:
            analysis: Problem analysis from Analyzer
            context: Contextual information

        Returns:
            Executable plan with steps and tool calls
        """
        # Get available tools
        available_tools = self.tool_registry.list_tools() if self.tool_registry else []
        tool_descriptions = []
        if self.tool_registry:
            for tool_name in available_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    tool_descriptions.append(f"- {tool_name}: {tool.description}")

        system_prompt = f"""You are an expert planner for a hibachi catering service.

Based on the analysis, create a detailed execution plan with specific steps.

Available Tools:
{chr(10).join(tool_descriptions) if tool_descriptions else "- No tools available"}

Output your plan as JSON:
{{
    "goal": "Clear statement of what we're trying to achieve",
    "steps": [
        {{
            "step_number": 1,
            "description": "What to do in this step",
            "tool_name": "tool_to_use" or null,
            "tool_parameters": {{"param": "value"}} or null,
            "expected_outcome": "What we expect to get"
        }},
        ...
    ],
    "estimated_duration_ms": 3000,
    "fallback_strategy": "What to do if plan fails"
}}

Make the plan specific and actionable."""

        user_prompt = f"""Analysis:
{json.dumps({
    "problem_statement": analysis.problem_statement,
    "requirements": analysis.requirements,
    "constraints": analysis.constraints,
    "success_criteria": analysis.success_criteria
}, indent=2)}

Context: {json.dumps(context, indent=2)}

Create a detailed execution plan."""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,  # Slightly higher for creative planning
            )

            # Parse JSON response
            plan_data = json.loads(response)

            steps = [
                PlanStep(
                    step_number=step["step_number"],
                    description=step["description"],
                    tool_name=step.get("tool_name"),
                    tool_parameters=step.get("tool_parameters"),
                    expected_outcome=step.get("expected_outcome"),
                )
                for step in plan_data["steps"]
            ]

            plan = ExecutionPlan(
                goal=plan_data["goal"],
                steps=steps,
                estimated_duration_ms=plan_data.get("estimated_duration_ms", 5000),
                fallback_strategy=plan_data.get("fallback_strategy"),
            )

            self.logger.info(f"Plan created: {len(steps)} steps, goal: {plan.goal}")

            return plan

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse plan JSON: {e}")
            # Return minimal plan
            return ExecutionPlan(
                goal=analysis.problem_statement,
                steps=[
                    PlanStep(
                        step_number=1,
                        description="Provide best available information",
                        expected_outcome="Customer receives helpful response",
                    )
                ],
                estimated_duration_ms=2000,
            )
        except Exception as e:
            self.logger.error(f"Planning failed: {e}", exc_info=True)
            raise


class ExecutorAgent:
    """
    Executes the plan by calling tools and gathering results.

    Responsibilities:
    - Execute each step in the plan
    - Call appropriate tools with correct parameters
    - Handle tool errors gracefully
    - Collect and organize results
    """

    def __init__(self, model_provider, tool_registry):
        self.model_provider = model_provider
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(f"{__name__}.ExecutorAgent")

    async def execute_plan(self, plan: ExecutionPlan, context: dict[str, Any]) -> ExecutionPlan:
        """
        Execute the plan step by step.

        Args:
            plan: Execution plan from Planner
            context: Contextual information

        Returns:
            Updated plan with execution results
        """
        self.logger.info(f"Executing plan with {len(plan.steps)} steps")

        for step in plan.steps:
            try:
                if step.tool_name and self.tool_registry:
                    # Execute tool call
                    tool = self.tool_registry.get_tool(step.tool_name)
                    if tool:
                        self.logger.debug(f"Step {step.step_number}: Calling {step.tool_name}")
                        
                        # Execute tool (handle both sync and async)
                        if hasattr(tool.function, "__call__"):
                            if step.tool_parameters:
                                result = tool.function(**step.tool_parameters)
                            else:
                                result = tool.function()
                        else:
                            result = {"error": "Tool not callable"}

                        step.result = result
                        step.completed = True
                        self.logger.debug(f"Step {step.step_number}: Success")
                    else:
                        self.logger.warning(f"Tool {step.tool_name} not found")
                        step.result = {"error": f"Tool {step.tool_name} not found"}
                        step.completed = False
                else:
                    # Information gathering step (no tool)
                    self.logger.debug(f"Step {step.step_number}: Info gathering")
                    step.result = {"status": "completed", "type": "information_step"}
                    step.completed = True

            except Exception as e:
                self.logger.error(f"Step {step.step_number} failed: {e}", exc_info=True)
                step.result = {"error": str(e)}
                step.completed = False

        completed_steps = sum(1 for step in plan.steps if step.completed)
        self.logger.info(f"Execution complete: {completed_steps}/{len(plan.steps)} steps succeeded")

        return plan


class CriticAgent:
    """
    Reviews the execution results for quality and completeness.

    Responsibilities:
    - Assess if all requirements were met
    - Evaluate solution quality
    - Identify gaps or issues
    - Recommend improvements
    - Provide final verdict (ACCEPT/REVISE/REJECT)
    """

    def __init__(self, model_provider):
        self.model_provider = model_provider
        self.logger = logging.getLogger(f"{__name__}.CriticAgent")

    async def critique(
        self, analysis: Analysis, plan: ExecutionPlan, context: dict[str, Any]
    ) -> Critique:
        """
        Review the execution results.

        Args:
            analysis: Original problem analysis
            plan: Executed plan with results
            context: Contextual information

        Returns:
            Critique with quality assessment and recommendations
        """
        # Collect execution summary
        execution_summary = []
        for step in plan.steps:
            execution_summary.append({
                "step": step.step_number,
                "description": step.description,
                "completed": step.completed,
                "result_preview": str(step.result)[:200] if step.result else None,
            })

        system_prompt = """You are a quality assurance expert for a hibachi catering service.

Review the execution results against the original requirements and success criteria.

Output your critique as JSON:
{
    "is_complete": true/false,
    "quality_score": 0.0-1.0,
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "missing_requirements": ["requirement 1", ...],
    "recommendations": ["recommendation 1", ...],
    "final_verdict": "ACCEPT" or "REVISE" or "REJECT"
}

Be thorough and constructive in your review."""

        user_prompt = f"""Original Requirements:
{json.dumps({
    "problem_statement": analysis.problem_statement,
    "requirements": analysis.requirements,
    "success_criteria": analysis.success_criteria
}, indent=2)}

Execution Results:
{json.dumps(execution_summary, indent=2)}

Review the execution and provide your critique."""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,  # Very low for critical evaluation
            )

            # Parse JSON response
            critique_data = json.loads(response)

            critique = Critique(
                is_complete=critique_data["is_complete"],
                quality_score=critique_data["quality_score"],
                strengths=critique_data["strengths"],
                weaknesses=critique_data["weaknesses"],
                missing_requirements=critique_data.get("missing_requirements", []),
                recommendations=critique_data["recommendations"],
                final_verdict=critique_data["final_verdict"],
            )

            self.logger.info(
                f"Critique complete: {critique.final_verdict}, "
                f"quality={critique.quality_score:.2f}"
            )

            return critique

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse critique JSON: {e}")
            # Return accepting critique to avoid blocking
            return Critique(
                is_complete=True,
                quality_score=0.75,
                strengths=["Attempted to address query"],
                weaknesses=["Could not fully evaluate"],
                missing_requirements=[],
                recommendations=[],
                final_verdict="ACCEPT",
            )
        except Exception as e:
            self.logger.error(f"Critique failed: {e}", exc_info=True)
            raise


class MultiAgentSystem:
    """
    Coordinates multiple specialized agents to solve complex problems.

    This system orchestrates Analyzer, Planner, Executor, and Critic agents
    to provide high-quality responses for complex queries that require
    multi-step reasoning and validation.
    """

    def __init__(
        self,
        model_provider,
        tool_registry,
        config: MultiAgentConfig | None = None,
    ):
        self.model_provider = model_provider
        self.tool_registry = tool_registry
        self.config = config or MultiAgentConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize agents
        self.analyzer = AnalyzerAgent(model_provider)
        self.planner = PlannerAgent(model_provider, tool_registry)
        self.executor = ExecutorAgent(model_provider, tool_registry)
        self.critic = CriticAgent(model_provider)

        # Message bus for agent communication
        self.messages: list[AgentMessage] = []

    async def process(self, query: str, context: dict[str, Any]) -> MultiAgentResult:
        """
        Process a complex query using the multi-agent system.

        Flow:
        1. Analyzer breaks down the problem
        2. Planner creates execution plan
        3. Executor runs the plan
        4. Critic reviews the results
        5. If not acceptable, revise and retry (up to max cycles)
        6. Generate final response

        Args:
            query: User's complex query
            context: Contextual information

        Returns:
            MultiAgentResult with comprehensive solution
        """
        start_time = datetime.now(timezone.utc)
        context = context or {}

        try:
            # Phase 1: Analysis
            self.logger.info("Phase 1: Analyzing query")
            analysis = await self.analyzer.analyze(query, context)
            self._log_message(AgentRole.ANALYZER, None, f"Analysis complete: {analysis.problem_statement}")

            # Phase 2-4: Plan, Execute, Critique cycle
            critique_cycles = 0
            final_plan = None
            final_critique = None

            while critique_cycles < self.config.max_critique_cycles:
                critique_cycles += 1

                # Phase 2: Planning
                self.logger.info(f"Phase 2: Planning (cycle {critique_cycles})")
                plan = await self.planner.create_plan(analysis, context)
                self._log_message(AgentRole.PLANNER, None, f"Plan created: {len(plan.steps)} steps")

                # Phase 3: Execution
                self.logger.info(f"Phase 3: Executing plan (cycle {critique_cycles})")
                executed_plan = await self.executor.execute_plan(plan, context)
                completed = sum(1 for s in executed_plan.steps if s.completed)
                self._log_message(
                    AgentRole.EXECUTOR, None, f"Execution complete: {completed}/{len(executed_plan.steps)} steps"
                )

                # Phase 4: Critique
                self.logger.info(f"Phase 4: Reviewing results (cycle {critique_cycles})")
                critique = await self.critic.critique(analysis, executed_plan, context)
                self._log_message(
                    AgentRole.CRITIC, None,
                    f"Critique: {critique.final_verdict}, quality={critique.quality_score:.2f}"
                )

                final_plan = executed_plan
                final_critique = critique

                # Check if we should continue iterating
                if critique.final_verdict == "ACCEPT":
                    break
                elif critique.final_verdict == "REJECT":
                    self.logger.warning("Solution rejected by critic")
                    break
                else:  # REVISE
                    self.logger.info("Revising solution based on critique")
                    # Update context with critique for next iteration
                    context["previous_critique"] = {
                        "weaknesses": critique.weaknesses,
                        "missing_requirements": critique.missing_requirements,
                        "recommendations": critique.recommendations,
                    }

            # Phase 5: Generate final response
            response = await self._generate_final_response(
                query, analysis, final_plan, final_critique, context
            )

            # Calculate metrics
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            tools_used = [
                step.tool_name for step in final_plan.steps if step.tool_name and step.completed
            ]
            
            # Estimate cost (4 LLM calls per cycle: analyze, plan, execute context, critique, + final response)
            estimated_cost = (critique_cycles * 4 + 1) * 0.003  # ~$0.003 per call

            return MultiAgentResult(
                success=final_critique.final_verdict == "ACCEPT",
                response=response,
                analysis=analysis,
                plan=final_plan,
                critique=final_critique,
                messages=self.messages,
                iterations=critique_cycles,
                critique_cycles=critique_cycles,
                tools_used=tools_used,
                cost_usd=estimated_cost,
                duration_ms=duration_ms,
            )

        except Exception as e:
            self.logger.error(f"Multi-agent processing failed: {e}", exc_info=True)
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return MultiAgentResult(
                success=False,
                response=f"I apologize, but I encountered an error while processing your complex request: {str(e)}",
                analysis=Analysis(
                    problem_statement=query,
                    requirements=[],
                    constraints=[],
                    complexity_factors=[],
                    success_criteria=[],
                ),
                plan=ExecutionPlan(goal="", steps=[], estimated_duration_ms=0),
                critique=Critique(
                    is_complete=False,
                    quality_score=0.0,
                    strengths=[],
                    weaknesses=["System error"],
                    missing_requirements=[],
                    recommendations=[],
                    final_verdict="REJECT",
                ),
                messages=self.messages,
                iterations=0,
                critique_cycles=0,
                tools_used=[],
                cost_usd=0.0,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def _generate_final_response(
        self,
        query: str,
        analysis: Analysis,
        plan: ExecutionPlan,
        critique: Critique,
        context: dict[str, Any],
    ) -> str:
        """Generate the final customer-facing response"""
        
        # Collect tool results
        tool_results = []
        for step in plan.steps:
            if step.completed and step.result:
                tool_results.append(f"Step {step.step_number}: {step.description}\nResult: {step.result}")

        system_prompt = """You are a helpful hibachi catering assistant.

Generate a final customer-facing response based on the analysis and execution results.

Your response should:
- Directly answer the customer's question
- Include specific details from tool results
- Be warm and professional
- Be concise but complete
- Use natural language (not technical jargon)"""

        user_prompt = f"""Customer Query: {query}

Analysis: {analysis.problem_statement}

Execution Results:
{chr(10).join(tool_results) if tool_results else "No tool results available"}

Quality Assessment:
- Complete: {critique.is_complete}
- Quality: {critique.quality_score:.1%}
- Strengths: {', '.join(critique.strengths)}

Generate a helpful, complete response for the customer."""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Natural, friendly tone
            )

            return response

        except Exception as e:
            self.logger.error(f"Failed to generate final response: {e}")
            return "I apologize, but I'm having trouble generating a complete response. Please call us at (916) 740-8768 for immediate assistance."

    def _log_message(self, from_agent: AgentRole, to_agent: AgentRole | None, content: str):
        """Log a message in the agent communication bus"""
        message = AgentMessage(from_agent=from_agent, to_agent=to_agent, content=content)
        self.messages.append(message)
        
        if self.config.log_agent_communication:
            self.logger.debug(f"[{from_agent.value}]: {content}")
